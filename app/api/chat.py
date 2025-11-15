"""Chatbot API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.message import MessageRole
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationWithMessages
)
from app.schemas.message import MessageCreate, MessageResponse, ChatMessageResponse
from app.services.conversation_service import ConversationService
from app.services.spoon_chat_service import SpoonChatService

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_create: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation.
    
    Args:
        conversation_create: Conversation creation data.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        Created conversation.
    """
    service = ConversationService(db)
    
    # Auto-generate title if not provided
    title = conversation_create.title
    if not title:
        title = "New conversation"
    
    conversation = service.create_conversation(current_user, title)
    return ConversationResponse.model_validate(conversation)


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List conversations for the current user.
    
    Args:
        skip: Number of conversations to skip.
        limit: Maximum number of conversations to return.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        List of conversations.
    """
    service = ConversationService(db)
    conversations = service.list_conversations(current_user, skip, limit)
    return [ConversationResponse.model_validate(conv) for conv in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a conversation with its messages.
    
    Args:
        conversation_id: Conversation ID.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        Conversation with messages.
    """
    service = ConversationService(db)
    conversation = service.get_conversation(conversation_id, current_user)
    
    # Get messages
    messages = service.get_messages(conversation)
    
    # Build response
    response = ConversationWithMessages.model_validate(conversation)
    response.messages = [MessageResponse.model_validate(msg) for msg in messages]
    
    return response


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    conversation_update: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a conversation.
    
    Args:
        conversation_id: Conversation ID.
        conversation_update: Conversation update data.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        Updated conversation.
    """
    service = ConversationService(db)
    conversation = service.get_conversation(conversation_id, current_user)
    updated_conversation = service.update_conversation(
        conversation,
        title=conversation_update.title
    )
    return ConversationResponse.model_validate(updated_conversation)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation.
    
    Args:
        conversation_id: Conversation ID.
        current_user: Current authenticated user.
        db: Database session.
    """
    service = ConversationService(db)
    conversation = service.get_conversation(conversation_id, current_user)
    if not service.delete_conversation(conversation):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )
    return None


@router.post("/conversations/{conversation_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    conversation_id: int,
    message_create: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message and get response from chatbot.
    
    Args:
        conversation_id: Conversation ID.
        message_create: Message creation data.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        User message and assistant response.
    """
    # Get conversation service
    conversation_service = ConversationService(db)
    conversation = conversation_service.get_conversation(conversation_id, current_user)
    
    # Generate response using Spoon chat orchestrator (with fallback to RAG)
    spoon_chat_service = SpoonChatService(db, conversation_service)
    result = await spoon_chat_service.send_message(
        conversation_id=conversation_id,
        message=message_create.content,
        user=current_user,
        top_k=5,
    )
    
    user_message = result.get("user_message")
    assistant_message = result.get("assistant_message")
    
    # If messages not found in result, get from database (should be there after save_message node)
    if not user_message or not assistant_message:
        # Refresh conversation to get latest messages
        db.refresh(conversation)
        recent_messages = conversation_service.get_recent_messages(conversation, limit=2)
        if len(recent_messages) >= 2:
            # Last message should be assistant, second last should be user
            assistant_message = recent_messages[-1]
            user_message = recent_messages[-2]
        elif len(recent_messages) == 1:
            # Only one message (should be assistant)
            assistant_message = recent_messages[0]
            # Get all messages to find user message
            all_messages = conversation_service.get_messages(conversation)
            if len(all_messages) >= 2:
                user_message = all_messages[-2]
    
    # If still not found (should not happen, but fallback), create them manually
    if not user_message or not assistant_message:
        user_message = conversation_service.create_message(
            conversation,
            message_create.content,
            MessageRole.USER,
        )
        assistant_message = conversation_service.create_message(
            conversation,
            result.get("response", ""),
            MessageRole.ASSISTANT,
        )
    
    # Build response
    return ChatMessageResponse(
        message=MessageResponse.model_validate(user_message),
        response=MessageResponse.model_validate(assistant_message),
        provider_used=result.get("provider_used"),
        metadata=result.get("spoon_agent_metadata"),
    )

