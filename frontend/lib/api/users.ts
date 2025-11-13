import apiClient from '../api';
import { User, UserCreate, UserUpdate } from '../types';

export const usersAPI = {
  // List users
  listUsers: async (search?: string, skip: number = 0, limit: number = 100): Promise<User[]> => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    
    const response = await apiClient.get<User[]>(`/api/users?${params.toString()}`);
    return response.data;
  },

  // Get user by ID
  getUser: async (userId: number): Promise<User> => {
    const response = await apiClient.get<User>(`/api/users/${userId}`);
    return response.data;
  },

  // Create user
  createUser: async (data: UserCreate): Promise<User> => {
    const response = await apiClient.post<User>('/api/users', data);
    return response.data;
  },

  // Update user
  updateUser: async (userId: number, data: UserUpdate): Promise<User> => {
    const response = await apiClient.put<User>(`/api/users/${userId}`, data);
    return response.data;
  },

  // Delete user
  deleteUser: async (userId: number): Promise<void> => {
    await apiClient.delete(`/api/users/${userId}`);
  },
};

