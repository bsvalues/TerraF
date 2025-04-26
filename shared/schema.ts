/**
 * Shared Schema Definitions
 * 
 * This file contains type definitions that are shared across the monorepo.
 * It serves as the single source of truth for data models used in the application.
 */

// ===== User Related Types =====

/**
 * User role within the system
 */
export type UserRole = 'admin' | 'user' | 'developer';

/**
 * User notification preferences
 */
export interface UserNotificationSettings {
  email: boolean;
  push: boolean;
  inApp: boolean;
}

/**
 * User settings
 */
export interface UserSettings {
  theme: 'dark' | 'light' | 'system';
  notifications: UserNotificationSettings;
  developerMode?: boolean;
  experimentalFeatures?: boolean;
}

/**
 * User model
 */
export interface User {
  id: string;
  email: string;
  displayName: string;
  role: UserRole;
  settings: UserSettings;
  avatar?: string;
  createdAt: Date;
  updatedAt: Date;
  lastLogin?: Date;
  isActive: boolean;
  workspaces?: string[]; // IDs of workspaces the user belongs to
}

// ===== Workspace Related Types =====

/**
 * Workspace model
 */
export interface Workspace {
  id: string;
  name: string;
  description?: string;
  createdBy: string; // User ID
  createdAt: Date;
  updatedAt: Date;
  isActive: boolean;
  members: WorkspaceMember[];
  settings?: WorkspaceSettings;
}

/**
 * Workspace member with role
 */
export interface WorkspaceMember {
  userId: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  joinedAt: Date;
}

/**
 * Workspace settings
 */
export interface WorkspaceSettings {
  defaultBranch: string;
  codeQualityChecks: boolean;
  securityScanning: boolean;
  workflowAutomation: boolean;
  integrations: Record<string, boolean>;
}

// ===== Plugin Related Types =====

/**
 * Plugin pricing types
 */
export type PluginPricingType = 'free' | 'paid' | 'subscription';

/**
 * Billing cycle options
 */
export type BillingCycle = 'monthly' | 'quarterly' | 'annual';

/**
 * Plugin pricing model
 */
export interface PluginPricing {
  type: PluginPricingType;
  price?: number;
  currency?: string;
  billingCycle?: BillingCycle;
  trialDays?: number;
}

/**
 * Plugin permission requirements
 */
export interface PluginRequirements {
  minApiVersion: string;
  permissions: string[];
  dependencies?: string[];
}

/**
 * Plugin model
 */
export interface Plugin {
  id: string;
  name: string;
  description: string;
  version: string;
  publisher: string;
  entryPoint: string;
  isPublic: boolean;
  pricing: PluginPricing;
  tags?: string[];
  createdAt: Date;
  updatedAt: Date;
  requirements: PluginRequirements;
}

/**
 * Plugin purchase/installation record
 */
export interface PluginPurchase {
  id: string;
  pluginId: string;
  userId: string;
  workspaceId?: string;
  purchaseDate: Date;
  expiryDate?: Date;
  status: 'active' | 'expired' | 'cancelled';
  transactionId?: string;
  price: number;
  currency: string;
}

// ===== Workflow Related Types =====

/**
 * Workflow status
 */
export type WorkflowStatus = 'draft' | 'active' | 'archived' | 'deleted';

/**
 * Workflow step type
 */
export type WorkflowStepType = 
  | 'code_analysis' 
  | 'security_scan' 
  | 'quality_check' 
  | 'architecture_analysis'
  | 'documentation' 
  | 'custom';

/**
 * Workflow step model
 */
export interface WorkflowStep {
  id: string;
  name: string;
  type: WorkflowStepType;
  description?: string;
  pluginId?: string; // ID of a plugin that provides this step
  config: Record<string, any>;
  position: number;
  isDependentOn?: string[]; // IDs of steps this step depends on
}

/**
 * Workflow model
 */
export interface Workflow {
  id: string;
  name: string;
  description?: string;
  workspaceId: string;
  createdBy: string; // User ID
  createdAt: Date;
  updatedAt: Date;
  isPublic: boolean;
  isTemplate: boolean;
  version: number;
  status: WorkflowStatus;
  steps: WorkflowStep[];
}

/**
 * Workflow run status
 */
export type WorkflowRunStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';

/**
 * Workflow run result
 */
export interface WorkflowRun {
  id: string;
  workflowId: string;
  workspaceId: string;
  triggeredBy: string; // User ID
  startedAt: Date;
  completedAt?: Date;
  status: WorkflowRunStatus;
  stepResults: WorkflowStepResult[];
}

/**
 * Workflow step execution result
 */
export interface WorkflowStepResult {
  stepId: string;
  startedAt: Date;
  completedAt?: Date;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  output?: any;
  errorMessage?: string;
}

// ===== Report Related Types =====

/**
 * Report type
 */
export type ReportType = 
  | 'code_quality' 
  | 'security' 
  | 'architecture' 
  | 'performance'
  | 'workflow_analysis' 
  | 'custom';

/**
 * Report severity level
 */
export type ReportSeverity = 'info' | 'low' | 'medium' | 'high' | 'critical';

/**
 * Report model
 */
export interface Report {
  id: string;
  workspaceId: string;
  workflowRunId?: string;
  type: ReportType;
  title: string;
  description?: string;
  createdAt: Date;
  createdBy: string; // User ID
  data: ReportData;
}

/**
 * Report data structure
 */
export interface ReportData {
  summary: {
    score?: number;
    passedChecks: number;
    failedChecks: number;
    skippedChecks: number;
  };
  issues: ReportIssue[];
  recommendations?: ReportRecommendation[];
  metadata?: Record<string, any>;
}

/**
 * Report issue
 */
export interface ReportIssue {
  id: string;
  title: string;
  description: string;
  severity: ReportSeverity;
  location?: {
    file?: string;
    startLine?: number;
    endLine?: number;
  };
  codeSnippet?: string;
  ruleId?: string;
  tags?: string[];
}

/**
 * Report recommendation
 */
export interface ReportRecommendation {
  id: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high';
  effort: 'trivial' | 'easy' | 'medium' | 'hard';
  potentialImpact: 'low' | 'medium' | 'high';
}

// ===== Analytics Related Types =====

/**
 * Analytics time period
 */
export type AnalyticsPeriod = 'day' | 'week' | 'month' | 'quarter' | 'year';

/**
 * Analytics metric
 */
export interface AnalyticsMetric {
  id: string;
  name: string;
  value: number;
  unit?: string;
  previousValue?: number;
  changePercentage?: number;
  trend?: 'up' | 'down' | 'stable';
}

/**
 * Analytics time series data point
 */
export interface AnalyticsDataPoint {
  timestamp: Date;
  value: number;
}

/**
 * Analytics time series
 */
export interface AnalyticsTimeSeries {
  id: string;
  name: string;
  period: AnalyticsPeriod;
  unit?: string;
  data: AnalyticsDataPoint[];
}

/**
 * Analytics dashboard
 */
export interface AnalyticsDashboard {
  id: string;
  workspaceId: string;
  name: string;
  description?: string;
  createdBy: string; // User ID
  createdAt: Date;
  updatedAt: Date;
  metrics: AnalyticsMetric[];
  timeSeries: AnalyticsTimeSeries[];
  filters?: Record<string, any>;
}