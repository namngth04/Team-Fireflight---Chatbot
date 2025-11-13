"""Document management API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.user import User
from app.models.document import DocumentType
from app.services.document_service import DocumentService
from app.schemas.document import DocumentResponse, DocumentUpdate

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Upload a document (Admin only).
    
    Uploads a document, parses it, chunks it, and adds it to the vector database.
    Currently only supports .txt files.
    """
    # Validate document type
    try:
        doc_type = DocumentType(document_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Must be one of: {[dt.value for dt in DocumentType]}"
        )
    
    # Create document service
    document_service = DocumentService(db)
    
    # Upload document
    document = document_service.upload_document(
        file=file,
        document_type=doc_type,
        description=description,
        uploaded_by=current_user
    )
    
    return DocumentResponse.model_validate(document)


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    search: Optional[str] = Query(None, description="Search by filename or description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all documents (Admin only).
    
    Returns a list of all documents, optionally filtered by type or search query.
    """
    # Parse document type if provided
    doc_type = None
    if document_type:
        try:
            doc_type = DocumentType(document_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid document type. Must be one of: {[dt.value for dt in DocumentType]}"
            )
    
    # Create document service
    document_service = DocumentService(db)
    
    # List documents
    documents = document_service.list_documents(
        document_type=doc_type,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get document by ID (Admin only).
    
    Returns information about a specific document.
    """
    # Create document service
    document_service = DocumentService(db)
    
    # Get document
    document = document_service.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse.model_validate(document)


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_data: DocumentUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update document (Admin only).
    
    Updates document description and/or type.
    """
    # Create document service
    document_service = DocumentService(db)
    
    # Get document
    document = document_service.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Update document
    document = document_service.update_document(
        document=document,
        description=document_data.description,
        document_type=document_data.document_type
    )
    
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete document (Admin only).
    
    Deletes a document from the database, vector database, and storage.
    """
    # Create document service
    document_service = DocumentService(db)
    
    # Get document
    document = document_service.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete document
    success = document_service.delete_document(document)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )
    
    return None

