# 🛠️ Cài Đặt

> Hướng dẫn dành cho Windows 10/11, Python 3.10+, PostgreSQL chạy trên `localhost:5433`. Điều chỉnh phù hợp nếu môi trường khác.

## 1. Yêu Cầu

- Python 3.10 trở lên
- PostgreSQL (đang chạy, user có quyền tạo DB)
- Node.js 18+
- Git

## 2. Clone repository

```bash
git clone <repo-url> Team-Fireflight---Chatbot
cd Team-Fireflight---Chatbot
```

Repo đã bao gồm phần phụ thuộc Spoon AI (`spoon-core/`) nên không cần clone riêng. Nếu pull từ fork khác, đảm bảo submodule/thư mục này có đầy đủ file Python.

## 3. Tạo Virtual Environment & Cài Backend

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install --upgrade pip
pip install -r requirements.txt
```

> Nếu sử dụng PowerShell, cần chạy `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` trước khi kích hoạt `.venv`.

## 4. Cài Spoon core (editable)

```bash
cd spoon-core
pip install -e .
cd ..
```

> Lệnh editable cho phép backend sử dụng bản Spoon AI nội bộ và dễ vá lỗi nhanh. Kiểm tra lại bằng `pip show spoon-ai`.

## 5. Cài đặt Ollama (tuỳ chọn fallback)

- Tải từ [https://ollama.ai/download](https://ollama.ai/download).
- Sau khi cài, chạy `ollama serve` trong một terminal khác.
- Kéo model khuyến nghị (ví dụ `qwen2.5:7b-instruct`):
  ```bash
  ollama pull qwen2.5:7b-instruct
  ```
- Điều chỉnh biến môi trường `OLLAMA_MODEL` tương ứng.

## 6. Tạo `.env`

```bash
copy env.example .env           # Windows
# cp env.example .env
```

Cập nhật các biến bắt buộc:

- `DATABASE_URL=postgresql://<user>:<password>@localhost:5433/chatbot_db`
- `GEMINI_API_KEY=<google-gemini-api-key>`
- `JWT_SECRET_KEY=<chuỗi-ngẫu-nhiên>`
- `SECRET_KEY=<chuỗi-ngẫu-nhiên>`
- `MCP_SERVER_PORT=8001`, `MCP_SERVER_ENABLED=true`
- `GEMINI_MODEL=gemini-2.5-flash`
- `OLLAMA_ENABLED=true` (nếu dùng fallback) + `OLLAMA_MODEL=<model>` và `OLLAMA_BASE_URL=<url-nếu-khác-default>`
- `CORS_ORIGINS=http://localhost:3000`
- Các biến còn lại xem [ENVIRONMENT.md](./ENVIRONMENT.md)

## 7. Chuẩn bị database

1. Tạo database `chatbot_db` trên PostgreSQL (pgAdmin hoặc `psql`).
2. Chạy migrations:
   ```bash
   alembic upgrade head
   ```
3. Tạo admin mặc định:
   ```bash
   python scripts/create_admin.py
   ```

> Script hỏi username/password và lưu user admin với mật khẩu băm bcrypt. Nếu muốn seed thêm dữ liệu hoặc kiểm thử upload, tham khảo `scripts/*.py` và thư mục `sample_documents/`.

## 8. Cài đặt frontend

```bash
cd frontend
npm install
cd ..
```

## 9. Kiểm tra lại trước khi chạy

- `.venv` hoạt động và cài đủ packages.
- `.env` đã điền các biến chính, không commit file này.
- Database đã migrate (kiểm tra bảng `users`, `documents`, `conversations`, `messages`).
- `pip show spoon-ai` và `pip show chromadb` trả kết quả.
- Admin mặc định tồn tại (truy vấn bảng `users` hoặc đăng nhập thử).
- Thư mục `sample_documents/` sẵn sàng để upload thử nghiệm.

Tiếp tục với [RUN.md](./RUN.md) để khởi động từng dịch vụ. Nếu gặp lỗi ở bước nào, xem [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).

