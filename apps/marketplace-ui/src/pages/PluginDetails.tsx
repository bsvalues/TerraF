import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';

interface PluginDetails {
  id: string;
  name: string;
  description: string;
  version: string;
  publisher: string;
  entryPoint: string;
  isPublic: boolean;
  createdAt: string;
  updatedAt: string;
  pricing: {
    type: 'free' | 'paid' | 'subscription';
    price?: number;
    currency?: string;
    billingCycle?: string;
    trialDays?: number;
  };
  tags?: string[];
  requirements: {
    minApiVersion: string;
    permissions: string[];
  };
}

const PluginDetails = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [plugin, setPlugin] = useState<PluginDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isPurchasing, setIsPurchasing] = useState(false);
  const [purchaseSuccess, setPurchaseSuccess] = useState(false);

  useEffect(() => {
    const fetchPluginDetails = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Mock data - in a real app, this would be an API call
        if (!id || (id !== 'plugin-1' && id !== 'plugin-2' && id !== 'plugin-3')) {
          throw new Error('Plugin not found');
        }
        
        // Simulating data that would come from the API
        const pluginData = {
          id,
          name: id === 'plugin-1' ? 'Code Quality Analyzer' : 
                id === 'plugin-2' ? 'Architecture Visualizer' : 
                'Advanced Security Scanner',
          description: id === 'plugin-1' 
            ? 'Analyzes code for quality issues, potential bugs, and ensures adherence to best practices. Provides actionable recommendations for improvement.'
            : id === 'plugin-2' 
            ? 'Visualizes application architecture with interactive diagrams, identifies dependencies, and suggests structural improvements.'
            : 'Enterprise-grade security scanning for code, identifying vulnerabilities, potential exploits, and security risks before they reach production.',
          version: id === 'plugin-3' ? '2.0.0' : '1.0.0',
          publisher: id === 'plugin-3' ? 'Security Partners' : 'TerraFusion',
          entryPoint: './index.js',
          isPublic: true,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          pricing: id === 'plugin-3' ? {
            type: 'subscription' as const,
            price: 29.99,
            currency: 'USD',
            billingCycle: 'monthly',
            trialDays: 14
          } : {
            type: 'free' as const
          },
          tags: id === 'plugin-1' ? ['code-quality', 'analysis'] :
                id === 'plugin-2' ? ['architecture', 'visualization'] :
                ['security', 'enterprise'],
          requirements: {
            minApiVersion: '1.0.0',
            permissions: ['codebase:read', 'reports:write']
          }
        };
        
        setPlugin(pluginData);
      } catch (err) {
        console.error('Error fetching plugin details:', err);
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchPluginDetails();
  }, [id]);

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
  };

  const handlePurchase = async () => {
    try {
      setIsPurchasing(true);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Success
      setPurchaseSuccess(true);
      
      // Reset after showing success message
      setTimeout(() => {
        setPurchaseSuccess(false);
      }, 3000);
    } catch (err) {
      console.error('Error purchasing plugin:', err);
      setError('Failed to process purchase. Please try again.');
    } finally {
      setIsPurchasing(false);
    }
  };

  // Helper for price formatting
  const formatPrice = (price?: number, currency?: string) => {
    if (price === undefined || currency === undefined) {
      return 'Free';
    }
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(price);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="w-16 h-16 border-4 border-primary-light border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card p-8 bg-red-900/20 border border-red-800 max-w-xl mx-auto">
        <h2 className="text-xl font-bold mb-4">Error</h2>
        <p className="text-red-300 mb-6">{error}</p>
        <button 
          onClick={() => navigate(-1)} 
          className="btn btn-secondary"
        >
          Go Back
        </button>
      </div>
    );
  }

  if (!plugin) {
    return null;
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Back Button */}
      <div className="mb-6">
        <button 
          onClick={() => navigate(-1)} 
          className="flex items-center text-zinc-400 hover:text-primary-light"
        >
          <svg 
            className="w-5 h-5 mr-1" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth="2" 
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
          Back to Marketplace
        </button>
      </div>
      
      {/* Plugin Header */}
      <div className="card mb-8">
        <div className="flex flex-col md:flex-row justify-between">
          <div className="mb-6 md:mb-0">
            <div className="flex items-center mb-2">
              <h1 className="text-3xl font-bold mr-3">{plugin.name}</h1>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                plugin.pricing.type === 'free' 
                  ? 'bg-emerald-800 text-emerald-100' 
                  : plugin.pricing.type === 'paid' 
                  ? 'bg-blue-800 text-blue-100' 
                  : 'bg-purple-800 text-purple-100'
              }`}>
                {plugin.pricing.type === 'free' ? 'Free' : plugin.pricing.type === 'paid' ? 'Paid' : 'Subscription'}
              </span>
            </div>
            <p className="text-zinc-400 mb-4">by {plugin.publisher} • Version {plugin.version}</p>
            <p className="text-zinc-300 max-w-3xl">{plugin.description}</p>
          </div>
          
          <div className="flex flex-col space-y-4">
            {plugin.pricing.type !== 'free' && (
              <div className="text-right">
                <p className="text-2xl font-bold">
                  {formatPrice(plugin.pricing.price, plugin.pricing.currency)}
                  {plugin.pricing.billingCycle && <span className="text-sm text-zinc-400">/{plugin.pricing.billingCycle}</span>}
                </p>
                {plugin.pricing.trialDays && (
                  <p className="text-sm text-zinc-400">
                    {plugin.pricing.trialDays}-day free trial
                  </p>
                )}
              </div>
            )}
            
            <button 
              onClick={handlePurchase}
              disabled={isPurchasing || purchaseSuccess}
              className={`btn btn-primary min-w-[160px] ${isPurchasing ? 'opacity-70 cursor-not-allowed' : ''} ${purchaseSuccess ? 'bg-green-700 hover:bg-green-700' : ''}`}
            >
              {isPurchasing ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing...
                </span>
              ) : purchaseSuccess ? (
                <span className="flex items-center justify-center">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                  </svg>
                  Installed!
                </span>
              ) : (
                `${plugin.pricing.type === 'free' ? 'Install' : 'Purchase'} Plugin`
              )}
            </button>
          </div>
        </div>
      </div>
      
      {/* Tabs */}
      <div className="border-b border-slate-700 mb-6">
        <nav className="flex space-x-8">
          <button
            onClick={() => handleTabChange('overview')}
            className={`py-4 font-medium text-sm border-b-2 px-1 ${
              activeTab === 'overview'
                ? 'border-primary text-primary-light'
                : 'border-transparent text-zinc-400 hover:text-zinc-300 hover:border-slate-600'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => handleTabChange('docs')}
            className={`py-4 font-medium text-sm border-b-2 px-1 ${
              activeTab === 'docs'
                ? 'border-primary text-primary-light'
                : 'border-transparent text-zinc-400 hover:text-zinc-300 hover:border-slate-600'
            }`}
          >
            Documentation
          </button>
          <button
            onClick={() => handleTabChange('support')}
            className={`py-4 font-medium text-sm border-b-2 px-1 ${
              activeTab === 'support'
                ? 'border-primary text-primary-light'
                : 'border-transparent text-zinc-400 hover:text-zinc-300 hover:border-slate-600'
            }`}
          >
            Support
          </button>
        </nav>
      </div>
      
      {/* Tab Content */}
      <div className="space-y-8">
        {activeTab === 'overview' && (
          <div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="col-span-2">
                <div className="card mb-8">
                  <h2 className="text-xl font-bold mb-4">Features</h2>
                  <ul className="space-y-3 text-zinc-300">
                    {id === 'plugin-1' ? (
                      <>
                        <li className="flex items-start">
                          <svg className="w-5 h-5 text-primary-light mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                          </svg>
                          <span>Automated code quality checks against industry standards</span>
                        </li>
                        <li className="flex items-start">
                          <svg className="w-5 h-5 text-primary-light mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                          </svg>
                          <span>Detailed reports with actionable improvement suggestions</span>
                        </li>
                        <li className="flex items-start">
                          <svg className="w-5 h-5 text-primary-light mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                          </svg>
                          <span>Customizable rule sets for different project requirements</span>
                        </li>
                        <li className="flex items-start">
                          <svg className="w-5 h-5 text-primary-light mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                          </svg>
                          <span>Integration with CI/CD pipelines for continuous quality checks</span>
                        </li>
                      </>
                    ) : id === 'plugin-2' ? (
                      <>
                        <li className="flex items-start">
                          <svg className="w-5 h-5 text-primary-light mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                          </svg>
                          <span>Interactive architecture diagrams with dependency visualization</span>
                        </li>
                        <li className="flex items-start">
                          <svg className="w-5 h-5 text-primary-light mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                          </svg>
                          <span>Real-time architecture updates as code changes</span>
                        </li>
                        <li className="flex items-start">
                          <svg className="w-5 h-5 text-primary-light mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                          </svg>
                          <span>Identification of cyclic dependencies and architectural weaknesses</span>
                        </li>
                        <li className="flex items-start">
                          <svg className="w-5 h-5 text-primary-light mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                          </svg>
                          <span>Export diagrams in multiple formats for documentation</span>
                        </li>
                      </>
                    ) : (
                      <>
                        <li className="flex items-start">
                          <svg className="w-5 h-5 text-primary-light mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                          </svg>
                          <span>Enterprise-grade security scanning using industry-leading databases</span>
                        </li>
                        <li className="flex items-start">
                          <svg className="w-5 h-5 text-primary-light mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                          </svg>
                          <span>Proactive vulnerability detection with remediation guidance</span>
                        </li>
                        <li className="flex items-start">
                          <svg className="w-5 h-5 text-primary-light mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                          </svg>
                          <span>Compliance checking for OWASP Top 10, GDPR, HIPAA, and more</span>
                        </li>
                        <li className="flex items-start">
                          <svg className="w-5 h-5 text-primary-light mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                          </svg>
                          <span>Weekly security database updates for latest threat protection</span>
                        </li>
                        <li className="flex items-start">
                          <svg className="w-5 h-5 text-primary-light mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                          </svg>
                          <span>Detailed security reports for management and compliance officers</span>
                        </li>
                      </>
                    )}
                  </ul>
                </div>
                
                {/* Screenshots or more info could go here */}
                <div className="card">
                  <h2 className="text-xl font-bold mb-4">How it works</h2>
                  <p className="text-zinc-300 mb-4">
                    {id === 'plugin-1'
                      ? 'The Code Quality Analyzer integrates directly into your TerraFusion workflow, automatically scanning your codebase for quality issues, technical debt, and potential bugs. It uses a combination of static analysis and AI-powered pattern recognition to identify problems and suggest improvements.'
                      : id === 'plugin-2'
                      ? 'The Architecture Visualizer scans your application structure, identifies components and their relationships, and generates interactive diagrams that help you understand and improve your architecture. It continuously updates as your codebase evolves, providing real-time insights into your application structure.'
                      : 'The Advanced Security Scanner performs comprehensive vulnerability assessments on your codebase, identifying potential security issues before they can be exploited. It integrates with your development workflow to catch security problems early in the development process, reducing the cost and risk of remediation.'}
                  </p>
                </div>
              </div>
              
              <div className="col-span-1">
                <div className="card mb-8">
                  <h3 className="text-lg font-semibold mb-4">Information</h3>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-zinc-400">Publisher</p>
                      <p className="text-zinc-300">{plugin.publisher}</p>
                    </div>
                    <div>
                      <p className="text-sm text-zinc-400">Version</p>
                      <p className="text-zinc-300">{plugin.version}</p>
                    </div>
                    <div>
                      <p className="text-sm text-zinc-400">Last Updated</p>
                      <p className="text-zinc-300">{new Date(plugin.updatedAt).toLocaleDateString()}</p>
                    </div>
                    <div>
                      <p className="text-sm text-zinc-400">Category</p>
                      <p className="text-zinc-300">{
                        id === 'plugin-1' 
                          ? 'Code Quality' 
                          : id === 'plugin-2' 
                          ? 'Visualization' 
                          : 'Security'
                      }</p>
                    </div>
                  </div>
                </div>
                
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4">Tags</h3>
                  <div className="flex flex-wrap gap-2">
                    {plugin.tags?.map((tag) => (
                      <span
                        key={tag}
                        className="bg-slate-700 text-zinc-300 px-2 py-1 rounded text-xs"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'docs' && (
          <div className="card">
            <h2 className="text-xl font-bold mb-4">Documentation</h2>
            <p className="text-zinc-300 mb-6">
              Comprehensive documentation for {plugin.name} is available to help you get the most out of this plugin.
            </p>
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-2">Installation</h3>
                <p className="text-zinc-300 mb-3">
                  After purchasing this plugin, installation is simple:
                </p>
                <ol className="list-decimal list-inside space-y-2 text-zinc-300 pl-4">
                  <li>Go to your TerraFusion dashboard</li>
                  <li>Navigate to Plugins &gt; Installed Plugins</li>
                  <li>Click "Activate" next to {plugin.name}</li>
                  <li>Follow the on-screen instructions to complete setup</li>
                </ol>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold mb-2">Configuration</h3>
                <p className="text-zinc-300">
                  Configure the plugin through the Settings panel after installation. Detailed configuration options are available in the full documentation.
                </p>
              </div>
              
              <div className="pt-4">
                <Link to="#" className="btn btn-secondary">
                  View Full Documentation
                </Link>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'support' && (
          <div className="card">
            <h2 className="text-xl font-bold mb-4">Support</h2>
            <p className="text-zinc-300 mb-6">
              If you have any questions or issues with {plugin.name}, our support team is here to help.
            </p>
            
            <div className="space-y-8">
              <div>
                <h3 className="text-lg font-semibold mb-3">Frequently Asked Questions</h3>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium text-zinc-200">How do I get started with {plugin.name}?</h4>
                    <p className="text-zinc-400">
                      After installation, you can access the plugin from your TerraFusion dashboard. Check the documentation for detailed setup instructions.
                    </p>
                  </div>
                  <div>
                    <h4 className="font-medium text-zinc-200">Can I use this plugin with my existing workflows?</h4>
                    <p className="text-zinc-400">
                      Yes, {plugin.name} is designed to integrate seamlessly with your existing TerraFusion workflows.
                    </p>
                  </div>
                  <div>
                    <h4 className="font-medium text-zinc-200">Is there a limit to how many projects I can analyze?</h4>
                    <p className="text-zinc-400">
                      {plugin.pricing.type === 'free' 
                        ? 'The free version allows up to 3 projects. For unlimited projects, consider upgrading to the Pro version.' 
                        : 'Your subscription allows unlimited projects within reasonable usage limits.'}
                    </p>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold mb-3">Contact Support</h3>
                <p className="text-zinc-300 mb-4">
                  Need additional help? Contact our support team:
                </p>
                <div className="space-y-3">
                  <a 
                    href="#" 
                    className="flex items-center text-primary-light hover:text-primary"
                  >
                    <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                      <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                    </svg>
                    support@terrafusion.io
                  </a>
                  <a 
                    href="#" 
                    className="flex items-center text-primary-light hover:text-primary"
                  >
                    <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                    </svg>
                    Live Chat
                  </a>
                  <a 
                    href="#" 
                    className="flex items-center text-primary-light hover:text-primary"
                  >
                    <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M2 5a2 2 0 012-2h8a2 2 0 012 2v10a2 2 0 002 2H4a2 2 0 01-2-2V5zm3 1h6v4H5V6zm6 6H5v2h6v-2z" clipRule="evenodd" />
                      <path d="M15 7h1a2 2 0 012 2v5.5a1.5 1.5 0 01-3 0V7z" />
                    </svg>
                    Submit a Ticket
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PluginDetails;