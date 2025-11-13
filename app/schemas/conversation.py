"""Conversation schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.message import MessageResponse


class ConversationBase(BaseModel):
    """Base conversation schema."""
    title: str = Field(..., max_length=200)


class ConversationCreate(BaseModel):
    """Create conversation schema."""
    title: Optional[str] = Field(None, max_length=200)


class ConversationUpdate(BaseModel):
    """Update conversation schema."""
    title: Optional[str] = Field(None, max_length=200)


class ConversationResponse(ConversationBase):
    """Conversation response schema."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    """Conversation with messages response schema."""
    messages: List[MessageResponse] = []

