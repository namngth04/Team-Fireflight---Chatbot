"""Document service."""
import os
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import UploadFile, HTTPException, status
from app.models.document import Document, DocumentType
from app.models.user import User
from app.utils.file_storage import save_uploaded_file, delete_file, get_file_size
from app.utils.document_parser import parse_txt_file
from app.services.retrieval.custom_chroma import CustomChromaClient
from app.core.config import settings


class DocumentService:
    """Document service for managing documents."""
    
    def __init__(self, db: Session):
        """Initialize document service.
        
        Args:
            db: Database session.
        """
        self.db = db
        self.retrieval_client = CustomChromaClient()
    
    def upload_document(
        self,
        file: UploadFile,
        document_type: DocumentType,
        description: Optional[str],
        uploaded_by: User
    ) -> Document:
        """Upload a document.
        
        Args:
            file: Uploaded file.
            document_type: Document type.
            description: Document description.
            uploaded_by: User who uploaded the document.
        
        Returns:
            Created Document object.
        
        Raises:
            HTTPException: If file type is invalid or file size exceeds limit.
        """
        # Validate file type (txt only for now)
        if not file.filename.endswith(".txt"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .txt files are supported at this time"
            )
        
        # Validate file size
        # Get file size by reading content (file.size might not be available)
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds maximum allowed size of {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Save file to storage
        file_path, original_filename = save_uploaded_file(file, uploaded_by.id)
        
        # Create document record in database
        document = Document(
            filename=original_filename,
            file_path=file_path,
            document_type=document_type,
            description=description,
            uploaded_by=uploaded_by.id,
            file_metadata={
                "file_size": file_size,
                "original_filename": original_filename,
            }
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        # Parse and chunk document
        try:
            chunks = parse_txt_file(
                file_path=file_path,
                document_id=document.id,
                filename=original_filename,
                document_type=document_type.value,
                uploaded_by=uploaded_by.id,
            )
            
            # Add chunks to vector database
            if chunks:
                self.retrieval_client.add_documents(chunks)
        
        except Exception as e:
            # If parsing fails, delete document from database
            self.db.delete(document)
            self.db.commit()
            # Delete file from storage
            delete_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process document: {str(e)}"
            )
        
        return document
    
    def list_documents(
        self,
        document_type: Optional[DocumentType] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """List documents.
        
        Args:
            document_type: Filter by document type. Defaults to None.
            search: Search by filename or description. Defaults to None.
            skip: Number of documents to skip. Defaults to 0.
            limit: Maximum number of documents to return. Defaults to 100.
        
        Returns:
            List of Document objects.
        """
        query = self.db.query(Document)
        
        # Filter by document type
        if document_type:
            query = query.filter(Document.document_type == document_type)
        
        # Search by filename or description
        if search:
            search_filter = or_(
                Document.filename.ilike(f"%{search}%"),
                Document.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Order by uploaded_at (newest first)
        query = query.order_by(Document.uploaded_at.desc())
        
        # Pagination
        documents = query.offset(skip).limit(limit).all()
        
        return documents
    
    def get_document(self, document_id: int) -> Optional[Document]:
        """Get document by ID.
        
        Args:
            document_id: Document ID.
        
        Returns:
            Document object or None if not found.
        """
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def update_document(
        self,
        document: Document,
        description: Optional[str] = None,
        document_type: Optional[DocumentType] = None
    ) -> Document:
        """Update document.
        
        Args:
            document: Document object to update.
            description: New description. Defaults to None.
            document_type: New document type. Defaults to None.
        
        Returns:
            Updated Document object.
        """
        # Update description
        if description is not None:
            document.description = description
        
        # Update document type
        if document_type is not None:
            # If document type changes, we need to update vector database metadata
            if document.document_type != document_type:
                # For now, we'll just update the database
                # In the future, we might want to update vector database metadata
                document.document_type = document_type
        
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def delete_document(self, document: Document) -> bool:
        """Delete document.
        
        Args:
            document: Document object to delete.
        
        Returns:
            True if document was deleted, False otherwise.
        """
        try:
            # Delete from vector database
            self.retrieval_client.delete_documents_by_metadata(document.id)
            
            # Delete file from storage
            delete_file(document.file_path)
            
            # Delete from database
            self.db.delete(document)
            self.db.commit()
            
            return True
        except Exception:
            self.db.rollback()
            return False
    

