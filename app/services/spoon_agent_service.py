"""Utility service to run Spoon MCP agents inside the backend."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from spoon_ai.agents.spoon_react_mcp import SpoonReactMCP
from spoon_ai.schema import Message, Role
from spoon_ai.tools.mcp_tool import MCPTool

from app.core.config import settings

logger = logging.getLogger(__name__)


class SpoonAgentService:
    """Wraps a SpoonReactMCP agent configured for the internal MCP server."""

    TOOL_DEFINITIONS = [
        ("vector_search_simple", "Truy vấn snippet từ ChromaDB để lấy thông tin nền."),
        ("conversation_history_simple", "Lấy lịch sử hội thoại để duy trì ngữ cảnh."),
        ("upload_document", "Tải tài liệu .txt và lập chỉ mục vào hệ thống."),
    ]

    def __init__(self) -> None:
        self.enabled = bool(settings.SPOON_AGENT_ENABLED and settings.MCP_SERVER_ENABLED)
        self._agent: Optional[SpoonReactMCP] = None
        self._run_lock = asyncio.Lock()
        self._timeout = max(30, settings.SPOON_AGENT_TIMEOUT or 90)

        if self.enabled:
            self._initialize_agent()
        else:
            logger.info("Spoon MCP agent is disabled via configuration.")

    def _initialize_agent(self) -> None:
        """Instantiate SpoonReactMCP with MCP tools."""
        try:
            mcp_config = {
                "url": settings.spoon_mcp_url,
                "transport": (settings.SPOON_MCP_TRANSPORT or "sse").lower(),
                "timeout": self._timeout,
            }

            tools: List[MCPTool] = []
            for name, description in self.TOOL_DEFINITIONS:
                tool = MCPTool(
                    name=name,
                    description=description,
                    mcp_config=mcp_config.copy(),
                )
                tools.append(tool)

            system_prompt = (
                "Bạn là Spoon MCP agent hỗ trợ chatbot nội bộ. "
                "Bạn có quyền sử dụng các tool sau:\n"
                "- vector_search_simple(query, top_k): lấy snippet tài liệu.\n"
                "- conversation_history_simple(conversation_id, username, limit): lấy lịch sử.\n"
                "- upload_document(file_path, document_type, description, uploaded_by): thêm tài liệu.\n\n"
                "Hãy trả lời trực tiếp, ngắn gọn bằng tiếng Việt cho câu hỏi hiện tại. "
                "Chỉ sử dụng thông tin lấy được từ các tool của bạn; không nhắc lại câu hỏi trước "
                "và không thêm phần tổng kết các câu hỏi khác nếu người dùng không yêu cầu. "
                "Nếu không tìm thấy dữ liệu chính xác, hãy chọn thông tin gần nhất, nêu rõ nguồn/snippet "
                "đang dựa vào và giải thích rằng đó là suy luận. Nếu hoàn toàn không có dữ liệu liên quan, "
                "hãy nói rõ là không tìm thấy."
            )

            self._agent = SpoonReactMCP(
                name="chatbot_spoon_mcp_agent",
                system_prompt=system_prompt,
                max_steps=settings.SPOON_AGENT_MAX_STEPS,
                tools=tools,
                x402_enabled=False,
                tool_choice="auto",
            )
            logger.info(
                "Initialized Spoon MCP agent with transport %s at %s",
                mcp_config["transport"],
                mcp_config["url"],
            )
        except Exception as exc:  # pragma: no cover - defensive
            self.enabled = False
            logger.error("Failed to initialize Spoon MCP agent: %s", exc, exc_info=True)

    def _reset_agent_state(self) -> None:
        if not self._agent:
            return
        try:
            self._agent.memory.clear()
        except Exception:
            pass
        self._agent.tool_calls = []
        self._agent.last_tool_error = None

    @staticmethod
    def _format_documents(documents: List[Any]) -> str:
        if not documents:
            return "Không có trích đoạn tài liệu nào được cung cấp."

        snippets = []
        for idx, doc in enumerate(documents[:3], start=1):
            metadata = getattr(doc, "metadata", {}) or {}
            filename = metadata.get("filename") or metadata.get("source") or "Tài liệu"
            snippet = (getattr(doc, "page_content", "") or "")[:500].strip()
            snippets.append(f"[Tài liệu {idx}] {filename}: {snippet}")
        return "\n\n".join(snippets)

    def _build_prompt(
        self,
        *,
        user_query: str,
        username: str,
        conversation_id: Optional[int],
        context: str,
        conversation_history: str,
        retrieved_documents: List[Any],
        top_k: int,
    ) -> str:
        doc_summary = self._format_documents(retrieved_documents)
        convo_ref = conversation_id if conversation_id is not None else "conversation mới"

        return (
            f"Người dùng: {username}\n"
            f"Conversation: {convo_ref}\n"
            f"Số tài liệu gợi ý (top_k): {top_k}\n\n"
            "Ngữ cảnh tổng hợp từ pipeline RAG:\n"
            f"{context.strip() or doc_summary}\n\n"
            "Lịch sử hội thoại gần đây:\n"
            f"{conversation_history}\n\n"
            f"Yêu cầu mới của người dùng:\n{user_query}\n\n"
            "Hãy dùng các MCP tool đã được liệt kê trong system prompt để hoàn thành nhiệm vụ. "
            "Nếu cần trả lời trực tiếp, hãy giải thích dựa trên dữ liệu thu được từ tool."
        )

    def _extract_latest_assistant_message(self) -> Optional[str]:
        if not self._agent:
            return None

        for message in reversed(self._agent.memory.messages):
            if isinstance(message, Message) and message.role == Role.ASSISTANT and message.content:
                return message.content
        return None

    async def run_mcp_agent(
        self,
        *,
        user_query: str,
        username: str,
        conversation_id: Optional[int],
        context: str,
        conversation_history: str,
        retrieved_documents: List[Any],
        top_k: int,
    ) -> Dict[str, Any]:
        """Execute the Spoon MCP agent and return response / metadata."""
        if not self.enabled or not self._agent:
            return {"error": "Spoon MCP agent is not enabled."}

        prompt = self._build_prompt(
            user_query=user_query,
            username=username,
            conversation_id=conversation_id,
            context=context,
            conversation_history=conversation_history,
            retrieved_documents=retrieved_documents,
            top_k=top_k,
        )

        async with self._run_lock:
            self._reset_agent_state()
            try:
                run_task = self._agent.run(request=prompt)
                run_log = await asyncio.wait_for(run_task, timeout=self._timeout + 15)
                response = self._extract_latest_assistant_message() or run_log

                metadata = {
                    "tool_calls": [
                        getattr(tool_call.function, "name", None)
                        for tool_call in getattr(self._agent, "tool_calls", []) or []
                    ],
                    "last_tool_error": getattr(self._agent, "last_tool_error", None),
                    "raw_run_log": run_log,
                }

                return {"response": response, "metadata": metadata}
            except asyncio.TimeoutError as exc:
                logger.error("Spoon MCP agent timed out: %s", exc)
                return {"error": "Spoon MCP agent timed out."}
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Spoon MCP agent execution failed: %s", exc, exc_info=True)
                return {"error": str(exc)}
            finally:
                self._reset_agent_state()


_spoon_agent_service = SpoonAgentService()


def get_spoon_agent_service() -> SpoonAgentService:
    """Return the singleton Spoon agent service."""
    return _spoon_agent_service

