"""
Model Content Protocol Server for Code Deep Dive Analyzer

This module implements the central protocol server that manages AI model interactions,
routes requests to appropriate models, and orchestrates agent communications.
"""

import os
import json
import time
import uuid
import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
import threading
import queue
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# Protocol Message Classes
# =============================================================================

class MessageType(Enum):
    """Types of messages that can be exchanged between agents and the protocol server"""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    ALERT = "alert"
    CAPABILITY_UPDATE = "capability_update"
    STATUS_UPDATE = "status_update"
    LEARNING_UPDATE = "learning_update"


class MessagePriority(Enum):
    """Priority levels for agent messages"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    BACKGROUND = 1


@dataclass
class AgentIdentity:
    """Identity information for an agent"""
    agent_id: str
    agent_type: str
    capabilities: List[str] = field(default_factory=list)
    status: str = "idle"
    trust_score: float = 1.0
    last_seen: float = field(default_factory=time.time)


@dataclass
class ProtocolMessage:
    """Standard message format for agent communication"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    sender: AgentIdentity = None
    recipients: List[str] = field(default_factory=list)
    message_type: MessageType = MessageType.REQUEST
    priority: MessagePriority = MessagePriority.MEDIUM
    content: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        result = asdict(self)
        result["message_type"] = self.message_type.value
        result["priority"] = self.priority.value
        if self.sender:
            result["sender"] = asdict(self.sender)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProtocolMessage":
        """Create message from dictionary"""
        # Handle enum conversions
        if "message_type" in data:
            data["message_type"] = MessageType(data["message_type"])
        if "priority" in data:
            data["priority"] = MessagePriority(data["priority"])
        if "sender" in data and data["sender"]:
            data["sender"] = AgentIdentity(**data["sender"])
        return cls(**data)


# =============================================================================
# Model Management
# =============================================================================

class ModelProvider(Enum):
    """Supported AI model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    model_id: str
    provider: ModelProvider
    capabilities: List[str]
    max_tokens: int
    token_cost_input: float
    token_cost_output: float
    context_length: int
    multi_modal: bool = False
    streaming: bool = True
    priority: int = 1  # Higher number = higher priority


class ModelManager:
    """
    Manages AI model configurations, selection, and availability
    """
    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self.default_models: Dict[str, str] = {}  # capability -> model_id
        self._initialize_default_models()
    
    def _initialize_default_models(self):
        """Initialize with default models"""
        # OpenAI models
        self.register_model(
            model_id="gpt-4o",
            provider=ModelProvider.OPENAI,
            capabilities=["code_analysis", "text_generation", "image_understanding"],
            max_tokens=4096,
            token_cost_input=0.01,
            token_cost_output=0.03,
            context_length=128000,
            multi_modal=True
        )
        
        self.register_model(
            model_id="gpt-3.5-turbo",
            provider=ModelProvider.OPENAI,
            capabilities=["text_generation", "quick_analysis"],
            max_tokens=4096,
            token_cost_input=0.0015,
            token_cost_output=0.002,
            context_length=16384
        )
        
        # Anthropic models
        self.register_model(
            model_id="claude-3-5-sonnet-20241022",
            provider=ModelProvider.ANTHROPIC,
            capabilities=["code_analysis", "text_generation", "reasoning"],
            max_tokens=4096,
            token_cost_input=0.008,
            token_cost_output=0.024,
            context_length=200000,
            multi_modal=True
        )
        
        # Set default models for each capability
        self.default_models = {
            "code_analysis": "gpt-4o",
            "text_generation": "gpt-3.5-turbo",
            "reasoning": "claude-3-5-sonnet-20241022",
            "image_understanding": "gpt-4o",
            "quick_analysis": "gpt-3.5-turbo"
        }
    
    def register_model(self, model_id: str, provider: ModelProvider, 
                      capabilities: List[str], max_tokens: int, 
                      token_cost_input: float, token_cost_output: float,
                      context_length: int, multi_modal: bool = False,
                      streaming: bool = True, priority: int = 1):
        """Register a new model with the manager"""
        self.models[model_id] = ModelConfig(
            model_id=model_id,
            provider=provider,
            capabilities=capabilities,
            max_tokens=max_tokens,
            token_cost_input=token_cost_input,
            token_cost_output=token_cost_output,
            context_length=context_length,
            multi_modal=multi_modal,
            streaming=streaming,
            priority=priority
        )
        
        # Update default models if this has higher priority
        for capability in capabilities:
            if (capability not in self.default_models or 
                priority > self.models[self.default_models[capability]].priority):
                self.default_models[capability] = model_id
    
    def get_model_for_capability(self, capability: str) -> Optional[ModelConfig]:
        """Get the best model for a specific capability"""
        if capability in self.default_models:
            return self.models.get(self.default_models[capability])
        return None
    
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model"""
        return self.models.get(model_id)


# =============================================================================
# Agent Management
# =============================================================================

class AgentCategory(Enum):
    """Categories of specialized agents"""
    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    DATABASE = "database"
    DOCUMENTATION = "documentation"
    AGENT_READINESS = "agent_readiness"
    LEARNING_COORDINATOR = "learning_coordinator"
    ORCHESTRATOR = "orchestrator"


@dataclass
class AgentConfig:
    """Configuration for a specialized agent"""
    agent_id: str
    agent_type: AgentCategory
    capabilities: List[str] = field(default_factory=list)
    preferred_model: Optional[str] = None
    active: bool = True
    max_concurrent_tasks: int = 1


class AgentRegistry:
    """
    Manages the registration and tracking of available agents
    """
    def __init__(self):
        self.agents: Dict[str, AgentIdentity] = {}
        self.agent_configs: Dict[str, AgentConfig] = {}
        self.agents_by_type: Dict[AgentCategory, List[str]] = {
            category: [] for category in AgentCategory
        }
    
    def register_agent(self, agent_config: AgentConfig) -> None:
        """Register a new agent"""
        self.agent_configs[agent_config.agent_id] = agent_config
        self.agents[agent_config.agent_id] = AgentIdentity(
            agent_id=agent_config.agent_id,
            agent_type=agent_config.agent_type.value,
            capabilities=agent_config.capabilities
        )
        self.agents_by_type[agent_config.agent_type].append(agent_config.agent_id)
        logger.info(f"Agent registered: {agent_config.agent_id} ({agent_config.agent_type.value})")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent"""
        if agent_id in self.agent_configs:
            agent_type = self.agent_configs[agent_id].agent_type
            self.agents_by_type[agent_type].remove(agent_id)
            del self.agent_configs[agent_id]
            del self.agents[agent_id]
            logger.info(f"Agent unregistered: {agent_id}")
    
    def update_agent_status(self, agent_id: str, status: str) -> None:
        """Update the status of an agent"""
        if agent_id in self.agents:
            self.agents[agent_id].status = status
            self.agents[agent_id].last_seen = time.time()
    
    def update_agent_capabilities(self, agent_id: str, capabilities: List[str]) -> None:
        """Update the capabilities of an agent"""
        if agent_id in self.agents:
            self.agents[agent_id].capabilities = capabilities
            if agent_id in self.agent_configs:
                self.agent_configs[agent_id].capabilities = capabilities
    
    def get_agents_by_capability(self, capability: str) -> List[str]:
        """Get all agents with a specific capability"""
        return [
            agent_id for agent_id, agent in self.agents.items()
            if capability in agent.capabilities and agent.status != "offline"
        ]
    
    def get_agents_by_type(self, agent_type: AgentCategory) -> List[str]:
        """Get all agents of a specific type"""
        return [
            agent_id for agent_id in self.agents_by_type[agent_type]
            if agent_id in self.agents and self.agents[agent_id].status != "offline"
        ]
    
    def get_agent_identity(self, agent_id: str) -> Optional[AgentIdentity]:
        """Get the identity of a specific agent"""
        return self.agents.get(agent_id)


# =============================================================================
# Message Broker
# =============================================================================

class MessageBroker:
    """
    Handles message routing between agents and maintains message queues
    """
    def __init__(self, agent_registry: AgentRegistry):
        self.agent_registry = agent_registry
        self.message_queues: Dict[str, queue.PriorityQueue] = {}
        self.global_broadcast_queue = queue.PriorityQueue()
        self.message_history: Dict[str, ProtocolMessage] = {}
        self.conversation_threads: Dict[str, List[str]] = {}  # conversation_id -> [message_ids]
        self._initialize_queues()
    
    def _initialize_queues(self) -> None:
        """Initialize message queues for all registered agents"""
        for agent_id in self.agent_registry.agents.keys():
            self.message_queues[agent_id] = queue.PriorityQueue()
    
    def _get_priority_value(self, priority: MessagePriority) -> int:
        """Convert priority enum to integer for queue prioritization (lower = higher priority)"""
        return 6 - priority.value
    
    def route_message(self, message: ProtocolMessage) -> None:
        """Route a message to its intended recipients"""
        # Store in message history
        self.message_history[message.message_id] = message
        
        # Track conversation thread
        conversation_id = message.metadata.get("conversation_id")
        if conversation_id:
            if conversation_id not in self.conversation_threads:
                self.conversation_threads[conversation_id] = []
            self.conversation_threads[conversation_id].append(message.message_id)
        
        # Handle broadcasts
        if "ALL" in message.recipients:
            # Put in global broadcast queue
            priority = self._get_priority_value(message.priority)
            self.global_broadcast_queue.put((priority, message))
            return
        
        # Handle agent category broadcasts
        category_broadcasts = []
        for recipient in message.recipients:
            if recipient.startswith("category:"):
                category_name = recipient.split(":")[1]
                try:
                    category = AgentCategory(category_name)
                    category_broadcasts.append(category)
                except ValueError:
                    logger.warning(f"Unknown agent category in recipient: {recipient}")
        
        # Get individual recipients from categories
        category_recipient_ids = []
        for category in category_broadcasts:
            category_recipient_ids.extend(self.agent_registry.get_agents_by_type(category))
        
        # Remove category specifiers and add individual agents
        direct_recipients = [r for r in message.recipients if not r.startswith("category:")]
        all_recipients = list(set(direct_recipients + category_recipient_ids))
        
        # Route to individual recipients
        priority = self._get_priority_value(message.priority)
        for recipient_id in all_recipients:
            if recipient_id in self.message_queues:
                self.message_queues[recipient_id].put((priority, message))
            else:
                logger.warning(f"Message sent to unknown agent: {recipient_id}")
    
    def get_next_message(self, agent_id: str) -> Optional[ProtocolMessage]:
        """Get the next message for an agent"""
        if agent_id not in self.message_queues:
            return None
        
        # Check direct messages first
        try:
            if not self.message_queues[agent_id].empty():
                _, message = self.message_queues[agent_id].get(block=False)
                return message
        except queue.Empty:
            pass
        
        # Then check broadcasts
        try:
            if not self.global_broadcast_queue.empty():
                _, message = self.global_broadcast_queue.get(block=False)
                # Don't return broadcast messages sent by this agent
                if message.sender and message.sender.agent_id != agent_id:
                    return message
        except queue.Empty:
            pass
        
        return None
    
    def get_conversation_thread(self, conversation_id: str) -> List[ProtocolMessage]:
        """Get all messages in a conversation thread"""
        if conversation_id not in self.conversation_threads:
            return []
        
        return [
            self.message_history[msg_id] 
            for msg_id in self.conversation_threads[conversation_id]
            if msg_id in self.message_history
        ]


# =============================================================================
# Task Orchestration
# =============================================================================

@dataclass
class Task:
    """Represents a task to be performed by an agent"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    description: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    assigned_agent: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    deadline: Optional[float] = None
    status: str = "pending"  # pending, assigned, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)  # task_ids this task depends on
    priority: MessagePriority = MessagePriority.MEDIUM


class TaskOrchestrator:
    """
    Coordinates task assignment, execution tracking, and dependency management
    """
    def __init__(self, agent_registry: AgentRegistry, message_broker: MessageBroker):
        self.agent_registry = agent_registry
        self.message_broker = message_broker
        self.tasks: Dict[str, Task] = {}
        self.agent_tasks: Dict[str, List[str]] = {}  # agent_id -> [task_ids]
        self.pending_tasks: List[str] = []
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []
        self.task_lock = threading.Lock()
        
        # Start the task assignment thread
        self.running = True
        self.assignment_thread = threading.Thread(target=self._task_assignment_loop)
        self.assignment_thread.daemon = True
        self.assignment_thread.start()
    
    def submit_task(self, task: Task) -> str:
        """Submit a new task for orchestration"""
        with self.task_lock:
            self.tasks[task.task_id] = task
            
            # If the task has unmet dependencies, don't add to pending yet
            if all(dep_id in self.completed_tasks for dep_id in task.dependencies):
                self.pending_tasks.append(task.task_id)
            
            logger.info(f"Task submitted: {task.task_id} - {task.description}")
            return task.task_id
    
    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """Manually assign a task to a specific agent"""
        with self.task_lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            task.assigned_agent = agent_id
            task.status = "assigned"
            
            if agent_id not in self.agent_tasks:
                self.agent_tasks[agent_id] = []
            
            self.agent_tasks[agent_id].append(task_id)
            
            if task_id in self.pending_tasks:
                self.pending_tasks.remove(task_id)
            
            # Create task assignment message
            self._send_task_assignment(task, agent_id)
            return True
    
    def update_task_status(self, task_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """Update the status of a task"""
        with self.task_lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            old_status = task.status
            task.status = status
            
            if result is not None:
                task.result = result
            
            # Handle status transitions
            if status == "completed":
                if task_id not in self.completed_tasks:
                    self.completed_tasks.append(task_id)
                
                if task.assigned_agent and task_id in self.agent_tasks.get(task.assigned_agent, []):
                    self.agent_tasks[task.assigned_agent].remove(task_id)
                
                # Check for dependent tasks that can now be scheduled
                self._check_dependent_tasks(task_id)
            
            elif status == "failed":
                if task_id not in self.failed_tasks:
                    self.failed_tasks.append(task_id)
                
                if task.assigned_agent and task_id in self.agent_tasks.get(task.assigned_agent, []):
                    self.agent_tasks[task.assigned_agent].remove(task_id)
            
            logger.info(f"Task {task_id} status updated: {old_status} -> {status}")
            return True
    
    def _check_dependent_tasks(self, completed_task_id: str) -> None:
        """Check for tasks that depend on a completed task and schedule them if ready"""
        for task_id, task in self.tasks.items():
            if (task_id not in self.pending_tasks and
                task.status == "pending" and 
                completed_task_id in task.dependencies):
                
                # Check if all dependencies are now satisfied
                if all(dep_id in self.completed_tasks for dep_id in task.dependencies):
                    self.pending_tasks.append(task_id)
                    logger.info(f"Task {task_id} is now ready for assignment (dependencies satisfied)")
    
    def _task_assignment_loop(self) -> None:
        """Background thread for automatic task assignment"""
        while self.running:
            tasks_assigned = 0
            
            with self.task_lock:
                # Create a copy to avoid modification during iteration
                pending_tasks = self.pending_tasks.copy()
                
                for task_id in pending_tasks:
                    if task_id not in self.tasks:
                        self.pending_tasks.remove(task_id)
                        continue
                    
                    task = self.tasks[task_id]
                    
                    # Skip already assigned tasks
                    if task.status != "pending":
                        self.pending_tasks.remove(task_id)
                        continue
                    
                    # Find suitable agent based on task type
                    assigned = self._find_and_assign_agent(task)
                    if assigned:
                        tasks_assigned += 1
                        self.pending_tasks.remove(task_id)
            
            # Sleep to prevent CPU spinning
            time.sleep(1 if tasks_assigned == 0 else 0.1)
    
    def _find_and_assign_agent(self, task: Task) -> bool:
        """Find an appropriate agent for a task and assign it"""
        capable_agents = self.agent_registry.get_agents_by_capability(task.task_type)
        
        if not capable_agents:
            logger.warning(f"No agents capable of task type: {task.task_type}")
            return False
        
        # Filter to only active agents
        active_agents = [
            agent_id for agent_id in capable_agents
            if self.agent_registry.agents[agent_id].status in ["idle", "active"]
        ]
        
        if not active_agents:
            return False
        
        # Find agent with fewest current tasks
        agent_load = {agent_id: len(self.agent_tasks.get(agent_id, [])) for agent_id in active_agents}
        
        # Get agent configs to check max concurrent tasks
        agent_max_tasks = {}
        for agent_id in active_agents:
            if agent_id in self.agent_registry.agent_configs:
                max_tasks = self.agent_registry.agent_configs[agent_id].max_concurrent_tasks
                agent_max_tasks[agent_id] = max_tasks
            else:
                agent_max_tasks[agent_id] = 1
        
        # Filter to agents that haven't reached their limit
        available_agents = [
            agent_id for agent_id in active_agents
            if agent_load.get(agent_id, 0) < agent_max_tasks.get(agent_id, 1)
        ]
        
        if not available_agents:
            return False
        
        # Select agent with lowest current load
        best_agent = min(available_agents, key=lambda a: agent_load.get(a, 0))
        
        # Assign task
        task.assigned_agent = best_agent
        task.status = "assigned"
        
        if best_agent not in self.agent_tasks:
            self.agent_tasks[best_agent] = []
        
        self.agent_tasks[best_agent].append(task.task_id)
        
        # Send assignment message
        self._send_task_assignment(task, best_agent)
        
        logger.info(f"Task {task.task_id} assigned to agent {best_agent}")
        return True
    
    def _send_task_assignment(self, task: Task, agent_id: str) -> None:
        """Create and send a task assignment message to an agent"""
        message = ProtocolMessage(
            sender=AgentIdentity(
                agent_id="orchestrator",
                agent_type=AgentCategory.ORCHESTRATOR.value
            ),
            recipients=[agent_id],
            message_type=MessageType.REQUEST,
            priority=task.priority,
            content={
                "task_id": task.task_id,
                "task_type": task.task_type,
                "description": task.description,
                "input_data": task.input_data
            },
            metadata={
                "conversation_id": task.conversation_id,
                "requires_response": True
            }
        )
        
        self.message_broker.route_message(message)


# =============================================================================
# Learning System
# =============================================================================

@dataclass
class FeedbackRecord:
    """Record of feedback on agent actions"""
    feedback_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    agent_id: str = ""
    action_type: str = ""
    timestamp: float = field(default_factory=time.time)
    rating: float = 0.0  # 0-1 rating
    source: str = ""  # user, agent, system
    comments: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningUpdate:
    """Represents a learning update for agent improvement"""
    update_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_types: List[str] = field(default_factory=list)
    capability: str = ""
    pattern: Dict[str, Any] = field(default_factory=dict)
    effectiveness: float = 0.0
    confidence: float = 0.0
    supporting_evidence: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


class LearningSystem:
    """
    Manages feedback collection, pattern recognition, and agent improvement
    """
    def __init__(self, agent_registry: AgentRegistry, message_broker: MessageBroker):
        self.agent_registry = agent_registry
        self.message_broker = message_broker
        self.feedback_records: Dict[str, FeedbackRecord] = {}
        self.learning_updates: Dict[str, LearningUpdate] = {}
        self.agent_performance: Dict[str, Dict[str, float]] = {}  # agent_id -> {metric: value}
        self.pattern_database: List[Dict[str, Any]] = []
        
        # Create the learning coordinator
        self._register_learning_coordinator()
    
    def _register_learning_coordinator(self) -> None:
        """Register the learning coordinator agent"""
        coordinator_config = AgentConfig(
            agent_id="learning_coordinator",
            agent_type=AgentCategory.LEARNING_COORDINATOR,
            capabilities=["pattern_recognition", "feedback_analysis", "model_evaluation"],
            preferred_model="gpt-4o",
            active=True,
            max_concurrent_tasks=5
        )
        
        self.agent_registry.register_agent(coordinator_config)
    
    def record_feedback(self, feedback: FeedbackRecord) -> str:
        """Record feedback on an agent action"""
        self.feedback_records[feedback.feedback_id] = feedback
        
        # Update agent performance metrics
        if feedback.agent_id not in self.agent_performance:
            self.agent_performance[feedback.agent_id] = {"average_rating": 0.0, "feedback_count": 0}
        
        # Update average rating
        current_avg = self.agent_performance[feedback.agent_id]["average_rating"]
        current_count = self.agent_performance[feedback.agent_id]["feedback_count"]
        new_count = current_count + 1
        new_avg = (current_avg * current_count + feedback.rating) / new_count
        
        self.agent_performance[feedback.agent_id].update({
            "average_rating": new_avg,
            "feedback_count": new_count,
            "last_feedback": feedback.timestamp
        })
        
        # Send feedback to learning coordinator
        self._notify_learning_coordinator(feedback)
        
        return feedback.feedback_id
    
    def _notify_learning_coordinator(self, feedback: FeedbackRecord) -> None:
        """Notify the learning coordinator about new feedback"""
        message = ProtocolMessage(
            sender=AgentIdentity(
                agent_id="learning_system",
                agent_type="system"
            ),
            recipients=["learning_coordinator"],
            message_type=MessageType.REQUEST,
            priority=MessagePriority.LOW,
            content={
                "action": "process_feedback",
                "feedback_id": feedback.feedback_id,
                "feedback": asdict(feedback)
            },
            metadata={
                "conversation_id": str(uuid.uuid4()),
                "requires_response": False
            }
        )
        
        self.message_broker.route_message(message)
    
    def register_learning_update(self, update: LearningUpdate) -> str:
        """Register a new learning update"""
        self.learning_updates[update.update_id] = update
        
        # Add to pattern database
        self.pattern_database.append({
            "update_id": update.update_id,
            "agent_types": update.agent_types,
            "capability": update.capability,
            "pattern": update.pattern,
            "effectiveness": update.effectiveness,
            "confidence": update.confidence,
            "created_at": update.created_at
        })
        
        # Broadcast learning update to relevant agents
        self._broadcast_learning_update(update)
        
        return update.update_id
    
    def _broadcast_learning_update(self, update: LearningUpdate) -> None:
        """Broadcast a learning update to relevant agents"""
        # Create list of recipients based on agent types
        recipients = []
        for agent_type in update.agent_types:
            try:
                category = AgentCategory(agent_type)
                recipients.append(f"category:{category.value}")
            except ValueError:
                # If not a category, might be a specific agent
                if agent_type in self.agent_registry.agents:
                    recipients.append(agent_type)
        
        # If no specific recipients, broadcast to all
        if not recipients:
            recipients = ["ALL"]
        
        message = ProtocolMessage(
            sender=AgentIdentity(
                agent_id="learning_system",
                agent_type="system"
            ),
            recipients=recipients,
            message_type=MessageType.LEARNING_UPDATE,
            priority=MessagePriority.MEDIUM,
            content={
                "update_type": "learning_pattern",
                "update_id": update.update_id,
                "capability": update.capability,
                "pattern": update.pattern,
                "effectiveness": update.effectiveness,
                "confidence": update.confidence
            },
            metadata={
                "conversation_id": str(uuid.uuid4()),
                "requires_action": True,
                "action": "apply_learning_update"
            }
        )
        
        self.message_broker.route_message(message)
    
    def get_relevant_patterns(self, agent_type: str, capability: str) -> List[Dict[str, Any]]:
        """Get relevant patterns for a specific agent type and capability"""
        return [
            pattern for pattern in self.pattern_database
            if (agent_type in pattern["agent_types"] or "ALL" in pattern["agent_types"]) and
            (pattern["capability"] == capability or pattern["capability"] == "ALL") and
            pattern["effectiveness"] >= 0.6  # Only return patterns with good effectiveness
        ]


# =============================================================================
# Protocol Server
# =============================================================================

class ProtocolServer:
    """
    Main server class that coordinates all components of the agent system
    """
    def __init__(self):
        self.model_manager = ModelManager()
        self.agent_registry = AgentRegistry()
        self.message_broker = MessageBroker(self.agent_registry)
        self.task_orchestrator = TaskOrchestrator(self.agent_registry, self.message_broker)
        self.learning_system = LearningSystem(self.agent_registry, self.message_broker)
        
        self.running = False
        self.main_thread = None
        
        # Install signal handlers for graceful shutdown
        try:
            import signal
            signal.signal(signal.SIGINT, self._handle_shutdown)
            signal.signal(signal.SIGTERM, self._handle_shutdown)
        except (ImportError, AttributeError):
            # Windows doesn't support SIGTERM
            pass
    
    def start(self):
        """Start the protocol server"""
        if self.running:
            logger.warning("Protocol server is already running")
            return
        
        self.running = True
        logger.info("Starting protocol server")
        
        # Register core system agents
        self._register_system_agents()
        
        # Start main processing thread
        self.main_thread = threading.Thread(target=self._main_loop)
        self.main_thread.daemon = True
        self.main_thread.start()
        
        logger.info("Protocol server started")
    
    def stop(self):
        """Stop the protocol server"""
        if not self.running:
            return
        
        logger.info("Stopping protocol server")
        self.running = False
        
        if self.main_thread:
            self.main_thread.join(timeout=5.0)
        
        logger.info("Protocol server stopped")
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down")
        self.stop()
    
    def _register_system_agents(self):
        """Register the core system agents"""
        # Register orchestrator
        orchestrator_config = AgentConfig(
            agent_id="orchestrator",
            agent_type=AgentCategory.ORCHESTRATOR,
            capabilities=["task_management", "agent_coordination"],
            preferred_model="gpt-4o",
            active=True,
            max_concurrent_tasks=10
        )
        self.agent_registry.register_agent(orchestrator_config)
        
        # Learning coordinator is registered by the learning system
    
    def _main_loop(self):
        """Main processing loop"""
        while self.running:
            # Periodic cleanup and maintenance
            self._check_agent_status()
            
            # Sleep to prevent CPU spinning
            time.sleep(1.0)
    
    def _check_agent_status(self):
        """Check the status of all agents and update accordingly"""
        current_time = time.time()
        timeout_threshold = 60.0  # 1 minute
        
        for agent_id, agent in list(self.agent_registry.agents.items()):
            # Skip system agents
            if agent_id in ["orchestrator", "learning_coordinator"]:
                continue
            
            # If agent hasn't sent a heartbeat in a while, mark as offline
            if current_time - agent.last_seen > timeout_threshold and agent.status != "offline":
                logger.warning(f"Agent {agent_id} appears to be offline (no heartbeat)")
                self.agent_registry.update_agent_status(agent_id, "offline")
    
    def register_agent(self, agent_config: AgentConfig) -> None:
        """Register a new agent with the system"""
        self.agent_registry.register_agent(agent_config)
    
    def send_message(self, message: ProtocolMessage) -> None:
        """Send a message through the broker"""
        self.message_broker.route_message(message)
    
    def submit_task(self, task: Task) -> str:
        """Submit a task for orchestration"""
        return self.task_orchestrator.submit_task(task)
    
    def record_feedback(self, feedback: FeedbackRecord) -> str:
        """Record feedback on an agent action"""
        return self.learning_system.record_feedback(feedback)
    
    def get_model_for_capability(self, capability: str) -> Optional[ModelConfig]:
        """Get the best model for a capability"""
        return self.model_manager.get_model_for_capability(capability)


# =============================================================================
# Server Instance
# =============================================================================

# Global server instance
_server_instance = None

def get_server():
    """Get or create the protocol server singleton instance"""
    global _server_instance
    if _server_instance is None:
        _server_instance = ProtocolServer()
    return _server_instance


def start_server():
    """Start the protocol server"""
    server = get_server()
    server.start()
    return server


def stop_server():
    """Stop the protocol server"""
    global _server_instance
    if _server_instance is not None:
        _server_instance.stop()
        _server_instance = None


# Make server startable via command line
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Model Content Protocol Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    
    server = start_server()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        stop_server()