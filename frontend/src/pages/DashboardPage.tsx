/** Dashboard page with opportunity list and filters. */

import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { opportunitiesApi } from '../api/client';
import FilterBar from '../components/FilterBar';
import OpportunityList from '../components/OpportunityList';
import OpportunityDetailModal from '../components/OpportunityDetailModal';

export default function DashboardPage() {
  const [filters, setFilters] = useState({
    search: '',
    minScore: null as number | null,
    maxScore: null as number | null,
    isValidated: null as boolean | null,
    timeRange: 'all',
    sortBy: 'score_desc',
  });

  const [selectedOpportunity, setSelectedOpportunity] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data: stats } = useQuery({
    queryKey: ['opportunities-stats'],
    queryFn: async () => {
      const response = await opportunitiesApi.getStats();
      return response.data;
    },
  });

  const handleOpportunityClick = useCallback((opportunity: any) => {
    setSelectedOpportunity(opportunity);
    setIsModalOpen(true);
  }, []);

  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false);
    setSelectedOpportunity(null);
  }, []);

  const handleUpdate = useCallback(() => {
    // Trigger refetch of opportunities
    window.location.reload();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Page header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Opportunities
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Discover and track business opportunities from across the web
          </p>
        </div>

        {/* Stats cards */}
        {stats?.data && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Opportunities</div>
              <div className="text-3xl font-bold text-gray-900 dark:text-white">
                {stats.data.total_count}
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Validated</div>
              <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                {stats.data.validated_count}
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Avg Score</div>
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                {stats.data.avg_score ? stats.data.avg_score.toFixed(1) : '--'}
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">High Score (70+)</div>
              <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                {stats.data.high_score_count}
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <FilterBar onFiltersChange={setFilters} />

        {/* Opportunities list */}
        <OpportunityList
          filters={filters}
          onOpportunityClick={handleOpportunityClick}
        />

        {/* Detail modal */}
        {isModalOpen && selectedOpportunity && (
          <OpportunityDetailModal
            opportunity={selectedOpportunity}
            onClose={handleCloseModal}
            onUpdate={handleUpdate}
          />
        )}
      </div>
    </div>
  );
}
