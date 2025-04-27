/**
 * Main API routes
 */
import { Router } from 'express';

const router = Router();

/**
 * @route   GET /api/status
 * @desc    Get API status information
 * @access  Public
 */
router.get('/status', (req, res) => {
  res.json({
    success: true,
    data: {
      service: 'TerraFusion API',
      status: 'operational',
      version: process.env.npm_package_version || '0.1.0',
      timestamp: new Date()
    },
    timestamp: new Date()
  });
});

export default router;