'use client';

import { AuthProvider } from '@/contexts/AuthContext';
import { ReactNode } from 'react';

interface ClientLayoutProps {
  children: ReactNode;
}

export default function ClientLayout({ children }: ClientLayoutProps) {
  return <AuthProvider>{children}</AuthProvider>;
}

