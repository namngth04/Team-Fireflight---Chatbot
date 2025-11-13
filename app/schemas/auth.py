"""Authentication schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1)


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None


class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

