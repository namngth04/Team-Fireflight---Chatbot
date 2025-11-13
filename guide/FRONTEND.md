# 💻 Frontend Guide (Next.js)

## 1. Công Nghệ & Cấu Trúc

- Next.js 14 (App Router) + TypeScript.
- TailwindCSS + shadcn/ui cho component.
- Quản lý trạng thái nhẹ nhàng qua React context (`contexts/AuthContext.tsx`).
- `frontend/app/` – pages (App Router) cho `login`, `chat`, `documents`, `users`.
- `frontend/components/` – UI component tái sử dụng (`ui`, `chat`, `layout`).
- `frontend/lib/api/` – Axios client chia theo domain (`auth`, `users`, `documents`, `chat`).
- `frontend/lib/types.ts` – định nghĩa kiểu chung.

## 2. Cài Đặt & Môi Trường

- Cài dependencies:
  ```bash
  cd frontend
  npm install
  ```
- Chạy development:
  ```bash
  npm run dev
  ```
- Tạo file `frontend/.env.local` (nếu cần):
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8000
  NEXT_PUBLIC_MCP_URL=http://localhost:8001/mcp/   # tuỳ chọn
  ```

## 3. Scripts npm

| Lệnh | Mục đích |
|------|----------|
| `npm run dev` | Chạy development server tại `http://localhost:3000`. |
| `npm run build` | Build production. |
| `npm run start` | Chạy production build (`npm run build` trước). |
| `npm run lint` | Kiểm tra lint (ESLint). |

## 4. Login & Session

- AuthContext lưu trữ thông tin user, token trong localStorage.
- Middleware kiểm tra token, redirect về `/login` nếu chưa đăng nhập.
- Đăng nhập admin hiển thị dashboard (users/documents); nhân viên vào trực tiếp trang chat.

## 5. UI Highlights

- Chat UI tham khảo ChatGPT: chat panel, conversation sidebar, message bubbles.
- User management:
  - Modal tạo/sửa user với validation rõ ràng.
  - Alert success/error (Toast) cho login, tạo user, cập nhật user.
  - Modal xem password (theo yêu cầu nghiệp vụ).
- Document management:
  - Upload modal với drag & drop (FileUpload component).
  - Filter/search, view details, edit description, delete.
  - Bỏ backdrop tối khi mở modal (theo feedback).
- Theme: phong cách tối ưu cho cả light/dark (có thể mở rộng).

## 6. Kiểm Thử Thủ Công

- Đăng nhập admin → toast “đăng nhập thành công”.
- Tạo user email sai → hiển thị lỗi.
- Upload file > 50MB → hiển thị thông báo vượt giới hạn.
- Chatbot: gửi tin → scroll auto xuống cuối, nút send căn giữa, input rõ nét.
- Conversation history: tạo nhiều conversation, chuyển nhanh, kiểm tra ghi nhớ.

## 7. Tối Ưu & Best Practices

- Axios interceptor tự động bỏ `Content-Type` khi gửi FormData (để browser tự set).
- Sử dụng `React.Suspense`/`loading.tsx` để hiển thị skeleton (có thể mở rộng).
- Hạn chế duplicate fetch: API layer xử lý cache đơn giản (cần thiết có thể dùng SWR/React Query).
- Giữ UI consistent: dùng component shadcn (Button, Input, Dialog, Alert).

## 8. Lộ Trình Phát Triển

- Hỗ trợ upload `.pdf`, `.docx` (kết hợp viewer).
- Thêm dark mode toggle, tùy chỉnh theme.
- Tích hợp `react-query` hoặc `tanstack query` để caching API.
- Tracking analytics (ví dụ RudderStack) cho hành vi người dùng.
- Tối ưu build cho production (image optimization, bundle analyzer).

