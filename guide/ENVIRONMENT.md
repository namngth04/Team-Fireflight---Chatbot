# 🌱 Environment Variables

Tất cả biến môi trường đều được đọc qua `app/core/config.py`. Bảng dưới liệt kê các biến chính, gợi ý giá trị và ghi chú bảo mật.

| Biến | Mặc định | Bắt buộc | Mô tả |
|------|----------|----------|-------|
| `DATABASE_URL` | - | ✅ | Chuỗi kết nối PostgreSQL. Ví dụ `postgresql://postgres:<pass>@localhost:5433/chatbot_db`. |
| `GEMINI_API_KEY` | - | ✅ | API key cho Google Gemini. Yêu cầu quyền gọi model `gemini-2.5-flash`. |
| `GEMINI_MODEL` | `gemini-2.5-flash` | ✅ | Tên model sử dụng qua Spoon LLM Manager. Có thể đổi sang model có rate limit cao hơn. |
| `JWT_SECRET_KEY` | - | ✅ | Secret dùng ký JWT. Nên sử dụng chuỗi random > 32 ký tự. |
| `SECRET_KEY` | - | ✅ | Secret cho FastAPI session (CSRF, OAuth). Có thể dùng cùng giá trị với `JWT_SECRET_KEY` nhưng nên tách riêng. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | ❌ | Thời hạn JWT (phút). |
| `PASSWORD_HASHING_ENABLED` | `false` | ❌ | Giữ `false` nếu muốn hiển thị/biên tập mật khẩu dạng plain text (đang **không** sử dụng). Khi triển khai thật, đặt `true` để hash mật khẩu và cập nhật lại UI + logic quản trị. |
| `FILE_STORAGE_DIR` | `storage` | ❌ | Thư mục lưu file `.txt` sau upload. |
| `MAX_UPLOAD_SIZE_MB` | `50` | ❌ | Giới hạn kích thước file. |
| `ALLOWED_FILE_TYPES` | `[".txt"]` | ❌ | Danh sách phần mở rộng cho Upload. |

## MCP & AI

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `MCP_SERVER_ENABLED` | `true` | Bật/tắt MCP server khi chạy `app/mcp_server.py`. |
| `MCP_SERVER_PORT` | `8001` | Port HTTP cho MCP server. |
| `MCP_TRANSPORT` | `http` | Transport mặc định (http/stdio). Khi dùng `fastmcp dev`, proxy tự cấu hình. |
| `MCP_PROXY_TOKEN` | - | Token bảo vệ khi dùng proxy (được generate bởi `fastmcp`). |
| `OLLAMA_ENABLED` | `false` | Bật fallback Ollama. |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct` (khuyến nghị) | Tên model trên Ollama (phải `ollama pull`). |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL tới server Ollama. |
| `LLM_RETRY_MAX_ATTEMPTS` | `3` | Số lần retry khi rate-limit. |
| `LLM_RETRY_BACKOFF` | `2` | Backoff cơ số (giây). |

## Frontend

| Biến | Mô tả |
|------|-------|
| `NEXT_PUBLIC_API_URL` | URL backend (nếu khác `http://localhost:8000`). |
| `NEXT_PUBLIC_MCP_URL` | URL MCP server (nếu cần gọi trực tiếp từ frontend). |

## Bảo Mật & Ghi Chú

- Không commit file `.env`.
- Với môi trường production, nên cấu hình secrets qua secret manager (AWS, GCP) hoặc biến môi trường hệ thống.
- Nếu bật `PASSWORD_HASHING_ENABLED`, cần cập nhật UI để không hiển thị plain text password và điều chỉnh lại yêu cầu nghiệp vụ.
- Khi expose MCP server ra internet, bắt buộc cấu hình `MCP_PROXY_TOKEN` hoặc gateway bảo mật.

Xem thêm:

- [INSTALL.md](./INSTALL.md) – cách tạo `.env`.
- [MCP_SERVER.md](./MCP_SERVER.md) – cấu hình transport, proxy token.
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) – xử lý lỗi liên quan biến môi trường.

