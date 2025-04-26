import { Link } from 'react-router-dom';

const NotFound = () => {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16">
      <svg
        className="w-24 h-24 text-primary-light mb-8"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      
      <h1 className="text-4xl font-bold mb-4">404</h1>
      <h2 className="text-2xl font-semibold mb-6">Page Not Found</h2>
      
      <p className="text-zinc-400 max-w-md mb-8">
        The page you are looking for might have been removed, had its name changed,
        or is temporarily unavailable.
      </p>
      
      <div className="space-y-4">
        <Link to="/" className="btn btn-primary block">
          Return to Home
        </Link>
        <Link to="/marketplace" className="text-primary-light hover:text-primary">
          Go to Marketplace
        </Link>
      </div>
    </div>
  );
};

export default NotFound;