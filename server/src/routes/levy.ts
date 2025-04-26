/**
 * Levy API Routes
 * 
 * This file defines API routes for the levy calculation proof-of-concept.
 */

import express from 'express';

const router = express.Router();

/**
 * Calculate property levy
 * 
 * This is a proof-of-concept endpoint that returns mock levy data for demonstration purposes.
 * In a real implementation, this would connect to a database or service to calculate actual levies.
 */
router.get('/levy', (req, res) => {
  const propertyId = req.query.propertyId || '123';
  
  // Generate a deterministic but seemingly random levy amount based on property ID
  // This ensures the same property ID always returns the same levy amount
  const baseAmount = 500; // Base amount for all properties
  
  // Use a simple hash function on the property ID to get a pseudo-random modifier
  let modifier = 0;
  for (let i = 0; i < String(propertyId).length; i++) {
    modifier += String(propertyId).charCodeAt(i);
  }
  
  const amount = baseAmount + (modifier % 1000); // Add up to $1000 based on property ID
  
  // Simulate a short delay to mimic database or service call
  setTimeout(() => {
    res.json({
      propertyId,
      amount,
      currency: 'USD',
      calculatedAt: new Date().toISOString(),
      dueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days from now
      status: 'pending'
    });
  }, 500); // 500ms delay
});

export default router;