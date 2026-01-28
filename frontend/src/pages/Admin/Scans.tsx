/** Scan management page for admins. */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../api/client';

interface Scan {
  id: string;
  source_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  opportunities_found: number;
  started_at: string;
  completed_at?: string;
  error_message?: string;
}

export default function Scans() {
  const [isRunning, setIsRunning] = useState(false);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['admin-scans'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/api/v1/admin/scans');
        return response.data;
      } catch (error) {
        // Endpoint might not exist yet
        return { data: { items: [] } };
      }
    },
  });

  const handleRunScan = async (sourceType: string) => {
    setIsRunning(true);
    try {
      await apiClient.post('/api/v1/scan', { sources: [sourceType] });
      alert(`Scan started for ${sourceType}`);
      refetch();
    } catch (error) {
      alert('Failed to start scan. Make sure Celery worker is running.');
    } finally {
      setIsRunning(false);
    }
  };

  const sources = [
    { id: 'bluesky', name: 'Bluesky', icon: '🦋' },
    { id: 'mastodon', name: 'Mastodon', icon: '🐘' },
    { id: 'reddit', name: 'Reddit', icon: '🔴' },
    { id: 'indie_hackers', name: 'Indie Hackers', icon: '🚀' },
    { id: 'product_hunt', name: 'Product Hunt', icon: '🎯' },
    { id: 'hacker_news', name: 'Hacker News', icon: '🍊' },
    { id: 'google_trends', name: 'Google Trends', icon: '📈' },
  ];

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Scans
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Manage data source scans and opportunity discovery
        </p>
      </div>

      {/* Info Banner */}
      <div className="mb-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
        <p className="text-sm text-yellow-800 dark:text-yellow-300">
          <strong>Requirement:</strong> Celery worker must be running to execute scans.
          Run: <code className="bg-yellow-100 dark:bg-yellow-900 px-2 py-1 rounded">celery -A app.celery_app worker --loglevel=info</code>
        </p>
      </div>

      {/* Run Scan Section */}
      <div className="mb-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Run New Scan
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {sources.map((source) => (
            <button
              key={source.id}
              onClick={() => handleRunScan(source.id)}
              disabled={isRunning}
              className="flex items-center space-x-3 p-4 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <span className="text-2xl">{source.icon}</span>
              <div className="text-left">
                <p className="font-medium text-gray-900 dark:text-white">{source.name}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {isRunning ? 'Starting...' : 'Click to scan'}
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Recent Scans */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Recent Scans
          </h2>
        </div>

        {isLoading ? (
          <div className="p-6 text-center text-gray-500 dark:text-gray-400">
            Loading scans...
          </div>
        ) : !data?.data?.items || data.data.items.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-gray-500 dark:text-gray-400">
              No scans found. Run a scan above to get started.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {data.data.items.map((scan: Scan) => (
              <div key={scan.id} className="px-6 py-4 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className={`w-3 h-3 rounded-full ${
                    scan.status === 'completed' ? 'bg-green-500' :
                    scan.status === 'running' ? 'bg-blue-500 animate-pulse' :
                    scan.status === 'failed' ? 'bg-red-500' :
                    'bg-yellow-500'
                  }`} />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white capitalize">
                      {scan.source_type.replace('_', ' ')}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {new Date(scan.started_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {scan.opportunities_found} opportunities
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                      {scan.status}
                    </p>
                  </div>
                  {scan.error_message && (
                    <p className="text-sm text-red-600 dark:text-red-400 max-w-xs truncate">
                      {scan.error_message}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
