# 🧩 Backend Guide (FastAPI + Spoon)

Tài liệu này tổng hợp kiến trúc, luồng xử lý chính và thao tác vận hành backend FastAPI kết hợp Spoon AI / MCP.

## 1. Kiến trúc tổng quan
- `app/main.py` khởi tạo FastAPI, cấu hình CORS và mount router `auth`, `users`, `documents`, `chat`.
- `app/api/` phân tách endpoint theo domain: xác thực/JWT, CRUD người dùng, quản trị tài liệu, hội thoại.
- `app/models/` + `app/schemas/` định nghĩa bảng SQLAlchemy (PostgreSQL) và Pydantic I/O cho `User`, `Document`, `Conversation`, `Message`.
- `app/services/` chứa business logic:
  - `conversation_service.py`, `document_service.py` thao tác DB và lưu/lấy message.
  - `spoon_chat_service.py` điều phối toàn bộ luồng chat.
  - `spoon_graph_service.py` thực thi graph RAG-lite, lập kế hoạch tool và tổng hợp câu trả lời.
  - `retrieval/custom_chroma.py` bọc ChromaDB + SentenceTransformer.
- `app/utils/` gồm parser `.txt`, lưu file vật lý trong `storage/`.
- `app/core/` quản lý config (`Settings`), SQL session, JWT, dependency để kiểm tra quyền.
- `app/mcp_server.py` chạy FastMCP server chia sẻ cùng DB/vector store, phục vụ các MCP tool (policy/ops lookup, upload document, conversation history).
- Repo còn đi kèm `spoon-core/` (submodule/thư viện gốc Spoon AI) và `guide/` chứa tài liệu vận hành.

## 2. Cấu hình & biến môi trường
- File mẫu: `env.example`. Khi chạy thực tế copy sang `.env`.
- Biến cốt lõi (đọc trong `app/core/config.py`):
  - DB/JWT: `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_EXPIRATION_HOURS`. Không cấu hình sẽ không khởi tạo được session.
  - LLM: `GEMINI_API_KEY`, `GEMINI_MODEL` cùng chuỗi fallback `SPOON_LLM_PROVIDER_CHAIN`. Ollama fallback bật qua `OLLAMA_ENABLED=true`.
  - Spoon/MCP: `SPOON_AGENT_ENABLED`, `SPOON_MCP_TRANSPORT`, `MCP_SERVER_*`. `settings.spoon_mcp_url` tự build nếu không chỉ định.
  - Retrieval & storage: `CHROMADB_PATH`, `FILE_STORAGE_PATH`, `MAX_FILE_SIZE` (50 MB mặc định).
  - Frontend/CORS: `CORS_ORIGINS` khớp domain Next.js (`localhost:3000`...). 
- Chạy `python scripts/generate_secrets.py` để sinh chuỗi bí mật và cập nhật `.env`.

## 3. Lớp dữ liệu & migration
- ORM sử dụng SQLAlchemy + session per-request (dependency `get_db`). Bảng được quản lý qua Alembic.
- Quy trình:
  ```bash
  alembic upgrade head          # apply latest schema
  alembic revision --autogenerate -m "short note"   # tạo migration mới
  alembic downgrade -1          # rollback 1 bước nếu cần
  ```
- Migration mẫu nằm trong `alembic/versions/`. Kiểm tra thay đổi ở `app/models/` trước khi auto-generate.

## 4. Pipeline tài liệu & vector database
1. Admin gọi `POST /api/documents/upload` với file `.txt`, chỉ định `document_type` (`policy` | `ops`).
2. `DocumentService.upload_document` (a) xác thực định dạng/kích thước, (b) lưu file vào `storage/<user_id>/`, (c) ghi metadata DB.
3. `app/utils/document_parser.py` đọc file, chunk theo ký tự (size 1000, overlap 200), gắn metadata như `document_id`, `chunk_index`.
4. `CustomChromaClient` sử dụng SentenceTransformer `paraphrase-multilingual-MiniLM-L12-v2` để embed và lưu vào ChromaDB (`chroma_db/`).
5. Xoá tài liệu sẽ gọi `delete_documents_by_metadata` để làm sạch cả vector store lẫn file vật lý.
- MCP tool `upload_document` tái sử dụng chu trình này khi gọi từ agent.

## 5. Luồng chat end-to-end
1. Frontend gửi `POST /api/chat/conversations/{id}/messages` cùng JWT.
2. Dependency `get_current_user` giải mã token, nạp `User` rồi `ConversationService.get_conversation` đảm bảo quyền sở hữu.
3. `SpoonChatService.send_message` làm việc với `ConversationService` và `SpoonGraphService`:
   - Kiểm tra graph có bật (`SPOON_AGENT_ENABLED` & `MCP_SERVER_ENABLED`).
   - Gọi `SpoonGraphService.run` với `rewrite=True`, `top_k` theo request.
4. Bên trong `SpoonGraphService`:
   - `_rewrite_query` + `_detect_intent` dùng LLM Manager (Gemini + fallback) để chuẩn hoá câu hỏi, phân loại `policy/ops`.
   - `_plan_tools` chọn danh sách MCP tool (`policy_txt_lookup`, `ops_txt_lookup`, `conversation_history_simple`).
   - Async gather kết quả MCP, gom `evidence`, gắn metadata (filename, distance, tool).
   - `_summarize_with_llm` cố gắng tạo câu trả lời dựa trên snippet (giới hạn 6 câu, kèm nguồn). Nếu không đủ dữ liệu sẽ fallback `_synthesize_response` hoặc trả lỗi `graph-no-answer` + gợi ý follow-up.
5. `SpoonChatService` lưu cặp tin nhắn user/assistant vào DB, trả về payload gồm `provider_used` (vd. `spoon-policy`) và `spoon_agent_metadata` (intent, tool_calls...).
6. Nếu metadata thiếu, API tự đọc lại 2 message cuối làm fallback trước khi trả response cho frontend.

## 6. MCP server & Spoon agent
- `app/mcp_server.py` khởi tạo FastMCP và expose toolset dùng chung với backend. Mỗi tool mở session riêng, gọi lại `DocumentService`, `ConversationService` hoặc `CustomChromaClient`. Chạy bằng `python -m app.mcp_server` hoặc script riêng (`scripts/run_with_spoon.ps1`).
- `SpoonAgentService` (được bật khi cần) tạo `SpoonReactMCP` agent với cùng các tool để xử lý tình huống phức tạp (upload tài liệu qua agent, chuỗi bước nhiều công cụ). Hiện tại luồng chat mặc định dùng `SpoonGraphService`; agent có thể tái sử dụng từ service khác nếu muốn.

## 7. Script & seed hữu ích
- `python scripts/create_admin.py` – tạo user admin đầu tiên (bcrypt hash, nhập password tại CLI).
- `python scripts/test_upload_document.py` – thử pipeline upload + indexing với sample `.txt`.
- `python scripts/test_vector_database.py`, `test_chat_provider.py`, `test_token.py` – kiểm tra kết nối LLM/Chroma/JWT.
- `python scripts/run_backend_simple.ps1` & `scripts/run_with_spoon.ps1` – tiện chạy uvicorn + MCP song song cho Windows.
- Chi tiết thêm trong [scripts/README.md](../scripts/README.md).

## 8. Chạy backend
- Dev (hot-reload):
  ```bash
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```
- Production (ví dụ Gunicorn + Uvicorn worker):
  ```bash
  gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    --workers 4 --bind 0.0.0.0:8000
  ```
- MCP server nên được bật song song (port 8001 SSE) nếu muốn dùng Spoon graph đầy đủ:
  ```bash
  python -m app.mcp_server
  ```

## 9. Testing
- Pytest toàn bộ:
  ```bash
  pytest
  ```
- Chạy nhóm cụ thể:
  ```bash
  pytest tests/services/test_conversation_service.py
  ```
- Report coverage:
  ```bash
  pytest --cov=app --cov-report=html
  ```

## 10. Bảo mật & vận hành
- Mật khẩu người dùng luôn băm bằng `bcrypt` (`app/core/security.py`). API tạo/cập nhật user chỉ trả plaintext password trong response duy nhất để admin ghi nhận.
- JWT dùng HS256, hạn `JWT_EXPIRATION_HOURS` (24h mặc định). Cần rotate `JWT_SECRET_KEY` định kỳ và cân nhắc refresh token khi mở rộng quy mô.
- Upload file giới hạn `.txt`, kiểm tra kích thước trước khi lưu; đường dẫn lưu tương đối để bảo vệ filesystem.
- Kiểm soát quyền rõ ràng: chỉ admin mới truy cập router `users` & `documents` (`get_current_admin`). Người dùng thường chỉ có auth/chat.
- CORS được cấu hình mở (`allow_methods=["*"]`), cần siết lại domain khi deploy.
- MCP/Spoon agent phụ thuộc vào cùng DB và file storage – backup/restore phải bao gồm cả `storage/` và `chroma_db/`.

## 11. Gợi ý mở rộng
- Bổ sung redis cache để lưu kết quả retrieval phổ biến hoặc throttling intent detection.
- Tách worker background (Celery/RQ) cho parsing tài liệu lớn, tránh block request.
- Ghi log cấu trúc + metrics Prometheus/OpenTelemetry để giám sát thời gian phản hồi LLM/MCP.
- Thêm rate limit per-user, reCAPTCHA cho endpoint auth để tránh brute-force.
- Xây API để invalidate Chroma chunk khi cập nhật nội dung tài liệu.

