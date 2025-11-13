'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { LogOut, User, Users, MessageSquare, ChevronDown, FileText } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export const Header: React.FC = () => {
  const { user, logout, isAdmin } = useAuth();
  const router = useRouter();
  const [showUserMenu, setShowUserMenu] = useState(false);
  
  const handleLogout = () => {
    logout();
    router.push('/login');
  };
  
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <button
              onClick={() => router.push('/chat')}
              className="flex items-center space-x-2 text-gray-900 hover:text-indigo-600 transition-colors duration-200"
            >
              <MessageSquare className="h-6 w-6" />
              <span className="text-xl font-bold">Chatbot Nội Bộ</span>
            </button>
          </div>
          
          {/* Navigation */}
          <nav className="flex items-center space-x-4">
            {/* Chat Link */}
            <button
              onClick={() => router.push('/chat')}
              className="text-gray-700 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200"
            >
              <MessageSquare className="h-5 w-5" />
            </button>
            
            {/* Users Link (Admin only) */}
            {isAdmin && (
              <button
                onClick={() => router.push('/users')}
                className="text-gray-700 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200"
              >
                <Users className="h-5 w-5" />
              </button>
            )}

            {/* Documents Link (Admin only) */}
            {isAdmin && (
              <button
                onClick={() => router.push('/documents')}
                className="text-gray-700 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200"
              >
                <FileText className="h-5 w-5" />
              </button>
            )}
            
            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center space-x-2 text-gray-700 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200"
              >
                <User className="h-5 w-5" />
                <span className="hidden sm:block">{user?.full_name || user?.username}</span>
                {isAdmin && (
                  <Badge variant="admin" className="hidden sm:inline-flex">
                    Admin
                  </Badge>
                )}
                <ChevronDown className="h-4 w-4" />
              </button>
              
              {/* Dropdown Menu */}
              {showUserMenu && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowUserMenu(false)}
                  />
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-20 border border-gray-200">
                    <div className="px-4 py-2 border-b border-gray-200">
                      <p className="text-sm font-medium text-gray-900">
                        {user?.full_name || user?.username}
                      </p>
                      <p className="text-xs text-gray-500">{user?.email}</p>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors duration-200 flex items-center space-x-2"
                    >
                      <LogOut className="h-4 w-4" />
                      <span>Đăng xuất</span>
                    </button>
                  </div>
                </>
              )}
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
};

