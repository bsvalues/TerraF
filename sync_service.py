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
from typing import Dict, List, Any, Optional, Union
from enum import Enum

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
    """Represents the result of validating a transformed record"""
    def __init__(
        self,
        record: TransformedRecord,
        is_valid: bool,
        errors: List[str] = None,
        warnings: List[str] = None
    ):
        self.record = record
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.validation_timestamp = datetime.datetime.now().isoformat()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "record": self.record.to_dict(),
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "validation_timestamp": self.validation_timestamp
        }


class SyncResult:
    """Represents the result of a sync operation"""
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
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
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
        
    def _calculate_duration(self) -> float:
        """Calculate duration in seconds between start and end times"""
        try:
            start = datetime.datetime.fromisoformat(self.start_time)
            end = datetime.datetime.fromisoformat(self.end_time)
            return (end - start).total_seconds()
        except (ValueError, TypeError):
            return 0.0


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
    
    def _map_operation_to_change_type(self, operation: str) -> ChangeType:
        """Map database operation to ChangeType enum"""
        op_map = {
            "INSERT": ChangeType.INSERT,
            "UPDATE": ChangeType.UPDATE,
            "DELETE": ChangeType.DELETE
        }
        return op_map.get(operation.upper(), ChangeType.NO_CHANGE)


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


class DataTransformer:
    """
    Transforms data from the source format to the target format.
    Utilizes DataTypeConverter for intelligent handling of data type differences.
    """
    def __init__(self, field_mapping_config: Dict[str, Any] = None):
        self.field_mapping = field_mapping_config or self._get_default_field_mapping()
        self.logger = logging.getLogger(self.__class__.__name__)
        # Initialize the data type converter for handling type conversions
        self.type_converter = DataTypeConverter()
        
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
                        "transformed_at": datetime.datetime.now().isoformat()
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
        
        for target_field, source_info in field_mapping.items():
            if isinstance(source_info, str):
                # Direct field mapping
                source_field = source_info
                if source_field in source_data:
                    result[target_field] = source_data[source_field]
            elif isinstance(source_info, dict):
                # Nested field mapping
                nested_result = {}
                for nested_target, nested_source in source_info.items():
                    if nested_source in source_data:
                        nested_result[nested_target] = source_data[nested_source]
                result[target_field] = nested_result
        
        # Apply transforms to fields that need them
        for field, transform_info in transforms.items():
            if field in result:
                transform_type = transform_info.get('type')
                if transform_type == 'format':
                    format_str = transform_info.get('format', '{}')
                    result[field] = format_str.format(result[field])
                elif transform_type == 'lookup':
                    lookup_map = transform_info.get('values', {})
                    result[field] = lookup_map.get(result[field], result[field])
                elif transform_type == 'combine':
                    fields = transform_info.get('fields', [])
                    separator = transform_info.get('separator', ' ')
                    values = [source_data.get(f, '') for f in fields]
                    result[field] = separator.join(str(v) for v in values if v)
        
        return result
    
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


class DataValidator:
    """
    Validates transformed data before it is written to the target system.
    """
    def __init__(self, validation_rules: Dict[str, Any] = None):
        self.validation_rules = validation_rules or self._get_default_validation_rules()
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def validate(self, records: List[TransformedRecord]) -> List[ValidationResult]:
        """
        Validate transformed records against defined rules.
        
        Args:
            records: List of transformed records
            
        Returns:
            List of validation results
        """
        self.logger.info(f"Validating {len(records)} records")
        
        validation_results = []
        for record in records:
            is_valid = True
            errors = []
            warnings = []
            
            if record.target_table in self.validation_rules:
                rules = self.validation_rules[record.target_table]
                
                # Check required fields
                for field in rules.get('required_fields', []):
                    if self._get_nested_field(record.data, field) is None:
                        is_valid = False
                        errors.append(f"Required field '{field}' is missing")
                
                # Check field types
                for field, expected_type in rules.get('field_types', {}).items():
                    value = self._get_nested_field(record.data, field)
                    if value is not None and not self._check_type(value, expected_type):
                        is_valid = False
                        errors.append(f"Field '{field}' has wrong type. Expected {expected_type}")
                
                # Check field constraints
                for field, constraints in rules.get('constraints', {}).items():
                    value = self._get_nested_field(record.data, field)
                    if value is not None:
                        # Check min/max for numeric fields
                        if 'min' in constraints and value < constraints['min']:
                            is_valid = False
                            errors.append(f"Field '{field}' value {value} is less than minimum {constraints['min']}")
                        
                        if 'max' in constraints and value > constraints['max']:
                            is_valid = False
                            errors.append(f"Field '{field}' value {value} is greater than maximum {constraints['max']}")
                        
                        # Check length for string fields
                        if 'min_length' in constraints and len(str(value)) < constraints['min_length']:
                            is_valid = False
                            errors.append(f"Field '{field}' length is less than minimum {constraints['min_length']}")
                        
                        if 'max_length' in constraints and len(str(value)) > constraints['max_length']:
                            is_valid = False
                            errors.append(f"Field '{field}' length is greater than maximum {constraints['max_length']}")
                        
                        # Check pattern for string fields
                        if 'pattern' in constraints and not re.match(constraints['pattern'], str(value)):
                            is_valid = False
                            errors.append(f"Field '{field}' does not match required pattern")
                
                # Check warning thresholds
                for field, thresholds in rules.get('warnings', {}).items():
                    value = self._get_nested_field(record.data, field)
                    if value is not None:
                        if 'min' in thresholds and value < thresholds['min']:
                            warnings.append(f"Field '{field}' value {value} is below warning threshold {thresholds['min']}")
                        
                        if 'max' in thresholds and value > thresholds['max']:
                            warnings.append(f"Field '{field}' value {value} is above warning threshold {thresholds['max']}")
            
            validation_results.append(ValidationResult(
                record=record,
                is_valid=is_valid,
                errors=errors,
                warnings=warnings
            ))
        
        valid_count = sum(1 for r in validation_results if r.is_valid)
        self.logger.info(f"Validation complete: {valid_count}/{len(records)} records valid")
        return validation_results
    
    def _get_nested_field(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get a nested field value using dot notation"""
        if '.' not in field_path:
            return data.get(field_path)
        
        parts = field_path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
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
    """
    def __init__(
        self,
        source_connection: DatabaseConnection,
        target_connection: DatabaseConnection,
        field_mapping_config: Dict[str, Any] = None,
        validation_rules: Dict[str, Any] = None
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
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def full_sync(self) -> SyncResult:
        """
        Perform a full synchronization of all data from source to target.
        
        Returns:
            SyncResult with details of the operation
        """
        self.logger.info("Starting full sync")
        start_time = datetime.datetime.now().isoformat()
        
        try:
            # Detect all changes (full sync doesn't use last_sync_time)
            changes = self.change_detector.detect_changes()
            
            # Transform the data
            transformed_records = self.transformer.transform(changes)
            
            # Validate the transformed data
            validation_results = self.validator.validate(transformed_records)
            
            # Write valid records to target
            sync_result = self._write_to_target(validation_results)
            
            # Set start time on result
            sync_result.start_time = start_time
            
            self.logger.info("Full sync completed successfully")
            return sync_result
            
        except Exception as e:
            self.logger.error(f"Full sync failed: {str(e)}")
            return SyncResult(
                success=False,
                error_details=[{"error": str(e), "type": "Exception"}],
                start_time=start_time,
                end_time=datetime.datetime.now().isoformat()
            )
    
    def incremental_sync(self, last_sync_time: str) -> SyncResult:
        """
        Perform an incremental synchronization of changes since last_sync_time.
        
        Args:
            last_sync_time: ISO-formatted timestamp of the last successful sync
            
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
            
            # Validate the transformed data
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


class DatabasePerformanceMonitor:
    """
    Monitors database performance during synchronization operations
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
        """Start monitoring database performance"""
        self.logger.info("Starting database performance monitoring")
        
        # Reset current metrics
        self.current_metrics = {
            "source": {
                "start_time": datetime.datetime.now().isoformat(),
                "queries_executed": 0,
                "rows_processed": 0,
                "execution_time_ms": 0,
                "avg_query_time_ms": 0,
                "max_query_time_ms": 0,
                "cpu_utilization": 0,
                "memory_utilization": 0,
                "io_operations": 0,
                "connections": 1
            },
            "target": {
                "start_time": datetime.datetime.now().isoformat(),
                "queries_executed": 0,
                "rows_processed": 0,
                "execution_time_ms": 0,
                "avg_query_time_ms": 0,
                "max_query_time_ms": 0,
                "cpu_utilization": 0,
                "memory_utilization": 0,
                "io_operations": 0,
                "connections": 1
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
        for db in ["source", "target"]:
            self.current_metrics[db]["end_time"] = end_time
            if self.current_metrics[db]["queries_executed"] > 0:
                self.current_metrics[db]["avg_query_time_ms"] = (
                    self.current_metrics[db]["execution_time_ms"] / 
                    self.current_metrics[db]["queries_executed"]
                )
            
            # Add to history
            self.metrics_history[db].append(self.current_metrics[db].copy())
            
            # Trim history if needed
            if len(self.metrics_history[db]) > self.max_history_size:
                self.metrics_history[db] = self.metrics_history[db][-self.max_history_size:]
        
        self.logger.info("Database performance monitoring stopped")
        return self.get_performance_summary()
    
    def record_query_metrics(self, db_type: str, query_time_ms: float, rows_affected: int) -> None:
        """
        Record metrics for a single query
        
        Args:
            db_type: "source" or "target"
            query_time_ms: Execution time in milliseconds
            rows_affected: Number of rows affected/returned
        """
        if db_type not in self.current_metrics:
            return
            
        metrics = self.current_metrics[db_type]
        metrics["queries_executed"] += 1
        metrics["rows_processed"] += rows_affected
        metrics["execution_time_ms"] += query_time_ms
        
        if query_time_ms > metrics["max_query_time_ms"]:
            metrics["max_query_time_ms"] = query_time_ms
    
    def simulate_system_metrics(self, db_type: str) -> None:
        """
        Simulate system-level metrics for demo purposes
        
        Args:
            db_type: "source" or "target"
        """
        if db_type not in self.current_metrics:
            return
            
        metrics = self.current_metrics[db_type]
        
        # Simulate CPU, memory, and IO based on query activity
        query_activity = min(100, metrics["queries_executed"] * 2)
        
        # Generate realistic metrics
        metrics["cpu_utilization"] = min(90, 30 + query_activity / 3 + random.randint(-5, 5))
        metrics["memory_utilization"] = min(90, 40 + query_activity / 4 + random.randint(-3, 3))
        metrics["io_operations"] = metrics["queries_executed"] * 3 + metrics["rows_processed"] / 10
    
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
        
        # Source database recommendations
        source_metrics = self.current_metrics["source"]
        if source_metrics.get("max_query_time_ms", 0) > 1000:
            recommendations.append({
                "database": "source",
                "type": "query_optimization",
                "severity": "high",
                "description": "Long-running queries detected in source database",
                "action": "Analyze slow queries and optimize with appropriate indexes"
            })
            
        if source_metrics.get("cpu_utilization", 0) > 80:
            recommendations.append({
                "database": "source",
                "type": "resource_allocation",
                "severity": "high",
                "description": "High CPU utilization in source database",
                "action": "Increase CPU allocation or optimize query execution"
            })
            
        # Target database recommendations  
        target_metrics = self.current_metrics["target"]
        if target_metrics.get("io_operations", 0) > 1000:
            recommendations.append({
                "database": "target",
                "type": "io_optimization",
                "severity": "medium",
                "description": "High I/O operations detected in target database",
                "action": "Consider batch operations and optimize write patterns"
            })
            
        if source_metrics.get("avg_query_time_ms", 0) > 500:
            recommendations.append({
                "database": "source",
                "type": "index_recommendation",
                "severity": "medium",
                "description": "Queries average execution time is high",
                "action": "Add indexes on frequently queried columns"
            })
            
        # General recommendations
        if len(self.metrics_history["source"]) >= 3:
            recommendations.append({
                "database": "both",
                "type": "sync_schedule",
                "severity": "low",
                "description": "Consider optimizing sync schedule based on database load",
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
        
        for db_type in ["source", "target"]:
            if len(self.metrics_history[db_type]) < 2:
                continue
                
            # Analyze last 5 samples or all if less than 5
            samples = self.metrics_history[db_type][-5:]
            
            # Extract metrics for trending
            cpu_trend = [s.get("cpu_utilization", 0) for s in samples]
            query_time_trend = [s.get("avg_query_time_ms", 0) for s in samples]
            
            # Calculate trends (positive = increasing, negative = decreasing)
            if len(cpu_trend) >= 2:
                trends[db_type]["cpu_trend"] = self._calculate_trend(cpu_trend)
            
            if len(query_time_trend) >= 2:
                trends[db_type]["query_time_trend"] = self._calculate_trend(query_time_trend)
                
            # Add qualitative assessment
            trends[db_type]["performance_trend"] = "stable"
            if db_type in trends and "query_time_trend" in trends[db_type]:
                if trends[db_type]["query_time_trend"] > 0.1:
                    trends[db_type]["performance_trend"] = "degrading"
                elif trends[db_type]["query_time_trend"] < -0.1:
                    trends[db_type]["performance_trend"] = "improving"
        
        return trends
    
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


class SyncService:
    """
    Main service class that provides the API for the SyncService.
    """
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
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
        
        # Initialize the schema comparison tool
        self.schema_comparison_tool = SchemaComparisonTool(
            source_connection=self.source_connection,
            target_connection=self.target_connection
        )
        
        # Initialize the database performance monitor
        self.performance_monitor = DatabasePerformanceMonitor(
            source_connection=self.source_connection,
            target_connection=self.target_connection
        )
        
        # Initialize the orchestrator
        self.orchestrator = SyncOrchestrator(
            source_connection=self.source_connection,
            target_connection=self.target_connection
        )
        
        # Track sync history
        self.last_sync_time = None
        self.sync_history = []
    
    def full_sync(self) -> Dict[str, Any]:
        """
        Perform a full sync from PACS to CAMA.
        
        Returns:
            Dictionary with sync results
        """
        self.logger.info("Full sync requested")
        
        result = self.orchestrator.full_sync()
        
        # Store sync information
        if result.success:
            self.last_sync_time = result.end_time
            
        self.sync_history.append({
            "type": "full",
            "timestamp": result.end_time,
            "success": result.success,
            "records_processed": result.records_processed,
            "records_succeeded": result.records_succeeded
        })
        
        return result.to_dict()
    
    def incremental_sync(self) -> Dict[str, Any]:
        """
        Perform an incremental sync from PACS to CAMA.
        
        Returns:
            Dictionary with sync results
        """
        self.logger.info("Incremental sync requested")
        
        # If no last sync time, do a full sync
        if self.last_sync_time is None:
            self.logger.info("No last sync time, performing full sync instead")
            return self.full_sync()
        
        result = self.orchestrator.incremental_sync(self.last_sync_time)
        
        # Store sync information
        if result.success:
            self.last_sync_time = result.end_time
            
        self.sync_history.append({
            "type": "incremental",
            "timestamp": result.end_time,
            "success": result.success,
            "records_processed": result.records_processed,
            "records_succeeded": result.records_succeeded
        })
        
        return result.to_dict()
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get the current sync status and history.
        
        Returns:
            Dictionary with sync status information
        """
        return {
            "last_sync_time": self.last_sync_time,
            "sync_history": self.sync_history[-5:],  # Last 5 sync operations
            "active": True,
            "version": "1.0.0"
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
        Get database performance metrics and recommendations.
        
        Returns:
            Dictionary with performance metrics and recommendations
        """
        self.logger.info("Getting database performance metrics")
        
        try:
            performance_summary = self.performance_monitor.get_performance_summary()
            
            # Add additional context for easier interpretation
            performance_summary["interpretation"] = {
                "source_db_health": self._interpret_db_health(
                    performance_summary["metrics"]["source"]
                ),
                "target_db_health": self._interpret_db_health(
                    performance_summary["metrics"]["target"]
                ),
                "risk_factors": self._identify_risk_factors(performance_summary),
                "optimization_priority": self._determine_optimization_priority(
                    performance_summary["recommendations"]
                )
            }
            
            return performance_summary
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {str(e)}")
            return {
                "error": f"Performance metrics retrieval failed: {str(e)}",
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def _interpret_db_health(self, metrics: Dict[str, Any]) -> str:
        """Interpret database health based on metrics"""
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
        
        if source_metrics.get("max_query_time_ms", 0) > 5000:
            risk_factors.append("Very slow queries in source database")
            
        if target_metrics.get("max_query_time_ms", 0) > 5000:
            risk_factors.append("Very slow queries in target database")
            
        if source_metrics.get("cpu_utilization", 0) > 85:
            risk_factors.append("Source database CPU near capacity")
            
        if source_metrics.get("memory_utilization", 0) > 90:
            risk_factors.append("Source database memory near capacity")
            
        if target_metrics.get("cpu_utilization", 0) > 85:
            risk_factors.append("Target database CPU near capacity")
            
        if target_metrics.get("memory_utilization", 0) > 90:
            risk_factors.append("Target database memory near capacity")
            
        trends = performance_summary.get("historical_trends", {})
        for db_type, trend_data in trends.items():
            if trend_data.get("performance_trend") == "degrading":
                risk_factors.append(f"Performance degradation trend in {db_type} database")
                
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