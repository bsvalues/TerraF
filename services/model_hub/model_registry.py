"""
Model Registry

This module implements the core functionality of the model registry,
which manages the lifecycle of AI models in the system.
"""
import os
import json
import time
import uuid
import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from datetime import datetime

class ModelStatus(Enum):
    """Possible statuses for a model in the registry"""
    DRAFT = "draft"
    TRAINING = "training"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


class ModelType(Enum):
    """Types of models supported by the system"""
    CODE_ANALYSIS = "code_analysis"
    ARCHITECTURE = "architecture"
    DATABASE = "database"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    MULTIMODAL = "multimodal"
    NEURO_SYMBOLIC = "neuro_symbolic"


class ModelFamily(Enum):
    """Model families/providers supported by the system"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    CUSTOM = "custom"


class ModelRegistry:
    """
    Central registry for AI models in the system.
    
    This class provides:
    - Model registration and discovery
    - Model versioning
    - Model evaluation and benchmarking
    - A/B testing framework
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the model registry.
        
        Args:
            storage_dir: Directory to store model metadata and artifacts
        """
        self.models = {}
        self.versions = {}
        self.evaluations = {}
        self.experiments = {}
        self.logger = logging.getLogger('model_registry')
        
        # Set up storage directory
        if storage_dir is None:
            storage_dir = os.path.join(os.path.dirname(__file__), 'storage')
        
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Load existing models
        self._load_models()
    
    def _load_models(self) -> None:
        """Load models from storage directory."""
        models_dir = os.path.join(self.storage_dir, 'models')
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
            return
        
        # Load model metadata
        for model_id in os.listdir(models_dir):
            model_path = os.path.join(models_dir, model_id, 'metadata.json')
            if os.path.exists(model_path):
                try:
                    with open(model_path, 'r') as f:
                        self.models[model_id] = json.load(f)
                    
                    # Load versions
                    versions_dir = os.path.join(models_dir, model_id, 'versions')
                    if os.path.exists(versions_dir):
                        self.versions[model_id] = {}
                        for version_id in os.listdir(versions_dir):
                            version_path = os.path.join(versions_dir, version_id, 'metadata.json')
                            if os.path.exists(version_path):
                                with open(version_path, 'r') as f:
                                    self.versions[model_id][version_id] = json.load(f)
                except Exception as e:
                    self.logger.error(f"Failed to load model {model_id}: {str(e)}")
    
    def register_model(self, name: str, model_type: ModelType, model_family: ModelFamily, 
                       description: str, features: List[str], 
                       configuration: Dict[str, Any]) -> str:
        """
        Register a new model in the registry.
        
        Args:
            name: Human-readable name of the model
            model_type: Type of model
            model_family: Family/provider of the model
            description: Description of the model
            features: List of features/capabilities the model provides
            configuration: Model-specific configuration parameters
            
        Returns:
            Unique ID of the registered model
        """
        # Generate a unique ID for the model
        model_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        # Create model metadata
        model_metadata = {
            'id': model_id,
            'name': name,
            'type': model_type.value,
            'family': model_family.value,
            'description': description,
            'features': features,
            'configuration': configuration,
            'created_at': created_at,
            'updated_at': created_at,
            'status': ModelStatus.DRAFT.value,
            'latest_version': None,
            'production_version': None
        }
        
        # Save model metadata
        self._save_model_metadata(model_id, model_metadata)
        
        # Add to in-memory registry
        self.models[model_id] = model_metadata
        self.versions[model_id] = {}
        
        self.logger.info(f"Registered new model: {name} (ID: {model_id})")
        return model_id
    
    def _save_model_metadata(self, model_id: str, metadata: Dict[str, Any]) -> None:
        """
        Save model metadata to storage.
        
        Args:
            model_id: ID of the model
            metadata: Model metadata
        """
        model_dir = os.path.join(self.storage_dir, 'models', model_id)
        os.makedirs(model_dir, exist_ok=True)
        
        metadata_path = os.path.join(model_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def register_model_version(self, model_id: str, version_name: str, 
                              artifact_uri: str, configuration: Dict[str, Any],
                              metrics: Optional[Dict[str, float]] = None) -> str:
        """
        Register a new version of an existing model.
        
        Args:
            model_id: ID of the parent model
            version_name: Name for this version
            artifact_uri: URI pointing to the model artifacts
            configuration: Version-specific configuration
            metrics: Optional performance metrics
            
        Returns:
            Version ID
        """
        if model_id not in self.models:
            raise ValueError(f"Model with ID {model_id} not found")
        
        # Generate a version ID
        version_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        # Create version metadata
        version_metadata = {
            'id': version_id,
            'model_id': model_id,
            'name': version_name,
            'artifact_uri': artifact_uri,
            'configuration': configuration,
            'metrics': metrics or {},
            'created_at': created_at,
            'status': ModelStatus.DRAFT.value,
            'is_latest': True,
            'is_production': False
        }
        
        # Update previous latest version
        if model_id in self.versions:
            for prev_version_id, prev_version in self.versions[model_id].items():
                if prev_version.get('is_latest', False):
                    prev_version['is_latest'] = False
                    self._save_version_metadata(model_id, prev_version_id, prev_version)
        
        # Save version metadata
        self._save_version_metadata(model_id, version_id, version_metadata)
        
        # Update model metadata
        model = self.models[model_id]
        model['latest_version'] = version_id
        model['updated_at'] = created_at
        self._save_model_metadata(model_id, model)
        
        # Add to in-memory registry
        if model_id not in self.versions:
            self.versions[model_id] = {}
        
        self.versions[model_id][version_id] = version_metadata
        
        self.logger.info(f"Registered new version {version_name} (ID: {version_id}) for model {model_id}")
        return version_id
    
    def _save_version_metadata(self, model_id: str, version_id: str, metadata: Dict[str, Any]) -> None:
        """
        Save version metadata to storage.
        
        Args:
            model_id: ID of the parent model
            version_id: ID of the version
            metadata: Version metadata
        """
        version_dir = os.path.join(self.storage_dir, 'models', model_id, 'versions', version_id)
        os.makedirs(version_dir, exist_ok=True)
        
        metadata_path = os.path.join(version_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a model.
        
        Args:
            model_id: ID of the model
            
        Returns:
            Model metadata or None if not found
        """
        return self.models.get(model_id)
    
    def get_model_version(self, model_id: str, version_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific model version.
        
        Args:
            model_id: ID of the model
            version_id: ID of the version
            
        Returns:
            Version metadata or None if not found
        """
        if model_id not in self.versions:
            return None
        
        return self.versions[model_id].get(version_id)
    
    def get_latest_version(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest version of a model.
        
        Args:
            model_id: ID of the model
            
        Returns:
            Latest version metadata or None if not found
        """
        if model_id not in self.models or model_id not in self.versions:
            return None
        
        latest_version_id = self.models[model_id].get('latest_version')
        if not latest_version_id:
            return None
        
        return self.versions[model_id].get(latest_version_id)
    
    def get_production_version(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the production version of a model.
        
        Args:
            model_id: ID of the model
            
        Returns:
            Production version metadata or None if not found
        """
        if model_id not in self.models or model_id not in self.versions:
            return None
        
        production_version_id = self.models[model_id].get('production_version')
        if not production_version_id:
            return None
        
        return self.versions[model_id].get(production_version_id)
    
    def promote_to_production(self, model_id: str, version_id: str) -> bool:
        """
        Promote a specific version to production.
        
        Args:
            model_id: ID of the model
            version_id: ID of the version to promote
            
        Returns:
            Success flag
        """
        if model_id not in self.models or model_id not in self.versions:
            return False
        
        if version_id not in self.versions[model_id]:
            return False
        
        # Update current production version if any
        current_production_id = self.models[model_id].get('production_version')
        if current_production_id and current_production_id in self.versions[model_id]:
            current_production = self.versions[model_id][current_production_id]
            current_production['is_production'] = False
            current_production['status'] = ModelStatus.STAGING.value
            self._save_version_metadata(model_id, current_production_id, current_production)
        
        # Update new production version
        new_production = self.versions[model_id][version_id]
        new_production['is_production'] = True
        new_production['status'] = ModelStatus.PRODUCTION.value
        self._save_version_metadata(model_id, version_id, new_production)
        
        # Update model metadata
        model = self.models[model_id]
        model['production_version'] = version_id
        model['status'] = ModelStatus.PRODUCTION.value
        model['updated_at'] = datetime.now().isoformat()
        self._save_model_metadata(model_id, model)
        
        self.logger.info(f"Promoted version {version_id} of model {model_id} to production")
        return True
    
    def list_models(self, model_type: Optional[ModelType] = None, 
                   status: Optional[ModelStatus] = None) -> List[Dict[str, Any]]:
        """
        List models in the registry, optionally filtered by type or status.
        
        Args:
            model_type: Optional filter by model type
            status: Optional filter by status
            
        Returns:
            List of model metadata
        """
        result = []
        
        for model_id, model in self.models.items():
            # Apply filters
            if model_type and model['type'] != model_type.value:
                continue
            
            if status and model['status'] != status.value:
                continue
            
            result.append(model)
        
        return result
    
    def list_model_versions(self, model_id: str) -> List[Dict[str, Any]]:
        """
        List all versions of a specific model.
        
        Args:
            model_id: ID of the model
            
        Returns:
            List of version metadata
        """
        if model_id not in self.versions:
            return []
        
        return list(self.versions[model_id].values())
    
    def update_model_status(self, model_id: str, status: ModelStatus) -> bool:
        """
        Update the status of a model.
        
        Args:
            model_id: ID of the model
            status: New status
            
        Returns:
            Success flag
        """
        if model_id not in self.models:
            return False
        
        # Update model metadata
        model = self.models[model_id]
        model['status'] = status.value
        model['updated_at'] = datetime.now().isoformat()
        self._save_model_metadata(model_id, model)
        
        self.logger.info(f"Updated status of model {model_id} to {status.value}")
        return True
    
    def update_version_status(self, model_id: str, version_id: str, status: ModelStatus) -> bool:
        """
        Update the status of a model version.
        
        Args:
            model_id: ID of the model
            version_id: ID of the version
            status: New status
            
        Returns:
            Success flag
        """
        if model_id not in self.versions or version_id not in self.versions[model_id]:
            return False
        
        # Update version metadata
        version = self.versions[model_id][version_id]
        version['status'] = status.value
        self._save_version_metadata(model_id, version_id, version)
        
        self.logger.info(f"Updated status of version {version_id} of model {model_id} to {status.value}")
        return True
    
    def register_evaluation(self, model_id: str, version_id: str, 
                           metrics: Dict[str, float], dataset_id: str,
                           parameters: Dict[str, Any]) -> str:
        """
        Register an evaluation result for a model version.
        
        Args:
            model_id: ID of the model
            version_id: ID of the version
            metrics: Evaluation metrics
            dataset_id: ID of the dataset used for evaluation
            parameters: Evaluation parameters
            
        Returns:
            Evaluation ID
        """
        if model_id not in self.versions or version_id not in self.versions[model_id]:
            raise ValueError(f"Model version {version_id} of model {model_id} not found")
        
        # Generate an evaluation ID
        evaluation_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        # Create evaluation metadata
        evaluation_metadata = {
            'id': evaluation_id,
            'model_id': model_id,
            'version_id': version_id,
            'metrics': metrics,
            'dataset_id': dataset_id,
            'parameters': parameters,
            'created_at': created_at
        }
        
        # Save evaluation metadata
        evaluation_dir = os.path.join(self.storage_dir, 'evaluations', model_id, version_id)
        os.makedirs(evaluation_dir, exist_ok=True)
        
        evaluation_path = os.path.join(evaluation_dir, f"{evaluation_id}.json")
        with open(evaluation_path, 'w') as f:
            json.dump(evaluation_metadata, f, indent=2)
        
        # Add to in-memory registry
        if model_id not in self.evaluations:
            self.evaluations[model_id] = {}
        
        if version_id not in self.evaluations[model_id]:
            self.evaluations[model_id][version_id] = {}
        
        self.evaluations[model_id][version_id][evaluation_id] = evaluation_metadata
        
        # Update version metrics
        version = self.versions[model_id][version_id]
        version['metrics'].update(metrics)
        self._save_version_metadata(model_id, version_id, version)
        
        self.logger.info(f"Registered evaluation {evaluation_id} for version {version_id} of model {model_id}")
        return evaluation_id
    
    def list_evaluations(self, model_id: str, version_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List evaluations for a model or model version.
        
        Args:
            model_id: ID of the model
            version_id: Optional ID of the version
            
        Returns:
            List of evaluation metadata
        """
        if model_id not in self.evaluations:
            return []
        
        if version_id:
            if version_id not in self.evaluations[model_id]:
                return []
            
            return list(self.evaluations[model_id][version_id].values())
        
        # Collect evaluations for all versions
        result = []
        for version_evals in self.evaluations[model_id].values():
            result.extend(version_evals.values())
        
        return result
    
    def create_ab_test(self, name: str, model_a_id: str, model_a_version_id: str,
                      model_b_id: str, model_b_version_id: str,
                      traffic_split: float, description: str,
                      success_criteria: Dict[str, Any]) -> str:
        """
        Create an A/B test experiment comparing two model versions.
        
        Args:
            name: Name of the experiment
            model_a_id: ID of model A
            model_a_version_id: Version ID of model A
            model_b_id: ID of model B
            model_b_version_id: Version ID of model B
            traffic_split: Percentage of traffic to model B (0.0 to 1.0)
            description: Description of the experiment
            success_criteria: Criteria for determining success
            
        Returns:
            Experiment ID
        """
        # Validate models and versions
        if model_a_id not in self.versions or model_a_version_id not in self.versions[model_a_id]:
            raise ValueError(f"Model version {model_a_version_id} of model {model_a_id} not found")
        
        if model_b_id not in self.versions or model_b_version_id not in self.versions[model_b_id]:
            raise ValueError(f"Model version {model_b_version_id} of model {model_b_id} not found")
        
        # Generate an experiment ID
        experiment_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        # Create experiment metadata
        experiment_metadata = {
            'id': experiment_id,
            'name': name,
            'type': 'a_b_test',
            'model_a_id': model_a_id,
            'model_a_version_id': model_a_version_id,
            'model_b_id': model_b_id,
            'model_b_version_id': model_b_version_id,
            'traffic_split': traffic_split,
            'description': description,
            'success_criteria': success_criteria,
            'status': 'running',
            'created_at': created_at,
            'updated_at': created_at,
            'results': None
        }
        
        # Save experiment metadata
        experiment_dir = os.path.join(self.storage_dir, 'experiments')
        os.makedirs(experiment_dir, exist_ok=True)
        
        experiment_path = os.path.join(experiment_dir, f"{experiment_id}.json")
        with open(experiment_path, 'w') as f:
            json.dump(experiment_metadata, f, indent=2)
        
        # Add to in-memory registry
        self.experiments[experiment_id] = experiment_metadata
        
        self.logger.info(f"Created A/B test experiment {name} (ID: {experiment_id})")
        return experiment_id
    
    def update_experiment_status(self, experiment_id: str, status: str,
                                results: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update the status and optionally add results to an experiment.
        
        Args:
            experiment_id: ID of the experiment
            status: New status
            results: Optional experiment results
            
        Returns:
            Success flag
        """
        if experiment_id not in self.experiments:
            return False
        
        # Update experiment metadata
        experiment = self.experiments[experiment_id]
        experiment['status'] = status
        experiment['updated_at'] = datetime.now().isoformat()
        
        if results:
            experiment['results'] = results
        
        # Save experiment metadata
        experiment_dir = os.path.join(self.storage_dir, 'experiments')
        experiment_path = os.path.join(experiment_dir, f"{experiment_id}.json")
        with open(experiment_path, 'w') as f:
            json.dump(experiment, f, indent=2)
        
        self.logger.info(f"Updated status of experiment {experiment_id} to {status}")
        return True
    
    def list_experiments(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List experiments, optionally filtered by status.
        
        Args:
            status: Optional filter by status
            
        Returns:
            List of experiment metadata
        """
        result = []
        
        for experiment_id, experiment in self.experiments.items():
            if status and experiment['status'] != status:
                continue
            
            result.append(experiment)
        
        return result
    
    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an experiment.
        
        Args:
            experiment_id: ID of the experiment
            
        Returns:
            Experiment metadata or None if not found
        """
        return self.experiments.get(experiment_id)
    
    def serve_model(self, model_type: ModelType) -> Tuple[str, str]:
        """
        Get the model and version to use for serving requests.
        
        This method handles A/B testing and serving the appropriate model version.
        
        Args:
            model_type: Type of model needed
            
        Returns:
            Tuple of (model_id, version_id) to use
        """
        # Find active A/B tests for this model type
        active_experiments = [
            exp for exp in self.experiments.values()
            if exp['status'] == 'running' and 
            self.models.get(exp['model_a_id'], {}).get('type') == model_type.value
        ]
        
        if active_experiments:
            # For simplicity, just use the first active experiment
            experiment = active_experiments[0]
            
            # Determine which model to serve based on traffic split
            # In a real implementation, this would use a consistent hashing algorithm
            import random
            if random.random() < experiment['traffic_split']:
                return experiment['model_b_id'], experiment['model_b_version_id']
            else:
                return experiment['model_a_id'], experiment['model_a_version_id']
        
        # No active experiments, find the production model of this type
        production_models = [
            (model_id, model) for model_id, model in self.models.items()
            if model['type'] == model_type.value and model['status'] == ModelStatus.PRODUCTION.value
        ]
        
        if production_models:
            # Use the first production model
            model_id, model = production_models[0]
            version_id = model.get('production_version')
            
            if version_id:
                return model_id, version_id
        
        # Fallback: find any model of this type with a latest version
        for model_id, model in self.models.items():
            if model['type'] == model_type.value and model.get('latest_version'):
                return model_id, model['latest_version']
        
        raise ValueError(f"No suitable model of type {model_type.value} found for serving")