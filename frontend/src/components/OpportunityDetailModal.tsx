/** Modal component for displaying opportunity details. */

import { useState } from 'react';
import { opportunitiesApi } from '../api/client';

interface OpportunityDetailModalProps {
  opportunity: any;
  onClose: () => void;
  onUpdate: () => void;
}

export default function OpportunityDetailModal({ opportunity, onClose, onUpdate }: OpportunityDetailModalProps) {
  const [status, setStatus] = useState(opportunity.user_status || 'none');
  const [notes, setNotes] = useState(opportunity.notes || '');
  const [isSaved, setIsSaved] = useState(opportunity.is_saved || false);

  const handleSave = async () => {
    try {
      await opportunitiesApi.update(opportunity.id, {
        status,
        notes,
        is_saved: isSaved,
      });
      onUpdate();
    } catch (error) {
      console.error('Failed to update opportunity:', error);
    }
  };

  const handleStatusChange = (newStatus: string) => {
    setStatus(newStatus);
    handleSave();
  };

  const toggleSaved = async () => {
    const newSavedState = !isSaved;
    setIsSaved(newSavedState);
    try {
      await opportunitiesApi.update(opportunity.id, { is_saved: newSavedState });
      onUpdate();
    } catch (error) {
      setIsSaved(!newSavedState); // Revert on error
      console.error('Failed to update saved status:', error);
    }
  };

  const getScoreColor = (score: number | null) => {
    if (score === null) return 'text-gray-500';
    if (score >= 80) return 'text-green-600 dark:text-green-400';
    if (score >= 60) return 'text-blue-600 dark:text-blue-400';
    if (score >= 40) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={onClose}
        ></div>

        {/* Modal */}
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          {/* Header */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                {opportunity.score !== null && (
                  <div className={`text-3xl font-bold ${getScoreColor(opportunity.score)}`}>
                    {opportunity.score}
                  </div>
                )}
                {opportunity.is_validated && (
                  <div className="px-3 py-1 bg-purple-100 text-purple-800 text-sm rounded-full">
                    ✓ Validated
                  </div>
                )}
              </div>
              <button
                onClick={toggleSaved}
                className={`flex items-center space-x-1 px-3 py-1 rounded-full border ${
                  isSaved
                    ? 'bg-yellow-50 border-yellow-300 text-yellow-700'
                    : 'bg-gray-50 border-gray-300 text-gray-600 hover:bg-gray-100'
                }`}
              >
                <svg className={`w-4 h-4 ${isSaved ? 'text-yellow-500' : ''}`} fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-1.838-.197-1.539.281l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292z" />
                </svg>
                <span className="text-sm">{isSaved ? 'Saved' : 'Save'}</span>
              </button>
            </div>

            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {opportunity.title}
            </h2>

            <p className="text-gray-600 dark:text-gray-300">
              {opportunity.description}
            </p>
          </div>

          {/* Status selection */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Your Status
            </h3>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => handleStatusChange('none')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  status === 'none'
                    ? 'bg-gray-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                }`}
              >
                None
              </button>
              <button
                onClick={() => handleStatusChange('researching')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  status === 'researching'
                    ? 'bg-blue-600 text-white'
                    : 'bg-blue-50 text-blue-700 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400'
                }`}
              >
                Researching
              </button>
              <button
                onClick={() => handleStatusChange('building')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  status === 'building'
                    ? 'bg-green-600 text-white'
                    : 'bg-green-50 text-green-700 hover:bg-green-100 dark:bg-green-900/30 dark:text-green-400'
                }`}
              >
                Building
              </button>
              <button
                onClick={() => handleStatusChange('dismissed')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  status === 'dismissed'
                    ? 'bg-red-600 text-white'
                    : 'bg-red-50 text-red-700 hover:bg-red-100 dark:bg-red-900/30 dark:text-red-400'
                }`}
              >
                Dismissed
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {opportunity.competitor_count}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Competitors</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {opportunity.mention_count}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Mentions</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {opportunity.source_types?.length || 0}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Sources</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-gray-900 dark:text-white">
                  {new Date(opportunity.created_at).toLocaleDateString()}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Added</div>
              </div>
            </div>
          </div>

          {/* Sources */}
          {opportunity.source_types && opportunity.source_types.length > 0 && (
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Sources
              </h3>
              <div className="flex flex-wrap gap-2">
                {opportunity.source_types.map((source: string) => (
                  <span
                    key={source}
                    className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm"
                  >
                    {source}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Notes */}
          <div className="p-6">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Your Notes
            </h3>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              onBlur={handleSave}
              placeholder="Add your notes about this opportunity..."
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white resize-none"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              Notes are saved automatically
            </p>
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
