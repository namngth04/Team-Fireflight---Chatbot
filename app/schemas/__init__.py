"""Pydantic schemas for API requests and responses."""
from app.schemas.user import User, UserCreate, UserUpdate, UserResponse
from app.schemas.auth import Token, TokenData, LoginRequest, LoginResponse
from app.schemas.document import DocumentBase, DocumentCreate, DocumentUpdate, DocumentResponse, DocumentUpload
from app.schemas.conversation import ConversationBase, ConversationCreate, ConversationUpdate, ConversationResponse, ConversationWithMessages
from app.schemas.message import MessageBase, MessageCreate, MessageResponse, ChatMessageResponse

__all__ = [
    "User",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "Token",
    "TokenData",
    "LoginRequest",
    "LoginResponse",
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentUpload",
    "ConversationBase",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "ConversationWithMessages",
    "MessageBase",
    "MessageCreate",
    "MessageResponse",
    "ChatMessageResponse",
]

