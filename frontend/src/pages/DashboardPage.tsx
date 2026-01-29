/** Dashboard page with dark mode design matching reference. */

import { useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { opportunitiesApi } from '../api/client';
import OpportunityDetailModal from '../components/OpportunityDetailModal';
import { Target, TrendingUp, AlertCircle, BarChart3, Search, Filter } from 'lucide-react';

export default function DashboardPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterScore, setFilterScore] = useState(0);
  const [sortBy, setSortBy] = useState('score');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedOpportunity, setSelectedOpportunity] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data: opportunitiesData, isLoading } = useQuery({
    queryKey: ['opportunities', searchTerm, filterScore, sortBy],
    queryFn: async () => {
      const params: any = { limit: 100 };
      if (filterScore > 0) params.min_score = filterScore;
      if (searchTerm) params.search = searchTerm;
      if (sortBy === 'score') params.sort = '-score';
      if (sortBy === 'revenue') params.sort = '-revenue';
      if (sortBy === 'mentions') params.sort = '-mentions';
      const response = await opportunitiesApi.list(params);
      return response.data.data;
    },
  });

  const { data: stats } = useQuery({
    queryKey: ['opportunities-stats'],
    queryFn: async () => {
      const response = await opportunitiesApi.getStats();
      return response.data.data;
    },
  });

  const filteredOpportunities = useMemo(() => {
    if (!opportunitiesData) return [];
    return opportunitiesData;
  }, [opportunitiesData]);

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-500 border-emerald-500 bg-emerald-500/10';
    if (score >= 60) return 'text-blue-500 border-blue-500 bg-blue-500/10';
    if (score >= 40) return 'text-amber-500 border-amber-500 bg-amber-500/10';
    return 'text-red-500 border-red-500 bg-red-500/10';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Maybe';
    return 'Reject';
  };

  const getRecommendation = (score: number, competitionLevel: string) => {
    if (score >= 80 && competitionLevel === 'Low') return 'Build immediately';
    if (score >= 70) return 'Build immediately';
    if (score >= 60) return 'Validate with landing page first';
    if (score >= 40) return 'High competition - need unique angle';
    return 'High risk - overcrowded market';
  };

  const handleOpportunityClick = useCallback((opportunity: any) => {
    setSelectedOpportunity(opportunity);
    setIsModalOpen(true);
  }, []);

  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false);
    setSelectedOpportunity(null);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-slate-200">
      {/* Stats Bar */}
      <div className="max-w-[1400px] mx-auto px-8 mt-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {[
            { label: 'Total Opportunities', value: stats?.total_opportunities || 0, icon: Target, color: '#3b82f6' },
            { label: 'Validated', value: stats?.validated_count || 0, icon: TrendingUp, color: '#10b981' },
            { label: 'High Score (70+)', value: stats?.score_distribution?.['81-100'] || 0, icon: AlertCircle, color: '#f59e0b' },
            { label: 'Average Score', value: stats?.avg_score ? Math.round(stats.avg_score) : 0, icon: BarChart3, color: '#8b5cf6' }
          ].map((stat) => {
            const IconComponent = stat.icon;
            return (
              <div key={stat.label} className="p-6 rounded-2xl bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm transition-all cursor-pointer hover:bg-slate-800/70">
                <div className="flex justify-between items-start mb-3">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    {stat.label}
                  </span>
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: `${stat.color}15` }}>
                    <IconComponent size={18} style={{ color: stat.color }} />
                  </div>
                </div>
                <div className="text-4xl font-extrabold text-white tracking-tight">
                  {stat.value}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1400px] mx-auto px-8 pb-12">
        {/* Search and Filters */}
        <div className="p-6 mb-8 rounded-2xl bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm">
          <div className="flex gap-4 flex-wrap items-center">
            <div className="flex-1 min-w-[300px] relative">
              <div className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500">
                <Search />
              </div>
              <input
                type="text"
                placeholder="Search opportunities..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-slate-900/50 border border-slate-700/50 text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              />
            </div>

            <div className="flex gap-3 flex-wrap">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-4 py-3.5 rounded-xl bg-slate-900/50 border border-slate-700/50 text-slate-200 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
              >
                <option value="score">Sort by Score</option>
                <option value="revenue">Sort by Competition</option>
                <option value="mentions">Sort by Mentions</option>
              </select>

              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`px-5 py-3.5 rounded-xl font-semibold flex items-center gap-2 transition-all ${
                  showFilters
                    ? 'bg-blue-500/15 border-blue-500/30 text-blue-400'
                    : 'bg-slate-900/50 border-slate-700/50 text-slate-300'
                } border`}
              >
                <Filter size={18} />
                Filters
              </button>
            </div>
          </div>

          {showFilters && (
            <div className="pt-6 mt-6 border-t border-slate-700/50">
              <label className="block text-sm font-semibold text-slate-400 mb-3">
                Minimum Score: {filterScore}
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={filterScore}
                onChange={(e) => setFilterScore(Number(e.target.value))}
                className="w-full h-1.5 rounded-full appearance-none cursor-pointer bg-slate-700 accent-blue-500"
                style={{
                  background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${filterScore}%, rgba(51, 65, 85, 0.5) ${filterScore}%, rgba(51, 65, 85, 0.5) 100%)`
                }}
              />
            </div>
          )}
        </div>

        {/* Opportunities Grid */}
        {isLoading ? (
          <div className="p-20 text-center rounded-2xl bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm">
            <p className="text-slate-400">Loading opportunities...</p>
          </div>
        ) : filteredOpportunities.length === 0 ? (
          <div className="p-20 text-center rounded-2xl bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm">
            <div className="mx-auto mb-4 text-slate-600">
              <AlertCircle size={48} />
            </div>
            <h3 className="text-xl font-bold text-slate-200 mb-2">No opportunities found</h3>
            <p className="text-slate-400">
              Try adjusting your filters or search term
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {filteredOpportunities.map((opportunity: any) => {
              const scoreColorClass = getScoreColor(opportunity.score);
              return (
                <div
                  key={opportunity.id}
                  onClick={() => handleOpportunityClick(opportunity)}
                  className="p-6 rounded-2xl bg-slate-800/50 border border-slate-700/50 cursor-pointer transition-all hover:bg-slate-800/70 backdrop-blur-sm relative overflow-hidden"
                >
                  {/* Score Badge */}
                  <div className={`absolute top-5 right-5 p-2 rounded-xl border-2 flex flex-col items-center gap-0.5 ${scoreColorClass}`}>
                    <div className="text-2xl font-extrabold leading-none">
                      {opportunity.score}
                    </div>
                    <div className="text-[10px] font-semibold uppercase tracking-wider">
                      {getScoreLabel(opportunity.score)}
                    </div>
                  </div>

                  <div className="pr-20">
                    <h3 className="text-xl font-bold text-white mb-3 leading-tight">
                      {opportunity.title}
                    </h3>

                    <p className="text-sm text-slate-400 mb-5 leading-relaxed">
                      {opportunity.problem || opportunity.description}
                    </p>

                    <div className="grid grid-cols-2 gap-3 mb-5">
                      <div>
                        <div className="text-xs text-slate-500 mb-1 font-medium">Competition</div>
                        <div className="text-sm font-semibold text-slate-200">
                          {opportunity.competition_level || 'N/A'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-1 font-medium">Mentions</div>
                        <div className="text-sm font-bold text-blue-400">
                          {opportunity.mention_count || 0}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-1 font-medium">Growth</div>
                        <div className="text-sm font-bold text-emerald-400">
                          {opportunity.growth_rate || 'N/A'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-1 font-medium">Volume</div>
                        <div className="text-sm font-semibold text-slate-200">
                          {opportunity.keyword_volume || 'N/A'}
                        </div>
                      </div>
                    </div>

                    <div className="px-4 py-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-sm font-semibold text-blue-400">
                      {getRecommendation(opportunity.score, opportunity.competition_level)}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {isModalOpen && selectedOpportunity && (
        <OpportunityDetailModal
          opportunity={selectedOpportunity}
          onClose={handleCloseModal}
          onUpdate={() => window.location.reload()}
        />
      )}
    </div>
  );
}
