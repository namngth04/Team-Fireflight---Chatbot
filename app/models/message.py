"""Message model."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class MessageRole(str, enum.Enum):
    """Message roles."""
    USER = "user"
    ASSISTANT = "assistant"


class Message(Base):
    """Message model."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    # Note: Indexes are automatically created by SQLAlchemy from index=True in Column definitions
    # No need to define __table_args__ with Index objects to avoid duplicates
    
    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role='{self.role}')>"

