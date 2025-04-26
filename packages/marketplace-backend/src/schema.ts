/**
 * Marketplace Schema
 * 
 * This file re-exports the marketplace types from the shared schema,
 * and adds any marketplace-specific types that aren't shared.
 */

// Re-export shared types
export { 
  PluginManifest, 
  PluginPricing, 
  PluginRequirements,
  PluginPurchase
} from '../../shared/schema';

// Marketplace-specific types that aren't in the shared schema

/**
 * Plugin installation status
 */
export interface PluginInstallation {
  pluginId: string;
  userId: string;
  workspaceId: string;
  installedAt: Date;
  status: 'active' | 'disabled' | 'error';
  version: string;
  lastUsed?: Date;
  config?: Record<string, any>;
}

/**
 * Plugin review
 */
export interface PluginReview {
  id: string;
  pluginId: string;
  userId: string;
  rating: number; // 1-5
  comment?: string;
  createdAt: Date;
  updatedAt?: Date;
}

/**
 * Plugin analytics data
 */
export interface PluginAnalytics {
  pluginId: string;
  installs: number;
  activeInstalls: number;
  averageRating: number;
  reviewCount: number;
  dailyActiveUsers: number;
}