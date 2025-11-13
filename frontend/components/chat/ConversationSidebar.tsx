'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  MessageSquare,
  Plus,
  Trash2,
  Edit2,
  X,
  Check,
  Loader2,
} from 'lucide-react';
import { Conversation } from '@/lib/types';
import { chatAPI } from '@/lib/api/chat';
import { parseError } from '@/lib/utils/error';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';

interface ConversationSidebarProps {
  conversations: Conversation[];
  selectedConversationId: number | null;
  onSelectConversation: (conversationId: number) => void;
  onCreateConversation: () => void;
  onDeleteConversation: (conversationId: number) => void;
  onUpdateConversation: (conversationId: number, title: string) => void;
  loading?: boolean;
}

export const ConversationSidebar: React.FC<ConversationSidebarProps> = ({
  conversations,
  selectedConversationId,
  onSelectConversation,
  onCreateConversation,
  onDeleteConversation,
  onUpdateConversation,
  loading = false,
}) => {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const editInputRef = useRef<HTMLInputElement>(null);

  // Focus input when editing
  useEffect(() => {
    if (editingId && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingId]);

  // Start editing
  const startEdit = (conversation: Conversation) => {
    setEditingId(conversation.id);
    setEditTitle(conversation.title);
  };

  // Cancel editing
  const cancelEdit = () => {
    setEditingId(null);
    setEditTitle('');
  };

  // Save edit
  const saveEdit = async (conversationId: number) => {
    if (!editTitle.trim()) {
      cancelEdit();
      return;
    }

    try {
      await onUpdateConversation(conversationId, editTitle.trim());
      setEditingId(null);
      setEditTitle('');
    } catch (error) {
      console.error('Error updating conversation:', error);
    }
  };

  // Handle delete
  const handleDelete = async (conversationId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Bạn có chắc chắn muốn xóa cuộc trò chuyện này?')) {
      setDeletingId(conversationId);
      try {
        await onDeleteConversation(conversationId);
      } catch (error) {
        console.error('Error deleting conversation:', error);
      } finally {
        setDeletingId(null);
      }
    }
  };

  return (
    <div className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <Button
          onClick={onCreateConversation}
          variant="primary"
          size="sm"
          className="w-full flex items-center justify-center space-x-2"
        >
          <Plus className="h-4 w-4" />
          <span>Cuộc trò chuyện mới</span>
        </Button>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-center">
            <Loader2 className="h-5 w-5 animate-spin text-gray-400 mx-auto" />
          </div>
        ) : conversations.length === 0 ? (
          <div className="p-4 text-center text-sm text-gray-500">
            <MessageSquare className="h-8 w-8 text-gray-400 mx-auto mb-2" />
            <p>Chưa có cuộc trò chuyện nào</p>
          </div>
        ) : (
          <div className="p-2">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                className={cn(
                  'group relative mb-1 p-3 rounded-lg cursor-pointer transition-colors duration-150',
                  selectedConversationId === conversation.id
                    ? 'bg-indigo-100 text-indigo-900'
                    : 'hover:bg-gray-100 text-gray-900'
                )}
                onClick={() => onSelectConversation(conversation.id)}
              >
                {editingId === conversation.id ? (
                  <div className="flex items-center space-x-2">
                    <input
                      ref={editInputRef}
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          saveEdit(conversation.id);
                        } else if (e.key === 'Escape') {
                          cancelEdit();
                        }
                      }}
                      onClick={(e) => e.stopPropagation()}
                      className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        saveEdit(conversation.id);
                      }}
                      className="text-green-600 hover:text-green-700"
                    >
                      <Check className="h-4 w-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        cancelEdit();
                      }}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center space-x-2">
                      <MessageSquare className="h-4 w-4 flex-shrink-0" />
                      <p className="flex-1 text-sm truncate">{conversation.title}</p>
                    </div>
                    <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          startEdit(conversation);
                        }}
                        className="text-gray-400 hover:text-indigo-600 p-1"
                        title="Đổi tên"
                      >
                        <Edit2 className="h-3 w-3" />
                      </button>
                      <button
                        onClick={(e) => handleDelete(conversation.id, e)}
                        disabled={deletingId === conversation.id}
                        className="text-gray-400 hover:text-red-600 p-1 disabled:opacity-50"
                        title="Xóa"
                      >
                        {deletingId === conversation.id ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <Trash2 className="h-3 w-3" />
                        )}
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

