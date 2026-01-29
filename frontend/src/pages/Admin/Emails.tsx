/** Email management page for admins. */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../api/client';

interface EmailLog {
  id: string;
  to: string;
  subject: string;
  status: 'sent' | 'failed' | 'pending';
  sent_at?: string;
  error?: string;
}

export default function Emails() {
  const [testEmail, setTestEmail] = useState('');

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['admin-emails'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/api/v1/admin/emails');
        return response.data;
      } catch (error) {
        return { data: { items: [] } };
      }
    },
  });

  const handleSendTest = async () => {
    if (!testEmail) {
      alert('Please enter an email address');
      return;
    }
    try {
      await apiClient.post('/api/v1/admin/emails/test', { to: testEmail });
      alert('Test email sent!');
      setTestEmail('');
      refetch();
    } catch (error) {
      alert('Failed to send test email. Check SMTP configuration in .env');
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Emails
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Monitor email delivery and test SMTP configuration
        </p>
      </div>

      {/* Info Banner */}
      <div className="mb-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <p className="text-sm text-blue-800 dark:text-blue-300">
          <strong>SMTP Configuration:</strong> Configure email settings in <code className="bg-blue-100 dark:bg-blue-900 px-2 py-1 rounded">backend/.env</code>
          <br />
          Required: SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM
        </p>
      </div>

      {/* Test Email Section */}
      <div className="mb-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Send Test Email
        </h2>
        <div className="flex space-x-3">
          <input
            type="email"
            value={testEmail}
            onChange={(e) => setTestEmail(e.target.value)}
            placeholder="recipient@example.com"
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          />
          <button
            onClick={handleSendTest}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Send Test
          </button>
        </div>
      </div>

      {/* Email Logs */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Recent Email Logs
          </h2>
        </div>

        {isLoading ? (
          <div className="p-6 text-center text-gray-500 dark:text-gray-400">
            Loading email logs...
          </div>
        ) : !data?.data?.items || data.data.items.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-gray-500 dark:text-gray-400">
              No emails sent yet. Send a test email above.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {data.data.items.map((log: EmailLog) => (
              <div key={log.id} className="px-6 py-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <div className={`w-2 h-2 rounded-full ${
                        log.status === 'sent' ? 'bg-green-500' :
                        log.status === 'failed' ? 'bg-red-500' :
                        'bg-yellow-500'
                      }`} />
                      <p className="font-medium text-gray-900 dark:text-white">{log.to}</p>
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        log.status === 'sent' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                        log.status === 'failed' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                        'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                      }`}>
                        {log.status}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{log.subject}</p>
                    {log.sent_at && (
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-500">
                        {new Date(log.sent_at).toLocaleString()}
                      </p>
                    )}
                    {log.error && (
                      <p className="mt-1 text-sm text-red-600 dark:text-red-400">{log.error}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
