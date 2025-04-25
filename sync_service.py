"""
SyncService Module for TerraFusion Platform

This module provides a comprehensive data synchronization service between
legacy PACS (Property Assessment Computer Systems) and modern CAMA (Computer-Aided
Mass Appraisal) systems. It includes components for detecting changes,
transforming data, validating transformations, and orchestrating the entire
sync process with self-healing capabilities.
"""

import os
import re
import json
import time
import random
import logging
import datetime
import threading
import queue
import multiprocessing
import concurrent.futures
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Union, Callable, TypedDict, TypeVar, Generic, Set, NamedTuple, Iterator
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field

# For demo purposes, we'll simulate database connections
class DatabaseConnection:
    """Simulated database connection"""
    def __init__(self, connection_string: str, db_type: str):
        self.connection_string = connection_string
        self.db_type = db_type
        self.logger = logging.getLogger(f"{self.__class__.__name__}-{db_type}")
        self.logger.info(f"Initialized connection to {db_type} database")
        
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Simulate executing a query against the database"""
        self.logger.info(f"Executing query: {query}")
        if params:
            self.logger.info(f"With parameters: {params}")
            
        # Simulate query execution delay
        time.sleep(0.1)
        
        # Return mock data based on query
        if "SELECT" in query.upper() and "FROM change_log" in query:
            return self._get_mock_change_log_data()
        elif "SELECT" in query.upper() and "FROM pacs_properties" in query:
            return self._get_mock_pacs_data()
        elif "SELECT" in query.upper() and "FROM cama_properties" in query:
            return self._get_mock_cama_data()
        elif "INSERT" in query.upper() or "UPDATE" in query.upper():
            # Simulate write operation
            return [{"affected_rows": 1, "status": "success"}]
        else:
            # Default mock data
            return [{"id": 1, "name": "Sample Data", "value": 123.45}]
    
    def _get_mock_change_log_data(self) -> List[Dict[str, Any]]:
        """Return mock change log data"""
        return [
            {
                "id": 1,
                "table_name": "properties",
                "record_id": 101,
                "operation": "UPDATE",
                "timestamp": "2025-04-24T10:15:30Z",
                "user_id": "admin"
            },
            {
                "id": 2,
                "table_name": "valuations",
                "record_id": 204,
                "operation": "INSERT",
                "timestamp": "2025-04-24T10:18:45Z",
                "user_id": "analyst"
            },
            {
                "id": 3,
                "table_name": "properties",
                "record_id": 156,
                "operation": "UPDATE",
                "timestamp": "2025-04-24T10:22:10Z",
                "user_id": "admin"
            }
        ]
    
    def _get_mock_pacs_data(self) -> List[Dict[str, Any]]:
        """Return mock PACS property data"""
        return [
            {
                "property_id": 101,
                "parcel_number": "12-345-67",
                "owner_name": "John Smith",
                "address": "123 Main St",
                "land_value": 125000,
                "improvement_value": 225000,
                "total_value": 350000,
                "last_updated": "2025-04-20T14:30:00Z"
            },
            {
                "property_id": 156,
                "parcel_number": "23-456-78",
                "owner_name": "Jane Doe",
                "address": "456 Oak Ave",
                "land_value": 180000,
                "improvement_value": 320000,
                "total_value": 500000,
                "last_updated": "2025-04-23T09:15:00Z"
            }
        ]
    
    def _get_mock_cama_data(self) -> List[Dict[str, Any]]:
        """Return mock CAMA property data"""
        return [
            {
                "property_id": "PROP-101",
                "parcel_id": "12-345-67",
                "ownership": {
                    "primary_owner": "John Smith",
                    "ownership_type": "Individual"
                },
                "location": {
                    "address_line1": "123 Main St",
                    "city": "Springfield",
                    "state": "IL",
                    "zip": "62701"
                },
                "valuation": {
                    "land": 125000,
                    "improvements": 225000,
                    "total": 350000,
                    "assessment_date": "2025-01-15"
                },
                "metadata": {
                    "last_sync": "2025-04-21T08:45:00Z",
                    "sync_status": "complete"
                }
            }
        ]


class ChangeType(Enum):
    """Types of changes that can be detected"""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    NO_CHANGE = "no_change"


class DetectedChange:
    """Represents a detected change in the source system"""
    def __init__(
        self, 
        record_id: str, 
        source_table: str, 
        change_type: ChangeType,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ):
        self.record_id = record_id
        self.source_table = source_table
        self.change_type = change_type
        self.old_data = old_data or {}
        self.new_data = new_data or {}
        self.timestamp = timestamp or datetime.datetime.now().isoformat()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "record_id": self.record_id,
            "source_table": self.source_table,
            "change_type": self.change_type.value,
            "old_data": self.old_data,
            "new_data": self.new_data,
            "timestamp": self.timestamp
        }


class TransformedRecord:
    """Represents a transformed record ready for target system"""
    def __init__(
        self,
        source_id: str,
        target_id: Optional[str],
        target_table: str,
        data: Dict[str, Any],
        operation: ChangeType,
        metadata: Dict[str, Any] = None
    ):
        self.source_id = source_id
        self.target_id = target_id
        self.target_table = target_table
        self.data = data
        self.operation = operation
        self.metadata = metadata or {
            "transformed_at": datetime.datetime.now().isoformat(),
            "transformer_version": "1.0.0"
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "target_table": self.target_table,
            "data": self.data,
            "operation": self.operation.value,
            "metadata": self.metadata
        }


class ValidationResult:
    """
    Represents the result of validating a transformed record.
    Enhanced with additional informational messages and validation metrics.
    """
    def __init__(
        self,
        record: TransformedRecord,
        is_valid: bool,
        errors: List[str] = None,
        warnings: List[str] = None,
        info: List[str] = None,
        metrics: Dict[str, Any] = None
    ):
        self.record = record
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.info = info or []  # Informational messages, not errors or warnings
        self.metrics = metrics or {}  # Validation metrics like completion, accuracy
        self.validation_time = datetime.datetime.now().isoformat()
        
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the validation result"""
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "info_count": len(self.info),
            "record_id": self.record.source_id,
            "table": self.record.target_table,
            "validation_time": self.validation_time
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to a dictionary"""
        return {
            "record": self.record.to_dict(),
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "metrics": self.metrics,
            "validation_time": self.validation_time
        }


class SyncResult:
    """
    Represents the result of a sync operation with enhanced performance metrics
    and detailed processing information.
    """
    def __init__(
        self,
        success: bool,
        records_processed: int = 0,
        records_succeeded: int = 0,
        records_failed: int = 0,
        error_details: List[Dict[str, Any]] = None,
        warnings: List[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ):
        self.success = success
        self.records_processed = records_processed
        self.records_succeeded = records_succeeded
        self.records_failed = records_failed
        self.error_details = error_details or []
        self.warnings = warnings or []
        self.start_time = start_time or datetime.datetime.now().isoformat()
        self.end_time = end_time or datetime.datetime.now().isoformat()
        
        # Enhanced attributes for performance optimization
        self.performance_metrics: Dict[str, Any] = {}
        self.tables_processed: Dict[str, int] = {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "success": self.success,
            "records_processed": self.records_processed,
            "records_succeeded": self.records_succeeded,
            "records_failed": self.records_failed,
            "error_details": self.error_details,
            "warnings": self.warnings,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self._calculate_duration()
        }
        
        # Add enhanced information if available
        if self.performance_metrics:
            result["performance_metrics"] = self.performance_metrics
            
        if self.tables_processed:
            result["tables_processed"] = self.tables_processed
            
        return result
        
    def _calculate_duration(self) -> float:
        """Calculate duration in seconds between start and end times"""
        try:
            start = datetime.datetime.fromisoformat(self.start_time)
            end = datetime.datetime.fromisoformat(self.end_time)
            return (end - start).total_seconds()
        except (ValueError, TypeError):
            return 0.0
            
    def get_processing_rate(self) -> float:
        """
        Calculate the processing rate in records per second
        
        Returns:
            Processing rate (records/second)
        """
        duration = self._calculate_duration()
        if duration <= 0 or self.records_processed <= 0:
            return 0.0
        return self.records_processed / duration
    
    def get_success_rate(self) -> float:
        """
        Calculate the success rate as a percentage
        
        Returns:
            Success rate (percentage)
        """
        if self.records_processed <= 0:
            return 0.0
        return (self.records_succeeded / self.records_processed) * 100.0
    
    def add_performance_metrics(self, metrics: Dict[str, Any]) -> None:
        """Add or update performance metrics"""
        if not hasattr(self, 'performance_metrics'):
            self.performance_metrics = {}
        
        # Merge metrics with any existing ones
        for category, values in metrics.items():
            if category in self.performance_metrics:
                if isinstance(values, dict) and isinstance(self.performance_metrics[category], dict):
                    # Merge dictionaries
                    self.performance_metrics[category].update(values)
                else:
                    # Replace value
                    self.performance_metrics[category] = values
            else:
                # Add new category
                self.performance_metrics[category] = values
                
    def add_table_processed(self, table_name: str, count: int = 1) -> None:
        """Record a table being processed with record count"""
        if not hasattr(self, 'tables_processed'):
            self.tables_processed = {}
            
        if table_name in self.tables_processed:
            self.tables_processed[table_name] += count
        else:
            self.tables_processed[table_name] = count


@dataclass
class PerformanceMetrics:
    """Performance metrics for sync operations"""
    operation_id: str = field(default_factory=lambda: f"op-{int(time.time())}")
    operation_type: str = "unknown"
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    records_processed: int = 0
    processing_rate: float = 0.0  # records per second
    batch_sizes: List[int] = field(default_factory=list)
    batch_durations: List[float] = field(default_factory=list)
    thread_counts: Dict[str, int] = field(default_factory=dict)
    memory_usage: Dict[str, float] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        result = {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "start_time": datetime.datetime.fromtimestamp(self.start_time).isoformat(),
            "records_processed": self.records_processed,
            "batch_stats": {
                "total_batches": len(self.batch_sizes),
                "avg_batch_size": sum(self.batch_sizes) / max(1, len(self.batch_sizes)),
                "avg_batch_duration_ms": sum(self.batch_durations) / max(1, len(self.batch_durations)) * 1000,
            },
            "resource_usage": {
                "threads": self.thread_counts,
                "memory_mb": self.memory_usage
            },
            "error_stats": self.error_counts
        }
        
        if self.end_time:
            duration = self.end_time - self.start_time
            result["end_time"] = datetime.datetime.fromtimestamp(self.end_time).isoformat()
            result["duration_seconds"] = duration
            result["processing_rate"] = self.records_processed / max(0.001, duration)
            
        return result
    
    def record_batch(self, size: int, duration_seconds: float) -> None:
        """Record a batch processing operation"""
        self.batch_sizes.append(size)
        self.batch_durations.append(duration_seconds)
        self.records_processed += size
    
    def complete(self) -> None:
        """Mark the operation as complete"""
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        if duration > 0:
            self.processing_rate = self.records_processed / duration


class BatchConfiguration:
    """Configuration for batch processing operations with advanced dynamic sizing"""
    def __init__(
        self, 
        batch_size: int = 100,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
        retry_backoff_factor: float = 1.5,
        max_retry_delay_seconds: float = 30.0,
        dynamic_sizing: bool = True,
        min_batch_size: int = 10,
        max_batch_size: int = 1000,
        target_batch_duration_seconds: float = 2.0,
        prioritize_tables: Dict[str, int] = None,  # Table name -> priority (lower is higher priority)
        adaptive_learning: bool = True,
        workload_specific_sizing: bool = True,
        resource_aware_sizing: bool = True
    ):
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.retry_backoff_factor = retry_backoff_factor
        self.max_retry_delay_seconds = max_retry_delay_seconds
        self.dynamic_sizing = dynamic_sizing
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.target_batch_duration_seconds = target_batch_duration_seconds
        self.prioritize_tables = prioritize_tables or {}
        self.adaptive_learning = adaptive_learning
        self.workload_specific_sizing = workload_specific_sizing
        self.resource_aware_sizing = resource_aware_sizing
        
        # Historical performance tracking for adaptive learning
        self.performance_history = {
            "batch_sizes": [],
            "durations": [],
            "timestamps": [],
            "operation_types": [],
            "resource_metrics": []
        }
        
        # Workload-specific batch size targets
        self.workload_targets = {
            "data_transform": 2.0,       # Target seconds for data transformation
            "data_validation": 1.5,      # Target seconds for data validation
            "repository_write": 3.0,       # Target seconds for repository writes
            "api_request": 1.0,          # Target seconds for API requests
            "default": 2.0               # Default target seconds
        }
        
        # Adaptive learning parameters
        self.learning_rate = 0.2         # How quickly to adapt to new performance data
        self.sample_window_size = 5      # Number of recent samples to consider
        
    def adjust_batch_size(
        self, 
        last_duration: float, 
        current_batch_size: int,
        operation_type: str = "default",
        resource_metrics: Dict[str, Any] = None
    ) -> int:
        """
        Dynamically adjust batch size based on performance, system resources,
        workload type, and historical performance data to optimize throughput.
        
        Args:
            last_duration: Duration of the last batch in seconds
            current_batch_size: Current batch size
            operation_type: Type of operation being performed (transform, validate, etc.)
            resource_metrics: Current system resource metrics (optional)
            
        Returns:
            Recommended batch size for the next operation
        """
        if not self.dynamic_sizing:
            return self.batch_size
        
        # Record performance data for adaptive learning
        if self.adaptive_learning:
            self.performance_history["batch_sizes"].append(current_batch_size)
            self.performance_history["durations"].append(last_duration)
            self.performance_history["timestamps"].append(datetime.datetime.now().isoformat())
            self.performance_history["operation_types"].append(operation_type)
            self.performance_history["resource_metrics"].append(resource_metrics or {})
            
            # Keep history within window size
            if len(self.performance_history["batch_sizes"]) > 100:  # Maximum history size
                self.performance_history["batch_sizes"] = self.performance_history["batch_sizes"][-100:]
                self.performance_history["durations"] = self.performance_history["durations"][-100:]
                self.performance_history["timestamps"] = self.performance_history["timestamps"][-100:]
                self.performance_history["operation_types"] = self.performance_history["operation_types"][-100:]
                self.performance_history["resource_metrics"] = self.performance_history["resource_metrics"][-100:]
        
        # Get target duration based on workload type
        target_duration = self.target_batch_duration_seconds
        if self.workload_specific_sizing and operation_type in self.workload_targets:
            target_duration = self.workload_targets[operation_type]
        
        # Apply resource-aware adjustments if available
        resource_adjustment = 1.0
        if self.resource_aware_sizing and resource_metrics:
            # Adjust based on CPU usage
            cpu_percent = resource_metrics.get("cpu_percent", 0)
            if cpu_percent > 80:
                resource_adjustment *= 0.7  # Significantly reduce batch size under high CPU load
            elif cpu_percent > 60:
                resource_adjustment *= 0.85  # Moderately reduce batch size under medium CPU load
            
            # Adjust based on memory usage
            memory_percent = resource_metrics.get("memory_percent", 0)
            if memory_percent > 85:
                resource_adjustment *= 0.75  # Reduce batch size under high memory pressure
            elif memory_percent > 70:
                resource_adjustment *= 0.9  # Slightly reduce batch size under medium memory pressure
            
            # Adjust based on I/O pressure if available
            io_percent = resource_metrics.get("disk_io_percent", 0)
            if io_percent > 70:
                resource_adjustment *= 0.8  # Reduce batch size under high I/O pressure
        
        # Apply adaptive learning based on recent performance
        adaptive_adjustment = 1.0
        if self.adaptive_learning and len(self.performance_history["batch_sizes"]) >= self.sample_window_size:
            # Calculate performance trend in the recent window
            recent_sizes = self.performance_history["batch_sizes"][-self.sample_window_size:]
            recent_durations = self.performance_history["durations"][-self.sample_window_size:]
            recent_ops = self.performance_history["operation_types"][-self.sample_window_size:]
            
            # Only consider same operation type
            same_op_indices = [i for i, op in enumerate(recent_ops) if op == operation_type]
            if same_op_indices:
                same_op_sizes = [recent_sizes[i] for i in same_op_indices]
                same_op_durations = [recent_durations[i] for i in same_op_indices]
                
                # Calculate average records processed per second
                if same_op_durations:
                    throughputs = [size / max(0.001, duration) for size, duration in zip(same_op_sizes, same_op_durations)]
                    avg_throughput = sum(throughputs) / len(throughputs)
                    
                    # Calculate optimal batch size to hit target duration
                    optimal_size = avg_throughput * target_duration
                    
                    # Apply learning rate to smooth adjustments
                    current_throughput = current_batch_size / max(0.001, last_duration)
                    if current_throughput > 0:
                        adaptive_adjustment = (
                            (1 - self.learning_rate) + 
                            self.learning_rate * (optimal_size / current_batch_size)
                        )
        
        # Calculate base adjustment from current performance
        if last_duration > target_duration * 1.5:
            # Too slow - decrease batch size
            base_adjustment = target_duration / max(0.001, last_duration)
        elif last_duration < target_duration * 0.75:
            # Too fast - increase batch size
            base_adjustment = target_duration / max(0.001, last_duration)
        else:
            # Close enough to target - minor adjustment
            deviation = last_duration / target_duration
            base_adjustment = 1.0 / max(0.5, min(1.5, deviation))
        
        # Combine all adjustment factors
        combined_adjustment = base_adjustment * resource_adjustment * adaptive_adjustment
        
        # Apply combined adjustment to calculate new batch size
        new_size = int(current_batch_size * combined_adjustment)
        
        # Ensure we stay within configured limits
        new_size = max(self.min_batch_size, min(self.max_batch_size, new_size))
        
        return new_size


class BatchProcessor:
    """
    Handles efficient batch processing of records with optimized throughput
    and error handling capabilities.
    """
    def __init__(
        self, 
        configuration: BatchConfiguration = None,
        logger: Optional[logging.Logger] = None
    ):
        self.config = configuration or BatchConfiguration()
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.metrics = PerformanceMetrics()
        self.shutdown_requested = False
        self.batch_queues: Dict[str, List] = {}  # Table name -> records
        self.checkpoints: Dict[str, Any] = {}  # For resumable operations
        
    def process_in_batches(
        self, 
        records: List[Any], 
        processor_func: Callable[[List[Any]], List[Any]],
        table_key: Callable[[Any], str] = None,
        operation_type: str = "default",
        resource_monitor = None
    ) -> List[Any]:
        """
        Process records in optimized batches with dynamic batch sizing
        
        Args:
            records: List of records to process
            processor_func: Function to process a batch of records
            table_key: Optional function to extract table name for priority
            operation_type: Type of operation (transform, validate, etc.) for specialized sizing
            resource_monitor: Optional ResourceMonitor instance for resource-aware batch sizing
            
        Returns:
            List of processed results
        """
        if not records:
            return []
            
        self.metrics = PerformanceMetrics()
        self.metrics.operation_type = operation_type
        
        # Sort by priority if table_key is provided
        if table_key and self.config.prioritize_tables:
            records = sorted(
                records,
                key=lambda r: self.config.prioritize_tables.get(table_key(r), 999)
            )
            
        # Process in batches
        results = []
        batch_size = self.config.batch_size
        
        for i in range(0, len(records), batch_size):
            if self.shutdown_requested:
                self.logger.warning("Shutdown requested, stopping batch processing")
                break
                
            # Get current resource metrics if available
            resource_metrics = None
            if resource_monitor:
                resource_metrics = resource_monitor.current_metrics
                
            batch = records[i:i+batch_size]
            batch_results, duration = self._process_batch_with_retry(batch, processor_func)
            results.extend(batch_results)
            
            # Record metrics and adjust batch size with enhanced parameters
            self.metrics.record_batch(len(batch), duration)
            batch_size = self.config.adjust_batch_size(
                last_duration=duration, 
                current_batch_size=batch_size,
                operation_type=operation_type,
                resource_metrics=resource_metrics
            )
            
            # Enhanced logging with more details
            resource_info = ""
            if resource_metrics:
                resource_info = (f" (CPU: {resource_metrics.get('cpu_percent', 0):.1f}%, "
                                 f"Mem: {resource_metrics.get('memory_percent', 0):.1f}%)")
                
            self.logger.info(
                f"Processed batch {len(self.metrics.batch_sizes)}: "
                f"{len(batch)} records in {duration:.2f}s, "
                f"rate: {len(batch)/max(0.001, duration):.1f} records/sec, "
                f"next batch size: {batch_size}{resource_info}"
            )
            
        self.metrics.complete()
        
        # Enhanced completion logging
        self.logger.info(
            f"Completed {operation_type} batch processing: {self.metrics.records_processed} records "
            f"in {self.metrics.total_duration:.2f}s, "
            f"avg rate: {self.metrics.processing_rate:.2f} records/sec, "
            f"best batch size: {self._get_optimal_batch_size()}"
        )
        
        return results
        
    def _get_optimal_batch_size(self) -> int:
        """Determine the optimal batch size based on performance metrics"""
        if not self.metrics.batch_sizes or not self.metrics.batch_durations:
            return self.config.batch_size
            
        # Calculate throughput for each batch
        throughputs = []
        for size, duration in zip(self.metrics.batch_sizes, self.metrics.batch_durations):
            throughput = size / max(0.001, duration)  # records per second
            throughputs.append((size, throughput))
            
        # Sort by throughput (highest first)
        throughputs.sort(key=lambda x: x[1], reverse=True)
        
        # Return the batch size with the highest throughput
        if throughputs:
            return throughputs[0][0]
        
        return self.config.batch_size
    
    def _process_batch_with_retry(
        self, 
        batch: List[Any], 
        processor_func: Callable[[List[Any]], List[Any]]
    ) -> Tuple[List[Any], float]:
        """
        Process a batch with enhanced retry logic, partial success handling,
        and intelligent error recovery
        """
        start_time = time.time()
        retries = 0
        last_error = None
        remaining_items = batch.copy()  # Track remaining items to be processed
        results = []  # Accumulate successful results
        
        # Implement retry with exponential backoff
        retry_delay = self.config.retry_delay_seconds
        
        # Track detailed error information for diagnostics
        error_details = {
            "attempts": 0,
            "errors": [],
            "recovery_actions": [],
            "partial_success_rate": 0.0
        }
        
        while remaining_items and retries <= self.config.max_retries:
            error_details["attempts"] += 1
            
            try:
                # Process the remaining batch
                current_batch_results = processor_func(remaining_items)
                
                # Aggregate with any previous partial results
                results.extend(current_batch_results)
                
                # Calculate duration and success metrics
                duration = time.time() - start_time
                success_rate = len(results) / len(batch) if batch else 1.0
                error_details["partial_success_rate"] = success_rate
                
                # All items processed successfully
                if len(results) == len(batch):
                    self.logger.info(f"Batch processing completed successfully after {retries} retries")
                    return results, duration
                
                # Handle partial success - determine which items were processed successfully
                # For now, this is a simulated implementation since we don't have details on the item structure
                processed_count = len(current_batch_results)
                remaining_items = remaining_items[processed_count:]
                
                self.logger.warning(
                    f"Partial batch processing success: {processed_count}/{len(remaining_items) + processed_count} " 
                    f"items processed. {len(remaining_items)} items remaining."
                )
                
                # If we had partial success but still have remaining items, continue with retry
                if remaining_items:
                    retries += 1
                    time.sleep(retry_delay)
                    # Implement exponential backoff with jitter
                    retry_delay = min(
                        self.config.max_retry_delay_seconds,
                        retry_delay * self.config.retry_backoff_factor * (1 + 0.2 * random.random())
                    )
                
            except Exception as e:
                retries += 1
                last_error = e
                error_type = type(e).__name__
                
                # Enhanced error logging
                error_context = {
                    "error_type": error_type,
                    "message": str(e),
                    "batch_size": len(remaining_items),
                    "retry_count": retries,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                error_details["errors"].append(error_context)
                
                # Track error in metrics
                if error_type not in self.metrics.error_counts:
                    self.metrics.error_counts[error_type] = 0
                self.metrics.error_counts[error_type] += 1
                
                # Examine the error for recovery strategy
                recovery_action = self._determine_error_recovery_strategy(error_type, str(e), retries)
                error_details["recovery_actions"].append(recovery_action)
                
                if retries <= self.config.max_retries:
                    self.logger.warning(
                        f"Batch processing error ({error_type}): {str(e)}. "
                        f"Retrying {retries}/{self.config.max_retries} "
                        f"in {retry_delay:.2f}s with recovery action: {recovery_action['action']}"
                    )
                    
                    # Apply recovery strategy before retry
                    if recovery_action["action"] == "reduce_batch_size" and len(remaining_items) > 1:
                        # Try with half the batch size
                        split_point = len(remaining_items) // 2
                        self.logger.info(f"Reducing batch size from {len(remaining_items)} to {split_point} for retry")
                        
                        # Attempt to process the first half
                        try:
                            half_batch_results = processor_func(remaining_items[:split_point])
                            results.extend(half_batch_results)
                            remaining_items = remaining_items[split_point:]
                            self.logger.info(f"Partial success with reduced batch size. {len(remaining_items)} items remaining.")
                        except Exception as split_error:
                            self.logger.warning(f"Reduced batch size still failed: {str(split_error)}")
                    
                    # Implement delay with a small random jitter to avoid thundering herd problems
                    jitter = random.uniform(0.8, 1.2)
                    time.sleep(retry_delay * jitter)
                    
                    # Implement exponential backoff
                    retry_delay = min(
                        self.config.max_retry_delay_seconds,
                        retry_delay * self.config.retry_backoff_factor
                    )
                else:
                    # Enhanced failure logging with detailed error history
                    error_log = "\n".join([
                        f"  Attempt {i+1}: {err['error_type']} - {err['message']}" 
                        for i, err in enumerate(error_details["errors"])
                    ])
                    
                    self.logger.error(
                        f"Batch processing failed after {retries} retries:\n{error_log}\n"
                        f"Partial success rate: {error_details['partial_success_rate']:.2%}"
                    )
                    
                    # If we had partial success, return what we have rather than failing completely
                    if results:
                        self.logger.warning(
                            f"Returning {len(results)}/{len(batch)} successfully processed items despite errors"
                        )
                        duration = time.time() - start_time
                        return results, duration
                        
                    # Otherwise, raise the error
                    raise
                    
        # Calculate final duration
        duration = time.time() - start_time
        
        # Check if we have any results to return after exhausting retries
        if results:
            self.logger.warning(
                f"Exhausted retries with {len(results)}/{len(batch)} items processed. "
                f"Duration: {duration:.2f}s"
            )
            return results, duration
            
        # No successful results after all retries
        if last_error:
            self.logger.error(f"Batch processing completely failed: {str(last_error)}")
            raise last_error
            
        # This should never happen due to the checks above
        return [], duration
        
    def _determine_error_recovery_strategy(self, error_type: str, error_message: str, retry_count: int) -> Dict[str, Any]:
        """
        Determine the best recovery strategy based on the error type and message
        
        Returns:
            Dict with action and parameters for recovery
        """
        # Default strategy
        strategy = {
            "action": "simple_retry",
            "reason": "Default retry policy"
        }
        
        # Connection-related errors
        if any(conn_err in error_type.lower() for conn_err in ["connection", "timeout", "network"]):
            if retry_count <= 2:
                strategy = {
                    "action": "increase_timeout",
                    "reason": "Connection issues detected, increasing timeout for next attempt"
                }
            else:
                strategy = {
                    "action": "reduce_batch_size",
                    "reason": "Persistent connection issues, reducing batch size to minimize impact"
                }
        
        # Resource-related errors
        elif any(res_err in error_type.lower() or res_err in error_message.lower() 
                for res_err in ["memory", "resource", "overflow", "capacity"]):
            strategy = {
                "action": "reduce_batch_size",
                "reason": "Resource constraints detected, reducing batch size to lower resource requirements"
            }
            
        # Data validation errors
        elif any(val_err in error_type.lower() or val_err in error_message.lower()
                for val_err in ["validation", "schema", "constraint", "integrity"]):
            strategy = {
                "action": "validate_individually",
                "reason": "Data validation issues detected, processing items individually to isolate problems"
            }
            
        # Rate limiting
        elif any(rate_err in error_message.lower() for rate_err in ["rate limit", "throttle", "quota"]):
            strategy = {
                "action": "exponential_backoff",
                "reason": "Rate limiting detected, implementing exponential backoff"
            }
            
        return strategy
    
    def save_checkpoint(self, key: str, data: Any) -> None:
        """Save a checkpoint for resumable processing"""
        self.checkpoints[key] = {
            "data": data,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    def get_checkpoint(self, key: str) -> Optional[Any]:
        """Get a previously saved checkpoint"""
        if key in self.checkpoints:
            return self.checkpoints[key]["data"]
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.metrics.to_dict()
    
    def request_shutdown(self) -> None:
        """Request a graceful shutdown of batch processing"""
        self.shutdown_requested = True


class ParallelProcessor:
    """
    Handles parallel processing using thread and process pools
    with dynamic resource allocation.
    """
    def __init__(
        self,
        thread_pool_size: int = None,
        process_pool_size: int = None,
        io_bound: bool = True,
        logger: Optional[logging.Logger] = None
    ):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.io_bound = io_bound
        
        # Auto-detect optimal pool sizes if not specified
        if thread_pool_size is None:
            thread_pool_size = min(32, (multiprocessing.cpu_count() * 4))
        
        if process_pool_size is None:
            process_pool_size = max(2, multiprocessing.cpu_count() - 1)
            
        self.thread_pool_size = thread_pool_size
        self.process_pool_size = process_pool_size
        self.metrics = PerformanceMetrics()
        self.metrics.thread_counts = {
            "thread_pool_size": thread_pool_size,
            "process_pool_size": process_pool_size
        }
        
        self.thread_executor = None
        self.process_executor = None
        
    def map(
        self, 
        func: Callable[[Any], Any], 
        items: List[Any],
        chunksize: int = 1,
        show_progress: bool = True
    ) -> List[Any]:
        """
        Apply function to each item in parallel
        
        Args:
            func: Function to apply to each item
            items: List of items to process
            chunksize: Size of chunks for multiprocessing (ignored for threads)
            show_progress: Whether to log progress
            
        Returns:
            List of results in the same order as input items
        """
        if not items:
            return []
            
        self.metrics = PerformanceMetrics()
        self.metrics.operation_type = "parallel_map"
        
        # Choose executor based on workload type
        if self.io_bound:
            self.logger.info(f"Using ThreadPoolExecutor with {self.thread_pool_size} workers")
            executor = ThreadPoolExecutor(max_workers=self.thread_pool_size)
        else:
            self.logger.info(f"Using ProcessPoolExecutor with {self.process_pool_size} workers")
            executor = ProcessPoolExecutor(max_workers=self.process_pool_size)
            
        # Set up progress tracking
        total_items = len(items)
        completed = 0
        results = [None] * total_items
        start_time = time.time()
        
        try:
            # Submit all tasks
            future_to_index = {
                executor.submit(func, item): i
                for i, item in enumerate(items)
            }
            
            # Process results as they complete
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    self.logger.error(f"Error processing item {index}: {str(e)}")
                    error_type = type(e).__name__
                    if error_type not in self.metrics.error_counts:
                        self.metrics.error_counts[error_type] = 0
                    self.metrics.error_counts[error_type] += 1
                    results[index] = None
                    
                # Update progress
                completed += 1
                if show_progress and completed % max(1, total_items // 10) == 0:
                    progress = completed / total_items * 100
                    elapsed = time.time() - start_time
                    rate = completed / max(0.001, elapsed)
                    remaining = (total_items - completed) / max(0.001, rate)
                    self.logger.info(
                        f"Progress: {progress:.1f}% ({completed}/{total_items}), "
                        f"Rate: {rate:.2f} items/sec, "
                        f"Est. remaining: {remaining:.1f}s"
                    )
        finally:
            executor.shutdown()
            
        # Record final metrics
        self.metrics.records_processed = total_items
        self.metrics.complete()
        self.logger.info(
            f"Completed parallel processing: {total_items} items "
            f"at {self.metrics.processing_rate:.2f} items/sec"
        )
            
        return results
    
    def map_batched(
        self,
        func: Callable[[List[Any]], List[Any]],
        items: List[Any],
        batch_size: int = 100,
        show_progress: bool = True
    ) -> List[Any]:
        """
        Apply function to batches of items in parallel
        
        Args:
            func: Function to apply to each batch
            items: List of items to process
            batch_size: Size of batches
            show_progress: Whether to log progress
            
        Returns:
            List of results (flattened)
        """
        if not items:
            return []
            
        # Create batches
        batches = []
        for i in range(0, len(items), batch_size):
            batches.append(items[i:i+batch_size])
            
        # Process batches in parallel
        self.logger.info(f"Processing {len(items)} items in {len(batches)} batches")
        batch_results = self.map(func, batches, show_progress=show_progress)
        
        # Flatten results
        results = []
        for batch_result in batch_results:
            if batch_result:
                results.extend(batch_result)
                
        return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.metrics.to_dict()


class ResourceMonitor:
    """
    Monitors system resources and provides dynamic 
    resource allocation recommendations.
    """
    def __init__(self, poll_interval_seconds: float = 5.0):
        self.poll_interval = poll_interval_seconds
        self.logger = logging.getLogger(self.__class__.__name__)
        self.monitoring = False
        self._monitor_thread = None
        self.metrics_history = []
        self.current_metrics = {
            "cpu_percent": 0,
            "memory_percent": 0,
            "memory_used_mb": 0,
            "disk_io_percent": 0,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    def start_monitoring(self) -> None:
        """Start background monitoring of system resources"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_resources,
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info("Resource monitoring started")
        
    def stop_monitoring(self) -> None:
        """Stop background monitoring"""
        self.monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
            self._monitor_thread = None
        self.logger.info("Resource monitoring stopped")
        
    def _monitor_resources(self) -> None:
        """Background thread for resource monitoring"""
        try:
            while self.monitoring:
                # Collect current resource metrics
                metrics = self._collect_metrics()
                
                # Save and rotate history
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > 100:
                    self.metrics_history = self.metrics_history[-100:]
                    
                # Update current metrics
                self.current_metrics = metrics
                
                # Sleep until next poll
                time.sleep(self.poll_interval)
        except Exception as e:
            self.logger.error(f"Error in resource monitoring: {str(e)}")
            self.monitoring = False
            
    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        # For the purpose of this example, we'll simulate metrics
        # In a real implementation, we would use psutil or similar
        return {
            "cpu_percent": random.uniform(10, 90),
            "memory_percent": random.uniform(20, 85),
            "memory_used_mb": random.uniform(1000, 8000),
            "disk_io_percent": random.uniform(5, 60),
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get the current system metrics"""
        return self.current_metrics
        
    def get_metrics_history(self) -> List[Dict[str, Any]]:
        """Get the history of metrics"""
        return self.metrics_history
        
    def recommend_resources(self, operation_type: str) -> Dict[str, Any]:
        """
        Recommend optimal resource allocation based on current system state
        
        Args:
            operation_type: Type of operation (e.g., 'etl', 'validation')
            
        Returns:
            Dictionary with thread count, process count, and batch size recommendations
        """
        # Get current system metrics
        metrics = self.current_metrics
        
        # Calculate recommended thread pool size based on CPU usage
        cpu_percent = metrics["cpu_percent"]
        memory_percent = metrics["memory_percent"]
        
        # Base recommendations
        base_thread_count = min(32, (multiprocessing.cpu_count() * 4))
        base_process_count = max(2, multiprocessing.cpu_count() - 1)
        
        # Adjust based on current resource usage
        if cpu_percent > 80:
            # CPU is highly loaded, reduce parallelism
            thread_factor = 0.6
            process_factor = 0.5
        elif cpu_percent > 60:
            thread_factor = 0.8
            process_factor = 0.7
        elif cpu_percent < 30:
            # CPU is underutilized, increase parallelism
            thread_factor = 1.2
            process_factor = 1.1
        else:
            # Moderate CPU usage, use base values
            thread_factor = 1.0
            process_factor = 1.0
            
        # Further adjust based on memory usage
        if memory_percent > 85:
            # High memory usage, reduce parallelism to avoid swapping
            thread_factor *= 0.7
            process_factor *= 0.6
            
        # Calculate recommended values
        recommended_thread_count = max(2, int(base_thread_count * thread_factor))
        recommended_process_count = max(1, int(base_process_count * process_factor))
        
        # Adjust batch size based on operation type and resource usage
        if operation_type == 'etl':
            if memory_percent > 80:
                batch_size = 50  # Smaller batches for memory-intensive operations
            elif cpu_percent > 70:
                batch_size = 100  # Moderate batches for CPU-intensive operations
            else:
                batch_size = 200  # Larger batches for general operations
        elif operation_type == 'validation':
            batch_size = 500  # Validation is typically less resource-intensive
        else:
            batch_size = 100  # Default batch size
            
        return {
            "thread_count": recommended_thread_count,
            "process_count": recommended_process_count,
            "batch_size": batch_size,
            "based_on": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "timestamp": metrics["timestamp"]
            }
        }


class RepositoryPerformanceMonitor:
    """
    Monitor repository performance and resource utilization.
    Provides insights into query execution times, connection pools,
    and repository load for performance optimization.
    """
    def __init__(
        self, 
        db_connection: DatabaseConnection,
        collection_interval_seconds: float = 10.0,
        max_history_size: int = 100
    ):
        self.db_connection = db_connection
        self.collection_interval = collection_interval_seconds
        self.max_history_size = max_history_size
        self.should_run = False
        self.monitoring_thread = None
        self.logger = logging.getLogger(f"{self.__class__.__name__}-{db_connection.db_type}")
        
        # Initialize metrics storage
        self.metrics = {
            "query_stats": {
                "avg_execution_time_ms": 0.0,
                "total_queries": 0,
                "queries_per_second": 0.0,
                "slow_query_count": 0
            },
            "connection_stats": {
                "active_connections": 0,
                "idle_connections": 0,
                "max_connections": 100,  # Simulated value
                "connection_utilization": 0.0
            },
            "resource_usage": {
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "disk_io_mb": 0.0
            },
            "history": [],
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Query timing history
        self.query_history = []
        
    def start(self) -> None:
        """Start database performance monitoring"""
        if self.monitoring_thread is not None:
            return
            
        self.should_run = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        self.logger.info(f"Database performance monitoring started for {self.db_connection.db_type}")
        
    def stop(self) -> None:
        """Stop database performance monitoring"""
        self.should_run = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
            self.monitoring_thread = None
        self.logger.info(f"Database performance monitoring stopped for {self.db_connection.db_type}")
        
    def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        try:
            while self.should_run:
                self._update_metrics()
                time.sleep(self.collection_interval)
        except Exception as e:
            self.logger.error(f"Error in database performance monitoring: {str(e)}")
            
    def _update_metrics(self) -> None:
        """Update database performance metrics"""
        try:
            # In a real implementation, these would be actual database queries
            # or monitoring API calls. For demo purposes, we'll simulate metrics.
            
            # Simulate connection stats
            active = random.randint(1, 20)
            idle = random.randint(5, 30)
            max_conn = 100
            
            # Update connection stats
            self.metrics["connection_stats"] = {
                "active_connections": active,
                "idle_connections": idle,
                "max_connections": max_conn,
                "connection_utilization": (active / max_conn) * 100.0
            }
            
            # Simulate resource usage
            self.metrics["resource_usage"] = {
                "cpu_percent": random.uniform(5.0, 40.0),
                "memory_mb": random.uniform(50.0, 500.0),
                "disk_io_mb": random.uniform(0.1, 10.0)
            }
            
            # Calculate query metrics based on recent history
            if self.query_history:
                avg_time = sum(q["execution_time_ms"] for q in self.query_history) / len(self.query_history)
                slow_count = sum(1 for q in self.query_history if q["execution_time_ms"] > 1000)
                
                # Queries per second based on recent history
                elapsed_time = 0
                if len(self.query_history) >= 2:
                    first = datetime.datetime.fromisoformat(self.query_history[0]["timestamp"])
                    last = datetime.datetime.fromisoformat(self.query_history[-1]["timestamp"])
                    elapsed_time = (last - first).total_seconds()
                
                qps = 0.0
                if elapsed_time > 0:
                    qps = len(self.query_history) / elapsed_time
                
                self.metrics["query_stats"] = {
                    "avg_execution_time_ms": avg_time,
                    "total_queries": len(self.query_history),
                    "queries_per_second": qps,
                    "slow_query_count": slow_count
                }
            
            # Update timestamp
            self.metrics["timestamp"] = datetime.datetime.now().isoformat()
            
            # Add to history
            history_entry = {
                "timestamp": self.metrics["timestamp"],
                "active_connections": self.metrics["connection_stats"]["active_connections"],
                "queries_per_second": self.metrics["query_stats"]["queries_per_second"],
                "avg_execution_time_ms": self.metrics["query_stats"]["avg_execution_time_ms"],
                "resource_usage": {
                    "cpu_percent": self.metrics["resource_usage"]["cpu_percent"],
                    "memory_mb": self.metrics["resource_usage"]["memory_mb"]
                }
            }
            self.metrics["history"].append(history_entry)
            
            # Trim history if needed
            if len(self.metrics["history"]) > self.max_history_size:
                self.metrics["history"] = self.metrics["history"][-self.max_history_size:]
                
        except Exception as e:
            self.logger.error(f"Error updating database performance metrics: {str(e)}")
    
    def record_query(self, query: str, execution_time_ms: float, rows_affected: int = 0) -> None:
        """Record information about a database query"""
        query_entry = {
            "query": query[:100],  # Only store beginning of query
            "execution_time_ms": execution_time_ms,
            "rows_affected": rows_affected,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        self.query_history.append(query_entry)
        
        # Keep history limited
        if len(self.query_history) > self.max_history_size:
            self.query_history = self.query_history[-self.max_history_size:]
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current database performance metrics"""
        return {
            "current": {
                "query_stats": self.metrics["query_stats"],
                "connection_stats": self.metrics["connection_stats"],
                "resource_usage": self.metrics["resource_usage"],
                "timestamp": self.metrics["timestamp"]
            },
            "history": self.metrics["history"][-10:]  # Return only last 10 entries
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Generate performance improvement recommendations based on metrics"""
        recommendations = []
        
        # Check connection pool utilization
        conn_util = self.metrics["connection_stats"]["connection_utilization"]
        if conn_util > 80.0:
            recommendations.append({
                "category": "connection_pool",
                "severity": "high",
                "message": "Connection pool utilization is high (>80%). Consider increasing max connections.",
                "current_value": conn_util,
                "recommendation": "Increase max_connections setting."
            })
        
        # Check for slow queries
        slow_count = self.metrics["query_stats"]["slow_query_count"]
        if slow_count > 5:
            recommendations.append({
                "category": "query_performance",
                "severity": "medium",
                "message": f"Found {slow_count} slow queries (>1000ms). Review and optimize.",
                "recommendation": "Analyze slow queries and add proper indexes."
            })
        
        # Check average query time
        avg_time = self.metrics["query_stats"]["avg_execution_time_ms"]
        if avg_time > 500.0:
            recommendations.append({
                "category": "query_performance",
                "severity": "medium",
                "message": f"Average query time is high ({avg_time:.2f}ms). Consider optimization.",
                "current_value": avg_time,
                "recommendation": "Review query patterns and database indexing strategy."
            })
        
        return recommendations


class DAGNode:
    """
    Represents a node in a directed acyclic graph for dependency tracking
    in incremental processing operations.
    """
    def __init__(self, id: str, data: Any = None):
        self.id = id
        self.data = data
        self.dependencies: Set[str] = set()  # IDs of nodes this node depends on
        self.dependents: Set[str] = set()    # IDs of nodes that depend on this node
        self.status = "pending"  # pending, processing, completed, failed
        self.result = None       # Result of processing this node
        self.error = None        # Error if processing failed
        
    def add_dependency(self, node_id: str) -> None:
        """Add a dependency for this node"""
        self.dependencies.add(node_id)
    
    def remove_dependency(self, node_id: str) -> None:
        """Remove a dependency for this node"""
        if node_id in self.dependencies:
            self.dependencies.remove(node_id)
            
    def add_dependent(self, node_id: str) -> None:
        """Add a dependent node"""
        self.dependents.add(node_id)
    
    def remove_dependent(self, node_id: str) -> None:
        """Remove a dependent node"""
        if node_id in self.dependents:
            self.dependents.remove(node_id)
            
    def is_ready(self) -> bool:
        """Check if this node is ready for processing"""
        return self.status == "pending" and not self.dependencies
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "dependencies": list(self.dependencies),
            "dependents": list(self.dependents),
            "status": self.status,
            "has_result": self.result is not None,
            "has_error": self.error is not None
        }


class DAGProcessor:
    """
    Processes nodes in a directed acyclic graph with dependency tracking
    for complex incremental operations.
    """
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.nodes: Dict[str, DAGNode] = {}
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.processing_order: List[str] = []  # Order in which nodes were processed
        self.metrics = PerformanceMetrics()
        self.metrics.operation_type = "dag_processing"
        
    def add_node(self, node_id: str, data: Any = None) -> DAGNode:
        """Add a node to the graph"""
        if node_id in self.nodes:
            return self.nodes[node_id]
            
        node = DAGNode(node_id, data)
        self.nodes[node_id] = node
        return node
    
    def add_dependency(self, dependent_id: str, dependency_id: str) -> None:
        """Add a dependency between nodes"""
        # Ensure nodes exist
        if dependent_id not in self.nodes:
            self.add_node(dependent_id)
        if dependency_id not in self.nodes:
            self.add_node(dependency_id)
            
        # Add dependency relationship
        self.nodes[dependent_id].add_dependency(dependency_id)
        self.nodes[dependency_id].add_dependent(dependent_id)
    
    def get_ready_nodes(self) -> List[DAGNode]:
        """Get nodes that are ready for processing"""
        return [
            node for node in self.nodes.values()
            if node.is_ready()
        ]
    
    def process_all(
        self, 
        processor_func: Callable[[Any], Any],
        parallel: bool = True,
        max_workers: int = None,
        checkpoint_after: int = 100
    ) -> Dict[str, Any]:
        """
        Process all nodes in dependency order
        
        Args:
            processor_func: Function to process a node's data
            parallel: Whether to process ready nodes in parallel
            max_workers: Maximum number of parallel workers
            checkpoint_after: Save checkpoint after this many nodes
            
        Returns:
            Dictionary of node_id -> results
        """
        if not max_workers:
            max_workers = min(32, (multiprocessing.cpu_count() * 2))
            
        # Start metrics
        self.metrics = PerformanceMetrics()
        self.metrics.operation_type = "dag_processing"
        self.metrics.thread_counts["max_workers"] = max_workers
        
        # Track processed nodes
        processed_nodes = 0
        results = {}
        
        # Process until all nodes are processed
        self.processing_order = []
        
        if parallel:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                while len(self.processing_order) < len(self.nodes):
                    # Get all ready nodes
                    ready_nodes = self.get_ready_nodes()
                    if not ready_nodes:
                        if len(self.processing_order) < len(self.nodes):
                            self.logger.error("No ready nodes but not all nodes processed. Possible cycle.")
                            break
                        continue
                        
                    self.logger.info(f"Processing {len(ready_nodes)} ready nodes in parallel")
                    
                    # Mark nodes as processing
                    for node in ready_nodes:
                        node.status = "processing"
                    
                    # Submit tasks
                    future_to_node = {
                        executor.submit(self._process_node, node, processor_func): node
                        for node in ready_nodes
                    }
                    
                    # Process results as they complete
                    for future in as_completed(future_to_node):
                        node = future_to_node[future]
                        try:
                            result = future.result()
                            results[node.id] = result
                            processed_nodes += 1
                            
                            # Update dependents
                            for dependent_id in node.dependents:
                                dependent = self.nodes[dependent_id]
                                dependent.remove_dependency(node.id)
                        except Exception as e:
                            self.logger.error(f"Error processing node {node.id}: {str(e)}")
                            error_type = type(e).__name__
                            if error_type not in self.metrics.error_counts:
                                self.metrics.error_counts[error_type] = 0
                            self.metrics.error_counts[error_type] += 1
                    
                    # Check if checkpoint needed
                    if processed_nodes % checkpoint_after == 0:
                        self.logger.info(f"Checkpoint: {processed_nodes} nodes processed")
        else:
            # Sequential processing
            while len(self.processing_order) < len(self.nodes):
                ready_nodes = self.get_ready_nodes()
                if not ready_nodes:
                    if len(self.processing_order) < len(self.nodes):
                        self.logger.error("No ready nodes but not all nodes processed. Possible cycle.")
                        break
                    continue
                
                # Process one node at a time
                node = ready_nodes[0]
                node.status = "processing"
                
                try:
                    result = self._process_node(node, processor_func)
                    results[node.id] = result
                    processed_nodes += 1
                    
                    # Update dependents
                    for dependent_id in node.dependents:
                        dependent = self.nodes[dependent_id]
                        dependent.remove_dependency(node.id)
                        
                    if processed_nodes % checkpoint_after == 0:
                        self.logger.info(f"Checkpoint: {processed_nodes} nodes processed")
                except Exception as e:
                    self.logger.error(f"Error processing node {node.id}: {str(e)}")
                    error_type = type(e).__name__
                    if error_type not in self.metrics.error_counts:
                        self.metrics.error_counts[error_type] = 0
                    self.metrics.error_counts[error_type] += 1
        
        # Complete metrics
        self.metrics.records_processed = processed_nodes
        self.metrics.complete()
        self.logger.info(
            f"Completed DAG processing: {processed_nodes} nodes "
            f"at {self.metrics.processing_rate:.2f} nodes/sec"
        )
        
        return results
    
    def _process_node(
        self, 
        node: DAGNode, 
        processor_func: Callable[[Any], Any]
    ) -> Any:
        """Process a single node"""
        try:
            # Process node data
            start_time = time.time()
            result = processor_func(node.data)
            duration = time.time() - start_time
            
            # Update node status
            node.status = "completed"
            node.result = result
            
            # Update processing order
            self.processing_order.append(node.id)
            
            # Log progress
            self.logger.debug(f"Processed node {node.id} in {duration:.4f}s")
            
            return result
        except Exception as e:
            # Update node status on error
            node.status = "failed"
            node.error = str(e)
            
            # Update processing order 
            self.processing_order.append(node.id)
            
            # Re-raise to propagate the error
            raise
    
    def visualize(self) -> str:
        """Generate a visualization of the graph"""
        # For a real implementation, this would use graphviz or similar
        # Here we'll just return a text representation
        lines = []
        lines.append("Directed Acyclic Graph Visualization:")
        lines.append(f"Total nodes: {len(self.nodes)}")
        
        status_counts = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}
        for node in self.nodes.values():
            status_counts[node.status] += 1
            
        lines.append(f"Status: {status_counts}")
        
        if self.processing_order:
            lines.append("Processing order: " + " -> ".join(self.processing_order[:5]) + 
                         (f" (+ {len(self.processing_order)-5} more)" if len(self.processing_order) > 5 else ""))
            
        # List nodes with many dependencies
        complex_nodes = [
            node for node in self.nodes.values()
            if len(node.dependencies) > 3 or len(node.dependents) > 3
        ]
        if complex_nodes:
            lines.append("Complex nodes:")
            for node in complex_nodes[:3]:
                lines.append(f"  Node {node.id}: {len(node.dependencies)} dependencies, {len(node.dependents)} dependents")
            if len(complex_nodes) > 3:
                lines.append(f"  (+ {len(complex_nodes)-3} more complex nodes)")
                
        return "\n".join(lines)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get processing metrics"""
        return self.metrics.to_dict()


class IncrementalETLOptimizer:
    """
    Optimizes change data capture and incremental ETL processes
    by monitoring transaction logs and efficiently tracking changes.
    """
    def __init__(self, source_connection: DatabaseConnection):
        self.source_connection = source_connection
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cdc_tracking = {}  # Tracks last processed position for each table
        
    def initialize_cdc_tracking(self, tables: List[str]) -> None:
        """Initialize CDC tracking for a list of tables"""
        for table in tables:
            if table not in self.cdc_tracking:
                self.cdc_tracking[table] = {
                    "last_lsn": None,  # Log Sequence Number
                    "last_timestamp": None,
                    "tracking_enabled": True,
                    "tracking_method": self._detect_optimal_tracking_method(table)
                }
                
    def _detect_optimal_tracking_method(self, table: str) -> str:
        """Detect the optimal change tracking method for a table"""
        # In a real implementation, this would analyze table structure, indexes, etc.
        # For demo purposes, we'll return a default method
        return "timestamp_column"
    
    def get_change_tracking_config(self, table: str) -> Dict[str, Any]:
        """Get change tracking configuration for a table"""
        if table not in self.cdc_tracking:
            self.initialize_cdc_tracking([table])
        return self.cdc_tracking[table]
    
    def update_tracking_position(self, table: str, lsn: Optional[str] = None, 
                               timestamp: Optional[str] = None) -> None:
        """Update the tracking position for a table"""
        if table in self.cdc_tracking:
            if lsn is not None:
                self.cdc_tracking[table]["last_lsn"] = lsn
            if timestamp is not None:
                self.cdc_tracking[table]["last_timestamp"] = timestamp
    
    def generate_incremental_query(self, table: str, last_sync_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate an optimized query for detecting changes since last sync
        
        Args:
            table: Table name to detect changes for
            last_sync_time: Optional override for last sync time
            
        Returns:
            Dictionary with query information
        """
        tracking_config = self.get_change_tracking_config(table)
        tracking_method = tracking_config["tracking_method"]
        
        # Use provided last_sync_time or the tracked timestamp
        effective_timestamp = last_sync_time or tracking_config["last_timestamp"]
        
        if tracking_method == "timestamp_column":
            query = f"""
            SELECT * FROM {table} 
            WHERE last_updated > :timestamp
            ORDER BY last_updated ASC
            """
            params = {"timestamp": effective_timestamp}
            
        elif tracking_method == "transaction_log":
            query = f"""
            SELECT * FROM change_log 
            WHERE table_name = :table 
            AND log_sequence_number > :lsn
            ORDER BY log_sequence_number ASC
            """
            params = {
                "table": table,
                "lsn": tracking_config["last_lsn"]
            }
            
        elif tracking_method == "change_tracking":
            query = f"""
            SELECT * FROM {table}_changes 
            WHERE change_time > :timestamp
            ORDER BY change_time ASC
            """
            params = {"timestamp": effective_timestamp}
            
        else:
            # Fallback to timestamp-based query
            query = f"""
            SELECT * FROM {table} 
            WHERE last_updated > :timestamp
            ORDER BY last_updated ASC
            """
            params = {"timestamp": effective_timestamp or "1900-01-01"}
            
        return {
            "query": query,
            "params": params,
            "tracking_method": tracking_method
        }
    
    def estimate_change_volume(self, table: str, last_sync_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Estimate the volume of changes since last sync
        
        Args:
            table: Table name to estimate changes for
            last_sync_time: Optional override for last sync time
            
        Returns:
            Dictionary with estimation information
        """
        tracking_config = self.get_change_tracking_config(table)
        effective_timestamp = last_sync_time or tracking_config["last_timestamp"]
        
        # In a real implementation, this would use table statistics and sampling
        # For demo purposes, we'll simulate an estimate
        if effective_timestamp is None:
            # No previous sync, assume full table
            return {
                "table": table,
                "estimated_rows": 1000,
                "estimated_size_mb": 10,
                "full_sync_recommended": True,
                "reason": "No previous sync information"
            }
        
        # Parse timestamp to calculate age
        if isinstance(effective_timestamp, str):
            try:
                last_sync = datetime.datetime.fromisoformat(effective_timestamp.replace('Z', '+00:00'))
                now = datetime.datetime.now(datetime.timezone.utc)
                hours_since_sync = (now - last_sync).total_seconds() / 3600
                
                # Simulate different volume based on age
                if hours_since_sync > 168:  # > 1 week
                    return {
                        "table": table,
                        "estimated_rows": 500,
                        "estimated_size_mb": 5,
                        "full_sync_recommended": True,
                        "reason": f"Last sync was {hours_since_sync:.1f} hours ago"
                    }
                elif hours_since_sync > 24:  # > 1 day
                    return {
                        "table": table,
                        "estimated_rows": 100,
                        "estimated_size_mb": 1,
                        "full_sync_recommended": False,
                        "reason": f"Last sync was {hours_since_sync:.1f} hours ago"
                    }
                else:
                    return {
                        "table": table,
                        "estimated_rows": 10,
                        "estimated_size_mb": 0.1,
                        "full_sync_recommended": False,
                        "reason": f"Last sync was {hours_since_sync:.1f} hours ago"
                    }
            except ValueError:
                # Couldn't parse timestamp
                return {
                    "table": table,
                    "estimated_rows": 100,
                    "estimated_size_mb": 1,
                    "full_sync_recommended": False,
                    "reason": "Using default estimate"
                }
        
        return {
            "table": table,
            "estimated_rows": 50,
            "estimated_size_mb": 0.5,
            "full_sync_recommended": False,
            "reason": "Using default estimate"
        }
    
    def optimize_batch_size(self, table: str, last_sync_time: Optional[str] = None) -> int:
        """
        Optimize batch size for processing changes
        
        Args:
            table: Table name to optimize for
            last_sync_time: Optional override for last sync time
            
        Returns:
            Recommended batch size
        """
        estimate = self.estimate_change_volume(table, last_sync_time)
        
        # Calculate optimal batch size based on estimated volume
        if estimate["estimated_rows"] > 1000:
            return 500
        elif estimate["estimated_rows"] > 100:
            return 100
        elif estimate["estimated_rows"] > 10:
            return 50
        else:
            return 25


class ChangeDetector:
    """
    Detects changes in the source system that need to be synchronized
    to the target system. Uses IncrementalETLOptimizer for improved efficiency.
    """
    def __init__(self, source_connection: DatabaseConnection):
        self.source_connection = source_connection
        self.logger = logging.getLogger(self.__class__.__name__)
        self.etl_optimizer = IncrementalETLOptimizer(source_connection)
        
    def detect_changes(self, last_sync_time: Optional[str] = None) -> List[DetectedChange]:
        """
        Detect changes in the source system since the last sync time.
        
        Args:
            last_sync_time: ISO-formatted timestamp of the last successful sync
            
        Returns:
            List of detected changes
        """
        self.logger.info(f"Detecting changes since {last_sync_time}")
        
        # In a real implementation, this would query the source system's change log
        # or use CDC mechanisms to identify changes
        
        # For demo purposes, we'll simulate detecting changes
        if last_sync_time:
            query = """
            SELECT * FROM change_log 
            WHERE timestamp > :last_sync_time 
            ORDER BY timestamp ASC
            """
            params = {"last_sync_time": last_sync_time}
        else:
            query = """
            SELECT * FROM change_log 
            ORDER BY timestamp ASC 
            LIMIT 10
            """
            params = {}
            
        change_log_entries = self.source_connection.execute_query(query, params)
        
        # Process the change log entries into DetectedChange objects
        detected_changes = []
        for entry in change_log_entries:
            # Get the full record data based on the change log entry
            record_query = f"""
            SELECT * FROM {entry['table_name']} 
            WHERE property_id = :record_id
            """
            record_params = {"record_id": entry['record_id']}
            record_data = self.source_connection.execute_query(record_query, record_params)
            
            if record_data:
                change_type = self._map_operation_to_change_type(entry['operation'])
                
                # Create a DetectedChange object
                detected_change = DetectedChange(
                    record_id=str(entry['record_id']),
                    source_table=entry['table_name'],
                    change_type=change_type,
                    new_data=record_data[0],
                    timestamp=entry['timestamp']
                )
                
                detected_changes.append(detected_change)
                
        self.logger.info(f"Detected {len(detected_changes)} changes")
        return detected_changes
    
    def detect_changes_for_table(self, table_name: str, filter_condition: Optional[str] = None) -> List[DetectedChange]:
        """
        Detect changes for a specific table with optional filtering.
        
        Args:
            table_name: Name of the table to detect changes for
            filter_condition: Optional SQL WHERE clause to filter records (without 'WHERE')
            
        Returns:
            List of detected changes for the specified table
        """
        self.logger.info(f"Detecting changes for table: {table_name}")
        
        # Determine the optimal query approach for this table
        tracking_config = self.etl_optimizer.get_tracking_config(table_name)
        
        # Build the base query
        base_query = f"SELECT * FROM {table_name}"
        
        # Add filter condition if provided
        if filter_condition:
            where_clause = f" WHERE {filter_condition}"
            self.logger.info(f"Applying filter: {filter_condition}")
        else:
            where_clause = ""
            
        # Complete the query
        query = f"{base_query}{where_clause}"
        
        # Execute the query to get all matching records
        records = self.source_connection.execute_query(query, {})
        
        # Transform the records into DetectedChange objects
        detected_changes = []
        for record in records:
            # For selective sync we default to INSERT operation
            # In a real implementation, we would determine the actual operation type
            change_type = ChangeType.INSERT
            
            # Get the record ID field (could be customized by table in a real implementation)
            record_id_field = "property_id" if table_name == "properties" else f"{table_name[:-1]}_id"
            
            # Create a DetectedChange object
            detected_change = DetectedChange(
                record_id=str(record.get(record_id_field, "")),
                source_table=table_name,
                change_type=change_type,
                new_data=record,
                timestamp=datetime.datetime.now().isoformat()
            )
            
            detected_changes.append(detected_change)
                
        self.logger.info(f"Detected {len(detected_changes)} changes for table {table_name}")
        
        return detected_changes
    
    def _map_operation_to_change_type(self, operation: str) -> ChangeType:
        """Map database operation to ChangeType enum"""
        op_map = {
            "INSERT": ChangeType.INSERT,
            "UPDATE": ChangeType.UPDATE,
            "DELETE": ChangeType.DELETE
        }
        return op_map.get(operation.upper(), ChangeType.NO_CHANGE)


class DataQualityProfiler:
    """
    Analyzes data quality across databases, providing metrics, anomaly detection,
    and data quality scoring to ensure data integrity during synchronization.
    """
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.logger = logging.getLogger(self.__class__.__name__)
        self.profiles = {}  # Cache for table profiles
        self.quality_scores = {}  # Cache for quality scores
        
    def profile_collection(self, collection_name: str, sample_size: int = 1000) -> Dict[str, Any]:
        """
        Generate a data quality profile for a collection
        
        Args:
            collection_name: Name of the collection to profile
            sample_size: Maximum number of items to analyze
            
        Returns:
            Dictionary with collection profile information
        """
        self.logger.info(f"Profiling collection {collection_name} (sample size: {sample_size})")
        
        try:
            # Query to get field information
            fields_query = f"""
            SELECT field_name, data_type 
            FROM information_schema.fields
            WHERE collection_name = :collection_name
            """
            
            # In a real implementation, this would get actual field metadata
            # For the simulation, we'll use mock data based on collection name
            fields = self._get_mock_fields(collection_name)
            
            # Sample data from the collection
            sample_query = f"""
            SELECT * FROM {collection_name}
            LIMIT :sample_size
            """
            
            # In a real implementation, this would be actual sample data
            # For the simulation, we'll use mock data
            sample_data = self.connection.execute_query(sample_query, {"sample_size": sample_size})
            
            # Generate profile
            profile = {
                "collection_name": collection_name,
                "timestamp": datetime.datetime.now().isoformat(),
                "item_count": self._estimate_row_count(collection_name),
                "fields": {},
                "correlation": {},
                "overall_quality_score": 0.0
            }
            
            # Process each field
            for field in fields:
                field_name = field["field_name"]
                data_type = field["data_type"]
                
                # Extract values for this field from sample data
                values = [item.get(field_name) for item in sample_data if field_name in item]
                
                # Generate field statistics
                field_profile = self._analyze_field(field_name, data_type, values)
                profile["fields"][field_name] = field_profile
            
            # Calculate correlations between numeric fields
            # In a real implementation, this would use actual correlation calculation
            # For the simulation, we'll generate mock correlation data
            profile["correlation"] = self._generate_mock_correlations(profile["fields"])
            
            # Calculate overall quality score
            profile["overall_quality_score"] = self._calculate_quality_score(profile)
            
            # Cache the profile
            self.profiles[collection_name] = profile
            self.quality_scores[collection_name] = profile["overall_quality_score"]
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Error profiling collection {collection_name}: {str(e)}")
            return {
                "error": str(e),
                "collection_name": collection_name,
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def detect_anomalies(self, collection_name: str, threshold: float = 0.8) -> Dict[str, Any]:
        """
        Detect anomalies in collection data based on the profile
        
        Args:
            collection_name: Name of the collection to analyze
            threshold: Threshold for anomaly detection (0-1)
            
        Returns:
            Dictionary with anomaly information
        """
        self.logger.info(f"Detecting anomalies in {collection_name} (threshold: {threshold})")
        
        try:
            # Get the profile or generate if not exists
            profile = self.profiles.get(collection_name)
            if not profile:
                profile = self.profile_collection(collection_name)
                
            # Find anomalies
            anomalies = {
                "collection_name": collection_name,
                "timestamp": datetime.datetime.now().isoformat(),
                "threshold": threshold,
                "fields": {},
                "items": []
            }
            
            # Check each field for anomalies
            for field_name, field_profile in profile["fields"].items():
                field_anomalies = []
                
                # Check for NULL percentage anomalies
                if field_profile.get("null_percentage", 0) > (1 - threshold) * 100:
                    field_anomalies.append({
                        "type": "high_null_percentage",
                        "value": field_profile["null_percentage"],
                        "description": f"High percentage of NULL values: {field_profile['null_percentage']:.2f}%"
                    })
                
                # Check for unique values anomalies
                if field_profile.get("unique_percentage", 0) < threshold * 100 and field_profile.get("cardinality", 0) < 10:
                    field_anomalies.append({
                        "type": "low_cardinality",
                        "value": field_profile["cardinality"],
                        "description": f"Low cardinality (few unique values): {field_profile['cardinality']}"
                    })
                
                # For numeric fields, check for statistical anomalies
                if field_profile.get("type") == "numeric":
                    # Check for skewness
                    if abs(field_profile.get("skewness", 0)) > 3:
                        field_anomalies.append({
                            "type": "high_skewness",
                            "value": field_profile["skewness"],
                            "description": f"Highly skewed distribution: {field_profile['skewness']:.2f}"
                        })
                    
                    # Check for outliers
                    if field_profile.get("outlier_percentage", 0) > (1 - threshold) * 100:
                        field_anomalies.append({
                            "type": "high_outliers",
                            "value": field_profile["outlier_percentage"],
                            "description": f"High percentage of outliers: {field_profile['outlier_percentage']:.2f}%"
                        })
                
                if field_anomalies:
                    anomalies["fields"][field_name] = field_anomalies
            
            # Item-level anomalies - in a real implementation, these would
            # be actual items that have anomalous values
            # For the simulation, we'll generate mock anomalous items
            anomalies["items"] = self._generate_mock_anomalous_records(collection_name, profile)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies in {collection_name}: {str(e)}")
            return {
                "error": str(e),
                "collection_name": collection_name,
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def get_quality_score(self, collection_name: str) -> Dict[str, Any]:
        """
        Get the quality score for a collection
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary with quality score information
        """
        self.logger.info(f"Getting quality score for {collection_name}")
        
        try:
            # Get the score from cache or calculate
            if collection_name in self.quality_scores:
                score = self.quality_scores[collection_name]
            else:
                profile = self.profile_collection(collection_name)
                score = profile["overall_quality_score"]
            
            return {
                "collection_name": collection_name,
                "quality_score": score,
                "timestamp": datetime.datetime.now().isoformat(),
                "score_interpretation": self._interpret_quality_score(score)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting quality score for {collection_name}: {str(e)}")
            return {
                "error": str(e),
                "collection_name": collection_name,
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def compare_quality(self, source_collection: str, target_collection: str) -> Dict[str, Any]:
        """
        Compare data quality between source and target collections
        
        Args:
            source_collection: Name of the source collection
            target_collection: Name of the target collection
            
        Returns:
            Dictionary with quality comparison information
        """
        self.logger.info(f"Comparing quality between {source_collection} and {target_collection}")
        
        try:
            # Get profiles for both collections
            source_profile = self.profiles.get(source_collection)
            if not source_profile:
                source_profile = self.profile_collection(source_collection)
                
            target_profile = self.profiles.get(target_collection)
            if not target_profile:
                target_profile = self.profile_collection(target_collection)
            
            # Compare quality metrics
            comparison = {
                "source_collection": source_collection,
                "target_collection": target_collection,
                "timestamp": datetime.datetime.now().isoformat(),
                "quality_diff": source_profile["overall_quality_score"] - target_profile["overall_quality_score"],
                "field_metrics": {},
                "summary": {}
            }
            
            # Compare common fields
            source_fields = set(source_profile["fields"].keys())
            target_fields = set(target_profile["fields"].keys())
            common_fields = source_fields.intersection(target_fields)
            
            for field in common_fields:
                source_field = source_profile["fields"][field]
                target_field = target_profile["fields"][field]
                
                # Calculate metric differences
                field_diff = {
                    "null_percentage_diff": source_field.get("null_percentage", 0) - target_field.get("null_percentage", 0),
                    "unique_percentage_diff": source_field.get("unique_percentage", 0) - target_field.get("unique_percentage", 0),
                    "quality_score_diff": source_field.get("quality_score", 0) - target_field.get("quality_score", 0)
                }
                
                # Add type-specific comparisons
                if source_field.get("type") == "numeric" and target_field.get("type") == "numeric":
                    field_diff.update({
                        "min_diff": source_field.get("min", 0) - target_field.get("min", 0),
                        "max_diff": source_field.get("max", 0) - target_field.get("max", 0),
                        "mean_diff": source_field.get("mean", 0) - target_field.get("mean", 0),
                        "std_dev_diff": source_field.get("std_dev", 0) - target_field.get("std_dev", 0)
                    })
                
                comparison["field_metrics"][field] = field_diff
            
            # Generate summary statistics
            field_count = len(common_fields)
            improved_fields = sum(1 for field, diff in comparison["field_metrics"].items() 
                               if diff["quality_score_diff"] > 0)
            degraded_fields = sum(1 for field, diff in comparison["field_metrics"].items() 
                               if diff["quality_score_diff"] < 0)
            
            comparison["summary"] = {
                "common_fields": field_count,
                "source_only_fields": len(source_fields - target_fields),
                "target_only_fields": len(target_fields - source_fields),
                "improved_fields": improved_fields,
                "degraded_fields": degraded_fields,
                "unchanged_fields": field_count - improved_fields - degraded_fields
            }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error comparing quality: {str(e)}")
            return {
                "error": str(e),
                "source_collection": source_collection,
                "target_collection": target_collection,
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def _estimate_row_count(self, collection_name: str) -> int:
        """Estimate item count for a collection"""
        # In a real implementation, this would use repository statistics
        # For the simulation, we'll generate a random count
        return random.randint(1000, 100000)
    
    def _get_mock_fields(self, collection_name: str) -> List[Dict[str, str]]:
        """Get mock field information for a collection"""
        if collection_name == "properties":
            return [
                {"field_name": "property_id", "data_type": "INTEGER"},
                {"field_name": "parcel_number", "data_type": "VARCHAR"},
                {"field_name": "owner_name", "data_type": "VARCHAR"},
                {"field_name": "address", "data_type": "VARCHAR"},
                {"field_name": "land_value", "data_type": "DECIMAL"},
                {"field_name": "improvement_value", "data_type": "DECIMAL"},
                {"field_name": "total_value", "data_type": "DECIMAL"},
                {"field_name": "last_updated", "data_type": "DATETIME"}
            ]
        elif collection_name == "valuations":
            return [
                {"field_name": "valuation_id", "data_type": "INTEGER"},
                {"field_name": "property_id", "data_type": "INTEGER"},
                {"field_name": "valuation_date", "data_type": "DATE"},
                {"field_name": "value_amount", "data_type": "DECIMAL"},
                {"field_name": "value_type", "data_type": "VARCHAR"},
                {"field_name": "assessor_id", "data_type": "INTEGER"}
            ]
        else:
            # Generic fields for other collections
            return [
                {"field_name": "id", "data_type": "INTEGER"},
                {"field_name": "name", "data_type": "VARCHAR"},
                {"field_name": "description", "data_type": "VARCHAR"},
                {"field_name": "created_at", "data_type": "DATETIME"},
                {"field_name": "updated_at", "data_type": "DATETIME"}
            ]
    
    def _analyze_field(self, field_name: str, data_type: str, values: List[Any]) -> Dict[str, Any]:
        """Analyze a field from sample data"""
        field_profile = {
            "name": field_name,
            "data_type": data_type,
            "sample_size": len(values)
        }
        
        # Count NULL values
        null_count = sum(1 for v in values if v is None)
        field_profile["null_count"] = null_count
        field_profile["null_percentage"] = (null_count / len(values) * 100) if values else 0
        
        # Count unique values
        non_null_values = [v for v in values if v is not None]
        unique_values = set(non_null_values)
        field_profile["cardinality"] = len(unique_values)
        field_profile["unique_percentage"] = (len(unique_values) / len(non_null_values) * 100) if non_null_values else 0
        
        # Type-specific analysis
        if data_type.upper() in ("INTEGER", "DECIMAL", "FLOAT", "NUMERIC"):
            field_profile["type"] = "numeric"
            numeric_values = [float(v) for v in non_null_values if str(v).replace(".", "", 1).isdigit()]
            
            if numeric_values:
                field_profile["min"] = min(numeric_values)
                field_profile["max"] = max(numeric_values)
                field_profile["mean"] = sum(numeric_values) / len(numeric_values)
                field_profile["median"] = self._calculate_median(numeric_values)
                
                # Standard deviation
                if len(numeric_values) > 1:
                    variance = sum((x - field_profile["mean"]) ** 2 for x in numeric_values) / len(numeric_values)
                    field_profile["std_dev"] = variance ** 0.5
                else:
                    field_profile["std_dev"] = 0
                
                # Calculate skewness
                if len(numeric_values) > 2 and field_profile["std_dev"] > 0:
                    skewness = sum((x - field_profile["mean"]) ** 3 for x in numeric_values)
                    skewness /= len(numeric_values) * (field_profile["std_dev"] ** 3)
                    field_profile["skewness"] = skewness
                else:
                    field_profile["skewness"] = 0
                
                # Identify outliers using IQR method
                q1, q3 = self._calculate_quartiles(numeric_values)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                outliers = [x for x in numeric_values if x < lower_bound or x > upper_bound]
                field_profile["outlier_count"] = len(outliers)
                field_profile["outlier_percentage"] = (len(outliers) / len(numeric_values) * 100) if numeric_values else 0
                
        elif data_type.upper() in ("VARCHAR", "CHAR", "TEXT"):
            field_profile["type"] = "text"
            text_values = [str(v) for v in non_null_values if v is not None]
            
            if text_values:
                field_profile["min_length"] = min(len(str(v)) for v in text_values)
                field_profile["max_length"] = max(len(str(v)) for v in text_values)
                field_profile["avg_length"] = sum(len(str(v)) for v in text_values) / len(text_values)
                
                # Check for email pattern
                email_pattern = r"[^@]+@[^@]+\.[^@]+"
                email_count = sum(1 for v in text_values if re.match(email_pattern, str(v)))
                field_profile["email_count"] = email_count
                field_profile["email_percentage"] = (email_count / len(text_values) * 100) if text_values else 0
                
        elif data_type.upper() in ("DATE", "DATETIME", "TIMESTAMP"):
            field_profile["type"] = "datetime"
            # In a real implementation, this would parse and analyze dates
            # For the simulation, we'll just set some basic metrics
            field_profile["has_future_dates"] = False
            field_profile["has_very_old_dates"] = False
            
        # Calculate field quality score
        field_profile["quality_score"] = self._calculate_field_quality_score(field_profile)
        
        return field_profile
    
    def _calculate_median(self, values: List[float]) -> float:
        """Calculate the median of a list of values"""
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n % 2 == 0:
            return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        else:
            return sorted_values[n//2]
    
    def _calculate_quartiles(self, values: List[float]) -> Tuple[float, float]:
        """Calculate the first and third quartiles"""
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n < 4:
            # Not enough values for meaningful quartiles
            return sorted_values[0], sorted_values[-1]
            
        q1_idx = n // 4
        q3_idx = (3 * n) // 4
        
        return sorted_values[q1_idx], sorted_values[q3_idx]
    
    def _calculate_field_quality_score(self, field_profile: Dict[str, Any]) -> float:
        """Calculate a quality score for a field (0-1)"""
        # Start with a perfect score and subtract penalties
        score = 1.0
        
        # Penalize for NULL values
        null_penalty = min(field_profile.get("null_percentage", 0) / 100, 0.5)
        score -= null_penalty
        
        # Type-specific penalties
        if field_profile.get("type") == "numeric":
            # Penalize for outliers
            outlier_penalty = min(field_profile.get("outlier_percentage", 0) / 200, 0.25)
            score -= outlier_penalty
            
            # Penalize for extreme skewness
            skewness = abs(field_profile.get("skewness", 0))
            skewness_penalty = min(skewness / 20, 0.25)
            score -= skewness_penalty
            
        elif field_profile.get("type") == "text":
            # Penalize for very short values if there are many
            if field_profile.get("min_length", 0) < 2 and field_profile.get("cardinality", 0) > 10:
                score -= 0.1
                
        # Ensure score is between 0 and 1
        return max(0, min(score, 1))
    
    def _calculate_quality_score(self, profile: Dict[str, Any]) -> float:
        """Calculate overall quality score for a collection"""
        field_scores = [field.get("quality_score", 0) for field in profile["fields"].values()]
        
        if not field_scores:
            return 0.0
            
        # Weight important fields more heavily
        # In a real implementation, this would use domain knowledge
        # For the simulation, we'll just use the average
        return sum(field_scores) / len(field_scores)
    
    def _interpret_quality_score(self, score: float) -> str:
        """Interpret a quality score as a descriptive category"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.8:
            return "good"
        elif score >= 0.6:
            return "adequate"
        elif score >= 0.4:
            return "poor"
        else:
            return "critical"
    
    def _generate_mock_correlations(self, fields: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Generate mock correlation data"""
        numeric_fields = [field for field, profile in fields.items() if profile.get("type") == "numeric"]
        correlations = {}
        
        for field in numeric_fields:
            correlations[field] = {}
            
        # Generate random correlations between fields
        for i, field1 in enumerate(numeric_fields):
            for field2 in numeric_fields[i+1:]:
                # Random correlation between -1 and 1
                correlation = random.uniform(-0.9, 0.9)
                correlations[field1][field2] = correlation
                correlations[field2][field1] = correlation
                
        return correlations
    
    def _generate_mock_anomalous_records(self, collection_name: str, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock anomalous records"""
        # In a real implementation, this would find actual anomalous records
        # For the simulation, we'll generate random anomalies
        anomalous_records = []
        
        # Generate a few anomalous records
        for i in range(3):
            record = {"id": random.randint(1000, 9999)}
            
            # Add anomalies for specific fields
            for field, field_profile in profile["fields"].items():
                if field_profile.get("type") == "numeric" and random.random() < 0.3:
                    # Generate outlier value
                    if "max" in field_profile:
                        record[field] = field_profile["max"] * (2 + random.random())
                elif field_profile.get("type") == "text" and random.random() < 0.3:
                    # Generate invalid text
                    record[field] = "###INVALID###" + str(random.randint(1, 100))
                        
            anomalous_records.append(record)
            
        return anomalous_records


class DataTypeConverter:
    """
    Handles data type conversions between different database systems.
    Specializes in converting between legacy data types and modern ones.
    """
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.conversion_registry = self._build_conversion_registry()
        
    def _build_conversion_registry(self) -> Dict[str, Dict[str, callable]]:
        """Build registry of conversion functions for different data types"""
        registry = {}
        
        # Register string type conversions
        registry["VARCHAR"] = {
            "VARCHAR": self._direct_copy,
            "TEXT": self._direct_copy,
            "CHAR": self._pad_or_truncate,
            "JSONB": self._string_to_json
        }
        
        # Register numeric type conversions
        registry["INTEGER"] = {
            "INTEGER": self._direct_copy,
            "BIGINT": self._direct_copy,
            "DECIMAL": self._int_to_decimal,
            "NUMERIC": self._int_to_decimal,
            "UUID": self._int_to_uuid,
            "VARCHAR": self._int_to_string
        }
        
        registry["DECIMAL"] = {
            "DECIMAL": self._direct_copy,
            "NUMERIC": self._direct_copy,
            "INTEGER": self._decimal_to_int,
            "VARCHAR": self._decimal_to_string
        }
        
        # Register date/time type conversions
        registry["DATE"] = {
            "DATE": self._direct_copy,
            "DATETIME": self._date_to_datetime,
            "TIMESTAMP": self._date_to_timestamp,
            "VARCHAR": self._date_to_string
        }
        
        registry["DATETIME"] = {
            "DATETIME": self._direct_copy,
            "TIMESTAMP": self._datetime_to_timestamp,
            "DATE": self._datetime_to_date,
            "VARCHAR": self._datetime_to_string
        }
        
        # Register boolean type conversions
        registry["BIT"] = {
            "BIT": self._direct_copy,
            "BOOLEAN": self._bit_to_boolean,
            "INTEGER": self._bit_to_int,
            "VARCHAR": self._bit_to_string
        }
        
        return registry
    
    def convert_value(self, value: Any, source_type: str, target_type: str) -> Any:
        """
        Convert a value from source type to target type
        
        Args:
            value: The value to convert
            source_type: The source data type (e.g., "INTEGER", "VARCHAR(100)")
            target_type: The target data type (e.g., "NUMERIC(10,2)", "JSONB")
            
        Returns:
            The converted value
        """
        if value is None:
            return None
            
        # Extract base types by removing size/precision specifications
        base_source_type = self._extract_base_type(source_type)
        base_target_type = self._extract_base_type(target_type)
        
        if base_source_type not in self.conversion_registry:
            raise ValueError(f"Unsupported source type: {source_type}")
            
        if base_target_type not in self.conversion_registry[base_source_type]:
            raise ValueError(f"Unsupported conversion: {source_type} to {target_type}")
            
        # Get conversion function and apply it
        conversion_func = self.conversion_registry[base_source_type][base_target_type]
        return conversion_func(value, source_type, target_type)
    
    def _extract_base_type(self, data_type: str) -> str:
        """Extract base type without size/precision specifications"""
        match = re.match(r'^([A-Z]+)', data_type)
        if match:
            return match.group(1)
        return data_type
    
    # Direct conversion (no type change)
    def _direct_copy(self, value: Any, source_type: str, target_type: str) -> Any:
        """Direct copy of value (no conversion needed)"""
        return value
    
    # String type conversions
    def _pad_or_truncate(self, value: str, source_type: str, target_type: str) -> str:
        """Pad or truncate string to fit CHAR fixed length"""
        if not isinstance(value, str):
            value = str(value)
            
        # Extract target length
        match = re.match(r'CHAR\((\d+)\)', target_type)
        if match:
            length = int(match.group(1))
            if len(value) < length:
                return value.ljust(length)
            else:
                return value[:length]
        return value
    
    def _string_to_json(self, value: str, source_type: str, target_type: str) -> Dict[str, Any]:
        """Convert string to JSON"""
        if isinstance(value, dict):
            return value
            
        try:
            # Try parsing as JSON
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # If not valid JSON, wrap in a simple object
            return {"value": value}
    
    # Numeric type conversions
    def _int_to_decimal(self, value: int, source_type: str, target_type: str) -> float:
        """Convert integer to decimal/numeric"""
        try:
            # Extract precision and scale if specified
            match = re.match(r'(DECIMAL|NUMERIC)\((\d+),(\d+)\)', target_type)
            if match:
                precision = int(match.group(2))
                scale = int(match.group(3))
                
                # Format with the right precision
                format_str = f"{{:.{scale}f}}"
                formatted = format_str.format(float(value))
                
                # Ensure it doesn't exceed precision
                parts = formatted.split('.')
                if len(parts[0]) > (precision - scale):
                    raise ValueError(f"Value {value} exceeds precision of {target_type}")
                    
                return float(formatted)
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _int_to_uuid(self, value: int, source_type: str, target_type: str) -> str:
        """Convert integer to UUID string"""
        try:
            # Create a deterministic UUID using the integer as a seed
            import hashlib
            md5 = hashlib.md5(str(value).encode()).hexdigest()
            return f"{md5[:8]}-{md5[8:12]}-{md5[12:16]}-{md5[16:20]}-{md5[20:32]}"
        except Exception:
            # Fallback to a random UUID if conversion fails
            import uuid
            return str(uuid.uuid4())
    
    def _int_to_string(self, value: int, source_type: str, target_type: str) -> str:
        """Convert integer to string"""
        return str(value)
    
    def _decimal_to_int(self, value: float, source_type: str, target_type: str) -> int:
        """Convert decimal to integer"""
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    
    def _decimal_to_string(self, value: float, source_type: str, target_type: str) -> str:
        """Convert decimal to string"""
        try:
            # Extract source scale if specified to maintain precision
            match = re.match(r'(DECIMAL|NUMERIC)\((\d+),(\d+)\)', source_type)
            if match:
                scale = int(match.group(3))
                format_str = f"{{:.{scale}f}}"
                return format_str.format(value)
            return str(value)
        except (ValueError, TypeError):
            return "0"
    
    # Date/time type conversions
    def _date_to_datetime(self, value: str, source_type: str, target_type: str) -> str:
        """Convert date to datetime"""
        try:
            if isinstance(value, str):
                # Parse the date string
                parsed_date = datetime.datetime.strptime(value, "%Y-%m-%d")
                # Return ISO format with time component
                return parsed_date.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
                # Add time component to date object
                return datetime.datetime.combine(value, datetime.time()).strftime("%Y-%m-%d %H:%M:%S")
            return value
        except (ValueError, TypeError):
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _date_to_timestamp(self, value: str, source_type: str, target_type: str) -> str:
        """Convert date to timestamp"""
        # First convert to datetime, then to timestamp format
        datetime_str = self._date_to_datetime(value, source_type, "DATETIME")
        try:
            parsed = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            return parsed.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        except (ValueError, TypeError):
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    def _date_to_string(self, value: str, source_type: str, target_type: str) -> str:
        """Convert date to string"""
        try:
            if isinstance(value, str):
                # Try to parse and format consistently
                parsed_date = datetime.datetime.strptime(value, "%Y-%m-%d")
                return parsed_date.strftime("%Y-%m-%d")
            elif isinstance(value, (datetime.date, datetime.datetime)):
                return value.strftime("%Y-%m-%d")
            return str(value)
        except (ValueError, TypeError):
            return str(value)
    
    def _datetime_to_timestamp(self, value: str, source_type: str, target_type: str) -> str:
        """Convert datetime to timestamp"""
        try:
            if isinstance(value, str):
                # Parse the datetime string
                parsed = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                return parsed.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            elif isinstance(value, datetime.datetime):
                return value.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            return value
        except (ValueError, TypeError):
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    def _datetime_to_date(self, value: str, source_type: str, target_type: str) -> str:
        """Convert datetime to date (truncate time component)"""
        try:
            if isinstance(value, str):
                # Parse the datetime string
                parsed = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                return parsed.strftime("%Y-%m-%d")
            elif isinstance(value, datetime.datetime):
                return value.strftime("%Y-%m-%d")
            return value
        except (ValueError, TypeError):
            return datetime.datetime.now().strftime("%Y-%m-%d")
    
    def _datetime_to_string(self, value: str, source_type: str, target_type: str) -> str:
        """Convert datetime to string"""
        try:
            if isinstance(value, str):
                # Validate it's a proper datetime
                datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                return value
            elif isinstance(value, datetime.datetime):
                return value.strftime("%Y-%m-%d %H:%M:%S")
            return str(value)
        except (ValueError, TypeError):
            return str(value)
    
    # Boolean type conversions
    def _bit_to_boolean(self, value: Any, source_type: str, target_type: str) -> bool:
        """Convert bit to boolean"""
        if isinstance(value, bool):
            return value
        if isinstance(value, int) or isinstance(value, str) and value.isdigit():
            return bool(int(value))
        if isinstance(value, str):
            return value.lower() in ('true', 't', 'yes', 'y', '1')
        return bool(value)
    
    def _bit_to_int(self, value: Any, source_type: str, target_type: str) -> int:
        """Convert bit to integer"""
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, int):
            return 1 if value else 0
        if isinstance(value, str):
            if value.isdigit():
                return 1 if int(value) else 0
            return 1 if value.lower() in ('true', 't', 'yes', 'y', '1') else 0
        return 1 if value else 0
    
    def _bit_to_string(self, value: Any, source_type: str, target_type: str) -> str:
        """Convert bit to string"""
        bool_value = self._bit_to_boolean(value, source_type, "BOOLEAN")
        return "true" if bool_value else "false"


class TransformationRule:
    """Base class for all transformation rules"""
    def apply(self, value: Any, context: Dict[str, Any] = None) -> Any:
        raise NotImplementedError("Subclasses must implement apply()")
    
    def get_description(self) -> str:
        return "Base transformation rule"


class FormatTransformation(TransformationRule):
    """Format a string value using a template"""
    def __init__(self, format_template: str):
        self.format_template = format_template
        
    def apply(self, value: Any, context: Dict[str, Any] = None) -> str:
        try:
            if isinstance(value, (list, tuple)):
                return self.format_template.format(*value)
            elif isinstance(value, dict):
                return self.format_template.format(**value)
            else:
                return self.format_template.format(value)
        except Exception as e:
            logging.error(f"Format transformation error: {e}")
            return str(value)
    
    def get_description(self) -> str:
        return f"Format using template: {self.format_template}"


class LookupTransformation(TransformationRule):
    """Replace values using a lookup dictionary"""
    def __init__(self, lookup_map: Dict[Any, Any], default_to_original: bool = True):
        self.lookup_map = lookup_map
        self.default_to_original = default_to_original
        
    def apply(self, value: Any, context: Dict[str, Any] = None) -> Any:
        if value in self.lookup_map:
            return self.lookup_map[value]
        elif self.default_to_original:
            return value
        else:
            return None
    
    def get_description(self) -> str:
        return f"Lookup using mapping of {len(self.lookup_map)} values"


class CombineTransformation(TransformationRule):
    """Combine multiple values into one string"""
    def __init__(self, separator: str = " "):
        self.separator = separator
        
    def apply(self, values: List[Any], context: Dict[str, Any] = None) -> str:
        return self.separator.join(str(v) for v in values if v is not None)
    
    def get_description(self) -> str:
        return f"Combine values with separator: '{self.separator}'"


class JsonPathExtraction(TransformationRule):
    """Extract data from JSON or nested dictionaries using JSON path syntax"""
    def __init__(self, path: str, default_value: Any = None):
        self.path = path
        self.default_value = default_value
        self._compile_path()
        
    def _compile_path(self):
        # Convert JSONPath to a list of key accessors
        self.path_parts = self.path.lstrip('$.').split('.')
        
    def apply(self, value: Dict[str, Any], context: Dict[str, Any] = None) -> Any:
        if not isinstance(value, dict):
            return self.default_value
            
        current = value
        try:
            for part in self.path_parts:
                # Handle array indexing
                if '[' in part and part.endswith(']'):
                    key, idx_str = part.split('[', 1)
                    idx = int(idx_str[:-1])  # remove the closing bracket
                    current = current.get(key, [])[idx]
                else:
                    current = current.get(part, None)
                    
                if current is None:
                    return self.default_value
            return current
        except (KeyError, IndexError, TypeError):
            return self.default_value
    
    def get_description(self) -> str:
        return f"Extract using JSON path: {self.path}"


class DateTimeTransformation(TransformationRule):
    """Convert between different date/time formats"""
    def __init__(self, source_format: str = None, target_format: str = "%Y-%m-%d"):
        self.source_format = source_format
        self.target_format = target_format
        
    def apply(self, value: Any, context: Dict[str, Any] = None) -> str:
        if not value:
            return None
            
        try:
            # If source_format is provided, parse using it
            if self.source_format:
                dt = datetime.datetime.strptime(str(value), self.source_format)
            else:
                # Try common formats
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%d-%b-%Y"]:
                    try:
                        dt = datetime.datetime.strptime(str(value), fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # If we get here, no format matched
                    raise ValueError(f"Could not parse date: {value}")
                    
            return dt.strftime(self.target_format)
        except Exception as e:
            logging.error(f"Date transformation error: {e}")
            return str(value)
    
    def get_description(self) -> str:
        src = self.source_format or "auto-detect"
        return f"Convert date from {src} to {self.target_format}"


class NumberTransformation(TransformationRule):
    """Transform numeric values (scaling, rounding, formatting)"""
    def __init__(self, 
                 scale_factor: float = 1.0, 
                 rounding_digits: int = None,
                 number_format: str = None):
        self.scale_factor = scale_factor
        self.rounding_digits = rounding_digits
        self.number_format = number_format
        
    def apply(self, value: Any, context: Dict[str, Any] = None) -> Any:
        if value is None:
            return None
            
        try:
            # Convert to float first
            num_value = float(value)
            
            # Apply scaling
            result = num_value * self.scale_factor
            
            # Apply rounding if specified
            if self.rounding_digits is not None:
                result = round(result, self.rounding_digits)
                
            # Format if specified, otherwise return the number
            if self.number_format:
                return self.number_format.format(result)
            return result
        except Exception as e:
            logging.error(f"Number transformation error: {e}")
            return value
    
    def get_description(self) -> str:
        parts = []
        if self.scale_factor != 1.0:
            parts.append(f"scale by {self.scale_factor}")
        if self.rounding_digits is not None:
            parts.append(f"round to {self.rounding_digits} digits")
        if self.number_format:
            parts.append(f"format as '{self.number_format}'")
        return "Number transformation: " + ", ".join(parts)


class AddressNormalization(TransformationRule):
    """Normalize address formats"""
    def __init__(self, output_format: str = "single_line"):
        self.output_format = output_format
        
    def apply(self, value: Any, context: Dict[str, Any] = None) -> Any:
        if isinstance(value, dict):
            # Handle structured address
            address = value
        elif isinstance(value, str):
            # Parse from string
            address = self._parse_address(value)
        else:
            return value
            
        if self.output_format == "single_line":
            parts = []
            if address.get('number'):
                parts.append(address.get('number', ''))
            if address.get('street'):
                parts.append(address.get('street', ''))
            if address.get('unit'):
                parts.append(f"#{address.get('unit', '')}")
            
            line2_parts = []
            if address.get('city'):
                line2_parts.append(address.get('city', ''))
            if address.get('state') and address.get('zip'):
                line2_parts.append(f"{address.get('state', '')}, {address.get('zip', '')}")
            elif address.get('state'):
                line2_parts.append(address.get('state', ''))
                
            result = " ".join(parts)
            if line2_parts:
                result += ", " + ", ".join(line2_parts)
            return result
        elif self.output_format == "json":
            return address
        else:
            return value
    
    def _parse_address(self, address_str: str) -> Dict[str, str]:
        """Basic address parsing - would be more sophisticated in production"""
        parts = address_str.split(',')
        result = {}
        
        if len(parts) >= 1:
            street_parts = parts[0].strip().split(' ')
            if street_parts and street_parts[0].isdigit():
                result['number'] = street_parts[0]
                result['street'] = ' '.join(street_parts[1:])
            else:
                result['street'] = parts[0].strip()
                
        if len(parts) >= 2:
            city_state_zip = parts[1].strip().split(' ')
            if len(city_state_zip) >= 1:
                result['city'] = city_state_zip[0]
            if len(city_state_zip) >= 2:
                result['state'] = city_state_zip[-2]
            if len(city_state_zip) >= 3:
                result['zip'] = city_state_zip[-1]
                
        return result
    
    def get_description(self) -> str:
        return f"Normalize address to {self.output_format} format"


class AIEnrichment(TransformationRule):
    """Enrich data using AI capabilities"""
    def __init__(self, enrichment_type: str, api_key_env_var: str = None):
        self.enrichment_type = enrichment_type
        self.api_key_env_var = api_key_env_var
        
    def apply(self, value: Any, context: Dict[str, Any] = None) -> Any:
        # This would use an actual AI service in production
        # For now, we'll simulate enrichment based on the type
        if self.enrichment_type == "address_completion":
            return self._simulate_address_completion(value)
        elif self.enrichment_type == "entity_extraction":
            return self._simulate_entity_extraction(value)
        else:
            return value
    
    def _simulate_address_completion(self, value: str) -> Dict[str, str]:
        """Simulate address completion"""
        if not isinstance(value, str):
            return value
            
        # Check if we have a partial address
        if ',' not in value and len(value.split()) <= 3:
            # Add a simulated completion
            address_parts = value.split()
            if len(address_parts) == 1:
                # Just a street name
                return f"{value} Street, Springfield, IL 62701"
            else:
                # Partial address
                return f"{value}, Springfield, IL 62701"
        return value
    
    def _simulate_entity_extraction(self, value: str) -> Dict[str, Any]:
        """Simulate entity extraction"""
        if not isinstance(value, str):
            return value
            
        # Extract potential entities from text
        result = {"original": value, "entities": {}}
        
        # Look for patterns like names, dates, and organizations
        name_pattern = r"([A-Z][a-z]+ [A-Z][a-z]+)"
        date_pattern = r"(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})"
        
        name_matches = re.findall(name_pattern, value)
        date_matches = re.findall(date_pattern, value)
        
        if name_matches:
            result["entities"]["names"] = name_matches
        if date_matches:
            result["entities"]["dates"] = date_matches
            
        return result
    
    def get_description(self) -> str:
        return f"AI enrichment: {self.enrichment_type}"


class ComplexTransformation(TransformationRule):
    """Combines multiple transformations in sequence"""
    def __init__(self, transforms: List[TransformationRule]):
        self.transforms = transforms
        
    def apply(self, value: Any, context: Dict[str, Any] = None) -> Any:
        result = value
        for transform in self.transforms:
            result = transform.apply(result, context)
        return result
    
    def get_description(self) -> str:
        return "Complex transformation: " + " → ".join(t.get_description() for t in self.transforms)


class DataTransformer:
    """
    Enhanced data transformer with advanced capabilities for complex transformations.
    Provides template-based field mapping, JSON path extraction, smart data type conversion,
    and AI-powered data enrichment.
    """
    def __init__(self, field_mapping_config: Dict[str, Any] = None):
        self.field_mapping = field_mapping_config or self._get_default_field_mapping()
        self.logger = logging.getLogger(self.__class__.__name__)
        # Initialize the data type converter for handling type conversions
        self.type_converter = DataTypeConverter()
        # Initialize transformation rule repository
        self.transformation_rules = self._initialize_transformation_rules()
        
    def transform(self, changes: List[DetectedChange]) -> List[TransformedRecord]:
        """
        Transform detected changes into the target system format.
        
        Args:
            changes: List of detected changes from the source system
            
        Returns:
            List of transformed records ready for the target system
        """
        self.logger.info(f"Transforming {len(changes)} records")
        
        transformed_records = []
        for change in changes:
            if change.source_table in self.field_mapping:
                mapping = self.field_mapping[change.source_table]
                
                # Apply the field mapping to transform the data
                transformed_data = self._apply_mapping(
                    change.new_data, 
                    mapping['fields'],
                    mapping.get('transforms', {})
                )
                
                # Apply global transformations if defined
                if 'global_transforms' in mapping:
                    transformed_data = self._apply_global_transforms(
                        transformed_data,
                        mapping['global_transforms'],
                        context={
                            'source_table': change.source_table,
                            'operation': change.change_type,
                            'source_data': change.new_data
                        }
                    )
                
                # Determine target ID and table
                target_table = mapping['target_table']
                target_id = self._determine_target_id(change, mapping)
                
                # Create the transformed record
                transformed_record = TransformedRecord(
                    source_id=change.record_id,
                    target_id=target_id,
                    target_table=target_table,
                    data=transformed_data,
                    operation=change.change_type,
                    metadata={
                        "source_table": change.source_table,
                        "source_timestamp": change.timestamp,
                        "transformed_at": datetime.datetime.now().isoformat(),
                        "transformation_version": "2.0",
                        "applied_rules": self._get_applied_rules(mapping)
                    }
                )
                
                transformed_records.append(transformed_record)
            else:
                self.logger.warning(f"No mapping configuration for table: {change.source_table}")
                
        self.logger.info(f"Transformed {len(transformed_records)} records")
        return transformed_records
    
    def _apply_mapping(
        self, 
        source_data: Dict[str, Any], 
        field_mapping: Dict[str, str],
        transforms: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply field mapping to transform source data to target format"""
        result = {}
        
        # Track which transformations were applied
        applied_transforms = set()
        
        # First extract all fields using field mapping
        for target_field, source_info in field_mapping.items():
            if isinstance(source_info, str):
                # Handle JSON path notation
                if '$.' in source_info:
                    extractor = JsonPathExtraction(source_info)
                    result[target_field] = extractor.apply(source_data)
                # Direct field mapping
                elif source_info in source_data:
                    result[target_field] = source_data[source_info]
            elif isinstance(source_info, dict):
                # Nested field mapping
                nested_result = {}
                for nested_target, nested_source in source_info.items():
                    if nested_source in source_data:
                        nested_result[nested_target] = source_data[nested_source]
                result[target_field] = nested_result
        
        # Then apply field-specific transformations
        for field, transform_info in transforms.items():
            # Track that we're applying this transformation
            transform_type = transform_info.get('type')
            applied_transforms.add(f"{field}:{transform_type}")
            
            # Get the field value to transform
            field_parts = field.split('.')
            if len(field_parts) == 1:
                # Simple field reference
                if field in result:
                    value = result[field]
                    transformed_value = self._apply_transform(value, transform_info, source_data)
                    result[field] = transformed_value
            else:
                # Nested field reference (e.g., "location.address")
                current = result
                for part in field_parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                last_part = field_parts[-1]
                if last_part in current:
                    value = current[last_part]
                    transformed_value = self._apply_transform(value, transform_info, source_data)
                    current[last_part] = transformed_value
        
        return result
    
    def _apply_transform(self, value: Any, transform_info: Dict[str, Any], 
                         source_data: Dict[str, Any]) -> Any:
        """Apply a specific transformation to a value"""
        transform_type = transform_info.get('type')
        
        # Use the transformation rule if available
        rule_name = transform_info.get('rule')
        if rule_name and rule_name in self.transformation_rules:
            return self.transformation_rules[rule_name].apply(value, {'source_data': source_data})
        
        # Otherwise use the inline configuration
        if transform_type == 'format':
            format_str = transform_info.get('format', '{}')
            transform = FormatTransformation(format_str)
            return transform.apply(value)
            
        elif transform_type == 'lookup':
            lookup_map = transform_info.get('values', {})
            transform = LookupTransformation(lookup_map)
            return transform.apply(value)
            
        elif transform_type == 'combine':
            fields = transform_info.get('fields', [])
            separator = transform_info.get('separator', ' ')
            values = [source_data.get(f, '') for f in fields]
            transform = CombineTransformation(separator)
            return transform.apply(values)
            
        elif transform_type == 'date':
            source_format = transform_info.get('source_format')
            target_format = transform_info.get('target_format', "%Y-%m-%d")
            transform = DateTimeTransformation(source_format, target_format)
            return transform.apply(value)
            
        elif transform_type == 'number':
            scale = transform_info.get('scale', 1.0)
            digits = transform_info.get('round')
            format_str = transform_info.get('format')
            transform = NumberTransformation(scale, digits, format_str)
            return transform.apply(value)
            
        elif transform_type == 'address':
            output_format = transform_info.get('format', 'single_line')
            transform = AddressNormalization(output_format)
            return transform.apply(value)
            
        elif transform_type == 'ai_enrich':
            enrich_type = transform_info.get('enrichment_type', 'general')
            api_key = transform_info.get('api_key_env')
            transform = AIEnrichment(enrich_type, api_key)
            return transform.apply(value)
            
        # Default: return the original value
        return value
    
    def _apply_global_transforms(self, data: Dict[str, Any], 
                               global_transforms: List[Dict[str, Any]],
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply global transformations to the entire record"""
        result = data.copy()
        
        for transform_info in global_transforms:
            transform_type = transform_info.get('type')
            
            if transform_type == 'rename_fields':
                mappings = transform_info.get('mappings', {})
                for old_name, new_name in mappings.items():
                    if old_name in result:
                        result[new_name] = result.pop(old_name)
                        
            elif transform_type == 'remove_fields':
                fields = transform_info.get('fields', [])
                for field in fields:
                    if field in result:
                        del result[field]
                        
            elif transform_type == 'add_fields':
                fields = transform_info.get('fields', {})
                for field_name, field_value in fields.items():
                    # Evaluate template if string contains placeholders
                    if isinstance(field_value, str) and '{' in field_value:
                        try:
                            field_value = field_value.format(**context, **result)
                        except Exception as e:
                            self.logger.warning(f"Failed to format template {field_value}: {e}")
                    result[field_name] = field_value
                    
            elif transform_type == 'transform_if':
                condition = transform_info.get('condition', {})
                if self._evaluate_condition(condition, result, context):
                    then_actions = transform_info.get('then', [])
                    for action in then_actions:
                        field = action.get('field')
                        transform = action.get('transform', {})
                        if field in result:
                            result[field] = self._apply_transform(
                                result[field], transform, context.get('source_data', {})
                            )
                else:
                    else_actions = transform_info.get('else', [])
                    for action in else_actions:
                        field = action.get('field')
                        transform = action.get('transform', {})
                        if field in result:
                            result[field] = self._apply_transform(
                                result[field], transform, context.get('source_data', {})
                            )
        
        return result
    
    def _evaluate_condition(self, condition: Dict[str, Any], 
                          data: Dict[str, Any], 
                          context: Dict[str, Any]) -> bool:
        """Evaluate a condition for conditional transformations"""
        op = condition.get('op', 'eq')
        
        if 'field' in condition:
            field = condition['field']
            field_value = data.get(field)
            expected = condition.get('value')
            
            if op == 'eq':
                return field_value == expected
            elif op == 'ne':
                return field_value != expected
            elif op == 'gt':
                return field_value > expected
            elif op == 'lt': 
                return field_value < expected
            elif op == 'in':
                return field_value in expected
            elif op == 'contains':
                return expected in field_value
            elif op == 'exists':
                return field in data
        
        elif 'op' == 'and' and 'conditions' in condition:
            return all(self._evaluate_condition(c, data, context) for c in condition['conditions'])
            
        elif 'op' == 'or' and 'conditions' in condition:
            return any(self._evaluate_condition(c, data, context) for c in condition['conditions'])
            
        # Default to True for malformed conditions
        return True
    
    def _get_applied_rules(self, mapping: Dict[str, Any]) -> List[str]:
        """Get a list of transformation rules applied to this record"""
        rules = []
        
        # Add field transforms
        if 'transforms' in mapping:
            for field, transform in mapping['transforms'].items():
                rule_type = transform.get('type', 'unknown')
                rules.append(f"{field}:{rule_type}")
                
        # Add global transforms
        if 'global_transforms' in mapping:
            for transform in mapping['global_transforms']:
                rules.append(f"global:{transform.get('type', 'unknown')}")
                
        return rules

    def _initialize_transformation_rules(self) -> Dict[str, TransformationRule]:
        """Initialize a repository of reusable transformation rules"""
        rules = {}
        
        # Add common address formatting
        rules["standard_address_format"] = AddressNormalization("single_line")
        rules["json_address_format"] = AddressNormalization("json")
        
        # Add date transformations
        rules["standard_date_format"] = DateTimeTransformation(target_format="%Y-%m-%d")
        rules["us_date_format"] = DateTimeTransformation(target_format="%m/%d/%Y")
        rules["timestamp_format"] = DateTimeTransformation(target_format="%Y-%m-%d %H:%M:%S")
        
        # Add currency transformations
        rules["usd_format"] = NumberTransformation(rounding_digits=2, number_format="${:.2f}")
        rules["integer_format"] = NumberTransformation(rounding_digits=0, number_format="{:.0f}")
        rules["percentage_format"] = NumberTransformation(scale_factor=100, number_format="{:.1f}%")
        
        # Add complex transformations
        address_formatter = ComplexTransformation([
            AddressNormalization("json"),
            JsonPathExtraction("$.street"),
            FormatTransformation("{}, {}, {} {}")
        ])
        rules["address_with_city_state"] = address_formatter
        
        return rules
    
    def _determine_target_id(self, change: DetectedChange, mapping: Dict[str, Any]) -> Optional[str]:
        """Determine the target system ID for a changed record"""
        # This would typically involve querying the target system to find
        # corresponding records, or generating a new ID for inserts
        
        # For demo purposes, we'll use a simple mapping based on the source ID
        if change.change_type == ChangeType.INSERT:
            # For inserts, return None to let the target system assign a new ID
            return None
        else:
            # For updates, format the ID according to the mapping configuration
            id_format = mapping.get('id_format', 'PROP-{}')
            return id_format.format(change.record_id)
    
    def _get_default_field_mapping(self) -> Dict[str, Any]:
        """Get default field mapping configuration for PACS to CAMA"""
        return {
            "properties": {
                "target_table": "properties",
                "id_format": "PROP-{}",
                "fields": {
                    "property_id": "property_id",
                    "parcel_id": "parcel_number",
                    "ownership": {
                        "primary_owner": "owner_name",
                        "ownership_type": "Individual"
                    },
                    "location": {
                        "address_line1": "address",
                        "city": "city",
                        "state": "state",
                        "zip": "zip"
                    },
                    "valuation": {
                        "land": "land_value",
                        "improvements": "improvement_value",
                        "total": "total_value",
                        "assessment_date": "last_updated"
                    },
                    "metadata": {
                        "last_sync": "NOW()",
                        "sync_status": "complete"
                    }
                },
                "transforms": {
                    "parcel_id": {
                        "type": "format",
                        "format": "{}"
                    },
                    "valuation.assessment_date": {
                        "type": "format",
                        "format": "{:.10}"
                    }
                }
            },
            "valuations": {
                "target_table": "property_valuations",
                "id_format": "VAL-{}",
                "fields": {
                    "valuation_id": "valuation_id",
                    "property_id": "property_id",
                    "valuation_date": "valuation_date",
                    "land_value": "land_value",
                    "improvement_value": "improvement_value",
                    "total_value": "total_value",
                    "valuation_method": "method",
                    "valuation_type": "type",
                    "assessor_notes": "notes"
                },
                "transforms": {
                    "valuation_date": {
                        "type": "format",
                        "format": "{:.10}"
                    },
                    "valuation_method": {
                        "type": "lookup",
                        "values": {
                            "M": "Market",
                            "C": "Cost",
                            "I": "Income"
                        }
                    }
                }
            }
        }


class ValidationSeverity(Enum):
    """Defines severity levels for validation messages"""
    ERROR = "error"        # Critical issue that prevents sync
    WARNING = "warning"    # Potential issue but allows sync
    INFO = "info"          # Informational message only


class ValidationRule:
    """Base class for all validation rules"""
    def __init__(self, field_path: str, severity: ValidationSeverity = ValidationSeverity.ERROR,
                 error_message: str = None):
        self.field_path = field_path
        self.severity = severity
        self.error_message = error_message
        
    def validate(self, data: Dict[str, Any], accessor: Callable) -> List[Dict[str, Any]]:
        """
        Validate data against this rule
        
        Args:
            data: The record data to validate
            accessor: Function to access nested fields
            
        Returns:
            List of validation issues (empty if validation passes)
        """
        raise NotImplementedError("Subclasses must implement validate()")
    
    def get_message(self, value: Any = None) -> str:
        """Get the error message for this rule"""
        if self.error_message:
            try:
                return self.error_message.format(field=self.field_path, value=value)
            except:
                return self.error_message
        return f"Validation failed for field '{self.field_path}'"
    
    def describe(self) -> str:
        """Describe this rule"""
        return "Base validation rule"


class RequiredFieldRule(ValidationRule):
    """Rule that requires a field to be present and non-None"""
    def validate(self, data: Dict[str, Any], accessor: Callable) -> List[Dict[str, Any]]:
        value = accessor(data, self.field_path)
        
        if value is None:
            return [{
                "field": self.field_path,
                "severity": self.severity.value,
                "message": self.get_message(),
                "rule_type": "required"
            }]
        return []
    
    def get_message(self, value: Any = None) -> str:
        if self.error_message:
            return super().get_message(value)
        return f"Required field '{self.field_path}' is missing"
    
    def describe(self) -> str:
        return f"Field '{self.field_path}' is required"


class TypeValidationRule(ValidationRule):
    """Rule that validates the type of a field"""
    def __init__(self, field_path: str, expected_type: str, 
                 severity: ValidationSeverity = ValidationSeverity.ERROR,
                 error_message: str = None):
        super().__init__(field_path, severity, error_message)
        self.expected_type = expected_type
        
    def validate(self, data: Dict[str, Any], accessor: Callable) -> List[Dict[str, Any]]:
        value = accessor(data, self.field_path)
        
        # Skip validation if value is None
        if value is None:
            return []
            
        if not self._check_type(value, self.expected_type):
            return [{
                "field": self.field_path,
                "severity": self.severity.value,
                "message": self.get_message(value),
                "rule_type": "type",
                "expected_type": self.expected_type,
                "actual_value": str(value)
            }]
        return []
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if a value matches the expected type"""
        if expected_type == 'string':
            return isinstance(value, str)
        elif expected_type == 'integer':
            return isinstance(value, int)
        elif expected_type == 'number':
            return isinstance(value, (int, float))
        elif expected_type == 'boolean':
            return isinstance(value, bool)
        elif expected_type == 'object':
            return isinstance(value, dict)
        elif expected_type == 'array':
            return isinstance(value, (list, tuple))
        elif expected_type == 'date':
            # Simple date format check, would be more robust in production
            if not isinstance(value, str):
                return False
            try:
                return bool(re.match(r'^\d{4}-\d{2}-\d{2}', value))
            except:
                return False
        else:
            return True  # Unknown type, assume valid
    
    def get_message(self, value: Any = None) -> str:
        if self.error_message:
            return super().get_message(value)
        return f"Field '{self.field_path}' has wrong type. Expected {self.expected_type}"
    
    def describe(self) -> str:
        return f"Field '{self.field_path}' must be of type {self.expected_type}"


class RangeValidationRule(ValidationRule):
    """Rule that validates numeric values are within a specified range"""
    def __init__(self, field_path: str, min_value: float = None, max_value: float = None,
                 severity: ValidationSeverity = ValidationSeverity.ERROR,
                 error_message: str = None):
        super().__init__(field_path, severity, error_message)
        self.min_value = min_value
        self.max_value = max_value
        
    def validate(self, data: Dict[str, Any], accessor: Callable) -> List[Dict[str, Any]]:
        value = accessor(data, self.field_path)
        
        # Skip validation if value is None
        if value is None:
            return []
        
        try:
            # Convert to numeric if needed
            if not isinstance(value, (int, float)):
                value = float(value)
                
            if self.min_value is not None and value < self.min_value:
                return [{
                    "field": self.field_path,
                    "severity": self.severity.value,
                    "message": self.get_message(value),
                    "rule_type": "range",
                    "constraint": "min",
                    "threshold": self.min_value,
                    "actual_value": value
                }]
                
            if self.max_value is not None and value > self.max_value:
                return [{
                    "field": self.field_path,
                    "severity": self.severity.value,
                    "message": self.get_message(value),
                    "rule_type": "range",
                    "constraint": "max",
                    "threshold": self.max_value,
                    "actual_value": value
                }]
        except (ValueError, TypeError):
            # If value can't be converted to a number, return a type error
            return [{
                "field": self.field_path,
                "severity": self.severity.value,
                "message": f"Field '{self.field_path}' must be numeric for range validation",
                "rule_type": "type_conversion",
                "actual_value": str(value)
            }]
            
        return []
    
    def get_message(self, value: Any = None) -> str:
        if self.error_message:
            return super().get_message(value)
            
        if self.min_value is not None and self.max_value is not None:
            return f"Field '{self.field_path}' value must be between {self.min_value} and {self.max_value}"
        elif self.min_value is not None:
            return f"Field '{self.field_path}' value must be at least {self.min_value}"
        elif self.max_value is not None:
            return f"Field '{self.field_path}' value must be at most {self.max_value}"
        else:
            return f"Range validation failed for field '{self.field_path}'"
    
    def describe(self) -> str:
        if self.min_value is not None and self.max_value is not None:
            return f"Field '{self.field_path}' must be between {self.min_value} and {self.max_value}"
        elif self.min_value is not None:
            return f"Field '{self.field_path}' must be >= {self.min_value}"
        elif self.max_value is not None:
            return f"Field '{self.field_path}' must be <= {self.max_value}"
        else:
            return f"Range validation for '{self.field_path}'"


class LengthValidationRule(ValidationRule):
    """Rule that validates string length is within a specified range"""
    def __init__(self, field_path: str, min_length: int = None, max_length: int = None,
                 severity: ValidationSeverity = ValidationSeverity.ERROR,
                 error_message: str = None):
        super().__init__(field_path, severity, error_message)
        self.min_length = min_length
        self.max_length = max_length
        
    def validate(self, data: Dict[str, Any], accessor: Callable) -> List[Dict[str, Any]]:
        value = accessor(data, self.field_path)
        
        # Skip validation if value is None
        if value is None:
            return []
        
        # Convert to string if needed
        str_value = str(value)
        length = len(str_value)
        
        if self.min_length is not None and length < self.min_length:
            return [{
                "field": self.field_path,
                "severity": self.severity.value,
                "message": self.get_message(value),
                "rule_type": "length",
                "constraint": "min_length",
                "threshold": self.min_length,
                "actual_length": length
            }]
            
        if self.max_length is not None and length > self.max_length:
            return [{
                "field": self.field_path,
                "severity": self.severity.value,
                "message": self.get_message(value),
                "rule_type": "length",
                "constraint": "max_length",
                "threshold": self.max_length,
                "actual_length": length
            }]
            
        return []
    
    def get_message(self, value: Any = None) -> str:
        if self.error_message:
            return super().get_message(value)
            
        length = len(str(value)) if value is not None else 0
        
        if self.min_length is not None and self.max_length is not None:
            return f"Field '{self.field_path}' length must be between {self.min_length} and {self.max_length} characters (currently {length})"
        elif self.min_length is not None:
            return f"Field '{self.field_path}' length must be at least {self.min_length} characters (currently {length})"
        elif self.max_length is not None:
            return f"Field '{self.field_path}' length must be at most {self.max_length} characters (currently {length})"
        else:
            return f"Length validation failed for field '{self.field_path}'"
    
    def describe(self) -> str:
        if self.min_length is not None and self.max_length is not None:
            return f"Field '{self.field_path}' length must be between {self.min_length} and {self.max_length}"
        elif self.min_length is not None:
            return f"Field '{self.field_path}' length must be >= {self.min_length}"
        elif self.max_length is not None:
            return f"Field '{self.field_path}' length must be <= {self.max_length}"
        else:
            return f"Length validation for '{self.field_path}'"


class PatternValidationRule(ValidationRule):
    """Rule that validates string values match a regular expression pattern"""
    def __init__(self, field_path: str, pattern: str,
                 severity: ValidationSeverity = ValidationSeverity.ERROR,
                 error_message: str = None):
        super().__init__(field_path, severity, error_message)
        self.pattern = pattern
        self._compiled_pattern = re.compile(pattern)
        
    def validate(self, data: Dict[str, Any], accessor: Callable) -> List[Dict[str, Any]]:
        value = accessor(data, self.field_path)
        
        # Skip validation if value is None
        if value is None:
            return []
        
        # Convert to string if needed
        str_value = str(value)
        
        if not self._compiled_pattern.match(str_value):
            return [{
                "field": self.field_path,
                "severity": self.severity.value,
                "message": self.get_message(value),
                "rule_type": "pattern",
                "pattern": self.pattern,
                "actual_value": str_value
            }]
            
        return []
    
    def get_message(self, value: Any = None) -> str:
        if self.error_message:
            return super().get_message(value)
        return f"Field '{self.field_path}' value does not match required pattern"
    
    def describe(self) -> str:
        return f"Field '{self.field_path}' must match pattern: {self.pattern}"


class CrossFieldValidationRule(ValidationRule):
    """Rule that validates relationships between multiple fields"""
    def __init__(self, field_path: str, related_field_path: str, relation_type: str,
                 severity: ValidationSeverity = ValidationSeverity.ERROR,
                 error_message: str = None):
        super().__init__(field_path, severity, error_message)
        self.related_field_path = related_field_path
        self.relation_type = relation_type
        
    def validate(self, data: Dict[str, Any], accessor: Callable) -> List[Dict[str, Any]]:
        value1 = accessor(data, self.field_path)
        value2 = accessor(data, self.related_field_path)
        
        # Skip validation if either value is None
        if value1 is None or value2 is None:
            return []
        
        valid = False
        
        if self.relation_type == 'eq':
            valid = value1 == value2
        elif self.relation_type == 'ne':
            valid = value1 != value2
        elif self.relation_type == 'gt':
            try:
                valid = float(value1) > float(value2)
            except (ValueError, TypeError):
                return [{
                    "field": self.field_path,
                    "related_field": self.related_field_path,
                    "severity": self.severity.value,
                    "message": f"Fields must be numeric for '{self.relation_type}' comparison",
                    "rule_type": "cross_field",
                    "values": {self.field_path: str(value1), self.related_field_path: str(value2)}
                }]
        elif self.relation_type == 'ge':
            try:
                valid = float(value1) >= float(value2)
            except (ValueError, TypeError):
                return [{
                    "field": self.field_path,
                    "related_field": self.related_field_path,
                    "severity": self.severity.value,
                    "message": f"Fields must be numeric for '{self.relation_type}' comparison",
                    "rule_type": "cross_field",
                    "values": {self.field_path: str(value1), self.related_field_path: str(value2)}
                }]
        elif self.relation_type == 'lt':
            try:
                valid = float(value1) < float(value2)
            except (ValueError, TypeError):
                return [{
                    "field": self.field_path,
                    "related_field": self.related_field_path,
                    "severity": self.severity.value,
                    "message": f"Fields must be numeric for '{self.relation_type}' comparison",
                    "rule_type": "cross_field",
                    "values": {self.field_path: str(value1), self.related_field_path: str(value2)}
                }]
        elif self.relation_type == 'le':
            try:
                valid = float(value1) <= float(value2)
            except (ValueError, TypeError):
                return [{
                    "field": self.field_path,
                    "related_field": self.related_field_path,
                    "severity": self.severity.value,
                    "message": f"Fields must be numeric for '{self.relation_type}' comparison",
                    "rule_type": "cross_field",
                    "values": {self.field_path: str(value1), self.related_field_path: str(value2)}
                }]
        elif self.relation_type == 'contains':
            valid = str(value2) in str(value1)
        elif self.relation_type == 'starts_with':
            valid = str(value1).startswith(str(value2))
        elif self.relation_type == 'ends_with':
            valid = str(value1).endswith(str(value2))
            
        if not valid:
            return [{
                "field": self.field_path,
                "related_field": self.related_field_path,
                "severity": self.severity.value,
                "message": self.get_message(value1),
                "rule_type": "cross_field",
                "relation": self.relation_type,
                "values": {self.field_path: str(value1), self.related_field_path: str(value2)}
            }]
            
        return []
    
    def get_message(self, value: Any = None) -> str:
        if self.error_message:
            return super().get_message(value)
            
        relation_desc = {
            'eq': 'equal to',
            'ne': 'not equal to',
            'gt': 'greater than',
            'ge': 'greater than or equal to',
            'lt': 'less than',
            'le': 'less than or equal to',
            'contains': 'containing',
            'starts_with': 'starting with',
            'ends_with': 'ending with'
        }.get(self.relation_type, self.relation_type)
        
        return f"Field '{self.field_path}' must be {relation_desc} '{self.related_field_path}'"
    
    def describe(self) -> str:
        relation_desc = {
            'eq': '==',
            'ne': '!=',
            'gt': '>',
            'ge': '>=',
            'lt': '<',
            'le': '<=',
            'contains': 'contains',
            'starts_with': 'starts with',
            'ends_with': 'ends with'
        }.get(self.relation_type, self.relation_type)
        
        return f"Field '{self.field_path}' {relation_desc} '{self.related_field_path}'"


class CustomValidationRule(ValidationRule):
    """Rule that uses a custom validation function"""
    def __init__(self, field_path: str, validation_func: Callable,
                 severity: ValidationSeverity = ValidationSeverity.ERROR,
                 error_message: str = None, description: str = None):
        super().__init__(field_path, severity, error_message)
        self.validation_func = validation_func
        self.description = description or "Custom validation rule"
        
    def validate(self, data: Dict[str, Any], accessor: Callable) -> List[Dict[str, Any]]:
        value = accessor(data, self.field_path)
        
        try:
            # Call the custom validation function
            result = self.validation_func(value, data)
            
            # If result is boolean, interpret True as valid
            if isinstance(result, bool):
                if result:
                    return []
                else:
                    return [{
                        "field": self.field_path,
                        "severity": self.severity.value,
                        "message": self.get_message(value),
                        "rule_type": "custom",
                        "description": self.description
                    }]
            
            # If result is a string, interpret as error message
            elif isinstance(result, str):
                if not result:
                    return []
                else:
                    return [{
                        "field": self.field_path,
                        "severity": self.severity.value,
                        "message": result,
                        "rule_type": "custom",
                        "description": self.description
                    }]
            
            # If result is a list, return it directly
            elif isinstance(result, list):
                return result
            
            # Otherwise assume validation passed
            return []
            
        except Exception as e:
            # If validation function raises an exception, return that as an error
            return [{
                "field": self.field_path,
                "severity": self.severity.value,
                "message": f"Validation error: {str(e)}",
                "rule_type": "custom",
                "description": self.description,
                "exception": str(e)
            }]
    
    def describe(self) -> str:
        return self.description


class RuleSet:
    """A collection of validation rules for a specific entity type"""
    def __init__(self, name: str, rules: List[ValidationRule] = None):
        self.name = name
        self.rules = rules or []
        
    def add_rule(self, rule: ValidationRule) -> 'RuleSet':
        """Add a rule to this rule set"""
        self.rules.append(rule)
        return self
        
    def validate(self, data: Dict[str, Any], accessor: Callable) -> List[Dict[str, Any]]:
        """Validate data against all rules in this rule set"""
        results = []
        for rule in self.rules:
            results.extend(rule.validate(data, accessor))
        return results


class DataValidator:
    """
    Enhanced validator with composable validation rules, cross-field validations,
    and data quality validation metrics.
    """
    def __init__(self, validation_rules: Dict[str, Any] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize from legacy rule format if provided
        if validation_rules:
            self.rule_sets = self._convert_legacy_rules(validation_rules)
        else:
            # Initialize modern rule sets
            self.rule_sets = self._create_default_rule_sets()
        
        # Data quality metrics
        self.data_quality_metrics = {
            "total_records_validated": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "error_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "validation_rate": 0,  # Records per second
            "field_error_distribution": {},
            "severity_distribution": {
                "error": 0,
                "warning": 0,
                "info": 0
            },
            "last_validation_timestamp": None
        }
        
    def _convert_legacy_rules(self, legacy_rules: Dict[str, Any]) -> Dict[str, RuleSet]:
        """Convert legacy validation rules format to modern rule sets"""
        rule_sets = {}
        
        for table, table_rules in legacy_rules.items():
            rule_set = RuleSet(name=table)
            
            for field, field_rules in table_rules.items():
                if "required" in field_rules and field_rules["required"]:
                    rule_set.add_rule(RequiredFieldRule(field_path=field))
                    
                if "type" in field_rules:
                    rule_set.add_rule(TypeValidationRule(
                        field_path=field, 
                        expected_type=field_rules["type"]
                    ))
                    
                if "min_length" in field_rules or "max_length" in field_rules:
                    rule_set.add_rule(LengthValidationRule(
                        field_path=field, 
                        min_length=field_rules.get("min_length"),
                        max_length=field_rules.get("max_length")
                    ))
                    
                if "pattern" in field_rules:
                    rule_set.add_rule(PatternValidationRule(
                        field_path=field, 
                        pattern=field_rules["pattern"]
                    ))
                    
                if "min_value" in field_rules or "max_value" in field_rules:
                    rule_set.add_rule(RangeValidationRule(
                        field_path=field, 
                        min_value=field_rules.get("min_value"),
                        max_value=field_rules.get("max_value")
                    ))
                
            rule_sets[table] = rule_set
            
        return rule_sets
    
    def _create_default_rule_sets(self) -> Dict[str, RuleSet]:
        """Create default rule sets for common tables"""
        rule_sets = {}
        
        # Property rule set
        property_rules = RuleSet(name="properties")
        property_rules.add_rule(RequiredFieldRule("parcel_id"))
        property_rules.add_rule(TypeValidationRule("parcel_id", "string"))
        property_rules.add_rule(RequiredFieldRule("ownership.primary_owner"))
        property_rules.add_rule(LengthValidationRule("ownership.primary_owner", min_length=2, max_length=100))
        property_rules.add_rule(TypeValidationRule("valuation.land", "number"))
        property_rules.add_rule(TypeValidationRule("valuation.improvements", "number"))
        property_rules.add_rule(TypeValidationRule("valuation.total", "number"))
        property_rules.add_rule(CrossFieldValidationRule(
            "valuation.total", "valuation.land", "gt", 
            error_message="Total valuation must be greater than land value"
        ))
        rule_sets["properties"] = property_rules
        
        # Assessment rule set
        assessment_rules = RuleSet(name="assessments")
        assessment_rules.add_rule(RequiredFieldRule("property_id"))
        assessment_rules.add_rule(RequiredFieldRule("assessment_date"))
        assessment_rules.add_rule(TypeValidationRule("assessment_date", "date"))
        assessment_rules.add_rule(RequiredFieldRule("assessed_value"))
        assessment_rules.add_rule(TypeValidationRule("assessed_value", "number"))
        assessment_rules.add_rule(RangeValidationRule("assessed_value", min_value=0))
        rule_sets["assessments"] = assessment_rules
        
        # Person rule set
        person_rules = RuleSet(name="persons")
        person_rules.add_rule(RequiredFieldRule("full_name"))
        person_rules.add_rule(LengthValidationRule("full_name", min_length=2, max_length=100))
        person_rules.add_rule(TypeValidationRule("email", "string"))
        person_rules.add_rule(PatternValidationRule(
            "email", 
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', 
            severity=ValidationSeverity.WARNING,
            error_message="Email format appears to be invalid"
        ))
        rule_sets["persons"] = person_rules
        
        return rule_sets
    
    def add_rule_set(self, table_name: str, rule_set: RuleSet) -> None:
        """Add a rule set for a table"""
        self.rule_sets[table_name] = rule_set
        
    def add_rule(self, table_name: str, rule: ValidationRule) -> None:
        """Add a rule to an existing rule set, or create a new one"""
        if table_name not in self.rule_sets:
            self.rule_sets[table_name] = RuleSet(name=table_name)
        self.rule_sets[table_name].add_rule(rule)
        
    def _get_accessor_function(self) -> Callable:
        """Get a function that can access nested fields in data"""
        def accessor(data: Dict[str, Any], field_path: str) -> Any:
            """Access a nested field in data using dot notation"""
            if not field_path:
                return None
                
            parts = field_path.split('.')
            current = data
            
            for part in parts:
                if current is None:
                    return None
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
                    
            return current
            
        return accessor
    
    def validate_single(self, record: TransformedRecord) -> ValidationResult:
        """
        Validate a single transformed record with enhanced error reporting.
        
        Args:
            record: A transformed record to validate
            
        Returns:
            ValidationResult for the record
        """
        start_time = time.time()
        accessor = self._get_accessor_function()
        table_name = record.target_table
        
        # Skip validation if no rules exist for this table
        if table_name not in self.rule_sets:
            # Create a default passing validation result
            result = ValidationResult(
                record=record,
                is_valid=True,
                info=[f"No validation rules defined for table '{table_name}'"]
            )
            
            # Update metrics
            self.data_quality_metrics["total_records_validated"] += 1
            self.data_quality_metrics["valid_records"] += 1
            
            return result
        
        # Get the rule set for this table
        rule_set = self.rule_sets[table_name]
        
        # Validate against all rules in the rule set
        validation_issues = rule_set.validate(record.data, accessor)
        
        # Process validation issues by severity
        errors = []
        warnings = []
        infos = []
        
        for issue in validation_issues:
            severity = issue.get("severity", "error")
            message = issue.get("message", "Unknown validation error")
            
            if severity == ValidationSeverity.ERROR.value:
                errors.append(message)
                self.data_quality_metrics["severity_distribution"]["error"] += 1
            elif severity == ValidationSeverity.WARNING.value:
                warnings.append(message)
                self.data_quality_metrics["severity_distribution"]["warning"] += 1
            elif severity == ValidationSeverity.INFO.value:
                infos.append(message)
                self.data_quality_metrics["severity_distribution"]["info"] += 1
            
            # Track field error distribution
            field = issue.get("field", "unknown")
            if field not in self.data_quality_metrics["field_error_distribution"]:
                self.data_quality_metrics["field_error_distribution"][field] = 0
            self.data_quality_metrics["field_error_distribution"][field] += 1
        
        # Determine if record is valid (no errors)
        is_valid = len(errors) == 0
        
        # Create validation metrics
        metrics = {
            "completion_percentage": self._calculate_completion_percentage(record.data),
            "field_count": len(record.data) if isinstance(record.data, dict) else 0,
            "validation_time_ms": int((time.time() - start_time) * 1000)
        }
        
        # Create validation result
        validation_result = ValidationResult(
            record=record,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            info=infos,
            metrics=metrics
        )
        
        # Update metrics
        self.data_quality_metrics["total_records_validated"] += 1
        if is_valid:
            self.data_quality_metrics["valid_records"] += 1
        else:
            self.data_quality_metrics["invalid_records"] += 1
        self.data_quality_metrics["error_count"] += len(errors)
        self.data_quality_metrics["warning_count"] += len(warnings)
        self.data_quality_metrics["info_count"] += len(infos)
        
        self.data_quality_metrics["last_validation_timestamp"] = datetime.datetime.now().isoformat()
        
        return validation_result
    
    def validate(self, records: List[TransformedRecord]) -> List[ValidationResult]:
        """
        Validate a list of transformed records.
        
        Args:
            records: List of transformed records to validate
            
        Returns:
            List of validation results
        """
        start_time = time.time()
        results = []
        
        # Validate each record individually
        for record in records:
            results.append(self.validate_single(record))
        
        # Update validation rate
        elapsed_time = time.time() - start_time
        if elapsed_time > 0:
            self.data_quality_metrics["validation_rate"] = len(records) / elapsed_time
        
        self.data_quality_metrics["last_validation_timestamp"] = datetime.datetime.now().isoformat()
        
        return results
        
    def validate_parallel(
        self, 
        records: List[TransformedRecord], 
        max_workers: int = None,
        batch_size: int = 50
    ) -> List[ValidationResult]:
        """
        Validate records in parallel using a thread pool for improved performance.
        
        Args:
            records: List of TransformedRecord objects to validate
            max_workers: Maximum number of worker threads (defaults to CPU count * 5)
            batch_size: Size of batches to process in parallel
            
        Returns:
            List of ValidationResult objects with validation outcomes
        """
        if not records:
            return []
            
        if max_workers is None:
            max_workers = min(32, multiprocessing.cpu_count() * 5)
            
        self.logger.info(
            f"Validating {len(records)} records in parallel "
            f"with {max_workers} workers and batch size {batch_size}"
        )
        
        start_time = time.time()
        all_results = []
        
        # Process in batches to avoid creating too many small tasks
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all records in this batch for validation
                future_to_record = {
                    executor.submit(self.validate_single, record): record
                    for record in batch
                }
                
                # Collect results as they complete
                batch_results = []
                for future in concurrent.futures.as_completed(future_to_record):
                    try:
                        result = future.result()
                        batch_results.append(result)
                    except Exception as e:
                        record = future_to_record[future]
                        self.logger.error(f"Validation error for record {record.source_id}: {str(e)}")
                        # Create an error result
                        batch_results.append(ValidationResult(
                            record=record,
                            is_valid=False,
                            errors=[f"Validation exception: {str(e)}"]
                        ))
                
                all_results.extend(batch_results)
                
        elapsed_time = time.time() - start_time
        
        # Update validation rate and metrics
        if elapsed_time > 0:
            validation_rate = len(records) / elapsed_time
            self.data_quality_metrics["validation_rate"] = validation_rate
            
        valid_count = sum(1 for r in all_results if r.is_valid)
        self.data_quality_metrics["total_records_validated"] += len(records)
        self.data_quality_metrics["valid_records"] += valid_count
        self.data_quality_metrics["invalid_records"] += (len(records) - valid_count)
        self.data_quality_metrics["last_validation_timestamp"] = datetime.datetime.now().isoformat()
        
        self.logger.info(
            f"Parallel validation complete: {valid_count}/{len(all_results)} records valid "
            f"in {elapsed_time:.2f}s ({len(records)/max(0.001, elapsed_time):.1f} records/sec)"
        )
        
        return all_results
    
    def _calculate_completion_percentage(self, data: Dict[str, Any]) -> float:
        """Calculate completion percentage of a record (non-null fields)"""
        if not isinstance(data, dict) or not data:
            return 0.0
        
        total_fields = 0
        non_null_fields = 0
        
        def count_fields(obj, prefix=""):
            nonlocal total_fields, non_null_fields
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    field_path = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, (dict, list)):
                        count_fields(value, field_path)
                    else:
                        total_fields += 1
                        if value is not None:
                            non_null_fields += 1
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    field_path = f"{prefix}[{i}]"
                    if isinstance(item, (dict, list)):
                        count_fields(item, field_path)
                    else:
                        total_fields += 1
                        if item is not None:
                            non_null_fields += 1
        
        count_fields(data)
        
        if total_fields == 0:
            return 0.0
            
        return (non_null_fields / total_fields) * 100.0
    
    def get_validation_metrics(self) -> Dict[str, Any]:
        """Get validation metrics"""
        return self.data_quality_metrics
    
    def reset_metrics(self) -> None:
        """Reset validation metrics"""
        self.data_quality_metrics = {
            "total_records_validated": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "error_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "validation_rate": 0,
            "field_error_distribution": {},
            "severity_distribution": {
                "error": 0,
                "warning": 0,
                "info": 0
            },
            "last_validation_timestamp": None
        }
        
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if a value matches the expected type"""
        if expected_type == 'string':
            return isinstance(value, str)
        elif expected_type == 'integer':
            return isinstance(value, int)
        elif expected_type == 'number':
            return isinstance(value, (int, float))
        elif expected_type == 'boolean':
            return isinstance(value, bool)
        elif expected_type == 'object':
            return isinstance(value, dict)
        elif expected_type == 'array':
            return isinstance(value, (list, tuple))
        elif expected_type == 'date':
            # Simple date format check, would be more robust in production
            if not isinstance(value, str):
                return False
            try:
                return bool(re.match(r'^\d{4}-\d{2}-\d{2}', value))
            except:
                return False
        else:
            return True  # Unknown type, assume valid
    
    def _get_default_validation_rules(self) -> Dict[str, Any]:
        """Get default validation rules for CAMA system"""
        return {
            "properties": {
                "required_fields": [
                    "parcel_id", 
                    "ownership.primary_owner",
                    "location.address_line1",
                    "valuation.total"
                ],
                "field_types": {
                    "property_id": "string",
                    "parcel_id": "string",
                    "ownership": "object",
                    "location": "object",
                    "valuation": "object",
                    "valuation.land": "number",
                    "valuation.improvements": "number",
                    "valuation.total": "number",
                    "valuation.assessment_date": "date"
                },
                "constraints": {
                    "parcel_id": {
                        "min_length": 5,
                        "max_length": 20,
                        "pattern": r"^[\w\-]+"
                    },
                    "ownership.primary_owner": {
                        "min_length": 2,
                        "max_length": 100
                    },
                    "location.address_line1": {
                        "min_length": 5,
                        "max_length": 100
                    },
                    "location.zip": {
                        "pattern": r"^\d{5}(-\d{4})?$"
                    },
                    "valuation.land": {
                        "min": 0
                    },
                    "valuation.improvements": {
                        "min": 0
                    },
                    "valuation.total": {
                        "min": 0
                    }
                },
                "warnings": {
                    "valuation.total": {
                        "min": 1000,
                        "max": 10000000
                    }
                }
            },
            "property_valuations": {
                "required_fields": [
                    "property_id",
                    "valuation_date",
                    "total_value"
                ],
                "field_types": {
                    "valuation_id": "string",
                    "property_id": "string",
                    "valuation_date": "date",
                    "land_value": "number",
                    "improvement_value": "number",
                    "total_value": "number",
                    "valuation_method": "string",
                    "assessor_notes": "string"
                },
                "constraints": {
                    "land_value": {
                        "min": 0
                    },
                    "improvement_value": {
                        "min": 0
                    },
                    "total_value": {
                        "min": 0
                    },
                    "valuation_method": {
                        "pattern": r"^(Market|Cost|Income)$"
                    }
                },
                "warnings": {
                    "total_value": {
                        "min": 1000,
                        "max": 10000000
                    }
                }
            }
        }


class ConflictResolutionHandler:
    """
    Advanced conflict resolution handler for managing complex data conflicts
    between source and target systems.
    """
    def __init__(self, source_connection: DatabaseConnection, target_connection: DatabaseConnection):
        self.source_connection = source_connection
        self.target_connection = target_connection
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Conflict resolution strategies
        self.resolution_strategies = {
            "last_updated_wins": self._resolve_by_last_updated,
            "source_wins": self._resolve_by_source_priority,
            "target_wins": self._resolve_by_target_priority,
            "merge": self._resolve_by_field_merge,
            "manual": self._mark_for_manual_resolution
        }
        
        # Default resolution strategy by table
        self.default_strategies = {
            "properties": "last_updated_wins",
            "valuations": "last_updated_wins",
            "assessors": "source_wins",
            "appeals": "target_wins",
            "attachments": "source_wins"
        }
        
        # Field-level resolution configurations
        self.field_resolution = {
            "properties": {
                "owner_name": "source_wins",  # Source is system of record for owner info
                "address": "source_wins",
                "land_value": "merge",  # Merge financial data if different
                "improvement_value": "merge",
                "total_value": "merge"
            },
            "valuations": {
                "valuation_date": "last_updated_wins",
                "value_amount": "merge",
                "comments": "merge_text"  # Special handler for text fields
            }
        }
        
        # Track conflicts history
        self.conflict_history = []
        
    def detect_conflicts(self, change: DetectedChange) -> Dict[str, Any]:
        """
        Detect potential conflicts between source and target data
        
        Args:
            change: Detected change from source
            
        Returns:
            Dictionary with conflict information if found
        """
        if change.change_type != ChangeType.UPDATE:
            # Only updates can have conflicts
            return None
            
        # Get current data in target system
        table_name = change.source_table
        record_id = change.record_id
        
        # Format target ID based on table convention 
        target_id = f"PROP-{record_id}" if table_name == "properties" else record_id
        
        query = f"""
        SELECT * FROM {table_name} 
        WHERE property_id = :target_id
        """
        params = {"target_id": target_id}
        
        target_records = self.target_connection.execute_query(query, params)
        
        if not target_records:
            # No existing record in target, no conflict
            return None
            
        # Compare source and target data to identify conflicts
        target_data = target_records[0]
        
        # Track conflicting fields
        conflicts = {
            "has_conflicts": False,
            "conflict_fields": [],
            "conflict_details": {},
            "source_data": change.new_data,
            "target_data": target_data,
            "resolution_strategy": self.get_resolution_strategy(table_name),
            "created_at": datetime.datetime.now().isoformat()
        }
        
        # Compare fields common to both
        for field, source_value in change.new_data.items():
            if field in target_data and self._is_conflicting_value(source_value, target_data[field], field):
                conflicts["has_conflicts"] = True
                conflicts["conflict_fields"].append(field)
                
                # Add detailed information about the conflict
                conflicts["conflict_details"][field] = {
                    "source_value": source_value,
                    "target_value": target_data[field],
                    "field_resolution": self.get_field_resolution_strategy(table_name, field),
                    "severity": self._determine_conflict_severity(field, source_value, target_data[field])
                }
                
        return conflicts if conflicts["has_conflicts"] else None
    
    def resolve_conflicts(self, conflicts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve detected conflicts based on strategies
        
        Args:
            conflicts: Dictionary with conflict information
            
        Returns:
            Dictionary with resolution results
        """
        if not conflicts or not conflicts["has_conflicts"]:
            return {"has_conflicts": False, "resolved": True, "data": conflicts["source_data"]}
            
        table_name = conflicts.get("table_name", "unknown")
        resolution_results = {
            "has_conflicts": True,
            "resolved": False,
            "resolution_strategy": conflicts["resolution_strategy"],
            "source_data": conflicts["source_data"],
            "target_data": conflicts["target_data"],
            "resolved_data": {},
            "unresolved_fields": []
        }
        
        # Apply resolution strategy to each conflicting field
        for field in conflicts["conflict_fields"]:
            field_details = conflicts["conflict_details"][field]
            field_strategy = field_details["field_resolution"]
            
            # Apply the appropriate resolution strategy
            if field_strategy in self.resolution_strategies:
                resolved_value = self.resolution_strategies[field_strategy](
                    field,
                    field_details["source_value"],
                    field_details["target_value"]
                )
                
                resolution_results["resolved_data"][field] = resolved_value
            else:
                # Mark field as unresolved
                resolution_results["unresolved_fields"].append(field)
                
        # Copy non-conflicting fields from source
        for field, value in conflicts["source_data"].items():
            if field not in resolution_results["resolved_data"] and field not in resolution_results["unresolved_fields"]:
                resolution_results["resolved_data"][field] = value
                
        # Set resolution status
        resolution_results["resolved"] = len(resolution_results["unresolved_fields"]) == 0
        
        # Add to conflict history
        self._add_to_conflict_history(conflicts, resolution_results)
        
        return resolution_results
    
    def get_resolution_strategy(self, table_name: str) -> str:
        """Get the default resolution strategy for a table"""
        return self.default_strategies.get(table_name, "last_updated_wins")
    
    def get_field_resolution_strategy(self, table_name: str, field_name: str) -> str:
        """Get the resolution strategy for a specific field"""
        if table_name in self.field_resolution and field_name in self.field_resolution[table_name]:
            return self.field_resolution[table_name][field_name]
        return self.get_resolution_strategy(table_name)
    
    def get_conflict_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get the conflict resolution history"""
        return self.conflict_history[-limit:] if limit > 0 else self.conflict_history
    
    def _is_conflicting_value(self, source_value: Any, target_value: Any, field_name: str) -> bool:
        """
        Determine if two values are in conflict
        
        Args:
            source_value: Value from source system
            target_value: Value from target system
            field_name: Name of the field being compared
            
        Returns:
            True if values are in conflict, False otherwise
        """
        # Handle None/null values
        if source_value is None and target_value is None:
            return False
            
        # Special case for numeric values - allow small differences
        if isinstance(source_value, (int, float)) and isinstance(target_value, (int, float)):
            # For financial fields, consider a 1% difference as non-conflicting
            if "value" in field_name.lower() or "amount" in field_name.lower():
                if source_value == 0 and target_value == 0:
                    return False
                    
                if source_value == 0:
                    percent_diff = abs(target_value) * 100
                elif target_value == 0:
                    percent_diff = abs(source_value) * 100
                else:
                    percent_diff = abs(source_value - target_value) / max(abs(source_value), abs(target_value)) * 100
                    
                return percent_diff > 1.0  # More than 1% difference is a conflict
                
        # Handle timestamps - allow small differences
        if "date" in field_name.lower() or "time" in field_name.lower():
            try:
                source_dt = None
                target_dt = None
                
                if isinstance(source_value, str):
                    source_dt = datetime.datetime.fromisoformat(source_value.replace('Z', '+00:00'))
                if isinstance(target_value, str):
                    target_dt = datetime.datetime.fromisoformat(target_value.replace('Z', '+00:00'))
                    
                if source_dt and target_dt:
                    diff_seconds = abs((source_dt - target_dt).total_seconds())
                    return diff_seconds > 60  # More than 1 minute difference is a conflict
            except (ValueError, TypeError):
                pass
                
        # Default comparison
        return source_value != target_value
    
    def _determine_conflict_severity(self, field_name: str, source_value: Any, target_value: Any) -> str:
        """Determine the severity of a conflict"""
        # Critical fields with high severity conflicts
        critical_fields = ["property_id", "parcel_number", "parcel_id", "owner_name"]
        financial_fields = ["land_value", "improvement_value", "total_value", "value_amount", "assessed_value"]
        
        if field_name in critical_fields:
            return "high"
            
        # Check for significant financial differences
        if field_name in financial_fields:
            if isinstance(source_value, (int, float)) and isinstance(target_value, (int, float)):
                percent_diff = 0
                
                if source_value == 0 and target_value == 0:
                    return "low"
                    
                if source_value == 0:
                    percent_diff = abs(target_value) * 100
                elif target_value == 0:
                    percent_diff = abs(source_value) * 100
                else:
                    percent_diff = abs(source_value - target_value) / max(abs(source_value), abs(target_value)) * 100
                
                if percent_diff > 10:
                    return "high"
                elif percent_diff > 5:
                    return "medium"
                else:
                    return "low"
        
        # Default to medium severity
        return "medium"
    
    def _add_to_conflict_history(self, conflict: Dict[str, Any], resolution: Dict[str, Any]) -> None:
        """Add a conflict and its resolution to the history"""
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "conflict": conflict,
            "resolution": resolution,
            "resolved": resolution["resolved"]
        }
        
        self.conflict_history.append(entry)
        
        # Trim history if it gets too large
        if len(self.conflict_history) > 1000:
            self.conflict_history = self.conflict_history[-1000:]
    
    # Resolution strategies
    def _resolve_by_last_updated(self, field: str, source_value: Any, target_value: Any) -> Any:
        """Resolve conflict by using the most recently updated value"""
        # In a real implementation, would check timestamps
        # For demo purposes, we'll assume source is more recent
        return source_value
    
    def _resolve_by_source_priority(self, field: str, source_value: Any, target_value: Any) -> Any:
        """Resolve conflict by giving priority to the source value"""
        return source_value
    
    def _resolve_by_target_priority(self, field: str, source_value: Any, target_value: Any) -> Any:
        """Resolve conflict by giving priority to the target value"""
        return target_value
    
    def _resolve_by_field_merge(self, field: str, source_value: Any, target_value: Any) -> Any:
        """
        Resolve conflict by merging values where possible
        
        This is a sophisticated merge function that tries to combine values
        based on the field type and content.
        """
        # Handle numeric values - use average for financial fields
        if isinstance(source_value, (int, float)) and isinstance(target_value, (int, float)):
            return (source_value + target_value) / 2
            
        # Handle dictionaries - merge them
        if isinstance(source_value, dict) and isinstance(target_value, dict):
            result = target_value.copy()
            result.update(source_value)  # Source values override target
            return result
            
        # Handle lists - combine unique items
        if isinstance(source_value, list) and isinstance(target_value, list):
            return list(set(target_value + source_value))
            
        # Handle strings - concatenate if they're different
        if isinstance(source_value, str) and isinstance(target_value, str):
            if source_value == target_value:
                return source_value
                
            if len(source_value) > 100 or len(target_value) > 100:
                # For long text, take the longest
                return source_value if len(source_value) > len(target_value) else target_value
            else:
                # For short text, concatenate with a delimiter
                return f"{target_value} | {source_value}"
                
        # Default to source value
        return source_value
    
    def _mark_for_manual_resolution(self, field: str, source_value: Any, target_value: Any) -> Any:
        """Mark field for manual resolution"""
        # This would normally trigger a workflow or notification
        # For demo purposes, we'll just use a special marker object
        return {
            "_manual_resolution_required": True,
            "source_value": source_value,
            "target_value": target_value,
            "field": field
        }


class SyncOrchestrator:
    """
    Orchestrates the sync process, handling change detection,
    transformation, validation, and writing to the target system.
    Enhanced with performance optimization capabilities for scalable processing.
    """
    def __init__(
        self,
        source_connection: DatabaseConnection,
        target_connection: DatabaseConnection,
        field_mapping_config: Dict[str, Any] = None,
        validation_rules: Dict[str, Any] = None,
        performance_config: Dict[str, Any] = None
    ):
        self.source_connection = source_connection
        self.target_connection = target_connection
        
        # Initialize components
        
        # Initialize conflict resolution handler
        self.conflict_handler = ConflictResolutionHandler(
            source_connection=source_connection,
            target_connection=target_connection
        )
        self.change_detector = ChangeDetector(source_connection)
        self.transformer = DataTransformer(field_mapping_config)
        self.validator = DataValidator(validation_rules)
        
        # Initialize performance optimization components
        perf_config = performance_config or {}
        
        # Configure batch processing
        batch_config = BatchConfiguration(
            batch_size=perf_config.get("batch_size", 100),
            max_retries=perf_config.get("max_retries", 3),
            dynamic_sizing=perf_config.get("dynamic_batch_sizing", True),
            min_batch_size=perf_config.get("min_batch_size", 10),
            max_batch_size=perf_config.get("max_batch_size", 1000),
            target_batch_duration_seconds=perf_config.get("target_batch_duration", 2.0),
            prioritize_tables=perf_config.get("table_priorities", {})
        )
        self.batch_processor = BatchProcessor(batch_config)
        
        # Configure parallel processing
        io_bound = perf_config.get("io_bound", True)  # Default to I/O bound for database operations
        self.parallel_processor = ParallelProcessor(
            thread_pool_size=perf_config.get("thread_pool_size", None),
            process_pool_size=perf_config.get("process_pool_size", None),
            io_bound=io_bound
        )
        
        # Configure resource monitoring
        self.resource_monitor = ResourceMonitor(
            poll_interval_seconds=perf_config.get("resource_poll_interval", 5.0)
        )
        
        # Configure database performance monitoring
        self.source_db_monitor = RepositoryPerformanceMonitor(
            source_connection=source_connection,
            target_connection=target_connection
        )
        
        # Configure incremental optimization
        self.dag_processor = DAGProcessor()
        
        # Start monitoring
        self.resource_monitor.start_monitoring()
        # Start database monitors - using their respective methods
        self.source_db_monitor.start_monitoring()
        # We only need one monitor instance for both source and target
        self.target_db_monitor = self.source_db_monitor
        
        # Metrics storage
        self.performance_metrics = {
            "batch_metrics": {},
            "parallel_metrics": {},
            "dag_metrics": {},
            "resource_metrics": [],
            "repository_metrics": {
                "source": {},
                "target": {}
            }
        }
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def full_sync(self, batch_processor=None, resource_monitor=None) -> SyncResult:
        """
        Perform a full synchronization of all data from source to target.
        Enhanced with batch processing and parallel execution for improved performance.
        
        Args:
            batch_processor: Optional batch processor to use for this operation
            resource_monitor: Optional resource monitor to use for this operation
            
        Returns:
            SyncResult with details of the operation
        """
        self.logger.info("Starting full sync with performance optimization")
        start_time = datetime.datetime.now().isoformat()
        
        try:
            # Check current resource usage and adjust parameters accordingly
            resource_metrics = self.resource_monitor.get_current_metrics()
            resource_recs = self.resource_monitor.recommend_resources("etl")
            
            # Log the resource recommendations
            self.logger.info(
                f"Resource recommendations: Threads={resource_recs['thread_count']}, "
                f"Processes={resource_recs['process_count']}, "
                f"Batch size={resource_recs['batch_size']}"
            )
            
            # Adjust parallel processor based on recommendations
            self.parallel_processor.thread_pool_size = resource_recs['thread_count']
            self.parallel_processor.process_pool_size = resource_recs['process_count']
            
            # Adjust batch processor based on recommendations
            self.batch_processor.config.batch_size = resource_recs['batch_size']
            
            # Record initial resource metrics
            self.performance_metrics["resource_metrics"].append(resource_metrics)
            
            # Detect all changes (full sync doesn't use last_sync_time)
            self.logger.info("Detecting changes...")
            changes = self.change_detector.detect_changes()
            self.logger.info(f"Detected {len(changes)} changes")
            
            # Transform the data in batches with parallel processing
            self.logger.info("Transforming records in optimized batches...")
            
            # Create a function to transform a batch of changes
            def transform_batch(batch):
                return self.transformer.transform(batch)
            
            # Process changes in batches using parallel processing
            transformed_records = self.batch_processor.process_in_batches(
                changes, 
                transform_batch,
                table_key=lambda x: x.source_table
            )
            
            # Store metrics from batch processing
            batch_metrics = self.batch_processor.get_metrics()
            self.performance_metrics["batch_metrics"]["transform"] = batch_metrics
            self.logger.info(
                f"Transformed {batch_metrics['records_processed']} records "
                f"at {batch_metrics['processing_rate']:.2f} records/sec"
            )
            
            # Validate the transformed data in parallel
            self.logger.info("Validating records in parallel using optimized validator...")
            
            # Use the validator's built-in parallel processing
            # This leverages the validator's optimized batch processing and metrics tracking
            resource_metrics = self.resource_monitor.get_current_metrics()
            recommended_threads = self.resource_monitor.recommend_resources("validation")["thread_count"]
            
            self.logger.info(f"Using {recommended_threads} threads for parallel validation")
            
            # Perform parallel validation with dynamic thread count
            validation_results = self.validator.validate_parallel(
                transformed_records,
                max_workers=recommended_threads,
                batch_size=min(100, max(10, len(transformed_records) // recommended_threads))
            )
            
            # Store metrics from parallel processing
            parallel_metrics = self.parallel_processor.get_metrics()
            self.performance_metrics["parallel_metrics"]["validate"] = parallel_metrics
            self.logger.info(
                f"Validated {parallel_metrics['records_processed']} records "
                f"at {parallel_metrics['processing_rate']:.2f} records/sec"
            )
            
            # Write valid records to target
            sync_result = self._write_to_target_optimized(validation_results)
            
            # Set start time on result
            sync_result.start_time = start_time
            
            # Add performance metrics to sync result
            sync_result.performance_metrics = self.performance_metrics
            
            # Log final resource metrics
            final_resource_metrics = self.resource_monitor.get_current_metrics()
            self.performance_metrics["resource_metrics"].append(final_resource_metrics)
            
            # Collect database performance metrics
            perf_summary = self.source_db_monitor.get_performance_summary()
            # Extract the metrics
            if "metrics" in perf_summary:
                source_db_metrics = perf_summary["metrics"].get("source", {})
                target_db_metrics = perf_summary["metrics"].get("target", {})
                self.performance_metrics["repository_metrics"]["source"] = source_db_metrics
                self.performance_metrics["repository_metrics"]["target"] = target_db_metrics
            
            # Get database performance recommendations
            source_recommendations = perf_summary.get("recommendations", [])
            target_recommendations = []
            
            if source_recommendations:
                self.logger.info(f"Source DB recommendations: {len(source_recommendations)} items found")
                for rec in source_recommendations:
                    self.logger.info(f"- {rec['severity'].upper()}: {rec['message']}")
            
            if target_recommendations:
                self.logger.info(f"Target DB recommendations: {len(target_recommendations)} items found")
                for rec in target_recommendations:
                    self.logger.info(f"- {rec['severity'].upper()}: {rec['message']}")
            
            self.logger.info("Full sync completed successfully")
            return sync_result
            
        except Exception as e:
            self.logger.error(f"Full sync failed: {str(e)}")
            # Stop resource monitoring in case of error
            return SyncResult(
                success=False,
                error_details=[{"error": str(e), "type": "Exception"}],
                start_time=start_time,
                end_time=datetime.datetime.now().isoformat()
            )
    
    def incremental_sync(self, last_sync_time: str, batch_processor=None, resource_monitor=None) -> SyncResult:
        """
        Perform an incremental synchronization of changes since last_sync_time.
        
        Args:
            last_sync_time: ISO-formatted timestamp of the last successful sync
            batch_processor: Optional batch processor to use for this operation
            resource_monitor: Optional resource monitor to use for this operation
            
        Returns:
            SyncResult with details of the operation
        """
        self.logger.info(f"Starting incremental sync from {last_sync_time}")
        start_time = datetime.datetime.now().isoformat()
        
        try:
            # Detect changes since last sync
            changes = self.change_detector.detect_changes(last_sync_time)
            
            # Transform the data
            transformed_records = self.transformer.transform(changes)
            
            # Validate the transformed data using parallel validation for better performance
            resource_metrics = self.resource_monitor.get_current_metrics()
            recommended_threads = self.resource_monitor.recommend_resources("validation")["thread_count"]
            
            self.logger.info(f"Using {recommended_threads} threads for parallel validation in incremental sync")
            
            # Use parallel validation if we have enough records to justify it
            if len(transformed_records) > 10:
                validation_results = self.validator.validate_parallel(
                    transformed_records,
                    max_workers=recommended_threads,
                    batch_size=min(100, max(10, len(transformed_records) // recommended_threads))
                )
            else:
                # For small batches, just use regular validation
                validation_results = self.validator.validate(transformed_records)
            
            # Write valid records to target
            sync_result = self._write_to_target(validation_results)
            
            # Set start time on result
            sync_result.start_time = start_time
            
            self.logger.info("Incremental sync completed successfully")
            return sync_result
            
        except Exception as e:
            self.logger.error(f"Incremental sync failed: {str(e)}")
            return SyncResult(
                success=False,
                error_details=[{"error": str(e), "type": "Exception"}],
                start_time=start_time,
                end_time=datetime.datetime.now().isoformat()
            )
    
    def selective_sync(self, tables: List[str], filter_conditions: Dict[str, str] = None, 
                       batch_processor=None, resource_monitor=None) -> SyncResult:
        """
        Perform a selective synchronization of specific repositories with optional filtering.
        
        Args:
            tables: List of repository names to synchronize
            filter_conditions: Optional dictionary mapping repository names to filter conditions
            batch_processor: Optional batch processor to use for this operation
            resource_monitor: Optional resource monitor to use for this operation
            
        Returns:
            SyncResult with details of the operation
        """
        self.logger.info(f"Starting selective sync for tables: {tables}")
        start_time = datetime.datetime.now().isoformat()
        tables_processed = {}
        
        try:
            # Initialize an empty list to collect all changes
            all_changes = []
            
            # Process each table
            for table in tables:
                self.logger.info(f"Processing table: {table}")
                
                # Get filter condition for this table if specified
                filter_condition = filter_conditions.get(table) if filter_conditions else None
                
                # Detect changes for this table with optional filtering
                table_changes = self.change_detector.detect_changes_for_table(
                    table, filter_condition=filter_condition
                )
                
                # Keep track of records processed per table
                tables_processed[table] = len(table_changes)
                
                # Add to collection of all changes
                all_changes.extend(table_changes)
                
            # Transform the data
            transformed_records = self.transformer.transform(all_changes)
            
            # Validate the transformed data using parallel validation for improved performance
            self.logger.info(f"Validating {len(transformed_records)} records for selective sync...")
            resource_metrics = self.resource_monitor.get_current_metrics()
            recommended_threads = self.resource_monitor.recommend_resources("validation")["thread_count"]
            
            self.logger.info(f"Using {recommended_threads} threads for parallel validation in selective sync")
            
            # Use parallel validation if we have enough records to justify it
            if len(transformed_records) > 10:
                validation_results = self.validator.validate_parallel(
                    transformed_records,
                    max_workers=recommended_threads,
                    batch_size=min(100, max(10, len(transformed_records) // recommended_threads))
                )
            else:
                # For small batches, just use regular validation
                validation_results = self.validator.validate(transformed_records)
            
            # Write valid records to target
            sync_result = self._write_to_target(validation_results)
            
            # Set start time on result
            sync_result.start_time = start_time
            
            # Add table-specific information
            sync_result.tables_processed = tables_processed
            
            self.logger.info(f"Selective sync completed successfully, processed {len(all_changes)} records")
            return sync_result
            
        except Exception as e:
            self.logger.error(f"Selective sync failed: {str(e)}")
            return SyncResult(
                success=False,
                error_details=[{"error": str(e), "type": "Exception", "tables": tables}],
                start_time=start_time,
                end_time=datetime.datetime.now().isoformat()
            )
    
    def _write_to_target(self, validation_results: List[ValidationResult]) -> SyncResult:
        """Write valid records to the target system"""
        valid_results = [r for r in validation_results if r.is_valid]
        invalid_results = [r for r in validation_results if not r.is_valid]
        
        self.logger.info(f"Writing {len(valid_results)} valid records to target")
        
        records_succeeded = 0
        error_details = []
        warnings = []
        
        # Process warnings from validation
        for result in validation_results:
            if result.warnings:
                warnings.extend([
                    f"Record {result.record.source_id}: {warning}"
                    for warning in result.warnings
                ])
        
        # Add validation errors to error details
        for result in invalid_results:
            error_details.append({
                "record_id": result.record.source_id,
                "errors": result.errors,
                "type": "Validation"
            })
        
        # Write valid records to target
        for result in valid_results:
            record = result.record
            try:
                if record.operation == ChangeType.INSERT:
                    self._insert_record(record)
                elif record.operation == ChangeType.UPDATE:
                    self._update_record(record)
                elif record.operation == ChangeType.DELETE:
                    self._delete_record(record)
                    
                records_succeeded += 1
                
            except Exception as e:
                self.logger.error(f"Error writing record {record.source_id}: {str(e)}")
                error_details.append({
                    "record_id": record.source_id,
                    "error": str(e),
                    "type": "Database"
                })
        
        # After processing, create a SyncResult
        return SyncResult(
            success=len(error_details) == 0,
            records_processed=len(validation_results),
            records_succeeded=records_succeeded,
            records_failed=len(validation_results) - records_succeeded,
            error_details=error_details,
            warnings=warnings,
            end_time=datetime.datetime.now().isoformat()
        )
    
    def _write_to_target_optimized(self, validation_results: List[ValidationResult]) -> SyncResult:
        """
        Write valid records to the target system using optimized batch and parallel processing.
        
        Args:
            validation_results: List of validation results to process
            
        Returns:
            SyncResult with details of the operation
        """
        valid_results = [r for r in validation_results if r.is_valid]
        invalid_results = [r for r in validation_results if not r.is_valid]
        
        self.logger.info(f"Writing {len(valid_results)} valid records to target with optimization")
        
        # Process warnings from validation
        warnings = []
        for result in validation_results:
            if result.warnings:
                warnings.extend([
                    f"Record {result.record.source_id}: {warning}"
                    for warning in result.warnings
                ])
        
        # Add validation errors to error details
        error_details = []
        for result in invalid_results:
            error_details.append({
                "record_id": result.record.source_id,
                "errors": result.errors,
                "type": "Validation"
            })
            
        # Group valid records by operation type and target table for batch processing
        operation_groups = {}
        for result in valid_results:
            record = result.record
            key = (record.operation, record.target_table)
            if key not in operation_groups:
                operation_groups[key] = []
            operation_groups[key].append(record)
            
        self.logger.info(f"Grouped records into {len(operation_groups)} operation groups")
        
        # Use batch processor to handle each group
        records_succeeded = 0
        records_failed = 0
        
        # Get resource recommendations for database operations
        resource_recs = self.resource_monitor.recommend_resources("database")
        self.logger.info(
            f"Database operation recommendations: Threads={resource_recs['thread_count']}, "
            f"Batch size={resource_recs['batch_size']}"
        )
        
        # Configure batch processor for database operations
        self.batch_processor.config.batch_size = resource_recs['batch_size']
        
        for (operation, table), records in operation_groups.items():
            self.logger.info(f"Processing {len(records)} {operation.value} operations for table {table}")
            
            # Create batch processing function based on operation type
            if operation == ChangeType.INSERT:
                batch_func = lambda batch: self._batch_insert(batch, table)
            elif operation == ChangeType.UPDATE:
                batch_func = lambda batch: self._batch_update(batch, table)
            elif operation == ChangeType.DELETE:
                batch_func = lambda batch: self._batch_delete(batch, table)
            else:
                self.logger.warning(f"Unknown operation type: {operation}")
                continue
                
            try:
                # Process this batch of records
                batch_results = self.batch_processor.process_in_batches(
                    records, batch_func
                )
                
                # Count successes from batch results
                success_count = sum(1 for result in batch_results if result.get("success", False))
                records_succeeded += success_count
                records_failed += len(records) - success_count
                
                # Add any batch errors to error details
                for result in batch_results:
                    if not result.get("success", False):
                        error_details.append({
                            "record_id": result.get("record_id", "unknown"),
                            "error": result.get("error", "Unknown batch processing error"),
                            "type": "Database"
                        })
                        
            except Exception as e:
                self.logger.error(f"Error in batch processing for {operation.value} on {table}: {str(e)}")
                error_details.append({
                    "operation": operation.value,
                    "table": table,
                    "error": str(e),
                    "type": "BatchProcessing"
                })
                records_failed += len(records)
                
        # Store batch metrics
        batch_metrics = self.batch_processor.get_metrics()
        self.performance_metrics["batch_metrics"]["database"] = batch_metrics
        
        # After processing, create a SyncResult
        return SyncResult(
            success=len(error_details) == 0,
            records_processed=len(validation_results),
            records_succeeded=records_succeeded,
            records_failed=records_failed + len(invalid_results),
            error_details=error_details,
            warnings=warnings,
            end_time=datetime.datetime.now().isoformat()
        )

    def _batch_insert(self, records: List[TransformedRecord], table: str) -> List[Dict[str, Any]]:
        """
        Insert a batch of records into the target system
        
        Args:
            records: List of records to insert
            table: Target table name
            
        Returns:
            List of result dictionaries
        """
        if not records:
            return []
            
        results = []
        
        try:
            # Build field list using the first record (assuming all records have the same structure)
            fields = list(records[0].data.keys())
            
            # Build VALUES clause for multiple records
            value_placeholder_rows = []
            all_params = {}
            
            for i, record in enumerate(records):
                # Create parameter names with index to avoid collision
                placeholders = []
                record_params = {}
                
                for field in fields:
                    param_name = f"{field}_{i}"
                    placeholders.append(f":{param_name}")
                    record_params[param_name] = record.data.get(field)
                    
                value_placeholder_rows.append(f"({', '.join(placeholders)})")
                all_params.update(record_params)
                
            # Build the full query
            query = f"""
            INSERT INTO {table} ({', '.join(fields)})
            VALUES {', '.join(value_placeholder_rows)}
            """
            
            # Execute the query
            self.target_connection.execute_query(query, all_params)
            
            # Record success for each record
            for record in records:
                results.append({
                    "success": True,
                    "record_id": record.source_id,
                    "operation": "insert"
                })
                
        except Exception as e:
            # If batch fails, add error for each record
            error_msg = str(e)
            self.logger.error(f"Batch insert error: {error_msg}")
            
            for record in records:
                results.append({
                    "success": False,
                    "record_id": record.source_id,
                    "operation": "insert",
                    "error": error_msg
                })
                
        return results
    
    def _batch_update(self, records: List[TransformedRecord], table: str) -> List[Dict[str, Any]]:
        """
        Update a batch of records in the target system
        
        Args:
            records: List of records to update
            table: Target table name
            
        Returns:
            List of result dictionaries
        """
        results = []
        
        # For updates, we'll process records individually but in a transaction
        try:
            # Begin transaction
            self.target_connection.execute_query("BEGIN TRANSACTION")
            
            for record in records:
                try:
                    # Build set clause for SQL
                    set_clauses = [f"{field} = :{field}" for field in record.data.keys()]
                    
                    query = f"""
                    UPDATE {table}
                    SET {', '.join(set_clauses)}
                    WHERE property_id = :target_id
                    """
                    
                    # Execute the query with parameters including target_id
                    params = {**record.data, "target_id": record.target_id}
                    self.target_connection.execute_query(query, params)
                    
                    results.append({
                        "success": True,
                        "record_id": record.source_id,
                        "operation": "update"
                    })
                    
                except Exception as e:
                    results.append({
                        "success": False,
                        "record_id": record.source_id,
                        "operation": "update",
                        "error": str(e)
                    })
                    
            # Commit transaction
            self.target_connection.execute_query("COMMIT")
            
        except Exception as e:
            # If transaction fails, rollback and mark all as failed
            self.logger.error(f"Transaction error in batch update: {str(e)}")
            try:
                self.target_connection.execute_query("ROLLBACK")
            except Exception as rollback_e:
                self.logger.error(f"Error rolling back transaction: {str(rollback_e)}")
                
            # Mark all records as failed
            results = []
            for record in records:
                results.append({
                    "success": False,
                    "record_id": record.source_id,
                    "operation": "update",
                    "error": f"Transaction error: {str(e)}"
                })
                
        return results
    
    def _batch_delete(self, records: List[TransformedRecord], table: str) -> List[Dict[str, Any]]:
        """
        Delete a batch of records from the target system
        
        Args:
            records: List of records to delete
            table: Target table name
            
        Returns:
            List of result dictionaries
        """
        if not records:
            return []
            
        results = []
        
        try:
            # Build IN clause with all target IDs
            target_ids = [record.target_id for record in records]
            id_placeholders = [f":id_{i}" for i in range(len(target_ids))]
            
            params = {f"id_{i}": target_id for i, target_id in enumerate(target_ids)}
            
            query = f"""
            DELETE FROM {table}
            WHERE property_id IN ({', '.join(id_placeholders)})
            """
            
            # Execute the query
            self.target_connection.execute_query(query, params)
            
            # Record success for each record
            for record in records:
                results.append({
                    "success": True,
                    "record_id": record.source_id,
                    "operation": "delete"
                })
                
        except Exception as e:
            # If batch fails, add error for each record
            error_msg = str(e)
            self.logger.error(f"Batch delete error: {error_msg}")
            
            for record in records:
                results.append({
                    "success": False,
                    "record_id": record.source_id,
                    "operation": "delete",
                    "error": error_msg
                })
                
        return results
    
    def _insert_record(self, record: TransformedRecord):
        """Insert a record into the target system"""
        # Build field list and values for SQL
        fields = list(record.data.keys())
        placeholders = [f":{field}" for field in fields]
        
        query = f"""
        INSERT INTO {record.target_table} ({', '.join(fields)})
        VALUES ({', '.join(placeholders)})
        """
        
        # Execute the query
        self.target_connection.execute_query(query, record.data)
        
        # In a real implementation, you'd handle ID generation and return
    
    def _update_record(self, record: TransformedRecord):
        """Update a record in the target system"""
        # Build set clause for SQL
        set_clauses = [f"{field} = :{field}" for field in record.data.keys()]
        
        query = f"""
        UPDATE {record.target_table}
        SET {', '.join(set_clauses)}
        WHERE property_id = :target_id
        """
        
        # Execute the query with parameters including target_id
        params = {**record.data, "target_id": record.target_id}
        self.target_connection.execute_query(query, params)
    
    def _delete_record(self, record: TransformedRecord):
        """Delete a record from the target system"""
        query = f"""
        DELETE FROM {record.target_table}
        WHERE property_id = :target_id
        """
        
        # Execute the query
        self.target_connection.execute_query(query, {"target_id": record.target_id})


# API for using the SyncService
class SchemaComparisonTool:
    """
    Tool for comparing database schemas between source and target systems.
    Helps identify structural differences for creating transformation mappings.
    """
    def __init__(self, source_connection: DatabaseConnection, target_connection: DatabaseConnection):
        self.source_connection = source_connection
        self.target_connection = target_connection
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def get_source_schema(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the schema details from the source database.
        
        Returns:
            Dictionary of table names and their column details
        """
        # In a real implementation, this would use database metadata APIs
        # For this demo, we'll return a simulated schema
        return {
            "properties": {
                "property_id": {"type": "INTEGER", "nullable": False, "primary_key": True},
                "parcel_number": {"type": "VARCHAR(20)", "nullable": False},
                "owner_name": {"type": "VARCHAR(100)", "nullable": False},
                "address": {"type": "VARCHAR(200)", "nullable": False},
                "land_value": {"type": "DECIMAL(12,2)", "nullable": False},
                "improvement_value": {"type": "DECIMAL(12,2)", "nullable": False},
                "total_value": {"type": "DECIMAL(12,2)", "nullable": False},
                "last_updated": {"type": "DATETIME", "nullable": False}
            },
            "valuations": {
                "valuation_id": {"type": "INTEGER", "nullable": False, "primary_key": True},
                "property_id": {"type": "INTEGER", "nullable": False, "foreign_key": "properties.property_id"},
                "valuation_date": {"type": "DATE", "nullable": False},
                "value_amount": {"type": "DECIMAL(12,2)", "nullable": False},
                "value_type": {"type": "VARCHAR(50)", "nullable": False},
                "assessor_id": {"type": "INTEGER", "nullable": True}
            },
            "assessors": {
                "assessor_id": {"type": "INTEGER", "nullable": False, "primary_key": True},
                "name": {"type": "VARCHAR(100)", "nullable": False},
                "certification": {"type": "VARCHAR(50)", "nullable": True},
                "active": {"type": "BIT", "nullable": False}
            }
        }
    
    def get_target_schema(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the schema details from the target database.
        
        Returns:
            Dictionary of table names and their column details
        """
        # In a real implementation, this would use database metadata APIs
        # For this demo, we'll return a simulated schema
        return {
            "properties": {
                "property_id": {"type": "VARCHAR(20)", "nullable": False, "primary_key": True},
                "parcel_id": {"type": "VARCHAR(20)", "nullable": False},
                "ownership": {"type": "JSONB", "nullable": False},
                "location": {"type": "JSONB", "nullable": False},
                "valuation": {"type": "JSONB", "nullable": False},
                "metadata": {"type": "JSONB", "nullable": False}
            },
            "valuations": {
                "valuation_id": {"type": "UUID", "nullable": False, "primary_key": True},
                "property_id": {"type": "VARCHAR(20)", "nullable": False, "foreign_key": "properties.property_id"},
                "assessment_date": {"type": "TIMESTAMP", "nullable": False},
                "assessed_value": {"type": "NUMERIC(15,2)", "nullable": False},
                "assessment_type": {"type": "VARCHAR(50)", "nullable": False},
                "assessor": {"type": "JSONB", "nullable": True}
            },
            "assessors": {
                "assessor_id": {"type": "UUID", "nullable": False, "primary_key": True},
                "personal_info": {"type": "JSONB", "nullable": False},
                "certifications": {"type": "JSONB", "nullable": True},
                "is_active": {"type": "BOOLEAN", "nullable": False}
            }
        }
    
    def compare_schemas(self) -> Dict[str, Any]:
        """
        Compare source and target schemas to identify differences and transformation needs.
        
        Returns:
            Dictionary with comparison results
        """
        source_schema = self.get_source_schema()
        target_schema = self.get_target_schema()
        
        comparison_results = {
            "tables": {
                "common": [],
                "source_only": [],
                "target_only": []
            },
            "column_differences": {},
            "data_type_conversions": [],
            "suggested_mappings": {}
        }
        
        # Find common tables and tables that exist only in one schema
        source_tables = set(source_schema.keys())
        target_tables = set(target_schema.keys())
        
        comparison_results["tables"]["common"] = list(source_tables.intersection(target_tables))
        comparison_results["tables"]["source_only"] = list(source_tables - target_tables)
        comparison_results["tables"]["target_only"] = list(target_tables - source_tables)
        
        # For common tables, analyze column differences
        for table in comparison_results["tables"]["common"]:
            source_cols = set(source_schema[table].keys())
            target_cols = set(target_schema[table].keys())
            
            comparison_results["column_differences"][table] = {
                "common": list(source_cols.intersection(target_cols)),
                "source_only": list(source_cols - target_cols),
                "target_only": list(target_cols - source_cols)
            }
            
            # Identify data type conversions needed
            for col in comparison_results["column_differences"][table]["common"]:
                source_type = source_schema[table][col]["type"]
                target_type = target_schema[table][col]["type"]
                
                if source_type != target_type:
                    comparison_results["data_type_conversions"].append({
                        "table": table,
                        "column": col,
                        "source_type": source_type,
                        "target_type": target_type,
                        "conversion_complexity": self._estimate_conversion_complexity(source_type, target_type)
                    })
            
            # Generate suggested mappings
            comparison_results["suggested_mappings"][table] = self._generate_mappings(
                source_schema[table], 
                target_schema[table]
            )
        
        return comparison_results
    
    def _estimate_conversion_complexity(self, source_type: str, target_type: str) -> str:
        """Estimate complexity of data type conversion"""
        # Conversions from numeric to numeric are simple
        if ("INT" in source_type or "DECIMAL" in source_type or "NUMERIC" in source_type) and \
           ("INT" in target_type or "DECIMAL" in target_type or "NUMERIC" in target_type):
            return "simple"
        
        # Conversions between similar string types are simple
        if ("CHAR" in source_type or "TEXT" in source_type) and \
           ("CHAR" in target_type or "TEXT" in target_type):
            return "simple"
        
        # Conversions between date/time types are moderate
        if ("DATE" in source_type or "TIME" in source_type) and \
           ("DATE" in target_type or "TIME" in target_type):
            return "moderate"
        
        # Special case for complex conversions
        if "JSONB" in target_type:
            return "complex"
        
        # Default to complex for all other conversions
        return "complex"
    
    def _generate_mappings(self, source_columns: Dict[str, Any], target_columns: Dict[str, Any]) -> Dict[str, Any]:
        """Generate suggested field mappings between source and target"""
        mappings = {}
        
        # Handle JSON/JSONB target columns
        json_target_columns = {col: details for col, details in target_columns.items() 
                              if "JSONB" in details["type"]}
        
        # For each JSON target column, suggest source columns that might map to it
        for json_col, details in json_target_columns.items():
            if json_col == "ownership":
                mappings[json_col] = {
                    "primary_owner": "owner_name",
                    "ownership_type": "COMPUTED"
                }
            elif json_col == "location":
                mappings[json_col] = {
                    "address_line1": "address",
                    "city": "PARSED",
                    "state": "PARSED",
                    "zip": "PARSED"
                }
            elif json_col == "valuation":
                mappings[json_col] = {
                    "land": "land_value",
                    "improvements": "improvement_value",
                    "total": "total_value",
                    "assessment_date": "last_updated"
                }
            elif json_col == "metadata":
                mappings[json_col] = {
                    "last_sync": "GENERATED",
                    "sync_status": "GENERATED"
                }
            
        # For regular columns, suggest direct mappings
        for target_col, target_details in target_columns.items():
            if "JSONB" not in target_details["type"]:
                # Look for exact matches
                if target_col in source_columns:
                    mappings[target_col] = target_col
                # Look for similar column names
                else:
                    for source_col in source_columns:
                        if target_col.lower() in source_col.lower() or source_col.lower() in target_col.lower():
                            mappings[target_col] = source_col
                            break
        
        return mappings
    
    def generate_mapping_config(self) -> Dict[str, Any]:
        """
        Generate a comprehensive mapping configuration based on schema comparison.
        
        Returns:
            Dictionary with mapping configuration for use by the DataTransformer
        """
        comparison = self.compare_schemas()
        
        mapping_config = {}
        for table, mapping in comparison["suggested_mappings"].items():
            source_table = table
            target_table = table
            
            field_mapping = {}
            transforms = {}
            
            for target_field, source_info in mapping.items():
                if isinstance(source_info, dict):
                    # Handle nested JSON mappings
                    field_mapping[target_field] = {}
                    for nested_target, nested_source in source_info.items():
                        if nested_source not in ("COMPUTED", "PARSED", "GENERATED"):
                            field_mapping[target_field][nested_target] = nested_source
                        else:
                            # Add transformer for special fields
                            transform_type = nested_source.lower()
                            transforms[f"{target_field}.{nested_target}"] = {
                                "type": transform_type,
                                "parameters": {}
                            }
                else:
                    # Handle direct field mappings
                    field_mapping[target_field] = source_info
            
            mapping_config[source_table] = {
                "target_table": target_table,
                "fields": field_mapping,
                "transforms": transforms
            }
        
        return mapping_config


class IndexOptimizer:
    """
    Analyzes query patterns and table statistics to recommend optimal indexes,
    improving database performance for common sync operations.
    """
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.logger = logging.getLogger(self.__class__.__name__)
        self.index_stats = {}  # Cache for index statistics
        self.query_log = []  # Store recent query log for analysis
        self.recommendations_cache = {}  # Cache for recommendations
        
    def log_query(self, query: str, execution_time: float) -> None:
        """
        Log a query for analysis
        
        Args:
            query: SQL query executed
            execution_time: Time in milliseconds to execute
        """
        # Keep only the last 100 queries for analysis
        if len(self.query_log) >= 100:
            self.query_log.pop(0)
            
        query_entry = {
            "query": query,
            "execution_time": execution_time,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        self.query_log.append(query_entry)
        
        # Clear recommendations cache when new queries are logged
        self.recommendations_cache = {}
        
    def get_table_indexes(self, table_name: str) -> Dict[str, Any]:
        """
        Get current indexes for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with index information
        """
        self.logger.info(f"Getting indexes for table {table_name}")
        
        try:
            # In a real implementation, this would execute a query to fetch indexes
            # For the simulation, we'll return mock index information
            indexes = self._get_mock_indexes(table_name)
            
            # Cache the results
            self.index_stats[table_name] = {
                "indexes": indexes,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            return {
                "table_name": table_name,
                "indexes": indexes,
                "count": len(indexes),
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting indexes for {table_name}: {str(e)}")
            return {
                "table_name": table_name,
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def analyze_query_patterns(self) -> Dict[str, Any]:
        """
        Analyze query patterns from the query log
        
        Returns:
            Dictionary with query pattern analysis
        """
        self.logger.info("Analyzing query patterns")
        
        if not self.query_log:
            return {
                "status": "empty",
                "message": "No queries in the log to analyze",
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        try:
            # Extract tables from queries
            table_pattern = r"FROM\s+([a-zA-Z0-9_]+)"
            tables_accessed = []
            
            for entry in self.query_log:
                tables = re.findall(table_pattern, entry["query"], re.IGNORECASE)
                tables_accessed.extend(tables)
            
            # Count occurrences of each table
            table_counts = {}
            for table in tables_accessed:
                if table not in table_counts:
                    table_counts[table] = 0
                table_counts[table] += 1
            
            # Extract WHERE clauses to find commonly filtered columns
            where_pattern = r"WHERE\s+(.+?)(?:\s+ORDER\s+BY|\s+GROUP\s+BY|\s+LIMIT|\s*;|\s*$)"
            where_clauses = []
            
            for entry in self.query_log:
                clauses = re.findall(where_pattern, entry["query"], re.IGNORECASE)
                where_clauses.extend(clauses)
            
            # Analyze columns in WHERE clauses
            column_pattern = r"([a-zA-Z0-9_]+)\s*[=<>]"
            filtered_columns = []
            
            for clause in where_clauses:
                columns = re.findall(column_pattern, clause)
                filtered_columns.extend(columns)
            
            # Count occurrences of each column
            column_counts = {}
            for column in filtered_columns:
                if column not in column_counts:
                    column_counts[column] = 0
                column_counts[column] += 1
            
            # Identify slow queries
            slow_threshold = 100  # ms
            slow_queries = [
                entry for entry in self.query_log 
                if entry["execution_time"] > slow_threshold
            ]
            
            # Calculate average execution time
            avg_execution_time = sum(entry["execution_time"] for entry in self.query_log) / len(self.query_log)
            
            return {
                "status": "success",
                "query_count": len(self.query_log),
                "avg_execution_time": avg_execution_time,
                "slow_query_count": len(slow_queries),
                "most_accessed_tables": sorted(table_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                "most_filtered_columns": sorted(column_counts.items(), key=lambda x: x[1], reverse=True)[:10],
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing query patterns: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def generate_index_recommendations(self, table_name: str) -> Dict[str, Any]:
        """
        Generate index recommendations for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with index recommendations
        """
        # Check cache first
        if table_name in self.recommendations_cache:
            self.logger.info(f"Using cached index recommendations for {table_name}")
            return self.recommendations_cache[table_name]
            
        self.logger.info(f"Generating index recommendations for {table_name}")
        
        try:
            # Get current indexes
            current_indexes = self.get_table_indexes(table_name)
            
            if "error" in current_indexes:
                return {
                    "table_name": table_name,
                    "status": "error",
                    "error": current_indexes["error"],
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
            # Analyze query patterns
            query_patterns = self.analyze_query_patterns()
            
            if query_patterns["status"] != "success":
                return {
                    "table_name": table_name,
                    "status": "insufficient_data",
                    "message": "Not enough query data to generate recommendations",
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
            # Find relevant query information for this table
            is_accessed = False
            for table, count in query_patterns.get("most_accessed_tables", []):
                if table.lower() == table_name.lower():
                    is_accessed = True
                    break
                    
            if not is_accessed:
                return {
                    "table_name": table_name,
                    "status": "no_queries",
                    "message": f"No queries accessing {table_name} found in the log",
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
            # Get relevant columns for this table
            # In a real implementation, this would check if the columns belong to this table
            # For the simulation, we'll make a simplifying assumption
            relevant_columns = []
            for column, count in query_patterns.get("most_filtered_columns", []):
                # Skip columns that already have indexes
                if not any(index["column"] == column for index in current_indexes.get("indexes", [])):
                    relevant_columns.append({"column": column, "query_count": count})
            
            # Generate recommendations
            recommendations = []
            for column_info in relevant_columns[:3]:  # Top 3 most promising columns
                column = column_info["column"]
                query_count = column_info["query_count"]
                
                # Calculate a priority score (1-10)
                priority = min(10, 1 + int(query_count / 2))
                
                # Estimate performance impact (percentage improvement)
                impact = random.randint(5, 50)
                
                recommendations.append({
                    "type": "index",
                    "column": column,
                    "index_type": self._recommend_index_type(column),
                    "priority": priority,
                    "estimated_impact": f"{impact}% query speedup",
                    "rationale": f"Column appears in {query_count} queries in the log"
                })
            
            # Add compound index recommendations if beneficial
            if len(relevant_columns) >= 2:
                # Recommend a compound index for top 2 columns
                col1 = relevant_columns[0]["column"]
                col2 = relevant_columns[1]["column"]
                
                # Calculate a priority score (1-10)
                priority = min(10, 1 + int((relevant_columns[0]["query_count"] + 
                                         relevant_columns[1]["query_count"]) / 4))
                
                # Estimate performance impact (percentage improvement)
                impact = random.randint(10, 60)
                
                recommendations.append({
                    "type": "compound_index",
                    "columns": [col1, col2],
                    "index_type": "btree",
                    "priority": priority,
                    "estimated_impact": f"{impact}% query speedup",
                    "rationale": f"Columns frequently appear together in queries"
                })
            
            # Add recommendations for dropping unused indexes
            unused_indexes = []
            for index in current_indexes.get("indexes", []):
                # In a real implementation, this would analyze index usage stats
                # For the simulation, we'll randomly mark some indexes as unused
                if random.random() < 0.3:
                    unused_indexes.append(index)
            
            for index in unused_indexes:
                recommendations.append({
                    "type": "drop_index",
                    "index_name": index["name"],
                    "priority": random.randint(1, 5),
                    "estimated_impact": "Reduced storage and faster writes",
                    "rationale": "Index appears to be unused in current query patterns"
                })
            
            # Generate DDL statements
            ddl_statements = self._generate_ddl_statements(table_name, recommendations)
            
            result = {
                "table_name": table_name,
                "status": "success",
                "recommendations": recommendations,
                "ddl_statements": ddl_statements,
                "current_indexes": current_indexes.get("indexes", []),
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Cache the results
            self.recommendations_cache[table_name] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating index recommendations: {str(e)}")
            return {
                "table_name": table_name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def apply_index_recommendation(self, table_name: str, recommendation_id: int) -> Dict[str, Any]:
        """
        Apply a specific index recommendation
        
        Args:
            table_name: Name of the table
            recommendation_id: ID of the recommendation to apply
            
        Returns:
            Dictionary with the application result
        """
        self.logger.info(f"Applying index recommendation {recommendation_id} for {table_name}")
        
        try:
            # Get recommendations
            recommendations = self.generate_index_recommendations(table_name)
            
            if recommendations.get("status") != "success":
                return {
                    "status": "error",
                    "message": "Failed to get recommendations",
                    "error": recommendations.get("error", "Unknown error"),
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
            # Check if the recommendation ID is valid
            if recommendation_id < 0 or recommendation_id >= len(recommendations.get("recommendations", [])):
                return {
                    "status": "error",
                    "message": f"Invalid recommendation ID: {recommendation_id}",
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
            # Get the recommendation
            recommendation = recommendations["recommendations"][recommendation_id]
            
            # Get the DDL statement
            ddl_statement = recommendations["ddl_statements"][recommendation_id]
            
            # In a real implementation, this would execute the DDL statement
            # For the simulation, we'll just pretend it was successful
            success = True
            error = None
            
            if success:
                # Clear cache to force refreshing recommendations and index stats
                if table_name in self.index_stats:
                    del self.index_stats[table_name]
                    
                if table_name in self.recommendations_cache:
                    del self.recommendations_cache[table_name]
                    
                # For demonstration purposes, let's pretend we update the table's indexes
                if recommendation["type"] == "index" or recommendation["type"] == "compound_index":
                    # Would add a new index in real implementation
                    pass
                elif recommendation["type"] == "drop_index":
                    # Would remove an index in real implementation
                    pass
                
                return {
                    "status": "success",
                    "table_name": table_name,
                    "recommendation_applied": recommendation,
                    "ddl_executed": ddl_statement,
                    "timestamp": datetime.datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to apply recommendation",
                    "error": error,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error applying index recommendation: {str(e)}")
            return {
                "status": "error",
                "message": f"Error applying index recommendation: {str(e)}",
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def _get_mock_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get mock index information for a table"""
        if table_name == "properties":
            return [
                {
                    "name": "properties_pkey",
                    "column": "property_id",
                    "type": "btree",
                    "unique": True,
                    "primary": True,
                    "size_kb": 128
                },
                {
                    "name": "idx_properties_parcel_number",
                    "column": "parcel_number",
                    "type": "btree",
                    "unique": True,
                    "primary": False,
                    "size_kb": 112
                }
            ]
        elif table_name == "valuations":
            return [
                {
                    "name": "valuations_pkey",
                    "column": "valuation_id",
                    "type": "btree",
                    "unique": True,
                    "primary": True,
                    "size_kb": 96
                },
                {
                    "name": "idx_valuations_property_id",
                    "column": "property_id",
                    "type": "btree",
                    "unique": False,
                    "primary": False,
                    "size_kb": 88
                }
            ]
        else:
            # Generic indexes for other tables
            return [
                {
                    "name": f"{table_name}_pkey",
                    "column": "id",
                    "type": "btree",
                    "unique": True,
                    "primary": True,
                    "size_kb": 64
                }
            ]
    
    def _recommend_index_type(self, column: str) -> str:
        """Recommend an index type based on column name and data characteristics"""
        # In a real implementation, this would analyze data distribution and column type
        # For the simulation, we'll use a simple heuristic based on column name
        
        if "id" in column.lower() or "key" in column.lower() or "code" in column.lower():
            return "btree"  # Good for equality and range queries
        elif "name" in column.lower() or "description" in column.lower():
            return "hash"  # Good for equality queries
        elif "date" in column.lower() or "time" in column.lower():
            return "btree"  # Good for range queries
        elif "text" in column.lower() or "comment" in column.lower():
            return "gin"  # Good for full-text search
        else:
            return "btree"  # Default to btree
    
    def _generate_ddl_statements(self, table_name: str, recommendations: List[Dict[str, Any]]) -> List[str]:
        """Generate DDL statements for the recommendations"""
        ddl_statements = []
        
        for rec in recommendations:
            if rec["type"] == "index":
                ddl = f"CREATE INDEX idx_{table_name}_{rec['column']} ON {table_name} USING {rec['index_type']} ({rec['column']});"
                ddl_statements.append(ddl)
            elif rec["type"] == "compound_index":
                columns = ", ".join(rec["columns"])
                column_names = "_".join(rec["columns"])
                ddl = f"CREATE INDEX idx_{table_name}_{column_names} ON {table_name} USING {rec['index_type']} ({columns});"
                ddl_statements.append(ddl)
            elif rec["type"] == "drop_index":
                ddl = f"DROP INDEX {rec['index_name']};"
                ddl_statements.append(ddl)
                
        return ddl_statements


class HistoricalTrendAnalyzer:
    """
    Analyzes historical trends in database metrics to predict future performance,
    identify recurring patterns, and optimize sync scheduling based on historical load.
    """
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.logger = logging.getLogger(self.__class__.__name__)
        self.metrics_history = {}  # Store historical metrics by date
        self.analysis_cache = {}  # Cache for trend analysis results
        
    def record_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Record current metrics for historical tracking
        
        Args:
            metrics: Current performance metrics
        """
        timestamp = datetime.datetime.now().isoformat()
        date_key = timestamp.split("T")[0]
        
        if date_key not in self.metrics_history:
            self.metrics_history[date_key] = []
            
        metrics_record = {
            "timestamp": timestamp,
            **metrics
        }
        
        self.metrics_history[date_key].append(metrics_record)
        self.logger.info(f"Recorded metrics for {date_key}")
        
        # Clear cache since we have new data
        self.analysis_cache = {}
        
    def get_historical_data(self, days: int = 30, metric_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get historical data for analysis
        
        Args:
            days: Number of days of history to retrieve
            metric_name: Optional specific metric to retrieve
            
        Returns:
            Dictionary with historical data
        """
        self.logger.info(f"Retrieving {days} days of historical data")
        
        try:
            # Calculate the cutoff date
            today = datetime.datetime.now().date()
            cutoff_date = today - datetime.timedelta(days=days)
            cutoff_str = cutoff_date.isoformat()
            
            # Filter data by date
            filtered_data = {}
            for date_key, metrics_list in self.metrics_history.items():
                if date_key >= cutoff_str:
                    filtered_data[date_key] = metrics_list
            
            # If a specific metric was requested, extract just that metric
            if metric_name:
                metric_data = {}
                for date_key, metrics_list in filtered_data.items():
                    metric_data[date_key] = []
                    for metrics in metrics_list:
                        if metric_name in metrics:
                            metric_data[date_key].append({
                                "timestamp": metrics["timestamp"],
                                metric_name: metrics[metric_name]
                            })
                return {
                    "metric": metric_name,
                    "days": days,
                    "data": metric_data
                }
            
            return {
                "days": days,
                "data": filtered_data
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving historical data: {str(e)}")
            return {
                "days": days,
                "error": str(e)
            }
    
    def analyze_trends(self, metric_name: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyze trends for a specific metric
        
        Args:
            metric_name: Name of the metric to analyze
            days: Number of days of history to analyze
            
        Returns:
            Dictionary with trend analysis results
        """
        # Check cache first
        cache_key = f"{metric_name}_{days}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
            
        self.logger.info(f"Analyzing trends for {metric_name} over {days} days")
        
        try:
            # Get historical data for this metric
            history = self.get_historical_data(days, metric_name)
            
            if "error" in history:
                return {
                    "metric": metric_name,
                    "days": days,
                    "error": history["error"]
                }
                
            # Extract data points for analysis
            data_points = []
            timestamps = []
            
            for date_key, metrics_list in history["data"].items():
                for metric in metrics_list:
                    if metric_name in metric:
                        data_points.append(float(metric[metric_name]))
                        timestamps.append(metric["timestamp"])
            
            # Can't analyze without data
            if not data_points:
                return {
                    "metric": metric_name,
                    "days": days,
                    "trend": "insufficient_data",
                    "message": f"No data available for {metric_name}"
                }
                
            # Calculate basic statistics
            avg = sum(data_points) / len(data_points)
            min_val = min(data_points)
            max_val = max(data_points)
            
            # Detect trend
            trend = self._detect_trend(data_points)
            
            # Look for patterns
            patterns = self._detect_patterns(data_points, timestamps)
            
            # Predict future values
            prediction = self._predict_future_values(data_points, 7)  # Predict 7 days ahead
            
            result = {
                "metric": metric_name,
                "days_analyzed": days,
                "trend": trend,
                "statistics": {
                    "count": len(data_points),
                    "min": min_val,
                    "max": max_val,
                    "avg": avg,
                    "current": data_points[-1] if data_points else None,
                    "percent_change": ((data_points[-1] - data_points[0]) / data_points[0] * 100) 
                                     if data_points and data_points[0] != 0 else 0
                },
                "patterns": patterns,
                "prediction": prediction
            }
            
            # Cache the result
            self.analysis_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {str(e)}")
            return {
                "metric": metric_name,
                "days": days,
                "trend": "error",
                "error": str(e)
            }
    
    def get_optimization_schedule(self) -> Dict[str, Any]:
        """
        Generate an optimized schedule for sync operations based on historical load
        
        Returns:
            Dictionary with scheduling recommendations
        """
        self.logger.info("Generating optimization schedule")
        
        try:
            # Analyze CPU trends to find low-usage times
            cpu_trends = self.analyze_trends("cpu_utilization", 14)
            
            if "error" in cpu_trends:
                return {
                    "error": cpu_trends["error"],
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
            # Analyze query volume trends
            query_trends = self.analyze_trends("query_volume", 14)
            
            # Generate hourly load profile
            load_profile = self._generate_hourly_load_profile(14)
            
            # Find optimal times for different operations
            recommended_times = {}
            
            # Find optimal time for full sync (lowest overall load)
            if load_profile and "hourly_load" in load_profile:
                min_load_hour = min(load_profile["hourly_load"].items(), key=lambda x: x[1])
                recommended_times["full_sync"] = {
                    "hour": min_load_hour[0],
                    "load_factor": min_load_hour[1],
                    "confidence": "high" if load_profile["consistency_score"] > 0.7 else "medium"
                }
                
                # Find good times for incremental syncs (moderate load times)
                sorted_hours = sorted(load_profile["hourly_load"].items(), key=lambda x: x[1])
                incremental_hours = [
                    {"hour": h[0], "load_factor": h[1]} 
                    for h in sorted_hours[:3]  # Best 3 hours
                ]
                recommended_times["incremental_sync"] = incremental_hours
            
            return {
                "schedule_recommendations": recommended_times,
                "load_profile": load_profile,
                "cpu_trends": cpu_trends,
                "query_trends": query_trends,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating optimization schedule: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def _detect_trend(self, data_points: List[float]) -> str:
        """Detect the overall trend in a series of data points"""
        if len(data_points) < 3:
            return "insufficient_data"
            
        # Simple linear regression to determine trend
        n = len(data_points)
        x = list(range(n))
        
        # Calculate slope of best-fit line
        x_mean = sum(x) / n
        y_mean = sum(data_points) / n
        
        numerator = sum((x[i] - x_mean) * (data_points[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
            
        slope = numerator / denominator
        
        # Determine trend based on slope
        if abs(slope) < 0.01 * y_mean:
            return "stable"
        elif slope > 0:
            if slope > 0.1 * y_mean:
                return "rapidly_increasing"
            else:
                return "gradually_increasing"
        else:
            if abs(slope) > 0.1 * y_mean:
                return "rapidly_decreasing"
            else:
                return "gradually_decreasing"
    
    def _detect_patterns(self, data_points: List[float], timestamps: List[str]) -> Dict[str, Any]:
        """Detect patterns in the data series"""
        if len(data_points) < 7:
            return {"detected": False, "reason": "insufficient_data"}
            
        patterns = {}
        
        # Extract day of week from timestamps
        days_of_week = []
        for ts in timestamps:
            try:
                dt = datetime.datetime.fromisoformat(ts)
                days_of_week.append(dt.weekday())
            except ValueError:
                pass
        
        # Check for day of week patterns
        if days_of_week:
            day_avg = {}
            day_count = {}
            
            for i, day in enumerate(days_of_week):
                if day not in day_avg:
                    day_avg[day] = 0
                    day_count[day] = 0
                
                day_avg[day] += data_points[i]
                day_count[day] += 1
            
            # Calculate average by day
            for day in day_avg:
                if day_count[day] > 0:
                    day_avg[day] /= day_count[day]
            
            # Check for significant differences between days
            if day_avg and len(day_avg) > 1:
                avg_values = list(day_avg.values())
                overall_avg = sum(avg_values) / len(avg_values)
                max_diff = max(abs(v - overall_avg) for v in avg_values)
                
                if max_diff > 0.2 * overall_avg:
                    # There's a significant difference between days
                    weekday_names = [
                        "Monday", "Tuesday", "Wednesday", "Thursday", 
                        "Friday", "Saturday", "Sunday"
                    ]
                    
                    day_pattern = {weekday_names[day]: avg for day, avg in day_avg.items()}
                    highest_day = max(day_avg.items(), key=lambda x: x[1])
                    lowest_day = min(day_avg.items(), key=lambda x: x[1])
                    
                    patterns["weekday_pattern"] = {
                        "detected": True,
                        "day_averages": day_pattern,
                        "highest_day": weekday_names[highest_day[0]],
                        "lowest_day": weekday_names[lowest_day[0]]
                    }
        
        # Check for cyclical patterns using autocorrelation
        if len(data_points) >= 14:
            max_lag = min(14, len(data_points) // 2)
            autocorr = []
            
            for lag in range(1, max_lag + 1):
                # Calculate autocorrelation for this lag
                series1 = data_points[:-lag] if lag > 0 else data_points
                series2 = data_points[lag:] if lag > 0 else data_points
                
                # Calculate correlation
                mean1 = sum(series1) / len(series1)
                mean2 = sum(series2) / len(series2)
                
                num = sum((series1[i] - mean1) * (series2[i] - mean2) for i in range(len(series1)))
                den1 = sum((x - mean1) ** 2 for x in series1)
                den2 = sum((x - mean2) ** 2 for x in series2)
                
                if den1 > 0 and den2 > 0:
                    corr = num / ((den1 * den2) ** 0.5)
                    autocorr.append((lag, corr))
            
            # Check for peaks in autocorrelation
            if autocorr:
                # Sort by correlation value
                sorted_autocorr = sorted(autocorr, key=lambda x: x[1], reverse=True)
                
                # If we have a strong correlation at some lag, it suggests a cycle
                if sorted_autocorr[0][1] > 0.6:
                    patterns["cyclical_pattern"] = {
                        "detected": True,
                        "cycle_length": sorted_autocorr[0][0],
                        "correlation": sorted_autocorr[0][1]
                    }
        
        # If no patterns were detected
        if not patterns:
            return {"detected": False, "reason": "no_significant_patterns"}
            
        patterns["detected"] = True
        return patterns
    
    def _predict_future_values(self, data_points: List[float], days_ahead: int) -> Dict[str, Any]:
        """Predict future values based on historical trends"""
        if len(data_points) < 7:
            return {"status": "error", "reason": "insufficient_data"}
            
        try:
            # Simple linear regression prediction
            n = len(data_points)
            x = list(range(n))
            
            # Calculate slope and intercept of best-fit line
            x_mean = sum(x) / n
            y_mean = sum(data_points) / n
            
            numerator = sum((x[i] - x_mean) * (data_points[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            
            if denominator == 0:
                slope = 0
            else:
                slope = numerator / denominator
                
            intercept = y_mean - slope * x_mean
            
            # Generate predictions
            predictions = []
            for i in range(1, days_ahead + 1):
                predicted_value = slope * (n + i - 1) + intercept
                predictions.append(round(predicted_value, 2))
            
            # Calculate a confidence score based on how well the model fits historical data
            # (simplified version of R-squared)
            y_predicted = [slope * i + intercept for i in x]
            ss_total = sum((y - y_mean) ** 2 for y in data_points)
            ss_residual = sum((data_points[i] - y_predicted[i]) ** 2 for i in range(n))
            
            if ss_total == 0:
                confidence = 0
            else:
                confidence = 1 - (ss_residual / ss_total)
            
            return {
                "status": "success",
                "days_ahead": days_ahead,
                "predictions": predictions,
                "confidence": confidence
            }
            
        except Exception as e:
            return {
                "status": "error",
                "reason": str(e)
            }
    
    def _generate_hourly_load_profile(self, days: int = 14) -> Dict[str, Any]:
        """Generate an hourly load profile based on historical data"""
        try:
            # Get relevant metrics for hourly analysis
            cpu_history = self.get_historical_data(days, "cpu_utilization")
            query_history = self.get_historical_data(days, "query_volume")
            
            if "error" in cpu_history or "error" in query_history:
                return {
                    "error": cpu_history.get("error") or query_history.get("error")
                }
                
            # Initialize hourly load factors
            hourly_load = {str(hour): 0.0 for hour in range(24)}
            hourly_samples = {str(hour): 0 for hour in range(24)}
            
            # Process CPU data
            for date_key, metrics_list in cpu_history["data"].items():
                for metric in metrics_list:
                    if "cpu_utilization" in metric and "timestamp" in metric:
                        try:
                            dt = datetime.datetime.fromisoformat(metric["timestamp"])
                            hour = str(dt.hour)
                            hourly_load[hour] += float(metric["cpu_utilization"])
                            hourly_samples[hour] += 1
                        except (ValueError, KeyError):
                            pass
            
            # Process query volume data
            for date_key, metrics_list in query_history["data"].items():
                for metric in metrics_list:
                    if "query_volume" in metric and "timestamp" in metric:
                        try:
                            dt = datetime.datetime.fromisoformat(metric["timestamp"])
                            hour = str(dt.hour)
                            # Normalize query volume to same scale as CPU (0-100)
                            norm_volume = min(100, float(metric["query_volume"]) / 10)
                            hourly_load[hour] += norm_volume
                            hourly_samples[hour] += 1
                        except (ValueError, KeyError):
                            pass
            
            # Calculate average load for each hour
            for hour in hourly_load:
                if hourly_samples[hour] > 0:
                    hourly_load[hour] /= hourly_samples[hour]
            
            # Calculate consistency score (how consistent the pattern is day-to-day)
            # In real implementation this would use day-to-day comparison
            # For simulation, we'll use a placeholder
            consistency_score = 0.85  # High consistency
            
            return {
                "hourly_load": hourly_load,
                "samples_per_hour": hourly_samples,
                "days_analyzed": days,
                "consistency_score": consistency_score,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating hourly load profile: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }


class RepositoryPerformanceMonitor:
    """
    Monitors repository performance during synchronization operations
    and provides metrics and optimization recommendations.
    """
    def __init__(self, source_connection: DatabaseConnection, target_connection: DatabaseConnection):
        self.source_connection = source_connection
        self.target_connection = target_connection
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Performance metrics storage
        self.metrics_history = {
            "source": [],
            "target": []
        }
        
        # Current sync metrics
        self.current_metrics = {
            "source": {},
            "target": {}
        }
        
        # Sampling configuration
        self.sampling_interval = 5  # seconds
        self.max_history_size = 100  # samples
        
    def start_monitoring(self) -> None:
        """Start monitoring repository performance"""
        self.logger.info("Starting repository performance monitoring")
        
        # Reset current metrics
        self.current_metrics = {
            "source": {
                "start_time": datetime.datetime.now().isoformat(),
                "operations_executed": 0,
                "rows_processed": 0,
                "execution_time_ms": 0,
                "avg_execution_time_ms": 0,
                "max_execution_time_ms": 0,
                "cpu_utilization": 0,
                "memory_utilization": 0,
                "io_operations": 0,
                "active_connections": 1
            },
            "target": {
                "start_time": datetime.datetime.now().isoformat(),
                "operations_executed": 0,
                "rows_processed": 0,
                "execution_time_ms": 0,
                "avg_execution_time_ms": 0,
                "max_execution_time_ms": 0,
                "cpu_utilization": 0,
                "memory_utilization": 0,
                "io_operations": 0,
                "active_connections": 1
            }
        }
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """
        Stop monitoring and finalize metrics
        
        Returns:
            Dictionary with performance summary
        """
        # Set end time 
        end_time = datetime.datetime.now().isoformat()
        
        # Finalize metrics
        for repo in ["source", "target"]:
            self.current_metrics[repo]["end_time"] = end_time
            if self.current_metrics[repo]["operations_executed"] > 0:
                self.current_metrics[repo]["avg_execution_time_ms"] = (
                    self.current_metrics[repo]["execution_time_ms"] / 
                    self.current_metrics[repo]["operations_executed"]
                )
            
            # Add to history
            self.metrics_history[repo].append(self.current_metrics[repo].copy())
            
            # Trim history if needed
            if len(self.metrics_history[repo]) > self.max_history_size:
                self.metrics_history[repo] = self.metrics_history[repo][-self.max_history_size:]
        
        self.logger.info("Repository performance monitoring stopped")
        return self.get_performance_summary()
    
    def record_query_metrics(self, repo_type: str, execution_time_ms: float, rows_affected: int) -> None:
        """
        Record metrics for a single operation
        
        Args:
            repo_type: "source" or "target"
            execution_time_ms: Execution time in milliseconds
            rows_affected: Number of rows affected/returned
        """
        if repo_type not in self.current_metrics:
            return
            
        metrics = self.current_metrics[repo_type]
        metrics["operations_executed"] += 1
        metrics["rows_processed"] += rows_affected
        metrics["execution_time_ms"] += execution_time_ms
        
        if execution_time_ms > metrics.get("max_execution_time_ms", 0):
            metrics["max_execution_time_ms"] = execution_time_ms
    
    def simulate_system_metrics(self, repo_type: str) -> None:
        """
        Simulate system-level metrics for demo purposes
        
        Args:
            repo_type: "source" or "target"
        """
        if repo_type not in self.current_metrics:
            return
            
        metrics = self.current_metrics[repo_type]
        
        # Simulate CPU, memory, and IO based on operation activity
        operation_activity = min(100, metrics.get("operations_executed", 0) * 2)
        
        # Generate realistic metrics
        metrics["cpu_utilization"] = min(90, 30 + operation_activity / 3 + random.randint(-5, 5))
        metrics["memory_utilization"] = min(90, 40 + operation_activity / 4 + random.randint(-3, 3))
        metrics["io_operations"] = metrics.get("operations_executed", 0) * 3 + metrics.get("rows_processed", 0) / 10
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of performance metrics
        
        Returns:
            Dictionary with performance summary
        """
        # Simulate metrics before generating summary
        self.simulate_system_metrics("source")
        self.simulate_system_metrics("target")
        
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics": self.current_metrics,
            "recommendations": self._generate_recommendations(),
            "historical_trends": self._analyze_historical_trends()
        }
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate performance optimization recommendations
        
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Source repository recommendations
        source_metrics = self.current_metrics["source"]
        if source_metrics.get("max_execution_time_ms", 0) > 1000:
            recommendations.append({
                "repository": "source",
                "type": "operation_optimization",
                "severity": "high",
                "description": "Long-running operations detected in source repository",
                "action": "Analyze slow operations and optimize with appropriate indexes"
            })
            
        if source_metrics.get("cpu_utilization", 0) > 80:
            recommendations.append({
                "repository": "source",
                "type": "resource_allocation",
                "severity": "high",
                "description": "High CPU utilization in source repository",
                "action": "Increase CPU allocation or optimize execution patterns"
            })
            
        # Target repository recommendations  
        target_metrics = self.current_metrics["target"]
        if target_metrics.get("io_operations", 0) > 1000:
            recommendations.append({
                "repository": "target",
                "type": "io_optimization",
                "severity": "medium",
                "description": "High I/O operations detected in target repository",
                "action": "Consider batch operations and optimize write patterns"
            })
            
        if source_metrics.get("avg_execution_time_ms", 0) > 500:
            recommendations.append({
                "repository": "source",
                "type": "index_recommendation",
                "severity": "medium",
                "description": "Operations average execution time is high",
                "action": "Add indexes on frequently accessed data"
            })
            
        # General recommendations
        if len(self.metrics_history["source"]) >= 3:
            recommendations.append({
                "repository": "both",
                "type": "sync_schedule",
                "severity": "low",
                "description": "Consider optimizing sync schedule based on repository load",
                "action": "Schedule syncs during low-activity periods"
            })
            
        return recommendations
    
    def _analyze_historical_trends(self) -> Dict[str, Any]:
        """
        Analyze historical performance trends
        
        Returns:
            Dictionary with trend analysis
        """
        trends = {
            "source": {},
            "target": {}
        }
        
        for repo_type in ["source", "target"]:
            if len(self.metrics_history[repo_type]) < 2:
                continue
                
            # Analyze last 5 samples or all if less than 5
            samples = self.metrics_history[repo_type][-5:]
            
            # Extract metrics for trending
            cpu_trend = [s.get("cpu_utilization", 0) for s in samples]
            execution_time_trend = [s.get("avg_execution_time_ms", 0) for s in samples]
            
            # Calculate trends (positive = increasing, negative = decreasing)
            if len(cpu_trend) >= 2:
                trends[repo_type]["cpu_trend"] = self._calculate_trend(cpu_trend)
            
            if len(execution_time_trend) >= 2:
                trends[repo_type]["execution_time_trend"] = self._calculate_trend(execution_time_trend)
                
            # Add qualitative assessment
            trends[repo_type]["performance_trend"] = "stable"
            if repo_type in trends and "execution_time_trend" in trends[repo_type]:
                if trends[repo_type]["execution_time_trend"] > 0.1:
                    trends[repo_type]["performance_trend"] = "degrading"
                elif trends[repo_type]["execution_time_trend"] < -0.1:
                    trends[repo_type]["performance_trend"] = "improving"
        
        return trends
        
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics
        
        Returns:
            Dictionary with current metrics for source and target repositories
        """
        # Ensure we have some metrics to return by simulating if needed
        self.simulate_system_metrics("source")
        self.simulate_system_metrics("target")
        
        return self.current_metrics
    
    def _calculate_trend(self, values: List[float]) -> float:
        """
        Calculate trend factor from a series of values
        
        Args:
            values: List of numeric values 
            
        Returns:
            Trend factor (positive = increasing, negative = decreasing)
        """
        if len(values) < 2:
            return 0
            
        # Simple linear regression slope
        n = len(values)
        x = list(range(n))
        mean_x = sum(x) / n
        mean_y = sum(values) / n
        
        # Calculate slope
        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
        
        # Avoid division by zero
        if denominator == 0:
            return 0
            
        slope = numerator / denominator
        
        # Normalize by the mean value to get relative trend
        if mean_y == 0:
            return 0
            
        return slope / mean_y


class TransactionSafetyManager:
    """
    Ensures data integrity through transaction management and failover mechanisms.
    Provides a robust transaction framework with commit/rollback capabilities,
    savepoints, and error recovery.
    """
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.logger = logging.getLogger(self.__class__.__name__)
        self.active_transaction = False
        self.savepoints = []
        self.operation_log = []
        self.error_handlers = {}
        
    def begin_transaction(self) -> Dict[str, Any]:
        """Begin a new transaction"""
        if self.active_transaction:
            self.logger.warning("Transaction already active, cannot begin a new one")
            return {
                "success": False,
                "message": "Transaction already active",
                "transaction_id": None
            }
            
        try:
            # In a real implementation, this would execute BEGIN TRANSACTION
            # For the simulation, we'll just set the flag
            self.active_transaction = True
            transaction_id = f"tx-{random.randint(100000, 999999)}"
            
            self.logger.info(f"Transaction {transaction_id} started")
            self.operation_log.append({
                "operation": "begin_transaction",
                "timestamp": datetime.datetime.now().isoformat(),
                "transaction_id": transaction_id
            })
            
            return {
                "success": True,
                "message": "Transaction started successfully",
                "transaction_id": transaction_id
            }
        except Exception as e:
            self.logger.error(f"Failed to start transaction: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to start transaction: {str(e)}",
                "transaction_id": None
            }
    
    def commit_transaction(self) -> Dict[str, Any]:
        """Commit the current transaction"""
        if not self.active_transaction:
            self.logger.warning("No active transaction to commit")
            return {
                "success": False,
                "message": "No active transaction",
                "operations_committed": 0
            }
            
        try:
            # In a real implementation, this would execute COMMIT
            # For the simulation, we'll reset state
            self.active_transaction = False
            operations_count = len(self.operation_log)
            
            self.logger.info(f"Transaction committed with {operations_count} operations")
            self.operation_log.append({
                "operation": "commit",
                "timestamp": datetime.datetime.now().isoformat(),
                "operations_count": operations_count
            })
            
            # Clear savepoints after successful commit
            self.savepoints = []
            
            return {
                "success": True,
                "message": "Transaction committed successfully",
                "operations_committed": operations_count
            }
        except Exception as e:
            self.logger.error(f"Failed to commit transaction: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to commit transaction: {str(e)}",
                "operations_committed": 0
            }
    
    def rollback_transaction(self, to_savepoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Rollback the current transaction
        
        Args:
            to_savepoint: Optional savepoint name to rollback to
            
        Returns:
            Dictionary with rollback results
        """
        if not self.active_transaction:
            self.logger.warning("No active transaction to rollback")
            return {
                "success": False,
                "message": "No active transaction",
                "operations_rolled_back": 0
            }
            
        try:
            operations_count = len(self.operation_log)
            
            if to_savepoint:
                # Find the savepoint
                savepoint_found = False
                for sp in self.savepoints:
                    if sp["name"] == to_savepoint:
                        savepoint_found = True
                        # In a real implementation, this would execute ROLLBACK TO SAVEPOINT
                        # For the simulation, we'll just log it
                        self.logger.info(f"Rolled back to savepoint {to_savepoint}")
                        operations_rolled_back = operations_count - sp["operation_index"]
                        break
                
                if not savepoint_found:
                    self.logger.warning(f"Savepoint {to_savepoint} not found")
                    return {
                        "success": False,
                        "message": f"Savepoint {to_savepoint} not found",
                        "operations_rolled_back": 0
                    }
            else:
                # Full rollback
                # In a real implementation, this would execute ROLLBACK
                self.active_transaction = False
                self.savepoints = []
                operations_rolled_back = operations_count
                self.logger.info("Transaction fully rolled back")
            
            self.operation_log.append({
                "operation": "rollback",
                "timestamp": datetime.datetime.now().isoformat(),
                "to_savepoint": to_savepoint,
                "operations_rolled_back": operations_rolled_back
            })
            
            return {
                "success": True,
                "message": f"Transaction rolled back {'' if not to_savepoint else f'to savepoint {to_savepoint}'} successfully",
                "operations_rolled_back": operations_rolled_back
            }
        except Exception as e:
            self.logger.error(f"Failed to rollback transaction: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to rollback transaction: {str(e)}",
                "operations_rolled_back": 0
            }
    
    def create_savepoint(self, name: str) -> Dict[str, Any]:
        """
        Create a savepoint in the current transaction
        
        Args:
            name: Name of the savepoint
            
        Returns:
            Dictionary with savepoint creation results
        """
        if not self.active_transaction:
            self.logger.warning("No active transaction to create savepoint")
            return {
                "success": False,
                "message": "No active transaction",
                "savepoint": None
            }
            
        try:
            # In a real implementation, this would execute SAVEPOINT
            # For the simulation, we'll just record it
            savepoint = {
                "name": name,
                "timestamp": datetime.datetime.now().isoformat(),
                "operation_index": len(self.operation_log)
            }
            
            self.savepoints.append(savepoint)
            
            self.logger.info(f"Savepoint {name} created")
            self.operation_log.append({
                "operation": "create_savepoint",
                "timestamp": datetime.datetime.now().isoformat(),
                "savepoint": name
            })
            
            return {
                "success": True,
                "message": f"Savepoint {name} created successfully",
                "savepoint": savepoint
            }
        except Exception as e:
            self.logger.error(f"Failed to create savepoint: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to create savepoint: {str(e)}",
                "savepoint": None
            }
    
    def execute_in_transaction(self, query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a query within the current transaction
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Dictionary with query execution results
        """
        if not self.active_transaction:
            self.logger.warning("No active transaction for query execution")
            return {
                "success": False,
                "message": "No active transaction",
                "results": None
            }
            
        try:
            # Execute the query
            results = self.connection.execute_query(query, params)
            
            self.logger.info(f"Query executed in transaction: {query[:50]}...")
            self.operation_log.append({
                "operation": "execute_query",
                "timestamp": datetime.datetime.now().isoformat(),
                "query": query,
                "params": params
            })
            
            return {
                "success": True,
                "message": "Query executed successfully in transaction",
                "results": results
            }
        except Exception as e:
            self.logger.error(f"Failed to execute query in transaction: {str(e)}")
            
            # Check if we have an error handler registered for this type of error
            error_type = type(e).__name__
            if error_type in self.error_handlers:
                handler_result = self.error_handlers[error_type](e, query, params)
                if handler_result.get("handled", False):
                    return {
                        "success": handler_result.get("success", False),
                        "message": handler_result.get("message", str(e)),
                        "results": handler_result.get("results", None),
                        "error_handled": True
                    }
            
            return {
                "success": False,
                "message": f"Failed to execute query in transaction: {str(e)}",
                "results": None
            }
    
    def register_error_handler(self, error_type: str, handler_function: callable) -> bool:
        """
        Register an error handler for a specific type of error
        
        Args:
            error_type: Name of the error type (e.g., "ValueError")
            handler_function: Function to call when this error occurs
            
        Returns:
            True if handler registered successfully, False otherwise
        """
        try:
            self.error_handlers[error_type] = handler_function
            self.logger.info(f"Registered error handler for {error_type}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register error handler: {str(e)}")
            return False
    
    def get_transaction_status(self) -> Dict[str, Any]:
        """Get the current status of the active transaction"""
        return {
            "active": self.active_transaction,
            "savepoints": len(self.savepoints),
            "operations": len(self.operation_log),
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def get_operation_log(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get the operation log for the current or last transaction"""
        return self.operation_log[-limit:] if limit > 0 else self.operation_log


class SyncService:
    """
    Main service class that provides the API for the SyncService.
    """
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Initialize database connections
        pacs_connection_string = os.environ.get(
            "PACS_DB_CONNECTION", 
            "Server=pacs-server;Database=pacs;User Id=sync_user;Password=********;"
        )
        cama_connection_string = os.environ.get(
            "CAMA_DB_CONNECTION",
            "postgresql://sync_user:********@cama-server:5432/cama"
        )
        
        self.source_connection = DatabaseConnection(pacs_connection_string, "PACS")
        self.target_connection = DatabaseConnection(cama_connection_string, "CAMA")
        
        # Initialize system resource monitor
        self.resource_monitor = ResourceMonitor(
            poll_interval_seconds=self.config.get("resource_poll_interval", 5.0)
        )
        self.resource_monitor.start_monitoring()
        self.logger.info("Resource monitoring started")
        
        # Initialize the schema comparison tool
        self.schema_comparison_tool = SchemaComparisonTool(
            source_connection=self.source_connection,
            target_connection=self.target_connection
        )
        
        # Initialize the database performance monitor
        self.performance_monitor = RepositoryPerformanceMonitor(
            source_connection=self.source_connection,
            target_connection=self.target_connection
        )
        
        # Initialize the transaction safety manager
        self.transaction_manager = TransactionSafetyManager(
            connection=self.target_connection
        )
        
        # Initialize the data quality profiler
        self.data_quality_profiler = DataQualityProfiler(
            connection=self.source_connection
        )
        
        # Initialize the historical trend analyzer
        self.trend_analyzer = HistoricalTrendAnalyzer(
            connection=self.source_connection
        )
        
        # Initialize the orchestrator
        self.orchestrator = SyncOrchestrator(
            source_connection=self.source_connection,
            target_connection=self.target_connection
        )
        
        # Initialize batch processor with advanced dynamic sizing
        batch_config = BatchConfiguration(
            batch_size=self.config.get("batch_size", 100),
            max_retries=self.config.get("max_retries", 3),
            dynamic_sizing=self.config.get("dynamic_sizing", True),
            adaptive_learning=self.config.get("adaptive_learning", True),
            workload_specific_sizing=self.config.get("workload_specific_sizing", True),
            resource_aware_sizing=self.config.get("resource_aware_sizing", True),
            target_batch_duration_seconds=self.config.get("target_batch_duration", 2.0)
        )
        self.batch_processor = BatchProcessor(configuration=batch_config, logger=self.logger)
        
        # Configure parallel processor
        self.parallel_processor = ParallelProcessor(
            thread_pool_size=self.config.get("thread_pool_size", None),
            process_pool_size=self.config.get("process_pool_size", None),
            io_bound=True,
            logger=self.logger
        )
        
        # Track sync history
        self.last_sync_time = None
        self.sync_history = []
    
    def full_sync(self, batch_processor=None, resource_monitor=None) -> Dict[str, Any]:
        """
        Perform a full sync between source and target repositories with optimized batch processing
        based on system resources and repository performance.
        
        Args:
            batch_processor: Optional batch processor to use for this operation
            resource_monitor: Optional resource monitor to use for this operation
            
        Returns:
            Dictionary with sync results
        """
        self.logger.info("Full sync requested with dynamic batch sizing")
        
        # Get performance metrics to optimize batch sizing
        metrics = self.get_performance_metrics()
        
        # Configure batch processor with dynamic batch sizing based on current metrics
        operation_specific_batch_sizes = metrics.get("optimal_batch_sizes", {}).get("optimal_batch_sizes", {})
        
        # Update batch configuration with operation-specific settings
        if hasattr(self, 'batch_processor') and self.batch_processor:
            self.logger.info("Applying dynamic batch sizing based on current system state")
            # Initialize with default settings first
            batch_config = BatchConfiguration(
                batch_size=operation_specific_batch_sizes.get("repository_read", 200),
                dynamic_sizing=True,
                adaptive_learning=True,
                workload_specific_sizing=True,
                resource_aware_sizing=True
            )
            self.batch_processor.config = batch_config
            
            # Log the optimization decisions
            if "adjustment_explanations" in metrics.get("optimal_batch_sizes", {}):
                for explanation in metrics["optimal_batch_sizes"]["adjustment_explanations"]:
                    self.logger.info(f"Batch optimization: {explanation}")
        
        # Perform the full sync with optimized configuration
        self.logger.info("Starting full sync with optimized batch configuration")
        result = self.orchestrator.full_sync(
            batch_processor=self.batch_processor,
            resource_monitor=self.resource_monitor
        )
        
        # Store sync information
        if result.success:
            self.last_sync_time = result.end_time
            
        # Capture performance metrics from this sync
        batch_metrics = {}
        if hasattr(self, 'batch_processor') and self.batch_processor:
            batch_metrics = self.batch_processor.get_metrics()
            
        # Add enhanced metrics to sync history
        sync_record = {
            "type": "full",
            "timestamp": result.end_time,
            "success": result.success,
            "records_processed": result.records_processed,
            "records_succeeded": result.records_succeeded,
            "performance": {
                "batch_processing_rate": batch_metrics.get("processing_rate", 0),
                "optimal_batch_size": self._get_optimal_batch_size_for_next_sync(result, batch_metrics)
            }
        }
        self.sync_history.append(sync_record)
        
        # Include the enhanced metrics in the result
        result_dict = result.to_dict()
        result_dict["performance_metrics"] = batch_metrics
        
        return result_dict
    
    def incremental_sync(self, batch_processor=None, resource_monitor=None) -> Dict[str, Any]:
        """
        Perform an incremental sync between source and target repositories with dynamic batch sizing
        based on system resources and repository performance.
        
        Args:
            batch_processor: Optional batch processor to use for this operation
            resource_monitor: Optional resource monitor to use for this operation
            
        Returns:
            Dictionary with sync results
        """
        self.logger.info("Incremental sync requested with dynamic batch sizing")
        
        # If no last sync time, do a full sync
        if self.last_sync_time is None:
            self.logger.info("No last sync time, performing full sync instead")
            return self.full_sync()
        
        # Get performance metrics to optimize batch sizing
        metrics = self.get_performance_metrics()
        
        # Configure batch processor with dynamic batch sizing based on current metrics
        operation_specific_batch_sizes = metrics.get("optimal_batch_sizes", {}).get("optimal_batch_sizes", {})
        
        # Update batch configuration with operation-specific settings
        if hasattr(self, 'batch_processor') and self.batch_processor:
            self.logger.info("Applying dynamic batch sizing based on current system state")
            # Initialize with default settings first
            batch_config = BatchConfiguration(
                batch_size=operation_specific_batch_sizes.get("data_transform", 100),
                dynamic_sizing=True,
                adaptive_learning=True,
                workload_specific_sizing=True,
                resource_aware_sizing=True
            )
            self.batch_processor.config = batch_config
            
            # Log the optimization decisions
            if "adjustment_explanations" in metrics.get("optimal_batch_sizes", {}):
                for explanation in metrics["optimal_batch_sizes"]["adjustment_explanations"]:
                    self.logger.info(f"Batch optimization: {explanation}")
        
        # Perform the incremental sync with optimized configuration
        self.logger.info("Starting incremental sync with optimized batch configuration")
        result = self.orchestrator.incremental_sync(
            self.last_sync_time, 
            batch_processor=self.batch_processor,
            resource_monitor=self.resource_monitor
        )
        
        # Store sync information
        if result.success:
            self.last_sync_time = result.end_time
            
        # Capture performance metrics from this sync
        batch_metrics = {}
        if hasattr(self, 'batch_processor') and self.batch_processor:
            batch_metrics = self.batch_processor.get_metrics()
            
        # Add enhanced metrics to sync history
        sync_record = {
            "type": "incremental",
            "timestamp": result.end_time,
            "success": result.success,
            "records_processed": result.records_processed,
            "records_succeeded": result.records_succeeded,
            "performance": {
                "batch_processing_rate": batch_metrics.get("processing_rate", 0),
                "optimal_batch_size": self._get_optimal_batch_size_for_next_sync(result, batch_metrics)
            }
        }
        self.sync_history.append(sync_record)
        
        # Include the enhanced metrics in the result
        result_dict = result.to_dict()
        result_dict["performance_metrics"] = batch_metrics
        
        return result_dict
        
    def _get_optimal_batch_size_for_next_sync(
        self, 
        sync_result: Any, 
        batch_metrics: Dict[str, Any]
    ) -> int:
        """
        Calculate the optimal batch size for the next sync operation
        based on the performance of the current sync.
        
        Args:
            sync_result: Result of the sync operation
            batch_metrics: Metrics from the batch processing
            
        Returns:
            Recommended batch size for the next sync
        """
        # Default to a reasonable batch size
        default_batch_size = 100
        
        if not batch_metrics or "batch_sizes" not in batch_metrics:
            return default_batch_size
            
        # If we have batch processing metrics with throughput information
        if "processing_rate" in batch_metrics and batch_metrics["processing_rate"] > 0:
            # Check if we have batch metrics history
            if "batch_sizes" in batch_metrics and "batch_durations" in batch_metrics:
                # Calculate throughput for each batch
                throughputs = []
                for size, duration in zip(batch_metrics["batch_sizes"], batch_metrics["batch_durations"]):
                    if duration > 0:
                        throughput = size / duration  # records per second
                        throughputs.append((size, throughput))
                
                # Find the batch size with the best throughput
                if throughputs:
                    # Sort by throughput (highest first)
                    throughputs.sort(key=lambda x: x[1], reverse=True)
                    optimal_size = throughputs[0][0]
                    self.logger.info(
                        f"Optimal batch size from performance history: {optimal_size} "
                        f"(throughput: {throughputs[0][1]:.2f} records/sec)"
                    )
                    return optimal_size
        
        # If no clear optimal size from metrics, use the last configured batch size
        if hasattr(self, 'batch_processor') and self.batch_processor:
            return self.batch_processor.config.batch_size
            
        return default_batch_size
    
    def selective_sync(self, tables: List[str], filter_conditions: Dict[str, str] = None, 
                       batch_processor=None, resource_monitor=None) -> Dict[str, Any]:
        """
        Perform a selective sync for specific repositories with optional filtering
        and optimized batch processing based on system resources and repository performance.
        
        Args:
            tables: List of repository names to synchronize
            filter_conditions: Optional dictionary mapping repository names to filter conditions
            batch_processor: Optional batch processor to use for this operation
            resource_monitor: Optional resource monitor to use for this operation
            
        Returns:
            Dictionary with sync results
        """
        self.logger.info(f"Selective sync requested for tables: {tables} with dynamic batch sizing")
        
        if not tables:
            self.logger.warning("No tables specified for selective sync")
            return {
                "success": False,
                "records_processed": 0,
                "records_succeeded": 0,
                "records_failed": 0,
                "error_details": [{"error": "No tables specified for selective sync"}],
                "warnings": [],
                "start_time": datetime.datetime.now().isoformat(),
                "end_time": datetime.datetime.now().isoformat(),
                "duration_seconds": 0
            }
        
        filter_conditions = filter_conditions or {}
        
        try:
            # Get performance metrics to optimize batch sizing
            metrics = self.get_performance_metrics()
            
            # Configure batch processor with dynamic batch sizing based on current metrics
            operation_specific_batch_sizes = metrics.get("optimal_batch_sizes", {}).get("optimal_batch_sizes", {})
            
            # Update batch configuration with operation-specific settings
            if hasattr(self, 'batch_processor') and self.batch_processor:
                self.logger.info("Applying dynamic batch sizing based on current system state")
                # Initialize with default settings first
                batch_config = BatchConfiguration(
                    batch_size=operation_specific_batch_sizes.get("repository_read", 150),
                    dynamic_sizing=True,
                    adaptive_learning=True,
                    workload_specific_sizing=True,
                    resource_aware_sizing=True
                )
                self.batch_processor.config = batch_config
                
                # Log the optimization decisions
                if "adjustment_explanations" in metrics.get("optimal_batch_sizes", {}):
                    for explanation in metrics["optimal_batch_sizes"]["adjustment_explanations"]:
                        self.logger.info(f"Batch optimization: {explanation}")
            
            # Perform the selective sync with optimized configuration
            self.logger.info("Starting selective sync with optimized batch configuration")
            result = self.orchestrator.selective_sync(
                tables, 
                filter_conditions,
                batch_processor=self.batch_processor,
                resource_monitor=self.resource_monitor
            )
            
            # Store sync information
            if result.success:
                self.last_sync_time = result.end_time
                
            # Capture performance metrics from this sync
            batch_metrics = {}
            if hasattr(self, 'batch_processor') and self.batch_processor:
                batch_metrics = self.batch_processor.get_metrics()
                
            # Add enhanced metrics to sync history
            sync_record = {
                "type": "selective",
                "tables": tables,
                "timestamp": result.end_time,
                "success": result.success,
                "records_processed": result.records_processed,
                "records_succeeded": result.records_succeeded,
                "performance": {
                    "batch_processing_rate": batch_metrics.get("processing_rate", 0),
                    "optimal_batch_size": self._get_optimal_batch_size_for_next_sync(result, batch_metrics)
                }
            }
            self.sync_history.append(sync_record)
            
            # Include the enhanced metrics in the result
            result_dict = result.to_dict()
            result_dict["performance_metrics"] = batch_metrics
            
            return result_dict
            
        except Exception as e:
            self.logger.error(f"Selective sync failed: {str(e)}")
            error_dict = {
                "success": False,
                "records_processed": 0,
                "records_succeeded": 0,
                "records_failed": 0,
                "error_details": [{"error": str(e)}],
                "warnings": [],
                "start_time": datetime.datetime.now().isoformat(),
                "end_time": datetime.datetime.now().isoformat(),
                "duration_seconds": 0
            }
            
            self.sync_history.append({
                "type": "selective",
                "tables": tables,
                "timestamp": datetime.datetime.now().isoformat(),
                "success": False,
                "records_processed": 0,
                "records_succeeded": 0
            })
            
            return error_dict
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get the current sync status and history.
        
        Returns:
            Dictionary with sync status information
        """
        # Get any scheduled syncs (in a real implementation)
        scheduled_syncs = []
        
        return {
            "last_sync_time": self.last_sync_time,
            "sync_history": self.sync_history[-5:],  # Last 5 sync operations
            "active": True,
            "version": "2.0.0",
            "scheduled_syncs": scheduled_syncs
        }
        
    def compare_schemas(self) -> Dict[str, Any]:
        """
        Compare schemas between source and target databases.
        
        Returns:
            Dictionary with schema comparison results
        """
        self.logger.info("Comparing database schemas")
        
        try:
            comparison_results = self.schema_comparison_tool.compare_schemas()
            
            # Include summary information for quick reference
            table_counts = {
                "common_tables": len(comparison_results["tables"]["common"]),
                "source_only_tables": len(comparison_results["tables"]["source_only"]),
                "target_only_tables": len(comparison_results["tables"]["target_only"])
            }
            
            # Count data type conversions by complexity
            conversion_complexity = {
                "simple": 0,
                "moderate": 0,
                "complex": 0
            }
            
            for conversion in comparison_results["data_type_conversions"]:
                complexity = conversion["conversion_complexity"]
                conversion_complexity[complexity] += 1
                
            return {
                "comparison_results": comparison_results,
                "table_counts": table_counts,
                "conversion_complexity": conversion_complexity,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error comparing schemas: {str(e)}")
            return {
                "error": f"Schema comparison failed: {str(e)}",
                "timestamp": datetime.datetime.now().isoformat()
            }
            
    def generate_mapping_config(self) -> Dict[str, Any]:
        """
        Generate a mapping configuration based on schema comparison.
        
        Returns:
            Dictionary with mapping configuration
        """
        self.logger.info("Generating mapping configuration")
        
        try:
            mapping_config = self.schema_comparison_tool.generate_mapping_config()
            
            return {
                "mapping_config": mapping_config,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating mapping config: {str(e)}")
            return {
                "error": f"Mapping configuration generation failed: {str(e)}",
                "timestamp": datetime.datetime.now().isoformat()
            }
            
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics, including system resources,
        repository performance, and dynamic batch processing recommendations.
        
        Returns:
            Dictionary with integrated performance metrics and recommendations
        """
        self.logger.info("Getting comprehensive performance metrics")
        
        try:
            # Set default values for metrics
            default_repo_metrics = {
                "metrics": {
                    "source": {
                        "cpu_utilization": 30,
                        "memory_utilization": 40,
                        "active_connections": 5,
                        "avg_execution_time_ms": 25,
                        "operations_executed": 100,
                        "transaction_count": 10
                    },
                    "target": {
                        "cpu_utilization": 35,
                        "memory_utilization": 45,
                        "active_connections": 8,
                        "avg_execution_time_ms": 30,
                        "operations_executed": 120,
                        "transaction_count": 15
                    }
                },
                "recommendations": [
                    {
                        "description": "Consider index optimization for improved operation performance",
                        "severity": "medium"
                    }
                ],
                "historical_trends": {}
            }
            
            # Get repository performance metrics with fallback
            try:
                repo_performance_summary = self.performance_monitor.get_performance_summary()
            except Exception as repo_err:
                self.logger.warning(f"Using fallback repository metrics due to error: {str(repo_err)}")
                repo_performance_summary = default_repo_metrics
            
            # Ensure required metrics exist
            for repo_type in ["source", "target"]:
                if repo_type not in repo_performance_summary.get("metrics", {}):
                    repo_performance_summary["metrics"][repo_type] = default_repo_metrics["metrics"][repo_type]
                
                # Ensure all required fields exist
                for field, default_value in default_repo_metrics["metrics"][repo_type].items():
                    if field not in repo_performance_summary["metrics"][repo_type]:
                        repo_performance_summary["metrics"][repo_type][field] = default_value
            
            # Ensure recommendations exist
            if "recommendations" not in repo_performance_summary:
                repo_performance_summary["recommendations"] = default_repo_metrics["recommendations"]
            
            # Get system resource metrics
            system_resources = self.resource_monitor.current_metrics
            
            # Add default values if system metrics are missing
            if not system_resources:
                system_resources = {
                    "cpu_percent": 40,
                    "memory_percent": 50,
                    "memory_used_mb": 2048,
                    "disk_io_percent": 30
                }
            
            # Get batch processing metrics if available
            batch_metrics = {}
            if hasattr(self, 'batch_processor') and self.batch_processor:
                try:
                    batch_metrics = self.batch_processor.get_metrics()
                except Exception as batch_err:
                    self.logger.warning(f"Failed to get batch metrics: {str(batch_err)}")
            
            # Calculate optimal batch sizes based on all available metrics
            try:
                optimal_batch_sizes = self._calculate_optimal_batch_sizes(
                    system_resources, 
                    repo_performance_summary
                )
            except Exception as batch_size_err:
                self.logger.warning(f"Error calculating optimal batch sizes: {str(batch_size_err)}")
                # Provide default optimal batch sizes
                optimal_batch_sizes = {
                    "optimal_batch_sizes": {
                        "data_transform": 150,
                        "data_validation": 300,
                        "repository_write": 80,
                        "repository_read": 200,
                        "api_request": 40
                    },
                    "adjustment_explanations": [
                        "Using default batch sizes due to calculation error"
                    ]
                }
            
            # Add additional context for easier interpretation
            performance_summary = {
                "repository": repo_performance_summary,
                "system_resources": system_resources,
                "batch_processing": batch_metrics,
                "optimal_batch_sizes": optimal_batch_sizes,
                "interpretation": {
                    "source_repo_health": self._interpret_repo_health(
                        repo_performance_summary["metrics"]["source"]
                    ),
                    "target_repo_health": self._interpret_repo_health(
                        repo_performance_summary["metrics"]["target"]
                    ),
                    "system_health": self._interpret_system_health(system_resources),
                    "risk_factors": self._identify_risk_factors(repo_performance_summary),
                    "optimization_priority": self._determine_optimization_priority(
                        repo_performance_summary["recommendations"]
                    )
                }
            }
            
            return performance_summary
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {str(e)}")
            # Return a minimal set of metrics to keep the UI functioning
            return {
                "error": f"Performance metrics retrieval failed: {str(e)}",
                "timestamp": datetime.datetime.now().isoformat(),
                "system_resources": {
                    "cpu_percent": 40,
                    "memory_percent": 50,
                    "memory_used_mb": 2048,
                    "disk_io_percent": 30
                },
                "repository": {
                    "metrics": {
                        "source": {
                            "cpu_utilization": 30,
                            "memory_utilization": 40,
                            "avg_execution_time_ms": 25,
                            "operations_executed": 100
                        },
                        "target": {
                            "cpu_utilization": 35,
                            "memory_utilization": 45,
                            "avg_execution_time_ms": 30,
                            "operations_executed": 120
                        }
                    },
                    "recommendations": []
                },
                "optimal_batch_sizes": {
                    "optimal_batch_sizes": {
                        "data_transform": 150,
                        "data_validation": 300,
                        "repository_write": 80,
                        "repository_read": 200,
                        "api_request": 40
                    }
                },
                "interpretation": {
                    "source_repo_health": "healthy",
                    "target_repo_health": "healthy",
                    "system_health": {
                        "overall_status": "healthy",
                        "components": {
                            "cpu": "healthy",
                            "memory": "healthy",
                            "disk_io": "healthy"
                        },
                        "resource_interpretations": []
                    },
                    "risk_factors": [],
                    "optimization_priority": "low"
                }
            }
    
    def _interpret_repo_health(self, metrics: Dict[str, Any]) -> str:
        """Interpret repository health based on metrics"""
        if metrics.get("cpu_utilization", 0) > 80 or metrics.get("memory_utilization", 0) > 85:
            return "critical"
        elif metrics.get("cpu_utilization", 0) > 70 or metrics.get("memory_utilization", 0) > 75:
            return "warning"
        elif metrics.get("cpu_utilization", 0) > 60 or metrics.get("memory_utilization", 0) > 65:
            return "moderate"
        else:
            return "healthy"
    
    def _identify_risk_factors(self, performance_summary: Dict[str, Any]) -> List[str]:
        """Identify risk factors from performance metrics"""
        risk_factors = []
        source_metrics = performance_summary["metrics"]["source"]
        target_metrics = performance_summary["metrics"]["target"]
        
        if source_metrics.get("max_execution_time_ms", 0) > 5000:
            risk_factors.append("Very slow operations in source repository")
            
        if target_metrics.get("max_execution_time_ms", 0) > 5000:
            risk_factors.append("Very slow operations in target repository")
            
        if source_metrics.get("cpu_utilization", 0) > 85:
            risk_factors.append("Source repository CPU near capacity")
            
        if source_metrics.get("memory_utilization", 0) > 90:
            risk_factors.append("Source repository memory near capacity")
            
        if target_metrics.get("cpu_utilization", 0) > 85:
            risk_factors.append("Target repository CPU near capacity")
            
        if target_metrics.get("memory_utilization", 0) > 90:
            risk_factors.append("Target repository memory near capacity")
            
        trends = performance_summary.get("historical_trends", {})
        for repo_type, trend_data in trends.items():
            if trend_data.get("performance_trend") == "degrading":
                risk_factors.append(f"Performance degradation trend in {repo_type} repository")
                
        return risk_factors
    
    def _determine_optimization_priority(self, recommendations: List[Dict[str, Any]]) -> str:
        """Determine the overall optimization priority"""
        if any(r.get("severity") == "high" for r in recommendations):
            return "high"
        elif any(r.get("severity") == "medium" for r in recommendations):
            return "medium"
        elif any(r.get("severity") == "low" for r in recommendations):
            return "low"
        else:
            return "none"
            
    def _interpret_system_health(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret system health based on resource metrics
        
        Args:
            metrics: Dictionary with system metrics
            
        Returns:
            Dictionary with health assessments
        """
        # Default metrics if not available
        cpu_percent = metrics.get("cpu_percent", 0)
        memory_percent = metrics.get("memory_percent", 0)
        memory_used_mb = metrics.get("memory_used_mb", 0)
        disk_io_percent = metrics.get("disk_io_percent", 0)
        
        # Calculate overall system status
        if cpu_percent > 90 or memory_percent > 90:
            overall_status = "critical"
        elif cpu_percent > 75 or memory_percent > 80:
            overall_status = "warning"
        elif cpu_percent > 60 or memory_percent > 65:
            overall_status = "elevated"
        else:
            overall_status = "healthy"
            
        # Calculate specific component status
        cpu_status = "healthy"
        if cpu_percent > 90:
            cpu_status = "critical"
        elif cpu_percent > 75:
            cpu_status = "warning"
        elif cpu_percent > 60:
            cpu_status = "elevated"
            
        memory_status = "healthy"
        if memory_percent > 90:
            memory_status = "critical"
        elif memory_percent > 80:
            memory_status = "warning"
        elif memory_percent > 65:
            memory_status = "elevated"
            
        disk_status = "healthy"
        if disk_io_percent > 85:
            disk_status = "warning"
        elif disk_io_percent > 70:
            disk_status = "elevated"
            
        # Generate resource usage interpretations
        resource_interpretations = []
        
        if cpu_percent > 85:
            resource_interpretations.append(
                "CPU usage is extremely high - reduce parallel processing"
            )
        elif cpu_percent > 70:
            resource_interpretations.append(
                "CPU usage is high - consider reducing batch processing load"
            )
            
        if memory_percent > 85:
            resource_interpretations.append(
                "Memory usage is extremely high - reduce batch sizes to prevent swapping"
            )
        elif memory_percent > 75:
            resource_interpretations.append(
                "Memory usage is high - monitor for potential issues"
            )
            
        if disk_io_percent > 80:
            resource_interpretations.append(
                "Disk I/O is very high - repository operations may be slowed"
            )
            
        return {
            "overall_status": overall_status,
            "components": {
                "cpu": cpu_status,
                "memory": memory_status,
                "disk_io": disk_status
            },
            "resource_interpretations": resource_interpretations
        }
        
    def _calculate_optimal_batch_sizes(
        self, 
        system_resources: Dict[str, Any], 
        repo_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate optimal batch sizes for different operations based on
        system resources and repository performance.
        
        Args:
            system_resources: Dictionary with system resource metrics
            repo_performance: Dictionary with repository performance metrics
            
        Returns:
            Dictionary with optimal batch sizes for different operations
        """
        # Extract key metrics
        cpu_percent = system_resources.get("cpu_percent", 0)
        memory_percent = system_resources.get("memory_percent", 0)
        
        # Extract repository metrics
        source_metrics = repo_performance.get("metrics", {}).get("source", {})
        target_metrics = repo_performance.get("metrics", {}).get("target", {})
        
        source_cpu = source_metrics.get("cpu_utilization", 0)
        source_memory = source_metrics.get("memory_utilization", 0)
        target_cpu = target_metrics.get("cpu_utilization", 0)
        target_memory = target_metrics.get("memory_utilization", 0)
        
        # Base batch sizes for different operations
        base_batch_sizes = {
            "data_transform": 200,   # CPU-intensive operations
            "data_validation": 500,  # Less resource-intensive
            "repository_write": 100,   # I/O-bound operations
            "repository_read": 300,    # I/O-bound but usually faster than writes
            "api_request": 50        # Network-bound operations
        }
        
        # System resource adjustment factors
        system_factors = {}
        
        # CPU adjustments - reduce batch size under high CPU load
        if cpu_percent > 85:
            system_factors["cpu"] = 0.5  # Significant reduction
        elif cpu_percent > 70:
            system_factors["cpu"] = 0.7  # Moderate reduction
        elif cpu_percent > 50:
            system_factors["cpu"] = 0.9  # Slight reduction
        elif cpu_percent < 20:
            system_factors["cpu"] = 1.2  # Increase if CPU is underutilized
        else:
            system_factors["cpu"] = 1.0  # No change
            
        # Memory adjustments - reduce batch size under high memory pressure
        if memory_percent > 85:
            system_factors["memory"] = 0.5  # Significant reduction
        elif memory_percent > 75:
            system_factors["memory"] = 0.7  # Moderate reduction
        elif memory_percent > 60:
            system_factors["memory"] = 0.9  # Slight reduction
        elif memory_percent < 30:
            system_factors["memory"] = 1.1  # Slight increase if memory is available
        else:
            system_factors["memory"] = 1.0  # No change
            
        # Repository adjustment factors
        repo_factors = {}
        
        # Source repository adjustments
        if source_cpu > 80 or source_memory > 85:
            repo_factors["source"] = 0.6  # Significant reduction
        elif source_cpu > 65 or source_memory > 70:
            repo_factors["source"] = 0.8  # Moderate reduction
        else:
            repo_factors["source"] = 1.0  # No change
            
        # Target repository adjustments
        if target_cpu > 80 or target_memory > 85:
            repo_factors["target"] = 0.6  # Significant reduction
        elif target_cpu > 65 or target_memory > 70:
            repo_factors["target"] = 0.8  # Moderate reduction
        else:
            repo_factors["target"] = 1.0  # No change
            
        # Calculate optimal batch sizes for each operation type
        optimal_batch_sizes = {}
        adjustment_explanations = []
        
        for op_type, base_size in base_batch_sizes.items():
            # Apply different factors based on operation type
            if op_type == "data_transform":
                # CPU-intensive operations - CPU is the limiting factor
                factor = min(system_factors["cpu"], system_factors["memory"])
                adjustment_explanations.append(
                    f"{op_type}: Using {factor:.2f} factor based on CPU/memory constraints"
                )
            elif op_type in ["repository_write", "repository_read"]:
                # Repository operations - consider both system and repository factors
                if op_type == "repository_write":
                    # Writes primarily affect target repository
                    factor = min(system_factors["memory"], repo_factors["target"])
                else:
                    # Reads primarily affect source repository
                    factor = min(system_factors["memory"], repo_factors["source"])
                adjustment_explanations.append(
                    f"{op_type}: Using {factor:.2f} factor based on system/repository constraints"
                )
            elif op_type == "data_validation":
                # Validation is typically less intensive
                factor = min(system_factors["cpu"] * 1.1, system_factors["memory"])
                adjustment_explanations.append(
                    f"{op_type}: Using {factor:.2f} factor (validation is less intensive)"
                )
            else:
                # Default for other operations
                factor = min(system_factors["cpu"], system_factors["memory"])
                adjustment_explanations.append(
                    f"{op_type}: Using {factor:.2f} factor based on system constraints"
                )
                
            # Calculate adjusted batch size
            adjusted_size = int(base_size * factor)
            
            # Set reasonable limits
            optimal_batch_sizes[op_type] = max(10, min(1000, adjusted_size))
            
        return {
            "optimal_batch_sizes": optimal_batch_sizes,
            "base_batch_sizes": base_batch_sizes,
            "system_factors": system_factors,
            "repository_factors": repo_factors,
            "adjustment_explanations": adjustment_explanations
        }
    
    def resolve_data_conflicts(self, change_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect and resolve conflicts for a change record
        
        Args:
            change_record: Dictionary with change information
            
        Returns:
            Dictionary with conflict resolution results
        """
        self.logger.info(f"Checking for conflicts: {change_record['record_id']}")
        
        try:
            # Create a DetectedChange object from the record
            change = DetectedChange(
                record_id=change_record["record_id"],
                source_table=change_record["source_table"],
                change_type=ChangeType(change_record["change_type"]),
                new_data=change_record["new_data"],
                old_data=change_record.get("old_data", {}),
                timestamp=change_record.get("timestamp", datetime.datetime.now().isoformat())
            )
            
            # Detect conflicts
            conflicts = self.orchestrator.conflict_handler.detect_conflicts(change)
            
            if not conflicts:
                self.logger.info("No conflicts detected")
                return {
                    "has_conflicts": False,
                    "message": "No conflicts detected",
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
            # Resolve conflicts
            resolution = self.orchestrator.conflict_handler.resolve_conflicts(conflicts)
            
            # Add audit information
            resolution["timestamp"] = datetime.datetime.now().isoformat()
            resolution["message"] = (
                "Conflicts successfully resolved" if resolution["resolved"] 
                else "Some conflicts require manual resolution"
            )
            
            self.logger.info(
                f"Resolved {len(conflicts['conflict_fields']) - len(resolution['unresolved_fields'])} "
                f"of {len(conflicts['conflict_fields'])} conflicts"
            )
            
            return resolution
            
        except Exception as e:
            self.logger.error(f"Error in conflict resolution: {str(e)}")
            return {
                "has_conflicts": True,
                "resolved": False,
                "error": str(e),
                "message": "Error occurred during conflict resolution",
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def get_conflict_history(self, limit: int = 20) -> Dict[str, Any]:
        """
        Get the history of conflict resolutions
        
        Args:
            limit: Maximum number of history entries to return
            
        Returns:
            Dictionary with conflict history
        """
        self.logger.info(f"Getting conflict history (limit={limit})")
        
        try:
            history = self.orchestrator.conflict_handler.get_conflict_history(limit)
            
            # Add summary statistics
            total_conflicts = len(history)
            resolved_count = sum(1 for entry in history if entry.get("resolved", False))
            
            return {
                "history": history,
                "summary": {
                    "total_conflicts": total_conflicts,
                    "resolved_conflicts": resolved_count,
                    "unresolved_conflicts": total_conflicts - resolved_count,
                    "resolution_rate": resolved_count / total_conflicts if total_conflicts > 0 else 0
                },
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting conflict history: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def begin_transaction(self) -> Dict[str, Any]:
        """
        Begin a new database transaction
        
        Returns:
            Dictionary with transaction status
        """
        self.logger.info("Beginning new transaction")
        
        try:
            result = self.transaction_manager.begin_transaction()
            result["timestamp"] = datetime.datetime.now().isoformat()
            
            return result
        except Exception as e:
            self.logger.error(f"Error starting transaction: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to start transaction",
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def commit_transaction(self) -> Dict[str, Any]:
        """
        Commit the current transaction
        
        Returns:
            Dictionary with commit status
        """
        self.logger.info("Committing transaction")
        
        try:
            result = self.transaction_manager.commit_transaction()
            result["timestamp"] = datetime.datetime.now().isoformat()
            
            return result
        except Exception as e:
            self.logger.error(f"Error committing transaction: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to commit transaction",
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def rollback_transaction(self, to_savepoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Rollback the current transaction
        
        Args:
            to_savepoint: Optional savepoint to roll back to
            
        Returns:
            Dictionary with rollback status
        """
        if to_savepoint:
            self.logger.info(f"Rolling back transaction to savepoint {to_savepoint}")
        else:
            self.logger.info("Rolling back transaction")
        
        try:
            result = self.transaction_manager.rollback_transaction(to_savepoint)
            result["timestamp"] = datetime.datetime.now().isoformat()
            
            return result
        except Exception as e:
            self.logger.error(f"Error rolling back transaction: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to rollback transaction",
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def create_savepoint(self, name: str) -> Dict[str, Any]:
        """
        Create a savepoint in the current transaction
        
        Args:
            name: Savepoint name
            
        Returns:
            Dictionary with savepoint status
        """
        self.logger.info(f"Creating savepoint {name}")
        
        try:
            result = self.transaction_manager.create_savepoint(name)
            result["timestamp"] = datetime.datetime.now().isoformat()
            
            return result
        except Exception as e:
            self.logger.error(f"Error creating savepoint: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create savepoint",
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def execute_in_transaction(self, query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a query within the current transaction
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Dictionary with query execution results
        """
        self.logger.info(f"Executing query in transaction: {query[:50]}...")
        
        try:
            result = self.transaction_manager.execute_in_transaction(query, params)
            result["timestamp"] = datetime.datetime.now().isoformat()
            
            return result
        except Exception as e:
            self.logger.error(f"Error executing query in transaction: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to execute query in transaction",
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def get_transaction_status(self) -> Dict[str, Any]:
        """
        Get the current transaction status
        
        Returns:
            Dictionary with transaction status
        """
        self.logger.info("Getting transaction status")
        
        try:
            status = self.transaction_manager.get_transaction_status()
            
            # Add operation log summary
            operation_log = self.transaction_manager.get_operation_log(5)  # Last 5 operations
            
            return {
                "status": status,
                "recent_operations": operation_log,
                "timestamp": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting transaction status: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def analyze_performance_trends(self, metric_name: str = "execution_time", days: int = 30) -> Dict[str, Any]:
        """
        Analyze historical trends for a specific performance metric
        
        Args:
            metric_name: Name of the metric to analyze
            days: Number of days of history to analyze
            
        Returns:
            Dictionary with trend analysis results
        """
        self.logger.info(f"Analyzing performance trends for {metric_name} over {days} days")
        
        try:
            # Get current metrics first to ensure we have recent data
            current_metrics = self.performance_monitor.get_current_metrics()
            
            # Record current metrics for historical analysis
            self.trend_analyzer.record_metrics(current_metrics)
            
            # Analyze the trends
            trend_results = self.trend_analyzer.analyze_trends(metric_name, days)
            
            return {
                **trend_results,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing performance trends: {str(e)}")
            return {
                "metric": metric_name,
                "days": days,
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def get_optimal_sync_schedule(self) -> Dict[str, Any]:
        """
        Get optimized scheduling recommendations for sync operations
        
        Returns:
            Dictionary with scheduling recommendations
        """
        self.logger.info("Getting optimal sync schedule")
        
        try:
            # Make sure we have current metrics first
            current_metrics = self.performance_monitor.get_current_metrics()
            self.trend_analyzer.record_metrics(current_metrics)
            
            # Get optimization schedule
            schedule = self.trend_analyzer.get_optimization_schedule()
            
            return {
                **schedule,
                "generated_at": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting optimal sync schedule: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def analyze_data_quality(self, collection_name: str) -> Dict[str, Any]:
        """
        Analyze data quality for a specific collection
        
        Args:
            collection_name: Name of the collection to analyze
            
        Returns:
            Dictionary with data quality analysis results
        """
        self.logger.info(f"Analyzing data quality for collection {collection_name}")
        
        try:
            profile = self.data_quality_profiler.profile_collection(collection_name)
            
            # Check for anomalies
            anomalies = self.data_quality_profiler.detect_anomalies(collection_name)
            
            # Get quality score
            quality_score = self.data_quality_profiler.get_quality_score(collection_name)
            
            return {
                "collection_name": collection_name,
                "profile": profile,
                "anomalies": anomalies,
                "quality_score": quality_score,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing data quality: {str(e)}")
            return {
                "collection_name": collection_name,
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }