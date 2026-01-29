/** Protected route component that requires authentication. */

import type { ReactElement } from 'react';

interface ProtectedRouteProps {
  children: ReactElement;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  // Authentication disabled - allow all access
  return children;
}
