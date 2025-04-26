/**
 * Streamlit Bridge Module
 * 
 * This module provides a bridge between the Streamlit application and the new API services.
 * It helps with the gradual migration by enabling communication between the old and new systems.
 */

import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';
import { API } from '../../../shared/config';
import { createHash } from 'crypto';

// Configure the base API client
const apiClient = axios.create({
  baseURL: API.baseUrl || 'http://localhost:4000',
  timeout: API.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Interface for API request options
 */
interface ApiRequestOptions {
  endpoint: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  data?: any;
  params?: Record<string, any>;
  headers?: Record<string, string>;
  version?: string;
  withCredentials?: boolean;
  cacheKey?: string;
  cacheTTL?: number; // In milliseconds
}

// Simple in-memory cache
const cache: Record<string, { data: any; timestamp: number }> = {};

/**
 * Call the API server from Streamlit
 * 
 * This function allows the Streamlit application to communicate with 
 * the new API server during the migration process.
 */
export async function callApi<T = any>(options: ApiRequestOptions): Promise<T> {
  const { 
    endpoint, 
    method = 'GET', 
    data = null, 
    params = {}, 
    headers = {},
    version = API.version, 
    withCredentials = true,
    cacheKey,
    cacheTTL = 60000 // Default cache TTL: 60 seconds
  } = options;

  // Check if we should use cache
  if (method === 'GET' && cacheKey) {
    const fullCacheKey = createHash('md5')
      .update(`${endpoint}:${JSON.stringify(params)}:${cacheKey}`)
      .digest('hex');
    
    const cachedItem = cache[fullCacheKey];
    
    if (cachedItem && (Date.now() - cachedItem.timestamp) < cacheTTL) {
      console.log(`[StreamlitBridge] Using cached data for ${endpoint}`);
      return cachedItem.data;
    }
  }

  // Prepare request config
  const config: AxiosRequestConfig = {
    method,
    url: `/api/${version}/${endpoint.replace(/^\//, '')}`,
    params,
    data,
    headers,
    withCredentials
  };

  try {
    // Make the API call
    const response: AxiosResponse<T> = await apiClient.request(config);
    
    // Cache the response if needed
    if (method === 'GET' && cacheKey) {
      const fullCacheKey = createHash('md5')
        .update(`${endpoint}:${JSON.stringify(params)}:${cacheKey}`)
        .digest('hex');
      
      cache[fullCacheKey] = {
        data: response.data,
        timestamp: Date.now()
      };
    }
    
    return response.data;
  } catch (error: any) {
    console.error(`[StreamlitBridge] API Error:`, error.message);
    
    // Enhance error with API details
    const enhancedError = new Error(
      `API call failed: ${error.message} (${method} ${endpoint})`
    );
    
    // Add axios response data if available
    if (error.response) {
      (enhancedError as any).status = error.response.status;
      (enhancedError as any).data = error.response.data;
    }
    
    throw enhancedError;
  }
}

/**
 * Clear the bridge cache
 */
export function clearCache(): void {
  Object.keys(cache).forEach(key => delete cache[key]);
  console.log('[StreamlitBridge] Cache cleared');
}

/**
 * Extended API methods for specific domains
 */
export const domainApis = {
  /**
   * Marketplace API methods
   */
  marketplace: {
    /**
     * List available plugins
     */
    listPlugins: (params: Record<string, any> = {}) => 
      callApi({ 
        endpoint: 'market/plugins', 
        params,
        cacheKey: 'plugins_list'
      }),
    
    /**
     * Get plugin details
     */
    getPlugin: (pluginId: string) => 
      callApi({ 
        endpoint: `market/plugins/${pluginId}`,
        cacheKey: `plugin_${pluginId}`
      }),
    
    /**
     * Purchase a plugin
     */
    purchasePlugin: (pluginId: string, paymentDetails: any) => 
      callApi({
        endpoint: `market/plugins/${pluginId}/purchase`,
        method: 'POST',
        data: paymentDetails
      })
  },
  
  /**
   * User management API methods
   */
  users: {
    /**
     * Get current user
     */
    getCurrentUser: () => 
      callApi({ 
        endpoint: 'users/me',
        cacheKey: 'current_user'
      }),
      
    /**
     * Update user settings
     */
    updateSettings: (settings: any) => 
      callApi({
        endpoint: 'users/settings',
        method: 'PUT',
        data: settings
      })
  }
};

export default {
  callApi,
  clearCache,
  domainApis
};