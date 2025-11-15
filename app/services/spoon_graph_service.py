"""Lightweight policy/ops graph orchestrating MCP tool calls."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from spoon_ai.llm.manager import get_llm_manager
from spoon_ai.schema import Message
from spoon_ai.tools.mcp_tool import MCPTool

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProviderPreference:
    """Represents one LLM provider option with optional overrides (model, etc.)."""

    provider: Optional[str]
    label: str
    kwargs: Dict[str, Any] = field(default_factory=dict)


class SpoonGraphService:
    """High-level orchestrator that routes queries to policy/ops MCP tools."""

    SUPPORTED_LLM_PROVIDERS = {"gemini", "openai", "anthropic", "deepseek", "openrouter"}

    def __init__(self) -> None:
        self.enabled = bool(settings.SPOON_AGENT_ENABLED and settings.MCP_SERVER_ENABLED)
        self._timeout = max(30, settings.SPOON_AGENT_TIMEOUT or 90)
        self._tools = self._build_mcp_tools()
        self.llm_manager = self._init_llm_manager()
        self.llm_provider_chain = self._load_llm_provider_chain()

    def _init_llm_manager(self):
        try:
            return get_llm_manager()
        except Exception as exc:
            logger.warning("LLM manager not available for graph summaries: %s", exc)
            return None

    def _load_llm_provider_chain(self) -> List[ProviderPreference]:
        chain = settings.SPOON_LLM_PROVIDER_CHAIN or os.getenv("SPOON_LLM_PROVIDER_CHAIN")
        if chain:
            preferences: List[ProviderPreference] = []
            for item in chain.split(","):
                pref = self._parse_provider_entry(item)
                if pref:
                    preferences.append(pref)
            if preferences:
                labels = [pref.label for pref in preferences]
                logger.info("Using custom LLM provider chain: %s", labels)
                return preferences
        return self._default_llm_chain()

    def _default_llm_chain(self) -> List[ProviderPreference]:
        """Fallback provider chain if env not specified."""
        preferred_models = [
            os.getenv("GEMINI_MODEL") or getattr(settings, "GEMINI_MODEL", None),
            "gemini-2.0-flash",
            "gemini-1.5-pro-latest",
        ]
        chain: List[ProviderPreference] = []
        seen: set[str] = set()
        for model in preferred_models:
            if not model:
                continue
            key = model.lower()
            if key in seen:
                continue
            seen.add(key)
            chain.append(
                ProviderPreference(
                    provider="gemini",
                    label=model,
                    kwargs={"model": model},
                )
            )
        if not chain:
            chain.append(ProviderPreference(provider="gemini", label="gemini-2.5-pro"))
        return chain

    def _parse_provider_entry(self, raw_value: str) -> Optional[ProviderPreference]:
        token = (raw_value or "").strip()
        if not token:
            return None

        normalized = token.lower()

        if normalized in {"default", "auto"}:
            return ProviderPreference(provider=None, label=token)

        # Format: provider:model
        if ":" in token:
            head, tail = token.split(":", 1)
            provider_name = head.strip().lower()
            if provider_name in self.SUPPORTED_LLM_PROVIDERS:
                kwargs: Dict[str, Any] = {}
                model = tail.strip()
                if model:
                    kwargs["model"] = model
                return ProviderPreference(provider=provider_name, label=token, kwargs=kwargs)

        # Handle explicit provider names (no model override)
        if normalized in self.SUPPORTED_LLM_PROVIDERS:
            return ProviderPreference(provider=normalized, label=token)

        # Handle common shorthand (e.g., gemini-2.5-flash)
        if normalized.startswith("gemini"):
            return ProviderPreference(provider="gemini", label=token, kwargs={"model": token})

        logger.warning(
            "LLM provider entry '%s' is not recognized. Supported providers: %s. Skipping.",
            token,
            ", ".join(sorted(self.SUPPORTED_LLM_PROVIDERS)),
        )
        return None

    def _build_mcp_tools(self) -> Dict[str, MCPTool]:
        mcp_config = {
            "url": settings.spoon_mcp_url,
            "transport": (settings.SPOON_MCP_TRANSPORT or "sse").lower(),
            "timeout": self._timeout,
            "max_retries": 2,
            "health_check_interval": 120,
        }
        tools = {}
        try:
            tools["policy_txt_lookup"] = MCPTool(
                name="policy_txt_lookup",
                description="Lookup chính sách nội bộ.",
                mcp_config=mcp_config.copy(),
            )
            tools["ops_txt_lookup"] = MCPTool(
                name="ops_txt_lookup",
                description="Lookup runbook vận hành/kỹ thuật.",
                mcp_config=mcp_config.copy(),
            )
            tools["conversation_history_simple"] = MCPTool(
                name="conversation_history_simple",
                description="Lấy lịch sử hội thoại.",
                mcp_config=mcp_config.copy(),
            )
        except Exception as exc:
            logger.error("Failed to initialize MCP tools for graph service: %s", exc)
            self.enabled = False
        return tools

    async def _call_llm(self, messages: List[Message], *, purpose: str) -> Tuple[Optional[str], Optional[str]]:
        """Call LLM with fallback chain."""
        if not self.llm_manager:
            return None, None

        providers = self.llm_provider_chain or self._default_llm_chain()
        for preference in providers:
            try:
                kwargs = dict(preference.kwargs) if preference.kwargs else {}
                provider_name = preference.provider
                if provider_name:
                    kwargs["provider"] = provider_name
                response = await self.llm_manager.chat(messages, **kwargs)
                content = (response.content or "").strip()
                if content:
                    reported_provider = response.provider or preference.label or provider_name or "default"
                    return content, reported_provider
            except Exception as exc:  # pragma: no cover - defensive
                label = preference.label or provider_name or "default"
                logger.warning("LLM provider %s failed for %s: %s", label, purpose, exc)
                continue
        return None, None

    @staticmethod
    def _normalize_text(value: str) -> str:
        return value.lower().strip()

    async def _detect_intent(self, user_query: str) -> Tuple[str, Optional[str], str]:
        intent, provider = await self._detect_intent_llm(user_query)
        return intent, provider or "llm", user_query

    def _plan_tools(self, intent: str) -> List[str]:
        if intent == "policy":
            return ["policy_txt_lookup"]
        if intent == "ops":
            return ["ops_txt_lookup"]
        return ["policy_txt_lookup", "ops_txt_lookup"]

    async def _rewrite_query(self, user_query: str) -> Tuple[str, Optional[str]]:
        if not self.llm_manager:
            return user_query, None
        # only rewrite if question is long or informal
        if len(user_query.split()) <= 4:
            return user_query, None
        system_prompt = (
            "Bạn là trợ lý chuẩn hóa câu hỏi để thuận tiện cho việc tìm kiếm tài liệu nội bộ. "
            "Hãy diễn đạt lại câu hỏi ngắn gọn, đầy đủ ý chính, dùng từ khóa rõ ràng. "
            "Chỉ trả về câu hỏi đã chuẩn hóa."
        )
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Câu hỏi gốc: {user_query}"),
        ]
        rewritten, provider = await self._call_llm(messages, purpose="query-rewrite")
        if rewritten:
            return rewritten, provider
        return user_query, None

    async def _detect_intent_llm(self, user_query: str) -> Tuple[str, Optional[str]]:
        if not self.llm_manager:
            return "ambiguous", None
        system_prompt = (
            "Bạn là bộ phân loại ý định. Hãy liệt kê TẤT CẢ các ý định thuộc các lớp sau,"
            " dùng dấu phẩy để ngăn cách:\n"
            "- policy: câu hỏi về chính sách, phúc lợi, nhân sự, remote work, nghỉ phép...\n"
            "- ops: câu hỏi về vận hành, kỹ thuật, deploy, quy trình backend...\n"
            "Nếu câu hỏi thuộc cả hai nhóm, hãy trả về 'policy,ops'. Nếu không rõ, trả về 'ambiguous'."
        )
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Câu hỏi: {user_query}"),
        ]
        content, provider = await self._call_llm(messages, purpose="intent-detection")
        cleaned = (content or "").lower().strip()
        tokens = [token.strip() for token in cleaned.split(",") if token.strip()]
        has_policy = any(token == "policy" for token in tokens)
        has_ops = any(token == "ops" for token in tokens)

        if has_policy and has_ops:
            return "ambiguous", provider
        if has_policy:
            return "policy", provider
        if has_ops:
            return "ops", provider
        return "ambiguous", provider

    async def _execute_tool(
        self,
        tool_name: str,
        query: str,
        top_k: int,
        include_content: bool,
    ) -> Tuple[str, Dict[str, Any], Optional[str]]:
        tool = self._tools.get(tool_name)
        if not tool:
            return tool_name, {}, f"Tool '{tool_name}' not initialized."

        try:
            raw_result = await tool.execute(
                query=query,
                top_k=top_k,
                include_content=include_content,
            )
            parsed = self._parse_tool_result(raw_result)
            return tool_name, parsed, None
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("MCP tool '%s' failed: %s", tool_name, exc)
            return tool_name, {}, str(exc)

    @staticmethod
    def _parse_tool_result(raw: Any) -> Dict[str, Any]:
        if raw is None:
            return {}
        if isinstance(raw, dict):
            return raw
        if hasattr(raw, "model_dump"):
            return raw.model_dump()
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"raw_text": raw}
        return {"raw": str(raw)}

    @staticmethod
    def _extract_evidence(result: Dict[str, Any]) -> List[Dict[str, Any]]:
        payload = result.get("results") or []
        evidence: List[Dict[str, Any]] = []
        for item in payload:
            metadata = item.get("metadata") or {}
            evidence.append(
                {
                    "content": item.get("content") or item.get("text") or "",
                    "metadata": metadata,
                }
            )
        return evidence

    @staticmethod
    def _distance_key(item: Dict[str, Any]) -> float:
        meta = item.get("metadata") or {}
        distance = meta.get("distance")
        if isinstance(distance, (int, float)):
            return float(distance)
        return float("inf")

    def _prioritize_evidence(
        self,
        evidence: List[Dict[str, Any]],
        tool_calls: List[str],
    ) -> List[Dict[str, Any]]:
        if not evidence:
            return evidence

        if len(tool_calls) <= 1:
            return sorted(evidence, key=self._distance_key)

        tool_to_doc = {
            "policy_txt_lookup": "policy",
            "ops_txt_lookup": "ops",
        }

        buckets: Dict[str, List[Dict[str, Any]]] = {}
        for item in evidence:
            meta = item.get("metadata") or {}
            key = meta.get("document_type") or meta.get("retrieval_tool") or "other"
            buckets.setdefault(key, []).append(item)

        for bucket in buckets.values():
            bucket.sort(key=self._distance_key)

        ordering: List[str] = []
        for tool in tool_calls:
            doc_type = tool_to_doc.get(tool)
            if doc_type and doc_type not in ordering:
                ordering.append(doc_type)
        for key in buckets.keys():
            if key not in ordering:
                ordering.append(key)

        prioritized: List[Dict[str, Any]] = []
        while True:
            added = False
            for key in ordering:
                bucket = buckets.get(key)
                if bucket:
                    prioritized.append(bucket.pop(0))
                    added = True
            if not added:
                break
        return prioritized

    def _build_citation_section(self, evidence: List[Dict[str, Any]], limit: int = 2) -> str:
        lines: List[str] = []
        for idx, item in enumerate(evidence[:limit], start=1):
            meta = item.get("metadata") or {}
            filename = meta.get("filename") or meta.get("source") or f"Tài liệu {idx}"
            section = meta.get("section") or meta.get("heading") or ""
            if section:
                lines.append(f"- {filename} › {section}")
            else:
                lines.append(f"- {filename}")
        if not lines:
            return ""
        return "\n\nNguồn:\n" + "\n".join(lines)

    def _synthesize_response(
        self,
        *,
        user_query: str,
        evidence: List[Dict[str, Any]],
        intent: str,
    ) -> Optional[str]:
        if not evidence:
            return None

        category = {
            "policy": "chính sách",
            "ops": "vận hành/kỹ thuật",
        }.get(intent, "tài liệu nội bộ")

        lines = []
        for idx, item in enumerate(evidence[:2], start=1):
            meta = item.get("metadata") or {}
            filename = meta.get("filename") or meta.get("source") or f"Tài liệu {idx}"
            snippet = (item.get("content") or "").strip()
            if snippet:
                lines.append(f"- {filename}: {snippet}")
        if not lines:
            return None

        extra = ""
        if len(evidence) > len(lines):
            extra = "\n- (Các tài liệu khác cũng phù hợp, có thể đào sâu thêm nếu cần.)"

        return (
            f"Dựa trên tài liệu {category}, đây là thông tin liên quan đến “{user_query}”:\n"
            + "\n".join(lines)
            + extra
        )

    async def _suggest_followups_llm(self, user_query: str) -> Optional[str]:
        if not self.llm_manager:
            return None
        messages = [
            Message(
                role="system",
                content=(
                    "Bạn đang hỗ trợ nhân viên khi không tìm thấy dữ liệu. "
                    "Hãy đề xuất tối đa 2 câu hỏi liên quan hoặc hướng dẫn họ cung cấp thêm thông tin."
                ),
            ),
            Message(role="user", content=f"Tôi không tìm được dữ liệu cho câu hỏi: {user_query}"),
        ]
        suggestions, _ = await self._call_llm(messages, purpose="followup-suggestion")
        return suggestions

    async def _summarize_with_llm(
        self,
        *,
        user_query: str,
        evidence: List[Dict[str, Any]],
        intent: str,
    ) -> Tuple[Optional[str], Optional[str], str]:
        if not self.llm_manager or not evidence:
            return None, None, "snippet"

        chunks = []
        for item in evidence[:3]:
            meta = item.get("metadata") or {}
            filename = meta.get("filename") or meta.get("source") or "Tài liệu"
            section = meta.get("section") or meta.get("heading") or ""
            snippet = (item.get("content") or "").strip()
            if not snippet:
                continue
            header = f"{filename}" + (f" › {section}" if section else "")
            chunks.append(f"{header}:\n{snippet}")

        if not chunks:
            return None, None, "snippet"

        evidence_text = "\n\n".join(chunks)
        system_prompt = (
            """[VAI TRÒ & MỤC TIÊU]
                Bạn là một Trợ lý AI Hỗ trợ Nghiệp vụ Nội bộ.
                Mục tiêu cốt lõi của bạn là trả lời các câu hỏi của nhân viên một cách CHÍNH XÁC, KHÁCH QUAN và chỉ dựa trên các "snippet" thông tin được cung cấp.

                [QUY TẮC XỬ LÝ SNIPPET - CỰC KỲ QUAN TRỌNG]
                1.  **LỌC THÔNG TIN (Filter):** Các snippet được cung cấp có thể chứa thông tin thừa hoặc nhiễu. Bạn CHỈ được phép sử dụng những thông tin nào TRỰC TIẾP trả lời cho câu hỏi của người dùng. Hãy chủ động bỏ qua mọi thông tin không liên quan trong snippet.
                2.  **XỬ LÝ SAI LỆCH (Handle Irrelevance):** Nếu TOÀN BỘ nội dung snippet được cung cấp rõ ràng KHÔNG liên quan đến câu hỏi của người dùng, bạn PHẢI trả lời: "Xin lỗi, tôi không tìm thấy thông tin liên quan đến [chủ đề câu hỏi] trong tài liệu được cung cấp."
                3.  **XỬ LÝ THIẾU THÔNG TIN (Handle Missing Parts):** Nếu câu hỏi của người dùng có nhiều ý, và snippet chỉ trả lời được một phần, hãy trả lời phần tìm thấy và nêu rõ ràng: "Về phần [ý còn thiếu], tôi không tìm thấy thông tin trong tài liệu."

                [QUY TẮC SUY LUẬN & CHỐNG BỊA ĐẶT (Inference & Anti-Hallucidation)]
                1.  **CẤM SUY DIỄN NGHIỆP VỤ:** TUYỆT ĐỐI KHÔNG suy diễn về các chính sách phức tạp, con số tài chính, hoặc các quy trình nghiệp vụ (Ví dụ: KHÔNG được đoán "ai là người phê duyệt", "tôi có được duyệt X không?", "lương của tôi sẽ tăng bao nhiêu?").
                2.  **CHO PHÉP SUY LUẬN LOGIC ĐƠN GIẢN:** Bạn **ĐƯỢC PHÉP** và **NÊN** thực hiện các suy luận logic trực tiếp, hiển nhiên (common-sense) từ thông tin được cung cấp.
                    * **VÍ DỤ (Quan trọng):** Khi snippet nói "Làm việc từ Thứ 2 đến Thứ 6" và người dùng hỏi "Thứ 7 có nghỉ không?", bạn được phép suy luận và trả lời "Có, theo tài liệu, ngày làm việc là Thứ 2 - Thứ 6, vì vậy Thứ 7 là ngày nghỉ."
                3.  **TRUNG THỰC KHI SUY LUẬN:** Khi thực hiện suy luận (như các ví dụ trên), hãy cho thấy cơ sở của bạn một cách ngắn gọn, tự nhiên. (Ví dụ: "Vì công ty làm việc từ T2-T6, nên T7 là ngày nghỉ...").

                [QUY TẮC VỀ CÂU TRẢ LỜI]
                1.  **TÍNH BAO QUÁT (Comprehensive):** Luôn đảm bảo trả lời ĐẦY ĐỦ tất cả các ý/phần trong câu hỏi của người dùng.
                2.  **TÍNH LINH HOẠT (Flexible):** Tùy chỉnh độ dài và chi tiết dựa trên ý định của người dùng (súc tích cho câu hỏi "Là gì", chi tiết cho câu hỏi "Như thế nào").
                3.  **TÍNH TỰ NHIÊN (Natural Tone):** Viết lại câu trả lời một cách tự nhiên. KHÔNG sao chép nguyên văn toàn bộ snippet.
                4.  **TRÍCH DẪN NGUỒN (Citation):** Luôn cố gắng nêu nguồn tài liệu nếu nó được cung cấp trong metadata của snippet.
                    * **Ưu tiên:** Sử dụng tên tài liệu/chính sách. (Ví dụ: "Theo Sổ tay Văn hóa,..." hoặc "Theo Chính sách Nghỉ phép năm 2025,...")
                    * **Không bịa đặt nguồn:** Nếu không có tên tài liệu cụ thể trong metadata, chỉ cần trả lời thông tin, không cần bịa ra nguồn.
                    * **Tránh:** Không dùng các từ chung chung như "theo snippet" hay "theo trích đoạn được cung cấp"."""
        )
        user_prompt = (
            f"Câu hỏi: {user_query}\n\n"
            f"Loại câu hỏi: {intent or 'chung'}\n\n"
            f"Tài liệu thu được:\n{evidence_text}\n\n"
            "Yêu cầu: Viết câu trả lời hoàn chỉnh, đủ ý quan trọng (số liệu, điều kiện,"
            " bước thực hiện). Không vượt quá 6 câu."
        )

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt),
        ]

        summary, provider = await self._call_llm(messages, purpose="answer-summary")
        if not summary:
            return None, provider, "snippet"

        return (
            summary + self._build_citation_section(evidence),
            provider,
            "llm-summary",
        )

    async def run(
        self,
        *,
        user_query: str,
        username: str,
        top_k: int = 5,
        rewrite: bool = False,
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {"error": "Spoon graph is disabled."}

        rewritten_query, rewrite_provider = await self._rewrite_query(user_query) if rewrite else (user_query, None)
        intent, intent_source, intent_query = await self._detect_intent(rewritten_query)
        plan = self._plan_tools(intent)

        tasks = [
            self._execute_tool(
                tool_name=tool_name,
                query=rewritten_query,
                top_k=top_k,
                include_content=True,
            )
            for tool_name in plan
        ]

        results = await asyncio.gather(*tasks)

        evidence: List[Dict[str, Any]] = []
        tool_calls: List[str] = []
        tool_runs: List[Dict[str, Any]] = []

        for tool_name, payload, error in results:
            if error:
                tool_runs.append({"tool": tool_name, "error": error})
                continue

            tool_calls.append(tool_name)
            extracted = self._extract_evidence(payload)
            document_type = (payload or {}).get("document_type")
            if extracted:
                for item in extracted:
                    meta = item.setdefault("metadata", {})
                    if document_type and not meta.get("document_type"):
                        meta["document_type"] = document_type
                    meta.setdefault("retrieval_tool", tool_name)
                evidence.extend(extracted)
            tool_runs.append(
                {
                    "tool": tool_name,
                    "result_count": len(extracted),
                    "query": user_query,
                }
            )

        answer_mode = "snippet-fallback"
        prioritized_evidence = self._prioritize_evidence(evidence, tool_calls)
        summary_text, summary_provider, summary_mode = await self._summarize_with_llm(
            user_query=user_query,
            evidence=prioritized_evidence,
            intent=intent if intent in {"policy", "ops"} else self._infer_provider(tool_calls),
        )
        response = summary_text
        if not response:
            response = self._synthesize_response(
                user_query=user_query,
                evidence=prioritized_evidence,
                intent=intent if intent in {"policy", "ops"} else self._infer_provider(tool_calls),
            )
        else:
            answer_mode = summary_mode

        provider_used = self._infer_provider(tool_calls)

        if not response:
            suggestions = await self._suggest_followups_llm(user_query)
            return {
                "error": "graph-no-answer",
                "metadata": {
                    "intent": intent,
                    "tool_runs": tool_runs,
                    "rewritten_query": rewritten_query if rewrite else None,
                    "suggestions": suggestions,
                },
            }

        return {
            "response": response,
            "evidence": evidence,
            "provider_used": provider_used,
            "metadata": {
                "intent": intent,
                "tool_calls": tool_calls,
                "tool_runs": tool_runs,
                "requested_by": username,
                "answer_mode": answer_mode,
                "intent_source": intent_source,
                "intent_query": intent_query,
                "rewritten_query": rewritten_query if rewrite else None,
                "rewrite_provider": rewrite_provider,
                "summary_provider": summary_provider,
            },
        }

    @staticmethod
    def _infer_provider(tool_calls: List[str]) -> str:
        if not tool_calls:
            return "spoon-graph"
        if all(call == "policy_txt_lookup" for call in tool_calls):
            return "spoon-policy"
        if all(call == "ops_txt_lookup" for call in tool_calls):
            return "spoon-ops"
        return "spoon-graph"

