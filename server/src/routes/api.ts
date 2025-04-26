/**
 * API Router
 * 
 * Main API router that mounts all domain-specific routers.
 */

import { Router } from 'express';
import { FEATURES } from '../../../shared/config';

// Create router
const apiRouter = Router();

// GET /api/v1 - API information
apiRouter.get('/', (_req, res) => {
  res.json({
    name: 'TerraFusion API',
    version: 'v1',
    documentation: '/api/v1/docs',
  });
});

// Mount domain-specific routers
// These will be implemented as we migrate each domain app

// TODO: Uncomment as domains are migrated
// apiRouter.use('/levy', levyRouter);
// apiRouter.use('/gis', gisRouter);
// apiRouter.use('/flow', flowRouter);

// Marketplace router (conditionally mounted based on feature flag)
if (FEATURES.enableMarketplace) {
  // We'll implement and import this later
  // apiRouter.use('/market', marketRouter);
  
  // For now, just return a placeholder response
  apiRouter.get('/market/plugins', (_req, res) => {
    res.json([
      { 
        id: 'example', 
        name: 'Example Plugin',
        description: 'This is a placeholder plugin for demonstration',
        version: '0.1.0',
        publisher: 'TerraFusion'
      }
    ]);
  });
}

export default apiRouter;