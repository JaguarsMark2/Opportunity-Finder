/** Admin dashboard with analytics and metrics. */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../../api/admin';

export default function AdminDashboard() {
  const [timeRange, setTimeRange] = useState('30d');

  const { data: analytics, isLoading, isError } = useQuery({
    queryKey: ['admin-analytics', timeRange],
    queryFn: async () => {
      const response = await adminApi.getAnalytics({ time_range: timeRange });
      return response.data;
    },
  });

  const { data: health } = useQuery({
    queryKey: ['admin-health'],
    queryFn: async () => {
      const response = await adminApi.getSystemHealth();
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (isError || !analytics?.data) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-600 dark:text-red-400">
          Failed to load analytics data
        </p>
      </div>
    );
  }

  const data = analytics.data;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Admin Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            System overview and analytics
          </p>
        </div>

        {/* Time range selector */}
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
          <option value="90d">Last 90 Days</option>
          <option value="all">All Time</option>
        </select>
      </div>

      {/* System health */}
      {health?.data && (
        <div className="mb-6 grid grid-cols-2 gap-4">
          <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 border ${
            health.data.database === 'healthy'
              ? 'border-green-200 dark:border-green-800'
              : 'border-red-200 dark:border-red-800'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Database</p>
                <p className={`text-lg font-semibold ${
                  health.data.database === 'healthy'
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {health.data.database}
                </p>
              </div>
              <span className="text-2xl">
                {health.data.database === 'healthy' ? '✅' : '❌'}
              </span>
            </div>
          </div>

          <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 border ${
            health.data.redis === 'healthy'
              ? 'border-green-200 dark:border-green-800'
              : 'border-red-200 dark:border-red-800'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Redis</p>
                <p className={`text-lg font-semibold ${
                  health.data.redis === 'healthy'
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {health.data.redis}
                </p>
              </div>
              <span className="text-2xl">
                {health.data.redis === 'healthy' ? '✅' : '❌'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* User metrics */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Users</h2>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Users</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {data.users.total}
            </p>
            <p className="text-sm text-green-600 dark:text-green-400 mt-2">
              +{data.users.new} new
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">Active</p>
            <p className="text-3xl font-bold text-green-600 dark:text-green-400">
              {data.users.active}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">Trialing</p>
            <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
              {data.users.trialing}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">Admins</p>
            <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">
              {data.users.admins}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">Conversion Rate</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {data.users.total > 0
                ? Math.round((data.users.active / data.users.total) * 100)
                : 0}%
            </p>
          </div>
        </div>
      </div>

      {/* Revenue metrics */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Revenue</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">Monthly Recurring Revenue</p>
            <p className="text-3xl font-bold text-green-600 dark:text-green-400">
              ${data.revenue.mrr}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">Active Subscribers</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {data.revenue.active_subscribers}
            </p>
          </div>
        </div>
      </div>

      {/* Opportunity metrics */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Opportunities</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Opportunities</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {data.opportunities.total}
            </p>
            <p className="text-sm text-blue-600 dark:text-blue-400 mt-2">
              +{data.opportunities.new} new
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">Validated</p>
            <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">
              {data.opportunities.validated}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">High Score (70+)</p>
            <p className="text-3xl font-bold text-green-600 dark:text-green-400">
              {data.opportunities.high_score}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">Validation Rate</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {data.opportunities.total > 0
                ? Math.round((data.opportunities.validated / data.opportunities.total) * 100)
                : 0}%
            </p>
          </div>
        </div>
      </div>

      {/* System metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Scan metrics */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Scans</h2>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Scans</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {data.scans.total}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Success Rate</p>
                <p className={`text-2xl font-bold ${
                  data.scans.success_rate >= 90
                    ? 'text-green-600 dark:text-green-400'
                    : data.scans.success_rate >= 70
                    ? 'text-yellow-600 dark:text-yellow-400'
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {data.scans.success_rate}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Recent</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {data.scans.recent}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Successful</p>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {data.scans.successful}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Email metrics */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Emails</h2>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Sent</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {data.emails.total}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Success Rate</p>
                <p className={`text-2xl font-bold ${
                  data.emails.success_rate >= 90
                    ? 'text-green-600 dark:text-green-400'
                    : data.emails.success_rate >= 70
                    ? 'text-yellow-600 dark:text-yellow-400'
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {data.emails.success_rate}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Recent</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {data.emails.recent}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Successful</p>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {data.emails.successful}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Daily signups chart */}
      {data.users.daily_signups && data.users.daily_signups.length > 0 && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Daily Signups</h2>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <div className="h-64 flex items-end justify-between gap-2">
              {data.users.daily_signups.map((day: any) => {
                const maxCount = Math.max(...data.users.daily_signups.map((d: any) => d.count), 1);
                const height = (day.count / maxCount) * 100;
                return (
                  <div key={day.date} className="flex-1 flex flex-col items-center">
                    <div
                      className="w-full bg-blue-500 hover:bg-blue-600 transition-colors rounded-t"
                      style={{ height: `${height}%`, minHeight: day.count > 0 ? '4px' : '0' }}
                      title={`${day.date}: ${day.count} signups`}
                    ></div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
