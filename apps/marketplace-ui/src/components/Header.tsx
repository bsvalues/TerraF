import { useState } from 'react';
import { Link } from 'react-router-dom';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  return (
    <header className="bg-card shadow-md">
      <div className="container mx-auto px-4 py-3">
        <div className="flex justify-between items-center">
          {/* Logo and Brand */}
          <Link to="/" className="flex items-center space-x-2">
            <svg
              className="w-8 h-8 text-primary"
              viewBox="0 0 24 24"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 2L2 7L12 12L22 7L12 2Z"
                fill="currentColor"
              />
              <path
                d="M2 17L12 22L22 17V7L12 12L2 7V17Z"
                fillOpacity="0.5"
                fill="currentColor"
              />
            </svg>
            <span className="text-xl font-bold">TerraFusion</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            <Link to="/" className="text-zinc-100 hover:text-primary-light">
              Home
            </Link>
            <Link to="/marketplace" className="text-zinc-100 hover:text-primary-light">
              Marketplace
            </Link>
            <Link to="/documentation" className="text-zinc-100 hover:text-primary-light">
              Documentation
            </Link>
            <Link to="/community" className="text-zinc-100 hover:text-primary-light">
              Community
            </Link>
          </nav>

          {/* Desktop User Controls */}
          <div className="hidden md:flex items-center space-x-4">
            <div className="relative">
              <button
                className="flex items-center space-x-2 text-zinc-100 hover:text-primary-light"
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              >
                <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
                  <span className="text-sm font-medium">DU</span>
                </div>
                <span>Demo User</span>
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>

              {isUserMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-card rounded-md shadow-lg py-1 z-10">
                  <Link
                    to="/profile"
                    className="block px-4 py-2 text-sm text-zinc-100 hover:bg-slate-700"
                  >
                    Your Profile
                  </Link>
                  <Link
                    to="/settings"
                    className="block px-4 py-2 text-sm text-zinc-100 hover:bg-slate-700"
                  >
                    Settings
                  </Link>
                  <Link
                    to="/plugins"
                    className="block px-4 py-2 text-sm text-zinc-100 hover:bg-slate-700"
                  >
                    Your Plugins
                  </Link>
                  <div className="border-t border-slate-600 my-1"></div>
                  <button
                    className="block w-full text-left px-4 py-2 text-sm text-zinc-100 hover:bg-slate-700"
                    onClick={() => console.log('Sign out')}
                  >
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden text-zinc-100 hover:text-primary-light"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              {isMenuOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <nav className="md:hidden mt-4 pt-4 border-t border-slate-600">
            <ul className="space-y-4 pb-3">
              <li>
                <Link
                  to="/"
                  className="block text-zinc-100 hover:text-primary-light"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Home
                </Link>
              </li>
              <li>
                <Link
                  to="/marketplace"
                  className="block text-zinc-100 hover:text-primary-light"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Marketplace
                </Link>
              </li>
              <li>
                <Link
                  to="/documentation"
                  className="block text-zinc-100 hover:text-primary-light"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Documentation
                </Link>
              </li>
              <li>
                <Link
                  to="/community"
                  className="block text-zinc-100 hover:text-primary-light"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Community
                </Link>
              </li>
              <li>
                <Link
                  to="/profile"
                  className="block text-zinc-100 hover:text-primary-light"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Your Profile
                </Link>
              </li>
              <li>
                <Link
                  to="/settings"
                  className="block text-zinc-100 hover:text-primary-light"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Settings
                </Link>
              </li>
              <li>
                <button
                  className="text-zinc-100 hover:text-primary-light"
                  onClick={() => console.log('Sign out')}
                >
                  Sign Out
                </button>
              </li>
            </ul>
          </nav>
        )}
      </div>
    </header>
  );
};

export default Header;