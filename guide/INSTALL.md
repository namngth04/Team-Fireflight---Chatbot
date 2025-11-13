# 🛠️ Cài Đặt

> Hướng dẫn dành cho Windows 10/11, Python 3.10+, PostgreSQL chạy trên `localhost:5433`. Điều chỉnh phù hợp nếu môi trường khác.

## 1. Yêu Cầu

- Python 3.10 trở lên
- PostgreSQL (đang chạy, user có quyền tạo DB)
- Node.js 18+
- Git

## 2. Clone Repository

```bash
git clone https://github.com/namngth04/Chatbot.git
cd Chatbot
```

Repo đã bao gồm mã nguồn Spoon AI (`spoon-core`) dưới dạng submodule nội bộ; không cần clone bổ sung.

## 3. Tạo Virtual Environment & Cài Backend

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install --upgrade pip
pip install -r requirements.txt
```

> Nếu sử dụng PowerShell, cần chạy `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` trước khi kích hoạt `.venv`.

## 4. Cài Spoon Core

```bash
cd spoon-core
pip install -e .
cd ..
```

> Lệnh `pip install -e .` cho phép bạn sửa trực tiếp mã nguồn Spoon nếu cần tuỳ chỉnh.

## 5. Cài Đặt Ollama (tuỳ chọn fallback)

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
- `MCP_SERVER_PORT=8001`
- `GEMINI_MODEL=gemini-2.5-flash`
- `OLLAMA_ENABLED=true` (nếu đã cài Ollama) + `OLLAMA_MODEL=<model>` và `OLLAMA_BASE_URL=<url-nếu-khác-default>`
- `MCP_SERVER_ENABLED=true` (để bật server mặc định)
- Tham khảo đầy đủ tại [ENVIRONMENT.md](./ENVIRONMENT.md)

## 7. Chuẩn Bị Database

1. Tạo database `chatbot_db` trên PostgreSQL (pgAdmin hoặc `psql`).
2. Chạy migrations:
   ```bash
   alembic upgrade head
   ```
3. Tạo admin mặc định:
   ```bash
   python scripts/create_admin.py
   ```

Nếu cần tạo thêm dữ liệu thử nghiệm, xem thêm [scripts/README.md](../scripts/README.md) (sẽ cập nhật trong tương lai).

## 8. Cài Đặt Frontend

```bash
cd frontend
npm install
cd ..
```

## 9. Kiểm Tra Lại

- `.venv` hoạt động và cài đủ packages.
- `.env` đã điền các biến trên (không commit file `.env`).
- Database có bảng sau khi migrate.
- `spoon-core` đã cài (`pip show spoon-ai`).
- Admin đã tạo thành công (kiểm tra bảng `users`).

Tiếp tục với [RUN.md](./RUN.md) để khởi động dự án. Nếu gặp sự cố trong quá trình cài đặt, xem [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).

