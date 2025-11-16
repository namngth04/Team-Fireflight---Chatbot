# 💻 Frontend Guide (Next.js)

## 1. Stack & cấu trúc

- Next.js 14 (App Router) + TypeScript + TailwindCSS + shadcn/ui.
- `app/` chứa route cấp cao: `login`, `chat`, `documents`, `users`, cùng layout bảo vệ qua `ProtectedRoute`.
- `components/`:
  - `components/chat/*` – `ConversationSidebar`, `MessageList`, `ChatInput`.
  - `components/ui/*` – wrapper shadcn (Button, Dialog, Input…).
  - `components/layout/Header.tsx`, `ClientLayout.tsx`.
- `contexts/AuthContext.tsx` lưu token + thông tin user trong `localStorage`, expose `login`, `logout`, `refreshProfile`.
- `lib/api/` chia API client theo domain (`auth.ts`, `users.ts`, `documents.ts`, `chat.ts`) sử dụng Axios wrapper `lib/api.ts`.
- `lib/types.ts` định nghĩa DTO đồng nhất với backend (`User`, `Document`, `Conversation`, `Message`).

## 2. Cài đặt & môi trường

```bash
cd frontend
npm install
npm run dev
```

Tùy biến endpoint bằng `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MCP_URL=http://localhost:8001/sse   # nếu frontend gọi MCP trực tiếp
```

> Frontend chỉ cần `NEXT_PUBLIC_API_URL` khi backend không nằm cùng origin. MCP URL là tuỳ chọn cho tool dev.

## 3. Scripts npm

| Lệnh | Mục đích |
|------|----------|
| `npm run dev` | Development server `http://localhost:3000`. |
| `npm run build` | Build production. |
| `npm run start` | Serve production build (sau `npm run build`). |
| `npm run lint` | ESLint theo cấu hình Next.js. |

## 4. Auth & điều hướng

- `AuthContext` lưu `accessToken` + `user` trong localStorage để survive refresh.
- Hook `useAuth()` được gọi trong `ProtectedRoute` để redirect về `/login` nếu chưa đăng nhập.
- Admin nhìn thấy tab `Users` và `Documents`, nhân viên chỉ thấy `Chat`.
- Logout xoá token + context, trả về `/login`.

## 5. Các trang chính

- **Login (`app/login/page.tsx`)** – Form đơn giản, gọi `auth.login`, hiển thị toast lỗi/thành công.
- **Chat (`app/chat/page.tsx`)** – Layout 2 cột (sidebar conversation + message feed). ChatInput gửi API `chat.sendMessage`, xử lý loading state và auto-scroll.
- **Documents (`app/documents/page.tsx`)** – Bảng tài liệu với search, filter theo `DocumentType`, modal upload (FormData), chỉnh description.
- **Users (`app/users/page.tsx`)** – CRUD user, modal xem mật khẩu (theo nghiệp vụ), validation phone/email.

## 6. UI/UX lưu ý

- Toast thông báo dùng shadcn `useToast`.
- Dialog upload sử dụng drag & drop component, tự reset sau khi call API.
- Các form gửi `FormData` nên **không** set `Content-Type`; Axios wrapper đã xoá header để browser tự đặt boundary.
- ChatInput disabled khi request pending để tránh spam, nút gửi căn giữa với icon consistent.
- Theme hiện tại hỗ trợ light, có thể mở rộng dark mode bằng `next-themes`.

## 7. Kiểm thử thủ công

- Đăng nhập admin ➜ thấy toast “Đăng nhập thành công”.
- Tạo user với email sai ➜ thông báo lỗi validation.
- Upload file > 50MB ➜ backend trả lỗi 400, UI hiện toast thất bại.
- Gửi tin chat ➜ message list auto-scroll xuống cuối, conversation sidebar cập nhật tiêu đề mới.
- Đổi qua user role employee ➜ không thấy menu quản trị.

## 8. Gợi ý mở rộng

- Tích hợp `@tanstack/react-query` để cache API và xử lý refetch.
- Thêm dark mode toggle, lưu theme vào localStorage.
- Hỗ trợ upload `.pdf`/`.docx` + preview (dùng worker hoặc chuyển đổi server side).
- Áp dụng role-based UI granular (ẩn nút upload khi không có quyền).
- Thêm e2e test (Playwright/Cypress) cho login + luồng chat.
