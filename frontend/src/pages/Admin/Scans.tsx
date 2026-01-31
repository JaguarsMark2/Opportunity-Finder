/** Scan management page for admins. */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../api/client';
import { useToast } from '../../components/Toast';

interface ScanRecord {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  opportunities_found: number;
  sources_processed: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

/** Live progress from Redis polling. */
interface ScanProgress {
  scan_id: string;
  progress: number;
  status: string;
  message: string;
  updated_at: string | null;
  /** DB fallback fields */
  opportunities_found?: number;
  error_message?: string | null;
}

/** Steps shown in the progress modal log. */
interface ProgressStep {
  message: string;
  progress: number;
  timestamp: Date;
}

/** Poll interval in ms when a scan is active. */
const POLL_INTERVAL = 2000;

export default function Scans() {
  const [runningSource, setRunningSource] = useState<string | null>(null);
  const [activeScanId, setActiveScanId] = useState<string | null>(null);
  const [liveProgress, setLiveProgress] = useState<ScanProgress | null>(null);
  const [progressLog, setProgressLog] = useState<ProgressStep[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [scanDone, setScanDone] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const logEndRef = useRef<HTMLDivElement | null>(null);
  const { showToast } = useToast();

  const { data: scans, isLoading, refetch } = useQuery({
    queryKey: ['admin-scans'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/api/v1/scan/recent');
        return (response.data.scans ?? []) as ScanRecord[];
      } catch {
        return [] as ScanRecord[];
      }
    },
  });

  /** Scroll log to bottom when new entries appear. */
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [progressLog]);

  /** Poll for active scan progress. */
  const pollScan = useCallback(async (scanId: string) => {
    try {
      const response = await apiClient.get(`/api/v1/scan/${scanId}`);
      const data = response.data as ScanProgress;
      setLiveProgress(data);

      // Add to log if message changed
      if (data.message) {
        setProgressLog((prev) => {
          const lastMsg = prev.length > 0 ? prev[prev.length - 1].message : '';
          if (data.message !== lastMsg) {
            return [...prev, { message: data.message, progress: data.progress, timestamp: new Date() }];
          }
          return prev;
        });
      }

      if (data.status === 'completed') {
        setScanDone(true);
        stopPolling();
        showToast(
          `Scan complete — ${data.opportunities_found ?? 0} opportunities found`,
          (data.opportunities_found ?? 0) > 0 ? 'success' : 'info',
        );
        refetch();
      } else if (data.status === 'failed') {
        setScanDone(true);
        stopPolling();
        setProgressLog((prev) => [
          ...prev,
          { message: data.error_message ?? data.message ?? 'Scan failed', progress: 0, timestamp: new Date() },
        ]);
        showToast(data.error_message ?? data.message ?? 'Scan failed', 'error');
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
    pollScan(activeScanId);
    pollRef.current = setInterval(() => pollScan(activeScanId), POLL_INTERVAL);
    return stopPolling;
  }, [activeScanId, pollScan]);

  const handleRunScan = async (sourceType: string) => {
    setRunningSource(sourceType);
    setLiveProgress(null);
    setProgressLog([{ message: 'Queuing scan task...', progress: 0, timestamp: new Date() }]);
    setScanDone(false);
    setShowModal(true);

    try {
      const response = await apiClient.post('/api/v1/scan', { sources: [sourceType] });
      const scanId = response.data.scan_id as string;
      setActiveScanId(scanId);
      setProgressLog((prev) => [...prev, { message: 'Scan task accepted by worker', progress: 2, timestamp: new Date() }]);
    } catch {
      showToast('Failed to start scan. Make sure Celery worker is running.', 'error');
      setProgressLog((prev) => [...prev, { message: 'Failed to start scan', progress: 0, timestamp: new Date() }]);
      setScanDone(true);
      setRunningSource(null);
    }
  };

  const handleStopScan = async () => {
    if (!activeScanId) return;
    try {
      await apiClient.post(`/api/v1/scan/${activeScanId}/cancel`);
      stopPolling();
      setScanDone(true);
      setLiveProgress((prev) => prev ? { ...prev, status: 'failed', message: 'Cancelled by user' } : prev);
      setProgressLog((prev) => [...prev, { message: 'Cancelled by user', progress: 0, timestamp: new Date() }]);
      showToast('Scan cancelled', 'warning');
      refetch();
    } catch {
      showToast('Failed to cancel scan', 'error');
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    if (scanDone) {
      setRunningSource(null);
      setActiveScanId(null);
      setLiveProgress(null);
      setProgressLog([]);
      setScanDone(false);
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

  const sourceName = (id: string): string => {
    const found = sources.find((s) => s.id === id);
    return found ? found.name : id.replace('_', ' ');
  };

  const sourceIcon = (id: string): string => {
    const found = sources.find((s) => s.id === id);
    return found ? found.icon : '🔍';
  };

  /** Format sources_processed into a readable label. */
  const formatSources = (scan: ScanRecord): string => {
    if (scan.sources_processed && typeof scan.sources_processed === 'object') {
      const keys = Object.keys(scan.sources_processed);
      if (keys.length > 0) return keys.map((k) => sourceName(k)).join(', ');
    }
    return 'All sources';
  };

  const handlePurgeAll = async () => {
    if (!confirm('Delete ALL opportunities, pending posts, and scan history? This cannot be undone.')) return;
    try {
      await apiClient.post('/api/v1/admin/purge-opportunities');
      showToast('All pipeline data purged', 'success');
      refetch();
    } catch {
      showToast('Failed to purge data', 'error');
    }
  };

  const progressPct = liveProgress?.progress ?? 0;
  const statusColor = liveProgress?.status === 'failed' ? 'red' : scanDone ? 'green' : 'blue';

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Scans</h1>
        <p className="text-gray-600 dark:text-gray-400">Trigger scans and monitor progress</p>
      </div>

      {/* Purge button */}
      <div className="mb-6 flex justify-end">
        <button
          onClick={handlePurgeAll}
          className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          Purge All Data
        </button>
      </div>

      {/* Run Scan Section */}
      <div className="mb-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Run New Scan</h2>
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
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Scans</h2>
          <button
            onClick={() => refetch()}
            className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
          >
            Refresh
          </button>
        </div>

        {isLoading ? (
          <div className="p-6 text-center text-gray-500 dark:text-gray-400">Loading scans...</div>
        ) : !scans || scans.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-gray-500 dark:text-gray-400">No scans found. Run a scan above to get started.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {scans.map((scan: ScanRecord) => (
              <div key={scan.id} className="px-6 py-4 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div
                    className={`w-3 h-3 rounded-full ${
                      scan.status === 'completed'
                        ? 'bg-green-500'
                        : scan.status === 'running'
                          ? 'bg-blue-500 animate-pulse'
                          : scan.status === 'failed'
                            ? 'bg-red-500'
                            : 'bg-yellow-500'
                    }`}
                  />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white capitalize">{formatSources(scan)}</p>
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
                      {scan.status}
                      {scan.status === 'running' ? ` (${scan.progress}%)` : ''}
                    </p>
                  </div>
                  {scan.error_message && (
                    <p className="text-sm text-red-600 dark:text-red-400 max-w-xs truncate">{scan.error_message}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Scan Progress Modal ── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={scanDone ? handleCloseModal : undefined} />

          {/* Modal */}
          <div className="relative w-full max-w-lg mx-4 bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            {/* Header */}
            <div className={`px-6 py-4 bg-${statusColor}-50 dark:bg-${statusColor}-900/20 border-b border-gray-200 dark:border-gray-700`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {runningSource && <span className="text-2xl">{sourceIcon(runningSource)}</span>}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {scanDone
                        ? liveProgress?.status === 'failed'
                          ? 'Scan Failed'
                          : 'Scan Complete'
                        : `Scanning ${runningSource ? sourceName(runningSource) : '...'}`}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {scanDone
                        ? `${liveProgress?.opportunities_found ?? 0} opportunities found`
                        : `${progressPct}% complete`}
                    </p>
                  </div>
                </div>
                {scanDone && (
                  <button
                    onClick={handleCloseModal}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xl leading-none"
                  >
                    &times;
                  </button>
                )}
              </div>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-gray-200 dark:bg-gray-700 h-2">
              <div
                className={`h-2 transition-all duration-700 ease-out ${
                  liveProgress?.status === 'failed'
                    ? 'bg-red-500'
                    : scanDone
                      ? 'bg-green-500'
                      : 'bg-blue-500'
                }`}
                style={{ width: `${Math.max(progressPct, scanDone ? 100 : 3)}%` }}
              />
            </div>

            {/* Live log */}
            <div className="px-6 py-4 max-h-64 overflow-y-auto font-mono text-sm">
              {progressLog.map((step, i) => {
                const isLatest = i === progressLog.length - 1 && !scanDone;
                return (
                  <div key={i} className="flex items-start gap-3 py-1.5">
                    <span className="flex-shrink-0 mt-0.5">
                      {scanDone && i === progressLog.length - 1 ? (
                        liveProgress?.status === 'failed' ? (
                          <span className="text-red-500">✗</span>
                        ) : (
                          <span className="text-green-500">✓</span>
                        )
                      ) : isLatest ? (
                        <span className="inline-block w-3 h-3 rounded-full bg-blue-500 animate-pulse" />
                      ) : (
                        <span className="text-green-500">✓</span>
                      )}
                    </span>
                    <span className={isLatest ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}>
                      {step.message}
                    </span>
                    <span className="ml-auto text-xs text-gray-400 dark:text-gray-500 flex-shrink-0">
                      {step.progress}%
                    </span>
                  </div>
                );
              })}
              <div ref={logEndRef} />
            </div>

            {/* Footer */}
            <div className="px-6 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/30 flex items-center justify-between">
              {scanDone ? (
                <>
                  <span />
                  <button
                    onClick={handleCloseModal}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
                  >
                    Close
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={handleStopScan}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium"
                  >
                    Stop Scan
                  </button>
                  <p className="text-xs text-gray-400 dark:text-gray-500 italic">
                    Polling every {POLL_INTERVAL / 1000}s...
                  </p>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
