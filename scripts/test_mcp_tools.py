"""
Simple helper to call MCP tools (policy_txt_lookup, ops_txt_lookup) via FastMCP client.
"""

import argparse
import asyncio
import json
from typing import Any, Dict

from fastmcp.client import Client


async def _call_tool(server: str, tool: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    client = Client(server)
    async with client:
        result = await client.call_tool(tool, payload)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Call MCP tools for testing.")
    parser.add_argument(
        "--server",
        default="http://localhost:8001/sse",
        help="MCP server endpoint (include path, e.g. http://localhost:8001/sse).",
    )
    parser.add_argument(
        "--tool",
        choices=["policy_txt_lookup", "ops_txt_lookup", "conversation_history_simple"],
        default="policy_txt_lookup",
        help="Tool name to call.",
    )
    parser.add_argument(
        "--query",
        default="nghỉ phép",
        help="Query string for policy/ops lookup tools.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of snippets to retrieve.",
    )
    parser.add_argument(
        "--include-content",
        action="store_true",
        help="Include full snippet content in the response.",
    )
    parser.add_argument(
        "--conversation-id",
        type=int,
        help="Conversation ID (conversation_history_simple only).",
    )
    parser.add_argument(
        "--username",
        default="admin",
        help="Username (conversation_history_simple only).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Limit messages (conversation_history_simple only).",
    )
    args = parser.parse_args()

    if args.tool in {"policy_txt_lookup", "ops_txt_lookup"}:
        payload: Dict[str, Any] = {
            "query": args.query,
            "top_k": args.top_k,
            "include_content": args.include_content,
        }
    elif args.tool == "conversation_history_simple":
        if args.conversation_id is None:
            parser.error("--conversation-id is required for conversation_history_simple")
        payload = {
            "conversation_id": args.conversation_id,
            "username": args.username,
            "limit": args.limit,
        }
    else:
        payload = {}

    result = asyncio.run(_call_tool(args.server, args.tool, payload))

    try:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except TypeError:
        # FastMCP returns CallToolResult; try model_dump if available
        if hasattr(result, "model_dump"):
            print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
        else:
            print(result)


if __name__ == "__main__":
    main()

