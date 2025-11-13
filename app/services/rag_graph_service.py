"""RAG service using Spoon AI StateGraph for chatbot."""
import os
import asyncio
import random
import logging
from typing import TypedDict, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from spoon_ai.graph import StateGraph
from spoon_ai.llm.manager import LLMManager, ConfigurationManager
from spoon_ai.llm.errors import RateLimitError
from spoon_ai.schema import Message as SpoonMessage
from app.services.retrieval.custom_chroma import CustomChromaClient
from app.core.config import settings
from app.models.message import Message, MessageRole

# Ensure GEMINI_API_KEY is in environment for ConfigurationManager
if settings.GEMINI_API_KEY and not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY

# Logger
logger = logging.getLogger(__name__)


class ChatbotState(TypedDict, total=False):
    """State schema for chatbot graph."""
    user_query: str
    conversation_id: int
    user: Any  # User object
    conversation_history: List[Message]
    retrieved_documents: List[Any]
    context: str
    system_prompt: str
    messages: List[SpoonMessage]
    response: str
    user_message: Any  # Message object (saved user message)
    assistant_message: Any  # Message object (saved assistant message)
    error: Optional[str]
    provider_used: Optional[str]  # Provider used (gemini, ollama, fallback)
    db: Session
    retrieval_client: CustomChromaClient
    llm_manager: LLMManager
    conversation_service: Any
    top_k: int


# System prompt template
SYSTEM_PROMPT_TEMPLATE = """Bạn là một chatbot nội bộ công ty. Nhiệm vụ của bạn là trả lời các câu hỏi của nhân viên dựa trên tài liệu công ty.

Hướng dẫn:
1. Chỉ trả lời dựa trên thông tin trong tài liệu được cung cấp
2. Nếu không tìm thấy thông tin trong tài liệu, hãy nói rằng bạn không có thông tin về câu hỏi này
3. Trả lời bằng tiếng Việt, rõ ràng và dễ hiểu
4. Sử dụng ngữ cảnh từ cuộc trò chuyện trước đó nếu có
5. Nếu câu hỏi không liên quan đến công ty, hãy nhắc nhở người dùng hỏi về công ty

Tài liệu tham khảo:
{context}

Cuộc trò chuyện trước đó:
{conversation_history}

Câu hỏi hiện tại: {user_query}

Hãy trả lời câu hỏi dựa trên thông tin trong tài liệu và cuộc trò chuyện trước đó."""


def _format_context(documents: List) -> str:
    """Format documents into context string."""
    if not documents:
        return "Không có tài liệu nào được tìm thấy."
    
    context_parts = []
    for i, doc in enumerate(documents, 1):
        metadata = doc.metadata or {}
        filename = metadata.get("filename", "Unknown")
        doc_type = metadata.get("document_type", "Unknown")
        content = doc.page_content
        context_parts.append(f"[Tài liệu {i}] {filename} ({doc_type}):\n{content}")
    
    return "\n\n".join(context_parts)


def _format_conversation_history(messages: List[Message]) -> str:
    """Format conversation history into string."""
    if not messages:
        return "Chưa có cuộc trò chuyện trước đó."
    
    history_parts = []
    for msg in messages:
        role = "Người dùng" if msg.role.value == "user" else "Chatbot"
        history_parts.append(f"{role}: {msg.content}")
    
    return "\n".join(history_parts)


async def load_conversation_history(state: ChatbotState) -> Dict[str, Any]:
    """Load conversation history from database."""
    try:
        conversation_id = state.get("conversation_id")
        conversation_service = state.get("conversation_service")
        user = state.get("user")
        
        if conversation_id and conversation_service and user:
            # Get conversation from database
            conversation = conversation_service.get_conversation(conversation_id, user)
            
            # Get recent messages (limit to 10 for context)
            recent_messages = conversation_service.get_recent_messages(conversation, limit=10)
            
            return {"conversation_history": recent_messages}
        else:
            return {"conversation_history": []}
    except Exception as e:
        return {
            "conversation_history": [],
            "error": f"Failed to load conversation history: {str(e)}"
        }


async def retrieve_documents(state: ChatbotState) -> Dict[str, Any]:
    """Retrieve relevant documents from vector database."""
    try:
        user_query = state.get("user_query", "")
        retrieval_client = state.get("retrieval_client")
        top_k = state.get("top_k", 5)
        
        if not retrieval_client:
            return {
                "retrieved_documents": [],
                "error": "Retrieval client not found"
            }
        
        # Retrieve documents
        documents = retrieval_client.query(user_query, k=top_k)
        
        return {"retrieved_documents": documents}
    except Exception as e:
        return {
            "retrieved_documents": [],
            "error": f"Failed to retrieve documents: {str(e)}"
        }


async def build_context(state: ChatbotState) -> Dict[str, Any]:
    """Build context from documents and conversation history."""
    try:
        # Get retrieved documents
        documents = state.get("retrieved_documents", [])
        
        # Format context
        context = _format_context(documents)
        
        # Get conversation history
        conversation_history = state.get("conversation_history", [])
        
        # Format conversation history
        history = _format_conversation_history(conversation_history)
        
        # Get user query
        user_query = state.get("user_query", "")
        
        # Build system prompt
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            context=context,
            conversation_history=history,
            user_query=user_query
        )
        
        # Build messages for LLM
        messages = []
        
        # Add system prompt
        messages.append(SpoonMessage(role="system", content=system_prompt))
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg.role.value == "user" else "assistant"
                messages.append(SpoonMessage(role=role, content=msg.content))
        
        # Add current user query
        messages.append(SpoonMessage(role="user", content=user_query))
        
        return {
            "context": context,
            "system_prompt": system_prompt,
            "messages": messages
        }
    except Exception as e:
        return {
            "error": f"Failed to build context: {str(e)}"
        }


async def generate_fallback_response(state: ChatbotState) -> Dict[str, Any]:
    """Generate fallback response based on documents only (no LLM)."""
    retrieved_documents = state.get("retrieved_documents", [])
    user_query = state.get("user_query", "")
    
    if not retrieved_documents:
        return {
            "response": "Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn trong tài liệu công ty. Vui lòng thử lại với câu hỏi khác hoặc liên hệ bộ phận hỗ trợ.",
            "error": "No documents found",
            "provider_used": "fallback"
        }
    
    # Extract relevant text from documents
    relevant_texts = []
    for doc in retrieved_documents[:3]:  # Top 3 documents
        content = doc.page_content[:500]  # First 500 characters
        relevant_texts.append(content)
    
    # Simple response based on documents
    response = f"Dựa trên tài liệu công ty, tôi tìm thấy thông tin sau:\n\n"
    response += "\n\n".join([f"- {text}" for text in relevant_texts])
    response += "\n\nVui lòng liên hệ bộ phận hỗ trợ để biết thêm chi tiết."
    
    logger.info("Using fallback response from documents (no LLM)")
    return {
        "response": response,
        "provider_used": "fallback"
    }


async def generate_response(state: ChatbotState) -> Dict[str, Any]:
    """Generate response using LLM with retry logic and Ollama fallback."""
    llm_manager = state.get("llm_manager")
    messages = state.get("messages", [])
    
    if not llm_manager:
        return {
            "response": "",
            "error": "LLM manager not found",
            "provider_used": None
        }
    
    # Get retry configuration from settings
    max_retries = settings.LLM_RETRY_ATTEMPTS
    base_delay = settings.LLM_RETRY_BASE_DELAY
    max_delay = settings.LLM_RETRY_MAX_DELAY
    
    # Gemini models to try (in order)
    # Primary model: gemini-2.5-flash (từ settings.GEMINI_MODEL)
    # Fallback models: Tự chọn (có thể thay đổi trong code)
    gemini_models = [
        settings.GEMINI_MODEL,  # Primary model (gemini-2.5-flash)
        "gemini-2.0-flash-exp",  # Fallback model 1 (có thể thay đổi)
        "gemini-1.5-pro",  # Fallback model 2 (có thể thay đổi)
        # Các fallback models khác có thể dùng (uncomment để dùng):
        # "gemini-2.5-flash-lite",  # Phiên bản tối ưu hóa về chi phí và tốc độ
        # "gemini-1.5-flash",  # Model ổn định, rate limit cao
    ]
    
    # Try Gemini models first
    for model in gemini_models:
        for attempt in range(max_retries):
            try:
                gemini_config = {
                    "model": model,
                    "max_tokens": 4096,
                    "temperature": 0.3,
                }
                
                response = await llm_manager.chat(
                    messages=messages,
                    provider="gemini",
                    **gemini_config
                )
                
                logger.info(f"Successfully generated response using Gemini model: {model}")
                return {
                    "response": response.content,
                    "provider_used": f"gemini-{model}"
                }
                
            except RateLimitError as e:
                # Rate limit error - retry with exponential backoff
                if attempt < max_retries - 1:
                    # Calculate delay: base_delay * (2^attempt) with jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    # Add jitter (random 0-1 seconds)
                    jitter = random.uniform(0, 1)
                    delay += jitter
                    
                    logger.warning(
                        f"Gemini model {model} rate limited. "
                        f"Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Max retries reached for this model, try next model
                    logger.warning(f"Gemini model {model} rate limited after {max_retries} retries. Trying next model...")
                    break
                    
            except Exception as e:
                # Check if error is rate limit related (even if not RateLimitError)
                error_detail = str(e).lower()
                if "rate limit" in error_detail or "quota" in error_detail or "429" in error_detail:
                    # Rate limit error (not caught as RateLimitError) - retry with exponential backoff
                    if attempt < max_retries - 1:
                        # Calculate delay: base_delay * (2^attempt) with jitter
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        # Add jitter (random 0-1 seconds)
                        jitter = random.uniform(0, 1)
                        delay += jitter
                        
                        logger.warning(
                            f"Gemini model {model} rate limited (error message). "
                            f"Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        # Max retries reached for this model, try next model
                        logger.warning(f"Gemini model {model} rate limited after {max_retries} retries. Trying next model...")
                        break
                else:
                    # Other errors - log and try next model
                    logger.warning(f"Gemini model {model} failed: {str(e)}. Trying next model...")
                    break
    
    # All Gemini models failed - try Ollama if enabled
    if settings.OLLAMA_ENABLED:
        try:
            logger.info("All Gemini models failed. Falling back to Ollama...")
            
            # Create OpenAI-compatible client for Ollama
            # Ollama uses OpenAI-compatible API
            from openai import AsyncOpenAI
            
            ollama_client = AsyncOpenAI(
                api_key=settings.OLLAMA_API_KEY,
                base_url=settings.OLLAMA_BASE_URL,
                timeout=60.0
            )
            
            # Convert messages to OpenAI format
            openai_messages = []
            for msg in messages:
                openai_msg = {"role": msg.role, "content": msg.content}
                openai_messages.append(openai_msg)
            
            # Call Ollama API
            ollama_response = await ollama_client.chat.completions.create(
                model=settings.OLLAMA_MODEL,
                messages=openai_messages,
                max_tokens=4096,
                temperature=0.3,
            )
            
            response_content = ollama_response.choices[0].message.content
            
            logger.info(f"Successfully generated response using Ollama model: {settings.OLLAMA_MODEL}")
            return {
                "response": response_content,
                "provider_used": f"ollama-{settings.OLLAMA_MODEL}"
            }
            
        except Exception as ollama_error:
            logger.error(f"Ollama fallback failed: {ollama_error}")
            # Ollama failed - use fallback response from documents
            return await generate_fallback_response(state)
    else:
        # Ollama not enabled - use fallback response from documents
        logger.info("Ollama not enabled. Using fallback response from documents.")
        return await generate_fallback_response(state)


async def save_message(state: ChatbotState) -> Dict[str, Any]:
    """Save messages to database."""
    try:
        conversation_id = state.get("conversation_id")
        user_query = state.get("user_query", "")
        response = state.get("response", "")
        conversation_service = state.get("conversation_service")
        user = state.get("user")
        
        if not conversation_id or not conversation_service or not user:
            return {"error": "Missing required state: conversation_id, conversation_service, or user"}
        
        # Get conversation
        conversation = conversation_service.get_conversation(conversation_id, user)
        
        # Save user message
        user_message = conversation_service.create_message(
            conversation,
            user_query,
            MessageRole.USER
        )
        
        # Save assistant message
        assistant_message = conversation_service.create_message(
            conversation,
            response,
            MessageRole.ASSISTANT
        )
        
        # Update conversation updated_at
        conversation_service.db.commit()
        conversation_service.db.refresh(conversation)
        
        return {
            "user_message": user_message,
            "assistant_message": assistant_message
        }
    except Exception as e:
        return {
            "error": f"Failed to save messages: {str(e)}"
        }


async def handle_error(state: ChatbotState) -> Dict[str, Any]:
    """Handle errors."""
    error = state.get("error")
    if error:
        print(f"Error in chatbot graph: {error}")
        # Set default response if error occurred
        if not state.get("response"):
            return {
                "response": f"Xin lỗi, đã xảy ra lỗi: {error}"
            }
    return {}


class RAGGraphService:
    """RAG service using Spoon AI StateGraph for chatbot."""
    
    def __init__(self, db: Session, conversation_service):
        """Initialize RAG graph service.
        
        Args:
            db: Database session.
            conversation_service: Conversation service instance.
        """
        self.db = db
        self.conversation_service = conversation_service
        self.retrieval_client = CustomChromaClient()
        
        # Initialize LLMManager with configuration
        config_manager = ConfigurationManager()
        
        # Log Ollama status
        if settings.OLLAMA_ENABLED:
            logger.info(f"Ollama fallback enabled with model: {settings.OLLAMA_MODEL}")
            logger.info(f"Ollama base URL: {settings.OLLAMA_BASE_URL}")
        else:
            logger.info("Ollama fallback disabled")
        
        self.llm_manager = LLMManager(config_manager)
        
        # Build graph
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """Build the chatbot graph.
        
        Returns:
            StateGraph instance.
        """
        # Create graph with ChatbotState schema
        graph = StateGraph(ChatbotState)
        
        # Add nodes to graph (using functions, StateGraph will wrap them in RunnableNode)
        graph.add_node("load_conversation_history", load_conversation_history)
        graph.add_node("retrieve_documents", retrieve_documents)
        graph.add_node("build_context", build_context)
        graph.add_node("generate_response", generate_response)
        graph.add_node("save_message", save_message)
        graph.add_node("handle_error", handle_error)
        
        # Add edges (linear flow)
        graph.add_edge("load_conversation_history", "retrieve_documents")
        graph.add_edge("retrieve_documents", "build_context")
        graph.add_edge("build_context", "generate_response")
        graph.add_edge("generate_response", "save_message")
        graph.add_edge("save_message", "handle_error")
        
        # Set entry point
        graph.set_entry_point("load_conversation_history")
        
        # Enable monitoring
        graph.enable_monitoring()
        
        return graph
    
    async def generate_response(
        self,
        user_query: str,
        conversation_id: int,
        user,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Generate response using RAG graph.
        
        Args:
            user_query: User query string.
            conversation_id: Conversation ID.
            user: User object.
            top_k: Number of documents to retrieve (default: 5).
            
        Returns:
            Dictionary with response, user_message, and assistant_message.
        """
        # Create initial state
        initial_state: ChatbotState = {
            "user_query": user_query,
            "conversation_id": conversation_id,
            "user": user,
            "conversation_history": [],
            "retrieved_documents": [],
            "context": "",
            "system_prompt": "",
            "messages": [],
            "response": "",
            "error": None,
            "provider_used": None,  # Initialize provider_used
            "db": self.db,
            "retrieval_client": self.retrieval_client,
            "llm_manager": self.llm_manager,
            "conversation_service": self.conversation_service,
            "top_k": top_k
        }
        
        # Execute graph
        try:
            result = await self.compiled_graph.invoke(initial_state)
            
            # Log provider used
            provider_used = result.get("provider_used", "unknown")
            if provider_used:
                logger.info(f"Response generated using provider: {provider_used}")
            
            return {
                "response": result.get("response", ""),
                "user_message": result.get("user_message"),
                "assistant_message": result.get("assistant_message"),
                "provider_used": provider_used
            }
        except Exception as e:
            import traceback
            error_detail = str(e)
            logger.error(f"Error in RAG graph execution: {error_detail}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "response": f"Xin lỗi, tôi không thể trả lời câu hỏi này lúc này. Lỗi: {error_detail}",
                "user_message": None,
                "assistant_message": None,
                "provider_used": None
            }

