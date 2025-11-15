"""
Script hỗ trợ upload tài liệu mẫu (policy/ops) và kiểm tra API documents.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DOCS: Dict[str, Path] = {
    "policy": ROOT_DIR / "sample_documents" / "policy_time_off_v2.txt",
    "ops": ROOT_DIR / "sample_documents" / "ops_backend_deploy.txt",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test upload documents via FastAPI endpoints.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="FastAPI base URL.")
    parser.add_argument("--username", default="admin", help="Login username.")
    parser.add_argument("--password", default="admin", help="Login password.")

    upload_group = parser.add_argument_group("Upload options")
    upload_group.add_argument(
        "--upload-sample",
        choices=["policy", "ops", "all"],
        help="Upload tài liệu mẫu tương ứng (policy/ops). Chọn 'all' để upload cả hai.",
    )
    upload_group.add_argument(
        "--file",
        type=Path,
        help="Đường dẫn file .txt tùy ý để upload.",
    )
    upload_group.add_argument(
        "--document-type",
        choices=["policy", "ops"],
        help="Loại tài liệu khi dùng --file.",
    )
    upload_group.add_argument(
        "--description",
        help="Mô tả cho tài liệu khi upload.",
    )

    parser.add_argument("--list", action="store_true", help="Liệt kê tất cả documents.")
    parser.add_argument("--get", type=int, dest="document_id", help="Lấy chi tiết document theo ID.")
    return parser.parse_args()


def login(base_url: str, username: str, password: str) -> str:
    """Đăng nhập và trả về JWT token."""
    print(f"🔐 Đang đăng nhập ({username}) ...")
    response = requests.post(
        f"{base_url}/api/auth/login",
        json={"username": username, "password": password},
        timeout=30,
    )
    if response.status_code != 200:
        print(f"❌ Lỗi đăng nhập: {response.status_code}")
        print(response.text)
        sys.exit(1)
    token = response.json()["access_token"]
    print("✅ Đăng nhập thành công.\n")
    return token


def upload_document(
    base_url: str,
    token: str,
    file_path: Path,
    document_type: str,
    description: Optional[str] = None,
) -> dict:
    """Upload tài liệu và trả về JSON document."""
    print(f"📄 Upload file: {file_path} (type={document_type})")

    if not file_path.exists():
        print(f"❌ File không tồn tại: {file_path}")
        sys.exit(1)

    if description is None:
        description = f"Tài liệu {document_type} - {file_path.name}"

    with open(file_path, "rb") as file_handle:
        files = {"file": (file_path.name, file_handle, "text/plain")}
        data = {"document_type": document_type, "description": description}
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.post(
            f"{base_url}/api/documents/upload",
            files=files,
            data=data,
            headers=headers,
            timeout=60,
        )

    if response.status_code != 201:
        print(f"❌ Lỗi upload document: {response.status_code}")
        print(response.text)
        sys.exit(1)

    document = response.json()
    print("   ✅ Thành công! ID:", document["id"])
    return document


def list_documents(base_url: str, token: str) -> List[dict]:
    """Liệt kê documents."""
    print("\n📋 Danh sách documents:")
    response = requests.get(
        f"{base_url}/api/documents",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if response.status_code != 200:
        print(f"❌ Lỗi lấy danh sách: {response.status_code}")
        print(response.text)
        sys.exit(1)

    documents = response.json()
    print(f"   Tổng: {len(documents)}")
    for doc in documents:
        print(f"   - ID {doc['id']}: {doc['filename']} ({doc['document_type']})")
    return documents


def get_document(base_url: str, token: str, document_id: int) -> dict:
    """Lấy chi tiết document."""
    print(f"\n🔍 Chi tiết document ID {document_id}:")
    response = requests.get(
        f"{base_url}/api/documents/{document_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )

    if response.status_code != 200:
        print(f"❌ Lỗi lấy document: {response.status_code}")
        print(response.text)
        sys.exit(1)

    document = response.json()
    print(f"   Filename : {document['filename']}")
    print(f"   Type     : {document['document_type']}")
    print(f"   Desc     : {document['description']}")
    print(f"   Path     : {document['file_path']}")
    return document


def ensure_sample_exists(doc_type: str) -> Path:
    path = SAMPLE_DOCS.get(doc_type)
    if not path or not path.exists():
        print(f"❌ Không tìm thấy file mẫu {doc_type} tại {path}")
        sys.exit(1)
    return path


def main():
    args = parse_args()
    base_url = args.base_url.rstrip("/")

    token = login(base_url, args.username, args.password)

    # Upload sample(s)
    if args.upload_sample:
        types = ["policy", "ops"] if args.upload_sample == "all" else [args.upload_sample]
        for doc_type in types:
            sample_path = ensure_sample_exists(doc_type)
            upload_document(base_url, token, sample_path, doc_type, description=args.description)

    # Upload custom file
    if args.file:
        if not args.document_type:
            print("❌ Cần --document-type khi dùng --file.")
            sys.exit(1)
        upload_document(base_url, token, args.file, args.document_type, description=args.description)

    if args.list:
        list_documents(base_url, token)

    if args.document_id is not None:
        get_document(base_url, token, args.document_id)

    if not any([args.upload_sample, args.file, args.list, args.document_id is not None]):
        print("ℹ️ Không có hành động nào được yêu cầu. Dùng --help để xem tùy chọn.")


if __name__ == "__main__":
    main()

