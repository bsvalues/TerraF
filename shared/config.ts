/**
 * Shared Configuration
 * 
 * Central configuration settings for all TerraFusion applications and services.
 * Environment-specific settings are loaded from environment variables with defaults.
 */

// Environment settings
export const ENV = {
  environment: process.env.NODE_ENV || 'development',
  isDevelopment: (process.env.NODE_ENV || 'development') === 'development',
  isProduction: process.env.NODE_ENV === 'production',
  isTest: process.env.NODE_ENV === 'test',
};

// Server configuration
export const SERVER = {
  port: parseInt(process.env.SERVER_PORT || '4000', 10),
  apiVersion: process.env.API_VERSION || 'v1',
  hostname: process.env.HOSTNAME || 'localhost',
  allowedOrigins: (process.env.ALLOWED_ORIGINS || 'http://localhost:3000').split(','),
  logLevel: process.env.LOG_LEVEL || 'info',
};

// Database configuration
export const DATABASE = {
  url: process.env.DATABASE_URL || '',
  ssl: process.env.DATABASE_SSL === 'true',
  poolSize: parseInt(process.env.DATABASE_POOL_SIZE || '10', 10),
  maxIdleTime: parseInt(process.env.DATABASE_MAX_IDLE_TIME || '30000', 10),
};

// Authentication configuration
export const AUTH = {
  jwtSecret: process.env.JWT_SECRET || 'dev-secret-do-not-use-in-production',
  jwtExpiry: process.env.JWT_EXPIRY || '1d',
  cookieName: process.env.AUTH_COOKIE_NAME || 'tf_auth',
  secureCookies: process.env.SECURE_COOKIES === 'true' || ENV.isProduction,
};

// Streaming AI configuration
export const AI = {
  openaiApiKey: process.env.OPENAI_API_KEY || '',
  anthropicApiKey: process.env.ANTHROPIC_API_KEY || '',
  defaultModel: process.env.DEFAULT_AI_MODEL || 'gpt-4',
  maxTokens: parseInt(process.env.MAX_AI_TOKENS || '4096', 10),
  temperature: parseFloat(process.env.AI_TEMPERATURE || '0.7'),
};

// Feature flags
export const FEATURES = {
  enableMarketplace: process.env.ENABLE_MARKETPLACE !== 'false',
  enableAnalytics: process.env.ENABLE_ANALYTICS !== 'false',
  enableAdminPanel: process.env.ENABLE_ADMIN_PANEL === 'true',
  betaFeatures: process.env.ENABLE_BETA_FEATURES === 'true',
};

// API integration endpoints
export const API = {
  baseUrl: process.env.API_BASE_URL || '',
  version: process.env.API_VERSION || 'v1',
  timeout: parseInt(process.env.API_TIMEOUT || '30000', 10),
};

// Monitoring and analytics
export const MONITORING = {
  sentryDsn: process.env.SENTRY_DSN || '',
  loggingEnabled: process.env.LOGGING_ENABLED !== 'false',
  metricsEnabled: process.env.METRICS_ENABLED === 'true',
};