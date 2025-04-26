import React, { useState, useEffect } from 'react';
import { API } from '../../../shared/config';

// Plugin type definition
interface Plugin {
  id: string;
  name: string;
  description: string;
  version: string;
  publisher: string;
  tags?: string[];
  pricing?: {
    type: 'free' | 'paid' | 'subscription';
    price?: number;
    currency?: string;
  };
}

export default function App() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch plugins on component mount
  useEffect(() => {
    async function fetchPlugins() {
      try {
        setLoading(true);
        const response = await fetch(`${API.baseUrl}/api/${API.version}/market/plugins`);
        
        if (!response.ok) {
          throw new Error(`API request failed with status ${response.status}`);
        }
        
        const data = await response.json();
        setPlugins(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching plugins:', err);
        setError('Failed to load plugins. Please try again later.');
        
        // Set some fallback data for development
        setPlugins([
          {
            id: 'fallback-plugin',
            name: 'Sample Plugin',
            description: 'A sample plugin for demonstration (fallback data)',
            version: '1.0.0',
            publisher: 'TerraFusion'
          }
        ]);
      } finally {
        setLoading(false);
      }
    }
    
    fetchPlugins();
  }, []);
  
  return (
    <div className="p-8 bg-gray-900 text-white min-h-screen">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-purple-500 mb-2">Plugin Marketplace</h1>
        <p className="text-gray-400">Discover and install plugins to enhance your TerraFusion experience</p>
      </header>
      
      {/* Loading state */}
      {loading && (
        <div className="flex justify-center my-12">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
        </div>
      )}
      
      {/* Error state */}
      {error && (
        <div className="bg-red-900/30 border border-red-500/50 text-red-200 px-4 py-3 rounded-md mb-6">
          <p>{error}</p>
          <button 
            className="mt-2 text-sm bg-red-800 hover:bg-red-700 px-3 py-1 rounded" 
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        </div>
      )}
      
      {/* Plugin grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {plugins.map(plugin => (
          <div 
            key={plugin.id} 
            className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden hover:border-purple-500/50 transition-colors"
          >
            <div className="p-5">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-xl font-semibold text-white">{plugin.name}</h2>
                <span className="text-xs bg-gray-700 px-2 py-1 rounded-full">v{plugin.version}</span>
              </div>
              <p className="text-gray-400 mb-4">{plugin.description}</p>
              
              <div className="flex justify-between items-center mt-6">
                <div className="text-sm text-gray-500">
                  By <span className="text-purple-400">{plugin.publisher}</span>
                </div>
                
                <button className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors">
                  {plugin.pricing?.type === 'free' ? 'Install' : 'Purchase'}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Empty state */}
      {!loading && !error && plugins.length === 0 && (
        <div className="text-center my-16">
          <p className="text-xl text-gray-400">No plugins available at this time.</p>
          <p className="text-gray-500 mt-2">Check back later for new additions!</p>
        </div>
      )}
    </div>
  );
}