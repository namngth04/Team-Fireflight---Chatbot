# 🚀 Chạy Hệ Thống

Tài liệu này mô tả chi tiết cách khởi động từng thành phần, đảm bảo các dịch vụ phụ thuộc sẵn sàng và cách xác minh nhanh sau khi chạy.

## 1. Chuẩn Bị Chung

- Đảm bảo `.venv` đã được kích hoạt và `.env` đầy đủ biến (xem [ENVIRONMENT.md](./ENVIRONMENT.md)).
- PostgreSQL (port 5433) đang chạy.
- Nếu dùng fallback Ollama: chạy `ollama serve` trong một terminal riêng.
- Kiểm tra mô hình đã pull (`ollama list`).

## 2. Backend (FastAPI)

```bash
.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Swagger UI: `http://localhost:8000/docs`
- Redoc (nếu bật): `http://localhost:8000/redoc`
- Health-check (tuỳ cấu hình): `http://localhost:8000/health`
- Log xác nhận: “Application startup complete.”

### Lệnh hữu ích

- `alembic upgrade head` – cập nhật schema mới nhất.
- `python scripts/create_admin.py` – tạo lại tài khoản admin nếu cần.
- `pytest` – chạy unit/integration test backend.

## 3. MCP server

### 3.1 Chạy trực tiếp (SSE/HTTP)

```bash
python -m app.mcp_server
```

- Mặc định chạy transport `sse` với endpoint `http://localhost:8001/sse` (đổi bằng `MCP_SERVER_PORT` hoặc `SPOON_MCP_PATH`).
- Nếu muốn HTTP thuần, đặt `MCP_TRANSPORT=http` (endpoint `http://localhost:8001/mcp`).
- Log khởi động hiển thị danh sách tool (`policy_txt_lookup`, `ops_txt_lookup`, `upload_document`, `conversation_history_simple`).

### 3.2 Dùng MCP Inspector (dev)

```bash
fastmcp dev app/mcp_server.py
```

- Proxy SSE: `http://localhost:3001/sse`.
- Inspector sẽ mở trình duyệt; nếu không hãy tự truy cập URL trên.
- Cấu hình Inspector:
  - Transport: `Streamable HTTP`
  - URL: `http://localhost:3001/sse`
  - Connection: `Direct`
- Khi không dùng proxy, cấu hình URL về `http://localhost:8001/sse` (hoặc `/mcp` nếu chuyển sang HTTP).

### 3.3 Lưu ý

- Backend FastAPI **phải** chạy trước vì MCP dùng chung DB/session và utils của backend.
- Nếu bật fallback Ollama (`OLLAMA_ENABLED=true`), chắc chắn `ollama serve` đã chạy và model khớp `OLLAMA_MODEL`.
- Chạy lệnh từ thư mục gốc để tránh `ModuleNotFoundError: No module named 'app'`.
- Xem thêm [MCP_SERVER.md](./MCP_SERVER.md) cho cấu hình transport nâng cao.

## 4. Frontend (Next.js)

```bash
cd frontend
npm run dev
```

- URL: `http://localhost:3000`
- Biến môi trường frontend (nếu cần): tạo `frontend/.env.local`.
- Tài khoản đăng nhập mặc định: `admin` / mật khẩu đã đặt.

### Script hữu ích

- `npm run lint` – kiểm tra lint.
- `npm run build` – build production.
- `npm run start` – chạy production (sau khi build).

## 5. Luồng khởi động khuyến nghị

1. PostgreSQL (nếu không phải service luôn bật).
2. Backend FastAPI (`uvicorn app.main:app ...`).
3. Ollama (nếu dùng fallback): `ollama serve` + `ollama pull <model>`.
4. MCP server (`python -m app.mcp_server` hoặc `fastmcp dev ...`).
5. Frontend (`npm run dev`).

> Gợi ý: dùng nhiều terminal/tab riêng cho từng dịch vụ để dễ theo dõi log.

## 6. Biến môi trường quan trọng khi chạy

- Backend: `DATABASE_URL`, `GEMINI_API_KEY`, `JWT_SECRET_KEY`, `SECRET_KEY`, `GEMINI_MODEL`, `OLLAMA_*`, `MCP_SERVER_PORT`, `MCP_TRANSPORT`.
- Frontend: `NEXT_PUBLIC_API_URL` (nếu cấu hình backend không chạy cùng domain), `NEXT_PUBLIC_MCP_URL` (tuỳ chọn).
- MCP: `MCP_SERVER_ENABLED`, `MCP_SERVER_PORT`, `MCP_TRANSPORT`, `MCP_PROXY_TOKEN` (khi đi qua proxy).
- Tham khảo chi tiết tại [ENVIRONMENT.md](./ENVIRONMENT.md).

## 7. Kiểm tra sau khi chạy

- Backend: `GET /docs` trả về 200, có thể thử gọi `POST /api/auth/login`.
- MCP: Inspector hiển thị “connected”, gọi thử tool `policy_txt_lookup`.
- Frontend: đăng nhập admin, xem danh sách user/documents, gửi chat thử.
- Vector DB: chạy `python scripts/test_vector_database.py` để chắc chắn đã index.

## 8. Dừng Hệ Thống

- Với mỗi dịch vụ, dùng `Ctrl + C` trong terminal tương ứng.
- Nếu sử dụng `fastmcp dev`, khi đóng proxy nhớ tắt cả backend để tránh socket treo.
- PostgreSQL/Ollama: tắt theo cách riêng (ví dụ stop service hoặc đóng terminal).

