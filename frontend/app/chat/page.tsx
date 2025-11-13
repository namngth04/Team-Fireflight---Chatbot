'use client';

import { useState, useEffect, useCallback } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import { Header } from '@/components/layout/Header';
import { ConversationSidebar } from '@/components/chat/ConversationSidebar';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { Alert } from '@/components/ui/Alert';
import { Loading } from '@/components/ui/Loading';
import { chatAPI } from '@/lib/api/chat';
import {
  Conversation,
  ConversationWithMessages,
  Message,
  ConversationCreate,
  ConversationUpdate,
  MessageCreate,
} from '@/lib/types';
import { parseError } from '@/lib/utils/error';
import { Loader2 } from 'lucide-react';

export default function ChatPage() {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<ConversationWithMessages | null>(null);
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [conversationsLoading, setConversationsLoading] = useState(false);

  // Load conversations
  const loadConversations = useCallback(async () => {
    try {
      setConversationsLoading(true);
      setError('');
      const data = await chatAPI.listConversations();
      setConversations(data);
    } catch (err: any) {
      const errorMessage = parseError(err) || 'Không thể tải danh sách cuộc trò chuyện. Vui lòng thử lại.';
      setError(errorMessage);
    } finally {
      setConversationsLoading(false);
      setLoading(false);
    }
  }, []);

  // Load conversation with messages
  const loadConversation = useCallback(async (conversationId: number) => {
    try {
      setLoading(true);
      setError('');
      const data = await chatAPI.getConversation(conversationId);
      setSelectedConversation(data);
      setMessages(data.messages || []);
      setSelectedConversationId(conversationId);
    } catch (err: any) {
      const errorMessage = parseError(err) || 'Không thể tải cuộc trò chuyện. Vui lòng thử lại.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Auto-select first conversation if no conversation is selected and conversations are loaded
  useEffect(() => {
    if (conversations.length > 0 && !selectedConversationId && !loading) {
      setSelectedConversationId(conversations[0].id);
    }
  }, [conversations, selectedConversationId, loading]);

  // Load conversation when selected
  useEffect(() => {
    if (selectedConversationId) {
      loadConversation(selectedConversationId);
    } else {
      setSelectedConversation(null);
      setMessages([]);
    }
  }, [selectedConversationId, loadConversation]);

  // Create new conversation
  const handleCreateConversation = async () => {
    try {
      setError('');
      const newConversation = await chatAPI.createConversation({});
      setConversations([newConversation, ...conversations]);
      setSelectedConversationId(newConversation.id);
    } catch (err: any) {
      const errorMessage = parseError(err) || 'Không thể tạo cuộc trò chuyện mới. Vui lòng thử lại.';
      setError(errorMessage);
    }
  };

  // Select conversation
  const handleSelectConversation = (conversationId: number) => {
    setSelectedConversationId(conversationId);
  };

  // Delete conversation
  const handleDeleteConversation = async (conversationId: number) => {
    try {
      setError('');
      await chatAPI.deleteConversation(conversationId);
      setConversations(conversations.filter((c) => c.id !== conversationId));
      
      // If deleted conversation was selected, select first conversation or clear
      if (selectedConversationId === conversationId) {
        const remaining = conversations.filter((c) => c.id !== conversationId);
        if (remaining.length > 0) {
          setSelectedConversationId(remaining[0].id);
        } else {
          setSelectedConversationId(null);
          setSelectedConversation(null);
          setMessages([]);
        }
      }
    } catch (err: any) {
      const errorMessage = parseError(err) || 'Không thể xóa cuộc trò chuyện. Vui lòng thử lại.';
      setError(errorMessage);
      throw err; // Re-throw to let ConversationSidebar handle it
    }
  };

  // Update conversation title
  const handleUpdateConversation = async (conversationId: number, title: string) => {
    try {
      setError('');
      const updated = await chatAPI.updateConversation(conversationId, { title });
      setConversations(
        conversations.map((c) => (c.id === conversationId ? updated : c))
      );
      
      // Update selected conversation if it's the one being updated
      if (selectedConversation && selectedConversation.id === conversationId) {
        setSelectedConversation({
          ...selectedConversation,
          title: updated.title,
        });
      }
    } catch (err: any) {
      const errorMessage = parseError(err) || 'Không thể cập nhật cuộc trò chuyện. Vui lòng thử lại.';
      setError(errorMessage);
      throw err; // Re-throw to let ConversationSidebar handle it
    }
  };

  // Send message
  const handleSendMessage = async (content: string) => {
    if (!selectedConversationId) {
      // Create new conversation if no conversation is selected
      try {
        setSending(true);
        setError('');
        const newConversation = await chatAPI.createConversation({});
        setConversations([newConversation, ...conversations]);
        setSelectedConversationId(newConversation.id);
        
        // Send message to new conversation
        await sendMessageToConversation(newConversation.id, content);
      } catch (err: any) {
        setSending(false);
        const errorMessage = parseError(err) || 'Không thể tạo cuộc trò chuyện mới. Vui lòng thử lại.';
        setError(errorMessage);
      }
    } else {
      sendMessageToConversation(selectedConversationId, content);
    }
  };

  // Send message to conversation
  const sendMessageToConversation = async (conversationId: number, content: string) => {
    // Add user message to UI immediately (optimistic update)
    const userMessage: Message = {
      id: Date.now(), // Temporary ID
      conversation_id: conversationId,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      setSending(true);
      setError('');

      // Send message to API
      const response = await chatAPI.sendMessage(conversationId, { content });

      // Replace temporary user message and add assistant response
      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== userMessage.id);
        return [...filtered, response.message, response.response];
      });

      // Update conversation in list (update updated_at)
      setConversations((prev) =>
        prev.map((c) =>
          c.id === conversationId
            ? { ...c, updated_at: response.response.created_at }
            : c
        )
      );

      // Reload conversation to get latest messages (in case of any sync issues)
      await loadConversation(conversationId);
    } catch (err: any) {
      // Remove optimistic user message on error
      setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
      
      const errorMessage = parseError(err) || 'Không thể gửi tin nhắn. Vui lòng thử lại.';
      setError(errorMessage);
    } finally {
      setSending(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <Header />
        
        {/* Error Alert */}
        {error && (
          <div className="px-4 py-2 bg-red-50 border-b border-red-200">
            <Alert
              type="error"
              message={error}
              onClose={() => setError('')}
            />
          </div>
        )}

        <div className="flex-1 flex overflow-hidden">
          {/* Sidebar */}
          <ConversationSidebar
            conversations={conversations}
            selectedConversationId={selectedConversationId}
            onSelectConversation={handleSelectConversation}
            onCreateConversation={handleCreateConversation}
            onDeleteConversation={handleDeleteConversation}
            onUpdateConversation={handleUpdateConversation}
            loading={conversationsLoading}
          />

          {/* Chat Area */}
          <div className="flex-1 flex flex-col bg-white">
            {loading && !selectedConversation ? (
              <div className="flex-1 flex items-center justify-center">
                <Loading size="lg" text="Đang tải cuộc trò chuyện..." />
              </div>
            ) : (
              <>
                {/* Message List */}
                <MessageList messages={messages} loading={sending} />

                {/* Chat Input */}
                <ChatInput
                  onSendMessage={handleSendMessage}
                  disabled={!selectedConversationId && conversations.length > 0}
                  loading={sending}
                />
              </>
            )}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
