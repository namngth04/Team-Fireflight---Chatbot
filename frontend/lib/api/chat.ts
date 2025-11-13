import apiClient from '../api';
import {
  Conversation,
  ConversationWithMessages,
  ConversationCreate,
  ConversationUpdate,
  MessageCreate,
  ChatMessageResponse,
} from '../types';

export const chatAPI = {
  // List conversations
  listConversations: async (skip: number = 0, limit: number = 100): Promise<Conversation[]> => {
    const params = new URLSearchParams();
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    
    const response = await apiClient.get<Conversation[]>(`/api/chat/conversations?${params.toString()}`);
    return response.data;
  },

  // Get conversation with messages
  getConversation: async (conversationId: number): Promise<ConversationWithMessages> => {
    const response = await apiClient.get<ConversationWithMessages>(`/api/chat/conversations/${conversationId}`);
    return response.data;
  },

  // Create conversation
  createConversation: async (data: ConversationCreate): Promise<Conversation> => {
    const response = await apiClient.post<Conversation>('/api/chat/conversations', data);
    return response.data;
  },

  // Update conversation
  updateConversation: async (conversationId: number, data: ConversationUpdate): Promise<Conversation> => {
    const response = await apiClient.put<Conversation>(`/api/chat/conversations/${conversationId}`, data);
    return response.data;
  },

  // Delete conversation
  deleteConversation: async (conversationId: number): Promise<void> => {
    await apiClient.delete(`/api/chat/conversations/${conversationId}`);
  },

  // Send message
  sendMessage: async (
    conversationId: number,
    data: MessageCreate
  ): Promise<ChatMessageResponse> => {
    const response = await apiClient.post<ChatMessageResponse>(
      `/api/chat/conversations/${conversationId}/messages`,
      data
    );
    return response.data;
  },
};

