"""Message schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.message import MessageRole


class MessageBase(BaseModel):
    """Base message schema."""
    content: str = Field(..., min_length=1)
    role: MessageRole


class MessageCreate(BaseModel):
    """Create message schema."""
    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    """Message response schema."""
    id: int
    conversation_id: int
    role: MessageRole
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    """Chat message response schema."""
    message: MessageResponse
    response: MessageResponse

