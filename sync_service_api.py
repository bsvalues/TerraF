"""
Enhanced SyncService API

This module provides a FastAPI application exposing comprehensive SyncService endpoints
for data synchronization, monitoring, configuration, and advanced features.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta

# Import the SyncService
from sync_service import SyncService, ChangeType

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
    version="2.0.0"
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

# Define enum for sync types
class SyncType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    SELECTIVE = "selective"
    DIFFERENTIAL = "differential"

# Define request models
class SelectiveSyncRequest(BaseModel):
    """Request model for selective sync operations."""
    tables: List[str] = Field(..., description="List of table names to sync")
    filter_conditions: Dict[str, Any] = Field(default={}, description="Optional filter conditions for each table")
    
    class Config:
        schema_extra = {
            "example": {
                "tables": ["properties", "valuations"],
                "filter_conditions": {
                    "properties": "county_id = 101",
                    "valuations": "valuation_date > '2025-01-01'"
                }
            }
        }

class MappingConfigRequest(BaseModel):
    """Request model for updating field mapping configurations."""
    source_table: str
    target_table: str
    field_mappings: Dict[str, str]
    transformations: Dict[str, Dict[str, Any]] = Field(default={})
    
    class Config:
        schema_extra = {
            "example": {
                "source_table": "pacs_properties",
                "target_table": "cama_properties",
                "field_mappings": {
                    "property_id": "property_id",
                    "owner_name": "ownership.primary_owner"
                },
                "transformations": {
                    "address": {
                        "type": "combine",
                        "source_fields": ["address_line1", "city", "state", "zip"],
                        "format": "{0}, {1}, {2} {3}"
                    }
                }
            }
        }

class ValidationRuleRequest(BaseModel):
    """Request model for updating validation rules."""
    table: str
    field: str
    rule_type: str
    rule_config: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "table": "cama_properties",
                "field": "valuation.total",
                "rule_type": "range_check",
                "rule_config": {
                    "min_value": 0,
                    "max_value": 10000000,
                    "error_message": "Property valuation must be between $0 and $10M"
                }
            }
        }

class ScheduleRequest(BaseModel):
    """Request model for scheduling sync operations."""
    sync_type: SyncType
    frequency: str = Field(..., description="Cron expression or simple frequency like '1d', '4h'")
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    tables: Optional[List[str]] = Field(default=None)
    
    class Config:
        schema_extra = {
            "example": {
                "sync_type": "incremental",
                "frequency": "0 */4 * * *",  # Every 4 hours
                "start_time": "2025-04-25T00:00:00Z",
                "end_time": "2025-05-25T00:00:00Z",
                "tables": ["properties", "valuations"]
            }
        }

# Define response models for API
class SyncResponse(BaseModel):
    """Response model for sync operations."""
    success: bool
    records_processed: int
    records_succeeded: int
    records_failed: int
    error_details: List[Dict[str, Any]] = []
    warnings: List[str] = []
    start_time: str
    end_time: str
    duration_seconds: float
    sync_id: Optional[str] = None

class DetailedSyncResponse(SyncResponse):
    """Extended response model with detailed information."""
    tables_processed: Dict[str, int] = {}
    performance_metrics: Dict[str, Any] = {}
    data_quality_metrics: Dict[str, Any] = {}

class StatusResponse(BaseModel):
    """Response model for status endpoint."""
    last_sync_time: Optional[str] = None
    sync_history: List[Dict[str, Any]] = []
    active: bool
    version: str
    scheduled_syncs: List[Dict[str, Any]] = []
    
class HealthResponse(BaseModel):
    """Response model for health endpoint."""
    status: str
    timestamp: str
    version: str
    components: Dict[str, Dict[str, Any]]

class SchemaComparisonResponse(BaseModel):
    """Response model for schema comparison endpoint."""
    comparison_results: Dict[str, Any]
    table_counts: Dict[str, int]
    conversion_complexity: Dict[str, int]
    timestamp: str

class MappingConfigResponse(BaseModel):
    """Response model for field mapping configuration."""
    mapping_id: str
    source_table: str
    target_table: str
    field_mappings: Dict[str, str]
    transformations: Dict[str, Dict[str, Any]] = {}
    created_at: str
    updated_at: str

class ValidationRuleResponse(BaseModel):
    """Response model for validation rules."""
    rule_id: str
    table: str
    field: str
    rule_type: str
    rule_config: Dict[str, Any]
    created_at: str
    updated_at: str

class ConflictResolutionResponse(BaseModel):
    """Response model for conflict resolution."""
    conflict_id: str
    table: str
    record_id: str
    conflict_type: str
    resolution: str
    details: Dict[str, Any]
    timestamp: str

class ScheduleResponse(BaseModel):
    """Response model for scheduled sync operations."""
    schedule_id: str
    sync_type: str
    frequency: str
    next_execution: str
    tables: Optional[List[str]] = None
    status: str

class StatisticsResponse(BaseModel):
    """Response model for sync statistics."""
    total_syncs: int
    successful_syncs: int
    failed_syncs: int
    total_records_processed: int
    average_duration: float
    last_24h: Dict[str, Any]
    last_7d: Dict[str, Any]
    last_30d: Dict[str, Any]

class AuditLogResponse(BaseModel):
    """Response model for audit log entries."""
    total_entries: int
    entries: List[Dict[str, Any]]

# Background task for sync operations
def background_sync_task(sync_type: SyncType, sync_service: SyncService, tables: List[str] = None):
    """Background task to run sync operations asynchronously."""
    logger.info(f"Starting background {sync_type.value} sync")
    
    try:
        if sync_type == SyncType.FULL:
            result = sync_service.full_sync()
        elif sync_type == SyncType.INCREMENTAL:
            result = sync_service.incremental_sync()
        elif sync_type == SyncType.SELECTIVE and tables:
            result = sync_service.selective_sync(tables)
        else:
            logger.error(f"Unsupported sync type: {sync_type}")
            return
        
        logger.info(f"Background {sync_type.value} sync completed: {result['success']}")
    except Exception as e:
        logger.error(f"Background {sync_type.value} sync failed: {str(e)}")

# API Endpoints
@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Health check endpoint."""
    logger.info("Health check requested")
    
    # In a real implementation, we would actually check component status
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "components": {
            "api": {"status": "ok"},
            "database": {"status": "ok"},
            "source_connection": {"status": "ok"},
            "target_connection": {"status": "ok"},
            "change_detector": {"status": "ok"},
            "transformer": {"status": "ok"},
            "validator": {"status": "ok"},
            "orchestrator": {"status": "ok"}
        }
    }

# Sync operations
@app.post("/sync/full", response_model=SyncResponse, tags=["Sync Operations"])
def full_sync(
    background_tasks: BackgroundTasks,
    async_mode: bool = Query(False, description="Run sync in background"),
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Perform a full sync from source to target system.
    
    - When async_mode=False (default): Executes synchronously and returns when complete
    - When async_mode=True: Starts sync in the background and returns immediately
    """
    logger.info(f"Full sync requested via API (async_mode={async_mode})")
    
    if async_mode:
        background_tasks.add_task(background_sync_task, SyncType.FULL, sync_service)
        return {
            "success": True,
            "records_processed": 0,
            "records_succeeded": 0,
            "records_failed": 0,
            "error_details": [],
            "warnings": ["Sync started in background. Check status endpoint for progress."],
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": 0,
            "sync_id": f"bg-full-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
    
    try:
        result = sync_service.full_sync()
        return result
    except Exception as e:
        logger.error(f"Full sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync/incremental", response_model=SyncResponse, tags=["Sync Operations"])
def incremental_sync(
    background_tasks: BackgroundTasks,
    async_mode: bool = Query(False, description="Run sync in background"),
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Perform an incremental sync from source to target system.
    
    - When async_mode=False (default): Executes synchronously and returns when complete
    - When async_mode=True: Starts sync in the background and returns immediately
    """
    logger.info(f"Incremental sync requested via API (async_mode={async_mode})")
    
    if async_mode:
        background_tasks.add_task(background_sync_task, SyncType.INCREMENTAL, sync_service)
        return {
            "success": True,
            "records_processed": 0,
            "records_succeeded": 0,
            "records_failed": 0,
            "error_details": [],
            "warnings": ["Sync started in background. Check status endpoint for progress."],
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": 0,
            "sync_id": f"bg-incr-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
    
    try:
        result = sync_service.incremental_sync()
        return result
    except Exception as e:
        logger.error(f"Incremental sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync/selective", response_model=SyncResponse, tags=["Sync Operations"])
def selective_sync(
    request: SelectiveSyncRequest,
    background_tasks: BackgroundTasks,
    async_mode: bool = Query(False, description="Run sync in background"),
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Perform a selective sync for specified tables and conditions.
    
    This endpoint allows fine-grained control over which tables and records are synchronized.
    """
    logger.info(f"Selective sync requested for tables: {request.tables}")
    
    if async_mode:
        background_tasks.add_task(background_sync_task, SyncType.SELECTIVE, sync_service, request.tables)
        return {
            "success": True,
            "records_processed": 0,
            "records_succeeded": 0,
            "records_failed": 0,
            "error_details": [],
            "warnings": ["Sync started in background. Check status endpoint for progress."],
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": 0,
            "sync_id": f"bg-sel-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
    
    try:
        # In a real implementation, we would pass the filter conditions as well
        result = sync_service.selective_sync(request.tables)
        return result
    except Exception as e:
        logger.error(f"Selective sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sync/status", response_model=StatusResponse, tags=["Sync Operations"])
def sync_status(sync_service: SyncService = Depends(get_sync_service)):
    """Get sync status and history."""
    logger.info("Sync status requested via API")
    return sync_service.get_sync_status()

@app.get("/sync/{sync_id}", response_model=DetailedSyncResponse, tags=["Sync Operations"])
def get_sync_details(
    sync_id: str = Path(..., description="ID of the sync operation"),
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Get detailed information about a specific sync operation.
    """
    logger.info(f"Details requested for sync: {sync_id}")
    try:
        # In a real implementation, we would have a method to get details by ID
        # For now, we'll return a mock response
        return {
            "success": True,
            "records_processed": 150,
            "records_succeeded": 145,
            "records_failed": 5,
            "error_details": [
                {"table": "valuations", "record_id": "1234", "error": "Validation failed: total value cannot be negative"}
            ],
            "warnings": ["5 records failed validation"],
            "start_time": (datetime.now() - timedelta(minutes=5)).isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": 300,
            "sync_id": sync_id,
            "tables_processed": {"properties": 100, "valuations": 50},
            "performance_metrics": {
                "avg_record_processing_time_ms": 15,
                "peak_memory_usage_mb": 120,
                "db_query_time_ms": 450
            },
            "data_quality_metrics": {
                "completeness": 0.98,
                "consistency": 0.96,
                "accuracy": 0.99
            }
        }
    except Exception as e:
        logger.error(f"Error getting sync details: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Sync operation {sync_id} not found")

# Schema and mapping endpoints
@app.get("/schema/compare", response_model=SchemaComparisonResponse, tags=["Schema & Mapping"])
def compare_schemas(sync_service: SyncService = Depends(get_sync_service)):
    """
    Compare schemas between source and target databases.
    
    This identifies tables, fields, and data types that differ between systems.
    """
    logger.info("Schema comparison requested via API")
    try:
        result = sync_service.compare_schemas()
        return result
    except Exception as e:
        logger.error(f"Schema comparison failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mapping/config", response_model=List[MappingConfigResponse], tags=["Schema & Mapping"])
def get_mapping_configs(
    source_table: Optional[str] = Query(None, description="Filter by source table name"),
    target_table: Optional[str] = Query(None, description="Filter by target table name"),
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Get all field mapping configurations.
    
    Optionally filter by source or target table name.
    """
    logger.info("Mapping configurations requested via API")
    try:
        # In a real implementation, we would have a method to list configs with filters
        # For now, we'll return a mock response
        configs = [
            {
                "mapping_id": "map-001",
                "source_table": "pacs_properties",
                "target_table": "cama_properties",
                "field_mappings": {
                    "property_id": "property_id",
                    "owner_name": "ownership.primary_owner",
                    "address": "location.address_line1",
                    "land_value": "valuation.land",
                    "improvement_value": "valuation.improvements",
                    "total_value": "valuation.total"
                },
                "transformations": {},
                "created_at": "2025-04-20T10:00:00Z",
                "updated_at": "2025-04-23T15:30:00Z"
            }
        ]
        
        # Apply filters if provided
        if source_table:
            configs = [c for c in configs if c["source_table"] == source_table]
        if target_table:
            configs = [c for c in configs if c["target_table"] == target_table]
            
        return configs
    except Exception as e:
        logger.error(f"Error retrieving mapping configs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mapping/config", response_model=MappingConfigResponse, tags=["Schema & Mapping"])
def create_mapping_config(
    request: MappingConfigRequest,
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Create a new field mapping configuration.
    """
    logger.info(f"Creating mapping config for {request.source_table} -> {request.target_table}")
    try:
        # In a real implementation, we would have a method to create a mapping config
        # For now, we'll return a mock response
        return {
            "mapping_id": f"map-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "source_table": request.source_table,
            "target_table": request.target_table,
            "field_mappings": request.field_mappings,
            "transformations": request.transformations,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating mapping config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Validation rules endpoints
@app.get("/validation/rules", response_model=List[ValidationRuleResponse], tags=["Validation"])
def get_validation_rules(
    table: Optional[str] = Query(None, description="Filter by table name"),
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Get all validation rules.
    
    Optionally filter by table name.
    """
    logger.info("Validation rules requested via API")
    try:
        # In a real implementation, we would have a method to list rules with filters
        # For now, we'll return a mock response
        rules = [
            {
                "rule_id": "rule-001",
                "table": "cama_properties",
                "field": "valuation.total",
                "rule_type": "range_check",
                "rule_config": {
                    "min_value": 0,
                    "max_value": 10000000,
                    "error_message": "Property valuation must be between $0 and $10M"
                },
                "created_at": "2025-04-20T10:00:00Z",
                "updated_at": "2025-04-20T10:00:00Z"
            }
        ]
        
        # Apply filter if provided
        if table:
            rules = [r for r in rules if r["table"] == table]
            
        return rules
    except Exception as e:
        logger.error(f"Error retrieving validation rules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validation/rules", response_model=ValidationRuleResponse, tags=["Validation"])
def create_validation_rule(
    request: ValidationRuleRequest,
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Create a new validation rule.
    """
    logger.info(f"Creating validation rule for {request.table}.{request.field}")
    try:
        # In a real implementation, we would have a method to create a validation rule
        # For now, we'll return a mock response
        return {
            "rule_id": f"rule-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "table": request.table,
            "field": request.field,
            "rule_type": request.rule_type,
            "rule_config": request.rule_config,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating validation rule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Monitoring and statistics endpoints
@app.get("/stats", response_model=StatisticsResponse, tags=["Monitoring"])
def get_sync_statistics(
    period: str = Query("all", description="Time period for stats: all, 24h, 7d, 30d"),
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Get statistics about sync operations.
    """
    logger.info(f"Sync statistics requested for period: {period}")
    try:
        # In a real implementation, we would calculate actual statistics
        # For now, we'll return a mock response
        return {
            "total_syncs": 152,
            "successful_syncs": 145,
            "failed_syncs": 7,
            "total_records_processed": 250000,
            "average_duration": 420.5,
            "last_24h": {
                "syncs": 4,
                "success_rate": 1.0,
                "records_processed": 2500,
                "average_duration": 310.2
            },
            "last_7d": {
                "syncs": 28,
                "success_rate": 0.96,
                "records_processed": 18000,
                "average_duration": 375.8
            },
            "last_30d": {
                "syncs": 120,
                "success_rate": 0.95,
                "records_processed": 75000,
                "average_duration": 405.3
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving sync statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audit/logs", response_model=AuditLogResponse, tags=["Monitoring"])
def get_audit_logs(
    start_date: Optional[datetime] = Query(None, description="Start date for log entries"),
    end_date: Optional[datetime] = Query(None, description="End date for log entries"),
    operation_type: Optional[str] = Query(None, description="Filter by operation type"),
    limit: int = Query(100, description="Maximum number of entries to return"),
    offset: int = Query(0, description="Offset for pagination"),
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Get audit logs for sync operations.
    """
    logger.info("Audit logs requested via API")
    try:
        # In a real implementation, we would retrieve actual audit logs
        # For now, we'll return a mock response
        return {
            "total_entries": 1500,
            "entries": [
                {
                    "id": "log-001",
                    "timestamp": "2025-04-24T10:15:30Z",
                    "operation": "FULL_SYNC",
                    "user": "api_user",
                    "status": "SUCCESS",
                    "details": {
                        "records_processed": 1500,
                        "duration_seconds": 450
                    }
                },
                {
                    "id": "log-002",
                    "timestamp": "2025-04-23T08:30:15Z",
                    "operation": "INCREMENTAL_SYNC",
                    "user": "scheduler",
                    "status": "SUCCESS",
                    "details": {
                        "records_processed": 150,
                        "duration_seconds": 45
                    }
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Schedule endpoints
@app.post("/schedule", response_model=ScheduleResponse, tags=["Scheduling"])
def create_schedule(
    request: ScheduleRequest,
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Create a new scheduled sync operation.
    """
    logger.info(f"Creating schedule for {request.sync_type} sync with frequency {request.frequency}")
    try:
        # In a real implementation, we would create an actual schedule
        # For now, we'll return a mock response
        next_execution = datetime.now() + timedelta(hours=1)
        return {
            "schedule_id": f"sched-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "sync_type": request.sync_type,
            "frequency": request.frequency,
            "next_execution": next_execution.isoformat(),
            "tables": request.tables,
            "status": "active"
        }
    except Exception as e:
        logger.error(f"Error creating schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schedule", response_model=List[ScheduleResponse], tags=["Scheduling"])
def get_schedules(
    sync_type: Optional[SyncType] = Query(None, description="Filter by sync type"),
    status: Optional[str] = Query(None, description="Filter by status (active, paused, completed)"),
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Get all scheduled sync operations.
    """
    logger.info("Schedules requested via API")
    try:
        # In a real implementation, we would retrieve actual schedules
        # For now, we'll return a mock response
        schedules = [
            {
                "schedule_id": "sched-001",
                "sync_type": "incremental",
                "frequency": "0 */4 * * *",  # Every 4 hours
                "next_execution": (datetime.now() + timedelta(hours=2)).isoformat(),
                "tables": None,
                "status": "active"
            },
            {
                "schedule_id": "sched-002",
                "sync_type": "full",
                "frequency": "0 0 * * 0",  # Weekly on Sunday at midnight
                "next_execution": (datetime.now() + timedelta(days=3)).isoformat(),
                "tables": None,
                "status": "active"
            }
        ]
        
        # Apply filters if provided
        if sync_type:
            schedules = [s for s in schedules if s["sync_type"] == sync_type]
        if status:
            schedules = [s for s in schedules if s["status"] == status]
            
        return schedules
    except Exception as e:
        logger.error(f"Error retrieving schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# For running the API directly
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5001))
    uvicorn.run(app, host="0.0.0.0", port=port)