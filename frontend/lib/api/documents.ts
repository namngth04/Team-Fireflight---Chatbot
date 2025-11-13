import apiClient from '../api';
import { Document, DocumentUpdate } from '../types';

export const documentsAPI = {
  // List documents
  listDocuments: async (
    documentType?: string,
    search?: string,
    skip: number = 0,
    limit: number = 100
  ): Promise<Document[]> => {
    const params = new URLSearchParams();
    if (documentType) params.append('document_type', documentType);
    if (search) params.append('search', search);
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    
    const response = await apiClient.get<Document[]>(`/api/documents?${params.toString()}`);
    return response.data;
  },

  // Get document by ID
  getDocument: async (documentId: number): Promise<Document> => {
    const response = await apiClient.get<Document>(`/api/documents/${documentId}`);
    return response.data;
  },

  // Upload document
  uploadDocument: async (file: File, documentType: string, description?: string): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    if (description) {
      formData.append('description', description);
    }
    
    // apiClient will automatically remove Content-Type header for FormData (via interceptor)
    const response = await apiClient.post<Document>('/api/documents/upload', formData);
    return response.data;
  },

  // Update document
  updateDocument: async (documentId: number, data: DocumentUpdate): Promise<Document> => {
    const response = await apiClient.put<Document>(`/api/documents/${documentId}`, data);
    return response.data;
  },

  // Delete document
  deleteDocument: async (documentId: number): Promise<void> => {
    await apiClient.delete(`/api/documents/${documentId}`);
  },
};

