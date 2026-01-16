/** Payment API client for Stripe integration. */

import apiClient from './client';

// Payments API
export const paymentsApi = {
  // Create checkout session
  createCheckout: (tierId: string, successUrl?: string, cancelUrl?: string) =>
    apiClient.post('/api/v1/payments/create-checkout', {
      tier_id: tierId,
      success_url: successUrl,
      cancel_url: cancelUrl,
    }),

  // Get customer portal URL
  getCustomerPortal: (returnUrl?: string) =>
    apiClient.post('/api/v1/payments/customer-portal', {
      return_url: returnUrl,
    }),

  // Get current subscription
  getSubscription: () =>
    apiClient.get('/api/v1/payments/subscription'),

  // Cancel subscription
  cancelSubscription: () =>
    apiClient.post('/api/v1/payments/subscription/cancel'),

  // Get pricing tiers
  getPricing: () =>
    apiClient.get('/api/v1/payments/pricing'),
};
