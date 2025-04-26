import { Link } from 'react-router-dom';
import PluginCard from '../components/PluginCard';

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

interface HomeProps {
  plugins: Plugin[];
  isLoading: boolean;
  error: string | null;
}

const Home = ({ plugins, isLoading, error }: HomeProps) => {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="py-12 md:py-20 text-center">
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          <span className="text-primary-light">Enhance</span> Your Development Workflow
        </h1>
        <p className="text-xl text-zinc-300 max-w-3xl mx-auto mb-8">
          Discover powerful plugins and integrations for TerraFusion to optimize your code,
          visualize workflows, and supercharge your development process.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/marketplace" className="btn btn-primary px-6 py-3">
            Browse Marketplace
          </Link>
          <Link to="/documentation" className="btn btn-secondary px-6 py-3">
            Read Documentation
          </Link>
        </div>
      </section>

      {/* Featured Plugins Section */}
      <section>
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Featured Plugins</h2>
          <Link to="/marketplace" className="text-primary-light hover:text-primary">
            View All
          </Link>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="card h-64 shimmer"></div>
            ))}
          </div>
        ) : error ? (
          <div className="card p-8 bg-red-900/20 border border-red-800">
            <p className="text-red-300">{error}</p>
            <button className="btn btn-secondary mt-4">Retry</button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {plugins.map((plugin) => (
              <PluginCard key={plugin.id} {...plugin} />
            ))}
          </div>
        )}
      </section>

      {/* Features Section */}
      <section className="py-10">
        <h2 className="text-2xl font-bold mb-8 text-center">Why Choose TerraFusion?</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="card">
            <div className="mb-4">
              <svg 
                className="w-12 h-12 text-primary-light mb-4" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth="2" 
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                ></path>
              </svg>
              <h3 className="text-xl font-bold">AI-Powered Code Analysis</h3>
            </div>
            <p className="text-zinc-300">
              Advanced AI models analyze your code for quality, performance, and security issues while suggesting optimizations.
            </p>
          </div>
          
          <div className="card">
            <div className="mb-4">
              <svg 
                className="w-12 h-12 text-primary-light mb-4" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth="2" 
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                ></path>
              </svg>
              <h3 className="text-xl font-bold">Intelligent Workflow Mapping</h3>
            </div>
            <p className="text-zinc-300">
              Visualize and optimize your development workflows with intelligent agents that learn from your processes.
            </p>
          </div>
          
          <div className="card">
            <div className="mb-4">
              <svg 
                className="w-12 h-12 text-primary-light mb-4" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth="2" 
                  d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z"
                ></path>
              </svg>
              <h3 className="text-xl font-bold">Extensible Plugin System</h3>
            </div>
            <p className="text-zinc-300">
              Customize and extend functionality with our growing marketplace of plugins for different technologies and workflows.
            </p>
          </div>
        </div>
      </section>

      {/* Call to Action */}
      <section className="py-16 text-center bg-gradient-to-r from-primary-dark/20 to-accent-dark/20 rounded-xl">
        <h2 className="text-3xl font-bold mb-4">Ready to Transform Your Development Workflow?</h2>
        <p className="text-xl text-zinc-300 max-w-2xl mx-auto mb-8">
          Join thousands of developers who are already using TerraFusion to optimize their development process.
        </p>
        <Link to="/get-started" className="btn btn-accent px-8 py-3 text-lg">
          Get Started for Free
        </Link>
      </section>
    </div>
  );
};

export default Home;