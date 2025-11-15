export interface User {
  id: number;
  username: string;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  date_of_birth: string | null;
  role: 'admin' | 'employee';
  password?: string;  // Plain text password (only present when creating/updating)
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface UserCreate {
  username: string;
  password: string;
  full_name: string;
  phone: string;
  date_of_birth: string;
  email?: string;
  role?: 'admin' | 'employee';
}

export interface UserUpdate {
  full_name?: string;
  phone?: string;
  date_of_birth?: string;
  email?: string;
  password?: string;
}

export type DocumentType = 'policy' | 'ops';

export interface Document {
  id: number;
  filename: string;
  file_path: string;
  document_type: DocumentType;
  description: string | null;
  uploaded_by: number;
  uploaded_at: string;
  updated_at: string;
  file_metadata?: Record<string, any> | null;
}

export interface DocumentUpdate {
  description?: string;
  document_type?: DocumentType;
}

export interface DocumentUploadForm {
  file: File;
  document_type: DocumentType;
  description?: string;
}

export type MessageRole = 'user' | 'assistant';

export interface Message {
  id: number;
  conversation_id: number;
  role: MessageRole;
  content: string;
  created_at: string;
}

export interface Conversation {
  id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

export interface ConversationCreate {
  title?: string;
}

export interface ConversationUpdate {
  title?: string;
}

export interface MessageCreate {
  content: string;
}

export interface ChatMessageResponse {
  message: Message;
  response: Message;
}

