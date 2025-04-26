/**
 * Shared Schema Definitions
 * 
 * This file contains shared type definitions and interfaces used across
 * multiple services and applications in the TerraFusion platform.
 */

// Base entity interface with common fields
export interface BaseEntity {
  id: string;
  createdAt: Date;
  updatedAt: Date;
}

// User entity
export interface User extends BaseEntity {
  email: string;
  name: string;
  role: UserRole;
  organizationId?: string;
  preferences?: UserPreferences;
  isActive: boolean;
}

export enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  DEVELOPER = 'developer',
  ANALYST = 'analyst',
}

export interface UserPreferences {
  theme?: 'light' | 'dark';
  notifications?: boolean;
  dashboardLayout?: string;
}

// Property-related interfaces
export interface Property extends BaseEntity {
  name: string;
  address: Address;
  ownerId: string;
  type: PropertyType;
  status: PropertyStatus;
  value?: number;
  assessmentId?: string;
  metadata?: Record<string, any>;
}

export enum PropertyType {
  RESIDENTIAL = 'residential',
  COMMERCIAL = 'commercial',
  INDUSTRIAL = 'industrial',
  AGRICULTURAL = 'agricultural',
  MIXED_USE = 'mixed_use',
}

export enum PropertyStatus {
  ACTIVE = 'active',
  PENDING = 'pending',
  ARCHIVED = 'archived',
  DELETED = 'deleted',
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zip: string;
  country: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
}

// Sync job related interfaces
export interface SyncJob extends BaseEntity {
  name: string;
  status: SyncJobStatus;
  source: string;
  target: string;
  progress: number;
  startedAt?: Date;
  completedAt?: Date;
  error?: string;
  itemsProcessed: number;
  itemsTotal: number;
  userId: string;
  metadata?: Record<string, any>;
}

export enum SyncJobStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

// Plugin marketplace interfaces
export interface PluginManifest extends BaseEntity {
  name: string;
  description: string;
  version: string;
  publisher: string;
  entryPoint: string;
  icon?: string;
  tags: string[];
  pricing: PluginPricing;
  requirements: PluginRequirements;
  compatibleWith: string[];
  isPublic: boolean;
}

export interface PluginPricing {
  type: 'free' | 'paid' | 'subscription';
  price?: number;
  currency?: string;
  billingCycle?: 'monthly' | 'yearly' | 'one-time';
  trialDays?: number;
}

export interface PluginRequirements {
  minApiVersion: string;
  permissions: string[];
  dependencies?: string[];
}

export interface PluginPurchase extends BaseEntity {
  pluginId: string;
  userId: string;
  transactionId: string;
  price: number;
  currency: string;
  status: 'completed' | 'pending' | 'failed' | 'refunded';
}