# 🔗 MCP Server Guide

MCP (Model Context Protocol) server cho phép các client (Inspector, Spoon tools, IDE) tương tác với chatbot và kho tài liệu qua giao thức chuẩn hoá.

## 1. Overview

- Entry point: `app/mcp_server.py`.
- Tool hiện có:
  - `query_documents`
  - `upload_document`
  - `chat_with_bot`
  - `get_conversation_history`
- Sử dụng `fastmcp` để hỗ trợ dev (proxy + Inspector).
- Hỗ trợ transport HTTP (mặc định) và STDIO (cấu hình qua biến môi trường).

## 2. Cách Chạy

### 2.1 HTTP trực tiếp

```bash
python app/mcp_server.py
```

- Endpoint: `http://localhost:8001/mcp/` (đổi bằng `MCP_SERVER_PORT`).
- Phù hợp cho client nội bộ gọi qua HTTP/REST wrapper.

### 2.2 Dev với Inspector

```bash
fastmcp dev app/mcp_server.py
```

- Proxy: `http://localhost:3001/sse`
- Inspector tự mở. Nếu không, truy cập thủ công.
- Khi Inspector yêu cầu cấu hình:
  - Transport Type: `Streamable HTTP`
  - URL: `http://localhost:3001/sse` (hoặc `http://localhost:8001/mcp/` nếu không dùng proxy)
  - Connection Type: `Direct`

### 2.3 STDIO (tuỳ chọn)

- Đặt `MCP_TRANSPORT=stdio`.
- Chạy:
  ```bash
  python app/mcp_server.py
  ```
- MCP server đọc/ghi qua STDIN/STDOUT (hữu ích khi tích hợp vào process khác).

## 3. Biến Môi Trường Liên Quan

- `MCP_SERVER_ENABLED` – bật/tắt server.
- `MCP_SERVER_PORT` – port HTTP (mặc định 8001).
- `MCP_TRANSPORT` – `http` hoặc `stdio`.
- `MCP_PROXY_TOKEN` – dùng khi kết nối qua proxy `fastmcp` để xác thực.
- `LOG_LEVEL` (tuỳ chọn) – điều chỉnh mức log (info/debug).

Chi tiết đầy đủ xem [ENVIRONMENT.md](./ENVIRONMENT.md).

## 4. Tích Hợp Với Backend

- MCP server sử dụng service backend (FastAPI). Backend phải chạy trước.
- Dùng `app.services` để truy vấn DB, vector DB, LLM.
- Khi upload document qua tool, cần quyền file system (đường dẫn tính từ gốc project).

## 5. Kiểm Thử

- Dùng `fastmcp dev` và gọi tool trong Inspector theo [TESTING.md](./TESTING.md).
- Script test API có thể dùng độc lập (VD: `python scripts/test_upload_document.py`), nhưng MCP tools nên test qua Inspector hoặc client tùy chỉnh.

## 6. Sự Cố Thường Gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|-----|-------------|-----------|
| `ModuleNotFoundError: No module named 'app'` | Chạy sai thư mục, thiếu `PYTHONPATH` | Chạy từ gốc dự án hoặc set `PYTHONPATH=.` |
| `FetchError: ECONNREFUSED` | Inspector trỏ sai URL | Dùng `http://localhost:3001/sse` (proxy) hoặc `http://localhost:8001/mcp/` với `/mcp/` ở cuối |
| `MCP error -32602` | JSON input sai schema | Kiểm tra lại JSON (tham khảo ví dụ trong README/tool docstring) |
| `Received request before initialization was complete` | MCP chưa kết nối backend/kho dữ liệu | Đảm bảo backend chạy trước, MCP log “Server ready” |

Tham khảo chi tiết hơn tại [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).

## 7. Định Hướng Phát Triển

- Thêm auth layer (API key, JWT) cho tool nhạy cảm.
- Cho phép cấu hình multi-tenant (nhiều workspace).
- Ghi log chi tiết cho mỗi tool call (metrics, audit trail).
- Tạo client CLI để tương tác nhanh (ví dụ `python scripts/mcp_cli.py`).
- Triển khai deploy container (Dockerfile) và expose qua HTTPS/reverse proxy.

