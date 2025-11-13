"""Conversation service."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.user import User


class ConversationService:
    """Conversation service for managing conversations and messages."""
    
    def __init__(self, db: Session):
        """Initialize conversation service.
        
        Args:
            db: Database session.
        """
        self.db = db
    
    def create_conversation(
        self,
        user: User,
        title: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation.
        
        Args:
            user: User who creates the conversation.
            title: Conversation title (optional).
            
        Returns:
            Created conversation.
        """
        # Auto-generate title if not provided
        if not title:
            title = "New conversation"
        
        conversation = Conversation(
            user_id=user.id,
            title=title
        )
        
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def list_conversations(
        self,
        user: User,
        skip: int = 0,
        limit: int = 100
    ) -> List[Conversation]:
        """List conversations for a user.
        
        Args:
            user: User to list conversations for.
            skip: Number of conversations to skip.
            limit: Maximum number of conversations to return.
            
        Returns:
            List of conversations.
        """
        conversations = (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user.id)
            .order_by(desc(Conversation.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return conversations
    
    def get_conversation(
        self,
        conversation_id: int,
        user: User
    ) -> Conversation:
        """Get a conversation by ID.
        
        Args:
            conversation_id: Conversation ID.
            user: User who owns the conversation.
            
        Returns:
            Conversation object.
            
        Raises:
            HTTPException: If conversation not found or not owned by user.
        """
        conversation = (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        if conversation.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        return conversation
    
    def update_conversation(
        self,
        conversation: Conversation,
        title: Optional[str] = None
    ) -> Conversation:
        """Update a conversation.
        
        Args:
            conversation: Conversation to update.
            title: New title (optional).
            
        Returns:
            Updated conversation.
        """
        if title is not None:
            conversation.title = title
        
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def delete_conversation(
        self,
        conversation: Conversation
    ) -> bool:
        """Delete a conversation.
        
        Args:
            conversation: Conversation to delete.
            
        Returns:
            True if deleted successfully.
        """
        try:
            self.db.delete(conversation)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False
    
    def get_messages(
        self,
        conversation: Conversation,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """Get messages for a conversation.
        
        Args:
            conversation: Conversation to get messages for.
            skip: Number of messages to skip.
            limit: Maximum number of messages to return.
            
        Returns:
            List of messages.
        """
        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at)
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return messages
    
    def create_message(
        self,
        conversation: Conversation,
        content: str,
        role: MessageRole
    ) -> Message:
        """Create a new message.
        
        Args:
            conversation: Conversation to add message to.
            content: Message content.
            role: Message role (user or assistant).
            
        Returns:
            Created message.
        """
        message = Message(
            conversation_id=conversation.id,
            content=content,
            role=role
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def get_recent_messages(
        self,
        conversation: Conversation,
        limit: int = 10
    ) -> List[Message]:
        """Get recent messages for a conversation.
        
        Args:
            conversation: Conversation to get messages for.
            limit: Maximum number of messages to return (default: 10).
            
        Returns:
            List of recent messages.
        """
        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(desc(Message.created_at))
            .limit(limit)
            .all()
        )
        
        # Reverse to get chronological order
        return list(reversed(messages))

