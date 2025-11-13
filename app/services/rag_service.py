"""RAG service for chatbot."""
import os
from typing import List, Optional
from sqlalchemy.orm import Session
from spoon_ai.llm.manager import LLMManager, ConfigurationManager
from spoon_ai.schema import Message as SpoonMessage
from app.services.retrieval.custom_chroma import CustomChromaClient
from app.core.config import settings

# Ensure GEMINI_API_KEY is in environment for ConfigurationManager
# ConfigurationManager loads from environment variables, not from settings
if settings.GEMINI_API_KEY and not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY


class RAGService:
    """RAG service for chatbot using Spoon AI LLMManager and ChromaDB."""
    
    SYSTEM_PROMPT = """Bạn là một chatbot nội bộ công ty. Nhiệm vụ của bạn là trả lời các câu hỏi của nhân viên dựa trên tài liệu công ty.

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
    
    def __init__(self, db: Session):
        """Initialize RAG service.
        
        Args:
            db: Database session.
        """
        self.db = db
        self.retrieval_client = CustomChromaClient()
        
        # Initialize LLMManager with ConfigurationManager
        # ConfigurationManager will load GEMINI_API_KEY from environment
        # Make sure GEMINI_API_KEY is set in .env file
        config_manager = ConfigurationManager()
        self.llm_manager = LLMManager(config_manager)
        
        # Gemini config (will be used when calling chat)
        # Note: ConfigurationManager will also load config from environment
        # But we can override with direct config if needed
        self.gemini_config = {
            "api_key": settings.GEMINI_API_KEY,
            "model": "gemini-2.0-flash-exp",  # Use Gemini 2.0 Flash Exp for better rate limits
            "max_tokens": 4096,
            "temperature": 0.3,
        }
    
    def _format_context(self, documents: List) -> str:
        """Format documents into context string.
        
        Args:
            documents: List of Document objects from ChromaDB.
            
        Returns:
            Formatted context string.
        """
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
    
    def _format_conversation_history(self, messages: List) -> str:
        """Format conversation history into string.
        
        Args:
            messages: List of Message objects from database.
            
        Returns:
            Formatted conversation history string.
        """
        if not messages:
            return "Chưa có cuộc trò chuyện trước đó."
        
        history_parts = []
        for msg in messages:
            role = "Người dùng" if msg.role.value == "user" else "Chatbot"
            history_parts.append(f"{role}: {msg.content}")
        
        return "\n".join(history_parts)
    
    async def generate_response(
        self,
        user_query: str,
        conversation_history: Optional[List] = None,
        top_k: int = 5
    ) -> str:
        """Generate response using RAG.
        
        Args:
            user_query: User query string.
            conversation_history: List of previous messages (optional).
            top_k: Number of documents to retrieve (default: 5).
            
        Returns:
            Generated response string.
        """
        # Retrieve relevant documents
        documents = self.retrieval_client.query(user_query, k=top_k)
        
        # Format context
        context = self._format_context(documents)
        
        # Format conversation history
        history = self._format_conversation_history(conversation_history or [])
        
        # Build system prompt
        system_prompt = self.SYSTEM_PROMPT.format(
            context=context,
            conversation_history=history,
            user_query=user_query
        )
        
        # Build messages for LLM
        # Include conversation history if available
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
        
        # Generate response using LLMManager
        # LLMManager will use ConfigurationManager to load provider config
        # If provider is not initialized, it will be initialized automatically
        try:
            response = await self.llm_manager.chat(
                messages=messages,
                provider="gemini",
                model=self.gemini_config.get("model", "gemini-2.0-flash-exp"),
                max_tokens=self.gemini_config.get("max_tokens", 4096),
                temperature=self.gemini_config.get("temperature", 0.3)
            )
            
            return response.content
        except Exception as e:
            # Fallback response
            import traceback
            error_detail = str(e)
            # Log error for debugging
            print(f"Error generating response: {error_detail}")
            print(f"Traceback: {traceback.format_exc()}")
            return f"Xin lỗi, tôi không thể trả lời câu hỏi này lúc này. Lỗi: {error_detail}"

