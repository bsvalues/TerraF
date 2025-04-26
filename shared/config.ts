/**
 * Centralized Configuration
 * 
 * This file provides centralized access to environment variables and configuration
 * settings used across the TerraFusion platform.
 */

// Environment detection
export const ENV = {
  isDevelopment: process.env.NODE_ENV === 'development',
  isProduction: process.env.NODE_ENV === 'production',
  isTest: process.env.NODE_ENV === 'test',
};

// API and service endpoints
export const API = {
  baseUrl: process.env.API_BASE_URL || 'http://localhost:4000',
  version: 'v1',
};

// Database configuration
export const DATABASE = {
  url: process.env.DATABASE_URL,
  poolSize: parseInt(process.env.DATABASE_POOL_SIZE || '10', 10),
  ssl: process.env.DATABASE_SSL === 'true',
};

// Authentication configuration
export const AUTH = {
  jwtSecret: process.env.JWT_SECRET || 'dev-secret-do-not-use-in-production',
  expiresIn: process.env.JWT_EXPIRES_IN || '24h',
  cookieName: 'terrafusion_token',
};

// Feature flags
export const FEATURES = {
  enableMarketplace: process.env.FEATURE_MARKETPLACE === 'true',
  enableBetaFeatures: process.env.FEATURE_BETA === 'true',
  enableAnalytics: process.env.FEATURE_ANALYTICS !== 'false', // Enabled by default
};

// Service configurations
export const SERVICES = {
  syncService: {
    batchSize: parseInt(process.env.SYNC_BATCH_SIZE || '100', 10),
    retryAttempts: parseInt(process.env.SYNC_RETRY_ATTEMPTS || '3', 10),
    workerCount: parseInt(process.env.SYNC_WORKER_COUNT || '2', 10),
  },
  marketplace: {
    storagePrefix: process.env.MARKETPLACE_STORAGE_PREFIX || 'plugins',
    defaultCurrency: process.env.MARKETPLACE_CURRENCY || 'USD',
  },
  fileStorage: {
    baseUrl: process.env.FILE_STORAGE_URL || 'http://localhost:4000/files',
    uploadPath: process.env.FILE_UPLOAD_PATH || './uploads',
    maxSizeMB: parseInt(process.env.FILE_MAX_SIZE_MB || '50', 10),
  },
};

// External service integrations
export const INTEGRATIONS = {
  stripe: {
    publicKey: process.env.STRIPE_PUBLIC_KEY,
    secretKey: process.env.STRIPE_SECRET_KEY,
    webhookSecret: process.env.STRIPE_WEBHOOK_SECRET,
  },
  mapbox: {
    apiKey: process.env.MAPBOX_API_KEY,
  },
};

// Logging configuration
export const LOGGING = {
  level: process.env.LOG_LEVEL || 'info',
  format: process.env.LOG_FORMAT || 'json',
};