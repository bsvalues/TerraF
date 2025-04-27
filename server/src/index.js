/**
 * Main Express server entry point
 */
const express = require('express');
const cors = require('cors');
const morgan = require('morgan');

// Create Express app
const app = express();
const PORT = process.env.PORT || 5001;

// Apply middleware
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

// Import routes
const apiRoutes = require('./routes/api');
const levyRoutes = require('./routes/levy');

// Mount API routes
app.use('/api', apiRoutes);
app.use('/api/v1', levyRoutes);

// Default route
app.get('/', (req, res) => {
  res.json({
    message: 'TerraFusion API',
    version: '0.1.0',
    endpoints: [
      '/api/status',
      '/api/v1/levy'
    ]
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  const statusCode = err.statusCode || 500;
  res.status(statusCode).json({
    success: false,
    error: err.message || 'Internal Server Error',
    timestamp: new Date()
  });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on http://0.0.0.0:${PORT}`);
});

module.exports = app;