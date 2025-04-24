"""
SyncService API

This module provides a FastAPI application exposing the SyncService endpoints.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

# Import the SyncService
from sync_service import SyncService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title="SyncService API",
    description="API for syncing data between PACS and CAMA systems",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a singleton instance of SyncService
sync_service_instance = None

def get_sync_service() -> SyncService:
    """Get the singleton SyncService instance."""
    global sync_service_instance
    if sync_service_instance is None:
        logger.info("Initializing SyncService")
        sync_service_instance = SyncService()
    return sync_service_instance

# Define response models for API
class SyncResponse(BaseModel):
    """Response model for sync operations."""
    success: bool
    records_processed: int
    records_succeeded: int
    records_failed: int
    error_details: list = []
    warnings: list = []
    start_time: str
    end_time: str
    duration_seconds: float

class StatusResponse(BaseModel):
    """Response model for status endpoint."""
    last_sync_time: Optional[str] = None
    sync_history: list = []
    active: bool
    version: str

class HealthResponse(BaseModel):
    """Response model for health endpoint."""
    status: str
    timestamp: str
    version: str
    components: Dict[str, Dict[str, Any]]

# API Endpoints
@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    logger.info("Health check requested")
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "api": {"status": "ok"},
            "database": {"status": "ok"}  # In real app, would check DB connectivity
        }
    }

@app.post("/sync/full", response_model=SyncResponse)
def full_sync(sync_service: SyncService = Depends(get_sync_service)):
    """Perform a full sync."""
    logger.info("Full sync requested via API")
    try:
        result = sync_service.full_sync()
        return result
    except Exception as e:
        logger.error(f"Full sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync/incremental", response_model=SyncResponse)
def incremental_sync(sync_service: SyncService = Depends(get_sync_service)):
    """Perform an incremental sync."""
    logger.info("Incremental sync requested via API")
    try:
        result = sync_service.incremental_sync()
        return result
    except Exception as e:
        logger.error(f"Incremental sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sync/status", response_model=StatusResponse)
def sync_status(sync_service: SyncService = Depends(get_sync_service)):
    """Get sync status and history."""
    logger.info("Sync status requested via API")
    return sync_service.get_sync_status()


# For running the API directly
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5001))
    uvicorn.run(app, host="0.0.0.0", port=port)