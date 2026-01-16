/** Profile page for user settings and stats. */

import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { userApi } from '../api/client';

export default function ProfilePage() {
  const { user } = useAuth();

  const { data: stats } = useQuery({
    queryKey: ['user-stats'],
    queryFn: async () => {
      const response = await userApi.getStats();
      return response.data;
    },
  });

  const { data: savedOpportunities } = useQuery({
    queryKey: ['saved-opportunities'],
    queryFn: async () => {
      const response = await userApi.getSaved({ limit: 10 });
      return response.data;
    },
  });

  const getTierLabel = (tier: string | null) => {
    if (!tier) return 'Free';
    switch (tier) {
      case 'starter':
        return 'Starter';
      case 'pro':
        return 'Pro';
      case 'enterprise':
        return 'Enterprise';
      default:
        return 'Free';
    }
  };

  const getTierColor = (tier: string | null) => {
    if (!tier) return 'bg-gray-100 text-gray-800';
    switch (tier) {
      case 'starter':
        return 'bg-blue-100 text-blue-800';
      case 'pro':
        return 'bg-purple-100 text-purple-800';
      case 'enterprise':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'trialing':
        return 'bg-blue-100 text-blue-800';
      case 'past_due':
        return 'bg-red-100 text-red-800';
      case 'canceled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Page header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Profile
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your account and view your activity
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Account info */}
          <div className="lg:col-span-2 space-y-6">
            {/* User details */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Account Details
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Email
                  </label>
                  <p className="text-gray-900 dark:text-white">{user?.email}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Member Since
                  </label>
                  <p className="text-gray-900 dark:text-white">
                    {user?.created_at
                      ? new Date(user.created_at).toLocaleDateString()
                      : 'N/A'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Subscription Status
                  </label>
                  <div className="flex items-center space-x-2 mt-1">
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                        user?.subscription_status || 'inactive'
                      )}`}
                    >
                      {user?.subscription_status || 'Inactive'}
                    </span>
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium ${getTierColor(
                        user?.subscription_tier_id || null
                      )}`}
                    >
                      {getTierLabel(user?.subscription_tier_id || null)}
                    </span>
                  </div>
                </div>
                {!user?.email_verified && (
                  <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
                    <p className="text-sm text-yellow-800 dark:text-yellow-400">
                      Please verify your email address to access all features.
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Stats */}
            {stats?.data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Your Activity
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {stats.data.viewed_count || 0}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Viewed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {stats.data.saved_count || 0}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Saved</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                      {stats.data.researching_count || 0}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Researching</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {stats.data.building_count || 0}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Building</div>
                  </div>
                </div>
              </div>
            )}

            {/* Saved opportunities */}
            {savedOpportunities?.data?.items &&
              savedOpportunities.data.items.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                    Recently Saved
                  </h2>
                  <div className="space-y-3">
                    {savedOpportunities.data.items.map((opp: any) => (
                      <div
                        key={opp.id}
                        className="p-4 bg-gray-50 dark:bg-gray-700 rounded-md border border-gray-200 dark:border-gray-600"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h3 className="font-medium text-gray-900 dark:text-white">
                              {opp.title}
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mt-1">
                              {opp.description}
                            </p>
                          </div>
                          {opp.score !== null && (
                            <div className="ml-4">
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm font-medium">
                                {opp.score}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick actions */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Quick Actions
              </h2>
              <div className="space-y-3">
                <a
                  href="/dashboard"
                  className="block px-4 py-2 text-center bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Browse Opportunities
                </a>
                <a
                  href="/saved"
                  className="block px-4 py-2 text-center border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  View Saved Items
                </a>
              </div>
            </div>

            {/* Subscription info */}
            {(!user?.subscription_tier_id || user.subscription_tier_id === 'free') && (
              <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg shadow-sm p-6 text-white">
                <h2 className="text-lg font-semibold mb-2">Upgrade to Pro</h2>
                <p className="text-sm text-blue-100 mb-4">
                  Get access to more opportunities, advanced filters, and priority support.
                </p>
                <button className="w-full px-4 py-2 bg-white text-blue-600 rounded-md hover:bg-blue-50 transition-colors font-medium">
                  View Plans
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
