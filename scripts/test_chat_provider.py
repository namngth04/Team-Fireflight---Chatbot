"""
Helper script to send a chat message and inspect provider_used/metadata.
"""

import argparse
import json
import sys
from typing import Any, Dict, Optional

import requests


def login(base_url: str, username: str, password: str) -> str:
    response = requests.post(
        f"{base_url}/api/auth/login",
        json={"username": username, "password": password},
        timeout=30,
    )
    if response.status_code != 200:
        print("Login failed:", response.text)
        sys.exit(1)
    return response.json()["access_token"]


def ensure_conversation(
    base_url: str,
    token: str,
    conversation_id: Optional[int],
    title: str,
) -> int:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    if conversation_id is not None:
        resp = requests.get(
            f"{base_url}/api/chat/conversations/{conversation_id}",
            headers=headers,
            timeout=30,
        )
        if resp.status_code == 200:
            return conversation_id
        print(
            f"Conversation {conversation_id} not accessible (status {resp.status_code}). Creating new one..."
        )

    resp = requests.post(
        f"{base_url}/api/chat/conversations",
        headers=headers,
        json={"title": title or "Test conversation"},
        timeout=30,
    )
    if resp.status_code != 201:
        print("Failed to create conversation:", resp.text)
        sys.exit(1)
    conv = resp.json()
    print(f"Created conversation ID {conv['id']}")
    return conv["id"]


def send_message(
    base_url: str,
    token: str,
    conversation_id: int,
    message: str,
) -> Dict[str, Any]:
    response = requests.post(
        f"{base_url}/api/chat/conversations/{conversation_id}/messages",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"content": message},
        timeout=60,
    )
    if response.status_code != 200:
        print("Chat request failed:", response.text)
        sys.exit(1)
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send chat message and inspect provider_used/metadata."
    )
    parser.add_argument("--base-url", default="http://localhost:8000", help="FastAPI base URL.")
    parser.add_argument("--username", default="admin", help="Username for login.")
    parser.add_argument("--password", default="admin123", help="Password for login.")
    parser.add_argument("--conversation-id", type=int, help="Conversation ID to reuse.")
    parser.add_argument(
        "--conversation-title",
        default="Test conversation",
        help="Title when creating a new conversation.",
    )
    parser.add_argument("--message", required=True, help="Message content to send.")
    args = parser.parse_args()

    token = login(args.base_url, args.username, args.password)
    conv_id = ensure_conversation(
        args.base_url, token, args.conversation_id, args.conversation_title
    )
    result = send_message(args.base_url, token, conv_id, args.message)

    print("conversation_id:", conv_id)
    print("provider_used:", result.get("provider_used"))
    metadata = result.get("spoon_agent_metadata") or result.get("metadata") or {}
    print("metadata:", json.dumps(metadata, ensure_ascii=False, indent=2))

    resp_obj = result.get("response") or {}
    preview = ""
    if isinstance(resp_obj, dict):
        preview = resp_obj.get("content") or resp_obj.get("response") or ""
    elif isinstance(resp_obj, str):
        preview = resp_obj
    print("response preview:", preview[:200])


if __name__ == "__main__":
    main()

