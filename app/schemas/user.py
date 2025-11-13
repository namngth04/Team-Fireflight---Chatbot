"""User schemas."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[datetime] = None


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=6, max_length=100)
    role: UserRole = UserRole.EMPLOYEE


class UserUpdate(BaseModel):
    """User update schema."""
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[datetime] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserResponse(UserBase):
    """User response schema."""
    id: int
    role: UserRole
    password: Optional[str] = None  # Plain text password (only returned when creating/updating)
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class User(UserResponse):
    """User schema (alias for UserResponse)."""
    pass

