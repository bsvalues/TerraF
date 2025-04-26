/**
 * Shared Schema Definitions
 * 
 * Common type definitions that are shared across services
 * in the TerraFusion monorepo.
 */

/**
 * User Account
 */
export interface User {
  id: string;
  email: string;
  displayName: string;
  avatarUrl?: string;
  role: 'user' | 'admin' | 'developer';
  createdAt: Date;
  updatedAt: Date;
  lastLoginAt?: Date;
  verifiedAt?: Date;
  settings?: UserSettings;
}

/**
 * User Settings
 */
export interface UserSettings {
  theme: 'light' | 'dark' | 'system';
  notifications: {
    email: boolean;
    push: boolean;
    inApp: boolean;
  };
  timezone?: string;
  language?: string;
  defaultDashboard?: string;
}

/**
 * Organization
 */
export interface Organization {
  id: string;
  name: string;
  slug: string;
  logoUrl?: string;
  contactEmail?: string;
  description?: string;
  createdAt: Date;
  updatedAt: Date;
  members?: OrganizationMember[];
  workspaces?: Workspace[];
}

/**
 * Organization Member
 */
export interface OrganizationMember {
  userId: string;
  organizationId: string;
  role: 'owner' | 'admin' | 'member' | 'guest';
  joinedAt: Date;
  invitedBy?: string;
}

/**
 * Workspace
 */
export interface Workspace {
  id: string;
  name: string;
  slug: string;
  organizationId: string;
  description?: string;
  createdAt: Date;
  updatedAt: Date;
  createdBy: string;
  isArchived: boolean;
  members?: WorkspaceMember[];
}

/**
 * Workspace Member
 */
export interface WorkspaceMember {
  userId: string;
  workspaceId: string;
  role: 'owner' | 'editor' | 'viewer';
  joinedAt: Date;
}

/**
 * Plugin Manifest
 */
export interface PluginManifest {
  id: string;
  name: string;
  description: string;
  version: string;
  publisher: string;
  entryPoint: string;
  icon?: string;
  tags?: string[];
  pricing: PluginPricing;
  requirements?: PluginRequirements;
  compatibleWith?: string[];
  isPublic: boolean;
  createdAt: Date;
  updatedAt: Date;
  publishedAt?: Date;
}

/**
 * Plugin Pricing
 */
export interface PluginPricing {
  type: 'free' | 'paid' | 'subscription';
  price?: number;
  currency?: string;
  billingCycle?: 'monthly' | 'yearly' | 'one-time';
  trialDays?: number;
}

/**
 * Plugin Requirements
 */
export interface PluginRequirements {
  minApiVersion?: string;
  permissions?: string[];
  dependencies?: {
    name: string;
    version: string;
  }[];
}

/**
 * Plugin Purchase
 */
export interface PluginPurchase {
  id: string;
  pluginId: string;
  userId: string;
  organizationId?: string;
  purchaseDate: Date;
  expiryDate?: Date;
  status: 'active' | 'expired' | 'cancelled';
  paymentMethod?: string;
  transactionId?: string;
  price: number;
  currency: string;
}

/**
 * Workflow Definition
 */
export interface Workflow {
  id: string;
  name: string;
  description?: string;
  workspaceId: string;
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
  isPublic: boolean;
  isTemplate: boolean;
  steps: WorkflowStep[];
  version: number;
  status: 'draft' | 'active' | 'archived';
}

/**
 * Workflow Step
 */
export interface WorkflowStep {
  id: string;
  workflowId: string;
  name: string;
  description?: string;
  type: string;
  config: Record<string, any>;
  position: number;
  dependencies: string[];
  timeout?: number;
}

/**
 * API Token
 */
export interface ApiToken {
  id: string;
  name: string;
  userId: string;
  token: string;
  createdAt: Date;
  expiresAt?: Date;
  lastUsedAt?: Date;
  scopes: string[];
}

/**
 * Notification
 */
export interface Notification {
  id: string;
  userId: string;
  title: string;
  message: string;
  status: 'unread' | 'read' | 'archived';
  type: 'info' | 'success' | 'warning' | 'error';
  linkUrl?: string;
  createdAt: Date;
  readAt?: Date;
  entityType?: string;
  entityId?: string;
}

/**
 * Activity Log
 */
export interface ActivityLog {
  id: string;
  userId: string;
  action: string;
  entityType: string;
  entityId: string;
  timestamp: Date;
  details?: Record<string, any>;
  ipAddress?: string;
  userAgent?: string;
}