/** Protected route component that requires authentication. */

import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../api/client';

interface ProtectedRouteProps {
  children: React.ReactElement;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const [isValidating, setIsValidating] = useState(true);
  const [isTokenValid, setIsTokenValid] = useState(false);

  useEffect(() => {
    // Only validate if we have a user (token in localStorage)
    if (!isAuthenticated || isLoading) {
      setIsValidating(false);
      return;
    }

    // Validate token with server
    const validateToken = async () => {
      try {
        await apiClient.get('/api/v1/user/profile');
        setIsTokenValid(true);
      } catch (error) {
        // Token is invalid, clear auth state
        setIsTokenValid(false);
      } finally {
        setIsValidating(false);
      }
    };

    validateToken();
  }, [isAuthenticated, isLoading]);

  if (isLoading || isValidating) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated || !isTokenValid) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
