/** API client with interceptors for token refresh. */

import axios, { AxiosError } from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5001';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // Don't retry if no original request or already retrying
    if (!originalRequest || originalRequest._retry) {
      return Promise.reject(error);
    }

    // If 401 and not a login request, try to refresh token
    if (error.response?.status === 401 && !originalRequest.url?.includes('/auth/')) {
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          // No refresh token, redirect to login
          window.location.href = '/login';
          return Promise.reject(error);
        }

        // Attempt to refresh token
        const response = await axios.post(
          `${API_BASE}/api/v1/auth/refresh`,
          {},
          {
            headers: { Authorization: `Bearer ${refreshToken}` },
          }
        );

        const { access_token } = response.data;

        // Store new token
        localStorage.setItem('access_token', access_token);

        // Update original request and retry
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        originalRequest._retry = true;
        return apiClient(originalRequest);

      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Opportunities API
export const opportunitiesApi = {
  list: (params: {
    min_score?: number;
    max_score?: number;
    is_validated?: boolean;
    sort?: string;
    search?: string;
    time_range?: string;
    limit?: number;
    cursor?: string;
  }) => apiClient.get('/api/v1/opportunities', { params }),

  get: (id: string) => apiClient.get(`/api/v1/opportunities/${id}`),

  update: (id: string, data: {
    status?: string;
    notes?: string;
    is_saved?: boolean;
  }) => apiClient.patch(`/api/v1/opportunities/${id}`, data),

  getStats: () => apiClient.get('/api/v1/opportunities/stats'),

  delete: (id: string) => apiClient.delete(`/api/v1/opportunities/${id}`),
};

// User API
export const userApi = {
  getProfile: () => apiClient.get('/api/v1/user/profile'),

  updateProfile: (data: any) => apiClient.patch('/api/v1/user/profile', data),

  getStats: () => apiClient.get('/api/v1/user/stats'),

  getSaved: (params?: { limit?: number; cursor?: string }) =>
    apiClient.get('/api/v1/user/saved', { params }),
};

// Scan API (admin only)
export const scanApi = {
  trigger: (sources?: string[]) =>
    apiClient.post('/api/v1/scan', sources ? { sources } : {}),

  getStatus: (scanId: string) =>
    apiClient.get(`/api/v1/scan/${scanId}`),

  getRecent: (limit?: number) =>
    apiClient.get('/api/v1/scan/recent', { params: { limit } }),

  getStats: () => apiClient.get('/api/v1/scan/stats'),
};

export default apiClient;
