"""
Enhanced Agent Base Module for TerraFlow Platform

This module provides the enhanced base class for all specialized AI agents
in the TerraFlow platform. It implements the improved agent communication 
protocol, task management, and operational capabilities.
"""

import json
import time
import uuid
import logging
import threading
import queue
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Set
from abc import ABC, abstractmethod

from infrastructure.architecture.agent_communication_protocol import (
    Message, MessageType, MessagePriority, MessageMetadata,
    create_request_message, create_response_message, create_broadcast_message,
    create_alert_message, create_heartbeat_message, create_capability_discovery_message
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentState(Enum):
    """Possible states for an agent"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    LEARNING = "learning"
    OFFLINE = "offline"

class AgentCategory(Enum):
    """Categories of agents in the system"""
    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    DATABASE = "database"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTING = "testing"
    AGENT_READINESS = "agent_readiness"
    LEARNING_COORDINATOR = "learning_coordinator"
    AI_INTEGRATION = "ai_integration"
    WORKFLOW_AUTOMATION = "workflow_automation"

class Task:
    """
    Task assigned to an agent.
    
    This class represents a task that can be assigned to and executed by an agent.
    """
    def __init__(self,
               task_id: str,
               agent_id: str,
               capability: str,
               parameters: Dict[str, Any],
               priority: str = "medium",
               deadline: Optional[float] = None,
               created_at: Optional[float] = None):
        """
        Initialize a new task.
        
        Args:
            task_id: Unique identifier for this task
            agent_id: ID of the agent assigned to this task
            capability: Capability required for this task
            parameters: Task parameters
            priority: Task priority
            deadline: Optional deadline for task completion
            created_at: Optional task creation timestamp
        """
        self.task_id = task_id
        self.agent_id = agent_id
        self.capability = capability
        self.parameters = parameters
        self.priority = priority
        self.deadline = deadline
        self.created_at = created_at or time.time()
        self.started_at = None
        self.completed_at = None
        self.status = "pending"
        self.result = None
        self.error = None
    
    def start(self):
        """Mark the task as started"""
        self.started_at = time.time()
        self.status = "running"
    
    def complete(self, result: Dict[str, Any]):
        """Mark the task as completed successfully"""
        self.completed_at = time.time()
        self.status = "completed"
        self.result = result
    
    def fail(self, error: str):
        """Mark the task as failed"""
        self.completed_at = time.time()
        self.status = "failed"
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the task to a dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "capability": self.capability,
            "parameters": self.parameters,
            "priority": self.priority,
            "deadline": self.deadline,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "result": self.result,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create a task from a dictionary"""
        task = cls(
            task_id=data["task_id"],
            agent_id=data["agent_id"],
            capability=data["capability"],
            parameters=data["parameters"],
            priority=data.get("priority", "medium"),
            deadline=data.get("deadline"),
            created_at=data.get("created_at")
        )
        
        task.started_at = data.get("started_at")
        task.completed_at = data.get("completed_at")
        task.status = data.get("status", "pending")
        task.result = data.get("result")
        task.error = data.get("error")
        
        return task

class EnhancedAgent(ABC):
    """
    Enhanced base class for all agents in the TerraFlow platform.
    
    This class implements the improved agent communication protocol,
    task management, and operational capabilities.
    """
    
    def __init__(self,
                 agent_id: str,
                 agent_type: AgentCategory,
                 capabilities: List[str],
                 preferred_model: Optional[str] = None,
                 message_broker=None):
        """
        Initialize a new agent.
        
        Args:
            agent_id: Unique identifier for this agent
            agent_type: Category this agent belongs to
            capabilities: List of capabilities this agent provides
            preferred_model: Optional preferred AI model to use
            message_broker: Message broker for agent communication
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.preferred_model = preferred_model
        self.message_broker = message_broker
        
        # Agent state
        self.state = AgentState.INITIALIZING
        self.last_heartbeat = time.time()
        self.last_status_update = time.time()
        
        # Task management
        self.task_queue = queue.PriorityQueue()
        self.current_tasks = {}  # task_id -> Task
        self.completed_tasks = {}  # task_id -> Task
        self.max_concurrent_tasks = self._get_max_concurrent_tasks()
        
        # Threading
        self.worker_thread = None
        self.message_handler_thread = None
        self.heartbeat_thread = None
        self.running = False
        
        # Message tracking
        self.pending_responses = {}  # request_id -> callback
        self.message_callbacks = {}  # message_type -> List[callback]
        
        # Learning
        self.learning_updates = {}  # update_id -> update_data
        
        # Register message callbacks
        self._register_message_callbacks()
    
    def _register_message_callbacks(self):
        """Register callbacks for different message types"""
        self.register_message_callback(MessageType.REQUEST, self._handle_request)
        self.register_message_callback(MessageType.RESPONSE, self._handle_response)
        self.register_message_callback(MessageType.BROADCAST, self._handle_broadcast)
        self.register_message_callback(MessageType.ALERT, self._handle_alert)
        self.register_message_callback(MessageType.LEARNING_UPDATE, self._handle_learning_update)
        self.register_message_callback(MessageType.CAPABILITY_DISCOVERY, self._handle_capability_discovery)
    
    def register_message_callback(self, message_type: MessageType, callback: Callable[[Message], None]):
        """
        Register a callback for a specific message type
        
        Args:
            message_type: The type of message to handle
            callback: The callback function to invoke
        """
        if message_type not in self.message_callbacks:
            self.message_callbacks[message_type] = []
        
        self.message_callbacks[message_type].append(callback)
    
    def start(self):
        """Start the agent's processing threads"""
        if self.running:
            logger.warning(f"Agent {self.agent_id} is already running")
            return
        
        self.running = True
        
        # Start worker thread
        self.worker_thread = threading.Thread(target=self._worker_loop)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
        # Start message handler thread
        self.message_handler_thread = threading.Thread(target=self._message_handler_loop)
        self.message_handler_thread.daemon = True
        self.message_handler_thread.start()
        
        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        
        # Subscribe to messages
        if self.message_broker:
            self.message_broker.subscribe(self.agent_id, self._process_message)
        
        # Update state
        self._update_state(AgentState.IDLE)
        
        # Send capability discovery
        self._send_capability_discovery()
        
        logger.info(f"Agent {self.agent_id} started")
    
    def stop(self):
        """Stop the agent's processing threads"""
        if not self.running:
            logger.warning(f"Agent {self.agent_id} is not running")
            return
        
        self.running = False
        
        # Update state
        self._update_state(AgentState.OFFLINE)
        
        # Unsubscribe from messages
        if self.message_broker:
            self.message_broker.unsubscribe(self.agent_id)
        
        # Wait for threads to terminate
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)
        
        if self.message_handler_thread:
            self.message_handler_thread.join(timeout=2.0)
        
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2.0)
        
        logger.info(f"Agent {self.agent_id} stopped")
    
    def _update_state(self, new_state: AgentState):
        """Update the agent's state and notify the server"""
        self.state = new_state
        self._send_status_update()
    
    def _send_status_update(self):
        """Send a status update to the server"""
        if not self.message_broker:
            return
        
        self.last_status_update = time.time()
        
        # Create status update message
        content = {
            "state": self.state.value,
            "capabilities": self.capabilities,
            "current_tasks": len(self.current_tasks),
            "completed_tasks": len(self.completed_tasks),
            "timestamp": time.time()
        }
        
        # Send as a status update message
        message = create_broadcast_message(
            sender_id=self.agent_id,
            recipients=["controller"],  # Send to controller
            content=content,
            priority=MessagePriority.LOW
        )
        
        self.message_broker.publish(message)
    
    def _send_heartbeat(self):
        """Send a heartbeat to the server to indicate the agent is still alive"""
        if not self.message_broker:
            return
        
        self.last_heartbeat = time.time()
        
        # Create heartbeat message
        metrics = {
            "memory_usage": 0,  # In a real implementation, this would be actual memory usage
            "cpu_usage": 0,  # In a real implementation, this would be actual CPU usage
            "task_queue_size": self.task_queue.qsize(),
            "current_tasks": len(self.current_tasks)
        }
        
        message = create_heartbeat_message(
            sender_id=self.agent_id,
            recipients=["controller"],  # Send to controller
            status=self.state.value,
            metrics=metrics
        )
        
        self.message_broker.publish(message)
    
    def _send_capability_discovery(self):
        """Send capability discovery message to inform about agent capabilities"""
        if not self.message_broker:
            return
        
        # Create capability details
        details = {
            "agent_type": self.agent_type.value,
            "preferred_model": self.preferred_model,
            "max_concurrent_tasks": self.max_concurrent_tasks
        }
        
        # Create capability discovery message
        message = create_capability_discovery_message(
            sender_id=self.agent_id,
            recipients=["controller"],  # Send to controller
            capabilities=self.capabilities,
            details=details
        )
        
        self.message_broker.publish(message)
    
    def _worker_loop(self):
        """Main worker loop that processes the agent's tasks"""
        while self.running:
            try:
                # If we're already processing the maximum number of tasks, wait
                if len(self.current_tasks) >= self.max_concurrent_tasks:
                    time.sleep(0.1)
                    continue
                
                # Get next task from queue
                try:
                    # Use get_nowait() to avoid blocking
                    priority, task_id = self.task_queue.get_nowait()
                    
                    # Skip if task is already completed or being processed
                    if task_id in self.current_tasks or task_id in self.completed_tasks:
                        self.task_queue.task_done()
                        continue
                    
                    # Process task
                    self._process_task(task_id)
                    
                except queue.Empty:
                    # No tasks in queue
                    if self.state == AgentState.BUSY and not self.current_tasks:
                        # If we were busy but now have no tasks, go back to idle
                        self._update_state(AgentState.IDLE)
                    
                    time.sleep(0.1)
            
            except Exception as e:
                logger.exception(f"Error in worker loop: {str(e)}")
                time.sleep(1.0)  # Sleep to avoid tight error loop
    
    def _message_handler_loop(self):
        """Loop for processing incoming messages"""
        # This loop is no longer needed with the message broker handling delivery
        # The message broker will call _process_message directly
        pass
    
    def _heartbeat_loop(self):
        """Loop for sending periodic heartbeats"""
        heartbeat_interval = 10.0  # seconds
        status_update_interval = 30.0  # seconds
        
        while self.running:
            try:
                current_time = time.time()
                
                # Send heartbeat if due
                if current_time - self.last_heartbeat >= heartbeat_interval:
                    self._send_heartbeat()
                
                # Send status update if due
                if current_time - self.last_status_update >= status_update_interval:
                    self._send_status_update()
                
                # Sleep for a short interval
                time.sleep(1.0)
                
            except Exception as e:
                logger.exception(f"Error in heartbeat loop: {str(e)}")
                time.sleep(5.0)  # Sleep longer on error
    
    def _process_message(self, message: Message):
        """
        Process an incoming message
        
        Args:
            message: The message to process
        """
        try:
            message_type = message.message_type
            
            # Check if we have callbacks for this message type
            if message_type in self.message_callbacks:
                for callback in self.message_callbacks[message_type]:
                    try:
                        callback(message)
                    except Exception as e:
                        logger.exception(f"Error in message callback: {str(e)}")
            else:
                logger.warning(f"No callback registered for message type {message_type}")
            
            # Confirm delivery
            if self.message_broker:
                self.message_broker.confirm_delivery(message.message_id, self.agent_id)
                
        except Exception as e:
            logger.exception(f"Error processing message: {str(e)}")
    
    def _handle_request(self, message: Message):
        """
        Handle a request message
        
        Args:
            message: The request message
        """
        try:
            content = message.content
            
            # Check if this is a task request
            if "task_id" in content and "capability" in content and "parameters" in content:
                # Create task from request
                task_id = content["task_id"]
                capability = content["capability"]
                parameters = content["parameters"]
                priority = content.get("priority", "medium")
                deadline = content.get("deadline")
                
                # Check if we support this capability
                if capability not in self.capabilities:
                    # Send response indicating we don't support this capability
                    response_content = {
                        "task_id": task_id,
                        "success": False,
                        "error": f"Agent does not support capability: {capability}"
                    }
                    
                    response = create_response_message(
                        sender_id=self.agent_id,
                        recipients=[message.sender_id],
                        request_id=message.message_id,
                        content=response_content
                    )
                    
                    self.message_broker.publish(response)
                    return
                
                # Create task
                task = Task(
                    task_id=task_id,
                    agent_id=self.agent_id,
                    capability=capability,
                    parameters=parameters,
                    priority=priority,
                    deadline=deadline
                )
                
                # Add to task queue
                priority_value = {"high": 0, "medium": 1, "low": 2}.get(priority.lower(), 1)
                self.task_queue.put((priority_value, task_id))
                
                # Store task
                self.completed_tasks[task_id] = task
                
                # Send acknowledgment
                response_content = {
                    "task_id": task_id,
                    "success": True,
                    "message": "Task accepted"
                }
                
                response = create_response_message(
                    sender_id=self.agent_id,
                    recipients=[message.sender_id],
                    request_id=message.message_id,
                    content=response_content
                )
                
                self.message_broker.publish(response)
                
                logger.info(f"Accepted task {task_id} for capability {capability}")
            
            else:
                # Handle other types of requests
                handler_method = f"_handle_{message.content.get('action', 'unknown')}_request"
                
                if hasattr(self, handler_method):
                    getattr(self, handler_method)(message)
                else:
                    # Send response indicating unknown request
                    response_content = {
                        "success": False,
                        "error": "Unknown request type"
                    }
                    
                    response = create_response_message(
                        sender_id=self.agent_id,
                        recipients=[message.sender_id],
                        request_id=message.message_id,
                        content=response_content
                    )
                    
                    self.message_broker.publish(response)
        
        except Exception as e:
            logger.exception(f"Error handling request: {str(e)}")
            
            # Send error response
            response_content = {
                "success": False,
                "error": f"Error processing request: {str(e)}"
            }
            
            response = create_response_message(
                sender_id=self.agent_id,
                recipients=[message.sender_id],
                request_id=message.message_id,
                content=response_content
            )
            
            self.message_broker.publish(response)
    
    def _handle_response(self, message: Message):
        """
        Handle a response message
        
        Args:
            message: The response message
        """
        try:
            # Get the request ID from the content
            request_id = message.content.get("request_id")
            
            if not request_id:
                logger.warning(f"Response message missing request_id: {message.message_id}")
                return
            
            # Check if we have a pending response callback for this request
            if request_id in self.pending_responses:
                # Call the callback
                callback = self.pending_responses[request_id]
                callback(message.content)
                
                # Remove from pending responses
                del self.pending_responses[request_id]
            else:
                logger.warning(f"No pending response callback for request {request_id}")
        
        except Exception as e:
            logger.exception(f"Error handling response: {str(e)}")
    
    def _handle_broadcast(self, message: Message):
        """
        Handle a broadcast message
        
        Args:
            message: The broadcast message
        """
        try:
            # Check if there's an action field
            action = message.content.get("action")
            
            if action:
                # Try to call a handler method for this action
                handler_method = f"_handle_{action}_broadcast"
                
                if hasattr(self, handler_method):
                    getattr(self, handler_method)(message)
                else:
                    logger.debug(f"No handler for broadcast action: {action}")
            else:
                logger.debug(f"Broadcast message has no action: {message.message_id}")
        
        except Exception as e:
            logger.exception(f"Error handling broadcast: {str(e)}")
    
    def _handle_alert(self, message: Message):
        """
        Handle an alert message
        
        Args:
            message: The alert message
        """
        try:
            alert_type = message.content.get("alert_type", "unknown")
            alert_message = message.content.get("alert_message", "")
            
            # Log the alert
            logger.warning(f"Alert received ({alert_type}): {alert_message}")
            
            # Try to call a handler method for this alert type
            handler_method = f"_handle_{alert_type}_alert"
            
            if hasattr(self, handler_method):
                getattr(self, handler_method)(message)
        
        except Exception as e:
            logger.exception(f"Error handling alert: {str(e)}")
    
    def _handle_learning_update(self, message: Message):
        """
        Handle a learning update message
        
        Args:
            message: The learning update message
        """
        try:
            update_id = message.content.get("update_id")
            pattern = message.content.get("pattern")
            capability = message.content.get("capability")
            
            if update_id and pattern and capability:
                # Check if this update is applicable to this agent
                applicable_agent_types = message.content.get("agent_types", [])
                
                if not applicable_agent_types or self.agent_type.value in applicable_agent_types:
                    # Store the learning update
                    self.learning_updates[update_id] = message.content
                    
                    # Apply the learning update
                    self._apply_learning_update(update_id, pattern, capability)
                    
                    logger.info(f"Applied learning update {update_id} for capability {capability}")
            else:
                logger.warning(f"Learning update missing required fields: {message.message_id}")
        
        except Exception as e:
            logger.exception(f"Error handling learning update: {str(e)}")
    
    def _handle_capability_discovery(self, message: Message):
        """
        Handle a capability discovery message
        
        Args:
            message: The capability discovery message
        """
        try:
            # Store agent capabilities for future use
            sender_id = message.sender_id
            capabilities = message.content.get("capabilities", [])
            details = message.content.get("details", {})
            
            logger.info(f"Discovered capabilities for agent {sender_id}: {capabilities}")
            
            # In a real implementation, we would store this information
            # for future use when routing tasks
        
        except Exception as e:
            logger.exception(f"Error handling capability discovery: {str(e)}")
    
    def _process_task(self, task_id: str):
        """
        Process a task from the queue
        
        Args:
            task_id: The ID of the task to process
        """
        if task_id not in self.completed_tasks:
            logger.warning(f"Task {task_id} not found")
            return
        
        # Get task
        task = self.completed_tasks[task_id]
        
        # Move to current tasks
        self.current_tasks[task_id] = task
        del self.completed_tasks[task_id]
        
        # Update state if we were idle
        if self.state == AgentState.IDLE:
            self._update_state(AgentState.BUSY)
        
        # Start task
        task.start()
        
        # Execute task in a separate thread to avoid blocking
        threading.Thread(target=self._execute_task_wrapper, args=(task,)).start()
    
    def _execute_task_wrapper(self, task: Task):
        """
        Wrapper for task execution to handle exceptions
        
        Args:
            task: The task to execute
        """
        try:
            # Execute the task
            result = self._execute_task(task)
            
            # Complete the task
            task.complete(result)
            
            # Send task response
            self._send_task_response(task, result)
            
        except Exception as e:
            logger.exception(f"Error executing task {task.task_id}: {str(e)}")
            
            # Fail the task
            error_message = f"Error executing task: {str(e)}"
            task.fail(error_message)
            
            # Send error response
            self._send_task_error(task, error_message)
        
        finally:
            # Remove from current tasks
            if task.task_id in self.current_tasks:
                del self.current_tasks[task.task_id]
            
            # Add to completed tasks
            self.completed_tasks[task.task_id] = task
            
            # Mark task as done in queue
            self.task_queue.task_done()
            
            # Update state if no more current tasks
            if not self.current_tasks and self.state == AgentState.BUSY:
                self._update_state(AgentState.IDLE)
    
    def _send_task_response(self, task: Task, result: Dict[str, Any]):
        """
        Send a response message for a completed task
        
        Args:
            task: The completed task
            result: The task result
        """
        if not self.message_broker:
            return
        
        # Create response content
        content = {
            "task_id": task.task_id,
            "success": True,
            "result": result,
            "execution_time": task.completed_at - task.started_at if task.started_at and task.completed_at else None
        }
        
        # Send to task requester - in a real implementation, we would know who requested the task
        # For now, we broadcast to the controller
        message = create_broadcast_message(
            sender_id=self.agent_id,
            recipients=["controller"],
            content=content
        )
        
        self.message_broker.publish(message)
    
    def _send_task_error(self, task: Task, error: str):
        """
        Send an error response message for a failed task
        
        Args:
            task: The failed task
            error: The error message
        """
        if not self.message_broker:
            return
        
        # Create response content
        content = {
            "task_id": task.task_id,
            "success": False,
            "error": error,
            "execution_time": task.completed_at - task.started_at if task.started_at and task.completed_at else None
        }
        
        # Send to task requester - in a real implementation, we would know who requested the task
        # For now, we broadcast to the controller
        message = create_broadcast_message(
            sender_id=self.agent_id,
            recipients=["controller"],
            content=content
        )
        
        self.message_broker.publish(message)
    
    def send_request(self, recipients: List[str], content: Dict[str, Any],
                   callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                   priority: MessagePriority = MessagePriority.MEDIUM):
        """
        Send a request message and optionally register a callback for the response
        
        Args:
            recipients: List of recipient agent IDs
            content: Message content
            callback: Optional callback function for the response
            priority: Message priority
            
        Returns:
            str: The message ID of the request
        """
        if not self.message_broker:
            logger.warning("No message broker available")
            return None
        
        # Create request message
        message = create_request_message(
            sender_id=self.agent_id,
            recipients=recipients,
            content=content,
            priority=priority
        )
        
        # Register callback if provided
        if callback:
            self.pending_responses[message.message_id] = callback
        
        # Send message
        self.message_broker.publish(message)
        
        return message.message_id
    
    def send_broadcast(self, recipients: List[str], content: Dict[str, Any],
                      priority: MessagePriority = MessagePriority.MEDIUM):
        """
        Send a broadcast message
        
        Args:
            recipients: List of recipient agent IDs
            content: Message content
            priority: Message priority
            
        Returns:
            str: The message ID of the broadcast
        """
        if not self.message_broker:
            logger.warning("No message broker available")
            return None
        
        # Create broadcast message
        message = create_broadcast_message(
            sender_id=self.agent_id,
            recipients=recipients,
            content=content,
            priority=priority
        )
        
        # Send message
        self.message_broker.publish(message)
        
        return message.message_id
    
    def send_alert(self, recipients: List[str], alert_type: str, alert_message: str,
                 details: Optional[Dict[str, Any]] = None,
                 priority: MessagePriority = MessagePriority.HIGH):
        """
        Send an alert message
        
        Args:
            recipients: List of recipient agent IDs
            alert_type: Type of alert
            alert_message: Alert message
            details: Additional alert details
            priority: Message priority
            
        Returns:
            str: The message ID of the alert
        """
        if not self.message_broker:
            logger.warning("No message broker available")
            return None
        
        # Create alert message
        message = create_alert_message(
            sender_id=self.agent_id,
            recipients=recipients,
            alert_type=alert_type,
            alert_message=alert_message,
            details=details,
            priority=priority
        )
        
        # Send message
        self.message_broker.publish(message)
        
        return message.message_id
    
    def submit_learning_update(self, pattern: Dict[str, Any], capability: str,
                            effectiveness: float, confidence: float,
                            agent_types: Optional[List[str]] = None):
        """
        Submit a learning update to the learning system
        
        Args:
            pattern: The pattern that was discovered
            capability: The capability this pattern applies to
            effectiveness: Estimated effectiveness (0.0 to 1.0)
            confidence: Confidence in the effectiveness estimate (0.0 to 1.0)
            agent_types: List of agent types this update applies to
            
        Returns:
            str: The update ID
        """
        if not self.message_broker:
            logger.warning("No message broker available")
            return None
        
        # Create update ID
        update_id = str(uuid.uuid4())
        
        # Create content
        content = {
            "update_id": update_id,
            "pattern": pattern,
            "capability": capability,
            "effectiveness": effectiveness,
            "confidence": confidence,
            "agent_types": agent_types,
            "submitted_by": self.agent_id,
            "submitted_at": time.time()
        }
        
        # Create message
        message = Message(
            message_id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            recipients=["learning_coordinator"],
            message_type=MessageType.LEARNING_UPDATE,
            content=content
        )
        
        # Send message
        self.message_broker.publish(message)
        
        return update_id
    
    def _get_max_concurrent_tasks(self) -> int:
        """
        Get the maximum number of concurrent tasks this agent can handle
        
        Returns:
            int: The maximum number of concurrent tasks
        """
        # Default implementation: 1 task at a time
        # Override in subclasses to provide a different value
        return 1
    
    def _apply_learning_update(self, update_id: str, pattern: Dict[str, Any], capability: str):
        """
        Apply a learning update to the agent's behavior
        
        Args:
            update_id: The ID of the update
            pattern: The pattern from the update
            capability: The capability this update applies to
        """
        # Default implementation does nothing
        # Override in subclasses to apply learning updates
        pass
    
    @abstractmethod
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a task assigned to this agent
        
        This method must be implemented by subclasses.
        
        Args:
            task: The task to execute
            
        Returns:
            Dict containing the result of the task execution
        """
        pass


# Specialized agent base classes

class CodeQualityAgent(EnhancedAgent):
    """Base class for code quality analysis agents"""
    
    def __init__(self, agent_id: str, capabilities: List[str], 
                 preferred_model: Optional[str] = None,
                 message_broker=None):
        """Initialize a code quality agent"""
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentCategory.CODE_QUALITY,
            capabilities=capabilities,
            preferred_model=preferred_model,
            message_broker=message_broker
        )
    
    def _get_max_concurrent_tasks(self) -> int:
        """Get the maximum number of concurrent tasks this agent can handle"""
        return 2  # Code quality agents can handle 2 tasks at once
    
    def _apply_learning_update(self, update_id: str, pattern: Dict[str, Any], capability: str):
        """Apply a learning update to the code quality agent"""
        logger.info(f"Applying learning update {update_id} for capability {capability}")
        # In a real implementation, this would update internal models or patterns
    
    @abstractmethod
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a code quality analysis task"""
        pass


class SecurityAgent(EnhancedAgent):
    """Base class for security analysis agents"""
    
    def __init__(self, agent_id: str, capabilities: List[str],
                 preferred_model: Optional[str] = None,
                 message_broker=None):
        """Initialize a security agent"""
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentCategory.SECURITY,
            capabilities=capabilities,
            preferred_model=preferred_model,
            message_broker=message_broker
        )
    
    def _get_max_concurrent_tasks(self) -> int:
        """Get the maximum number of concurrent tasks this agent can handle"""
        return 2  # Security agents can handle 2 tasks at once
    
    @abstractmethod
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a security analysis task"""
        pass


class PerformanceAgent(EnhancedAgent):
    """Base class for performance analysis agents"""
    
    def __init__(self, agent_id: str, capabilities: List[str],
                 preferred_model: Optional[str] = None,
                 message_broker=None):
        """Initialize a performance agent"""
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentCategory.PERFORMANCE,
            capabilities=capabilities,
            preferred_model=preferred_model,
            message_broker=message_broker
        )
    
    def _get_max_concurrent_tasks(self) -> int:
        """Get the maximum number of concurrent tasks this agent can handle"""
        return 3  # Performance agents can handle 3 tasks at once
    
    @abstractmethod
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a performance analysis task"""
        pass


class WorkflowAutomationAgent(EnhancedAgent):
    """Base class for workflow automation agents"""
    
    def __init__(self, agent_id: str, capabilities: List[str],
                 preferred_model: Optional[str] = None,
                 message_broker=None):
        """Initialize a workflow automation agent"""
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentCategory.WORKFLOW_AUTOMATION,
            capabilities=capabilities,
            preferred_model=preferred_model,
            message_broker=message_broker
        )
    
    def _get_max_concurrent_tasks(self) -> int:
        """Get the maximum number of concurrent tasks this agent can handle"""
        return 5  # Workflow automation agents can handle 5 tasks at once
    
    @abstractmethod
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a workflow automation task"""
        pass