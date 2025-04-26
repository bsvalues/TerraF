import { useEffect, useState } from 'react';
import { Routes, Route, Link } from 'react-router-dom';

// Import components
import Header from './components/Header';
import Footer from './components/Footer';
import PluginCard from './components/PluginCard';

// Import pages
import Home from './pages/Home';
import PluginDetails from './pages/PluginDetails';
import NotFound from './pages/NotFound';

// Interface for plugin object
interface Plugin {
  id: string;
  name: string;
  description: string;
  version: string;
  publisher: string;
  pricing: {
    type: 'free' | 'paid' | 'subscription';
    price?: number;
    currency?: string;
  };
  tags?: string[];
}

function App() {
  const [featuredPlugins, setFeaturedPlugins] = useState<Plugin[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // In a real implementation, this would use the API client to fetch data
    const fetchFeaturedPlugins = async () => {
      try {
        setIsLoading(true);
        
        // Simulate API call with timeout
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Mock data for now - would come from API
        const plugins = [
          {
            id: 'plugin-1',
            name: 'Code Quality Analyzer',
            description: 'Analyzes code for quality and best practices',
            version: '1.0.0',
            publisher: 'TerraFusion',
            pricing: { type: 'free' as const },
            tags: ['code-quality', 'analysis']
          },
          {
            id: 'plugin-2',
            name: 'Architecture Visualizer',
            description: 'Visualizes application architecture',
            version: '1.1.0',
            publisher: 'TerraFusion',
            pricing: { type: 'free' as const },
            tags: ['architecture', 'visualization']
          },
          {
            id: 'plugin-3',
            name: 'Advanced Security Scanner',
            description: 'Enterprise-grade security scanning for code',
            version: '2.0.0',
            publisher: 'Security Partners',
            pricing: {
              type: 'subscription' as const,
              price: 29.99,
              currency: 'USD'
            },
            tags: ['security', 'enterprise']
          },
        ];
        
        setFeaturedPlugins(plugins);
      } catch (err) {
        setError('Failed to load plugins. Please try again later.');
        console.error('Error fetching plugins:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchFeaturedPlugins();
  }, []);

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      
      <main className="flex-1 container mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Home plugins={featuredPlugins} isLoading={isLoading} error={error} />} />
          <Route path="/plugins/:id" element={<PluginDetails />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      
      <Footer />
    </div>
  );
}

export default App;