/** Header component with navigation and theme toggle. */

import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface HeaderProps {
  darkMode: boolean;
  setDarkMode: (value: boolean) => void;
}

export default function Header({ darkMode, setDarkMode }: HeaderProps) {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">OF</span>
            </div>
            <span className="text-xl font-bold text-gray-900 dark:text-white">Opportunity Finder</span>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            <Link to="/dashboard" className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium">
              Dashboard
            </Link>
            {isAuthenticated ? (
              <>
                {user?.role === 'admin' && (
                  <Link to="/admin" className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 font-medium">
                    Admin
                  </Link>
                )}
                <Link to="/saved" className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">
                  Saved
                </Link>
                <Link to="/billing" className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">
                  Billing
                </Link>
                <Link to="/profile" className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">
                  Profile
                </Link>
              </>
            ) : (
              <>
                <Link to="/login" className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">
                  Sign In
                </Link>
                <Link to="/register" className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                  Get Started
                </Link>
              </>
            )}
          </nav>

          {/* Right side actions */}
          <div className="flex items-center space-x-4">
            {/* Dark mode toggle */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              aria-label="Toggle dark mode"
            >
              {darkMode ? (
                <svg className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 001 1v3a1 1 0 001 1h1a1 1 0 001 1v1a1 1 0 001 1h3a1 1 0 001-1V6a1 1 0 00-1-1v-1a1 1 0 011-1V2a1 1 0 00-1-1h-1a1 1 0 01-1 1v1a1 1 0 001 1v1a1 1 0 001 1h3a1 1 0 001-1V5a1 1 0 00-1-1zM6 12a2 2 0 110-4 2 2 0 010 4z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                </svg>
              )}
            </button>

            {/* User menu */}
            {isAuthenticated && (
              <div className="flex items-center space-x-3">
                <span className="text-sm text-gray-600 dark:text-gray-300 hidden sm:block">
                  {user?.email}
                </span>
                <button
                  onClick={logout}
                  className="text-sm text-gray-600 dark:text-gray-300 hover:text-red-600"
                >
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
