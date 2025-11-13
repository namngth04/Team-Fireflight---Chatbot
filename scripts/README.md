# 📜 Scripts Guide

Các script Python hỗ trợ quản trị hệ thống và kiểm thử nhanh. Chạy script luôn từ thư mục gốc dự án (đã kích hoạt `.venv`).

## 1. Quản Trị

| Script | Mục đích | Cách chạy |
|--------|---------|-----------|
| `create_admin.py` | Tạo admin mặc định (username `admin`) | `python scripts/create_admin.py` (sẽ hỏi password) |
| `generate_secrets.py` | Sinh chuỗi random cho `.env` | `python scripts/generate_secrets.py` |
| `test_token.py` | Kiểm tra token JWT có hợp lệ | `python scripts/test_token.py <token>` |

## 2. Kiểm Thử Document & Vector DB

| Script | Mục đích | Cách chạy |
|--------|---------|-----------|
| `test_upload_document.py` | Đăng nhập → upload tài liệu mẫu → liệt kê → xem chi tiết. Sử dụng file ở `resources/sample_documents/`. | `python scripts/test_upload_document.py` |
| `test_vector_database.py` | Kiểm tra dữ liệu trong ChromaDB, query thử một số từ khoá. | `python scripts/test_vector_database.py` |

## 3. Ghi Chú

- Các script phụ thuộc vào backend đang chạy (`uvicorn app.main:app --reload`).
- `test_upload_document.py` yêu cầu tài khoản admin tồn tại.
- Có thể chỉnh `BASE_URL` trong script nếu backend deploy ở địa chỉ khác.
- Khi cần mở rộng (ví dụ script xoá documents), tạo file mới trong thư mục này và cập nhật README.

