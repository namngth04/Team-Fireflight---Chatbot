# 🔗 MCP Server Guide

MCP (Model Context Protocol) server cho phép các client (Inspector, Spoon tools, IDE) tương tác với chatbot và kho tài liệu qua giao thức chuẩn hoá.

## 1. Overview

- Entry point: `app/mcp_server.py`.
- Tool hiện có:
  - `policy_txt_lookup` – truy vấn snippet tài liệu chính sách.
  - `ops_txt_lookup` – truy vấn snippet runbook/vận hành.
  - `conversation_history_simple` – trả về metadata + message gần nhất của conversation.
  - `upload_document` – upload `.txt`, parse chunk và index vào Chroma.
- Sử dụng `fastmcp` để hỗ trợ dev (proxy + Inspector).
- Hỗ trợ transport `sse` (mặc định), `http`, `stdio` (cấu hình qua biến môi trường).

## 2. Cách Chạy

### 2.1 SSE/HTTP trực tiếp

```bash
python -m app.mcp_server
```

- Mặc định transport `sse` với endpoint `http://localhost:8001/sse` (đổi bằng `MCP_SERVER_PORT` + `SPOON_MCP_PATH`).
- Đặt `MCP_TRANSPORT=http` để chuyển sang endpoint `http://localhost:8001/mcp`.
- Phù hợp khi Spoon agent hoặc client nội bộ kết nối trực tiếp mà không cần proxy.

### 2.2 Dev với Inspector

```bash
fastmcp dev app/mcp_server.py
```

- Proxy: `http://localhost:3001/sse`
- Inspector tự mở. Nếu không, truy cập thủ công.
- Khi Inspector yêu cầu cấu hình:
  - Transport Type: `Streamable HTTP`
  - URL: `http://localhost:3001/sse` (hoặc `http://localhost:8001/sse` nếu không dùng proxy)
  - Connection Type: `Direct`

### 2.3 STDIO (tuỳ chọn)

- Đặt `MCP_TRANSPORT=stdio`.
- Chạy:
  ```bash
  python app/mcp_server.py
  ```
- MCP server đọc/ghi qua STDIN/STDOUT (hữu ích khi tích hợp vào process khác).

## 3. Biến môi trường liên quan

- `MCP_SERVER_ENABLED`, `MCP_SERVER_HOST`, `MCP_SERVER_PORT`.
- `MCP_TRANSPORT` (`sse`/`http`/`stdio`) và `SPOON_MCP_PATH`.
- `SPOON_MCP_TRANSPORT`, `SPOON_MCP_URL` – override URL khi SpoonGraph chạy ở process khác.
- `MCP_PROXY_TOKEN` – dùng để bảo vệ proxy `fastmcp dev`.
- `LOG_LEVEL` (tuỳ chọn) – điều chỉnh mức log (info/debug).

Chi tiết đầy đủ xem [ENVIRONMENT.md](./ENVIRONMENT.md).

## 4. Tích Hợp Với Backend

- MCP server sử dụng service backend (FastAPI). Backend phải chạy trước.
- Dùng `app.services` để truy vấn DB, vector DB, LLM.
- Khi upload document qua tool, cần quyền file system (đường dẫn tính từ gốc project).

## 5. Kiểm thử

- Dùng `fastmcp dev` và gọi từng tool theo checklist [TESTING.md](./TESTING.md).
- Các script trong `scripts/` (ví dụ `test_upload_document.py`) kiểm tra trực tiếp backend; với MCP nên ưu tiên Inspector để xem payload trả về.

## 6. Sự Cố Thường Gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|-----|-------------|-----------|
| `ModuleNotFoundError: No module named 'app'` | Chạy sai thư mục, thiếu `PYTHONPATH` | Chạy từ gốc dự án hoặc set `PYTHONPATH=.` |
| `FetchError: ECONNREFUSED` | Inspector trỏ sai URL | Dùng `http://localhost:3001/sse` (proxy) hoặc endpoint khớp transport (`/sse` hoặc `/mcp`) |
| `MCP error -32602` | JSON input sai schema | Kiểm tra lại JSON (tham khảo ví dụ trong README/tool docstring) |
| `Received request before initialization was complete` | MCP chưa kết nối backend/kho dữ liệu | Đảm bảo backend chạy trước, MCP log “Server ready” |

Tham khảo chi tiết hơn tại [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).

## 7. Định Hướng Phát Triển

- Thêm auth layer (API key, JWT) cho tool nhạy cảm.
- Cho phép cấu hình multi-tenant (nhiều workspace).
- Ghi log chi tiết cho mỗi tool call (metrics, audit trail).
- Tạo client CLI để tương tác nhanh (ví dụ `python scripts/mcp_cli.py`).
- Triển khai deploy container (Dockerfile) và expose qua HTTPS/reverse proxy.

