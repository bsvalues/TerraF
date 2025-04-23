"""
Agent Orchestrator

This module implements an orchestrator for specialized AI agents, enabling collective intelligence
through sophisticated communication, task allocation, and coordination mechanisms.
"""
import os
import json
import logging
import time
import uuid
import threading
from queue import Queue, PriorityQueue
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable

class AgentType(Enum):
    """Types of AI agents in the system."""
    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    DATABASE = "database"
    DOCUMENTATION = "documentation"
    LEARNING_COORDINATOR = "learning_coordinator"
    AGENT_READINESS = "agent_readiness"
    CUSTOM = "custom"


class AgentStatus(Enum):
    """Status of an agent in the system."""
    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    LEARNING = "learning"
    ERROR = "error"
    OFFLINE = "offline"


class MessageType(Enum):
    """Types of messages that agents can exchange."""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    ALERT = "alert"
    LEARNING_UPDATE = "learning_update"


class MessagePriority(Enum):
    """Priority levels for messages."""
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class TaskStatus(Enum):
    """Status of a task in the system."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class Message:
    """
    Represents a message between agents.
    """
    
    def __init__(self, message_id: str, sender: str, recipients: List[str],
               message_type: MessageType, content: Dict[str, Any],
               priority: MessagePriority = MessagePriority.MEDIUM,
               conversation_id: Optional[str] = None,
               in_reply_to: Optional[str] = None,
               metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a message.
        
        Args:
            message_id: Unique identifier for the message
            sender: ID of the sending agent
            recipients: List of recipient agent IDs
            message_type: Type of message
            content: Message content
            priority: Message priority
            conversation_id: Optional ID of the conversation this message is part of
            in_reply_to: Optional ID of the message this is a reply to
            metadata: Optional message metadata
        """
        self.id = message_id
        self.sender = sender
        self.recipients = recipients
        self.message_type = message_type
        self.content = content
        self.priority = priority
        self.conversation_id = conversation_id or message_id  # Use message_id as conversation_id if not provided
        self.in_reply_to = in_reply_to
        self.metadata = metadata or {}
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to a dictionary."""
        return {
            'id': self.id,
            'sender': self.sender,
            'recipients': self.recipients,
            'message_type': self.message_type.value,
            'content': self.content,
            'priority': self.priority.value,
            'conversation_id': self.conversation_id,
            'in_reply_to': self.in_reply_to,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a message from a dictionary.
        
        Args:
            data: Message data dictionary
        
        Returns:
            Message instance
        """
        return cls(
            message_id=data['id'],
            sender=data['sender'],
            recipients=data['recipients'],
            message_type=MessageType(data['message_type']),
            content=data['content'],
            priority=MessagePriority(data['priority']),
            conversation_id=data.get('conversation_id'),
            in_reply_to=data.get('in_reply_to'),
            metadata=data.get('metadata', {})
        )


class Task:
    """
    Represents a task that can be assigned to an agent.
    """
    
    def __init__(self, task_id: str, task_type: str, requester: str,
               parameters: Dict[str, Any], priority: int = 2,
               deadline: Optional[float] = None,
               metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a task.
        
        Args:
            task_id: Unique identifier for the task
            task_type: Type of task
            requester: ID of the agent or system requesting the task
            parameters: Task parameters
            priority: Task priority (1=high, 3=low)
            deadline: Optional deadline timestamp
            metadata: Optional task metadata
        """
        self.id = task_id
        self.task_type = task_type
        self.requester = requester
        self.parameters = parameters
        self.priority = priority
        self.deadline = deadline
        self.metadata = metadata or {}
        self.status = TaskStatus.PENDING
        self.assigned_to = None
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to a dictionary."""
        return {
            'id': self.id,
            'task_type': self.task_type,
            'requester': self.requester,
            'parameters': self.parameters,
            'priority': self.priority,
            'deadline': self.deadline,
            'metadata': self.metadata,
            'status': self.status.value,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'result': self.result,
            'error': self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """
        Create a task from a dictionary.
        
        Args:
            data: Task data dictionary
        
        Returns:
            Task instance
        """
        task = cls(
            task_id=data['id'],
            task_type=data['task_type'],
            requester=data['requester'],
            parameters=data['parameters'],
            priority=data['priority'],
            deadline=data.get('deadline'),
            metadata=data.get('metadata', {})
        )
        
        task.status = TaskStatus(data['status'])
        task.assigned_to = data.get('assigned_to')
        task.created_at = data['created_at']
        task.started_at = data.get('started_at')
        task.completed_at = data.get('completed_at')
        task.result = data.get('result')
        task.error = data.get('error')
        
        return task


class AgentInfo:
    """
    Information about an agent in the system.
    """
    
    def __init__(self, agent_id: str, agent_type: AgentType, name: str,
               capabilities: List[str], metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize agent information.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of the agent
            name: Human-readable name for the agent
            capabilities: List of capabilities the agent provides
            metadata: Optional agent metadata
        """
        self.id = agent_id
        self.agent_type = agent_type
        self.name = name
        self.capabilities = capabilities
        self.metadata = metadata or {}
        self.status = AgentStatus.INITIALIZING
        self.last_heartbeat = time.time()
        self.current_tasks = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent info to a dictionary."""
        return {
            'id': self.id,
            'agent_type': self.agent_type.value,
            'name': self.name,
            'capabilities': self.capabilities,
            'metadata': self.metadata,
            'status': self.status.value,
            'last_heartbeat': self.last_heartbeat,
            'current_tasks': self.current_tasks
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentInfo':
        """
        Create agent info from a dictionary.
        
        Args:
            data: Agent info data dictionary
        
        Returns:
            AgentInfo instance
        """
        agent_info = cls(
            agent_id=data['id'],
            agent_type=AgentType(data['agent_type']),
            name=data['name'],
            capabilities=data['capabilities'],
            metadata=data.get('metadata', {})
        )
        
        agent_info.status = AgentStatus(data['status'])
        agent_info.last_heartbeat = data['last_heartbeat']
        agent_info.current_tasks = data.get('current_tasks', [])
        
        return agent_info


class AgentOrchestrator:
    """
    Orchestrates a team of specialized AI agents.
    
    This class provides:
    - Agent registration and status tracking
    - Message routing and delivery
    - Task allocation and scheduling
    - Collective intelligence coordination
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the agent orchestrator.
        
        Args:
            storage_dir: Optional directory for persistent storage
        """
        # Set up storage directory
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), 'orchestrator_storage')
        
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize logger
        self.logger = logging.getLogger('agent_orchestrator')
        
        # Initialize agent registry
        self.agents = {}  # agent_id -> AgentInfo
        
        # Initialize message queue
        self.message_queue = PriorityQueue()  # (priority, message_id) -> Message
        
        # Initialize task queue
        self.task_queue = PriorityQueue()  # (priority, created_at, task_id) -> Task
        
        # Initialize active tasks and messages
        self.active_tasks = {}  # task_id -> Task
        self.message_store = {}  # message_id -> Message
        
        # Initialize message subscription
        self.subscriptions = {}  # agent_id -> Set[agent_id]
        
        # Initialize stats
        self.stats = {
            'messages_processed': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'agent_heartbeats': 0
        }
        
        # Initialize threading controls
        self.running = False
        self.message_thread = None
        self.task_thread = None
        self.heartbeat_thread = None
        
        # Load existing data
        self._load_data()
    
    def _load_data(self) -> None:
        """Load existing data from storage."""
        # Load agent registry
        agents_dir = os.path.join(self.storage_dir, 'agents')
        if os.path.exists(agents_dir):
            for filename in os.listdir(agents_dir):
                if filename.endswith('.json'):
                    agent_id = filename[:-5]  # Remove '.json'
                    agent_path = os.path.join(agents_dir, filename)
                    
                    try:
                        with open(agent_path, 'r') as f:
                            agent_data = json.load(f)
                        
                        agent_info = AgentInfo.from_dict(agent_data)
                        
                        # Set initial status to offline since we're just loading
                        agent_info.status = AgentStatus.OFFLINE
                        
                        self.agents[agent_id] = agent_info
                        
                        self.logger.info(f"Loaded agent info: {agent_info.name} (ID: {agent_id})")
                    
                    except Exception as e:
                        self.logger.error(f"Error loading agent info from {agent_path}: {e}")
        
        # Load active tasks
        tasks_dir = os.path.join(self.storage_dir, 'tasks')
        if os.path.exists(tasks_dir):
            for filename in os.listdir(tasks_dir):
                if filename.endswith('.json'):
                    task_id = filename[:-5]  # Remove '.json'
                    task_path = os.path.join(tasks_dir, filename)
                    
                    try:
                        with open(task_path, 'r') as f:
                            task_data = json.load(f)
                        
                        task = Task.from_dict(task_data)
                        
                        # Only add non-completed tasks to queue
                        if task.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]:
                            self.active_tasks[task_id] = task
                            
                            # Add to task queue if pending
                            if task.status == TaskStatus.PENDING:
                                self.task_queue.put((task.priority, task.created_at, task_id))
                        
                        self.logger.info(f"Loaded task: {task_id}")
                    
                    except Exception as e:
                        self.logger.error(f"Error loading task from {task_path}: {e}")
        
        # Load message store
        messages_dir = os.path.join(self.storage_dir, 'messages')
        if os.path.exists(messages_dir):
            # Only load recent messages (last 24h)
            cutoff_time = time.time() - 86400  # 24 hours ago
            
            for filename in os.listdir(messages_dir):
                if filename.endswith('.json'):
                    message_id = filename[:-5]  # Remove '.json'
                    message_path = os.path.join(messages_dir, filename)
                    
                    try:
                        with open(message_path, 'r') as f:
                            message_data = json.load(f)
                        
                        # Skip old messages
                        if message_data['timestamp'] < cutoff_time:
                            continue
                        
                        message = Message.from_dict(message_data)
                        
                        self.message_store[message_id] = message
                        
                        self.logger.info(f"Loaded message: {message_id}")
                    
                    except Exception as e:
                        self.logger.error(f"Error loading message from {message_path}: {e}")
        
        # Load stats
        stats_path = os.path.join(self.storage_dir, 'stats.json')
        if os.path.exists(stats_path):
            try:
                with open(stats_path, 'r') as f:
                    self.stats = json.load(f)
                
                self.logger.info("Loaded orchestrator stats")
            
            except Exception as e:
                self.logger.error(f"Error loading orchestrator stats: {e}")
        
        # Load subscriptions
        subscriptions_path = os.path.join(self.storage_dir, 'subscriptions.json')
        if os.path.exists(subscriptions_path):
            try:
                with open(subscriptions_path, 'r') as f:
                    subscriptions_data = json.load(f)
                
                # Convert to sets
                self.subscriptions = {
                    agent_id: set(subscribers)
                    for agent_id, subscribers in subscriptions_data.items()
                }
                
                self.logger.info("Loaded agent subscriptions")
            
            except Exception as e:
                self.logger.error(f"Error loading agent subscriptions: {e}")
    
    def _save_agent_info(self, agent_info: AgentInfo) -> None:
        """
        Save agent info to storage.
        
        Args:
            agent_info: Agent info to save
        """
        agents_dir = os.path.join(self.storage_dir, 'agents')
        os.makedirs(agents_dir, exist_ok=True)
        
        agent_path = os.path.join(agents_dir, f"{agent_info.id}.json")
        
        with open(agent_path, 'w') as f:
            json.dump(agent_info.to_dict(), f, indent=2)
    
    def _save_task(self, task: Task) -> None:
        """
        Save task to storage.
        
        Args:
            task: Task to save
        """
        tasks_dir = os.path.join(self.storage_dir, 'tasks')
        os.makedirs(tasks_dir, exist_ok=True)
        
        task_path = os.path.join(tasks_dir, f"{task.id}.json")
        
        with open(task_path, 'w') as f:
            json.dump(task.to_dict(), f, indent=2)
    
    def _save_message(self, message: Message) -> None:
        """
        Save message to storage.
        
        Args:
            message: Message to save
        """
        messages_dir = os.path.join(self.storage_dir, 'messages')
        os.makedirs(messages_dir, exist_ok=True)
        
        message_path = os.path.join(messages_dir, f"{message.id}.json")
        
        with open(message_path, 'w') as f:
            json.dump(message.to_dict(), f, indent=2)
    
    def _save_stats(self) -> None:
        """Save stats to storage."""
        stats_path = os.path.join(self.storage_dir, 'stats.json')
        
        with open(stats_path, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def _save_subscriptions(self) -> None:
        """Save subscriptions to storage."""
        subscriptions_path = os.path.join(self.storage_dir, 'subscriptions.json')
        
        # Convert sets to lists for JSON serialization
        subscriptions_data = {
            agent_id: list(subscribers)
            for agent_id, subscribers in self.subscriptions.items()
        }
        
        with open(subscriptions_path, 'w') as f:
            json.dump(subscriptions_data, f, indent=2)
    
    def start(self) -> None:
        """Start the orchestrator threads."""
        if self.running:
            return
        
        self.running = True
        
        # Start message processing thread
        self.message_thread = threading.Thread(target=self._message_processor)
        self.message_thread.daemon = True
        self.message_thread.start()
        
        # Start task processing thread
        self.task_thread = threading.Thread(target=self._task_processor)
        self.task_thread.daemon = True
        self.task_thread.start()
        
        # Start heartbeat monitoring thread
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_monitor)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        
        self.logger.info("Started agent orchestrator")
    
    def stop(self) -> None:
        """Stop the orchestrator threads."""
        self.running = False
        
        # Wait for threads to stop
        if self.message_thread:
            self.message_thread.join(timeout=2.0)
        
        if self.task_thread:
            self.task_thread.join(timeout=2.0)
        
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2.0)
        
        # Save stats
        self._save_stats()
        
        # Save subscriptions
        self._save_subscriptions()
        
        self.logger.info("Stopped agent orchestrator")
    
    def _message_processor(self) -> None:
        """Message processing thread."""
        while self.running:
            try:
                # Get message from queue (with timeout to allow checking self.running)
                try:
                    priority, message_id = self.message_queue.get(timeout=1.0)
                    
                    # Get message
                    message = self.message_store.get(message_id)
                    
                    if message:
                        # Process message
                        self._process_message(message)
                        
                        # Update stats
                        self.stats['messages_processed'] += 1
                        
                        # Save stats periodically
                        if self.stats['messages_processed'] % 100 == 0:
                            self._save_stats()
                    
                    # Mark as done
                    self.message_queue.task_done()
                
                except Exception:
                    # Timeout or empty queue, continue
                    pass
            
            except Exception as e:
                self.logger.error(f"Error in message processor: {e}")
    
    def _task_processor(self) -> None:
        """Task processing thread."""
        while self.running:
            try:
                # Get task from queue (with timeout to allow checking self.running)
                try:
                    priority, created_at, task_id = self.task_queue.get(timeout=1.0)
                    
                    # Get task
                    task = self.active_tasks.get(task_id)
                    
                    if task and task.status == TaskStatus.PENDING:
                        # Assign task to agent
                        self._assign_task(task)
                    
                    # Mark as done
                    self.task_queue.task_done()
                
                except Exception:
                    # Timeout or empty queue, continue
                    pass
            
            except Exception as e:
                self.logger.error(f"Error in task processor: {e}")
    
    def _heartbeat_monitor(self) -> None:
        """Heartbeat monitoring thread."""
        while self.running:
            try:
                # Check agent heartbeats
                current_time = time.time()
                
                for agent_id, agent_info in list(self.agents.items()):
                    # Skip offline agents
                    if agent_info.status == AgentStatus.OFFLINE:
                        continue
                    
                    # Check if heartbeat is overdue (30 seconds)
                    if current_time - agent_info.last_heartbeat > 30:
                        # Mark agent as offline
                        agent_info.status = AgentStatus.OFFLINE
                        
                        # Save agent info
                        self._save_agent_info(agent_info)
                        
                        self.logger.warning(f"Agent {agent_info.name} (ID: {agent_id}) is offline due to missed heartbeats")
                
                # Sleep for a bit
                time.sleep(5.0)
            
            except Exception as e:
                self.logger.error(f"Error in heartbeat monitor: {e}")
    
    def _process_message(self, message: Message) -> None:
        """
        Process a message.
        
        Args:
            message: Message to process
        """
        # Check recipients
        for recipient_id in message.recipients:
            if recipient_id in self.agents:
                # Queue message for agent
                self._queue_message_for_agent(message, recipient_id)
            else:
                self.logger.warning(f"Message recipient {recipient_id} not found")
        
        # Also deliver to subscribers if broadcast
        if message.message_type == MessageType.BROADCAST:
            for subscriber_id in self.subscriptions.get(message.sender, set()):
                if subscriber_id not in message.recipients:
                    # Queue message for subscriber
                    self._queue_message_for_agent(message, subscriber_id)
    
    def _queue_message_for_agent(self, message: Message, agent_id: str) -> None:
        """
        Queue a message for delivery to an agent.
        
        Args:
            message: Message to queue
            agent_id: ID of the recipient agent
        """
        # In a real implementation, this would queue the message
        # for delivery to the agent, possibly via a message broker
        # or agent-specific queue.
        
        # For this simplified implementation, we just log it
        self.logger.info(f"Queued message {message.id} for agent {agent_id}")
    
    def _assign_task(self, task: Task) -> None:
        """
        Assign a task to an agent.
        
        Args:
            task: Task to assign
        """
        # Find a suitable agent for the task
        assigned_agent_id = self._find_agent_for_task(task)
        
        if assigned_agent_id:
            # Update task
            task.status = TaskStatus.ASSIGNED
            task.assigned_to = assigned_agent_id
            
            # Save task
            self._save_task(task)
            
            # Update agent info
            agent_info = self.agents[assigned_agent_id]
            agent_info.current_tasks.append(task.id)
            
            # Save agent info
            self._save_agent_info(agent_info)
            
            # Notify agent of the task assignment
            self._send_task_assignment_message(task, assigned_agent_id)
            
            self.logger.info(f"Assigned task {task.id} to agent {assigned_agent_id}")
        else:
            # No suitable agent found, return task to queue with lower priority
            new_priority = min(task.priority + 1, 3)  # Increase priority (lower urgency)
            self.task_queue.put((new_priority, time.time(), task.id))
            
            self.logger.warning(f"No suitable agent found for task {task.id}, requeued with priority {new_priority}")
    
    def _find_agent_for_task(self, task: Task) -> Optional[str]:
        """
        Find a suitable agent for a task.
        
        Args:
            task: Task to assign
            
        Returns:
            ID of the selected agent or None if no suitable agent found
        """
        suitable_agents = []
        
        # Find agents with required capabilities
        required_capability = task.task_type
        
        for agent_id, agent_info in self.agents.items():
            # Skip offline, initializing, or error agents
            if agent_info.status in [AgentStatus.OFFLINE, AgentStatus.INITIALIZING, AgentStatus.ERROR]:
                continue
            
            # Check if agent has the required capability
            if required_capability in agent_info.capabilities:
                # Agent is suitable
                suitable_agents.append((agent_id, agent_info))
        
        if not suitable_agents:
            return None
        
        # Select the most suitable agent
        # For now, use a simple selection: least busy agent
        suitable_agents.sort(key=lambda a: len(a[1].current_tasks))
        
        return suitable_agents[0][0]
    
    def _send_task_assignment_message(self, task: Task, agent_id: str) -> None:
        """
        Send a message to an agent about a task assignment.
        
        Args:
            task: Assigned task
            agent_id: ID of the assigned agent
        """
        # Create message
        message_id = str(uuid.uuid4())
        
        message = Message(
            message_id=message_id,
            sender="orchestrator",
            recipients=[agent_id],
            message_type=MessageType.REQUEST,
            content={
                'action': 'task_assignment',
                'task_id': task.id,
                'task_type': task.task_type,
                'parameters': task.parameters
            },
            priority=MessagePriority.HIGH
        )
        
        # Store message
        self.message_store[message_id] = message
        
        # Save message
        self._save_message(message)
        
        # Queue message
        self.message_queue.put((message.priority.value, message_id))
    
    def register_agent(self, agent_id: str, agent_type: Union[str, AgentType],
                    name: str, capabilities: List[str],
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Register an agent with the orchestrator.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of the agent
            name: Human-readable name for the agent
            capabilities: List of capabilities the agent provides
            metadata: Optional agent metadata
            
        Returns:
            Registration success
        """
        # Convert agent_type from string if needed
        if isinstance(agent_type, str):
            agent_type = AgentType(agent_type)
        
        # Create agent info
        agent_info = AgentInfo(
            agent_id=agent_id,
            agent_type=agent_type,
            name=name,
            capabilities=capabilities,
            metadata=metadata
        )
        
        # Set initial status
        agent_info.status = AgentStatus.INITIALIZING
        
        # Store agent info
        self.agents[agent_id] = agent_info
        
        # Save agent info
        self._save_agent_info(agent_info)
        
        self.logger.info(f"Registered agent: {name} (ID: {agent_id})")
        return True
    
    def update_agent_status(self, agent_id: str, status: Union[str, AgentStatus],
                         current_tasks: Optional[List[str]] = None) -> bool:
        """
        Update an agent's status.
        
        Args:
            agent_id: ID of the agent
            status: New status
            current_tasks: Optional list of current task IDs
            
        Returns:
            Update success
        """
        if agent_id not in self.agents:
            return False
        
        # Convert status from string if needed
        if isinstance(status, str):
            status = AgentStatus(status)
        
        # Update agent info
        agent_info = self.agents[agent_id]
        agent_info.status = status
        agent_info.last_heartbeat = time.time()
        
        if current_tasks is not None:
            agent_info.current_tasks = current_tasks
        
        # Save agent info
        self._save_agent_info(agent_info)
        
        # Update stats
        self.stats['agent_heartbeats'] += 1
        
        return True
    
    def send_message(self, sender: str, recipients: List[str],
                   message_type: Union[str, MessageType],
                   content: Dict[str, Any],
                   priority: Union[int, MessagePriority] = MessagePriority.MEDIUM,
                   conversation_id: Optional[str] = None,
                   in_reply_to: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Send a message.
        
        Args:
            sender: ID of the sending agent
            recipients: List of recipient agent IDs
            message_type: Type of message
            content: Message content
            priority: Message priority
            conversation_id: Optional ID of the conversation
            in_reply_to: Optional ID of the message this is a reply to
            metadata: Optional message metadata
            
        Returns:
            Message ID or None if sender not found
        """
        if sender != "orchestrator" and sender not in self.agents:
            return None
        
        # Convert message_type from string if needed
        if isinstance(message_type, str):
            message_type = MessageType(message_type)
        
        # Convert priority from int if needed
        if isinstance(priority, int):
            for p in MessagePriority:
                if p.value == priority:
                    priority = p
                    break
            else:
                priority = MessagePriority.MEDIUM
        
        # Create message
        message_id = str(uuid.uuid4())
        
        message = Message(
            message_id=message_id,
            sender=sender,
            recipients=recipients,
            message_type=message_type,
            content=content,
            priority=priority,
            conversation_id=conversation_id,
            in_reply_to=in_reply_to,
            metadata=metadata
        )
        
        # Store message
        self.message_store[message_id] = message
        
        # Save message
        self._save_message(message)
        
        # Queue message
        self.message_queue.put((message.priority.value, message_id))
        
        self.logger.info(f"Queued message from {sender} to {', '.join(recipients)}")
        return message_id
    
    def subscribe_to_agent(self, subscriber_id: str, publisher_id: str) -> bool:
        """
        Subscribe an agent to another agent's broadcasts.
        
        Args:
            subscriber_id: ID of the subscribing agent
            publisher_id: ID of the publishing agent
            
        Returns:
            Subscription success
        """
        if subscriber_id not in self.agents or publisher_id not in self.agents:
            return False
        
        # Initialize subscription set if needed
        if publisher_id not in self.subscriptions:
            self.subscriptions[publisher_id] = set()
        
        # Add subscription
        self.subscriptions[publisher_id].add(subscriber_id)
        
        # Save subscriptions
        self._save_subscriptions()
        
        self.logger.info(f"Agent {subscriber_id} subscribed to broadcasts from {publisher_id}")
        return True
    
    def unsubscribe_from_agent(self, subscriber_id: str, publisher_id: str) -> bool:
        """
        Unsubscribe an agent from another agent's broadcasts.
        
        Args:
            subscriber_id: ID of the subscribing agent
            publisher_id: ID of the publishing agent
            
        Returns:
            Unsubscription success
        """
        if publisher_id not in self.subscriptions:
            return False
        
        # Remove subscription
        self.subscriptions[publisher_id].discard(subscriber_id)
        
        # Save subscriptions
        self._save_subscriptions()
        
        self.logger.info(f"Agent {subscriber_id} unsubscribed from broadcasts from {publisher_id}")
        return True
    
    def get_subscriptions(self, agent_id: str) -> List[str]:
        """
        Get the IDs of agents subscribed to an agent's broadcasts.
        
        Args:
            agent_id: ID of the publishing agent
            
        Returns:
            List of subscriber agent IDs
        """
        return list(self.subscriptions.get(agent_id, set()))
    
    def create_task(self, task_type: str, requester: str,
                 parameters: Dict[str, Any],
                 priority: int = 2,
                 deadline: Optional[float] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new task.
        
        Args:
            task_type: Type of task
            requester: ID of the agent or system requesting the task
            parameters: Task parameters
            priority: Task priority (1=high, 3=low)
            deadline: Optional deadline timestamp
            metadata: Optional task metadata
            
        Returns:
            Task ID
        """
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Create task
        task = Task(
            task_id=task_id,
            task_type=task_type,
            requester=requester,
            parameters=parameters,
            priority=priority,
            deadline=deadline,
            metadata=metadata
        )
        
        # Store task
        self.active_tasks[task_id] = task
        
        # Save task
        self._save_task(task)
        
        # Queue task
        self.task_queue.put((priority, time.time(), task_id))
        
        self.logger.info(f"Created task: {task_id} ({task_type})")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task or None if not found
        """
        return self.active_tasks.get(task_id)
    
    def update_task_status(self, task_id: str, status: Union[str, TaskStatus],
                        result: Optional[Dict[str, Any]] = None,
                        error: Optional[str] = None) -> bool:
        """
        Update a task's status.
        
        Args:
            task_id: ID of the task
            status: New status
            result: Optional task result
            error: Optional error message
            
        Returns:
            Update success
        """
        if task_id not in self.active_tasks:
            return False
        
        # Convert status from string if needed
        if isinstance(status, str):
            status = TaskStatus(status)
        
        # Update task
        task = self.active_tasks[task_id]
        
        # Update status
        task.status = status
        
        # Update result or error if provided
        if result is not None:
            task.result = result
        
        if error is not None:
            task.error = error
        
        # Update timestamps
        if status == TaskStatus.IN_PROGRESS and task.started_at is None:
            task.started_at = time.time()
        
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED] and task.completed_at is None:
            task.completed_at = time.time()
        
        # Save task
        self._save_task(task)
        
        # Update agent info if assigned
        if task.assigned_to and task.assigned_to in self.agents:
            agent_info = self.agents[task.assigned_to]
            
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED]:
                # Remove from current tasks
                if task_id in agent_info.current_tasks:
                    agent_info.current_tasks.remove(task_id)
                
                # Save agent info
                self._save_agent_info(agent_info)
        
        # Update stats
        if status == TaskStatus.COMPLETED:
            self.stats['tasks_completed'] += 1
        elif status == TaskStatus.FAILED:
            self.stats['tasks_failed'] += 1
        
        # Notify requester of task completion or failure
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            self._send_task_completion_message(task)
        
        return True
    
    def _send_task_completion_message(self, task: Task) -> None:
        """
        Send a message to the requester about task completion.
        
        Args:
            task: Completed task
        """
        # Skip if requester is 'orchestrator'
        if task.requester == "orchestrator":
            return
        
        # Create message
        message_id = str(uuid.uuid4())
        
        message = Message(
            message_id=message_id,
            sender="orchestrator",
            recipients=[task.requester],
            message_type=MessageType.RESPONSE,
            content={
                'action': 'task_completion',
                'task_id': task.id,
                'task_type': task.task_type,
                'status': task.status.value,
                'result': task.result,
                'error': task.error
            },
            priority=MessagePriority.HIGH
        )
        
        # Store message
        self.message_store[message_id] = message
        
        # Save message
        self._save_message(message)
        
        # Queue message
        self.message_queue.put((message.priority.value, message_id))
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Agent info dictionary or None if not found
        """
        if agent_id not in self.agents:
            return None
        
        return self.agents[agent_id].to_dict()
    
    def list_agents(self, agent_type: Optional[Union[str, AgentType]] = None,
                 status: Optional[Union[str, AgentStatus]] = None) -> List[Dict[str, Any]]:
        """
        List agents in the system.
        
        Args:
            agent_type: Optional filter by agent type
            status: Optional filter by status
            
        Returns:
            List of agent info dictionaries
        """
        # Convert filters from strings if needed
        if isinstance(agent_type, str):
            agent_type = AgentType(agent_type)
        
        if isinstance(status, str):
            status = AgentStatus(status)
        
        # Apply filters
        result = []
        
        for agent_info in self.agents.values():
            # Apply agent type filter
            if agent_type and agent_info.agent_type != agent_type:
                continue
            
            # Apply status filter
            if status and agent_info.status != status:
                continue
            
            # Add to result
            result.append(agent_info.to_dict())
        
        return result
    
    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a message by ID.
        
        Args:
            message_id: ID of the message
            
        Returns:
            Message dictionary or None if not found
        """
        if message_id not in self.message_store:
            return None
        
        return self.message_store[message_id].to_dict()
    
    def get_agent_messages(self, agent_id: str, 
                        as_sender: bool = True, 
                        as_recipient: bool = True,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get messages involving an agent.
        
        Args:
            agent_id: ID of the agent
            as_sender: Whether to include messages sent by the agent
            as_recipient: Whether to include messages received by the agent
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        result = []
        
        for message in self.message_store.values():
            if as_sender and message.sender == agent_id:
                result.append(message.to_dict())
            elif as_recipient and agent_id in message.recipients:
                result.append(message.to_dict())
            
            if len(result) >= limit:
                break
        
        # Sort by timestamp (newest first)
        result.sort(key=lambda m: m['timestamp'], reverse=True)
        
        return result[:limit]
    
    def get_conversation(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages in a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            List of message dictionaries
        """
        result = []
        
        for message in self.message_store.values():
            if message.conversation_id == conversation_id:
                result.append(message.to_dict())
        
        # Sort by timestamp
        result.sort(key=lambda m: m['timestamp'])
        
        return result
    
    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """
        Get statistics for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Statistics dictionary
        """
        if agent_id not in self.agents:
            return {'error': 'Agent not found'}
        
        agent_info = self.agents[agent_id]
        
        # Count messages sent and received
        messages_sent = 0
        messages_received = 0
        
        for message in self.message_store.values():
            if message.sender == agent_id:
                messages_sent += 1
            
            if agent_id in message.recipients:
                messages_received += 1
        
        # Count tasks assigned, completed, and failed
        tasks_assigned = 0
        tasks_completed = 0
        tasks_failed = 0
        
        for task in self.active_tasks.values():
            if task.assigned_to == agent_id:
                tasks_assigned += 1
                
                if task.status == TaskStatus.COMPLETED:
                    tasks_completed += 1
                elif task.status == TaskStatus.FAILED:
                    tasks_failed += 1
        
        # Calculate success rate
        success_rate = tasks_completed / tasks_assigned if tasks_assigned > 0 else 0
        
        return {
            'agent_id': agent_id,
            'name': agent_info.name,
            'type': agent_info.agent_type.value,
            'status': agent_info.status.value,
            'capabilities': agent_info.capabilities,
            'current_tasks': len(agent_info.current_tasks),
            'messages_sent': messages_sent,
            'messages_received': messages_received,
            'tasks_assigned': tasks_assigned,
            'tasks_completed': tasks_completed,
            'tasks_failed': tasks_failed,
            'success_rate': success_rate
        }
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """
        Get statistics for the orchestrator.
        
        Returns:
            Statistics dictionary
        """
        # Count agents by type and status
        agents_by_type = {}
        agents_by_status = {}
        
        for agent_info in self.agents.values():
            agent_type = agent_info.agent_type.value
            agents_by_type[agent_type] = agents_by_type.get(agent_type, 0) + 1
            
            agent_status = agent_info.status.value
            agents_by_status[agent_status] = agents_by_status.get(agent_status, 0) + 1
        
        # Count active tasks by status
        tasks_by_status = {}
        
        for task in self.active_tasks.values():
            task_status = task.status.value
            tasks_by_status[task_status] = tasks_by_status.get(task_status, 0) + 1
        
        # Count messages by type
        messages_by_type = {}
        
        for message in self.message_store.values():
            message_type = message.message_type.value
            messages_by_type[message_type] = messages_by_type.get(message_type, 0) + 1
        
        return {
            'agent_count': len(self.agents),
            'agents_by_type': agents_by_type,
            'agents_by_status': agents_by_status,
            'active_task_count': len(self.active_tasks),
            'tasks_by_status': tasks_by_status,
            'message_count': len(self.message_store),
            'messages_by_type': messages_by_type,
            'messages_processed': self.stats.get('messages_processed', 0),
            'tasks_completed': self.stats.get('tasks_completed', 0),
            'tasks_failed': self.stats.get('tasks_failed', 0),
            'agent_heartbeats': self.stats.get('agent_heartbeats', 0)
        }
    
    def broadcast_message(self, sender: str, message_type: Union[str, MessageType],
                      content: Dict[str, Any],
                      target_type: Optional[Union[str, AgentType]] = None,
                      priority: Union[int, MessagePriority] = MessagePriority.MEDIUM,
                      metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Broadcast a message to all agents or agents of a specific type.
        
        Args:
            sender: ID of the sending agent
            message_type: Type of message
            content: Message content
            target_type: Optional agent type to target
            priority: Message priority
            metadata: Optional message metadata
            
        Returns:
            Message ID or None if sender not found
        """
        if sender != "orchestrator" and sender not in self.agents:
            return None
        
        # Convert message_type from string if needed
        if isinstance(message_type, str):
            message_type = MessageType(message_type)
        
        # Force message type to BROADCAST
        message_type = MessageType.BROADCAST
        
        # Convert target_type from string if needed
        if isinstance(target_type, str):
            target_type = AgentType(target_type)
        
        # Get recipients
        recipients = []
        
        for agent_id, agent_info in self.agents.items():
            # Skip the sender
            if agent_id == sender:
                continue
            
            # Apply target_type filter
            if target_type and agent_info.agent_type != target_type:
                continue
            
            # Add to recipients
            recipients.append(agent_id)
        
        # Send message if there are recipients
        if recipients:
            return self.send_message(
                sender=sender,
                recipients=recipients,
                message_type=message_type,
                content=content,
                priority=priority,
                metadata=metadata
            )
        
        return None