"""Document model."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class DocumentType(str, enum.Enum):
    """Document types."""
    POLICIES = "policies"  # Chính sách
    PROCESSES = "processes"  # Quy trình
    GUIDELINES = "guidelines"  # Hướng dẫn
    COMPANY_INFO = "company_info"  # Thông tin công ty
    FORMS = "forms"  # Biểu mẫu
    TRAINING = "training"  # Tài liệu đào tạo
    ANNOUNCEMENTS = "announcements"  # Thông báo
    TECHNICAL = "technical"  # Tài liệu kỹ thuật
    SUPPORT = "support"  # Tài nguyên hỗ trợ


class Document(Base):
    """Document model."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False, index=True)
    description = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    file_metadata = Column(JSON, nullable=True)  # Changed from 'metadata' to 'file_metadata' because 'metadata' is reserved in SQLAlchemy
    
    # Relationships
    uploader = relationship("User", back_populates="documents")
    
    # Note: Indexes are automatically created by SQLAlchemy from index=True in Column definitions
    # No need to define __table_args__ with Index objects to avoid duplicates
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', type='{self.document_type}')>"

