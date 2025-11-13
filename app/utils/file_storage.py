"""File storage utilities."""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
from app.core.config import settings


def ensure_storage_dir() -> Path:
    """Ensure storage directory exists.
    
    Returns:
        Path to storage directory.
    """
    storage_path = Path(settings.FILE_STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path


def save_uploaded_file(file: UploadFile, user_id: int) -> tuple[str, str]:
    """Save uploaded file to storage.
    
    Args:
        file: Uploaded file.
        user_id: ID of the user uploading the file.
    
    Returns:
        Tuple of (file_path, filename) where file_path is the full path to the saved file.
    """
    # Ensure storage directory exists
    storage_path = ensure_storage_dir()
    
    # Create user-specific directory
    user_dir = storage_path / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Full path to saved file
    file_path = user_dir / unique_filename
    
    # Ensure file pointer is at the beginning
    file.file.seek(0)
    
    # Save file
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Return relative path from storage root and original filename
    relative_path = str(file_path.relative_to(storage_path))
    return relative_path, file.filename


def delete_file(file_path: str) -> bool:
    """Delete file from storage.
    
    Args:
        file_path: Relative path to file from storage root.
    
    Returns:
        True if file was deleted, False otherwise.
    """
    try:
        storage_path = Path(settings.FILE_STORAGE_PATH)
        full_path = storage_path / file_path
        
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    except Exception:
        return False


def read_file_content(file_path: str) -> str:
    """Read file content.
    
    Args:
        file_path: Relative path to file from storage root.
    
    Returns:
        File content as string.
    """
    storage_path = Path(settings.FILE_STORAGE_PATH)
    full_path = storage_path / file_path
    
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


def get_file_size(file_path: str) -> int:
    """Get file size in bytes.
    
    Args:
        file_path: Relative path to file from storage root.
    
    Returns:
        File size in bytes.
    """
    storage_path = Path(settings.FILE_STORAGE_PATH)
    full_path = storage_path / file_path
    
    if full_path.exists():
        return full_path.stat().st_size
    return 0

