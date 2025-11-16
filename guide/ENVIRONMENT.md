# 🌱 Environment Variables

Mọi cấu hình đều được khai báo trong `app/core/config.py`. Bảng dưới tổng hợp các biến quan trọng theo nhóm.

## 1. Database & Secrets

| Biến | Mặc định | Bắt buộc | Mô tả |
|------|----------|----------|-------|
| `DATABASE_URL` | - | ✅ | PostgreSQL connection string (`postgresql://user:pass@localhost:5433/chatbot_db`). |
| `JWT_SECRET_KEY` | - | ✅ | Secret ký JWT. Nên dùng chuỗi random >32 ký tự. |
| `JWT_ALGORITHM` | `HS256` | ❌ | Thuật toán JWT. |
| `JWT_EXPIRATION_HOURS` | `24` | ❌ | Thời hạn JWT. |
| `SECRET_KEY` | - | ✅ | Secret của FastAPI (session, CSRF). |
| `DEBUG` | `true` | ❌ | Bật log debug. |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:3001` | ❌ | Danh sách origin cho frontend. |

## 2. LLM & Spoon Agent

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `GEMINI_API_KEY` | - | API key Google Gemini (bắt buộc). |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Model chính dùng cho intent/rewrite/summary. |
| `SPOON_LLM_PROVIDER_CHAIN` | - | Chuỗi ưu tiên LLM, ví dụ `gemini:gemini-2.5-flash,ollama:qwen2.5:7b`. |
| `OLLAMA_ENABLED` | `true` | Bật fallback nội bộ. Đặt `false` nếu không cài Ollama. |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Endpoint OpenAI-compatible của Ollama. |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Model chạy trên Ollama (`ollama pull` trước). |
| `OLLAMA_API_KEY` | `ollama` | Dummy key (Ollama không cần thật). |
| `LLM_RETRY_ATTEMPTS` | `3` | Số lần retry chung cho LLM. |
| `LLM_RETRY_BASE_DELAY` | `2.0` | Độ trễ ban đầu (giây). |
| `LLM_RETRY_MAX_DELAY` | `60.0` | Độ trễ tối đa (giây). |
| `SPOON_AGENT_ENABLED` | `true` | Cho phép dùng Spoon graph orchestration. |
| `SPOON_AGENT_MAX_STEPS` | `6` | Số bước tối đa trong đồ thị. |
| `SPOON_AGENT_TIMEOUT` | `90` | Timeout (giây). |

## 3. MCP Server & tool routing

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `MCP_SERVER_ENABLED` | `true` | Bật FastMCP server (`app/mcp_server.py`). |
| `MCP_SERVER_HOST` | `localhost` | Host bind. |
| `MCP_SERVER_PORT` | `8001` | Port SSE/HTTP. |
| `MCP_TRANSPORT` | `sse` | `sse`, `http` hoặc `stdio`. |
| `SPOON_MCP_TRANSPORT` | `sse` | Transport khi Spoon agent kết nối MCP. |
| `SPOON_MCP_URL` | - | Ghi đè URL nếu MCP nằm ngoài backend. |
| `SPOON_MCP_PATH` | `/sse` | Đường dẫn mặc định nếu không đặt URL. |

## 4. Retrieval & File storage

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `CHROMADB_PATH` | `./chroma_db` | Đường dẫn lưu persistent vector store. |
| `FILE_STORAGE_PATH` | `./storage` | Thư mục chứa file .txt sau khi upload. |
| `MAX_FILE_SIZE` | `52428800` | Tối đa 50MB cho mỗi tài liệu. |

## 5. Frontend (tham khảo)

| Biến | Mô tả |
|------|-------|
| `NEXT_PUBLIC_API_URL` | Đặt khi frontend không chạy cùng origin với backend. |
| `NEXT_PUBLIC_MCP_URL` | URL MCP (SSE/HTTP) nếu frontend cần gọi trực tiếp. |

## 6. Ghi chú bảo mật

- Không commit `.env`. Sử dụng secret manager cho môi trường production.
- Khi expose MCP ra ngoài, bắt buộc đặt proxy/token (tham khảo `guide/MCP_SERVER.md`).
- Nên rotate `JWT_SECRET_KEY` và `SECRET_KEY` định kỳ, đồng thời thông báo người dùng đăng nhập lại.

Tài liệu liên quan:

- [INSTALL.md](./INSTALL.md) – tạo `.env`.
- [RUN.md](./RUN.md) – khởi động dịch vụ.
- [MCP_SERVER.md](./MCP_SERVER.md) – cấu hình transport/proxy.
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) – xử lý sự cố biến môi trường.

