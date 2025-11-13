"""
Script hỗ trợ upload tài liệu mẫu và kiểm tra các API documents.
"""
import sys
from pathlib import Path
from typing import Optional

import requests

BASE_URL = "http://localhost:8000"

ROOT_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DOC = ROOT_DIR / "resources" / "sample_documents" / "TAI_LIEU_MAU_CHINH_SACH.txt"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def login(username: str = "admin", password: str = "admin") -> str:
    """Đăng nhập và trả về JWT token."""
    print(f"🔐 Đang đăng nhập với username: {username}...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": username, "password": password},
        timeout=30,
    )

    if response.status_code != 200:
        print(f"❌ Lỗi đăng nhập: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

    token = response.json()["access_token"]
    print("✅ Đăng nhập thành công!")
    return token


def upload_document(
    token: str,
    file_path: Path,
    document_type: str = "policies",
    description: Optional[str] = None,
) -> dict:
    """Upload tài liệu và trả về JSON document."""
    print(f"\n📄 Đang upload document: {file_path.name}...")

    if not file_path.exists():
        print(f"❌ File không tồn tại: {file_path}")
        sys.exit(1)

    if description is None:
        description = f"Tài liệu mẫu về chính sách công ty - {file_path.name}"

    with open(file_path, "rb") as file_handle:
        files = {"file": (file_path.name, file_handle, "text/plain")}
        data = {"document_type": document_type, "description": description}
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.post(
            f"{BASE_URL}/api/documents/upload",
            files=files,
            data=data,
            headers=headers,
            timeout=60,
        )

    if response.status_code != 201:
        print(f"❌ Lỗi upload document: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

    document = response.json()
    print("✅ Upload document thành công!")
    print(f"   Document ID: {document['id']}")
    print(f"   Filename: {document['filename']}")
    print(f"   Document Type: {document['document_type']}")
    print(f"   Description: {document['description']}")
    print(f"   Uploaded At: {document['uploaded_at']}")
    return document


def list_documents(token: str) -> list:
    """Liệt kê documents."""
    print("\n📋 Đang lấy danh sách documents...")
    response = requests.get(
        f"{BASE_URL}/api/documents",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )

    if response.status_code != 200:
        print(f"❌ Lỗi lấy danh sách documents: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

    documents = response.json()
    print(f"✅ Tổng số documents: {len(documents)}")
    for doc in documents:
        print(f"\n--- Document ID: {doc['id']} ---")
        print(f"Filename: {doc['filename']}")
        print(f"Document Type: {doc['document_type']}")
        print(f"Description: {doc['description']}")
        print(f"Uploaded At: {doc['uploaded_at']}")
    return documents


def get_document(token: str, document_id: int) -> dict:
    """Lấy chi tiết document."""
    print(f"\n🔍 Đang lấy document ID: {document_id}...")
    response = requests.get(
        f"{BASE_URL}/api/documents/{document_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )

    if response.status_code != 200:
        print(f"❌ Lỗi lấy document: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

    document = response.json()
    print("✅ Lấy document thành công!")
    print(f"   Document ID: {document['id']}")
    print(f"   Filename: {document['filename']}")
    print(f"   Document Type: {document['document_type']}")
    print(f"   Description: {document['description']}")
    print(f"   File Path: {document['file_path']}")
    return document


def main():
    """Chạy toàn bộ quy trình test upload."""
    print("=" * 60)
    print("🧪 TEST UPLOAD DOCUMENT")
    print("=" * 60)

    if not SAMPLE_DOC.exists():
        print(f"❌ Không tìm thấy file mẫu tại: {SAMPLE_DOC}")
        print("   Vui lòng đảm bảo thư mục resources/sample_documents có sẵn.")
        sys.exit(1)

    token = login()
    document = upload_document(token, SAMPLE_DOC, document_type="policies")
    document_id = document["id"]

    list_documents(token)
    get_document(token, document_id)

    print("\nHoàn tất! Bạn có thể chạy thêm `python scripts/test_vector_database.py` để kiểm tra vector DB.")


if __name__ == "__main__":
    main()

