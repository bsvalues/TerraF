/**
 * Authentication Middleware
 * 
 * Handles JWT validation and user authentication.
 */

import { Request, Response, NextFunction } from 'express';
import { AUTH } from '../../../shared/config';

// Interface for authenticated request
export interface AuthenticatedRequest extends Request {
  user?: {
    id: string;
    email: string;
    role: string;
  };
}

/**
 * Middleware to verify JWT and attach user to request
 */
export const authMiddleware = (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  // In a real implementation, this would validate the JWT token
  // For now, this is just a placeholder that allows requests through
  
  // Get token from header or cookie
  const token = req.headers.authorization?.split(' ')[1] || 
                req.cookies?.[AUTH.cookieName];
  
  if (!token) {
    // For development purposes, allow unauthenticated requests
    // In production, uncomment the following line:
    // return res.status(401).json({ error: 'Authentication required' });
    
    // For now, attach a demo user
    req.user = {
      id: 'demo-user',
      email: 'demo@terrafusion.example',
      role: 'developer',
    };
    return next();
  }
  
  try {
    // This would validate the token and extract user information
    // For now, just attach a mock user
    req.user = {
      id: 'authenticated-user',
      email: 'user@terrafusion.example',
      role: 'admin',
    };
    next();
  } catch (error) {
    res.status(403).json({ error: 'Invalid or expired token' });
  }
};

/**
 * Middleware to check if user has required role
 */
export const requireRole = (roles: string[]) => {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Authentication required' });
    }
    
    if (!roles.includes(req.user.role)) {
      return res.status(403).json({ 
        error: 'Insufficient permissions',
        required: roles,
        current: req.user.role
      });
    }
    
    next();
  };
};