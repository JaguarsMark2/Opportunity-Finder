/** Saved opportunities page. */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { userApi } from '../api/client';
import OpportunityCard from '../components/OpportunityCard';
import OpportunityDetailModal from '../components/OpportunityDetailModal';

export default function SavedPage() {
  const [selectedOpportunity, setSelectedOpportunity] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['saved-opportunities-full'],
    queryFn: async () => {
      const response = await userApi.getSaved({ limit: 50 });
      return response.data;
    },
  });

  const handleOpportunityClick = (opportunity: any) => {
    setSelectedOpportunity(opportunity);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedOpportunity(null);
  };

  const handleUpdate = () => {
    refetch();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
            Saved Opportunities
          </h1>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 animate-pulse">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16 mb-4"></div>
                <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-1"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
            Saved Opportunities
          </h1>
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <p className="text-red-600 dark:text-red-400">
              {error instanceof Error ? error.message : 'Failed to load saved opportunities'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const opportunities = data?.data?.items || [];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Saved Opportunities
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {opportunities.length} {opportunities.length === 1 ? 'opportunity' : 'opportunities'} saved
          </p>
        </div>

        {opportunities.length === 0 ? (
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-12 text-center">
            <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No saved opportunities yet
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Start exploring opportunities and save the ones that interest you.
            </p>
            <a
              href="/dashboard"
              className="inline-block px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Browse Opportunities
            </a>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {opportunities.map((opportunity: any) => (
              <OpportunityCard
                key={opportunity.id}
                opportunity={opportunity}
                onClick={() => handleOpportunityClick(opportunity)}
              />
            ))}
          </div>
        )}

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
