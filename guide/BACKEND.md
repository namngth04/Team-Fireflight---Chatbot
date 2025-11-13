# 🧩 Backend Guide (FastAPI)

Tài liệu này mô tả kiến trúc, luồng chính và thao tác thường xuyên với backend.

## 1. Kiến Trúc

- `app/api/` – router FastAPI chia theo domain (`auth`, `users`, `documents`, `chat`).
- `app/models/` – ORM model SQLAlchemy (user, document, conversation, message).
- `app/schemas/` – Pydantic schema (request/response).
- `app/services/` – business logic:
  - `conversation_service.py`, `document_service.py` – xử lý CRUD.
  - `rag_graph_service.py` – StateGraph vận hành chatbot (Spoon AI).
  - `rag_service.py` – fallback logic khi không dùng graph.
- `app/utils/` – tiện ích (parser, file storage).
- `app/core/` – config, database session, bảo mật (JWT).

## 2. Database & Migration

- Chạy migration:
  ```bash
  alembic upgrade head
  ```
- Tạo migration mới (khi thay đổi model):
  ```bash
  alembic revision --autogenerate -m "description"
  ```
- Rollback:
  ```bash
  alembic downgrade -1
  ```

## 3. Seed & Script Hữu Ích

- `python scripts/create_admin.py` – tạo admin mặc định (username `admin`, nhập password tại CLI).
- `python scripts/generate_secrets.py` – tạo chuỗi random cho `.env`.
- `python scripts/test_upload_document.py` – kiểm tra API documents.
- `python scripts/test_vector_database.py` – xác minh vector DB.

> Chi tiết từng script xem thêm [scripts/README.md](../scripts/README.md).

## 4. Chạy Backend

- Dev mode:
  ```bash
  uvicorn app.main:app --reload
  ```
- Production (ví dụ với `gunicorn` + `uvicorn` workers):
  ```bash
  gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
  ```

## 5. Testing

- Unit/Integration:
  ```bash
  pytest
  ```
- Chạy một file cụ thể:
  ```bash
  pytest tests/api/test_users.py
  ```
- Coverage (tuỳ chọn):
  ```bash
  pytest --cov=app --cov-report=html
  ```

## 6. Lưu Ý Bảo Mật

- Hiện tại mật khẩu user đang lưu plain-text (theo yêu cầu nghiệp vụ). Nếu muốn chuyển sang hash, bật `PASSWORD_HASHING_ENABLED=true` và cập nhật UI.
- JWT sử dụng HS256. Nên rotate `JWT_SECRET_KEY` định kỳ và cân nhắc refresh token nếu mở rộng.
- Kiểm soát CORS (cấu hình trong `app/main.py`) khi deploy đa miền.

## 7. Spoon StateGraph

- Vị trí: `app/services/rag_graph_service.py`.
- Sử dụng `StateGraph` gồm các node:
  1. Chuẩn bị context (hội thoại trước).
  2. Truy vấn vector store (`CustomChromaClient`).
  3. Xây prompt, gọi LLM (Gemini → fallback Ollama).
  4. Lưu message vào DB.
- Configuration Manager tự đồng bộ `GEMINI_API_KEY`.
- Có retry/backoff khi gặp `RateLimitError`.

## 8. Vector Database

- Sử dụng `CustomChromaClient` (ChromaDB + sentence-transformers).
- Lưu chunk metadata (document_id, chunk_index).
- Cache client ở cấp module tránh load model nhiều lần.
- File liên quan: `app/services/retrieval/custom_chroma.py`.

## 9. Lộ Trình Mở Rộng

- Bổ sung caching (Redis) cho kết quả truy vấn.
- Thêm background task (Celery/RQ) để xử lý upload lớn.
- Áp dụng rate-limit cho API công khai.
- Thêm logging cấu trúc (JSON) và metrics (Prometheus).

