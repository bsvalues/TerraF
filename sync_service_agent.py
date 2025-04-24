"""
SyncService Agent

This module provides an agent for managing and executing data synchronization
between legacy PACS and modern CAMA systems.
"""

import os
import re
import json
import time
import random
import logging
from typing import Dict, List, Any, Optional, Union
import datetime

# Import the simplified agent base
from simple_agent_base import Agent, AgentCategory

# Import the SyncService
from sync_service import SyncService, DetectedChange, TransformedRecord, ValidationResult

class SyncServiceAgent(Agent):
    """
    Agent for managing data synchronization between systems.
    
    This agent handles:
    - Detecting changes in source systems
    - Transforming data between formats
    - Validating data consistency
    - Orchestrating sync processes
    """
    
    def __init__(self, agent_id: str = "sync_service_agent", 
                capabilities: List[str] = None):
        """Initialize the SyncService Agent"""
        if capabilities is None:
            capabilities = [
                "detect_changes",
                "transform_data",
                "validate_data",
                "perform_sync",
                "monitor_sync_status"
            ]
        
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentCategory.DATA_INTEGRATION,
            capabilities=capabilities
        )
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize the SyncService
        self.sync_service = SyncService()
        
    def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task assigned to this agent.
        
        Args:
            task: The task to execute
        
        Returns:
            Dict containing the result of the task execution
        """
        task_type = task.get("type", "unknown")
        result = {"status": "error", "message": f"Unknown task type: {task_type}"}
        
        # Implement task execution logic here
        if task_type == "detect_changes":
            result = self._detect_changes_task(task)
        elif task_type == "transform_data":
            result = self._transform_data_task(task)
        elif task_type == "validate_data":
            result = self._validate_data_task(task)
        elif task_type == "perform_sync":
            result = self._perform_sync_task(task)
        elif task_type == "monitor_sync_status":
            result = self._monitor_sync_status_task(task)
        
        return result
    
    def _detect_changes_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a change detection task"""
        last_sync_time = task.get("last_sync_time")
        
        try:
            # Use the SyncService to detect changes
            changes = self.sync_service.orchestrator.change_detector.detect_changes(last_sync_time)
            
            # Serialize the changes for the response
            serialized_changes = [change.to_dict() for change in changes]
            
            change_counts = {
                "insert": sum(1 for c in changes if c.change_type.value == "insert"),
                "update": sum(1 for c in changes if c.change_type.value == "update"),
                "delete": sum(1 for c in changes if c.change_type.value == "delete"),
                "no_change": sum(1 for c in changes if c.change_type.value == "no_change")
            }
            
            return {
                "status": "success",
                "detected_changes": serialized_changes,
                "change_counts": change_counts,
                "total_changes": len(changes),
                "source_system": "PACS",
                "last_sync_time": last_sync_time,
                "current_time": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error in change detection: {str(e)}")
            return {
                "status": "error",
                "message": f"Change detection failed: {str(e)}",
                "source_system": "PACS",
                "last_sync_time": last_sync_time
            }
    
    def _transform_data_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a data transformation task"""
        # Get change data from the task
        changes_data = task.get("changes", [])
        
        try:
            # Convert serialized changes back to DetectedChange objects
            changes = []
            for change_data in changes_data:
                changes.append(DetectedChange(
                    record_id=change_data.get("record_id"),
                    source_table=change_data.get("source_table"),
                    change_type=change_data.get("change_type"),
                    old_data=change_data.get("old_data"),
                    new_data=change_data.get("new_data"),
                    timestamp=change_data.get("timestamp")
                ))
            
            # Use the SyncService to transform data
            transformed_records = self.sync_service.orchestrator.transformer.transform(changes)
            
            # Serialize the transformed records
            serialized_records = [record.to_dict() for record in transformed_records]
            
            table_counts = {}
            for record in transformed_records:
                table = record.target_table
                if table not in table_counts:
                    table_counts[table] = 0
                table_counts[table] += 1
            
            return {
                "status": "success",
                "transformed_records": serialized_records,
                "total_records": len(transformed_records),
                "table_counts": table_counts,
                "source_tables": list(set(change.source_table for change in changes)),
                "target_tables": list(set(record.target_table for record in transformed_records))
            }
        except Exception as e:
            self.logger.error(f"Error in data transformation: {str(e)}")
            return {
                "status": "error",
                "message": f"Data transformation failed: {str(e)}",
                "source_tables": list(set(change.get("source_table") for change in changes_data)),
                "changes_count": len(changes_data)
            }
    
    def _validate_data_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a data validation task"""
        # Get transformed record data from the task
        records_data = task.get("records", [])
        
        try:
            # Convert serialized records back to TransformedRecord objects
            records = []
            for record_data in records_data:
                records.append(TransformedRecord(
                    source_id=record_data.get("source_id"),
                    target_id=record_data.get("target_id"),
                    target_table=record_data.get("target_table"),
                    data=record_data.get("data", {}),
                    operation=record_data.get("operation"),
                    metadata=record_data.get("metadata", {})
                ))
            
            # Use the SyncService to validate data
            validation_results = self.sync_service.orchestrator.validator.validate(records)
            
            # Serialize the validation results
            serialized_results = [result.to_dict() for result in validation_results]
            
            # Calculate validation statistics
            valid_count = sum(1 for result in validation_results if result.is_valid)
            invalid_count = sum(1 for result in validation_results if not result.is_valid)
            warning_count = sum(len(result.warnings) for result in validation_results)
            
            return {
                "status": "success",
                "validation_results": serialized_results,
                "total_records": len(validation_results),
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "warning_count": warning_count,
                "validation_rate": 100 * valid_count / len(validation_results) if validation_results else 0
            }
        except Exception as e:
            self.logger.error(f"Error in data validation: {str(e)}")
            return {
                "status": "error",
                "message": f"Data validation failed: {str(e)}",
                "records_count": len(records_data)
            }
    
    def _perform_sync_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a sync task"""
        sync_type = task.get("sync_type", "incremental")
        
        try:
            # Perform the sync operation
            if sync_type == "full":
                result = self.sync_service.full_sync()
            else:
                result = self.sync_service.incremental_sync()
            
            return {
                "status": "success",
                "sync_result": result,
                "sync_type": sync_type,
                "timestamp": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error performing {sync_type} sync: {str(e)}")
            return {
                "status": "error",
                "message": f"{sync_type.capitalize()} sync failed: {str(e)}",
                "sync_type": sync_type,
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def _monitor_sync_status_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a sync status monitoring task"""
        try:
            # Get sync status from the service
            status = self.sync_service.get_sync_status()
            
            return {
                "status": "success",
                "sync_status": status,
                "query_time": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error monitoring sync status: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to get sync status: {str(e)}",
                "query_time": datetime.datetime.now().isoformat()
            }