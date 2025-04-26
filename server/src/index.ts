/**
 * TerraFusion API Server
 * 
 * Main server entry point that configures the Express application
 * and mounts middleware and routes.
 */

import express from 'express';
import path from 'path';
import cors from 'cors';
import morgan from 'morgan';
import cookieParser from 'cookie-parser';
import { ENV, SERVER } from '../../shared/config';

// Import routes
import apiRouter from './routes/api';

// Import middleware
import { errorHandler } from './middleware/error';

// Create Express application
const app = express();

// Configure middleware
app.use(cors({
  origin: ENV.isDevelopment ? '*' : SERVER.allowedOrigins,
  credentials: true,
}));

// Parse JSON request bodies
app.use(express.json());

// Parse URL-encoded request bodies
app.use(express.urlencoded({ extended: true }));

// Parse cookies
app.use(cookieParser());

// Logging middleware
app.use(morgan(ENV.isDevelopment ? 'dev' : 'combined'));

// Static files
app.use('/static', express.static(path.join(__dirname, '../public')));

// Mount routes
app.use(`/api/${SERVER.apiVersion}`, apiRouter);

// Health check endpoint
app.get('/health', (_req, res) => {
  res.status(200).json({ status: 'ok' });
});

// Error handling middleware (must be last)
app.use(errorHandler);

// Start server
const PORT = process.env.PORT || SERVER.port;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Environment: ${ENV.environment}`);
  console.log(`API version: ${SERVER.apiVersion}`);
});

export default app;