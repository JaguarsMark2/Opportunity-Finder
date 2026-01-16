/** Admin API client for administrative operations. */

import apiClient from './client';

// Admin API
export const adminApi = {
  // ============================================================================
  // Pricing Management
  // ============================================================================
  listPricingTiers: (params?: { include_inactive?: boolean }) =>
    apiClient.get('/api/v1/admin/pricing', { params }),

  getPricingTier: (tierId: string) =>
    apiClient.get(`/api/v1/admin/pricing/${tierId}`),

  createPricingTier: (data: {
    name: string;
    slug: string;
    description: string;
    price: number;
    yearly_price?: number;
    currency?: string;
    stripe_price_id?: string;
    stripe_yearly_price_id?: string;
    opportunities_limit?: number;
    scan_frequency?: string;
    email_alerts_enabled?: boolean;
    email_frequency?: string;
    features?: string[];
    is_active?: boolean;
    display_order?: number;
  }) => apiClient.post('/api/v1/admin/pricing', data),

  updatePricingTier: (tierId: string, data: any) =>
    apiClient.patch(`/api/v1/admin/pricing/${tierId}`, data),

  deletePricingTier: (tierId: string) =>
    apiClient.delete(`/api/v1/admin/pricing/${tierId}`),

  // ============================================================================
  // User Management
  // ============================================================================
  listUsers: (params?: {
    search?: string;
    role?: string;
    subscription_status?: string;
    subscription_tier_id?: string;
    is_email_verified?: boolean;
    limit?: number;
    cursor?: string;
  }) => apiClient.get('/api/v1/admin/users', { params }),

  getUserDetails: (userId: string) =>
    apiClient.get(`/api/v1/admin/users/${userId}`),

  updateUser: (userId: string, data: {
    role?: string;
    subscription_status?: string;
    subscription_tier_id?: string;
    email_verified?: boolean;
  }) => apiClient.patch(`/api/v1/admin/users/${userId}`, data),

  // ============================================================================
  // Scoring Configuration
  // ============================================================================
  getScoringConfig: () =>
    apiClient.get('/api/v1/admin/scoring/config'),

  updateScoringWeights: (data: {
    demand_weight?: number;
    competition_weight?: number;
    engagement_weight?: number;
    validation_weight?: number;
    recency_weight?: number;
  }) => apiClient.put('/api/v1/admin/scoring/weights', data),

  updateScoringThresholds: (data: {
    high_score_threshold?: number;
    medium_score_threshold?: number;
    validation_threshold?: number;
    min_competitors?: number;
    max_competitors?: number;
  }) => apiClient.put('/api/v1/admin/scoring/thresholds', data),

  // ============================================================================
  // Analytics
  // ============================================================================
  getAnalytics: (params?: { time_range?: string }) =>
    apiClient.get('/api/v1/admin/analytics', { params }),

  // ============================================================================
  // System Health
  // ============================================================================
  getSystemHealth: () =>
    apiClient.get('/api/v1/admin/health'),
};
