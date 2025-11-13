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
from app.services.rag_graph_service import RAGGraphService
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
    "MCP server cho chatbot nội bộ. Sử dụng các tool để truy vấn tài liệu, "
    "upload tài liệu mới, trò chuyện với bot và xem lịch sử hội thoại. "
    "Các tool hoạt động trên cùng cơ sở dữ liệu và vector store với backend FastAPI."
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


@server.tool(
    name="query_documents",
    description=(
        "Tìm kiếm tài liệu nội bộ liên quan tới một câu hỏi. "
        "Sử dụng ChromaDB với embeddings sentence-transformers."
    ),
    tags={"documents", "retrieval"},
)
async def query_documents(query: str, top_k: int = 5) -> Dict[str, Any]:
    """Query vector database for documents related to the provided question."""
    if not query or not query.strip():
        raise ValueError("Query must not be empty.")

    top_k = max(1, min(top_k, 10))
    retrieval_client = _get_retrieval_client()
    documents = retrieval_client.query(query, k=top_k)

    results: List[Dict[str, Any]] = []
    for doc in documents:
        results.append(_serialize_document(doc))

    return {
        "query": query,
        "results": results,
        "count": len(results),
    }


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
    name="chat_with_bot",
    description=(
        "Gửi tin nhắn tới chatbot nội bộ với workflow RAG của Spoon. "
        "Có thể truyền conversation_id để tiếp tục cuộc trò chuyện cũ."
    ),
    tags={"chat", "rag"},
)
async def chat_with_bot(
    message: str,
    username: str,
    conversation_id: Optional[int] = None,
    top_k: int = 5,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Send a message to the chatbot using Spoon's StateGraph RAG pipeline."""
    if not message or not message.strip():
        raise ValueError("Message must not be empty.")

    db = _get_session()
    try:
        user = _get_user_by_username(db, username)
        conversation_service = ConversationService(db)

        if conversation_id is not None:
            conversation = conversation_service.get_conversation(conversation_id, user)
        else:
            conversation = conversation_service.create_conversation(
                user=user,
                title=title or _default_conversation_title(message),
            )
            conversation_id = conversation.id

        rag_service = RAGGraphService(db, conversation_service)
        result = await rag_service.generate_response(
            user_query=message,
            conversation_id=conversation_id,
            user=user,
            top_k=top_k,
        )

        assistant_message = result.get("assistant_message")
        user_message = result.get("user_message")

        response_payload: Dict[str, Any] = {
            "conversation_id": conversation_id,
            "response": result.get("response", ""),
            "provider_used": result.get("provider_used"),
            "assistant_message": (
                _serialize_message(assistant_message) if assistant_message else None
            ),
            "user_message": (
                _serialize_message(user_message) if user_message else None
            ),
        }

        return response_payload
    finally:
        db.close()


@server.tool(
    name="get_conversation_history",
    description="Lấy lịch sử hội thoại (tối đa 100 tin nhắn) cho một conversation.",
    tags={"chat"},
)
async def get_conversation_history(
    conversation_id: int,
    username: str,
    limit: int = 50,
) -> Dict[str, Any]:
    """Return conversation metadata and recent messages."""
    limit = max(1, min(limit, 100))

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
    """Run MCP server with transport determined from environment."""
    if not settings.MCP_SERVER_ENABLED:
        raise RuntimeError("MCP server is disabled. Set MCP_SERVER_ENABLED=true to run.")

    transport = os.getenv("MCP_TRANSPORT", "http")

    if transport == "stdio":
        server.run(transport="stdio")
    else:
        # Default: HTTP transport for local testing
        port = settings.MCP_SERVER_PORT or 8001
        server.run(transport="http", host="0.0.0.0", port=port)


if __name__ == "__main__":
    run_server()

