/** Scan management page for admins. */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../api/client';
import { useToast } from '../../components/Toast';

interface Scan {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  opportunities_found: number;
  sources_processed: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

/** Poll interval in ms when a scan is active. */
const POLL_INTERVAL = 3000;

export default function Scans() {
  const [runningSource, setRunningSource] = useState<string | null>(null);
  const [activeScanId, setActiveScanId] = useState<string | null>(null);
  const [activeScanStatus, setActiveScanStatus] = useState<Scan | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const { showToast } = useToast();

  const { data: scans, isLoading, refetch } = useQuery({
    queryKey: ['admin-scans'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/api/v1/scan/recent');
        return (response.data.scans ?? []) as Scan[];
      } catch {
        return [] as Scan[];
      }
    },
  });

  /** Poll for active scan progress. */
  const pollScan = useCallback(async (scanId: string) => {
    try {
      const response = await apiClient.get(`/api/v1/scan/${scanId}`);
      const status = response.data as Scan;
      setActiveScanStatus(status);

      if (status.status === 'completed') {
        showToast(
          `Scan complete — ${status.opportunities_found} opportunities found`,
          status.opportunities_found > 0 ? 'success' : 'info',
        );
        stopPolling();
        setActiveScanId(null);
        setRunningSource(null);
        refetch();
      } else if (status.status === 'failed') {
        showToast(
          status.error_message ?? 'Scan failed',
          'error',
        );
        stopPolling();
        setActiveScanId(null);
        setRunningSource(null);
        refetch();
      }
    } catch {
      // Scan record might not be written yet — keep polling
    }
  }, [showToast, refetch]);

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  /** Start polling when activeScanId changes. */
  useEffect(() => {
    if (!activeScanId) return;
    // Immediate first poll
    pollScan(activeScanId);
    pollRef.current = setInterval(() => pollScan(activeScanId), POLL_INTERVAL);
    return stopPolling;
  }, [activeScanId, pollScan]);

  const handleRunScan = async (sourceType: string) => {
    setRunningSource(sourceType);
    setActiveScanStatus(null);
    try {
      const response = await apiClient.post('/api/v1/scan', { sources: [sourceType] });
      const scanId = response.data.scan_id as string;
      setActiveScanId(scanId);
      showToast(`Scan started for ${sourceType.replace('_', ' ')}`, 'info');
    } catch {
      showToast('Failed to start scan. Make sure Celery worker is running.', 'error');
      setRunningSource(null);
    }
  };

  const sources = [
    { id: 'hacker_news', name: 'Hacker News', icon: '🍊' },
    { id: 'indie_hackers', name: 'Indie Hackers', icon: '🚀' },
    { id: 'bluesky', name: 'Bluesky', icon: '🦋' },
    { id: 'mastodon', name: 'Mastodon', icon: '🐘' },
    { id: 'reddit', name: 'Reddit', icon: '🔴' },
    { id: 'product_hunt', name: 'Product Hunt', icon: '🎯' },
    { id: 'google_trends', name: 'Google Trends', icon: '📈' },
  ];

  /** Format sources_processed into a readable label. */
  const formatSources = (scan: Scan): string => {
    if (scan.sources_processed && typeof scan.sources_processed === 'object') {
      const keys = Object.keys(scan.sources_processed);
      if (keys.length > 0) return keys.map((k) => k.replace('_', ' ')).join(', ');
    }
    return 'All sources';
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Scans
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Trigger scans and monitor progress
        </p>
      </div>

      {/* Active Scan Progress */}
      {runningSource && (
        <div className="mb-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <div className="w-4 h-4 rounded-full bg-blue-500 animate-pulse" />
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-800 dark:text-blue-300">
                Scanning {runningSource.replace('_', ' ')}...
                {activeScanStatus && (
                  <span className="ml-2 font-normal">
                    {activeScanStatus.progress}% complete
                  </span>
                )}
              </p>
              {activeScanStatus && activeScanStatus.opportunities_found > 0 && (
                <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                  {activeScanStatus.opportunities_found} opportunities found so far
                </p>
              )}
            </div>
          </div>
          {/* Progress bar */}
          {activeScanStatus && (
            <div className="mt-3 w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2">
              <div
                className="bg-blue-600 dark:bg-blue-400 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.max(activeScanStatus.progress, 5)}%` }}
              />
            </div>
          )}
        </div>
      )}

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
              disabled={runningSource !== null}
              className="flex items-center space-x-3 p-4 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <span className="text-2xl">{source.icon}</span>
              <div className="text-left">
                <p className="font-medium text-gray-900 dark:text-white">{source.name}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {runningSource === source.id ? 'Scanning...' : 'Click to scan'}
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Recent Scans */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Recent Scans
          </h2>
          <button
            onClick={() => refetch()}
            className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
          >
            Refresh
          </button>
        </div>

        {isLoading ? (
          <div className="p-6 text-center text-gray-500 dark:text-gray-400">
            Loading scans...
          </div>
        ) : !scans || scans.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-gray-500 dark:text-gray-400">
              No scans found. Run a scan above to get started.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {scans.map((scan: Scan) => (
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
                      {formatSources(scan)}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {scan.started_at ? new Date(scan.started_at).toLocaleString() : 'Pending'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {scan.opportunities_found} opportunities
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                      {scan.status}{scan.status === 'running' ? ` (${scan.progress}%)` : ''}
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
