/** Authentication context for managing user auth state. */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiClient from '../api/client';
import authService from '../services/authService';

// DEV MODE: Auto-login as admin for development
const DEV_MODE = true;

interface User {
  id: string;
  email: string;
  role: string;
  subscription_status: string;
  subscription_tier_id?: string | null;
  email_verified?: boolean;
  created_at?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing session on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user');

    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        // Invalid user data, clear everything
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
      }
    } else if (DEV_MODE) {
      // Dev mode: Auto-set admin user
      const devUser: User = {
        id: '1de75072-3eb7-4bdd-a0a0-ff2016b9960b',
        email: 'admin@local.dev',
        role: 'admin',
        subscription_status: 'active',
        email_verified: true,
      };
      setUser(devUser);
      localStorage.setItem('user', JSON.stringify(devUser));
    }

    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const response = await authService.login({ email, password });

    // Store tokens and user data
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('refresh_token', response.refresh_token);
    localStorage.setItem('user', JSON.stringify(response.user));

    setUser(response.user);
  };

  const register = async (email: string, password: string) => {
    await authService.register({ email, password });
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      try {
        await authService.logout(refreshToken);
      } catch (e) {
        // Ignore logout errors
        console.error('Logout error:', e);
      }
    }

    // Clear local storage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');

    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const response = await apiClient.get('/api/v1/user/profile');
      setUser(response.data);
      localStorage.setItem('user', JSON.stringify(response.data));
    } catch (e) {
      // Token might be expired, clear everything
      await logout();
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
