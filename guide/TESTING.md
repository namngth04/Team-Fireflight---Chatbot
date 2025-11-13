# 🧪 Kiểm Thử & Kiểm Tra Nhanh

Tài liệu này giữ vai trò checklist kiểm tra thủ công (smoke test) sau khi cài đặt hoặc deploy. Với từng nhóm, có thể mở rộng thành case chi tiết trong tương lai.

## 1. Chuẩn Bị Chung

- Backend, MCP server, frontend đều đang chạy (xem [RUN.md](./RUN.md)).
- Đảm bảo đã có ít nhất một tài liệu `.txt` (sử dụng `resources/sample_documents/TAI_LIEU_MAU_CHINH_SACH.txt` nếu cần).
- Tài khoản admin hoạt động.
- Có kết nối internet (để gọi Gemini).

## 2. API Backend (Postman/cURL)

| Bước | Endpoint | Nội dung kiểm tra | Ghi chú |
|------|----------|-------------------|---------|
| 1 | `POST /api/auth/login` | Nhận token, body trả về `access_token`, `token_type` | Dùng admin credentials |
| 2 | `GET /api/users/` | Trả về danh sách người dùng | Header `Authorization: Bearer <token>` |
| 3 | `POST /api/users/` | Tạo user mới, expect 201 | Kiểm tra validation email/phone |
| 4 | `PUT /api/users/{id}` | Cập nhật user, nhận alert thành công | |
| 5 | `POST /api/documents/upload` | Upload `.txt` < 50MB, expect 201 | Form-data: `file`, `document_type`, `description` |
| 6 | `GET /api/documents/?document_type=policies` | Filter hoạt động, pagination nếu có | |
| 7 | `DELETE /api/documents/{id}` (tuỳ chọn) | Xoá document, expect 200 | Chỉ test nếu cần |

## 3. Frontend (Manual)

1. Đăng nhập admin: xuất hiện toast thành công, handle lỗi nếu nhập sai.
2. Điều hướng tới `Quản lý người dùng`:
   - Tạo user mới, kiểm tra validation realtime (email, phone).
   - Sửa user, xem thông báo thành công, modal đóng đúng.
   - Xem/ẩn mật khẩu theo yêu cầu (modal xem password).
3. Điều hướng tới `Quản lý tài liệu`:
   - Upload file `.txt`, kiểm tra hiển thị trong bảng.
   - Sử dụng search & filter, pagination (nếu có).
   - Xem chi tiết (modal) đảm bảo backdrop đẹp, UI đúng thiết kế ChatGPT-like.
4. Đăng nhập bằng user vừa tạo:
   - Kiểm tra chuyển hướng tới trang chat, không hiển thị dashboard admin.

## 4. Chatbot & RAG

1. Tạo hội thoại mới trên `/chat`.
2. Đặt câu hỏi “Chính sách nghỉ phép năm 2025 như thế nào?”.
3. Xác minh:
   - Phản hồi chứa thông tin trích từ tài liệu.
   - `provider_used` trong log/backend là `gemini-2.5-flash`.
   - Tin nhắn được lưu (refresh trang vẫn hiển thị).
4. Tắt tạm GEMINI API key (hoặc chỉnh sai), gửi câu hỏi mới:
   - Fallback Ollama hoạt động nếu đã bật.
   - Log hiển thị retry/backoff.
5. Đặt câu hỏi không có trong tài liệu → bot trả lời lịch sự, gợi ý upload thêm dữ liệu.

## 5. MCP Tools (Inspector hoặc client)

| Tool | Input mẫu | Kỳ vọng |
|------|-----------|---------|
| `query_documents` | `{"query": "nghỉ phép", "top_k": 3}` | `results` trả về <= 3, metadata đầy đủ |
| `upload_document` | `{"file_path": "resources/sample_documents/TAI_LIEU_MAU_CHINH_SACH.txt", ...}` | Trả về `id`, `filename`, DB tăng record |
| `chat_with_bot` | `{"message": "...", "username": "admin"}` | Trả về `conversation_id`, `response`, `provider_used` |
| `get_conversation_history` | `{"conversation_id": <id>}` | Trả về danh sách messages, có timestamp |

> Thử cả 2 chế độ: thông qua proxy (`fastmcp dev`) và kết nối trực tiếp (`http://localhost:8001/mcp/`).

## 6. Vector Database

- Chạy `python scripts/test_vector_database.py`.
- Kỳ vọng:
  - Hiển thị tổng số document trong collection.
  - In thông tin metadata (filename, document_type, chunk).
  - Query mẫu (`nghỉ phép`, `bảo mật`, `làm việc từ xa`) trả kết quả > 0.
- Nếu collection rỗng → upload lại tài liệu và chạy script lần nữa.

## 7. Kiểm Tra Log & Giám Sát

- `uvicorn`:
  - Không có lỗi 500 trong luồng chính.
  - Khi upload file, log hiển thị đường dẫn và document type.
- MCP server:
  - Không còn lỗi `ModuleNotFoundError`.
  - Không thấy `FetchError: ECONNREFUSED` (đảm bảo URL `/mcp/` đúng).
  - Khi rate-limit Gemini, log ghi nhận retry và fallback.
- Frontend (console):
  - Không báo lỗi runtime (React “Cannot update a component while rendering…” đã được fix).

## 8. Checklist Tổng

- [ ] Backend API hoạt động, authentication pass.
- [ ] Admin tạo/sửa user thành công, validation chuẩn.
- [ ] Upload/search/filter tài liệu hoạt động.
- [ ] Chatbot trả lời dựa trên tài liệu, lưu lịch sử.
- [ ] MCP tools chạy được cả HTTP và thông qua proxy.
- [ ] Vector database có dữ liệu và query trả kết quả liên quan.
- [ ] Log sạch, không còn lỗi đã từng gặp trong quá trình phát triển.

Nếu bất kỳ bước nào thất bại, tham khảo [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) để xử lý.

