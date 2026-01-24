/** Authentication service for API calls. */

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5001';

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: {
    id: string;
    email: string;
    role: string;
    subscription_status: string;
  };
}

export interface User {
  id: string;
  email: string;
  role: string;
  subscription_status: string;
  email_verified: boolean;
}

const authService = {
  async register(data: RegisterRequest): Promise<{ message: string; success?: boolean; user_id?: string }> {
    const response = await axios.post(`${API_BASE}/api/v1/auth/register`, data);
    return response.data;
  },

  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await axios.post(`${API_BASE}/api/v1/auth/login`, data);
    return response.data;
  },

  async verifyEmail(token: string): Promise<{ message: string }> {
    const response = await axios.get(`${API_BASE}/api/v1/auth/verify-email/${token}`);
    return response.data;
  },

  async forgotPassword(email: string): Promise<{ message: string }> {
    const response = await axios.post(`${API_BASE}/api/v1/auth/forgot-password`, { email });
    return response.data;
  },

  async resetPassword(token: string, newPassword: string): Promise<{ message: string }> {
    const response = await axios.post(`${API_BASE}/api/v1/auth/reset-password`, {
      token,
      new_password: newPassword
    });
    return response.data;
  },

  async refreshToken(refreshToken: string): Promise<{ access_token: string }> {
    const response = await axios.post(`${API_BASE}/api/v1/auth/refresh`, {}, {
      headers: { Authorization: `Bearer ${refreshToken}` }
    });
    return response.data;
  },

  async logout(refreshToken: string): Promise<{ message: string }> {
    const response = await axios.post(`${API_BASE}/api/v1/auth/logout`, {
      refresh_token: refreshToken
    }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    });
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await axios.get(`${API_BASE}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    });
    return response.data;
  }
};

export default authService;
