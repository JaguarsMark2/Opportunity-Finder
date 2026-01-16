/** Pricing tier management page for admins. */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../../api/admin';

export default function PricingManagement() {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingTier, setEditingTier] = useState<any>(null);

  const { data: tiers, isLoading } = useQuery({
    queryKey: ['admin-pricing'],
    queryFn: async () => {
      const response = await adminApi.listPricingTiers({ include_inactive: true });
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: adminApi.createPricingTier,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-pricing'] });
      setShowCreateModal(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ tierId, data }: { tierId: string; data: any }) =>
      adminApi.updatePricingTier(tierId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-pricing'] });
      setEditingTier(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: adminApi.deletePricingTier,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-pricing'] });
    },
  });

  const handleToggleActive = (tier: any) => {
    updateMutation.mutate({
      tierId: tier.id,
      data: { is_active: !tier.is_active },
    });
  };

  const handleDelete = (tierId: string) => {
    if (confirm('Are you sure you want to delete this pricing tier?')) {
      deleteMutation.mutate(tierId);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Pricing Management
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage subscription tiers and pricing
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + Add Tier
        </button>
      </div>

      {/* Pricing tiers */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {tiers?.data?.items?.map((tier: any) => (
          <div
            key={tier.id}
            className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border ${
              !tier.is_active
                ? 'border-gray-300 dark:border-gray-600 opacity-60'
                : 'border-gray-200 dark:border-gray-700'
            }`}
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {tier.name}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {tier.slug}
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    tier.is_active
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400'
                  }`}
                >
                  {tier.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>

            <div className="mb-4">
              <div className="text-3xl font-bold text-gray-900 dark:text-white">
                ${tier.price}
                <span className="text-lg font-normal text-gray-500">/mo</span>
              </div>
              {tier.yearly_price && (
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  ${tier.yearly_price}/year
                </div>
              )}
            </div>

            <p className="text-gray-600 dark:text-gray-300 text-sm mb-4">
              {tier.description}
            </p>

            <ul className="space-y-2 mb-4">
              {tier.features?.map((feature: string, idx: number) => (
                <li key={idx} className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                  <svg className="w-4 h-4 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  {feature}
                </li>
              ))}
            </ul>

            <div className="text-xs text-gray-500 dark:text-gray-400 mb-4">
              <div>Scan: {tier.scan_frequency}</div>
              <div>Emails: {tier.email_alerts_enabled ? tier.email_frequency : 'disabled'}</div>
              {tier.opportunities_limit && (
                <div>Limit: {tier.opportunities_limit} opportunities</div>
              )}
              {tier.user_count !== undefined && (
                <div>Users: {tier.user_count}</div>
              )}
            </div>

            <div className="flex space-x-2">
              <button
                onClick={() => handleToggleActive(tier)}
                className={`flex-1 px-3 py-2 text-sm rounded-md ${
                  tier.is_active
                    ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400'
                    : 'bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-400'
                }`}
              >
                {tier.is_active ? 'Disable' : 'Enable'}
              </button>
              <button
                onClick={() => setEditingTier(tier)}
                className="px-3 py-2 text-sm bg-blue-100 text-blue-800 rounded-md hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-400"
              >
                Edit
              </button>
              <button
                onClick={() => handleDelete(tier.id)}
                className="px-3 py-2 text-sm bg-red-100 text-red-800 rounded-md hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Create/Edit Modal */}
      {(showCreateModal || editingTier) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black bg-opacity-50" onClick={() => {
            setShowCreateModal(false);
            setEditingTier(null);
          }}></div>
          <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              {editingTier ? 'Edit Pricing Tier' : 'Create Pricing Tier'}
            </h2>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                const data = {
                  name: String(formData.get('name') || ''),
                  slug: String(formData.get('slug') || ''),
                  description: String(formData.get('description') || ''),
                  price: parseFloat(String(formData.get('price') || '0')),
                  yearly_price: formData.get('yearly_price')
                    ? parseFloat(String(formData.get('yearly_price')))
                    : undefined,
                  currency: String(formData.get('currency') || 'USD'),
                  scan_frequency: String(formData.get('scan_frequency') || 'daily'),
                  email_alerts_enabled: formData.get('email_alerts_enabled') === 'true',
                  email_frequency: String(formData.get('email_frequency') || 'daily'),
                  features: String(formData.get('features') || '').split('\n').filter(Boolean),
                  is_active: formData.get('is_active') === 'true',
                  display_order: parseInt(String(formData.get('display_order') || '0'), 10),
                };

                if (editingTier) {
                  updateMutation.mutate({ tierId: editingTier.id, data });
                } else {
                  createMutation.mutate(data);
                }
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Name
                </label>
                <input
                  name="name"
                  defaultValue={editingTier?.name}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Slug
                </label>
                <input
                  name="slug"
                  defaultValue={editingTier?.slug}
                  required
                  pattern="[a-z0-9-]+"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  name="description"
                  defaultValue={editingTier?.description}
                  required
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Monthly Price
                  </label>
                  <input
                    name="price"
                    type="number"
                    step="0.01"
                    defaultValue={editingTier?.price}
                    required
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Yearly Price
                  </label>
                  <input
                    name="yearly_price"
                    type="number"
                    step="0.01"
                    defaultValue={editingTier?.yearly_price}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Features (one per line)
                </label>
                <textarea
                  name="features"
                  defaultValue={editingTier?.features?.join('\n')}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div className="flex space-x-2 pt-4">
                <button
                  type="submit"
                  disabled={createMutation.isPending || updateMutation.isPending}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {editingTier ? 'Update' : 'Create'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingTier(null);
                  }}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
