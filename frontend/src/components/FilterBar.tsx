/** Filter bar component for filtering opportunities. */

import { useState } from 'react';

interface FilterBarProps {
  onFiltersChange: (filters: {
    search: string;
    minScore: number | null;
    maxScore: number | null;
    isValidated: boolean | null;
    timeRange: string;
    sortBy: string;
  }) => void;
}

export default function FilterBar({ onFiltersChange }: FilterBarProps) {
  const [search, setSearch] = useState('');
  const [minScore, setMinScore] = useState<number | null>(null);
  const [maxScore, setMaxScore] = useState<number | null>(null);
  const [isValidated, setIsValidated] = useState<boolean | null>(null);
  const [timeRange, setTimeRange] = useState('all');
  const [sortBy, setSortBy] = useState('score_desc');

  const handleSearchChange = (value: string) => {
    setSearch(value);
    updateFilters({ search: value });
  };

  const handleMinScoreChange = (value: string) => {
    const score = value ? parseInt(value, 10) : null;
    setMinScore(score);
    updateFilters({ minScore: score });
  };

  const handleMaxScoreChange = (value: string) => {
    const score = value ? parseInt(value, 10) : null;
    setMaxScore(score);
    updateFilters({ maxScore: score });
  };

  const handleValidationToggle = () => {
    const newValue = isValidated === null ? true : isValidated === true ? false : null;
    setIsValidated(newValue);
    updateFilters({ isValidated: newValue });
  };

  const updateFilters = (updates: Partial<{
    search: string;
    minScore: number | null;
    maxScore: number | null;
    isValidated: boolean | null;
    timeRange: string;
    sortBy: string;
  }>) => {
    onFiltersChange({
      search,
      minScore,
      maxScore,
      isValidated,
      timeRange,
      sortBy,
      ...updates,
    });
  };

  const resetFilters = () => {
    setSearch('');
    setMinScore(null);
    setMaxScore(null);
    setIsValidated(null);
    setTimeRange('all');
    setSortBy('score_desc');
    onFiltersChange({
      search: '',
      minScore: null,
      maxScore: null,
      isValidated: null,
      timeRange: 'all',
      sortBy: 'score_desc',
    });
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        {/* Search */}
        <div className="lg:col-span-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Search
          </label>
          <input
            type="text"
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder="Search opportunities..."
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          />
        </div>

        {/* Min Score */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Min Score
          </label>
          <input
            type="number"
            min="0"
            max="100"
            value={minScore ?? ''}
            onChange={(e) => handleMinScoreChange(e.target.value)}
            placeholder="0"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          />
        </div>

        {/* Max Score */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Max Score
          </label>
          <input
            type="number"
            min="0"
            max="100"
            value={maxScore ?? ''}
            onChange={(e) => handleMaxScoreChange(e.target.value)}
            placeholder="100"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          />
        </div>

        {/* Time Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Time Range
          </label>
          <select
            value={timeRange}
            onChange={(e) => {
              setTimeRange(e.target.value);
              updateFilters({ timeRange: e.target.value });
            }}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="all">All Time</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
        </div>

        {/* Sort By */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Sort By
          </label>
          <select
            value={sortBy}
            onChange={(e) => {
              setSortBy(e.target.value);
              updateFilters({ sortBy: e.target.value });
            }}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="score_desc">Score (High-Low)</option>
            <option value="score_asc">Score (Low-High)</option>
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
          </select>
        </div>
      </div>

      {/* Second row: Validation toggle and reset */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-6">
          {/* Validation Toggle */}
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={isValidated === true}
              onChange={handleValidationToggle}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              Validated Only
            </span>
            {isValidated === false && (
              <span className="text-xs text-gray-500">(showing unvalidated)</span>
            )}
          </label>
        </div>

        {/* Reset Button */}
        <button
          onClick={resetFilters}
          className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
        >
          Reset Filters
        </button>
      </div>
    </div>
  );
}
