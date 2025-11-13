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

## 3. MCP Server

### 3.1 Chạy trực tiếp (HTTP)

```bash
python app/mcp_server.py
```

- Endpoint: `http://localhost:8001/mcp/` (điều chỉnh bằng `MCP_SERVER_PORT`).
- Log hiển thị danh sách tool và transport đã kích hoạt.
- Thích hợp cho ứng dụng nội bộ gọi trực tiếp qua HTTP.

### 3.2 Dùng MCP Inspector (dev)

```bash
fastmcp dev app/mcp_server.py
```

- Dev proxy: `http://localhost:3001/sse`
- Inspector tự mở trong trình duyệt (hoặc truy cập thủ công).
- Cấu hình Inspector:
  - Transport: `Streamable HTTP`
  - URL: `http://localhost:3001/sse` (proxy)
  - Connection: `Direct`
- Để kết nối trực tiếp thay vì proxy, đặt `MCP_TRANSPORT=http` và dùng `http://localhost:8001/mcp/`.

### 3.3 Lưu Ý

- Backend FastAPI phải chạy trước vì MCP server gọi service backend.
- Nếu `OLLAMA_ENABLED=true`, phải có `ollama serve` + model tương ứng.
- Khi gặp lỗi `ModuleNotFoundError: No module named 'app'`, kiểm tra `PYTHONPATH` hoặc chạy từ thư mục gốc dự án.
- Chi tiết hơn xem [MCP_SERVER.md](./MCP_SERVER.md).

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

## 5. Luồng Khởi Động Khuyến Nghị

1. PostgreSQL (nếu sử dụng dịch vụ rời).
2. Backend FastAPI (`uvicorn ...`).
3. Ollama (nếu dùng fallback): `ollama serve`.
4. MCP server (`python app/mcp_server.py` hoặc `fastmcp dev ...`).
5. Frontend (`npm run dev`).

> Gợi ý: dùng nhiều terminal/tab riêng cho từng dịch vụ để dễ theo dõi log.

## 6. Biến Môi Trường Quan Trọng Khi Chạy

- Backend: `DATABASE_URL`, `GEMINI_API_KEY`, `JWT_SECRET_KEY`, `SECRET_KEY`, `GEMINI_MODEL`, `OLLAMA_*`, `MCP_SERVER_PORT`, `MCP_TRANSPORT`.
- Frontend: `NEXT_PUBLIC_API_URL` (nếu cấu hình backend không chạy cùng domain), `NEXT_PUBLIC_MCP_URL` (tuỳ chọn).
- MCP: `MCP_SERVER_ENABLED`, `MCP_SERVER_PORT`, `MCP_TRANSPORT`, `MCP_PROXY_TOKEN` (khi đi qua proxy).
- Tham khảo chi tiết tại [ENVIRONMENT.md](./ENVIRONMENT.md).

## 7. Kiểm Tra Sau Khi Chạy

- Backend: `GET /docs` trả về 200, có thể thử gọi `POST /api/auth/login`.
- MCP: Inspector hiển thị “connected”, gọi thử tool `query_documents`.
- Frontend: đăng nhập admin, xem danh sách user/documents, gửi chat thử.
- Vector DB: chạy `python scripts/test_vector_database.py` để chắc chắn đã index.

## 8. Dừng Hệ Thống

- Với mỗi dịch vụ, dùng `Ctrl + C` trong terminal tương ứng.
- Nếu sử dụng `fastmcp dev`, khi đóng proxy nhớ tắt cả backend để tránh socket treo.
- PostgreSQL/Ollama: tắt theo cách riêng (ví dụ stop service hoặc đóng terminal).

