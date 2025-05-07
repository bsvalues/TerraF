"""
Schema Versioning System for TerraFlow Platform

This module provides a schema versioning system that enables smooth transitions
between different database schema versions. It tracks schema changes, applies
migrations, and ensures backward compatibility.
"""

import os
import json
import time
import uuid
import logging
import importlib
import inspect
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Set, Type, TypeVar, Generic
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaVersionStatus(Enum):
    """Possible statuses for a schema version"""
    DRAFT = "draft"
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    DEPRECATED = "deprecated"

T = TypeVar('T')

class SchemaVersion(Generic[T]):
    """
    Represents a version of a database schema
    
    This class tracks the version number, changes, and status of a schema version.
    """
    
    def __init__(self,
                version: str,
                schema: Type[T],
                description: str,
                changes: List[str],
                created_by: str = "system",
                status: SchemaVersionStatus = SchemaVersionStatus.DRAFT):
        """
        Initialize a new schema version
        
        Args:
            version: The version number (semver recommended)
            schema: The schema class or definition
            description: A description of this version
            changes: List of changes made in this version
            created_by: Who created this version
            status: The status of this version
        """
        self.version = version
        self.schema = schema
        self.description = description
        self.changes = changes
        self.created_by = created_by
        self.status = status
        self.created_at = time.time()
        self.applied_at = None
    
    def update_status(self, status: SchemaVersionStatus, applied_at: Optional[float] = None):
        """
        Update the status of this version
        
        Args:
            status: The new status
            applied_at: When the schema was applied (for APPLIED status)
        """
        self.status = status
        
        if status == SchemaVersionStatus.APPLIED and applied_at is None:
            self.applied_at = time.time()
        elif applied_at is not None:
            self.applied_at = applied_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "version": self.version,
            "description": self.description,
            "changes": self.changes,
            "created_by": self.created_by,
            "status": self.status.value,
            "created_at": self.created_at,
            "applied_at": self.applied_at,
            # Schema is not serialized as it's a class/type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], schema_class: Type[T]) -> 'SchemaVersion[T]':
        """Create from dictionary"""
        version = cls(
            version=data["version"],
            schema=schema_class,
            description=data["description"],
            changes=data["changes"],
            created_by=data["created_by"],
            status=SchemaVersionStatus(data["status"])
        )
        
        version.created_at = data.get("created_at", time.time())
        version.applied_at = data.get("applied_at")
        
        return version

class Migration:
    """
    Represents a migration between two schema versions
    
    This class defines how to migrate data from one schema version to another.
    """
    
    def __init__(self,
                migration_id: str,
                from_version: str,
                to_version: str,
                description: str,
                migration_fn: Optional[Callable[[Any], Any]] = None,
                reverse_migration_fn: Optional[Callable[[Any], Any]] = None):
        """
        Initialize a new migration
        
        Args:
            migration_id: Unique identifier for this migration
            from_version: Source schema version
            to_version: Target schema version
            description: Description of this migration
            migration_fn: Function to migrate data from source to target
            reverse_migration_fn: Function to migrate data from target to source
        """
        self.migration_id = migration_id
        self.from_version = from_version
        self.to_version = to_version
        self.description = description
        self.migration_fn = migration_fn
        self.reverse_migration_fn = reverse_migration_fn
        self.created_at = time.time()
    
    def apply(self, data: Any) -> Any:
        """
        Apply this migration to some data
        
        Args:
            data: The data to migrate
            
        Returns:
            Any: The migrated data
        
        Raises:
            ValueError: If no migration function is defined
        """
        if self.migration_fn is None:
            raise ValueError(f"No migration function defined for {self.migration_id}")
        
        return self.migration_fn(data)
    
    def reverse(self, data: Any) -> Any:
        """
        Apply the reverse of this migration to some data
        
        Args:
            data: The data to migrate
            
        Returns:
            Any: The migrated data
            
        Raises:
            ValueError: If no reverse migration function is defined
        """
        if self.reverse_migration_fn is None:
            raise ValueError(f"No reverse migration function defined for {self.migration_id}")
        
        return self.reverse_migration_fn(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "migration_id": self.migration_id,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "description": self.description,
            "created_at": self.created_at,
            # Functions are not serialized
        }

class SchemaRegistry:
    """
    Registry for schema versions and migrations
    
    This class manages schema versions and the migrations between them.
    """
    
    def __init__(self, schema_type: str, data_dir: str = "data/schemas"):
        """
        Initialize a new schema registry
        
        Args:
            schema_type: The type of schema this registry manages
            data_dir: Directory for storing schema data
        """
        self.schema_type = schema_type
        self.data_dir = data_dir
        self.versions = {}  # version -> SchemaVersion
        self.migrations = {}  # migration_id -> Migration
        self.version_migrations = {}  # (from_version, to_version) -> migration_id
        self.current_version = None
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.join(data_dir, schema_type), exist_ok=True)
        
        # Load existing schemas and migrations
        self._load_data()
    
    def _get_schema_path(self) -> str:
        """Get path for schema versions file"""
        return os.path.join(self.data_dir, self.schema_type, "versions.json")
    
    def _get_migrations_path(self) -> str:
        """Get path for migrations file"""
        return os.path.join(self.data_dir, self.schema_type, "migrations.json")
    
    def _get_current_version_path(self) -> str:
        """Get path for current version file"""
        return os.path.join(self.data_dir, self.schema_type, "current_version.json")
    
    def _load_data(self):
        """Load schema versions and migrations from disk"""
        # Load schema versions
        schema_path = self._get_schema_path()
        if os.path.exists(schema_path):
            try:
                with open(schema_path, "r") as f:
                    versions_data = json.load(f)
                
                # We need to import the schema classes dynamically
                module_name = f"infrastructure.data.schemas.{self.schema_type}"
                try:
                    module = importlib.import_module(module_name)
                    
                    for version, version_data in versions_data.items():
                        # Get the schema class from the module
                        schema_class_name = f"{self.schema_type.capitalize()}Schema_{version.replace('.', '_')}"
                        schema_class = getattr(module, schema_class_name, None)
                        
                        if schema_class:
                            self.versions[version] = SchemaVersion.from_dict(version_data, schema_class)
                        else:
                            logger.warning(f"Schema class {schema_class_name} not found in module {module_name}")
                    
                    logger.info(f"Loaded {len(self.versions)} schema versions for {self.schema_type}")
                    
                except ImportError:
                    logger.error(f"Error importing module {module_name}")
                
            except Exception as e:
                logger.error(f"Error loading schema versions: {str(e)}")
        
        # Load migrations
        migrations_path = self._get_migrations_path()
        if os.path.exists(migrations_path):
            try:
                with open(migrations_path, "r") as f:
                    migrations_data = json.load(f)
                
                # We need to import the migration functions dynamically
                module_name = f"infrastructure.data.migrations.{self.schema_type}"
                try:
                    module = importlib.import_module(module_name)
                    
                    for migration_id, migration_data in migrations_data.items():
                        # Get the migration functions from the module
                        migration_fn_name = f"migrate_{migration_data['from_version'].replace('.', '_')}_to_{migration_data['to_version'].replace('.', '_')}"
                        reverse_migration_fn_name = f"migrate_{migration_data['to_version'].replace('.', '_')}_to_{migration_data['from_version'].replace('.', '_')}"
                        
                        migration_fn = getattr(module, migration_fn_name, None)
                        reverse_migration_fn = getattr(module, reverse_migration_fn_name, None)
                        
                        if migration_fn:
                            migration = Migration(
                                migration_id=migration_id,
                                from_version=migration_data["from_version"],
                                to_version=migration_data["to_version"],
                                description=migration_data["description"],
                                migration_fn=migration_fn,
                                reverse_migration_fn=reverse_migration_fn
                            )
                            
                            migration.created_at = migration_data.get("created_at", time.time())
                            
                            self.migrations[migration_id] = migration
                            self.version_migrations[(migration.from_version, migration.to_version)] = migration_id
                        else:
                            logger.warning(f"Migration function {migration_fn_name} not found in module {module_name}")
                    
                    logger.info(f"Loaded {len(self.migrations)} migrations for {self.schema_type}")
                    
                except ImportError:
                    logger.error(f"Error importing module {module_name}")
                
            except Exception as e:
                logger.error(f"Error loading migrations: {str(e)}")
        
        # Load current version
        current_version_path = self._get_current_version_path()
        if os.path.exists(current_version_path):
            try:
                with open(current_version_path, "r") as f:
                    current_version_data = json.load(f)
                
                self.current_version = current_version_data.get("version")
                
                logger.info(f"Current version for {self.schema_type}: {self.current_version}")
                
            except Exception as e:
                logger.error(f"Error loading current version: {str(e)}")
    
    def _save_data(self):
        """Save schema versions and migrations to disk"""
        # Save schema versions
        schema_path = self._get_schema_path()
        try:
            versions_data = {version: version_obj.to_dict() for version, version_obj in self.versions.items()}
            
            with open(schema_path, "w") as f:
                json.dump(versions_data, f, indent=2)
            
            logger.debug(f"Saved schema versions for {self.schema_type}")
            
        except Exception as e:
            logger.error(f"Error saving schema versions: {str(e)}")
        
        # Save migrations
        migrations_path = self._get_migrations_path()
        try:
            migrations_data = {migration_id: migration.to_dict() for migration_id, migration in self.migrations.items()}
            
            with open(migrations_path, "w") as f:
                json.dump(migrations_data, f, indent=2)
            
            logger.debug(f"Saved migrations for {self.schema_type}")
            
        except Exception as e:
            logger.error(f"Error saving migrations: {str(e)}")
        
        # Save current version
        current_version_path = self._get_current_version_path()
        try:
            current_version_data = {"version": self.current_version}
            
            with open(current_version_path, "w") as f:
                json.dump(current_version_data, f, indent=2)
            
            logger.debug(f"Saved current version for {self.schema_type}")
            
        except Exception as e:
            logger.error(f"Error saving current version: {str(e)}")
    
    def register_version(self, version: SchemaVersion) -> bool:
        """
        Register a new schema version
        
        Args:
            version: The schema version to register
            
        Returns:
            bool: True if the version was registered, False otherwise
        """
        if version.version in self.versions:
            logger.warning(f"Schema version {version.version} already exists for {self.schema_type}")
            return False
        
        # Register version
        self.versions[version.version] = version
        
        # Save data
        self._save_data()
        
        logger.info(f"Registered schema version {version.version} for {self.schema_type}")
        
        return True
    
    def register_migration(self, migration: Migration) -> bool:
        """
        Register a new migration
        
        Args:
            migration: The migration to register
            
        Returns:
            bool: True if the migration was registered, False otherwise
        """
        if migration.migration_id in self.migrations:
            logger.warning(f"Migration {migration.migration_id} already exists for {self.schema_type}")
            return False
        
        if (migration.from_version, migration.to_version) in self.version_migrations:
            logger.warning(f"Migration from {migration.from_version} to {migration.to_version} already exists for {self.schema_type}")
            return False
        
        # Check that both versions exist
        if migration.from_version not in self.versions:
            logger.warning(f"Source version {migration.from_version} does not exist for {self.schema_type}")
            return False
        
        if migration.to_version not in self.versions:
            logger.warning(f"Target version {migration.to_version} does not exist for {self.schema_type}")
            return False
        
        # Register migration
        self.migrations[migration.migration_id] = migration
        self.version_migrations[(migration.from_version, migration.to_version)] = migration.migration_id
        
        # Save data
        self._save_data()
        
        logger.info(f"Registered migration from {migration.from_version} to {migration.to_version} for {self.schema_type}")
        
        return True
    
    def get_version(self, version: str) -> Optional[SchemaVersion]:
        """
        Get a schema version
        
        Args:
            version: The version to get
            
        Returns:
            Optional[SchemaVersion]: The schema version, or None if not found
        """
        return self.versions.get(version)
    
    def get_current_version(self) -> Optional[SchemaVersion]:
        """
        Get the current schema version
        
        Returns:
            Optional[SchemaVersion]: The current schema version, or None if not set
        """
        if self.current_version:
            return self.versions.get(self.current_version)
        return None
    
    def get_migration(self, from_version: str, to_version: str) -> Optional[Migration]:
        """
        Get a migration between two versions
        
        Args:
            from_version: Source version
            to_version: Target version
            
        Returns:
            Optional[Migration]: The migration, or None if not found
        """
        migration_id = self.version_migrations.get((from_version, to_version))
        if migration_id:
            return self.migrations.get(migration_id)
        return None
    
    def find_migration_path(self, from_version: str, to_version: str) -> List[Migration]:
        """
        Find a path of migrations between two versions
        
        Args:
            from_version: Source version
            to_version: Target version
            
        Returns:
            List[Migration]: List of migrations to apply in order, or empty list if no path found
        """
        # If versions are the same, no migration needed
        if from_version == to_version:
            return []
        
        # Check for direct migration
        direct_migration = self.get_migration(from_version, to_version)
        if direct_migration:
            return [direct_migration]
        
        # Try to find a path using breadth-first search
        visited = set([from_version])
        queue = [(from_version, [])]
        
        while queue:
            current_version, path = queue.pop(0)
            
            # Get all migrations from current version
            for (source, target), migration_id in self.version_migrations.items():
                if source == current_version and target not in visited:
                    migration = self.migrations[migration_id]
                    new_path = path + [migration]
                    
                    if target == to_version:
                        # Found a path
                        return new_path
                    
                    visited.add(target)
                    queue.append((target, new_path))
        
        # No path found
        return []
    
    def set_current_version(self, version: str) -> bool:
        """
        Set the current schema version
        
        Args:
            version: The version to set as current
            
        Returns:
            bool: True if the version was set, False otherwise
        """
        if version not in self.versions:
            logger.warning(f"Schema version {version} does not exist for {self.schema_type}")
            return False
        
        # Update version status
        for v, version_obj in self.versions.items():
            if v == version:
                version_obj.update_status(SchemaVersionStatus.APPLIED)
            elif version_obj.status == SchemaVersionStatus.APPLIED:
                version_obj.update_status(SchemaVersionStatus.DEPRECATED)
        
        self.current_version = version
        
        # Save data
        self._save_data()
        
        logger.info(f"Set current version to {version} for {self.schema_type}")
        
        return True
    
    def migrate_data(self, data: Any, from_version: str, to_version: str) -> Any:
        """
        Migrate data from one version to another
        
        Args:
            data: The data to migrate
            from_version: Source version
            to_version: Target version
            
        Returns:
            Any: The migrated data
            
        Raises:
            ValueError: If no migration path is found
        """
        # Find migration path
        migration_path = self.find_migration_path(from_version, to_version)
        
        if not migration_path:
            raise ValueError(f"No migration path found from {from_version} to {to_version}")
        
        # Apply migrations in order
        migrated_data = data
        
        for migration in migration_path:
            migrated_data = migration.apply(migrated_data)
        
        return migrated_data
    
    def validate_schema(self, data: Any, version: Optional[str] = None) -> bool:
        """
        Validate data against a schema version
        
        Args:
            data: The data to validate
            version: The version to validate against (defaults to current version)
            
        Returns:
            bool: True if the data is valid, False otherwise
            
        Raises:
            ValueError: If the version is not found
        """
        # Get version
        if version is None:
            version = self.current_version
        
        if not version:
            raise ValueError("No version specified and no current version set")
        
        version_obj = self.versions.get(version)
        
        if not version_obj:
            raise ValueError(f"Schema version {version} not found")
        
        # Validate data against schema
        schema_class = version_obj.schema
        
        try:
            # Check if schema_class is a dataclass
            if hasattr(schema_class, "__dataclass_fields__"):
                schema_class(**data)
                return True
            
            # Check if schema_class is a Pydantic model
            if hasattr(schema_class, "model_validate"):
                schema_class.model_validate(data)
                return True
            
            # Check if schema_class has a validate method
            if hasattr(schema_class, "validate"):
                schema_class.validate(data)
                return True
            
            # Check if schema_class is a class with a constructor that takes the data
            try:
                schema_class(**data)
                return True
            except:
                pass
            
            logger.warning(f"Unable to validate data against schema {schema_class.__name__}")
            return False
            
        except Exception as e:
            logger.warning(f"Validation error: {str(e)}")
            return False