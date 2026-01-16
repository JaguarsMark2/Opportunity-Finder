/** Billing and subscription management page. */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { paymentsApi } from '../api/payments';

export default function BillingPage() {
  const queryClient = useQueryClient();
  const [checkoutStatus, setCheckoutStatus] = useState<'idle' | 'processing' | 'success' | 'canceled'>('idle');

  // Check URL for checkout status
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('success') === 'true') {
      setCheckoutStatus('success');
      // Clear URL params
      window.history.replaceState({}, '', window.location.pathname);
      queryClient.invalidateQueries({ queryKey: ['subscription'] });
    } else if (urlParams.get('canceled') === 'true') {
      setCheckoutStatus('canceled');
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [queryClient]);

  const { data: subscription, isLoading } = useQuery({
    queryKey: ['subscription'],
    queryFn: async () => {
      const response = await paymentsApi.getSubscription();
      return response.data;
    },
  });

  const { data: pricing } = useQuery({
    queryKey: ['pricing-tiers'],
    queryFn: async () => {
      const response = await paymentsApi.getPricing();
      return response.data;
    },
  });

  const checkoutMutation = useMutation({
    mutationFn: (tierId: string) => paymentsApi.createCheckout(tierId),
    onSuccess: (data) => {
      if (data.data.checkout_url) {
        window.location.href = data.data.checkout_url;
      }
    },
  });

  const portalMutation = useMutation({
    mutationFn: () => paymentsApi.getCustomerPortal(),
    onSuccess: (data) => {
      if (data.data.portal_url) {
        window.location.href = data.data.portal_url;
      }
    },
  });

  const cancelMutation = useMutation({
    mutationFn: paymentsApi.cancelSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscription'] });
    },
  });

  const handleSubscribe = (tierId: string) => {
    setCheckoutStatus('processing');
    checkoutMutation.mutate(tierId);
  };

  const handleManageBilling = () => {
    portalMutation.mutate();
  };

  const handleCancelSubscription = () => {
    if (confirm('Are you sure you want to cancel your subscription? You will lose access to premium features at the end of your billing period.')) {
      cancelMutation.mutate();
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'trialing':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      case 'past_due':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      case 'canceled':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Billing & Subscription
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your subscription and payment methods
          </p>
        </div>

        {/* Checkout status messages */}
        {checkoutStatus === 'success' && (
          <div className="mb-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
            <p className="text-green-800 dark:text-green-400">
              ✓ Payment successful! Your subscription is now active.
            </p>
          </div>
        )}
        {checkoutStatus === 'canceled' && (
          <div className="mb-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <p className="text-yellow-800 dark:text-yellow-400">
              Payment was canceled. You can try again anytime.
            </p>
          </div>
        )}

        {/* Current subscription */}
        {isLoading ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <div className="animate-pulse">
              <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4"></div>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
            </div>
          </div>
        ) : subscription?.data ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700 mb-8">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Current Subscription
            </h2>

            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
                    {subscription.data.tier_name || 'Free Plan'}
                  </h3>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(subscription.data.subscription_status)}`}>
                    {subscription.data.subscription_status}
                  </span>
                </div>

                {subscription.data.tier_price > 0 && (
                  <p className="text-lg text-gray-600 dark:text-gray-400">
                    ${subscription.data.tier_price}/month
                  </p>
                )}

                {subscription.data.cancel_at_period_end && (
                  <p className="text-sm text-orange-600 dark:text-orange-400 mt-2">
                    ⚠️ Your subscription will be canceled at the end of your billing period
                  </p>
                )}
              </div>

              <div className="flex space-x-3">
                {subscription.data.stripe_subscription_id && (
                  <>
                    <button
                      onClick={handleManageBilling}
                      disabled={portalMutation.isPending}
                      className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
                    >
                      Manage Billing
                    </button>
                    {!subscription.data.cancel_at_period_end && subscription.data.subscription_status === 'active' && (
                      <button
                        onClick={handleCancelSubscription}
                        disabled={cancelMutation.isPending}
                        className="px-4 py-2 border border-red-300 dark:border-red-800 text-red-700 dark:text-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
                      >
                        Cancel Plan
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        ) : null}

        {/* Pricing tiers */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {subscription?.data?.stripe_subscription_id ? 'Change Plan' : 'Choose a Plan'}
          </h2>

          {pricing?.data?.items ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {pricing.data.items.map((tier: any) => {
                const isCurrentPlan = subscription?.data?.tier_id === tier.id;
                const isFree = tier.price === 0;

                return (
                  <div
                    key={tier.id}
                    className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border ${
                      isCurrentPlan
                        ? 'border-blue-500 dark:border-blue-500 ring-2 ring-blue-500 dark:ring-blue-500'
                        : 'border-gray-200 dark:border-gray-700'
                    } p-6`}
                  >
                    {isCurrentPlan && (
                      <div className="text-sm font-medium text-blue-600 dark:text-blue-400 mb-2">
                        Current Plan
                      </div>
                    )}

                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                      {tier.name}
                    </h3>

                    <div className="mb-4">
                      <span className="text-3xl font-bold text-gray-900 dark:text-white">
                        ${tier.price}
                      </span>
                      <span className="text-gray-600 dark:text-gray-400">
                        /month
                      </span>
                    </div>

                    <p className="text-gray-600 dark:text-gray-300 text-sm mb-6">
                      {tier.description}
                    </p>

                    <ul className="space-y-3 mb-6">
                      {tier.features.map((feature: string, idx: number) => (
                        <li key={idx} className="flex items-start text-sm text-gray-600 dark:text-gray-400">
                          <svg className="w-5 h-5 mr-2 text-green-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                          {feature}
                        </li>
                      ))}
                    </ul>

                    <button
                      onClick={() => handleSubscribe(tier.id)}
                      disabled={isCurrentPlan || checkoutMutation.isPending}
                      className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${
                        isCurrentPlan
                          ? 'bg-gray-100 text-gray-400 cursor-not-allowed dark:bg-gray-700'
                          : isFree
                          ? 'bg-gray-100 text-gray-800 hover:bg-gray-200 dark:bg-gray-700 dark:text-white'
                          : 'bg-blue-600 text-white hover:bg-blue-700'
                      }`}
                    >
                      {isCurrentPlan
                        ? 'Current Plan'
                        : isFree
                        ? 'Downgrade to Free'
                        : 'Subscribe'}
                    </button>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-4"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
              </div>
            </div>
          )}
        </div>

        {/* Billing info */}
        <div className="mt-8 bg-gray-50 dark:bg-gray-800/50 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            Billing Information
          </h3>
          <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <li>• You can change or cancel your plan at any time</li>
            <li>• Billing is handled securely through Stripe</li>
            <li>• Your payment information is stored securely by Stripe</li>
            <li>• You'll receive an email receipt for each payment</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
