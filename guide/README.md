# 📘 Project Guide

Thư mục `guide/` là bộ tài liệu chính thức cho dự án chatbot nội bộ. Mỗi tài liệu tập trung vào một phần của hệ thống để dễ tra cứu và cập nhật.

## Tổng Quan Tài Liệu

- [INSTALL.md](./INSTALL.md) – Chuẩn bị môi trường, cài đặt backend, Spoon AI, frontend, cấu hình `.env`, thiết lập database.
- [RUN.md](./RUN.md) – Quy trình khởi động từng thành phần, quản lý biến môi trường và thứ tự đề xuất.
- [TESTING.md](./TESTING.md) – Checklist kiểm thử thủ công, hướng dẫn dùng script hỗ trợ.
- [ENVIRONMENT.md](./ENVIRONMENT.md) – Danh sách biến môi trường, mô tả giá trị, ghi chú bảo mật.
- [BACKEND.md](./BACKEND.md) – Kiến trúc backend, câu lệnh migration, seed, script quản trị, test.
- [FRONTEND.md](./FRONTEND.md) – Cấu trúc frontend, script npm, cấu hình UI, lưu ý triển khai.
- [MCP_SERVER.md](./MCP_SERVER.md) – Hướng dẫn vận hành MCP server (HTTP/SSE/STDIO), công cụ, xử lý sự cố.
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) – Các lỗi phổ biến (Gemini rate limit, Ollama, ModuleNotFoundError, kết nối MCP) và cách khắc phục.

> Lưu ý: Tài liệu cũ trong `docs/` chỉ phục vụ giai đoạn phát triển và đã bị `.gitignore`. Khi bàn giao hoặc chia sẻ với đội dự án, ưu tiên sử dụng bộ tài liệu trong `guide/`.

