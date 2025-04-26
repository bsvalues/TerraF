import { Link } from 'react-router-dom';

interface PluginCardProps {
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

const PluginCard = ({
  id,
  name,
  description,
  version,
  publisher,
  pricing,
  tags = [],
}: PluginCardProps) => {
  // Helper to format price
  const formatPrice = (price?: number, currency?: string) => {
    if (price === undefined || currency === undefined) {
      return 'Free';
    }
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(price);
  };
  
  // Helper to determine badge color based on pricing type
  const getPricingBadgeColor = (pricingType: string) => {
    switch (pricingType) {
      case 'free':
        return 'bg-emerald-800 text-emerald-100';
      case 'paid':
        return 'bg-blue-800 text-blue-100';
      case 'subscription':
        return 'bg-purple-800 text-purple-100';
      default:
        return 'bg-gray-800 text-gray-100';
    }
  };
  
  return (
    <div className="card transition-all hover:shadow-xl hover:scale-[1.02]">
      <div className="flex flex-col h-full">
        <div className="flex justify-between items-start mb-3">
          <div>
            <h3 className="text-lg font-semibold mb-1">{name}</h3>
            <p className="text-sm text-zinc-400">by {publisher}</p>
          </div>
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${getPricingBadgeColor(pricing.type)}`}>
            {pricing.type === 'free' ? 'Free' : pricing.type === 'paid' ? 'Paid' : 'Subscription'}
          </div>
        </div>
        
        <p className="text-sm text-zinc-300 mb-4 flex-grow">{description}</p>
        
        <div className="mt-auto">
          {/* Tags */}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="bg-slate-700 text-zinc-300 px-2 py-1 rounded text-xs"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
          
          <div className="flex justify-between items-center">
            <div>
              <p className="text-sm text-zinc-400">Version {version}</p>
              {pricing.type !== 'free' && (
                <p className="text-sm font-medium">
                  {formatPrice(pricing.price, pricing.currency)}
                  {pricing.type === 'subscription' && '/mo'}
                </p>
              )}
            </div>
            
            <Link
              to={`/plugins/${id}`}
              className="btn btn-primary text-sm"
            >
              View Details
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PluginCard;