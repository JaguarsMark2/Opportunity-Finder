/** Data sources configuration page for admins. */

import { useEffect, useState } from 'react';
import apiClient from '../../api/client';

interface DataSource {
  id: string;
  name: string;
  description: string;
  is_enabled: boolean;
  requires_auth: boolean;
  config_fields: string[];
  config: Record<string, string>;
  has_config: boolean;
  collector_available: boolean;
  docs_url: string;
}

interface TestResult {
  success: boolean;
  message: string;
  items_found: number;
  sample?: Array<{ title: string; url: string }> | string[];
}

export default function DataSources() {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editingSource, setEditingSource] = useState<string | null>(null);
  const [editConfig, setEditConfig] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  const [testingSource, setTestingSource] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, TestResult>>({});

  // Load data sources on mount
  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get('/api/v1/admin/data-sources');
      setSources(response.data.data || []);
    } catch (err) {
      setError('Failed to load data sources. Make sure backend is running.');
      console.error('Failed to load sources:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (sourceId: string, currentEnabled: boolean) => {
    try {
      const endpoint = currentEnabled
        ? `/api/v1/admin/data-sources/${sourceId}/disable`
        : `/api/v1/admin/data-sources/${sourceId}/enable`;

      await apiClient.post(endpoint);

      // Update local state
      setSources(sources.map(s =>
        s.id === sourceId ? { ...s, is_enabled: !currentEnabled } : s
      ));
    } catch (err) {
      console.error('Failed to toggle source:', err);
      alert('Failed to toggle source. Check console for details.');
    }
  };

  const handleEdit = (source: DataSource) => {
    setEditingSource(source.id);
    // Initialize with empty values for config fields
    const initialConfig: Record<string, string> = {};
    source.config_fields.forEach(field => {
      initialConfig[field] = '';
    });
    setEditConfig(initialConfig);
  };

  const handleSave = async (sourceId: string) => {
    try {
      setSaving(true);

      // Only send non-empty values
      const configToSave: Record<string, string> = {};
      Object.entries(editConfig).forEach(([key, value]) => {
        if (value && value.trim()) {
          configToSave[key] = value.trim();
        }
      });

      if (Object.keys(configToSave).length === 0) {
        alert('Please enter at least one configuration value.');
        return;
      }

      await apiClient.put(`/api/v1/admin/data-sources/${sourceId}/config`, configToSave);

      // Reload sources to get updated state
      await loadSources();

      setEditingSource(null);
      setEditConfig({});

      alert('Configuration saved successfully!');
    } catch (err) {
      console.error('Failed to save config:', err);
      alert('Failed to save configuration. Check console for details.');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async (sourceId: string) => {
    try {
      setTestingSource(sourceId);
      setTestResults(prev => ({ ...prev, [sourceId]: { success: false, message: 'Testing...', items_found: 0 } }));

      const response = await apiClient.post(`/api/v1/admin/data-sources/${sourceId}/test`);
      const result = response.data.data as TestResult;

      setTestResults(prev => ({ ...prev, [sourceId]: result }));
    } catch (err: any) {
      const errorMessage = err.response?.data?.error || 'Test failed. Check console for details.';
      setTestResults(prev => ({
        ...prev,
        [sourceId]: { success: false, message: errorMessage, items_found: 0 }
      }));
      console.error('Test failed:', err);
    } finally {
      setTestingSource(null);
    }
  };

  const getStatusColor = (source: DataSource) => {
    if (!source.collector_available) return 'bg-gray-300';
    if (source.is_enabled) return 'bg-green-500';
    return 'bg-yellow-500';
  };

  const getStatusText = (source: DataSource) => {
    if (!source.collector_available) return 'Not Available';
    if (source.is_enabled) return 'Enabled';
    return 'Disabled';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Data Sources
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Configure and test external data sources for opportunity collection
        </p>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
          <button
            onClick={loadSources}
            className="mt-2 text-sm text-red-600 dark:text-red-400 underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Info Banner */}
      <div className="mb-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <p className="text-sm text-blue-800 dark:text-blue-300">
          <strong>Tip:</strong> Use the <strong>Test</strong> button to verify connectivity before enabling a source.
          Sources without authentication (like Hacker News) can be tested immediately.
        </p>
      </div>

      {/* Data Sources List */}
      <div className="space-y-4">
        {sources.map((source) => (
          <div
            key={source.id}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6"
          >
            {/* Header Row */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${getStatusColor(source)}`} />
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {source.name}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {source.description}
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-2">
                {/* Enable/Disable Toggle */}
                <button
                  onClick={() => handleToggle(source.id, source.is_enabled)}
                  disabled={!source.collector_available}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    !source.collector_available
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed dark:bg-gray-700 dark:text-gray-500'
                      : source.is_enabled
                        ? 'bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-400'
                        : 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400'
                  }`}
                >
                  {getStatusText(source)}
                </button>

                {/* Configure Button */}
                {source.config_fields.length > 0 && (
                  <button
                    onClick={() => handleEdit(source)}
                    className="px-3 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 rounded text-sm font-medium hover:bg-blue-200 dark:hover:bg-blue-900/50"
                  >
                    Configure
                  </button>
                )}

                {/* Test Button */}
                <button
                  onClick={() => handleTest(source.id)}
                  disabled={testingSource === source.id || !source.collector_available}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    !source.collector_available
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed dark:bg-gray-700 dark:text-gray-500'
                      : testingSource === source.id
                        ? 'bg-purple-200 text-purple-800 dark:bg-purple-900/50 dark:text-purple-400'
                        : 'bg-purple-100 text-purple-800 hover:bg-purple-200 dark:bg-purple-900/30 dark:text-purple-400'
                  }`}
                >
                  {testingSource === source.id ? 'Testing...' : 'Test'}
                </button>

                {/* Docs Link */}
                {source.docs_url && (
                  <a
                    href={source.docs_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1 bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 rounded text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-600"
                  >
                    Docs
                  </a>
                )}
              </div>
            </div>

            {/* Test Result */}
            {testResults[source.id] && (
              <div
                className={`mt-3 p-3 rounded-lg text-sm ${
                  testResults[source.id].success
                    ? 'bg-green-50 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                    : 'bg-red-50 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <span className={`text-lg ${testResults[source.id].success ? '' : ''}`}>
                    {testResults[source.id].success ? '✓' : '✗'}
                  </span>
                  <span className="font-medium">{testResults[source.id].message}</span>
                </div>
                {testResults[source.id].sample && testResults[source.id].sample!.length > 0 && (
                  <div className="mt-2 text-xs opacity-75">
                    Sample: {Array.isArray(testResults[source.id].sample) &&
                      testResults[source.id].sample!.slice(0, 3).map((item, i) => (
                        <span key={i}>
                          {typeof item === 'string' ? item : item.title}
                          {i < 2 ? ', ' : ''}
                        </span>
                      ))
                    }
                  </div>
                )}
              </div>
            )}

            {/* Configuration Form */}
            {editingSource === source.id && (
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Configuration
                </h4>
                <div className="space-y-3">
                  {source.config_fields.map((field) => (
                    <div key={field}>
                      <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                        {field.replace(/_/g, ' ').toUpperCase()}
                        {source.requires_auth && <span className="text-red-500 ml-1">*</span>}
                      </label>
                      <input
                        type={field.includes('secret') || field.includes('password') || field.includes('token') || field.includes('key') ? 'password' : 'text'}
                        value={editConfig[field] || ''}
                        onChange={(e) => setEditConfig({ ...editConfig, [field]: e.target.value })}
                        placeholder={`Enter ${field.replace(/_/g, ' ')}`}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                  ))}
                </div>
                <div className="mt-4 flex justify-end space-x-2">
                  <button
                    onClick={() => {
                      setEditingSource(null);
                      setEditConfig({});
                    }}
                    disabled={saving}
                    className="px-4 py-2 text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleSave(source.id)}
                    disabled={saving}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {saving ? 'Saving...' : 'Save Configuration'}
                  </button>
                </div>
              </div>
            )}

            {/* Config Status */}
            {editingSource !== source.id && source.config_fields.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                <div className="flex items-center space-x-2 text-sm">
                  <span className={`w-2 h-2 rounded-full ${source.has_config ? 'bg-green-500' : 'bg-gray-300'}`} />
                  <span className={source.has_config ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}>
                    {source.has_config ? 'API keys configured' : 'No API keys configured'}
                  </span>
                  {source.requires_auth && !source.has_config && (
                    <span className="text-red-500 text-xs">(Required)</span>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Refresh Button */}
      <div className="mt-6 text-center">
        <button
          onClick={loadSources}
          className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
        >
          Refresh Sources
        </button>
      </div>
    </div>
  );
}
