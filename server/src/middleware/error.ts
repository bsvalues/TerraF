/**
 * Error Handling Middleware
 * 
 * Global error handler for the Express application.
 */

import { Request, Response, NextFunction } from 'express';
import { ENV } from '../../../shared/config';

// Custom error class with status code
export class ApiError extends Error {
  statusCode: number;
  
  constructor(message: string, statusCode: number = 500) {
    super(message);
    this.statusCode = statusCode;
    this.name = this.constructor.name;
    Error.captureStackTrace(this, this.constructor);
  }
}

/**
 * Global error handler middleware
 */
export const errorHandler = (
  err: Error | ApiError, 
  _req: Request, 
  res: Response, 
  _next: NextFunction
) => {
  console.error(`[Error] ${err.message}`);
  
  // Set default status code
  const statusCode = (err as ApiError).statusCode || 500;
  
  // Prepare response
  const response: any = {
    error: {
      message: err.message || 'Internal Server Error',
      status: statusCode
    }
  };
  
  // Add stack trace in development
  if (ENV.isDevelopment && err.stack) {
    response.error.stack = err.stack;
  }
  
  res.status(statusCode).json(response);
};