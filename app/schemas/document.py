"""Document schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.document import DocumentType


class DocumentBase(BaseModel):
    """Base document schema."""
    filename: str = Field(..., max_length=255)
    document_type: DocumentType
    description: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Document creation schema."""
    pass


class DocumentUpdate(BaseModel):
    """Document update schema."""
    description: Optional[str] = None
    document_type: Optional[DocumentType] = None


class DocumentResponse(DocumentBase):
    """Document response schema."""
    id: int
    file_path: str
    uploaded_by: int
    uploaded_at: datetime
    updated_at: datetime
    file_metadata: Optional[dict] = None
    
    class Config:
        from_attributes = True


class DocumentUpload(BaseModel):
    """Document upload schema."""
    document_type: DocumentType
    description: Optional[str] = None

