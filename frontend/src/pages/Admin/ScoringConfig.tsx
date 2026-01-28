/** Scoring configuration page for admins. */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../../api/admin';

interface ScoringConfigData {
  data: {
    weights: {
      demand_weight: number;
      competition_weight: number;
      engagement_weight: number;
      validation_weight: number;
      recency_weight: number;
    };
    thresholds: {
      high_score_threshold: number;
      medium_score_threshold: number;
      validation_threshold: number;
      min_competitors: number;
      max_competitors: number;
    };
    enabled_criteria: Record<string, boolean>;
    last_updated?: string;
    updated_by?: string;
  };
}

export default function ScoringConfig() {
  const queryClient = useQueryClient();
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [localCriteria, setLocalCriteria] = useState<Record<string, boolean>>({});

  const { data: config, isLoading } = useQuery<ScoringConfigData>({
    queryKey: ['admin-scoring-config'],
    queryFn: async () => {
      const response = await adminApi.getScoringConfig();
      return response.data;
    },
  });

  // Set local criteria when config loads
  useEffect(() => {
    if (config?.data?.enabled_criteria) {
      setLocalCriteria(config.data.enabled_criteria);
    }
  }, [config]);

  const weightsMutation = useMutation({
    mutationFn: adminApi.updateScoringWeights,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-scoring-config'] });
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    },
    onError: () => {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 2000);
    },
  });

  const thresholdsMutation = useMutation({
    mutationFn: adminApi.updateScoringThresholds,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-scoring-config'] });
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    },
    onError: () => {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 2000);
    },
  });

  const criteriaMutation = useMutation({
    mutationFn: adminApi.updateScoringCriteria,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-scoring-config'] });
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    },
    onError: () => {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 2000);
    },
  });

  const handleWeightChange = (_key: string, _value: number) => {
    setSaveStatus('idle');
  };

  const handleSaveWeights = () => {
    if (!config?.data?.weights) return;

    const weights = {
      demand_weight: config.data.weights.demand_weight || 0,
      competition_weight: config.data.weights.competition_weight || 0,
      engagement_weight: config.data.weights.engagement_weight || 0,
      validation_weight: config.data.weights.validation_weight || 0,
      recency_weight: config.data.weights.recency_weight || 0,
    };

    setSaveStatus('saving');
    weightsMutation.mutate(weights);
  };

  const handleSaveThresholds = () => {
    if (!config?.data?.thresholds) return;

    const thresholds = {
      high_score_threshold: config.data.thresholds.high_score_threshold || 70,
      medium_score_threshold: config.data.thresholds.medium_score_threshold || 50,
      validation_threshold: config.data.thresholds.validation_threshold || 60,
      min_competitors: config.data.thresholds.min_competitors || 1,
      max_competitors: config.data.thresholds.max_competitors || 20,
    };

    setSaveStatus('saving');
    thresholdsMutation.mutate(thresholds);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const weights = config?.data?.weights || {
    demand_weight: 0,
    competition_weight: 0,
    engagement_weight: 0,
    validation_weight: 0,
    recency_weight: 0,
  };
  const thresholds = config?.data?.thresholds || {
    high_score_threshold: 70,
    medium_score_threshold: 50,
    validation_threshold: 60,
    min_competitors: 1,
    max_competitors: 20,
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Scoring Configuration
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Adjust weights and thresholds for opportunity scoring
          </p>
        </div>

        {saveStatus !== 'idle' && (
          <div className={`px-4 py-2 rounded-md ${
            saveStatus === 'saved'
              ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
              : saveStatus === 'error'
              ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
              : 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
          }`}>
            {saveStatus === 'saved' ? '✓ Saved'
              : saveStatus === 'error' ? '✗ Error saving'
              : 'Saving...'}
          </div>
        )}
      </div>

      {/* Enabled Criteria Section */}
      <div className="mb-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Enabled Scoring Criteria
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Toggle which criteria to include in opportunity scoring. Disabled criteria will not affect scores.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { key: 'upvotes', label: '🔼 Upvotes', desc: 'Community validation via upvotes' },
            { key: 'mentions', label: '📢 Mentions', desc: 'Frequency of mentions across sources' },
            { key: 'revenue_proof', label: '💰 Revenue Proof', desc: 'Competitor revenue/MRR data' },
            { key: 'competition', label: '⚔️ Competition', desc: 'Number of existing competitors' },
            { key: 'build_complexity', label: '🔧 Build Complexity', desc: 'Technical complexity assessment' },
            { key: 'b2b_focus', label: '🏢 B2B Focus', desc: 'Business-to-business market focus' },
            { key: 'engagement_signals', label: '💬 Engagement', desc: 'Comments, shares, interactions' },
          ].map((criterion) => (
            <label
              key={criterion.key}
              className="flex items-start space-x-3 p-3 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={localCriteria[criterion.key] ?? true}
                onChange={(e) => {
                  setLocalCriteria({ ...localCriteria, [criterion.key]: e.target.checked });
                  setSaveStatus('idle');
                }}
                className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <div>
                <span className="block text-sm font-medium text-gray-900 dark:text-white">
                  {criterion.label}
                </span>
                <span className="block text-xs text-gray-500 dark:text-gray-400">
                  {criterion.desc}
                </span>
              </div>
            </label>
          ))}
        </div>

        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={() => criteriaMutation.mutate(localCriteria)}
            disabled={criteriaMutation.isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {criteriaMutation.isPending ? 'Saving...' : 'Save Criteria'}
          </button>
        </div>

        {/* Upvote Info (shown when upvotes enabled) */}
        {localCriteria.upvotes !== false && (
          <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <h4 className="text-sm font-semibold text-green-800 dark:text-green-300 mb-2">
              Upvote Validation Details
            </h4>
            <p className="text-xs text-green-700 dark:text-green-400 mb-2">
              Upvotes indicate community validation - each upvote represents another person with the same pain point.
            </p>
            <div className="grid grid-cols-3 gap-2 text-xs text-green-700 dark:text-green-400">
              <div><strong>10+</strong> Initial validation</div>
              <div><strong>50+</strong> Strong validation</div>
              <div><strong>100+</strong> Validated market</div>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scoring Weights */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Scoring Weights
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
            Adjust how much each factor contributes to the overall score. Weights should sum to 1.0.
          </p>

          <div className="space-y-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Demand Weight
                </label>
                <span className="text-sm font-mono text-gray-900 dark:text-white">
                  {((weights.demand_weight || 0) * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.demand_weight || 0}
                onChange={(e) => handleWeightChange('demand_weight', parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Market demand and search volume
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Competition Weight
                </label>
                <span className="text-sm font-mono text-gray-900 dark:text-white">
                  {((weights.competition_weight || 0) * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.competition_weight || 0}
                onChange={(e) => handleWeightChange('competition_weight', parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Number of existing competitors
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Engagement Weight
                </label>
                <span className="text-sm font-mono text-gray-900 dark:text-white">
                  {((weights.engagement_weight || 0) * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.engagement_weight || 0}
                onChange={(e) => handleWeightChange('engagement_weight', parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                User engagement and social signals
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Validation Weight
                </label>
                <span className="text-sm font-mono text-gray-900 dark:text-white">
                  {((weights.validation_weight || 0) * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.validation_weight || 0}
                onChange={(e) => handleWeightChange('validation_weight', parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Validation from multiple sources
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Recency Weight
                </label>
                <span className="text-sm font-mono text-gray-900 dark:text-white">
                  {((weights.recency_weight || 0) * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.recency_weight || 0}
                onChange={(e) => handleWeightChange('recency_weight', parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Freshness of the opportunity
              </p>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Total Weight
              </span>
              <span className={`text-sm font-mono ${
                Math.abs((weights.demand_weight || 0) + (weights.competition_weight || 0) +
                       (weights.engagement_weight || 0) + (weights.validation_weight || 0) +
                       (weights.recency_weight || 0) - 1.0) < 0.01
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-red-600 dark:text-red-400'
              }`}>
                {((weights.demand_weight || 0) + (weights.competition_weight || 0) +
                  (weights.engagement_weight || 0) + (weights.validation_weight || 0) +
                  (weights.recency_weight || 0)).toFixed(2)}
                {Math.abs((weights.demand_weight || 0) + (weights.competition_weight || 0) +
                       (weights.engagement_weight || 0) + (weights.validation_weight || 0) +
                       (weights.recency_weight || 0) - 1.0) >= 0.01 && ' (should be 1.0)'}
              </span>
            </div>

            <button
              onClick={handleSaveWeights}
              disabled={weightsMutation.isPending}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {weightsMutation.isPending ? 'Saving...' : 'Save Weights'}
            </button>
          </div>
        </div>

        {/* Scoring Thresholds */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Scoring Thresholds
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
            Set score thresholds for categorizing opportunities.
          </p>

          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                High Score Threshold
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={thresholds.high_score_threshold || 70}
                onChange={(e) => {
                  thresholds.high_score_threshold = parseFloat(e.target.value);
                }}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Opportunities with score ≥ this value are marked as high quality
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Medium Score Threshold
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={thresholds.medium_score_threshold || 50}
                onChange={(e) => {
                  thresholds.medium_score_threshold = parseFloat(e.target.value);
                }}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Opportunities with score between medium and high are marked as medium quality
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Validation Threshold
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={thresholds.validation_threshold || 60}
                onChange={(e) => {
                  thresholds.validation_threshold = parseFloat(e.target.value);
                }}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Minimum score required to mark an opportunity as validated
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Minimum Competitors
                </label>
                <input
                  type="number"
                  min="0"
                  value={thresholds.min_competitors || 1}
                  onChange={(e) => {
                    thresholds.min_competitors = parseInt(e.target.value);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Minimum competitors to validate
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Maximum Competitors
                </label>
                <input
                  type="number"
                  min="0"
                  value={thresholds.max_competitors || 20}
                  onChange={(e) => {
                    thresholds.max_competitors = parseInt(e.target.value);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Maximum competitors for ideal opportunities
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={handleSaveThresholds}
              disabled={thresholdsMutation.isPending}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {thresholdsMutation.isPending ? 'Saving...' : 'Save Thresholds'}
            </button>
          </div>

          {/* Last updated info */}
          {config?.data?.last_updated && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Last updated: {new Date(config.data.last_updated).toLocaleString()}
                {config.data.updated_by && ` by ${config.data.updated_by}`}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
