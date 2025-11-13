"""Document parser utilities."""
from pathlib import Path
from typing import List
from spoon_ai.retrieval.base import Document
from app.utils.file_storage import read_file_content
from app.core.config import settings


def parse_txt_file(file_path: str, document_id: int, filename: str, 
                   document_type: str, uploaded_by: int, chunk_size: int = 1000, 
                   chunk_overlap: int = 200) -> List[Document]:
    """Parse TXT file and chunk it.
    
    Args:
        file_path: Relative path to file from storage root.
        document_id: Document ID in database.
        filename: Original filename.
        document_type: Document type.
        uploaded_by: User ID who uploaded the document.
        chunk_size: Size of each chunk. Defaults to 1000.
        chunk_overlap: Overlap between chunks. Defaults to 200.
    
    Returns:
        List of Document objects (chunks).
    """
    # Read file content
    content = read_file_content(file_path)
    
    # Chunk content
    chunks = _chunk_text(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    # Create Document objects
    documents = []
    for i, chunk in enumerate(chunks):
        metadata = {
            "document_id": document_id,
            "filename": filename,
            "document_type": document_type,
            "uploaded_by": uploaded_by,
            "chunk_index": i,
            "total_chunks": len(chunks),
        }
        documents.append(Document(page_content=chunk, metadata=metadata))
    
    return documents


def _chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Chunk text into smaller pieces.
    
    Args:
        text: Text to chunk.
        chunk_size: Size of each chunk. Defaults to 1000.
        chunk_overlap: Overlap between chunks. Defaults to 200.
    
    Returns:
        List of text chunks.
    """
    if not text:
        return []
    
    # Simple chunking by character count
    # TODO: Use better chunking strategy (sentence-aware, token-aware, etc.)
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary if possible
        if end < len(text):
            # Look for sentence endings within the last 100 characters
            search_start = max(0, len(chunk) - 100)
            for i in range(len(chunk) - 1, search_start - 1, -1):
                if chunk[i] in [".", "!", "?", "\n"]:
                    chunk = chunk[:i + 1]
                    end = start + len(chunk)
                    break
        
        chunks.append(chunk.strip())
        
        # Move start position with overlap
        start = end - chunk_overlap
    
    return [chunk for chunk in chunks if chunk]  # Remove empty chunks

