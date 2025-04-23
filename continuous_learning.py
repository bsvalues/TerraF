"""
Continuous Learning Module for Code Deep Dive Analyzer

This module implements the continuous learning capabilities of the agent system,
including feedback processing, pattern recognition, model updating, and knowledge sharing.
"""

import os
import json
import time
import uuid
import logging
import re
import pickle
import threading
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta

# Import protocol server components for feedback and learning updates
from protocol_server import (
    FeedbackRecord, LearningUpdate, Task, MessageType, MessagePriority, AgentCategory,
    get_server
)

# Import model interface for pattern analysis
from agent_base import ModelInterface

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeedbackCollector:
    """
    Collects and processes feedback on agent actions from users and other agents.
    
    This component is responsible for:
    - Recording explicit and implicit feedback
    - Aggregating feedback by agent, action type, etc.
    - Identifying patterns in feedback
    - Triggering learning updates
    """
    
    def __init__(self):
        """Initialize the feedback collector"""
        self.server = get_server()
        self.feedback_records: Dict[str, FeedbackRecord] = {}
        self.feedback_by_agent: Dict[str, List[str]] = {}  # agent_id -> [feedback_ids]
        self.feedback_by_action: Dict[str, List[str]] = {}  # action_type -> [feedback_ids]
        self.recent_feedback: List[str] = []  # Recently received feedback IDs
        self.feedback_tracker = {}  # Track patterns in feedback
        
        # Create feedback aggregation thread
        self.running = True
        self.aggregation_thread = threading.Thread(target=self._feedback_aggregation_loop)
        self.aggregation_thread.daemon = True
        self.aggregation_thread.start()
    
    def record_feedback(self, feedback: FeedbackRecord) -> str:
        """
        Record a new feedback instance
        
        Args:
            feedback: The feedback record
            
        Returns:
            The feedback ID
        """
        # Set feedback ID if not already set
        if not feedback.feedback_id:
            feedback.feedback_id = str(uuid.uuid4())
        
        # Store feedback
        self.feedback_records[feedback.feedback_id] = feedback
        
        # Update indexes
        if feedback.agent_id not in self.feedback_by_agent:
            self.feedback_by_agent[feedback.agent_id] = []
        self.feedback_by_agent[feedback.agent_id].append(feedback.feedback_id)
        
        if feedback.action_type not in self.feedback_by_action:
            self.feedback_by_action[feedback.action_type] = []
        self.feedback_by_action[feedback.action_type].append(feedback.feedback_id)
        
        # Add to recent feedback
        self.recent_feedback.append(feedback.feedback_id)
        if len(self.recent_feedback) > 100:  # Keep only most recent 100
            self.recent_feedback = self.recent_feedback[-100:]
        
        # Log feedback
        logger.info(f"Recorded feedback {feedback.feedback_id} for agent {feedback.agent_id} on {feedback.action_type}")
        
        return feedback.feedback_id
    
    def get_feedback_by_agent(self, agent_id: str, limit: int = 50) -> List[FeedbackRecord]:
        """
        Get all feedback for a specific agent
        
        Args:
            agent_id: Agent ID to retrieve feedback for
            limit: Maximum number of records to return
            
        Returns:
            List of feedback records
        """
        if agent_id not in self.feedback_by_agent:
            return []
        
        feedback_ids = self.feedback_by_agent[agent_id]
        return [self.feedback_records[fid] for fid in feedback_ids[-limit:] if fid in self.feedback_records]
    
    def get_feedback_by_action(self, action_type: str, limit: int = 50) -> List[FeedbackRecord]:
        """
        Get all feedback for a specific action type
        
        Args:
            action_type: Action type to retrieve feedback for
            limit: Maximum number of records to return
            
        Returns:
            List of feedback records
        """
        if action_type not in self.feedback_by_action:
            return []
        
        feedback_ids = self.feedback_by_action[action_type]
        return [self.feedback_records[fid] for fid in feedback_ids[-limit:] if fid in self.feedback_records]
    
    def get_recent_feedback(self, limit: int = 20) -> List[FeedbackRecord]:
        """
        Get most recent feedback
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of feedback records
        """
        ids = self.recent_feedback[-limit:]
        return [self.feedback_records[fid] for fid in ids if fid in self.feedback_records]
    
    def _feedback_aggregation_loop(self):
        """Background thread for feedback aggregation and analysis"""
        while self.running:
            try:
                # Check if there's enough new feedback to analyze
                if len(self.recent_feedback) >= 5:
                    self._analyze_recent_feedback()
                
                # Sleep to prevent CPU spinning
                time.sleep(60)  # Check every minute
            
            except Exception as e:
                logger.error(f"Error in feedback aggregation loop: {e}")
                time.sleep(300)  # Sleep longer after error
    
    def _analyze_recent_feedback(self):
        """Analyze recent feedback for patterns"""
        # Get recent feedback records
        recent_records = self.get_recent_feedback(20)
        
        # Group by agent and action
        by_agent_action = {}
        
        for record in recent_records:
            key = f"{record.agent_id}:{record.action_type}"
            if key not in by_agent_action:
                by_agent_action[key] = []
            by_agent_action[key].append(record)
        
        # For each group with at least 3 records, check for patterns
        for key, records in by_agent_action.items():
            if len(records) < 3:
                continue
            
            # Check if average rating indicates a pattern
            avg_rating = sum(r.rating for r in records) / len(records)
            
            if avg_rating < 0.3:  # Consistently negative feedback
                self._handle_negative_pattern(key, records, avg_rating)
            elif avg_rating > 0.7:  # Consistently positive feedback
                self._handle_positive_pattern(key, records, avg_rating)
    
    def _handle_negative_pattern(self, key: str, records: List[FeedbackRecord], avg_rating: float):
        """Handle pattern of negative feedback"""
        agent_id, action_type = key.split(":")
        
        # Check if we've already identified this pattern recently
        now = time.time()
        if key in self.feedback_tracker:
            last_time, count = self.feedback_tracker[key]
            # If we've seen this pattern within the last hour, increment count
            if now - last_time < 3600:
                self.feedback_tracker[key] = (now, count + 1)
                # Only trigger learning update if pattern persists
                if count >= 2:
                    self._trigger_learning_update(agent_id, action_type, records, avg_rating)
                return
        
        # Record new pattern
        self.feedback_tracker[key] = (now, 1)
        
        # Trigger learning update if rating is very low
        if avg_rating < 0.2:
            self._trigger_learning_update(agent_id, action_type, records, avg_rating)
    
    def _handle_positive_pattern(self, key: str, records: List[FeedbackRecord], avg_rating: float):
        """Handle pattern of positive feedback"""
        agent_id, action_type = key.split(":")
        
        # Check if we've already identified this pattern recently
        now = time.time()
        if key in self.feedback_tracker:
            last_time, count = self.feedback_tracker[key]
            # If we've seen this pattern within the last day, increment count
            if now - last_time < 86400:
                self.feedback_tracker[key] = (now, count + 1)
                # Only trigger learning update if pattern persists and is very positive
                if count >= 3 and avg_rating > 0.8:
                    self._trigger_learning_update(agent_id, action_type, records, avg_rating)
                return
        
        # Record new pattern
        self.feedback_tracker[key] = (now, 1)
        
        # For positive patterns, we're more conservative about updates
        # Only trigger if rating is very high and consistent
        if avg_rating > 0.9:
            self._trigger_learning_update(agent_id, action_type, records, avg_rating)
    
    def _trigger_learning_update(self, agent_id: str, action_type: str, records: List[FeedbackRecord], avg_rating: float):
        """Trigger a learning update based on feedback pattern"""
        # Create a learning task for the learning coordinator
        # Extract common context from feedback for pattern detection
        contexts = [record.context for record in records if record.context]
        common_elements = self._extract_common_elements(contexts)
        
        task = Task(
            task_type="analyze_feedback_pattern",
            description=f"Analyze feedback pattern for {agent_id} on {action_type}",
            input_data={
                "agent_id": agent_id,
                "action_type": action_type,
                "feedback_records": [asdict(record) for record in records],
                "average_rating": avg_rating,
                "common_elements": common_elements
            },
            assigned_agent="learning_coordinator",
            priority=MessagePriority.LOW
        )
        
        self.server.task_orchestrator.submit_task(task)
        logger.info(f"Triggered learning task for pattern: {agent_id}:{action_type}, avg rating: {avg_rating:.2f}")
    
    def _extract_common_elements(self, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract common elements from a list of context dictionaries"""
        if not contexts:
            return {}
        
        # Start with first context
        common = contexts[0].copy()
        
        # Intersect with remaining contexts
        for context in contexts[1:]:
            for key in list(common.keys()):
                if key not in context or context[key] != common[key]:
                    del common[key]
        
        return common
    
    def stop(self):
        """Stop the feedback collector"""
        self.running = False
        if self.aggregation_thread.is_alive():
            self.aggregation_thread.join(timeout=1.0)


class PatternRepository:
    """
    Stores and retrieves learning patterns identified from feedback.
    
    This component maintains a database of patterns that have been identified
    and validated, allowing agents to access them for continuous improvement.
    """
    
    def __init__(self, storage_path: str = "./.patterns"):
        """
        Initialize the pattern repository
        
        Args:
            storage_path: Path to store pattern data
        """
        self.storage_path = storage_path
        self.patterns: Dict[str, LearningUpdate] = {}
        self.patterns_by_capability: Dict[str, List[str]] = {}  # capability -> [pattern_ids]
        self.patterns_by_agent_type: Dict[str, List[str]] = {}  # agent_type -> [pattern_ids]
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing patterns
        self._load_patterns()
    
    def _load_patterns(self):
        """Load patterns from disk"""
        pattern_file = os.path.join(self.storage_path, "patterns.json")
        if os.path.exists(pattern_file):
            try:
                with open(pattern_file, 'r') as f:
                    patterns_data = json.load(f)
                
                for pattern_id, pattern_data in patterns_data.items():
                    update = LearningUpdate(
                        update_id=pattern_id,
                        agent_types=pattern_data["agent_types"],
                        capability=pattern_data["capability"],
                        pattern=pattern_data["pattern"],
                        effectiveness=pattern_data["effectiveness"],
                        confidence=pattern_data["confidence"],
                        supporting_evidence=pattern_data["supporting_evidence"],
                        created_at=pattern_data["created_at"]
                    )
                    
                    self.patterns[pattern_id] = update
                    
                    # Update indexes
                    if update.capability not in self.patterns_by_capability:
                        self.patterns_by_capability[update.capability] = []
                    self.patterns_by_capability[update.capability].append(pattern_id)
                    
                    for agent_type in update.agent_types:
                        if agent_type not in self.patterns_by_agent_type:
                            self.patterns_by_agent_type[agent_type] = []
                        self.patterns_by_agent_type[agent_type].append(pattern_id)
                
                logger.info(f"Loaded {len(self.patterns)} patterns from storage")
            
            except Exception as e:
                logger.error(f"Error loading patterns: {e}")
    
    def _save_patterns(self):
        """Save patterns to disk"""
        pattern_file = os.path.join(self.storage_path, "patterns.json")
        try:
            patterns_data = {}
            for pattern_id, update in self.patterns.items():
                patterns_data[pattern_id] = asdict(update)
            
            with open(pattern_file, 'w') as f:
                json.dump(patterns_data, f, indent=2)
            
            logger.info(f"Saved {len(self.patterns)} patterns to storage")
        
        except Exception as e:
            logger.error(f"Error saving patterns: {e}")
    
    def add_pattern(self, update: LearningUpdate) -> str:
        """
        Add a new learning pattern
        
        Args:
            update: The learning update
            
        Returns:
            The pattern ID
        """
        # Set update ID if not already set
        if not update.update_id:
            update.update_id = str(uuid.uuid4())
        
        # Store pattern
        self.patterns[update.update_id] = update
        
        # Update indexes
        if update.capability not in self.patterns_by_capability:
            self.patterns_by_capability[update.capability] = []
        self.patterns_by_capability[update.capability].append(update.update_id)
        
        for agent_type in update.agent_types:
            if agent_type not in self.patterns_by_agent_type:
                self.patterns_by_agent_type[agent_type] = []
            self.patterns_by_agent_type[agent_type].append(update.update_id)
        
        # Save to disk
        self._save_patterns()
        
        return update.update_id
    
    def get_pattern(self, pattern_id: str) -> Optional[LearningUpdate]:
        """
        Get a specific pattern by ID
        
        Args:
            pattern_id: The pattern ID
            
        Returns:
            The learning update or None if not found
        """
        return self.patterns.get(pattern_id)
    
    def get_patterns_by_capability(self, capability: str) -> List[LearningUpdate]:
        """
        Get all patterns for a specific capability
        
        Args:
            capability: The capability
            
        Returns:
            List of learning updates
        """
        if capability not in self.patterns_by_capability:
            return []
        
        pattern_ids = self.patterns_by_capability[capability]
        return [self.patterns[pid] for pid in pattern_ids if pid in self.patterns]
    
    def get_patterns_by_agent_type(self, agent_type: str) -> List[LearningUpdate]:
        """
        Get all patterns for a specific agent type
        
        Args:
            agent_type: The agent type
            
        Returns:
            List of learning updates
        """
        if agent_type not in self.patterns_by_agent_type:
            return []
        
        pattern_ids = self.patterns_by_agent_type[agent_type]
        return [self.patterns[pid] for pid in pattern_ids if pid in self.patterns]
    
    def get_high_confidence_patterns(self, min_confidence: float = 0.7) -> List[LearningUpdate]:
        """
        Get all patterns with high confidence
        
        Args:
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of learning updates
        """
        return [update for update in self.patterns.values() if update.confidence >= min_confidence]
    
    def update_pattern_confidence(self, pattern_id: str, new_confidence: float, add_evidence: Optional[str] = None) -> bool:
        """
        Update the confidence score for a pattern
        
        Args:
            pattern_id: The pattern ID
            new_confidence: New confidence score
            add_evidence: Optional evidence to add
            
        Returns:
            True if successful, False otherwise
        """
        if pattern_id not in self.patterns:
            return False
        
        update = self.patterns[pattern_id]
        
        # Update confidence
        update.confidence = new_confidence
        
        # Add evidence if provided
        if add_evidence and add_evidence not in update.supporting_evidence:
            update.supporting_evidence.append(add_evidence)
        
        # Save to disk
        self._save_patterns()
        
        return True


class ModelUpdateManager:
    """
    Manages the process of updating AI models based on learning patterns.
    
    This component handles:
    - Collecting training data from patterns
    - Preparing datasets for fine-tuning
    - Scheduling model updates
    - Tracking model versions and performance
    """
    
    def __init__(self, training_data_path: str = "./.training_data"):
        """
        Initialize the model update manager
        
        Args:
            training_data_path: Path to store training data
        """
        self.training_data_path = training_data_path
        self.server = get_server()
        self.pattern_repository = PatternRepository()
        
        # Model update tracking
        self.model_versions: Dict[str, List[Dict[str, Any]]] = {}  # model_id -> [version_info]
        self.model_performances: Dict[str, Dict[str, float]] = {}  # model_id -> {metric: value}
        self.update_schedule: Dict[str, float] = {}  # model_id -> next_update_time
        
        # Create training data directory if it doesn't exist
        os.makedirs(training_data_path, exist_ok=True)
        
        # Create model update thread
        self.running = True
        self.update_thread = threading.Thread(target=self._model_update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def schedule_model_update(self, model_id: str, delay_hours: float = 24.0):
        """
        Schedule a model update
        
        Args:
            model_id: The model ID to update
            delay_hours: Hours to wait before updating
        """
        next_update = time.time() + (delay_hours * 3600)
        self.update_schedule[model_id] = next_update
        logger.info(f"Scheduled update for model {model_id} at {datetime.fromtimestamp(next_update)}")
    
    def collect_training_data(self, model_id: str) -> str:
        """
        Collect training data for a model update
        
        Args:
            model_id: The model ID
            
        Returns:
            Path to the training data file
        """
        # Get model configuration
        model_config = self.server.model_manager.get_model_config(model_id)
        if not model_config:
            raise ValueError(f"Unknown model: {model_id}")
        
        # Get high-confidence patterns
        patterns = self.pattern_repository.get_high_confidence_patterns(min_confidence=0.7)
        
        # Get capabilities for this model
        capabilities = model_config.capabilities
        
        # Filter patterns relevant to this model's capabilities
        relevant_patterns = [p for p in patterns if p.capability in capabilities]
        
        if not relevant_patterns:
            logger.warning(f"No relevant patterns found for model {model_id}")
            # Return empty training file path
            filename = f"{model_id}_empty.jsonl"
            file_path = os.path.join(self.training_data_path, filename)
            with open(file_path, 'w') as f:
                f.write("")
            return file_path
        
        # Create training examples from patterns
        training_examples = []
        
        for pattern in relevant_patterns:
            # For each pattern, create a training example
            example = self._create_training_example(pattern)
            if example:
                training_examples.append(example)
        
        if not training_examples:
            logger.warning(f"No training examples generated for model {model_id}")
            # Return empty training file path instead of None
            filename = f"{model_id}_empty_examples.jsonl"
            file_path = os.path.join(self.training_data_path, filename)
            with open(file_path, 'w') as f:
                f.write("")
            return file_path
        
        # Save training data to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{model_id}_{timestamp}.jsonl"
        file_path = os.path.join(self.training_data_path, filename)
        
        with open(file_path, 'w') as f:
            for example in training_examples:
                f.write(json.dumps(example) + '\n')
        
        logger.info(f"Collected {len(training_examples)} training examples for model {model_id}")
        return file_path
    
    def _create_training_example(self, pattern: LearningUpdate) -> Optional[Dict[str, Any]]:
        """Create a training example from a learning pattern"""
        # The format depends on the model and pattern type
        # This is a simplified example
        try:
            # Extract pattern details
            capability = pattern.capability
            pattern_data = pattern.pattern
            
            # Create a prompt based on capability
            if capability == "code_analysis":
                prompt = f"Analyze this code for quality issues: {pattern_data.get('code_sample', '')}"
                ideal_response = pattern_data.get('ideal_analysis', '')
            
            elif capability == "pattern_detection":
                prompt = f"Identify design patterns in this code: {pattern_data.get('code_sample', '')}"
                ideal_response = pattern_data.get('ideal_detection', '')
            
            else:
                # Default format
                prompt = f"Process this input for {capability}: {json.dumps(pattern_data)}"
                ideal_response = pattern_data.get('ideal_response', '')
            
            if not ideal_response:
                return None
            
            # Create example in the format expected by the model provider
            return {
                "prompt": prompt,
                "completion": ideal_response,
                "capability": capability,
                "effectiveness": pattern.effectiveness,
                "confidence": pattern.confidence
            }
        
        except Exception as e:
            logger.error(f"Error creating training example from pattern: {e}")
            return None
    
    def _model_update_loop(self):
        """Background thread for scheduled model updates"""
        while self.running:
            try:
                # Check if any models are due for update
                current_time = time.time()
                
                for model_id, update_time in list(self.update_schedule.items()):
                    if current_time >= update_time:
                        # Remove from schedule
                        del self.update_schedule[model_id]
                        
                        # Perform update
                        self._perform_model_update(model_id)
                
                # Sleep to prevent CPU spinning
                time.sleep(300)  # Check every 5 minutes
            
            except Exception as e:
                logger.error(f"Error in model update loop: {e}")
                time.sleep(900)  # Sleep longer after error
    
    def _perform_model_update(self, model_id: str):
        """Perform a model update"""
        logger.info(f"Starting update for model {model_id}")
        
        try:
            # Collect training data
            training_data_path = self.collect_training_data(model_id)
            
            if not training_data_path:
                logger.warning(f"No training data available for model {model_id}")
                return
            
            # In a real implementation, this would trigger an actual fine-tuning job
            # with the model provider. For this example, we'll simulate it.
            
            # Simulate successful update
            new_version = self._simulate_model_update(model_id, training_data_path)
            
            # Update model version tracking
            if model_id not in self.model_versions:
                self.model_versions[model_id] = []
            
            self.model_versions[model_id].append(new_version)
            
            # Simulate performance evaluation
            performance = self._simulate_performance_evaluation(model_id, new_version)
            self.model_performances[model_id] = performance
            
            logger.info(f"Completed update for model {model_id}: version {new_version['version']}")
            
            # Schedule next update (in a real system, this would be based on usage and feedback)
            self.schedule_model_update(model_id, delay_hours=48.0)
        
        except Exception as e:
            logger.error(f"Error updating model {model_id}: {e}")
            # Schedule retry
            self.schedule_model_update(model_id, delay_hours=6.0)
    
    def _simulate_model_update(self, model_id: str, training_data_path: str) -> Dict[str, Any]:
        """Simulate a model update (in a real system, this would call the provider API)"""
        # Count training examples
        example_count = 0
        with open(training_data_path, 'r') as f:
            for line in f:
                example_count += 1
        
        # Generate simulated version info
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        version_id = f"{model_id}_ft_{timestamp}"
        
        return {
            "version": version_id,
            "base_model": model_id,
            "training_examples": example_count,
            "training_data": training_data_path,
            "created_at": time.time()
        }
    
    def _simulate_performance_evaluation(self, model_id: str, version_info: Dict[str, Any]) -> Dict[str, float]:
        """Simulate performance evaluation of updated model"""
        # In a real system, this would run benchmark tests
        # For simulation, we'll just generate plausible metrics
        import random
        
        # Simulate 5% improvement over previous version
        previous_performance = self.model_performances.get(model_id, {
            "accuracy": 0.8,
            "latency": 0.5,
            "token_efficiency": 0.7
        })
        
        return {
            "accuracy": min(0.98, previous_performance["accuracy"] * 1.05),
            "latency": max(0.3, previous_performance["latency"] * 0.95),
            "token_efficiency": min(0.95, previous_performance["token_efficiency"] * 1.05)
        }
    
    def stop(self):
        """Stop the model update manager"""
        self.running = False
        if self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)


class AgentKnowledgeDistributor:
    """
    Distributes knowledge and learning updates across agents.
    
    This component is responsible for:
    - Broadcasting learning updates to relevant agents
    - Managing agent knowledge synchronization
    - Tracking which agents have applied which updates
    """
    
    def __init__(self):
        """Initialize the knowledge distributor"""
        self.server = get_server()
        self.pattern_repository = PatternRepository()
        
        # Update tracking
        self.agent_updates: Dict[str, Set[str]] = {}  # agent_id -> {update_ids}
        self.pending_updates: Dict[str, List[Tuple[str, LearningUpdate]]] = {}  # agent_id -> [(update_id, update)]
        
        # Create distribution thread
        self.running = True
        self.distribution_thread = threading.Thread(target=self._distribution_loop)
        self.distribution_thread.daemon = True
        self.distribution_thread.start()
    
    def distribute_update(self, update: LearningUpdate):
        """
        Distribute a learning update to relevant agents
        
        Args:
            update: The learning update
        """
        # Store the update in the pattern repository
        update_id = self.pattern_repository.add_pattern(update)
        
        # Get all agents that should receive this update
        target_agents = []
        
        # If update applies to specific agent types
        for agent_type in update.agent_types:
            # Check if this is an agent category
            try:
                category = AgentCategory(agent_type)
                agents = self.server.agent_registry.get_agents_by_type(category)
                target_agents.extend(agents)
            except ValueError:
                # Not a category, might be a specific agent
                if agent_type in self.server.agent_registry.agents:
                    target_agents.append(agent_type)
        
        # If update applies to a capability
        if update.capability:
            agents = self.server.agent_registry.get_agents_by_capability(update.capability)
            target_agents.extend(agents)
        
        # Ensure unique list
        target_agents = list(set(target_agents))
        
        if not target_agents:
            logger.warning(f"No target agents found for update {update_id}")
            return
        
        # Add to pending updates for each target agent
        for agent_id in target_agents:
            if agent_id not in self.pending_updates:
                self.pending_updates[agent_id] = []
            
            # Check if agent already has this update
            if agent_id in self.agent_updates and update_id in self.agent_updates[agent_id]:
                continue
            
            # Add to pending updates
            self.pending_updates[agent_id].append((update_id, update))
        
        logger.info(f"Scheduled update {update_id} for distribution to {len(target_agents)} agents")
    
    def mark_update_received(self, agent_id: str, update_id: str):
        """
        Mark an update as received by an agent
        
        Args:
            agent_id: The agent ID
            update_id: The update ID
        """
        # Record that agent has received the update
        if agent_id not in self.agent_updates:
            self.agent_updates[agent_id] = set()
        
        self.agent_updates[agent_id].add(update_id)
        
        # Remove from pending updates
        if agent_id in self.pending_updates:
            self.pending_updates[agent_id] = [
                (uid, update) for uid, update in self.pending_updates[agent_id]
                if uid != update_id
            ]
    
    def get_pending_updates(self, agent_id: str) -> List[LearningUpdate]:
        """
        Get pending updates for an agent
        
        Args:
            agent_id: The agent ID
            
        Returns:
            List of pending updates
        """
        if agent_id not in self.pending_updates:
            return []
        
        return [update for _, update in self.pending_updates[agent_id]]
    
    def _distribution_loop(self):
        """Background thread for distributing updates to agents"""
        while self.running:
            try:
                # For each agent with pending updates
                for agent_id, updates in list(self.pending_updates.items()):
                    if not updates:
                        continue
                    
                    # Check if agent is active
                    agent = self.server.agent_registry.get_agent_identity(agent_id)
                    if not agent or agent.status == "offline":
                        continue
                    
                    # Send updates one at a time
                    update_id, update = updates[0]
                    self._send_update_to_agent(agent_id, update_id, update)
                    
                    # Wait before sending next update (to avoid overwhelming agents)
                    break
                
                # Sleep to prevent CPU spinning
                time.sleep(10)  # Distribute updates every 10 seconds
            
            except Exception as e:
                logger.error(f"Error in distribution loop: {e}")
                time.sleep(60)  # Sleep longer after error
    
    def _send_update_to_agent(self, agent_id: str, update_id: str, update: LearningUpdate):
        """Send an update to an agent"""
        # Create a learning update message
        message = {
            "sender": {
                "agent_id": "knowledge_distributor",
                "agent_type": "system"
            },
            "recipients": [agent_id],
            "message_type": MessageType.LEARNING_UPDATE.value,
            "priority": MessagePriority.MEDIUM.value,
            "content": {
                "update_id": update_id,
                "agent_types": update.agent_types,
                "capability": update.capability,
                "pattern": update.pattern,
                "effectiveness": update.effectiveness,
                "confidence": update.confidence
            },
            "metadata": {
                "conversation_id": str(uuid.uuid4()),
                "requires_acknowledgment": True
            }
        }
        
        # Send message via protocol server
        self.server.message_broker.route_message(message)
        logger.info(f"Sent update {update_id} to agent {agent_id}")
    
    def stop(self):
        """Stop the knowledge distributor"""
        self.running = False
        if self.distribution_thread.is_alive():
            self.distribution_thread.join(timeout=1.0)


# =============================================================================
# Continuous Learning System
# =============================================================================

class ContinuousLearningSystem:
    """
    Main class that coordinates all continuous learning components.
    
    This system manages:
    - Feedback collection and processing
    - Pattern identification and storage
    - Model updating
    - Knowledge distribution
    """
    
    def __init__(self):
        """Initialize the continuous learning system"""
        self.feedback_collector = FeedbackCollector()
        self.pattern_repository = PatternRepository()
        self.model_updater = ModelUpdateManager()
        self.knowledge_distributor = AgentKnowledgeDistributor()
        
        logger.info("Continuous learning system initialized")
    
    def record_feedback(self, feedback: FeedbackRecord) -> str:
        """
        Record feedback on an agent action
        
        Args:
            feedback: The feedback record
            
        Returns:
            The feedback ID
        """
        return self.feedback_collector.record_feedback(feedback)
    
    def register_learning_update(self, update: LearningUpdate) -> str:
        """
        Register a new learning update
        
        Args:
            update: The learning update
            
        Returns:
            The update ID
        """
        # Store the update
        update_id = self.pattern_repository.add_pattern(update)
        
        # Schedule distribution to agents
        self.knowledge_distributor.distribute_update(update)
        
        # Schedule model update if high confidence
        if update.confidence >= 0.8:
            # Determine which models to update based on capability
            capability = update.capability
            models_to_update = []
            
            # Get server instance
            server = get_server()
            
            # Find models that handle this capability
            for model_id, model_config in server.model_manager.models.items():
                if capability in model_config.capabilities:
                    models_to_update.append(model_id)
            
            # Schedule updates
            for model_id in models_to_update:
                self.model_updater.schedule_model_update(model_id)
        
        return update_id
    
    def get_patterns_for_agent(self, agent_id: str, agent_type: str, capabilities: List[str]) -> List[LearningUpdate]:
        """
        Get all relevant patterns for an agent
        
        Args:
            agent_id: The agent ID
            agent_type: The agent type
            capabilities: List of agent capabilities
            
        Returns:
            List of relevant patterns
        """
        # Get patterns by agent type
        type_patterns = self.pattern_repository.get_patterns_by_agent_type(agent_type)
        
        # Get patterns by capability
        capability_patterns = []
        for capability in capabilities:
            capability_patterns.extend(self.pattern_repository.get_patterns_by_capability(capability))
        
        # Combine and deduplicate
        all_patterns = {}
        for pattern in type_patterns + capability_patterns:
            all_patterns[pattern.update_id] = pattern
        
        return list(all_patterns.values())
    
    def stop(self):
        """Stop all components of the continuous learning system"""
        self.feedback_collector.stop()
        self.model_updater.stop()
        self.knowledge_distributor.stop()
        logger.info("Continuous learning system stopped")


# Singleton instance
_learning_system = None

def get_learning_system() -> ContinuousLearningSystem:
    """
    Get the singleton instance of the continuous learning system
    
    Returns:
        The continuous learning system
    """
    global _learning_system
    if _learning_system is None:
        _learning_system = ContinuousLearningSystem()
    
    return _learning_system