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


class ChangeDetector:
    """
    Detects changes in the source system that need to be synchronized
    to the target system.
    """
    def __init__(self, source_connection: DatabaseConnection):
        self.source_connection = source_connection
        self.logger = logging.getLogger(self.__class__.__name__)
        
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


class DataTransformer:
    """
    Transforms data from the source format to the target format.
    """
    def __init__(self, field_mapping_config: Dict[str, Any] = None):
        self.field_mapping = field_mapping_config or self._get_default_field_mapping()
        self.logger = logging.getLogger(self.__class__.__name__)
        
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