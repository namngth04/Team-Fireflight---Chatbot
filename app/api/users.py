"""User management API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_password_hash
from app.core.dependencies import get_current_admin, get_current_user
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/api/users", tags=["users"])


# IMPORTANT: More specific routes must be defined BEFORE less specific routes
# This ensures FastAPI matches /api/users/{user_id} before /api/users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get user by ID (Admin only).
    
    Returns user information by user ID.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.get("", response_model=List[UserResponse])
async def list_users(
    search: Optional[str] = Query(None, description="Search by username, full_name, phone, or email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all users (Admin only).
    
    Returns a list of all users, optionally filtered by search query.
    """
    users_query = db.query(User)
    
    # Search filter
    if search:
        search_filter = or_(
            User.username.ilike(f"%{search}%"),
            User.full_name.ilike(f"%{search}%"),
            User.phone.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%")
        )
        users_query = users_query.filter(search_filter)
    
    # Pagination
    users = users_query.offset(skip).limit(limit).all()
    
    return [UserResponse.model_validate(user) for user in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (Admin only).
    
    Creates a new user with the provided information.
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists (if provided)
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Create new user
    new_user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        full_name=user_data.full_name,
        email=user_data.email,
        phone=user_data.phone,
        date_of_birth=user_data.date_of_birth
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Return user with plain text password in response
    user_response = UserResponse.model_validate(new_user)
    user_response.password = user_data.password  # Include plain text password in response
    return user_response


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update user (Admin only).
    
    Updates user information. Can update full_name, phone, date_of_birth, email, and password.
    Password is optional - only update if provided.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if email already exists (if provided and changed)
    if user_data.email and user_data.email != user.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Track if password was updated
    updated_password = None
    
    # Update user fields
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.date_of_birth is not None:
        user.date_of_birth = user_data.date_of_birth
    if user_data.password is not None:
        # Update password if provided
        updated_password = user_data.password
        user.password_hash = get_password_hash(user_data.password)
    
    db.commit()
    db.refresh(user)
    
    # Return user with plain text password in response if it was updated
    user_response = UserResponse.model_validate(user)
    if updated_password is not None:
        user_response.password = updated_password  # Include plain text password in response
    return user_response


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete user (Admin only).
    
    Deletes a user by ID. Cannot delete admin user or yourself.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cannot delete admin user
    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete admin user"
        )
    
    # Cannot delete yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    # Delete user (cascade will handle related records)
    db.delete(user)
    db.commit()
    
    return None

