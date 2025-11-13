'use client';

import React, { useState, KeyboardEvent, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  loading?: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  disabled = false,
  loading = false,
  placeholder = 'Nhập câu hỏi của bạn...',
}) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  const handleSend = () => {
    if (!message.trim() || disabled || loading) return;

    onSendMessage(message.trim());
    setMessage('');

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <div className="flex items-end gap-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || loading}
            rows={1}
            className={cn(
              'w-full px-4 py-2.5 border border-gray-300 rounded-lg resize-none',
              'focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
              'transition-colors duration-200',
              'max-h-32 overflow-y-auto',
              'text-gray-900 font-normal placeholder:text-gray-400',
              'disabled:text-gray-500 disabled:placeholder:text-gray-300',
              (disabled || loading) && 'opacity-50 cursor-not-allowed'
            )}
            style={{ minHeight: '44px', lineHeight: '1.5' }}
          />
        </div>
        <Button
          onClick={handleSend}
          disabled={!message.trim() || disabled || loading}
          variant="primary"
          size="md"
          className="flex-shrink-0 h-[44px] min-w-[44px] px-4"
          isLoading={loading}
        >
          {loading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Send className="h-5 w-5" />
          )}
        </Button>
      </div>
      <p className="text-xs text-gray-500 mt-2 text-center">
        Nhấn Enter để gửi, Shift + Enter để xuống dòng
      </p>
    </div>
  );
};

