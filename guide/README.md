# 📘 Project Guide

Thư mục `guide/` là nguồn tài liệu duy nhất cần theo dõi khi bàn giao cho đội phát triển/vận hành. Mỗi file tập trung vào một chủ đề, cập nhật đúng với kiến trúc FastAPI + Spoon AI hiện tại.

## Sơ đồ tài liệu

- [INSTALL.md](./INSTALL.md) – Chuẩn bị môi trường (Python, Node, PostgreSQL, Spoon core), tạo `.env`, migrate DB, cài frontend.
- [ENVIRONMENT.md](./ENVIRONMENT.md) – Toàn bộ biến môi trường chia nhóm (DB/JWT, LLM, MCP, lưu trữ, frontend).
- [RUN.md](./RUN.md) – Thứ tự bật dịch vụ (PostgreSQL → FastAPI → Ollama → MCP → Next.js), kèm lệnh nhanh và mẹo giám sát.
- [BACKEND.md](./BACKEND.md) – Kiến trúc backend, pipeline tài liệu, luồng chat Spoon graph, script quản trị.
- [FRONTEND.md](./FRONTEND.md) – App Router layout, API layer, AuthContext, checklist UI/UX.
- [MCP_SERVER.md](./MCP_SERVER.md) – Khởi chạy FastMCP server, danh sách tool (`policy_txt_lookup`, `ops_txt_lookup`, `conversation_history_simple`, `upload_document`), cách dùng Inspector/proxy.
- [TESTING.md](./TESTING.md) – Checklist smoke test (API, frontend, chat, MCP, vector DB) + payload mẫu.
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) – Lỗi thường gặp (DB, MCP, Gemini, Ollama, frontend) và hướng xử lý.

> Các tài liệu cũ trong `docs/` đã bỏ và bị ignore. Luôn cập nhật/tra cứu tại `guide/` để tránh sai lệch.

