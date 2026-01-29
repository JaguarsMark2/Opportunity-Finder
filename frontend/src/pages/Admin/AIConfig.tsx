/** AI Configuration page for admins. */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../api/client';

interface AIConfigData {
  provider: string;
  model: string;
  api_url: string;
  enabled: boolean;
  api_key_set: boolean;
  api_key_masked: string;
}

interface FilterRules {
  exclude_keywords: string[];
  require_keywords: string[];
  min_upvotes: number;
  min_comments: number;
  exclude_categories: string[];
  custom_rules: Array<{
    type: string;
    value: string;
    reason: string;
    added_at: string;
  }>;
}

export default function AIConfig() {
  const queryClient = useQueryClient();
  const [newApiKey, setNewApiKey] = useState('');
  const [newExcludeKeyword, setNewExcludeKeyword] = useState('');
  const [excludeReason, setExcludeReason] = useState('');
  const [configError, setConfigError] = useState<string | null>(null);
  const [modelInput, setModelInput] = useState('');

  // Fetch AI config
  const { data: aiConfig, isLoading: aiLoading } = useQuery({
    queryKey: ['ai-config'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/ai/config');
      return response.data.data as AIConfigData;
    },
  });

  // Sync model input when config loads
  useEffect(() => {
    if (aiConfig?.model) {
      setModelInput(aiConfig.model);
    }
  }, [aiConfig?.model]);

  // Fetch filter rules
  const { data: filterRules, isLoading: rulesLoading } = useQuery({
    queryKey: ['filter-rules'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/filter-rules');
      return response.data.data as FilterRules;
    },
  });

  // Update AI config mutation
  const updateAIConfig = useMutation({
    mutationFn: async (config: Partial<AIConfigData & { api_key?: string }>) => {
      const response = await apiClient.put('/api/v1/admin/ai/config', config);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-config'] });
      setNewApiKey('');
      setConfigError(null);
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.error || error?.message || 'Failed to update config';
      setConfigError(msg);
    },
  });

  // Test AI connection mutation
  const [testError, setTestError] = useState<string | null>(null);
  const testAI = useMutation({
    mutationFn: async () => {
      setTestError(null);
      const response = await apiClient.post('/api/v1/admin/ai/test');
      return response.data.data;
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.error || error?.message || 'Test request failed';
      setTestError(msg);
    },
  });

  // Add exclusion keyword mutation
  const addExclusion = useMutation({
    mutationFn: async ({ keyword, reason }: { keyword: string; reason: string }) => {
      const response = await apiClient.post('/api/v1/admin/filter-rules/add-exclusion', {
        keyword,
        reason,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rules'] });
      setNewExcludeKeyword('');
      setExcludeReason('');
    },
  });

  // Update filter rules mutation
  const updateFilterRules = useMutation({
    mutationFn: async (rules: FilterRules) => {
      const response = await apiClient.put('/api/v1/admin/filter-rules', rules);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rules'] });
    },
  });

  const handleSaveApiKey = () => {
    if (newApiKey.trim()) {
      updateAIConfig.mutate({ api_key: newApiKey.trim() });
    }
  };

  const handleToggleEnabled = () => {
    if (aiConfig) {
      updateAIConfig.mutate({ enabled: !aiConfig.enabled });
    }
  };

  const handleProviderChange = (provider: string) => {
    const models: Record<string, string> = {
      glm: 'glm-4',
      openai: 'gpt-4o-mini',
      anthropic: 'claude-3-haiku-20240307',
    };
    updateAIConfig.mutate({ provider, model: models[provider] || '' });
  };

  const handleAddExclusion = () => {
    if (newExcludeKeyword.trim()) {
      addExclusion.mutate({ keyword: newExcludeKeyword.trim(), reason: excludeReason });
    }
  };

  const handleRemoveExclusion = (keyword: string) => {
    if (filterRules) {
      const updated = {
        ...filterRules,
        exclude_keywords: filterRules.exclude_keywords.filter((k) => k !== keyword),
      };
      updateFilterRules.mutate(updated);
    }
  };

  const handleUpdateMinUpvotes = (value: number) => {
    if (filterRules) {
      updateFilterRules.mutate({ ...filterRules, min_upvotes: value });
    }
  };

  const handleUpdateMinComments = (value: number) => {
    if (filterRules) {
      updateFilterRules.mutate({ ...filterRules, min_comments: value });
    }
  };

  if (aiLoading || rulesLoading) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        Loading configuration...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          AI & Filtering Configuration
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Configure AI analysis and filtering rules for opportunity detection
        </p>
      </div>

      {/* AI Configuration Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          AI Provider Configuration
        </h2>

        {/* Provider Selection */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            AI Provider
          </label>
          <div className="flex gap-3">
            {['glm', 'openai', 'anthropic'].map((provider) => (
              <button
                key={provider}
                onClick={() => handleProviderChange(provider)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  aiConfig?.provider === provider
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {provider === 'glm' ? 'GLM (Zhipu)' : provider === 'openai' ? 'OpenAI' : 'Anthropic'}
              </button>
            ))}
          </div>
          {updateAIConfig.isPending && (
            <p className="mt-2 text-sm text-blue-600 dark:text-blue-400">Saving...</p>
          )}
          {configError && (
            <p className="mt-2 text-sm text-red-600 dark:text-red-400">
              Error: {configError}
            </p>
          )}
        </div>

        {/* API Key */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            API Key
          </label>
          <div className="flex gap-3">
            <input
              type="password"
              value={newApiKey}
              onChange={(e) => setNewApiKey(e.target.value)}
              placeholder={aiConfig?.api_key_set ? aiConfig.api_key_masked : 'Enter API key...'}
              className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              onClick={handleSaveApiKey}
              disabled={!newApiKey.trim() || updateAIConfig.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {updateAIConfig.isPending ? 'Saving...' : 'Save Key'}
            </button>
          </div>
          {aiConfig?.api_key_set && (
            <p className="mt-1 text-sm text-green-600 dark:text-green-400">
              API key is configured
            </p>
          )}
        </div>

        {/* Model */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Model
          </label>
          <div className="flex gap-3">
            <input
              type="text"
              list="model-suggestions"
              value={modelInput}
              onChange={(e) => setModelInput(e.target.value)}
              placeholder="e.g. glm-4, glm-4v, gpt-4o-mini"
              className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              onClick={() => { if (modelInput.trim()) updateAIConfig.mutate({ model: modelInput.trim() }); }}
              disabled={!modelInput.trim() || modelInput === aiConfig?.model || updateAIConfig.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Save Model
            </button>
            <datalist id="model-suggestions">
              {aiConfig?.provider === 'glm' && (
                <>
                  <option value="glm-4" />
                  <option value="glm-4-plus" />
                  <option value="glm-4-flash" />
                  <option value="glm-4-long" />
                  <option value="glm-4-0520" />
                </>
              )}
              {aiConfig?.provider === 'openai' && (
                <>
                  <option value="gpt-4o-mini" />
                  <option value="gpt-4o" />
                  <option value="gpt-4-turbo" />
                </>
              )}
              {aiConfig?.provider === 'anthropic' && (
                <>
                  <option value="claude-3-haiku-20240307" />
                  <option value="claude-3-5-sonnet-20241022" />
                  <option value="claude-3-5-haiku-20241022" />
                </>
              )}
            </datalist>
          </div>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Type any model name your API key supports. Suggestions provided as hints.
          </p>
        </div>

        {/* Enable/Disable & Test */}
        <div className="flex items-center gap-4 flex-wrap">
          <button
            onClick={handleToggleEnabled}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              aiConfig?.enabled
                ? 'bg-green-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            }`}
          >
            {aiConfig?.enabled ? 'AI Enabled' : 'AI Disabled'}
          </button>

          <button
            onClick={() => testAI.mutate()}
            disabled={!aiConfig?.api_key_set || testAI.isPending}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {testAI.isPending ? 'Testing...' : 'Test Connection'}
          </button>
        </div>

        {/* Test Result Display */}
        {testAI.data && (
          <div className={`mt-4 p-4 rounded-lg border ${
            testAI.data.success
              ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
              : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
          }`}>
            <p className={`text-sm font-medium ${
              testAI.data.success
                ? 'text-green-800 dark:text-green-300'
                : 'text-red-800 dark:text-red-300'
            }`}>
              {testAI.data.success ? 'Connection Successful' : 'Connection Failed'}
            </p>
            <p className={`mt-1 text-sm ${
              testAI.data.success
                ? 'text-green-700 dark:text-green-400'
                : 'text-red-700 dark:text-red-400'
            }`}>
              {testAI.data.message}
            </p>
          </div>
        )}

        {/* Test Error Display (network/server errors) */}
        {!testAI.data && testError && (
          <div className="mt-4 p-4 rounded-lg border bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
            <p className="text-sm font-medium text-red-800 dark:text-red-300">
              Request Failed
            </p>
            <p className="mt-1 text-sm text-red-700 dark:text-red-400">
              {testError}
            </p>
          </div>
        )}
      </div>

      {/* Filtering Rules Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Filtering Rules
        </h2>

        {/* Minimum Thresholds */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Minimum Upvotes: {filterRules?.min_upvotes || 5}
            </label>
            <input
              type="range"
              min="0"
              max="50"
              value={filterRules?.min_upvotes || 5}
              onChange={(e) => handleUpdateMinUpvotes(Number(e.target.value))}
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Minimum Comments: {filterRules?.min_comments || 2}
            </label>
            <input
              type="range"
              min="0"
              max="20"
              value={filterRules?.min_comments || 2}
              onChange={(e) => handleUpdateMinComments(Number(e.target.value))}
              className="w-full"
            />
          </div>
        </div>

        {/* Add Exclusion */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Add Exclusion Keyword
          </label>
          <div className="flex gap-3 mb-2">
            <input
              type="text"
              value={newExcludeKeyword}
              onChange={(e) => setNewExcludeKeyword(e.target.value)}
              placeholder="Keyword to exclude..."
              className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
            <input
              type="text"
              value={excludeReason}
              onChange={(e) => setExcludeReason(e.target.value)}
              placeholder="Reason (optional)..."
              className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
            <button
              onClick={handleAddExclusion}
              disabled={!newExcludeKeyword.trim() || addExclusion.isPending}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Add Exclusion
            </button>
          </div>
        </div>

        {/* Current Exclusions */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Excluded Keywords ({filterRules?.exclude_keywords?.length || 0})
          </label>
          <div className="flex flex-wrap gap-2">
            {filterRules?.exclude_keywords?.map((keyword) => (
              <span
                key={keyword}
                className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300"
              >
                {keyword}
                <button
                  onClick={() => handleRemoveExclusion(keyword)}
                  className="ml-1 hover:text-red-600"
                >
                  x
                </button>
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h3 className="font-semibold text-blue-800 dark:text-blue-300 mb-2">How it works</h3>
        <ul className="text-sm text-blue-700 dark:text-blue-400 space-y-1">
          <li>1. Posts are collected from data sources (Hacker News, etc.)</li>
          <li>2. Filter rules exclude junk (job posts, promos, low engagement)</li>
          <li>3. AI analyzes remaining posts to extract the core pain point</li>
          <li>4. Similar pain points are clustered into single opportunities</li>
          <li>5. Opportunities are scored based on validation signals</li>
        </ul>
      </div>
    </div>
  );
}
