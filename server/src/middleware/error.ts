/**
 * Error Handling Middleware
 * 
 * Provides centralized error handling for the Express application.
 */

import { Request, Response, NextFunction } from 'express';
import { ENV } from '../../../shared/config';

/**
 * Custom API Error class
 */
export class ApiError extends Error {
  statusCode: number;
  details?: any;

  constructor(message: string, statusCode: number = 500, details?: any) {
    super(message);
    this.statusCode = statusCode;
    this.details = details;
    this.name = 'ApiError';
  }

  static badRequest(message: string, details?: any) {
    return new ApiError(message, 400, details);
  }

  static unauthorized(message: string = 'Unauthorized', details?: any) {
    return new ApiError(message, 401, details);
  }

  static forbidden(message: string = 'Forbidden', details?: any) {
    return new ApiError(message, 403, details);
  }

  static notFound(message: string = 'Resource not found', details?: any) {
    return new ApiError(message, 404, details);
  }

  static conflict(message: string, details?: any) {
    return new ApiError(message, 409, details);
  }

  static internal(message: string = 'Internal server error', details?: any) {
    return new ApiError(message, 500, details);
  }
}

/**
 * Global error handler middleware
 */
export function errorHandler(
  err: Error | ApiError,
  req: Request,
  res: Response,
  next: NextFunction
) {
  // Log the error
  console.error('[Error]', err);

  // Determine status code and prepare response
  const statusCode = (err as ApiError).statusCode || 500;
  const message = err.message || 'Something went wrong';

  // Prepare error response
  const errorResponse: Record<string, any> = {
    error: {
      message,
      status: statusCode,
    }
  };

  // Add details in development mode or for API errors
  if (ENV.isDevelopment || err instanceof ApiError) {
    if ((err as ApiError).details) {
      errorResponse.error.details = (err as ApiError).details;
    }

    // Include stack trace in development
    if (ENV.isDevelopment) {
      errorResponse.error.stack = err.stack;
    }
  }

  // Send error response
  res.status(statusCode).json(errorResponse);
}

/**
 * 404 handler middleware
 */
export function notFoundHandler(
  req: Request, 
  res: Response
) {
  res.status(404).json({
    error: {
      message: `Not Found - ${req.originalUrl}`,
      status: 404
    }
  });
}