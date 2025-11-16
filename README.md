# 🤖 Internal Company Chatbot

Nền tảng chatbot nội bộ hỗ trợ nhân viên tra cứu chính sách nhân sự và runbook vận hành. Hệ thống dùng FastAPI + Spoon AI StateGraph, kết hợp Retrieval-Augmented Generation (RAG) và MCP server để truy xuất tài liệu chuẩn hóa và sinh câu trả lời đáng tin cậy.

## 🌟 Tóm Tắt Nhanh

- **Bài toán**: xây chatbot nội bộ giúp nhân viên hỏi chính sách và quy trình vận hành.
- **Giải pháp**: FastAPI backend kích hoạt Spoon Graph (Gemini + Ollama fallback) với retrieval ChromaDB và MCP server để chia sẻ toolset cho các client khác.
- **Điểm nổi bật**:
  - Quản trị viên quản lý người dùng, upload tài liệu `.txt`, phân loại policy/ops.
  - Nhân viên chat real-time, lưu lịch sử hội thoại, tiếp tục trên nhiều thiết bị.
  - Spoon Graph orchestration chạy multi-intent: rewrite query, gọi song song `policy_txt_lookup`, `ops_txt_lookup`, rồi tổng hợp citation.
  - MCP server (FastMCP) mở sẵn tool `policy_txt_lookup`, `ops_txt_lookup`, `conversation_history_simple`, `upload_document` để IDE/Inspector tái sử dụng cùng pipeline.

## 🏗️ Kiến Trúc Hệ Thống

| Lớp | Vai trò chính | Công nghệ |
| --- | ------------- | --------- |
| Giao diện | Next.js 14 + React + Tailwind, quản lý auth bằng context, streaming hội thoại | `frontend/app/*`, `components/ui/*` |
| API & Auth | FastAPI router `auth/users/documents/chat`, JWT (python-jose), bcrypt hash mật khẩu | `app/api`, `app/core/security.py` |
| Orchestration | `SpoonGraphService` chuẩn hóa câu hỏi, detect intent, lập kế hoạch và ghép kết quả đa tool | `app/services/spoon_graph_service.py` |
| Retrieval | `CustomChromaClient` dùng SentenceTransformers `paraphrase-multilingual-MiniLM-L12-v2`, lọc theo `document_type` | `app/services/retrieval/custom_chroma.py` |
| LLM Chain | Gemini 2.5 Flash (primary) + chuỗi fallback cấu hình qua `SPOON_LLM_PROVIDER_CHAIN`; Ollama Qwen2.5 chạy local | `app/core/config.py`, Spoon AI manager |
| MCP Server | FastMCP expose `policy_txt_lookup`, `ops_txt_lookup`, `conversation_history_simple`, `upload_document` | `app/mcp_server.py` |
| Persistence | PostgreSQL (SQLAlchemy + Alembic), lưu user/conversation/document; local storage cho file `.txt`; ChromaDB lưu embedding | `app/models`, `storage/`, `chroma_db/` |

## 🧰 Thành Phần Nổi Bật

- **Backend core**: FastAPI, SQLAlchemy 2.0, Alembic migrations, JWT + bcrypt.
- **LLM stack**: Spoon AI StateGraph + LLM Manager, Gemini 2.5 Flash (primary), chuỗi fallback cấu hình qua `SPOON_LLM_PROVIDER_CHAIN`, Ollama Qwen2.5 cho on-prem.
- **Retrieval**: SentenceTransformers (paraphrase-multilingual-MiniLM-L12-v2) + ChromaDB, metadata enrichment (document_type, chunk_index, retrieval_tool).
- **Frontend**: Next.js 14 App Router, React 19, Tailwind CSS 4, component library tự xây (Button/Card/Modal/FileUpload).

## 🔌 Tích Hợp Spoon AI

Spoon AI là nền tảng cốt lõi giúp hệ thống vận hành RAG một cách có kiểm soát và dễ mở rộng. Các thành phần chính:

1. **StateGraph điều phối hội thoại**
   - Định nghĩa trong `app/services/rag_graph_service.py`.
   - Các node chính:
     1. Chuẩn bị context (thu thập lịch sử hội thoại từ DB).
     2. Truy vấn vector store (`CustomChromaClient`) để lấy tài liệu liên quan.
     3. Lắp ghép system prompt + nguồn tài liệu để gọi LLM.
     4. Ghi log và lưu message (user, assistant) vào database.
   - Hỗ trợ retry/backoff khi gặp `RateLimitError`, ghi nhận provider đã dùng (`gemini`, `ollama`, `fallback`).

2. **LLM Manager & Configuration Manager**
   - Tự động đọc biến môi trường (`GEMINI_API_KEY`, `GEMINI_MODEL`, `OLLAMA_*`).
   - Thay đổi model/khóa cấu hình mà không cần sửa code.
   - Ghi nhận thời gian phản hồi, thống kê provider để tối ưu sau này.

3. **Fallback đa mô hình**
   - Ưu tiên Gemini 2.5 Flash.
   - Khi lỗi quota/rate limit, chuyển qua Ollama (nếu `OLLAMA_ENABLED=true`) với chính sách retry, exponential backoff.
   - Có thể mở rộng thêm provider khác bằng cách cấu hình.

4. **MCP Graph Integration**
   - MCP server (`app/mcp_server.py`).
   - Toolset: `policy_txt_lookup`, `ops_txt_lookup`, `conversation_history_simple`, `upload_document`.

Spoon AI giúp tách bạch luồng điều phối (graph) khỏi controller, dễ kiểm soát state, logging và mở rộng trong tương lai (ví dụ thêm bước tiền xử lý/tóm tắt).

## 🌐 MCP Server

### Vai trò trong dự án

- Là cầu nối tiêu chuẩn hóa (Model Context Protocol) giúp các client như Spoon Inspector, IDE hoặc ứng dụng nội bộ tương tác với chatbot.
- Cho phép thực hiện các thao tác ngoài UI hiện có: tìm kiếm tài liệu, upload, trò chuyện với bot, truy xuất lịch sử hội thoại.
- Kế thừa toàn bộ logic RAG/StateGraph ở backend, đảm bảo trả lời nhất quán với ứng dụng web.

### Những gì đã triển khai

- Toolset: `query_documents`, `upload_document`, `chat_with_bot`, `get_conversation_history`.
- Hỗ trợ transport HTTP (mặc định) và tương thích với proxy `fastmcp dev` để dùng Inspector qua SSE.
- Sẵn sàng fallback Gemini → Ollama nhờ tái sử dụng `rag_graph_service`.
- Logging & retry tương tự backend, đảm bảo error handling nhất quán.

### Định hướng phát triển

- Bổ sung lớp xác thực khi expose ra môi trường ngoài (API key, OAuth nội bộ).
- Ghi nhận telemetry (thời gian phản hồi, tỉ lệ fallback) để tối ưu chất lượng.
- Thêm tool nâng cao: batch upload, trigger re-index, xuất thống kê hội thoại.
- Cung cấp packaging (Docker image) và hướng dẫn deploy trên server từ xa (HTTPS, reverse proxy).
- Thêm health-check và auto-restart để tăng độ sẵn sàng trong môi trường production.

## 🚀 Bắt Đầu Nhanh

1. **Clone & submodule Spoon** (đã bao gồm trong repo).
2. **Cấu hình Python environment** (`python -m venv .venv`, `pip install -r requirements.txt`).
3. **Cài đặt Spoon core**: `cd spoon-core && pip install -e . && cd ..`.
4. **Chuẩn bị `.env`** (xem `env.example` + cập nhật `GEMINI_API_KEY`, `DATABASE_URL` port 5433, `JWT_SECRET_KEY`, `OLLAMA_ENABLED`, `OLLAMA_MODEL`, `MCP_SERVER_PORT`, …).
5. **Khởi tạo database**: `alembic upgrade head`, sau đó `python scripts/create_admin.py`.
6. **Chạy dịch vụ**:
   - Backend API: `uvicorn app.main:app --reload`.
   - MCP server: `python app/mcp_server.py` (hoặc `fastmcp dev app/mcp_server.py` để dùng Inspector).
   - Frontend: `cd frontend && npm install && npm run dev`.

## 🔮 Định Hướng Phát Triển

- **Đa định dạng & pipeline ingest**: hỗ trợ PDF/DOCX, tự động trích metadata, dashboard giám sát tiến độ ingest.
- **Observability nâng cao**: analytics hội thoại, heatmap intent, cảnh báo khi retriever trả về ít kết quả hoặc answer_mode=snippet-fallback tăng cao.
- **Mở rộng MCP/tooling**: tích hợp nguồn dữ liệu khác (SharePoint, wiki), batch upload, trigger re-index, export thống kê hội thoại.
- **Trải nghiệm frontend**: streaming chunk-by-chunk, markdown + highlight nguồn, push notification khi tài liệu ingest xong.
- **CI/CD & bảo mật**: Playwright/Cypress E2E, Docker Compose cho dev, tích hợp Secret Manager/SSO doanh nghiệp, audit log chi tiết.

Hướng dẫn chi tiết (cài đặt, chạy, kiểm thử) nằm trong thư mục `guide/`.