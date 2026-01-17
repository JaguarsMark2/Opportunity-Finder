/** Modal component for displaying opportunity details with dark theme. */

import { useState } from 'react';
import { opportunitiesApi } from '../api/client';
import { X, TrendingUp, Users, Target } from 'lucide-react';

interface OpportunityDetailModalProps {
  opportunity: any;
  onClose: () => void;
  onUpdate: () => void;
}

export default function OpportunityDetailModal({ opportunity, onClose, onUpdate }: OpportunityDetailModalProps) {
  const [status, setStatus] = useState(opportunity.user_status || 'none');
  const [notes, setNotes] = useState(opportunity.user_notes || '');
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
      setIsSaved(!newSavedState);
      console.error('Failed to update saved status:', error);
    }
  };

  const getScoreColor = (score: number | null) => {
    if (score === null) return 'text-gray-500';
    if (score >= 80) return 'text-emerald-500 border-emerald-500 bg-emerald-500/10';
    if (score >= 60) return 'text-blue-500 border-blue-500 bg-blue-500/10';
    if (score >= 40) return 'text-amber-500 border-amber-500 bg-amber-500/10';
    return 'text-red-500 border-red-500 bg-red-500/10';
  };

  const getScoreLabel = (score: number | null) => {
    if (score === null) return 'N/A';
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Maybe';
    return 'Reject';
  };

  const getRecommendation = (score: number | null, competitionLevel: string) => {
    if (score === null) return 'Not scored';
    if (score >= 80 && competitionLevel === 'Low') return 'Build immediately';
    if (score >= 70) return 'Build immediately';
    if (score >= 60) return 'Validate with landing page first';
    if (score >= 40) return 'High competition - need unique angle';
    return 'High risk - overcrowded market';
  };

  const scoreColorClass = getScoreColor(opportunity.score);

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center p-8 bg-black/80 backdrop-blur-sm"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className={`relative w-full max-w-3xl max-h-[90vh] overflow-auto rounded-3xl bg-gradient-to-br from-slate-800 to-slate-900 border-2 shadow-2xl ${scoreColorClass}`}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 text-slate-400 transition-colors rounded-lg hover:bg-slate-700/50 hover:text-slate-200"
        >
          <X size={24} />
        </button>

        {/* Header */}
        <div className="p-8 border-b border-slate-700/50">
          <div className="flex items-start justify-between gap-6 flex-wrap">
            <div className="flex-1 min-w-[300px]">
              <h2 className="text-4xl font-extrabold text-white tracking-tight mb-3">
                {opportunity.title}
              </h2>
              <p className="text-lg text-slate-300 leading-relaxed">
                {opportunity.problem || opportunity.description}
              </p>
            </div>
            <div className={`p-4 text-center border-3 rounded-2xl min-w-[120px] ${scoreColorClass}`}>
              <div className="text-5xl font-extrabold leading-none">
                {opportunity.score ?? 'N/A'}
              </div>
              <div className="text-sm font-semibold uppercase tracking-wider mt-2">
                {getScoreLabel(opportunity.score)}
              </div>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="p-8 space-y-8">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              {
                label: 'Competitors',
                value: opportunity.competitor_count ?? 0,
                icon: Users,
                color: 'text-amber-500',
                bg: 'bg-amber-500/10',
              },
              {
                label: 'Mentions',
                value: opportunity.mention_count ?? 0,
                icon: TrendingUp,
                color: 'text-blue-400',
                bg: 'bg-blue-500/10',
              },
              {
                label: 'Competition',
                value: opportunity.competition_level || 'N/A',
                icon: Users,
                color: 'text-amber-500',
                bg: 'bg-amber-500/10',
              },
              {
                label: 'Sources',
                value: opportunity.source_types?.length || 0,
                icon: Target,
                color: 'text-purple-500',
                bg: 'bg-purple-500/10',
              }
            ].map((item) => {
              const IconComponent = item.icon;
              return (
                <div key={item.label} className="p-5 rounded-xl bg-slate-800/50 border border-slate-700/50">
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`w-8 h-8 rounded-lg ${item.bg} flex items-center justify-center`}>
                      <IconComponent size={16} className={item.color} />
                    </div>
                    <span className="text-sm font-medium text-slate-400">{item.label}</span>
                  </div>
                  <div className="text-xl font-bold text-white ml-11">
                    {item.value}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Recommendation */}
          <div className="p-5 rounded-xl bg-blue-500/10 border border-blue-500/20">
            <div className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-2">
              Recommendation
            </div>
            <div className="text-lg font-bold text-white">
              {getRecommendation(opportunity.score, opportunity.competition_level)}
            </div>
          </div>

          {/* Sources */}
          {opportunity.source_types && opportunity.source_types.length > 0 && (
            <div>
              <div className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
                Data Sources
              </div>
              <div className="flex flex-wrap gap-2">
                {opportunity.source_types.map((source: string) => (
                  <span
                    key={source}
                    className="px-3 py-1.5 text-sm font-medium text-slate-300 rounded-lg bg-slate-700/50 border border-slate-600/50"
                  >
                    {source}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* User Actions Section */}
          <div className="p-6 rounded-xl bg-slate-800/50 border border-slate-700/50 space-y-5">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                Your Status
              </div>
              <button
                onClick={toggleSaved}
                className={`px-5 py-2.5 rounded-lg font-semibold flex items-center gap-2 transition-all ${
                  isSaved
                    ? 'bg-amber-500/15 border-amber-500/30 text-amber-400'
                    : 'bg-slate-900/50 border-slate-600/50 text-slate-300'
                } border`}
              >
                <span className="text-lg">{isSaved ? '⭐' : '☆'}</span>
                {isSaved ? 'Saved' : 'Save'}
              </button>
            </div>

            <div className="flex flex-wrap gap-3">
              {[
                { value: 'none', label: 'None', color: 'text-slate-400', border: 'border-slate-600/50' },
                { value: 'researching', label: 'Researching', color: 'text-blue-400', border: 'border-blue-500/30' },
                { value: 'building', label: 'Building', color: 'text-emerald-400', border: 'border-emerald-500/30' },
                { value: 'dismissed', label: 'Dismissed', color: 'text-red-400', border: 'border-red-500/30' }
              ].map((statusOption) => (
                <button
                  key={statusOption.value}
                  onClick={() => handleStatusChange(statusOption.value)}
                  className={`px-5 py-2.5 rounded-lg font-semibold transition-all border ${
                    status === statusOption.value
                      ? `${statusOption.color} ${statusOption.border} bg-current/10`
                      : 'bg-slate-900/50 border-slate-600/50 text-slate-300'
                  }`}
                >
                  {statusOption.label}
                </button>
              ))}
            </div>
          </div>

          {/* Notes */}
          <div>
            <div className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
              Your Notes
            </div>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              onBlur={handleSave}
              placeholder="Add your notes about this opportunity..."
              rows={4}
              className="w-full px-4 py-3.5 rounded-xl bg-slate-900/50 border border-slate-700 text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
            <p className="mt-2 text-xs text-slate-500">
              Notes are saved automatically
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
