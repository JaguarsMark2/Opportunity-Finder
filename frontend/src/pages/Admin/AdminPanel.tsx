/** Main admin panel page with navigation. */

import { useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';

export default function AdminPanel() {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const menuItems = [
    { path: '/admin', label: 'Dashboard', icon: '📊' },
    { path: '/admin/users', label: 'Users', icon: '👥' },
    { path: '/admin/pricing', label: 'Pricing', icon: '💰' },
    { path: '/admin/scoring', label: 'Scoring', icon: '🎯' },
    { path: '/admin/scans', label: 'Scans', icon: '🔍' },
    { path: '/admin/emails', label: 'Emails', icon: '📧' },
    { path: '/admin/data-sources', label: 'Data Sources', icon: '🔌' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="flex">
        {/* Sidebar */}
        {sidebarOpen && (
          <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 min-h-screen">
            <div className="p-6">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white mb-1">
                Admin Panel
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Opportunity Finder
              </p>
            </div>

            <nav className="mt-6">
              {menuItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center space-x-3 px-6 py-3 transition-colors ${
                      isActive
                        ? 'bg-blue-50 dark:bg-blue-900/20 border-r-4 border-blue-600 text-blue-600 dark:text-blue-400'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    <span className="text-lg">{item.icon}</span>
                    <span className="font-medium">{item.label}</span>
                  </Link>
                );
              })}
            </nav>

            <div className="absolute bottom-0 left-0 w-64 p-6 border-t border-gray-200 dark:border-gray-700">
              <Link
                to="/dashboard"
                className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
              >
                <span>←</span>
                <span>Back to App</span>
              </Link>
            </div>
          </div>
        )}

        {/* Main content */}
        <div className="flex-1">
          {/* Top bar */}
          <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
            >
              {sidebarOpen ? '◀' : '▶'}
            </button>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Admin Mode
              </span>
            </div>
          </div>

          {/* Page content */}
          <div className="p-6">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}
