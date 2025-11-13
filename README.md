# 🤖 Internal Company Chatbot

Nền tảng chatbot nội bộ hỗ trợ nhân viên tra cứu chính sách, quy trình và tài nguyên kỹ thuật dựa trên tập tài liệu do quản trị viên quản lý. Hệ thống áp dụng Spoon AI StateGraph, kết hợp Retrieval-Augmented Generation (RAG) và Spoon MCP server để cung cấp câu trả lời chính xác, cập nhật.

## 🌟 Tóm Tắt Nhanh

- **Mục tiêu**: xây dựng chatbot nội bộ với hai vai trò (Admin, Employee) và luồng chat tương tự ChatGPT nhưng dựa trên tài liệu doanh nghiệp.
- **Điểm nổi bật**:
  - Admin quản lý người dùng & tài liệu (9 loại tài liệu .txt, 50MB).
  - Nhân viên trò chuyện với bot, lưu và tiếp tục hội thoại.
  - RAG pipeline với Spoon AI StateGraph, Gemini 2.5 Flash làm mô hình chính, Ollama model fallback (tùy chọn).
  - MCP server cung cấp tool cho Inspector hoặc ứng dụng khác: tra cứu tài liệu, upload, chat, lấy lịch sử hội thoại.

## 🏗️ Kiến Trúc & Công Nghệ

- **Backend**: FastAPI, SQLAlchemy, Alembic, JWT, Spoon AI (StateGraph, LLM Manager).
- **Frontend**: Next.js 14 (App Router), React, TailwindCSS, shadcn/ui.
- **AI & Retrieval**: Google Gemini 2.5 Flash (primary), Ollama fallback (mô hình tùy chọn), ChromaDB + sentence-transformers, Spoon MCP server.
- **Hạ tầng dữ liệu**: PostgreSQL (port 5433 theo môi trường thực tế), lưu file cục bộ.
- **Dev tooling**: `fastmcp` cho MCP dev server, scripts tạo admin & bí mật.

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
   - MCP server (`app/mcp_server.py`) sử dụng cùng StateGraph và service lớp dưới, bảo đảm kết quả đồng nhất giữa UI và client bên ngoài.
   - Tool MCP call thẳng vào graph/service (không dựng lại logic).

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
   - MCP server: `python app/mcp_server.py` (hoặc `fastmcp dev app/mcp_server.py` khi cần Inspector).
   - Frontend: `cd frontend && npm install && npm run dev`.

Hướng dẫn chi tiết (cài đặt, chạy, kiểm thử) nằm trong thư mục `guide/`.

## 🧪 Kiểm Thử & Giám Sát

- Tài liệu test nhanh: `guide/TESTING.md`.
- Script hỗ trợ:
  - `python scripts/test_upload_document.py`
  - `python scripts/test_vector_database.py`
- Tài liệu mẫu: `resources/sample_documents/TAI_LIEU_MAU_CHINH_SACH.txt`.

## 🔮 Hướng Phát Triển Tương Lai

- Mở rộng hỗ trợ upload `.pdf`, `.docx`, và pipeline xử lý văn bản nâng cao.
- Bổ sung dashboard phân tích usage (conversation analytics, provider metrics).
- Tích hợp SSO doanh nghiệp và log auditing chi tiết.
- Hoàn thiện bộ test end-to-end (Playwright/Cypress) sau khi roadmap tối ưu được duyệt.
- Đóng gói deploy (Docker compose, cloud runbook) khi hệ thống ổn định.