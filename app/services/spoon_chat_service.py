"""High-level chat service orchestrating Spoon agent and fallback RAG graph."""

from __future__ import annotations

import logging
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.models.message import MessageRole
from app.models.user import User
from app.services.conversation_service import ConversationService
from app.services.spoon_graph_service import SpoonGraphService

logger = logging.getLogger(__name__)


class SpoonChatService:
    """Chat orchestration service using Spoon agent as entry point."""

    def __init__(
        self,
        db: Session,
        conversation_service: ConversationService,
    ) -> None:
        self.db = db
        self.conversation_service = conversation_service
        self.spoon_graph_service = SpoonGraphService()

    async def send_message(
        self,
        *,
        conversation_id: int,
        message: str,
        user: User,
        top_k: int = 5,
    ) -> Dict[str, object]:
        """Process a chat message using Spoon agent then fallback."""
        conversation = self.conversation_service.get_conversation(conversation_id, user)

        if not self.spoon_graph_service.enabled:
            logger.warning("Spoon graph service disabled. Returning error response.")
            return self._error_response(
                conversation=conversation,
                user_message=message,
                error_text="Xin lỗi, tôi không thể xử lý yêu cầu này ngay bây giờ.",
                provider="spoon-error",
                metadata={"error": "graph-disabled"},
            )

        graph_result = await self.spoon_graph_service.run(
            user_query=message,
            username=user.username,
            top_k=top_k,
            rewrite=True,
        )

        if graph_result.get("response"):
            logger.info(
                "Spoon graph returned response via %s",
                graph_result.get("provider_used"),
            )
            user_message, assistant_message = self._save_conversation_turn(
                conversation, message, graph_result["response"]  # type: ignore[index]
            )
            return {
                "response": graph_result["response"],
                "user_message": user_message,
                "assistant_message": assistant_message,
                "provider_used": graph_result.get("provider_used") or "spoon-graph",
                "spoon_agent_metadata": graph_result.get("metadata"),
            }

        error_msg = graph_result.get("error") or "graph-no-answer"
        logger.warning("Spoon graph could not answer (%s).", error_msg)
        return self._error_response(
            conversation=conversation,
            user_message=message,
            error_text="Xin lỗi, tôi không tìm thấy thông tin phù hợp cho câu hỏi này.",
            provider="spoon-error",
            metadata={
                "error": error_msg,
                "intent": graph_result.get("metadata", {}).get("intent") if isinstance(graph_result.get("metadata"), dict) else None,
            },
        )

    @staticmethod
    def _format_history(messages) -> str:
        if not messages:
            return "Chưa có hội thoại trước đó."

        parts = []
        for msg in messages:
            speaker = "Người dùng" if msg.role == MessageRole.USER else "Chatbot"
            parts.append(f"{speaker}: {msg.content}")
        return "\n".join(parts)

    def _save_conversation_turn(
        self,
        conversation,
        user_message: str,
        assistant_message: str,
    ):
        user_msg = self.conversation_service.create_message(
            conversation,
            user_message,
            MessageRole.USER,
        )
        assistant_msg = self.conversation_service.create_message(
            conversation,
            assistant_message,
            MessageRole.ASSISTANT,
        )
        return user_msg, assistant_msg

    def _error_response(
        self,
        *,
        conversation,
        user_message: str,
        error_text: str,
        provider: str,
        metadata: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        user_msg, assistant_msg = self._save_conversation_turn(
            conversation,
            user_message,
            error_text,
        )
        return {
            "response": error_text,
            "user_message": user_msg,
            "assistant_message": assistant_msg,
            "provider_used": provider,
            "spoon_agent_metadata": metadata or {},
        }

