# 🛠️ Troubleshooting

Tổng hợp lỗi phổ biến và cách xử lý trong quá trình phát triển, chạy thử dự án.

## 1. Backend & Database

| Vấn đề | Triệu chứng | Giải pháp |
|--------|-------------|-----------|
| Database chưa chạy | Lỗi kết nối `psycopg2.OperationalError` | Kiểm tra PostgreSQL (port 5433), chạy lại service, đảm bảo `.env` đúng `DATABASE_URL`. |
| Migration lỗi | `relation already exists` hoặc `No such table` | Kiểm tra lịch sử, dùng `alembic downgrade -1` rồi `upgrade head`; xoá DB và migrate lại nếu cần. |
| 422 khi tạo user | API trả `422 Unprocessable Entity` | Kiểm tra payload, format email/phone, password rỗng; xem log FastAPI để biết field nào lỗi. |
| Lỗi CORS | Frontend không gọi được API | Cập nhật CORS trong `app/main.py`, đặt `FRONTEND_URL` và bật `allow_credentials=True` nếu cần. |

## 2. MCP Server

| Vấn đề | Triệu chứng | Giải pháp |
|--------|-------------|-----------|
| `ModuleNotFoundError: No module named 'app'` | Chạy `fastmcp dev app/mcp_server.py` báo lỗi | Chạy lệnh từ thư mục gốc dự án hoặc thêm `PYTHONPATH=.` trước khi chạy. |
| `FetchError: ECONNREFUSED` | Inspector báo không kết nối được | Đảm bảo MCP server đang chạy. Kiểm tra URL (phải có `/mcp/` khi dùng trực tiếp) và port. |
| `Invalid request parameters` (-32602) | Tool trả lỗi | Kiểm tra JSON input so với schema (docstring tool). Thử với payload mẫu trong [TESTING.md](./TESTING.md). |
| `Received request before initialization was complete` | Warning trong log | Backend chưa sẵn sàng hoặc vector DB chưa init. Chờ backend chạy xong, đảm bảo DB và Chroma init thành công. |

## 3. Gemini & LLM

| Vấn đề | Triệu chứng | Giải pháp |
|--------|-------------|-----------|
| Rate-limit Gemini | Response lỗi 429, log hiển thị `RateLimitError` | Đã có retry/backoff. Nếu vẫn xảy ra, chuyển sang model có quota cao hơn hoặc kích hoạt fallback Ollama. |
| `GEMINI_API_KEY` sai | Lỗi auth từ provider | Kiểm tra `.env`, đảm bảo key hợp lệ và service account được cấp quyền. |
| Response rỗng | Bot trả lời không có dữ liệu | Kiểm tra tài liệu đã upload và vector DB; chạy lại script test; xem log `retrieved_documents`. |

## 4. Ollama

| Vấn đề | Triệu chứng | Giải pháp |
|--------|-------------|-----------|
| `ollama` command not found | Terminal báo không tồn tại | Đảm bảo đã cài Ollama và thêm vào PATH. Trên Windows cần logout/login sau khi cài. |
| Model chưa tải | Lỗi khi fallback | Chạy `ollama pull <model>` trước. Kiểm tra `OLLAMA_MODEL` khớp tên model. |
| Server không chạy sau restart | Không kết nối 11434 | Ollama không auto-start. Chạy `ollama serve` thủ công hoặc cấu hình service tự chạy. |

## 5. Frontend

| Vấn đề | Triệu chứng | Giải pháp |
|--------|-------------|-----------|
| "Cannot update a component while rendering..." | React runtime error | Đã fix bằng việc điều chỉnh logic Router. Nếu tái diễn, kiểm tra hook setState trong render. |
| "Objects are not valid as a React child" | Hiển thị object trực tiếp | Đảm bảo component chỉ render string/element (đã xử lý trong UI). |
| UI blur hoặc lệch | Input chat mờ, nút send lệch | Đã căn chỉnh, nếu khác hãy kiểm tra CSS override hoặc custom tailwind. |

## 6. Khác

| Vấn đề | Triệu chứng | Giải pháp |
|--------|-------------|-----------|
| `ModuleNotFoundError` bất chợt | Một số file chạy được, file khác không | Kiểm tra `PYTHONPATH`, chạy `python -m` thay vì `python path/to/file.py`. |
| Thiếu tài liệu mẫu | `FileNotFoundError` khi test upload | Đảm bảo `resources/sample_documents/TAI_LIEU_MAU_CHINH_SACH.txt` tồn tại. |
| Git ignore docs | Thư mục `docs/` không hiển thị | Cố ý bỏ qua trong `.gitignore`. Sử dụng `guide/` cho tài liệu chính thức. |

Nếu sự cố không nằm trong danh sách, thu thập log (backend, MCP, frontend console) và mô tả thao tác để dễ tái现. Update tài liệu này khi phát hiện issue mới.

