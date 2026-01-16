/** Opportunity card component for displaying opportunities. */

interface OpportunityCardProps {
  opportunity: {
    id: string;
    title: string;
    description: string;
    score: number | null;
    is_validated: boolean;
    competitor_count: number;
    mention_count: number;
    source_types: string[];
    created_at: string;
    user_status?: string;
    is_saved?: boolean;
  };
  onClick: () => void;
}

export default function OpportunityCard({ opportunity, onClick }: OpportunityCardProps) {
  const { title, description, score, is_validated, competitor_count, mention_count, source_types, created_at, is_saved } = opportunity;

  const getScoreColor = (score: number | null) => {
    if (score === null) return 'bg-gray-200 text-gray-500';
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-blue-100 text-blue-800';
    if (score >= 40) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <div
      onClick={onClick}
      className="bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer p-6 border border-gray-200 dark:border-gray-700"
    >
      {/* Header: Score and saved status */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          {score !== null ? (
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(score)}`}>
              {score}
            </div>
          ) : (
            <div className="px-3 py-1 rounded-full text-sm font-medium bg-gray-200 text-gray-500">
              --
            </div>
          )}
          {is_validated && (
            <div className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full flex items-center">
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745.723 3.066 3.066 0 001.745-.723 3.066 3.066 0 00-1.745.723 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 00-1.745.723 3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745.723 3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745.723 3.066 3.066 0 01-1.745-.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 011.745-.723 3.066 3.066 0 011.745.723 3.066 3.066 0 001.745-.723zm9.866 0a3.066 3.066 0 01-1.745-.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 011.745-.723 3.066 3.066 0 011.745.723 3.066 3.066 0 011.745-.723 3.066 3.066 0 011.745.723 3.066 3.066 0 011.745-.723zm1.745 1.745a3.066 3.066 0 01-1.745-.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 011.745-.723 3.066 3.066 0 011.745.723 3.066 3.066 0 011.745-.723zM6.267 6.066a3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745.723 3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745.723 3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745.723 3.066 3.066 0 001.745-.723 3.066 3.066 0 001.745.723 3.066 3.066 0 011.745-.723 3.066 3.066 0 011.745-.723zm9.866 0a3.066 3.066 0 01-1.745-.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 011.745-.723 3.066 3.066 0 011.745.723 3.066 3.066 0 011.745-.723zm1.745 1.745a3.066 3.066 0 01-1.745-.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 01-1.745.723 3.066 3.066 0 011.745-.723 3.066 3.066 0 011.745.723 3.066 3.066 0 011.745-.723z" clipRule="evenodd" />
              </svg>
              Validated
            </div>
          )}
        </div>

        {is_saved && (
          <svg className="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-1.838-.197-1.539.281l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292z" />
          </svg>
        )}
      </div>

      {/* Title */}
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
        {title}
      </h3>

      {/* Description */}
      <p className="text-gray-600 dark:text-gray-300 text-sm mb-4 line-clamp-3">
        {description}
      </p>

      {/* Stats */}
      <div className="flex flex-wrap gap-4 mb-4 text-sm">
        <div className="flex items-center text-gray-500 dark:text-gray-400">
          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v7h8v-7z" />
          </svg>
          {competitor_count} competitors
        </div>
        <div className="flex items-center text-gray-500 dark:text-gray-400">
          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 001-1V9a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          {mention_count} mentions
        </div>
        {source_types && source_types.length > 0 && (
          <div className="flex items-center text-gray-500 dark:text-gray-400">
            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {source_types.join(', ')}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
        <span>
          {new Date(created_at).toLocaleDateString()}
        </span>
        <span className="text-blue-600 dark:text-blue-400">
          View details →
        </span>
      </div>
    </div>
  );
}
