"""MCP server exposing internal chatbot capabilities via Spoon AI services."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import UploadFile
from fastmcp import FastMCP

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.document import DocumentType
from app.models.user import User
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.retrieval.custom_chroma import CustomChromaClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_database():
    """Ensure database session factory is available."""
    if SessionLocal is None:
        raise RuntimeError(
            "DATABASE_URL is not configured. Please set it in the environment before "
            "starting the MCP server."
        )


def _get_session():
    """Create a new database session."""
    _ensure_database()
    return SessionLocal()  # type: ignore[call-arg]


def _get_user_by_username(db, username: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise ValueError(f"User '{username}' not found.")
    return user


def _normalize_document_type(document_type: str) -> DocumentType:
    try:
        return DocumentType(document_type.lower())
    except ValueError as exc:  # pragma: no cover - defensive
        valid_types = ", ".join(dt.value for dt in DocumentType)
        raise ValueError(
            f"Invalid document_type '{document_type}'. Valid values: {valid_types}."
        ) from exc


def _serialize_document(doc, include_content: bool = True) -> Dict[str, Any]:
    metadata = dict(doc.metadata or {})
    result: Dict[str, Any] = {
        "metadata": metadata,
        "distance": metadata.get("distance"),
    }
    if include_content:
        result["content"] = doc.page_content
    return result


def _serialize_message(message) -> Dict[str, Any]:
    return {
        "id": message.id,
        "role": message.role.value,
        "content": message.content,
        "created_at": message.created_at.isoformat() if getattr(message, "created_at", None) else None,
        "updated_at": (
            message.updated_at.isoformat()
            if getattr(message, "updated_at", None)
            else None
        ),
    }


def _default_conversation_title(message: str) -> str:
    title = message.strip()
    if len(title) <= 48:
        return title or "New conversation"
    return f"{title[:45]}..."


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

instructions = (
    "MCP server cho chatbot nội bộ. Toolset bao gồm:\n"
    "- policy_txt_lookup: truy vấn snippet từ tài liệu chính sách (.txt).\n"
    "- ops_txt_lookup: truy vấn snippet từ tài liệu vận hành/kỹ thuật (.txt).\n"
    "- conversation_history_simple: lấy lịch sử hội thoại.\n"
    "- upload_document: thêm tài liệu mới.\n"
    "Các tool sử dụng chung database và vector store với backend FastAPI."
)

server = FastMCP(
    name="internal-chatbot-mcp",
    version="1.0.0",
    instructions=instructions,
)


_retrieval_client: Optional[CustomChromaClient] = None


def _get_retrieval_client() -> CustomChromaClient:
    global _retrieval_client
    if _retrieval_client is None:
        _retrieval_client = CustomChromaClient()
    return _retrieval_client


def _run_txt_lookup(
    *,
    query: str,
    top_k: int,
    document_type: DocumentType,
    include_content: bool,
) -> Dict[str, Any]:
    if not query or not query.strip():
        raise ValueError("Query must not be empty.")

    top_k = max(1, min(top_k, 10))
    retrieval_client = _get_retrieval_client()
    documents = retrieval_client.query(
        query,
        k=top_k,
        where={"document_type": {"$eq": document_type.value}},
    )

    results: List[Dict[str, Any]] = [
        _serialize_document(doc, include_content=include_content) for doc in documents
    ]

    return {
        "query": query,
        "results": results,
        "count": len(results),
        "document_type": document_type.value,
    }


@server.tool(
    name="policy_txt_lookup",
    description="Truy vấn snippet từ tài liệu chính sách nội bộ (.txt).",
    tags={"documents", "retrieval", "policy"},
)
async def policy_txt_lookup(
    query: str,
    top_k: int = 5,
    include_content: bool = True,
) -> Dict[str, Any]:
    return _run_txt_lookup(
        query=query,
        top_k=top_k,
        document_type=DocumentType.POLICY,
        include_content=include_content,
    )


@server.tool(
    name="ops_txt_lookup",
    description="Truy vấn snippet từ tài liệu vận hành/kỹ thuật (.txt).",
    tags={"documents", "retrieval", "ops"},
)
async def ops_txt_lookup(
    query: str,
    top_k: int = 5,
    include_content: bool = True,
) -> Dict[str, Any]:
    return _run_txt_lookup(
        query=query,
        top_k=top_k,
        document_type=DocumentType.OPS,
        include_content=include_content,
    )


@server.tool(
    name="upload_document",
    description=(
        "Upload tài liệu .txt lên hệ thống và lập chỉ mục vào vector database. "
        "Yêu cầu cung cấp đường dẫn file trên máy chủ MCP."
    ),
    tags={"documents", "admin"},
)
async def upload_document(
    file_path: str,
    document_type: str,
    description: Optional[str] = None,
    uploaded_by: str = "admin",
) -> Dict[str, Any]:
    """Upload a .txt document and add it to both the database and ChromaDB."""
    path = Path(file_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"File '{file_path}' does not exist.")
    if not path.is_file():
        raise ValueError(f"Path '{file_path}' is not a file.")
    if path.suffix.lower() != ".txt":
        raise ValueError("Only .txt files are supported.")

    doc_type = _normalize_document_type(document_type)

    db = _get_session()
    try:
        user = _get_user_by_username(db, uploaded_by)

        document_service = DocumentService(db)
        with path.open("rb") as file_obj:
            upload = UploadFile(filename=path.name, file=file_obj)
            document = document_service.upload_document(
                file=upload,
                document_type=doc_type,
                description=description,
                uploaded_by=user,
            )

        return {
            "id": document.id,
            "filename": document.filename,
            "document_type": document.document_type.value,
            "description": document.description,
            "uploaded_by": user.username,
            "uploaded_at": document.uploaded_at.isoformat()
            if document.uploaded_at
            else None,
        }
    finally:
        db.close()


@server.tool(
    name="conversation_history_simple",
    description="Lấy lịch sử hội thoại (tối đa 50 tin nhắn) cho một conversation.",
    tags={"chat"},
)
async def conversation_history_simple(
    conversation_id: int,
    username: str,
    limit: int = 20,
) -> Dict[str, Any]:
    """Return conversation metadata and recent messages."""
    limit = max(1, min(limit, 50))

    db = _get_session()
    try:
        user = _get_user_by_username(db, username)
        conversation_service = ConversationService(db)
        conversation = conversation_service.get_conversation(conversation_id, user)
        messages = conversation_service.get_messages(
            conversation=conversation, skip=0, limit=limit
        )

        return {
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat()
                if conversation.created_at
                else None,
                "updated_at": conversation.updated_at.isoformat()
                if conversation.updated_at
                else None,
            },
            "messages": [_serialize_message(msg) for msg in messages],
            "count": len(messages),
        }
    finally:
        db.close()




# ---------------------------------------------------------------------------
# Entrypoint helpers
# ---------------------------------------------------------------------------


def run_server():
    """Run MCP server with transport determined from environment/settings."""
    if not settings.MCP_SERVER_ENABLED:
        raise RuntimeError("MCP server is disabled. Set MCP_SERVER_ENABLED=true to run.")

    transport = os.getenv("MCP_TRANSPORT")
    if not transport:
        transport = settings.SPOON_MCP_TRANSPORT or "sse"
    transport = transport.lower()

    if transport == "stdio":
        server.run(transport="stdio")
    elif transport == "sse":
        port = settings.MCP_SERVER_PORT or 8001
        server.run(transport="sse", host=settings.MCP_SERVER_HOST or "0.0.0.0", port=port)
    elif transport == "http":
        port = settings.MCP_SERVER_PORT or 8001
        server.run(transport="http", host=settings.MCP_SERVER_HOST or "0.0.0.0", port=port)
    else:
        raise ValueError(f"Unsupported MCP transport '{transport}'. Use 'sse', 'http', or 'stdio'.")


if __name__ == "__main__":
    run_server()

