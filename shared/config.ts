/**
 * Shared Configuration
 * 
 * This file contains configuration settings that are shared across the monorepo.
 * Environment-specific values are loaded from environment variables.
 */

// Environment detection
const isDevelopment = process.env.NODE_ENV === 'development';
const isProduction = process.env.NODE_ENV === 'production';
const isTest = process.env.NODE_ENV === 'test';

// Environment settings
export const ENV = {
  name: process.env.NODE_ENV || 'development',
  isDevelopment,
  isProduction,
  isTest,
};

// API settings
export const API = {
  baseUrl: process.env.API_BASE_URL || 'http://localhost:4000',
  timeout: parseInt(process.env.API_TIMEOUT || '30000', 10),
  version: process.env.API_VERSION || 'v1',
};

// Authentication settings
export const AUTH = {
  jwtSecret: process.env.JWT_SECRET || 'terrafusion-dev-secret-key',
  jwtExpiresIn: process.env.JWT_EXPIRES_IN || '1d',
  cookieName: 'tf_auth_token',
  cookieMaxAge: 24 * 60 * 60 * 1000, // 1 day in milliseconds
};

// Database settings
export const DB = {
  url: process.env.DATABASE_URL,
  maxConnections: parseInt(process.env.DB_MAX_CONNECTIONS || '10', 10),
  idleTimeout: parseInt(process.env.DB_IDLE_TIMEOUT || '10000', 10), // 10 seconds
};

// Cache settings
export const CACHE = {
  ttl: parseInt(process.env.CACHE_TTL || '300', 10), // 5 minutes in seconds
  checkPeriod: parseInt(process.env.CACHE_CHECK_PERIOD || '600', 10), // 10 minutes in seconds
};

// File storage settings
export const STORAGE = {
  uploadDir: process.env.UPLOAD_DIR || './uploads',
  maxFileSize: parseInt(process.env.MAX_FILE_SIZE || '10485760', 10), // 10MB in bytes
  allowedMimeTypes: (process.env.ALLOWED_MIME_TYPES || 'image/jpeg,image/png,application/pdf').split(','),
};

// Integration settings
export const INTEGRATIONS = {
  openai: {
    apiKey: process.env.OPENAI_API_KEY,
    model: process.env.OPENAI_MODEL || 'gpt-4',
    maxTokens: parseInt(process.env.OPENAI_MAX_TOKENS || '2048', 10),
  },
  anthropic: {
    apiKey: process.env.ANTHROPIC_API_KEY,
    model: process.env.ANTHROPIC_MODEL || 'claude-3-opus-20240229',
  },
  github: {
    clientId: process.env.GITHUB_CLIENT_ID,
    clientSecret: process.env.GITHUB_CLIENT_SECRET,
    callbackUrl: process.env.GITHUB_CALLBACK_URL,
  },
};

// Feature flags
export const FEATURES = {
  marketplace: process.env.FEATURE_MARKETPLACE !== 'false',
  workflowVisualizer: process.env.FEATURE_WORKFLOW_VISUALIZER !== 'false',
  multiAgentOrchestration: process.env.FEATURE_MULTI_AGENT_ORCHESTRATION === 'true',
  advancedAnalytics: process.env.FEATURE_ADVANCED_ANALYTICS === 'true',
};

// Marketplace settings
export const MARKETPLACE = {
  commissionRate: parseFloat(process.env.MARKETPLACE_COMMISSION_RATE || '0.15'), // 15%
  featuredPluginLimit: parseInt(process.env.FEATURED_PLUGIN_LIMIT || '6', 10),
};

// Rate limiting
export const RATE_LIMITS = {
  api: {
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: parseInt(process.env.API_RATE_LIMIT || '100', 10), // limit each IP to 100 requests per windowMs
  },
  auth: {
    windowMs: 60 * 60 * 1000, // 1 hour
    max: parseInt(process.env.AUTH_RATE_LIMIT || '5', 10), // limit each IP to 5 login attempts per hour
  },
};

// Logging settings
export const LOGGING = {
  level: process.env.LOG_LEVEL || (isDevelopment ? 'debug' : 'info'),
  format: process.env.LOG_FORMAT || 'json',
};

// Cors settings
export const CORS = {
  origin: process.env.CORS_ORIGIN || '*',
  methods: process.env.CORS_METHODS || 'GET,HEAD,PUT,PATCH,POST,DELETE',
};

// Default pagination settings
export const PAGINATION = {
  defaultLimit: parseInt(process.env.DEFAULT_PAGINATION_LIMIT || '25', 10),
  maxLimit: parseInt(process.env.MAX_PAGINATION_LIMIT || '100', 10),
};