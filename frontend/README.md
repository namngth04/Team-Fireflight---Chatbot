# 🖥️ Frontend - Chatbot Nội Bộ Công Ty

Frontend cho hệ thống chatbot nội bộ công ty sử dụng Next.js, TypeScript, và Tailwind CSS.

## 🚀 Quick Start

### 1. **Install Dependencies**

```bash
npm install
```

### 2. **Setup Environment Variables**

Tạo file `.env.local`:

```env
# API Base URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# App Name
NEXT_PUBLIC_APP_NAME=Chatbot Nội Bộ Công Ty
```

### 3. **Run Development Server**

```bash
npm run dev
```

Frontend sẽ chạy tại: http://localhost:3000

## 📋 Features

### ✅ Authentication
- Login với username/password
- JWT token management
- Auto-logout khi token expired
- Protected routes

### ✅ User Management (Admin only)
- List users
- Search users
- Create user
- Update user
- Delete user

### ✅ Protected Routes
- Route guard cho `/chat`
- Route guard cho `/users` (Admin only)
- Auto-redirect đến `/login` khi chưa đăng nhập

## 🛠️ Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Context API (React)
- **API Client**: Axios
- **Authentication**: JWT (localStorage)

## 📁 Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Home page (redirect)
│   ├── login/
│   │   └── page.tsx        # Login page
│   ├── chat/
│   │   └── page.tsx        # Chat page (protected)
│   └── users/
│       └── page.tsx        # User management page (Admin only)
├── components/
│   ├── ClientLayout.tsx    # Client layout wrapper
│   └── ProtectedRoute.tsx  # Protected route component
├── contexts/
│   └── AuthContext.tsx     # Authentication context
├── lib/
│   ├── api.ts              # API client (axios)
│   ├── api/
│   │   ├── auth.ts         # Auth API
│   │   └── users.ts        # Users API
│   └── types.ts            # TypeScript types
└── .env.local              # Environment variables
```

## 🧪 Testing

### Test Authentication

1. Mở browser, truy cập http://localhost:3000
2. Redirect đến `/login`
3. Đăng nhập với `admin/admin`
4. Redirect đến `/chat`

### Test User Management

1. Đăng nhập với `admin/admin`
2. Truy cập `/users`
3. Tạo user mới
4. Search users
5. Update user
6. Delete user

## 📚 Documentation

- [Giai Đoạn 5 - README](../docs/giai-doan-5/README.md)
- [Hướng Dẫn Test](../docs/giai-doan-5/HUONG_DAN_TEST.md)
- [Kết Quả Giai Đoạn 5](../docs/giai-doan-5/KET_QUA_GIAI_DOAN_5.md)

## 🐛 Troubleshooting

### CORS Error

Nếu gặp lỗi CORS, kiểm tra backend CORS configuration:
- `CORS_ORIGINS` trong `.env` phải bao gồm `http://localhost:3000`

### Token Expired

Nếu token hết hạn:
- Token sẽ được xóa tự động
- User sẽ được redirect đến `/login`

### API Connection Error

Nếu không kết nối được API:
- Kiểm tra backend server đang chạy
- Kiểm tra `NEXT_PUBLIC_API_URL` trong `.env.local`
- Kiểm tra network tab trong browser DevTools

## 🚀 Build

### Build for Production

```bash
npm run build
```

### Start Production Server

```bash
npm start
```

## 📝 License

MIT License
