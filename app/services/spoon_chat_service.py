"""High-level chat service orchestrating Spoon agent and fallback RAG graph."""

from __future__ import annotations

import logging
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.models.message import MessageRole
from app.models.user import User
from app.services.conversation_service import ConversationService
from app.services.spoon_agent_service import get_spoon_agent_service

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
        self.spoon_agent_service = get_spoon_agent_service()

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

        spoon_result = await self._run_spoon_agent(
            conversation=conversation,
            user=user,
            message=message,
            top_k=top_k,
        )

        if spoon_result.get("response"):
            logger.info("Spoon agent returned response via %s", spoon_result.get("provider_used"))
            user_message = self.conversation_service.create_message(
                conversation,
                message,
                MessageRole.USER,
            )
            assistant_message = self.conversation_service.create_message(
                conversation,
                spoon_result["response"],  # type: ignore[index]
                MessageRole.ASSISTANT,
            )

            result = {
                "response": spoon_result["response"],
                "user_message": user_message,
                "assistant_message": assistant_message,
                "provider_used": spoon_result.get("provider_used") or "spoon-agent",
                "spoon_agent_metadata": spoon_result.get("metadata"),
            }
            return result

        logger.warning("Spoon agent unavailable (%s). Returning fallback message.", spoon_result.get("error"))
        error_response = "Xin lỗi, tôi không thể trả lời câu hỏi này vào lúc này."
        user_message = self.conversation_service.create_message(
            conversation,
            message,
            MessageRole.USER,
        )
        assistant_message = self.conversation_service.create_message(
            conversation,
            error_response,
            MessageRole.ASSISTANT,
        )
        return {
            "response": error_response,
            "user_message": user_message,
            "assistant_message": assistant_message,
            "provider_used": "spoon-error",
            "spoon_agent_metadata": {"error": spoon_result.get("error")},
        }

    async def _run_spoon_agent(
        self,
        *,
        conversation,
        user: User,
        message: str,
        top_k: int,
    ) -> Dict[str, object]:
        """Execute Spoon agent with minimal context. Returns response or error."""
        if not self.spoon_agent_service.enabled:
            return {"error": "Spoon agent disabled in configuration."}

        history = self.conversation_service.get_recent_messages(conversation, limit=10)
        history_str = self._format_history(history)

        try:
            result = await self.spoon_agent_service.run_mcp_agent(
                user_query=message,
                username=user.username,
                conversation_id=conversation.id,
                context="",
                conversation_history=history_str,
                retrieved_documents=[],
                top_k=top_k,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Spoon agent execution failed: %s", exc, exc_info=True)
            return {"error": str(exc)}

        if result.get("response"):
            metadata = result.get("metadata") or {}
            provider = self._infer_provider(metadata)
            return {
                "response": result["response"],
                "metadata": metadata,
                "provider_used": provider,
            }

        return {"error": result.get("error", "Unknown Spoon agent error")}

    @staticmethod
    def _format_history(messages) -> str:
        if not messages:
            return "Chưa có hội thoại trước đó."

        parts = []
        for msg in messages:
            speaker = "Người dùng" if msg.role == MessageRole.USER else "Chatbot"
            parts.append(f"{speaker}: {msg.content}")
        return "\n".join(parts)

    @staticmethod
    def _infer_provider(metadata: Dict[str, object]) -> str:
        tool_calls = metadata.get("tool_calls") or []
        if isinstance(tool_calls, list):
            if any(call == "vector_search_simple" for call in tool_calls):
                return "spoon-vector"
            if any(call == "upload_document" for call in tool_calls):
                return "spoon-upload"
        return "spoon-agent"

