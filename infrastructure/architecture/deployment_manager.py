"""
Zero-Downtime Deployment Manager for TerraFlow Platform

This module implements a deployment manager that enables zero-downtime
updates to the TerraFlow platform through blue-green deployment patterns,
feature flagging, and automatic rollback mechanisms.
"""

import os
import json
import time
import uuid
import logging
import threading
import subprocess
from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentState(Enum):
    """Possible states for a deployment"""
    INITIALIZED = "initialized"
    PREPARING = "preparing"
    DEPLOYING = "deploying"
    TESTING = "testing"
    ACTIVE = "active"
    ROLLING_BACK = "rolling_back"
    FAILED = "failed"
    COMPLETED = "completed"

class DeploymentStrategy(Enum):
    """Deployment strategies supported by the manager"""
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    RECREATE = "recreate"

class FeatureFlag:
    """
    Feature flag for controlling access to new features
    """
    def __init__(self, 
                flag_id: str, 
                name: str, 
                description: str, 
                enabled: bool = False,
                percentage: float = 0.0,
                conditions: Optional[Dict[str, Any]] = None):
        """
        Initialize a new feature flag
        
        Args:
            flag_id: Unique identifier for the flag
            name: Human-readable name for the flag
            description: Description of the feature
            enabled: Whether the flag is enabled
            percentage: Percentage of users who should see the feature (0.0 to 1.0)
            conditions: Additional conditions for enabling the feature
        """
        self.flag_id = flag_id
        self.name = name
        self.description = description
        self.enabled = enabled
        self.percentage = percentage
        self.conditions = conditions or {}
        self.created_at = time.time()
        self.updated_at = time.time()
    
    def update(self, 
              enabled: Optional[bool] = None,
              percentage: Optional[float] = None,
              conditions: Optional[Dict[str, Any]] = None):
        """
        Update the feature flag
        
        Args:
            enabled: New enabled state
            percentage: New percentage
            conditions: New conditions
        """
        if enabled is not None:
            self.enabled = enabled
        
        if percentage is not None:
            self.percentage = max(0.0, min(1.0, percentage))
        
        if conditions is not None:
            self.conditions = conditions
        
        self.updated_at = time.time()
    
    def is_enabled_for_user(self, user_id: str, user_attributes: Dict[str, Any]) -> bool:
        """
        Check if the feature is enabled for a specific user
        
        Args:
            user_id: User identifier
            user_attributes: User attributes for condition checking
            
        Returns:
            bool: True if the feature is enabled for this user
        """
        # If the flag is disabled globally, it's disabled for everyone
        if not self.enabled:
            return False
        
        # Check conditions
        for condition_key, condition_value in self.conditions.items():
            if condition_key in user_attributes:
                user_value = user_attributes[condition_key]
                
                # Simple equality check - in a real implementation, we would have more sophisticated conditions
                if user_value != condition_value:
                    return False
        
        # Check percentage rollout
        if self.percentage < 1.0:
            # Use a hash of the user ID to ensure consistent behavior
            # This ensures the same user always gets the same result
            import hashlib
            user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            user_percentage = (user_hash % 100) / 100.0
            
            return user_percentage < self.percentage
        
        # If we made it here, the feature is enabled for this user
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "flag_id": self.flag_id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "percentage": self.percentage,
            "conditions": self.conditions,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeatureFlag':
        """Create from dictionary"""
        flag = cls(
            flag_id=data["flag_id"],
            name=data["name"],
            description=data["description"],
            enabled=data["enabled"],
            percentage=data["percentage"],
            conditions=data["conditions"]
        )
        
        flag.created_at = data.get("created_at", time.time())
        flag.updated_at = data.get("updated_at", time.time())
        
        return flag

class Deployment:
    """
    Represents a deployment of the TerraFlow platform
    """
    def __init__(self,
                deployment_id: str,
                version: str,
                strategy: DeploymentStrategy,
                components: List[str],
                config: Dict[str, Any]):
        """
        Initialize a new deployment
        
        Args:
            deployment_id: Unique identifier for the deployment
            version: Version being deployed
            strategy: Deployment strategy to use
            components: List of components to deploy
            config: Deployment configuration
        """
        self.deployment_id = deployment_id
        self.version = version
        self.strategy = strategy
        self.components = components
        self.config = config
        self.state = DeploymentState.INITIALIZED
        self.start_time = None
        self.end_time = None
        self.current_phase = None
        self.phases_completed = []
        self.active_environment = None  # For blue-green: "blue" or "green"
        self.logs = []
        self.metrics = {}
        self.health_checks = {}
        self.feature_flags = {}
    
    def start(self):
        """Start the deployment"""
        self.state = DeploymentState.PREPARING
        self.start_time = time.time()
        self.log("Deployment started")
    
    def complete(self):
        """Mark the deployment as complete"""
        self.state = DeploymentState.COMPLETED
        self.end_time = time.time()
        self.log("Deployment completed successfully")
    
    def fail(self, reason: str):
        """Mark the deployment as failed"""
        self.state = DeploymentState.FAILED
        self.end_time = time.time()
        self.log(f"Deployment failed: {reason}")
    
    def start_phase(self, phase: str):
        """Start a new deployment phase"""
        self.current_phase = phase
        self.log(f"Starting phase: {phase}")
    
    def complete_phase(self, phase: str):
        """Complete a deployment phase"""
        if phase == self.current_phase:
            self.phases_completed.append(phase)
            self.current_phase = None
            self.log(f"Completed phase: {phase}")
    
    def log(self, message: str):
        """Add a log entry"""
        timestamp = time.time()
        entry = {
            "timestamp": timestamp,
            "message": message
        }
        
        self.logs.append(entry)
        logger.info(f"[Deployment {self.deployment_id}] {message}")
    
    def update_health_check(self, component: str, status: bool, details: Dict[str, Any] = None):
        """Update health check status for a component"""
        self.health_checks[component] = {
            "status": status,
            "details": details or {},
            "timestamp": time.time()
        }
    
    def add_feature_flag(self, flag: FeatureFlag):
        """Add a feature flag to the deployment"""
        self.feature_flags[flag.flag_id] = flag
    
    def update_metrics(self, metrics: Dict[str, Any]):
        """Update deployment metrics"""
        self.metrics.update(metrics)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "deployment_id": self.deployment_id,
            "version": self.version,
            "strategy": self.strategy.value,
            "components": self.components,
            "config": self.config,
            "state": self.state.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "current_phase": self.current_phase,
            "phases_completed": self.phases_completed,
            "active_environment": self.active_environment,
            "logs": self.logs,
            "metrics": self.metrics,
            "health_checks": self.health_checks,
            "feature_flags": {flag_id: flag.to_dict() for flag_id, flag in self.feature_flags.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Deployment':
        """Create from dictionary"""
        deployment = cls(
            deployment_id=data["deployment_id"],
            version=data["version"],
            strategy=DeploymentStrategy(data["strategy"]),
            components=data["components"],
            config=data["config"]
        )
        
        deployment.state = DeploymentState(data["state"])
        deployment.start_time = data.get("start_time")
        deployment.end_time = data.get("end_time")
        deployment.current_phase = data.get("current_phase")
        deployment.phases_completed = data.get("phases_completed", [])
        deployment.active_environment = data.get("active_environment")
        deployment.logs = data.get("logs", [])
        deployment.metrics = data.get("metrics", {})
        deployment.health_checks = data.get("health_checks", {})
        
        # Restore feature flags
        feature_flags_data = data.get("feature_flags", {})
        for flag_id, flag_data in feature_flags_data.items():
            deployment.feature_flags[flag_id] = FeatureFlag.from_dict(flag_data)
        
        return deployment

class HealthCheckResult:
    """Result of a health check"""
    def __init__(self, status: bool, message: str, metrics: Dict[str, Any] = None):
        """
        Initialize a health check result
        
        Args:
            status: True if healthy, False otherwise
            message: Health check message
            metrics: Optional metrics from the health check
        """
        self.status = status
        self.message = message
        self.metrics = metrics or {}
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "status": self.status,
            "message": self.message,
            "metrics": self.metrics,
            "timestamp": self.timestamp
        }

class DeploymentManager:
    """
    Manages deployments for the TerraFlow platform
    
    This class handles zero-downtime updates through blue-green deployment
    patterns, feature flagging, and automatic rollback mechanisms.
    """
    
    def __init__(self, data_dir: str = "data/deployments"):
        """
        Initialize the deployment manager
        
        Args:
            data_dir: Directory for storing deployment data
        """
        self.data_dir = data_dir
        self.deployments = {}  # deployment_id -> Deployment
        self.active_deployment = None
        self.feature_flags = {}  # flag_id -> FeatureFlag
        self.environments = {
            "blue": {"status": "inactive", "version": None},
            "green": {"status": "inactive", "version": None}
        }
        self.health_check_registry = {}  # component -> health_check_function
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing deployments and feature flags
        self._load_data()
    
    def _load_data(self):
        """Load deployment and feature flag data from disk"""
        # Load deployments
        deployments_file = os.path.join(self.data_dir, "deployments.json")
        if os.path.exists(deployments_file):
            try:
                with open(deployments_file, "r") as f:
                    deployments_data = json.load(f)
                
                for deployment_id, deployment_data in deployments_data.items():
                    self.deployments[deployment_id] = Deployment.from_dict(deployment_data)
                
                # Find active deployment
                active_deployments = [d for d in self.deployments.values() if d.state == DeploymentState.ACTIVE]
                if active_deployments:
                    self.active_deployment = active_deployments[0].deployment_id
                    
                    # Set environment status
                    active_env = active_deployments[0].active_environment
                    if active_env in self.environments:
                        self.environments[active_env]["status"] = "active"
                        self.environments[active_env]["version"] = active_deployments[0].version
                
                logger.info(f"Loaded {len(self.deployments)} deployments from disk")
                
            except Exception as e:
                logger.error(f"Error loading deployments: {str(e)}")
        
        # Load feature flags
        feature_flags_file = os.path.join(self.data_dir, "feature_flags.json")
        if os.path.exists(feature_flags_file):
            try:
                with open(feature_flags_file, "r") as f:
                    feature_flags_data = json.load(f)
                
                for flag_id, flag_data in feature_flags_data.items():
                    self.feature_flags[flag_id] = FeatureFlag.from_dict(flag_data)
                
                logger.info(f"Loaded {len(self.feature_flags)} feature flags from disk")
                
            except Exception as e:
                logger.error(f"Error loading feature flags: {str(e)}")
    
    def _save_data(self):
        """Save deployment and feature flag data to disk"""
        # Save deployments
        deployments_file = os.path.join(self.data_dir, "deployments.json")
        try:
            deployments_data = {deployment_id: deployment.to_dict() for deployment_id, deployment in self.deployments.items()}
            
            with open(deployments_file, "w") as f:
                json.dump(deployments_data, f, indent=2)
            
            logger.debug("Saved deployments to disk")
            
        except Exception as e:
            logger.error(f"Error saving deployments: {str(e)}")
        
        # Save feature flags
        feature_flags_file = os.path.join(self.data_dir, "feature_flags.json")
        try:
            feature_flags_data = {flag_id: flag.to_dict() for flag_id, flag in self.feature_flags.items()}
            
            with open(feature_flags_file, "w") as f:
                json.dump(feature_flags_data, f, indent=2)
            
            logger.debug("Saved feature flags to disk")
            
        except Exception as e:
            logger.error(f"Error saving feature flags: {str(e)}")
    
    def create_deployment(self,
                         version: str,
                         strategy: DeploymentStrategy = DeploymentStrategy.BLUE_GREEN,
                         components: Optional[List[str]] = None,
                         config: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new deployment
        
        Args:
            version: Version being deployed
            strategy: Deployment strategy to use
            components: List of components to deploy (None for all)
            config: Deployment configuration
            
        Returns:
            str: The deployment ID
        """
        deployment_id = str(uuid.uuid4())
        
        # Default to all components if not specified
        if components is None:
            components = ["api", "worker", "web", "agent"]
        
        # Default config
        if config is None:
            config = {
                "timeout": 300,  # seconds
                "health_check_timeout": 60,  # seconds
                "rollback_on_failure": True,
                "health_check_retries": 3,
                "health_check_interval": 5  # seconds
            }
        
        # Create deployment
        deployment = Deployment(
            deployment_id=deployment_id,
            version=version,
            strategy=strategy,
            components=components,
            config=config
        )
        
        # Store deployment
        self.deployments[deployment_id] = deployment
        
        # Save data
        self._save_data()
        
        logger.info(f"Created deployment {deployment_id} for version {version}")
        
        return deployment_id
    
    def start_deployment(self, deployment_id: str) -> bool:
        """
        Start a deployment
        
        Args:
            deployment_id: The deployment ID
            
        Returns:
            bool: True if the deployment was started, False otherwise
        """
        if deployment_id not in self.deployments:
            logger.error(f"Deployment {deployment_id} not found")
            return False
        
        deployment = self.deployments[deployment_id]
        
        # Check if already started
        if deployment.state != DeploymentState.INITIALIZED:
            logger.warning(f"Deployment {deployment_id} already started (state: {deployment.state.value})")
            return False
        
        # Start deployment
        deployment.start()
        
        # Save data
        self._save_data()
        
        # Start deployment in a background thread
        threading.Thread(target=self._execute_deployment, args=(deployment_id,)).start()
        
        return True
    
    def _execute_deployment(self, deployment_id: str):
        """
        Execute a deployment
        
        Args:
            deployment_id: The deployment ID
        """
        if deployment_id not in self.deployments:
            logger.error(f"Deployment {deployment_id} not found")
            return
        
        deployment = self.deployments[deployment_id]
        
        try:
            # Execute deployment based on strategy
            strategy = deployment.strategy
            
            if strategy == DeploymentStrategy.BLUE_GREEN:
                self._execute_blue_green_deployment(deployment_id)
            elif strategy == DeploymentStrategy.CANARY:
                self._execute_canary_deployment(deployment_id)
            elif strategy == DeploymentStrategy.ROLLING:
                self._execute_rolling_deployment(deployment_id)
            elif strategy == DeploymentStrategy.RECREATE:
                self._execute_recreate_deployment(deployment_id)
            else:
                deployment.fail(f"Unsupported deployment strategy: {strategy.value}")
            
        except Exception as e:
            logger.exception(f"Error executing deployment {deployment_id}: {str(e)}")
            deployment.fail(f"Error: {str(e)}")
            
            # Save data
            self._save_data()
    
    def _execute_blue_green_deployment(self, deployment_id: str):
        """
        Execute a blue-green deployment
        
        Args:
            deployment_id: The deployment ID
        """
        deployment = self.deployments[deployment_id]
        
        try:
            # Phase 1: Prepare the inactive environment
            deployment.start_phase("prepare")
            
            # Determine which environment to use
            current_active = self._get_active_environment()
            new_env = "green" if current_active == "blue" else "blue"
            
            deployment.log(f"Current active environment: {current_active}")
            deployment.log(f"New environment: {new_env}")
            
            # Set up the new environment
            self._setup_environment(deployment, new_env)
            
            deployment.complete_phase("prepare")
            
            # Phase 2: Deploy to the inactive environment
            deployment.start_phase("deploy")
            
            # Deploy to the new environment
            self._deploy_to_environment(deployment, new_env)
            
            deployment.complete_phase("deploy")
            
            # Phase 3: Test the new environment
            deployment.start_phase("test")
            
            # Run health checks on the new environment
            health_check_passed = self._run_health_checks(deployment, new_env)
            
            if not health_check_passed:
                deployment.log("Health checks failed, rolling back")
                deployment.state = DeploymentState.ROLLING_BACK
                
                # Rollback
                self._cleanup_environment(deployment, new_env)
                
                deployment.fail("Health checks failed")
                return
            
            deployment.complete_phase("test")
            
            # Phase 4: Switch traffic to the new environment
            deployment.start_phase("switch")
            
            # Switch traffic
            self._switch_traffic(deployment, new_env)
            
            # Mark the new environment as active
            self.environments[new_env]["status"] = "active"
            self.environments[new_env]["version"] = deployment.version
            
            # Mark the old environment as inactive
            if current_active:
                self.environments[current_active]["status"] = "inactive"
            
            # Update deployment state
            deployment.active_environment = new_env
            deployment.state = DeploymentState.ACTIVE
            
            # Update active deployment
            self.active_deployment = deployment_id
            
            deployment.complete_phase("switch")
            
            # Complete deployment
            deployment.complete()
            
        except Exception as e:
            logger.exception(f"Error in blue-green deployment {deployment_id}: {str(e)}")
            deployment.fail(f"Error: {str(e)}")
            
            # Attempt rollback if configured
            if deployment.config.get("rollback_on_failure", True):
                deployment.log("Rolling back due to error")
                deployment.state = DeploymentState.ROLLING_BACK
                
                # Determine which environment to rollback
                new_env = "green" if current_active == "blue" else "blue"
                
                # Rollback
                self._cleanup_environment(deployment, new_env)
        
        finally:
            # Save data
            self._save_data()
    
    def _execute_canary_deployment(self, deployment_id: str):
        """
        Execute a canary deployment
        
        Args:
            deployment_id: The deployment ID
        """
        deployment = self.deployments[deployment_id]
        
        try:
            # Phase 1: Prepare for canary deployment
            deployment.start_phase("prepare")
            
            # Determine which environment to use as the canary
            current_active = self._get_active_environment()
            
            if not current_active:
                # No active environment, default to blue-green
                logger.info("No active environment, falling back to blue-green deployment")
                self._execute_blue_green_deployment(deployment_id)
                return
            
            deployment.log(f"Current active environment: {current_active}")
            deployment.log("Preparing for canary deployment")
            
            # Create canary instances
            canary_instances = self._create_canary_instances(deployment)
            
            deployment.complete_phase("prepare")
            
            # Phase 2: Deploy to canary instances
            deployment.start_phase("deploy_canary")
            
            # Deploy to canary instances
            for instance in canary_instances:
                self._deploy_to_instance(deployment, instance)
            
            deployment.complete_phase("deploy_canary")
            
            # Phase 3: Test canary instances
            deployment.start_phase("test_canary")
            
            # Run health checks on canary instances
            all_healthy = True
            for instance in canary_instances:
                if not self._run_instance_health_check(deployment, instance):
                    all_healthy = False
                    break
            
            if not all_healthy:
                deployment.log("Canary health checks failed, rolling back")
                deployment.state = DeploymentState.ROLLING_BACK
                
                # Rollback canary instances
                for instance in canary_instances:
                    self._rollback_instance(deployment, instance)
                
                deployment.fail("Canary health checks failed")
                return
            
            deployment.complete_phase("test_canary")
            
            # Phase 4: Gradually increase traffic to canary
            deployment.start_phase("increase_traffic")
            
            # Start with a small percentage and gradually increase
            traffic_percentages = [10, 25, 50, 75, 100]
            
            for percentage in traffic_percentages:
                deployment.log(f"Increasing traffic to canary: {percentage}%")
                
                # Update traffic routing
                self._update_traffic_routing(deployment, canary_instances, percentage)
                
                # Wait for a period to collect metrics
                time.sleep(deployment.config.get("canary_interval", 60))
                
                # Check metrics to ensure everything is healthy
                if not self._check_canary_metrics(deployment, canary_instances):
                    deployment.log(f"Canary metrics check failed at {percentage}%, rolling back")
                    deployment.state = DeploymentState.ROLLING_BACK
                    
                    # Rollback canary instances
                    for instance in canary_instances:
                        self._rollback_instance(deployment, instance)
                    
                    # Reset traffic routing
                    self._update_traffic_routing(deployment, canary_instances, 0)
                    
                    deployment.fail(f"Canary metrics check failed at {percentage}%")
                    return
            
            deployment.complete_phase("increase_traffic")
            
            # Phase 5: Complete deployment to all instances
            deployment.start_phase("deploy_all")
            
            # Deploy to all remaining instances
            remaining_instances = self._get_remaining_instances(deployment, canary_instances)
            
            for instance in remaining_instances:
                self._deploy_to_instance(deployment, instance)
            
            deployment.complete_phase("deploy_all")
            
            # Update deployment state
            deployment.state = DeploymentState.ACTIVE
            
            # Update active deployment
            self.active_deployment = deployment_id
            
            # Complete deployment
            deployment.complete()
            
        except Exception as e:
            logger.exception(f"Error in canary deployment {deployment_id}: {str(e)}")
            deployment.fail(f"Error: {str(e)}")
            
            # Attempt rollback if configured
            if deployment.config.get("rollback_on_failure", True):
                deployment.log("Rolling back due to error")
                deployment.state = DeploymentState.ROLLING_BACK
                
                # Rollback all instances
                for instance in canary_instances:
                    self._rollback_instance(deployment, instance)
                
                # Reset traffic routing
                self._update_traffic_routing(deployment, canary_instances, 0)
        
        finally:
            # Save data
            self._save_data()
    
    def _execute_rolling_deployment(self, deployment_id: str):
        """
        Execute a rolling deployment
        
        Args:
            deployment_id: The deployment ID
        """
        deployment = self.deployments[deployment_id]
        deployment.log("Rolling deployment not implemented, falling back to blue-green")
        
        # Fall back to blue-green deployment
        self._execute_blue_green_deployment(deployment_id)
    
    def _execute_recreate_deployment(self, deployment_id: str):
        """
        Execute a recreate deployment
        
        Args:
            deployment_id: The deployment ID
        """
        deployment = self.deployments[deployment_id]
        deployment.log("Recreate deployment not implemented, falling back to blue-green")
        
        # Fall back to blue-green deployment
        self._execute_blue_green_deployment(deployment_id)
    
    def _get_active_environment(self) -> Optional[str]:
        """Get the currently active environment (blue or green)"""
        for env, status in self.environments.items():
            if status["status"] == "active":
                return env
        return None
    
    def _setup_environment(self, deployment: Deployment, environment: str):
        """
        Set up a deployment environment
        
        Args:
            deployment: The deployment
            environment: The environment to set up (blue or green)
        """
        deployment.log(f"Setting up environment: {environment}")
        
        # In a real implementation, this would provision or prepare infrastructure
        # For demonstration purposes, we'll simply log the steps
        
        deployment.log(f"Provisioning resources for {environment} environment")
        time.sleep(1)  # Simulate work
        
        deployment.log(f"Configuring network for {environment} environment")
        time.sleep(1)  # Simulate work
        
        deployment.log(f"Environment {environment} ready")
    
    def _deploy_to_environment(self, deployment: Deployment, environment: str):
        """
        Deploy to an environment
        
        Args:
            deployment: The deployment
            environment: The environment to deploy to (blue or green)
        """
        deployment.log(f"Deploying version {deployment.version} to {environment} environment")
        
        # In a real implementation, this would deploy the application
        # For demonstration purposes, we'll simply log the steps
        
        for component in deployment.components:
            deployment.log(f"Deploying component {component} to {environment}")
            time.sleep(1)  # Simulate work
        
        deployment.log(f"Deployment to {environment} environment complete")
    
    def _run_health_checks(self, deployment: Deployment, environment: str) -> bool:
        """
        Run health checks on an environment
        
        Args:
            deployment: The deployment
            environment: The environment to check (blue or green)
            
        Returns:
            bool: True if all health checks pass, False otherwise
        """
        deployment.log(f"Running health checks on {environment} environment")
        
        # In a real implementation, this would run actual health checks
        # For demonstration purposes, we'll simulate health checks
        
        all_passed = True
        
        for component in deployment.components:
            deployment.log(f"Checking health of component {component}")
            
            # Simulate health check
            health_check_fn = self.health_check_registry.get(component)
            
            if health_check_fn:
                try:
                    result = health_check_fn(environment, deployment.version)
                    
                    if not result.status:
                        deployment.log(f"Health check failed for {component}: {result.message}")
                        all_passed = False
                        deployment.update_health_check(component, False, result.metrics)
                    else:
                        deployment.log(f"Health check passed for {component}")
                        deployment.update_health_check(component, True, result.metrics)
                
                except Exception as e:
                    deployment.log(f"Error in health check for {component}: {str(e)}")
                    all_passed = False
                    deployment.update_health_check(component, False, {"error": str(e)})
            else:
                # No health check function, assume healthy
                deployment.log(f"No health check function for {component}, assuming healthy")
                deployment.update_health_check(component, True)
        
        if all_passed:
            deployment.log("All health checks passed")
        else:
            deployment.log("One or more health checks failed")
        
        return all_passed
    
    def _switch_traffic(self, deployment: Deployment, new_environment: str):
        """
        Switch traffic to a new environment
        
        Args:
            deployment: The deployment
            new_environment: The environment to switch to (blue or green)
        """
        deployment.log(f"Switching traffic to {new_environment} environment")
        
        # In a real implementation, this would update load balancers or proxies
        # For demonstration purposes, we'll simply log the steps
        
        deployment.log("Updating load balancer configuration")
        time.sleep(1)  # Simulate work
        
        deployment.log(f"Traffic switched to {new_environment} environment")
    
    def _cleanup_environment(self, deployment: Deployment, environment: str):
        """
        Clean up an environment
        
        Args:
            deployment: The deployment
            environment: The environment to clean up (blue or green)
        """
        deployment.log(f"Cleaning up {environment} environment")
        
        # In a real implementation, this would tear down resources
        # For demonstration purposes, we'll simply log the steps
        
        deployment.log(f"Stopping services in {environment} environment")
        time.sleep(1)  # Simulate work
        
        deployment.log(f"Releasing resources in {environment} environment")
        time.sleep(1)  # Simulate work
        
        deployment.log(f"Environment {environment} cleaned up")
    
    def _create_canary_instances(self, deployment: Deployment) -> List[Dict[str, Any]]:
        """
        Create canary instances for a deployment
        
        Args:
            deployment: The deployment
            
        Returns:
            List[Dict[str, Any]]: List of canary instances
        """
        deployment.log("Creating canary instances")
        
        # In a real implementation, this would create actual instances
        # For demonstration purposes, we'll create simulated instances
        
        canary_percentage = deployment.config.get("canary_percentage", 10)
        
        # Simulate creating instances for each component
        instances = []
        
        for component in deployment.components:
            # Determine how many instances to create as canaries
            total_instances = 5  # Simulated total instances per component
            canary_count = max(1, int(total_instances * canary_percentage / 100))
            
            deployment.log(f"Creating {canary_count} canary instances for {component}")
            
            for i in range(canary_count):
                instance = {
                    "id": f"{component}-canary-{i}",
                    "component": component,
                    "environment": "canary",
                    "version": deployment.version
                }
                
                instances.append(instance)
        
        return instances
    
    def _deploy_to_instance(self, deployment: Deployment, instance: Dict[str, Any]):
        """
        Deploy to a specific instance
        
        Args:
            deployment: The deployment
            instance: The instance to deploy to
        """
        deployment.log(f"Deploying to instance {instance['id']}")
        
        # In a real implementation, this would deploy to an actual instance
        # For demonstration purposes, we'll simply log the steps
        
        component = instance["component"]
        
        deployment.log(f"Updating {component} on instance {instance['id']}")
        time.sleep(1)  # Simulate work
        
        deployment.log(f"Deployment to instance {instance['id']} complete")
    
    def _run_instance_health_check(self, deployment: Deployment, instance: Dict[str, Any]) -> bool:
        """
        Run health check on a specific instance
        
        Args:
            deployment: The deployment
            instance: The instance to check
            
        Returns:
            bool: True if the health check passes, False otherwise
        """
        instance_id = instance["id"]
        component = instance["component"]
        
        deployment.log(f"Running health check on instance {instance_id}")
        
        # In a real implementation, this would run an actual health check
        # For demonstration purposes, we'll simulate a health check
        
        health_check_fn = self.health_check_registry.get(component)
        
        if health_check_fn:
            try:
                result = health_check_fn("canary", deployment.version, instance_id)
                
                if not result.status:
                    deployment.log(f"Health check failed for instance {instance_id}: {result.message}")
                    return False
                else:
                    deployment.log(f"Health check passed for instance {instance_id}")
                    return True
            
            except Exception as e:
                deployment.log(f"Error in health check for instance {instance_id}: {str(e)}")
                return False
        else:
            # No health check function, assume healthy
            deployment.log(f"No health check function for {component}, assuming instance {instance_id} is healthy")
            return True
    
    def _update_traffic_routing(self, deployment: Deployment, canary_instances: List[Dict[str, Any]], percentage: int):
        """
        Update traffic routing for canary instances
        
        Args:
            deployment: The deployment
            canary_instances: List of canary instances
            percentage: Percentage of traffic to route to canary instances
        """
        deployment.log(f"Updating traffic routing: {percentage}% to canary instances")
        
        # In a real implementation, this would update load balancers or proxies
        # For demonstration purposes, we'll simply log the steps
        
        deployment.log("Updating load balancer configuration for canary routing")
        time.sleep(1)  # Simulate work
        
        deployment.log(f"Traffic routing updated: {percentage}% to canary instances")
    
    def _check_canary_metrics(self, deployment: Deployment, canary_instances: List[Dict[str, Any]]) -> bool:
        """
        Check metrics for canary instances
        
        Args:
            deployment: The deployment
            canary_instances: List of canary instances
            
        Returns:
            bool: True if metrics are acceptable, False otherwise
        """
        deployment.log("Checking metrics for canary instances")
        
        # In a real implementation, this would check actual metrics
        # For demonstration purposes, we'll simulate metric checks
        
        # Simulate checking error rate, response time, etc.
        error_rate = 0.01  # 1% error rate
        avg_response_time = 150  # milliseconds
        
        # Update metrics in deployment
        deployment.update_metrics({
            "canary_error_rate": error_rate,
            "canary_avg_response_time": avg_response_time
        })
        
        # Check if metrics are acceptable
        max_error_rate = deployment.config.get("max_error_rate", 0.05)  # 5%
        max_response_time = deployment.config.get("max_response_time", 500)  # milliseconds
        
        if error_rate > max_error_rate:
            deployment.log(f"Canary error rate too high: {error_rate*100}% (max {max_error_rate*100}%)")
            return False
        
        if avg_response_time > max_response_time:
            deployment.log(f"Canary response time too high: {avg_response_time}ms (max {max_response_time}ms)")
            return False
        
        deployment.log("Canary metrics are acceptable")
        return True
    
    def _get_remaining_instances(self, deployment: Deployment, canary_instances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get remaining instances that need to be updated
        
        Args:
            deployment: The deployment
            canary_instances: List of canary instances
            
        Returns:
            List[Dict[str, Any]]: List of remaining instances
        """
        # In a real implementation, this would get actual instances
        # For demonstration purposes, we'll simulate instances
        
        canary_ids = {instance["id"] for instance in canary_instances}
        remaining_instances = []
        
        for component in deployment.components:
            # Determine how many total instances exist for this component
            total_instances = 5  # Simulated total instances per component
            
            for i in range(total_instances):
                instance_id = f"{component}-{i}"
                
                # Skip if this is a canary instance
                if instance_id in canary_ids:
                    continue
                
                instance = {
                    "id": instance_id,
                    "component": component,
                    "environment": "production",
                    "version": "previous"  # This would be the actual previous version
                }
                
                remaining_instances.append(instance)
        
        return remaining_instances
    
    def _rollback_instance(self, deployment: Deployment, instance: Dict[str, Any]):
        """
        Rollback a specific instance
        
        Args:
            deployment: The deployment
            instance: The instance to rollback
        """
        deployment.log(f"Rolling back instance {instance['id']}")
        
        # In a real implementation, this would rollback an actual instance
        # For demonstration purposes, we'll simply log the steps
        
        component = instance["component"]
        
        deployment.log(f"Stopping {component} on instance {instance['id']}")
        time.sleep(0.5)  # Simulate work
        
        deployment.log(f"Reverting {component} on instance {instance['id']} to previous version")
        time.sleep(0.5)  # Simulate work
        
        deployment.log(f"Rollback of instance {instance['id']} complete")
    
    def register_health_check(self, component: str, health_check_fn: Callable[[str, str, Optional[str]], HealthCheckResult]):
        """
        Register a health check function for a component
        
        Args:
            component: The component to register the health check for
            health_check_fn: The health check function
        """
        self.health_check_registry[component] = health_check_fn
        logger.info(f"Registered health check for component {component}")
    
    def get_deployment(self, deployment_id: str) -> Optional[Deployment]:
        """
        Get a deployment
        
        Args:
            deployment_id: The deployment ID
            
        Returns:
            Optional[Deployment]: The deployment, or None if not found
        """
        return self.deployments.get(deployment_id)
    
    def get_active_deployment(self) -> Optional[Deployment]:
        """
        Get the active deployment
        
        Returns:
            Optional[Deployment]: The active deployment, or None if none is active
        """
        if self.active_deployment:
            return self.deployments.get(self.active_deployment)
        return None
    
    def get_deployments(self, limit: int = 10, offset: int = 0) -> List[Deployment]:
        """
        Get deployments
        
        Args:
            limit: Maximum number of deployments to return
            offset: Offset for pagination
            
        Returns:
            List[Deployment]: List of deployments
        """
        return list(self.deployments.values())[offset:offset+limit]
    
    def create_feature_flag(self, name: str, description: str, enabled: bool = False,
                          percentage: float = 0.0, conditions: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new feature flag
        
        Args:
            name: Name of the feature flag
            description: Description of the feature
            enabled: Whether the flag is enabled
            percentage: Percentage of users who should see the feature (0.0 to 1.0)
            conditions: Additional conditions for enabling the feature
            
        Returns:
            str: The feature flag ID
        """
        flag_id = str(uuid.uuid4())
        
        # Create feature flag
        flag = FeatureFlag(
            flag_id=flag_id,
            name=name,
            description=description,
            enabled=enabled,
            percentage=percentage,
            conditions=conditions
        )
        
        # Store feature flag
        self.feature_flags[flag_id] = flag
        
        # Save data
        self._save_data()
        
        logger.info(f"Created feature flag {flag_id}: {name}")
        
        return flag_id
    
    def update_feature_flag(self, flag_id: str, enabled: Optional[bool] = None,
                          percentage: Optional[float] = None,
                          conditions: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update a feature flag
        
        Args:
            flag_id: The feature flag ID
            enabled: New enabled state
            percentage: New percentage
            conditions: New conditions
            
        Returns:
            bool: True if the flag was updated, False otherwise
        """
        if flag_id not in self.feature_flags:
            logger.error(f"Feature flag {flag_id} not found")
            return False
        
        flag = self.feature_flags[flag_id]
        
        # Update flag
        flag.update(enabled=enabled, percentage=percentage, conditions=conditions)
        
        # Save data
        self._save_data()
        
        logger.info(f"Updated feature flag {flag_id}")
        
        return True
    
    def delete_feature_flag(self, flag_id: str) -> bool:
        """
        Delete a feature flag
        
        Args:
            flag_id: The feature flag ID
            
        Returns:
            bool: True if the flag was deleted, False otherwise
        """
        if flag_id not in self.feature_flags:
            logger.error(f"Feature flag {flag_id} not found")
            return False
        
        # Delete flag
        del self.feature_flags[flag_id]
        
        # Save data
        self._save_data()
        
        logger.info(f"Deleted feature flag {flag_id}")
        
        return True
    
    def get_feature_flag(self, flag_id: str) -> Optional[FeatureFlag]:
        """
        Get a feature flag
        
        Args:
            flag_id: The feature flag ID
            
        Returns:
            Optional[FeatureFlag]: The feature flag, or None if not found
        """
        return self.feature_flags.get(flag_id)
    
    def get_feature_flags(self) -> List[FeatureFlag]:
        """
        Get all feature flags
        
        Returns:
            List[FeatureFlag]: List of feature flags
        """
        return list(self.feature_flags.values())
    
    def is_feature_enabled(self, flag_id: str, user_id: str,
                         user_attributes: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if a feature is enabled for a specific user
        
        Args:
            flag_id: The feature flag ID
            user_id: User identifier
            user_attributes: User attributes for condition checking
            
        Returns:
            bool: True if the feature is enabled for this user
        """
        if flag_id not in self.feature_flags:
            logger.warning(f"Feature flag {flag_id} not found")
            return False
        
        flag = self.feature_flags[flag_id]
        return flag.is_enabled_for_user(user_id, user_attributes or {})


# Example health check function
def api_health_check(environment: str, version: str, instance_id: Optional[str] = None) -> HealthCheckResult:
    """
    Example health check function for the API component
    
    Args:
        environment: The environment to check (blue, green, or canary)
        version: The version to check
        instance_id: Optional instance ID for specific instance checks
        
    Returns:
        HealthCheckResult: The health check result
    """
    try:
        # In a real implementation, this would make actual health check requests
        # For demonstration purposes, we'll simulate a health check
        
        # Simulate checking if API is responding
        is_healthy = True
        
        # Collect some metrics
        metrics = {
            "response_time": 120,  # milliseconds
            "error_rate": 0.01,  # 1%
            "request_count": 100
        }
        
        if is_healthy:
            return HealthCheckResult(
                status=True,
                message=f"API is healthy in {environment} environment (version: {version})",
                metrics=metrics
            )
        else:
            return HealthCheckResult(
                status=False,
                message=f"API is not healthy in {environment} environment (version: {version})",
                metrics=metrics
            )
    
    except Exception as e:
        return HealthCheckResult(
            status=False,
            message=f"Error checking API health: {str(e)}",
            metrics={"error": str(e)}
        )