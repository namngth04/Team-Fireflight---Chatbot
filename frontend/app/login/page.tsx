'use client';

import { useState, FormEvent, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { parseError } from '@/lib/utils/error';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { Loading } from '@/components/ui/Loading';
import { Card } from '@/components/ui/Card';
import { MessageSquare, User, Lock } from 'lucide-react';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();

  // Redirect if already authenticated (using useEffect to avoid render phase update)
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.push('/chat');
    }
  }, [isAuthenticated, authLoading, router]);

  // Show loading while checking authentication
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50">
        <Loading size="lg" text="Đang tải..." />
      </div>
    );
  }

  // Don't render login form if already authenticated
  if (isAuthenticated) {
    return null;
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      await login({ username, password });
      setSuccess('Đăng nhập thành công! Đang chuyển hướng...');
      // Redirect after a short delay to show success message
      setTimeout(() => {
        router.push('/chat');
      }, 1000);
    } catch (err: any) {
      const errorMessage = parseError(err) || 'Đăng nhập thất bại. Vui lòng kiểm tra lại tên đăng nhập và mật khẩu.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        <Card className="shadow-xl">
          {/* Logo/Header */}
          <div className="text-center mb-8">
            <div className="mx-auto h-12 w-12 bg-indigo-600 rounded-full flex items-center justify-center mb-4">
              <MessageSquare className="h-6 w-6 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900">
              Đăng nhập
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Chatbot nội bộ công ty
            </p>
          </div>

          {/* Form */}
          <form className="space-y-6" onSubmit={handleSubmit}>
            {/* Success Alert */}
            {success && (
              <Alert
                type="success"
                message={success}
                onClose={() => setSuccess('')}
              />
            )}

            {/* Error Alert */}
            {error && (
              <Alert
                type="error"
                message={error}
                onClose={() => setError('')}
              />
            )}

            {/* Username Input */}
            <Input
              label="Tên đăng nhập"
              type="text"
              placeholder="Nhập tên đăng nhập"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              icon={<User className="h-5 w-5" />}
              required
            />

            {/* Password Input */}
            <Input
              label="Mật khẩu"
              type="password"
              placeholder="Nhập mật khẩu"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={<Lock className="h-5 w-5" />}
              required
            />

            {/* Submit Button */}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={loading}
              className="w-full"
            >
              Đăng nhập
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}

