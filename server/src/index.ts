/**
 * TerraFusion Monolithic Server
 * 
 * Main entry point for the TerraFusion backend server that consolidates
 * all domain-specific APIs into a single process.
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { json, urlencoded } from 'body-parser';
import morgan from 'morgan';

// Import routers
import apiRouter from './routes/api';
import { healthRouter } from './routes/health';

// Import middleware
import { authMiddleware } from './middleware/auth';
import { errorHandler } from './middleware/error';

// Create Express application
const app = express();

// Apply global middleware
app.use(helmet()); // Security headers
app.use(cors()); // CORS support
app.use(json()); // Parse JSON bodies
app.use(urlencoded({ extended: true })); // Parse URL-encoded bodies
app.use(morgan('dev')); // Logging

// Mount routes
app.use('/health', healthRouter);
app.use('/api/v1', authMiddleware, apiRouter);

// Apply error handling middleware
app.use(errorHandler);

// Start server
const port = process.env.PORT || 4000;
app.listen(port, () => {
  console.log(`TerraFusion server listening on port ${port}`);
  console.log(`Health check available at http://localhost:${port}/health`);
  console.log(`API available at http://localhost:${port}/api/v1`);
});