/** Opportunity list component. */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { opportunitiesApi } from '../api/client';
import OpportunityCard from './OpportunityCard';
import { useToast } from './Toast';

interface OpportunityListProps {
  filters: {
    search: string;
    minScore: number | null;
    maxScore: number | null;
    isValidated: boolean | null;
    timeRange: string;
    sortBy: string;
  };
  onOpportunityClick: (opportunity: any) => void;
}

export default function OpportunityList({ filters, onOpportunityClick }: OpportunityListProps) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const handleDelete = async (id: string) => {
    try {
      await opportunitiesApi.delete(id);
      showToast('Opportunity deleted', 'success');
      queryClient.invalidateQueries({ queryKey: ['opportunities'] });
    } catch {
      showToast('Failed to delete opportunity', 'error');
    }
  };

  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['opportunities', filters],
    queryFn: async () => {
      const params: any = {};

      if (filters.search) params.search = filters.search;
      if (filters.minScore !== null) params.min_score = filters.minScore;
      if (filters.maxScore !== null) params.max_score = filters.maxScore;
      if (filters.isValidated !== null) params.is_validated = filters.isValidated;
      if (filters.timeRange !== 'all') params.time_range = filters.timeRange;
      if (filters.sortBy) params.sort = filters.sortBy;
      params.limit = 50;

      const response = await opportunitiesApi.list(params);
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 animate-pulse">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16 mb-4"></div>
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-1"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3 mb-4"></div>
            <div className="flex gap-4">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <div className="flex items-center">
          <svg className="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745.723 3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745.723 3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745.723 3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745.723 3.066 3.066 0 001.745-.723zm9.866 0a3.066 3.066 0 01-1.745-.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 011.745-.723 3.066 3.066 0 011.745.723 3.066 3.066 0 011.745-.723 3.066 3.066 0 011.745.723 3.066 3.066 0 011.745.723 3.066 3.066 0 011.745-.723zm1.745 1.745a3.066 3.066 0 01-1.745-.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 011.745-.723 3.066 3.066 0 011.745.723 3.066 3.066 0 011.745-.723zM6.267 6.066a3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745.723 3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745.723 3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745.723 3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745.723 3.066 3.066 0 001.745-.723zm9.866 0a3.066 3.066 0 01-1.745-.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 011.745-.723 3.066 3.066 0 011.745.723 3.066 3.066 0 011.745-.723zm1.745 1.745a3.066 3.066 0 01-1.745-.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 011.745-.723 3.066 3.066 0 011.745.723 3.066 3.066 0 011.745-.723z" clipRule="evenodd" />
          </svg>
          <div>
            <h3 className="text-red-800 dark:text-red-400 font-medium">Error loading opportunities</h3>
            <p className="text-red-600 dark:text-red-500 text-sm mt-1">
              {error instanceof Error ? error.message : 'Something went wrong'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const opportunities = data?.data?.items || [];

  if (opportunities.length === 0) {
    return (
      <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-12 text-center">
        <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          No opportunities found
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          Try adjusting your filters or check back later for new opportunities.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {opportunities.map((opportunity: any) => (
          <OpportunityCard
            key={opportunity.id}
            opportunity={opportunity}
            onClick={() => onOpportunityClick(opportunity)}
            onDelete={handleDelete}
          />
        ))}
      </div>
    </div>
  );
}
