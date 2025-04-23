"""
Agent Base Module for Code Deep Dive Analyzer

This module provides the base classes and interfaces for all specialized AI agents
in the system. It handles communication with the protocol server, message processing,
task execution, and continuous learning capabilities.
"""

import os
import json
import time
import uuid
import logging
import threading
import queue
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict

# Import protocol server components
from protocol_server import (
    ProtocolMessage, MessageType, MessagePriority, AgentIdentity, AgentCategory,
    Task, FeedbackRecord, LearningUpdate, ModelConfig, get_server
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Possible states for an agent"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    LEARNING = "learning"
    OFFLINE = "offline"


class Agent(ABC):
    """
    Base class for all agents in the system.
    
    This class handles communication with the protocol server, message processing,
    task execution and tracking, and provides hooks for specialized agent behavior.
    """
    def __init__(self, agent_id: str, agent_type: AgentCategory, capabilities: List[str],
                preferred_model: Optional[str] = None):
        """
        Initialize a new agent.
        
        Args:
            agent_id: Unique identifier for this agent
            agent_type: Category this agent belongs to
            capabilities: List of capabilities this agent provides
            preferred_model: Optional preferred AI model to use
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.preferred_model = preferred_model
        
        # State management
        self.state = AgentState.INITIALIZING
        self._state_lock = threading.Lock()
        
        # Communication
        self.server = get_server()
        self.inbox = queue.Queue()
        self.outbox = queue.Queue()
        
        # Task management
        self.current_tasks: Dict[str, Task] = {}
        self.task_history: Dict[str, Dict[str, Any]] = {}
        
        # Learning system
        self.knowledge_base: Dict[str, Any] = {}
        self.learned_patterns: List[Dict[str, Any]] = []
        
        # Threading
        self._should_stop = threading.Event()
        self._worker_thread = None
        self._message_handler_thread = None
        self._heartbeat_thread = None
    
    def start(self):
        """Start the agent's processing threads"""
        # Register with protocol server
        self._register_with_server()
        
        # Start worker thread
        self._worker_thread = threading.Thread(target=self._worker_loop)
        self._worker_thread.daemon = True
        self._worker_thread.start()
        
        # Start message handler thread
        self._message_handler_thread = threading.Thread(target=self._message_handler_loop)
        self._message_handler_thread.daemon = True
        self._message_handler_thread.start()
        
        # Start heartbeat thread
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self._heartbeat_thread.daemon = True
        self._heartbeat_thread.start()
        
        # Change state to idle
        self._update_state(AgentState.IDLE)
        
        logger.info(f"Agent {self.agent_id} started")
    
    def stop(self):
        """Stop the agent's processing threads"""
        logger.info(f"Stopping agent {self.agent_id}")
        self._should_stop.set()
        
        # Wait for threads to terminate
        if self._worker_thread:
            self._worker_thread.join(timeout=2.0)
        
        if self._message_handler_thread:
            self._message_handler_thread.join(timeout=2.0)
        
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=2.0)
        
        # Change state to offline
        self._update_state(AgentState.OFFLINE)
        
        logger.info(f"Agent {self.agent_id} stopped")
    
    def _register_with_server(self):
        """Register this agent with the protocol server"""
        from protocol_server import AgentConfig
        
        # Create agent configuration
        agent_config = AgentConfig(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            capabilities=self.capabilities,
            preferred_model=self.preferred_model,
            active=True,
            max_concurrent_tasks=self._get_max_concurrent_tasks()
        )
        
        # Register with server
        self.server.register_agent(agent_config)
    
    def _get_max_concurrent_tasks(self) -> int:
        """Get the maximum number of concurrent tasks this agent can handle"""
        # Override this in subclasses if needed
        return 1
    
    def _update_state(self, new_state: AgentState):
        """Update the agent's state and notify the server"""
        with self._state_lock:
            old_state = self.state
            self.state = new_state
            
            # If state has changed, notify server
            if old_state != new_state:
                self._send_status_update()
    
    def _send_status_update(self):
        """Send a status update to the server"""
        identity = AgentIdentity(
            agent_id=self.agent_id,
            agent_type=self.agent_type.value,
            capabilities=self.capabilities,
            status=self.state.value
        )
        
        message = ProtocolMessage(
            sender=identity,
            recipients=["orchestrator"],
            message_type=MessageType.STATUS_UPDATE,
            priority=MessagePriority.LOW,
            content={"status": self.state.value},
            metadata={}
        )
        
        self.server.send_message(message)
    
    def _send_heartbeat(self):
        """Send a heartbeat to the server to indicate the agent is still alive"""
        identity = AgentIdentity(
            agent_id=self.agent_id,
            agent_type=self.agent_type.value,
            capabilities=self.capabilities,
            status=self.state.value
        )
        
        message = ProtocolMessage(
            sender=identity,
            recipients=["orchestrator"],
            message_type=MessageType.STATUS_UPDATE,
            priority=MessagePriority.LOW,
            content={"heartbeat": time.time()},
            metadata={}
        )
        
        self.server.send_message(message)
    
    def _worker_loop(self):
        """Main worker loop that processes the agent's tasks"""
        while not self._should_stop.is_set():
            try:
                # Check for tasks from the protocol server
                self._check_for_new_tasks()
                
                # Process any current tasks
                self._process_current_tasks()
                
                # Sleep briefly to prevent CPU spinning
                time.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Error in worker loop for agent {self.agent_id}: {str(e)}")
                # Sleep longer after an error
                time.sleep(1.0)
    
    def _message_handler_loop(self):
        """Loop for processing incoming messages"""
        while not self._should_stop.is_set():
            try:
                # Check for new messages
                self._check_for_new_messages()
                
                # Process messages in the inbox
                self._process_inbox()
                
                # Send messages in the outbox
                self._process_outbox()
                
                # Sleep briefly to prevent CPU spinning
                time.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Error in message handler loop for agent {self.agent_id}: {str(e)}")
                # Sleep longer after an error
                time.sleep(1.0)
    
    def _heartbeat_loop(self):
        """Loop for sending periodic heartbeats"""
        while not self._should_stop.is_set():
            try:
                # Send heartbeat
                self._send_heartbeat()
                
                # Sleep for a longer period (heartbeats don't need to be frequent)
                time.sleep(30.0)
            
            except Exception as e:
                logger.error(f"Error in heartbeat loop for agent {self.agent_id}: {str(e)}")
                # Sleep shorter after an error to retry sooner
                time.sleep(5.0)
    
    def _check_for_new_messages(self):
        """Check for new messages from the protocol server"""
        # Get next message from the server
        message = self.server.message_broker.get_next_message(self.agent_id)
        
        if message:
            # Add to inbox for processing
            self.inbox.put(message)
    
    def _process_inbox(self):
        """Process messages in the inbox"""
        if self.inbox.empty():
            return
        
        try:
            # Get next message from inbox
            message = self.inbox.get_nowait()
            
            # Process based on message type
            if message.message_type == MessageType.REQUEST:
                self._handle_request(message)
            
            elif message.message_type == MessageType.RESPONSE:
                self._handle_response(message)
            
            elif message.message_type == MessageType.LEARNING_UPDATE:
                self._handle_learning_update(message)
            
            elif message.message_type == MessageType.BROADCAST:
                self._handle_broadcast(message)
            
            elif message.message_type == MessageType.ALERT:
                self._handle_alert(message)
            
            # Mark message as processed
            self.inbox.task_done()
        
        except queue.Empty:
            pass
    
    def _process_outbox(self):
        """Send messages in the outbox to the protocol server"""
        if self.outbox.empty():
            return
        
        try:
            # Get next message from outbox
            message = self.outbox.get_nowait()
            
            # Send to server
            self.server.send_message(message)
            
            # Mark message as sent
            self.outbox.task_done()
        
        except queue.Empty:
            pass
    
    def _handle_request(self, message: ProtocolMessage):
        """Handle request messages"""
        logger.info(f"Agent {self.agent_id} received request: {message.content.get('task_id', 'unknown')}")
        
        # Extract task information
        task_id = message.content.get("task_id")
        if not task_id:
            logger.warning(f"Received request without task_id: {message.message_id}")
            return
        
        # Create task object
        task = Task(
            task_id=task_id,
            conversation_id=message.metadata.get("conversation_id", str(uuid.uuid4())),
            task_type=message.content.get("task_type", ""),
            description=message.content.get("description", ""),
            input_data=message.content.get("input_data", {}),
            assigned_agent=self.agent_id,
            status="assigned"
        )
        
        # Add to current tasks
        self.current_tasks[task_id] = task
        
        # Update state if needed
        if self.state == AgentState.IDLE:
            self._update_state(AgentState.BUSY)
        
        # Schedule task for execution in the worker loop
        # (don't execute directly here to avoid blocking the message handler)
    
    def _handle_response(self, message: ProtocolMessage):
        """Handle response messages"""
        # Extract information
        conversation_id = message.metadata.get("conversation_id")
        if not conversation_id:
            logger.warning(f"Received response without conversation_id: {message.message_id}")
            return
        
        # Process the response (implementation will depend on subclass needs)
        self._process_response(message)
    
    def _handle_learning_update(self, message: ProtocolMessage):
        """Handle learning update messages"""
        # Extract update information
        update_id = message.content.get("update_id")
        if not update_id:
            logger.warning(f"Received learning update without update_id: {message.message_id}")
            return
        
        # Store new pattern in the agent's knowledge base
        pattern = message.content.get("pattern", {})
        capability = message.content.get("capability", "")
        effectiveness = message.content.get("effectiveness", 0.0)
        
        if pattern and capability and effectiveness > 0.5:
            # Add to learned patterns
            self.learned_patterns.append({
                "update_id": update_id,
                "pattern": pattern,
                "capability": capability,
                "effectiveness": effectiveness,
                "confidence": message.content.get("confidence", 0.0),
                "applied": False,
                "received_at": time.time()
            })
            
            # Switch to learning state temporarily
            self._update_state(AgentState.LEARNING)
            
            # Apply the pattern to the agent's behavior
            self._apply_learning_update(update_id, pattern, capability)
            
            # Revert to previous state
            if self.current_tasks:
                self._update_state(AgentState.BUSY)
            else:
                self._update_state(AgentState.IDLE)
    
    def _handle_broadcast(self, message: ProtocolMessage):
        """Handle broadcast messages"""
        # Process based on content
        action = message.metadata.get("action", "")
        
        if action:
            # Handle specific broadcast actions
            self._process_broadcast_action(message, action)
    
    def _handle_alert(self, message: ProtocolMessage):
        """Handle alert messages"""
        # Extract alert information
        alert_type = message.content.get("alert_type", "")
        alert_message = message.content.get("message", "")
        
        logger.warning(f"Agent {self.agent_id} received alert: {alert_type} - {alert_message}")
        
        # Take action based on alert type
        if alert_type == "system_shutdown":
            self.stop()
    
    def _process_response(self, message: ProtocolMessage):
        """
        Process a response message.
        
        This method should be implemented by subclasses based on their needs.
        """
        # Default implementation does nothing
        pass
    
    def _process_broadcast_action(self, message: ProtocolMessage, action: str):
        """
        Process a broadcast action.
        
        This method should be implemented by subclasses based on their needs.
        """
        # Default implementation does nothing
        pass
    
    def _check_for_new_tasks(self):
        """Check for new tasks from the protocol server"""
        # This is done via the message handler already
        pass
    
    def _process_current_tasks(self):
        """Process any current tasks"""
        if not self.current_tasks:
            if self.state == AgentState.BUSY:
                self._update_state(AgentState.IDLE)
            return
        
        # Process each task
        for task_id, task in list(self.current_tasks.items()):
            # Skip tasks that are not assigned or already running
            if task.status not in ["assigned"]:
                continue
            
            # Mark as running
            task.status = "running"
            
            try:
                # Execute task
                result = self._execute_task(task)
                
                # Mark as completed
                task.status = "completed"
                task.result = result
                
                # Update server about task completion
                self.server.task_orchestrator.update_task_status(
                    task_id, "completed", result
                )
                
                # Send response message
                self._send_task_response(task, result)
                
                # Move to task history
                self.task_history[task_id] = {
                    "task": asdict(task),
                    "completed_at": time.time(),
                    "success": True
                }
                
                # Remove from current tasks
                del self.current_tasks[task_id]
            
            except Exception as e:
                logger.error(f"Error executing task {task_id}: {str(e)}")
                
                # Mark as failed
                task.status = "failed"
                
                # Update server about task failure
                self.server.task_orchestrator.update_task_status(
                    task_id, "failed", {"error": str(e)}
                )
                
                # Send error response
                self._send_task_error(task, str(e))
                
                # Move to task history
                self.task_history[task_id] = {
                    "task": asdict(task),
                    "completed_at": time.time(),
                    "success": False,
                    "error": str(e)
                }
                
                # Remove from current tasks
                del self.current_tasks[task_id]
        
        # Update state if needed
        if not self.current_tasks and self.state == AgentState.BUSY:
            self._update_state(AgentState.IDLE)
    
    def _send_task_response(self, task: Task, result: Dict[str, Any]):
        """Send a response message for a completed task"""
        identity = AgentIdentity(
            agent_id=self.agent_id,
            agent_type=self.agent_type.value,
            capabilities=self.capabilities,
            status=self.state.value
        )
        
        message = ProtocolMessage(
            sender=identity,
            recipients=["orchestrator"],
            message_type=MessageType.RESPONSE,
            priority=MessagePriority.MEDIUM,
            content={
                "task_id": task.task_id,
                "status": "completed",
                "result": result
            },
            metadata={
                "conversation_id": task.conversation_id,
                "parent_message_id": task.task_id
            }
        )
        
        self.outbox.put(message)
    
    def _send_task_error(self, task: Task, error: str):
        """Send an error response message for a failed task"""
        identity = AgentIdentity(
            agent_id=self.agent_id,
            agent_type=self.agent_type.value,
            capabilities=self.capabilities,
            status=self.state.value
        )
        
        message = ProtocolMessage(
            sender=identity,
            recipients=["orchestrator"],
            message_type=MessageType.RESPONSE,
            priority=MessagePriority.HIGH,  # Higher priority for errors
            content={
                "task_id": task.task_id,
                "status": "failed",
                "error": error
            },
            metadata={
                "conversation_id": task.conversation_id,
                "parent_message_id": task.task_id
            }
        )
        
        self.outbox.put(message)
    
    def _apply_learning_update(self, update_id: str, pattern: Dict[str, Any], capability: str):
        """
        Apply a learning update to the agent's behavior.
        
        This method should be implemented by subclasses based on their needs.
        """
        # Default implementation just marks the pattern as applied
        for pattern_info in self.learned_patterns:
            if pattern_info["update_id"] == update_id:
                pattern_info["applied"] = True
                logger.info(f"Agent {self.agent_id} applied learning update: {update_id}")
                break
    
    @abstractmethod
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a task assigned to this agent.
        
        This method must be implemented by subclasses.
        
        Args:
            task: The task to execute
        
        Returns:
            Dict containing the result of the task execution
        """
        raise NotImplementedError("Subclasses must implement _execute_task method")
    
    def send_message(self, recipients: List[str], message_type: MessageType,
                   content: Dict[str, Any], metadata: Dict[str, Any] = None,
                   priority: MessagePriority = MessagePriority.MEDIUM):
        """
        Send a message to other agents.
        
        Args:
            recipients: List of recipient agent IDs
            message_type: Type of message
            content: Message content
            metadata: Message metadata
            priority: Message priority
        """
        identity = AgentIdentity(
            agent_id=self.agent_id,
            agent_type=self.agent_type.value,
            capabilities=self.capabilities,
            status=self.state.value
        )
        
        message = ProtocolMessage(
            sender=identity,
            recipients=recipients,
            message_type=message_type,
            priority=priority,
            content=content,
            metadata=metadata or {}
        )
        
        self.outbox.put(message)
    
    def record_feedback(self, task_id: str, action_type: str,
                      rating: float, comments: str = "",
                      context: Dict[str, Any] = None):
        """
        Record feedback on an action performed by the agent.
        
        Args:
            task_id: ID of the task the feedback relates to
            action_type: Type of action the feedback is about
            rating: Rating from 0.0 to 1.0
            comments: Optional comments about the rating
            context: Optional context information
        """
        feedback = FeedbackRecord(
            task_id=task_id,
            agent_id=self.agent_id,
            action_type=action_type,
            rating=rating,
            source="self",
            comments=comments,
            context=context or {}
        )
        
        self.server.learning_system.record_feedback(feedback)
    
    def submit_learning_update(self, pattern: Dict[str, Any], capability: str,
                            effectiveness: float, confidence: float,
                            agent_types: List[str] = None):
        """
        Submit a learning update to the learning system.
        
        Args:
            pattern: The pattern that was discovered
            capability: The capability this pattern applies to
            effectiveness: Estimated effectiveness (0.0 to 1.0)
            confidence: Confidence in the effectiveness estimate (0.0 to 1.0)
            agent_types: List of agent types this update applies to
        """
        if agent_types is None:
            agent_types = [self.agent_type.value]
        
        update = LearningUpdate(
            agent_types=agent_types,
            capability=capability,
            pattern=pattern,
            effectiveness=effectiveness,
            confidence=confidence,
            supporting_evidence=[]
        )
        
        self.server.learning_system.register_learning_update(update)


# =============================================================================
# Model Interface
# =============================================================================

class ModelInterface:
    """
    Interface for interacting with AI models.
    
    This class abstracts away the differences between different model providers
    and provides a unified interface for agents to use.
    """
    def __init__(self, model_id: Optional[str] = None, capability: Optional[str] = None):
        """
        Initialize the model interface.
        
        Args:
            model_id: Optional specific model ID to use
            capability: Optional capability to select model for
        """
        self.server = get_server()
        
        # Get model configuration
        if model_id:
            self.model_config = self.server.model_manager.get_model_config(model_id)
        elif capability:
            self.model_config = self.server.model_manager.get_model_for_capability(capability)
        else:
            # Default to GPT-4o if no specific model or capability is specified
            self.model_config = self.server.model_manager.get_model_config("gpt-4o")
        
        if not self.model_config:
            raise ValueError(f"No model found for ID {model_id} or capability {capability}")
        
        # Initialize provider-specific clients as needed
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize provider-specific clients"""
        if self.model_config.provider.value == "openai":
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            except ImportError:
                logger.error("OpenAI package not installed")
                self.openai_client = None
        
        elif self.model_config.provider.value == "anthropic":
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
            except ImportError:
                logger.error("Anthropic package not installed")
                self.anthropic_client = None
    
    def generate_text(self, prompt: str, system_message: Optional[str] = None,
                    max_tokens: Optional[int] = None) -> str:
        """
        Generate text using the configured model.
        
        Args:
            prompt: The user prompt to send to the model
            system_message: Optional system message for chat models
            max_tokens: Maximum tokens to generate
        
        Returns:
            The generated text
        """
        if not max_tokens:
            max_tokens = self.model_config.max_tokens
        
        if self.model_config.provider.value == "openai":
            return self._generate_text_openai(prompt, system_message, max_tokens)
        
        elif self.model_config.provider.value == "anthropic":
            return self._generate_text_anthropic(prompt, system_message, max_tokens)
        
        else:
            raise ValueError(f"Unsupported model provider: {self.model_config.provider.value}")
    
    def _generate_text_openai(self, prompt: str, system_message: Optional[str], max_tokens: int) -> str:
        """Generate text using OpenAI models"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.openai_client.chat.completions.create(
            model=self.model_config.model_id,
            messages=messages,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def _generate_text_anthropic(self, prompt: str, system_message: Optional[str], max_tokens: int) -> str:
        """Generate text using Anthropic models"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized")
        
        # Combine system message and prompt if both provided
        if system_message:
            full_prompt = f"{system_message}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        response = self.anthropic_client.messages.create(
            model=self.model_config.model_id,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": full_prompt}]
        )
        
        return response.content[0].text
    
    def analyze_code(self, code: str, language: str, query: str) -> Dict[str, Any]:
        """
        Analyze code using the configured model.
        
        Args:
            code: The code to analyze
            language: The programming language of the code
            query: What to analyze about the code
        
        Returns:
            Analysis results
        """
        prompt = f"""
        Please analyze the following {language} code based on this query: "{query}"
        
        ```{language}
        {code}
        ```
        
        Provide a detailed analysis focusing specifically on the query.
        Format your response as JSON with the following structure:
        {{
            "analysis": "The main analysis text",
            "issues": [
                {{
                    "description": "Description of the issue",
                    "severity": "high/medium/low",
                    "line_numbers": [line numbers if applicable],
                    "recommendations": ["List of recommendations"]
                }}
            ],
            "recommendations": ["List of overall recommendations"]
        }}
        """
        
        system_message = "You are an expert code analyzer specializing in identifying code patterns, issues, and optimization opportunities. Provide analysis in JSON format only."
        
        # Generate the analysis
        try:
            result_text = self.generate_text(prompt, system_message)
            
            # Extract JSON from the response (in case the model added extra text)
            import json
            import re
            
            json_match = re.search(r'(\{.*\})', result_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                result = json.loads(json_str)
            else:
                result = json.loads(result_text)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing code: {str(e)}")
            return {
                "analysis": f"Error analyzing code: {str(e)}",
                "issues": [],
                "recommendations": ["Try again with a smaller code sample"]
            }


# =============================================================================
# Specialized Agent Base Classes
# =============================================================================

class CodeQualityAgent(Agent):
    """Base class for code quality analysis agents"""
    
    def __init__(self, agent_id: str, capabilities: List[str], preferred_model: Optional[str] = None):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentCategory.CODE_QUALITY,
            capabilities=capabilities,
            preferred_model=preferred_model
        )
        
        # Code quality specific attributes
        self.quality_thresholds = {
            "complexity": 10,      # Maximum acceptable cyclomatic complexity
            "length": 100,         # Maximum acceptable function length in lines
            "nesting": 3,          # Maximum acceptable nesting level
            "comments": 0.2,       # Minimum acceptable comment ratio
            "duplication": 0.1     # Maximum acceptable code duplication ratio
        }
    
    def _get_max_concurrent_tasks(self) -> int:
        return 3  # Code quality agents can handle multiple tasks
    
    def _apply_learning_update(self, update_id: str, pattern: Dict[str, Any], capability: str):
        """Apply a learning update to the code quality agent"""
        super()._apply_learning_update(update_id, pattern, capability)
        
        # Update quality thresholds if this is a threshold update
        if capability == "quality_thresholds" and "thresholds" in pattern:
            new_thresholds = pattern["thresholds"]
            for key, value in new_thresholds.items():
                if key in self.quality_thresholds:
                    self.quality_thresholds[key] = value
                    logger.info(f"Updated {key} threshold to {value}")


class ArchitectureAgent(Agent):
    """Base class for architecture analysis agents"""
    
    def __init__(self, agent_id: str, capabilities: List[str], preferred_model: Optional[str] = None):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentCategory.ARCHITECTURE,
            capabilities=capabilities,
            preferred_model=preferred_model
        )
        
        # Architecture specific attributes
        self.known_patterns = []
        self.known_antipatterns = []
    
    def _get_max_concurrent_tasks(self) -> int:
        return 1  # Architecture analysis is typically resource-intensive


class DatabaseAgent(Agent):
    """Base class for database analysis agents"""
    
    def __init__(self, agent_id: str, capabilities: List[str], preferred_model: Optional[str] = None):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentCategory.DATABASE,
            capabilities=capabilities,
            preferred_model=preferred_model
        )
        
        # Database specific attributes
        self.known_orm_frameworks = [
            "sqlalchemy", "django.db", "peewee", 
            "sequelize", "mongoose", "typeorm",
            "entity framework", "hibernate"
        ]
    
    def _get_max_concurrent_tasks(self) -> int:
        return 2  # Database analysis can be parallelized to some extent


class DocumentationAgent(Agent):
    """Base class for documentation agents"""
    
    def __init__(self, agent_id: str, capabilities: List[str], preferred_model: Optional[str] = None):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentCategory.DOCUMENTATION,
            capabilities=capabilities,
            preferred_model=preferred_model
        )
        
        # Documentation specific attributes
        self.documentation_templates = {}
    
    def _get_max_concurrent_tasks(self) -> int:
        return 5  # Documentation can be highly parallelized


class AgentReadinessAgent(Agent):
    """Base class for agent readiness evaluation agents"""
    
    def __init__(self, agent_id: str, capabilities: List[str], preferred_model: Optional[str] = None):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentCategory.AGENT_READINESS,
            capabilities=capabilities,
            preferred_model=preferred_model
        )
        
        # Agent readiness specific attributes
        self.ml_frameworks = [
            "tensorflow", "pytorch", "scikit-learn", "keras",
            "huggingface", "transformers", "langchain", "llama-index"
        ]
    
    def _get_max_concurrent_tasks(self) -> int:
        return 2  # Agent readiness evaluation is moderately parallelizable


class LearningCoordinatorAgent(Agent):
    """
    Base class for the learning coordinator agent.
    
    This special agent analyzes feedback, identifies patterns,
    and coordinates learning updates across the agent system.
    """
    
    def __init__(self, agent_id: str = "learning_coordinator", preferred_model: Optional[str] = None):
        capabilities = [
            "pattern_recognition", "feedback_analysis", 
            "learning_coordination", "model_evaluation"
        ]
        
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentCategory.LEARNING_COORDINATOR,
            capabilities=capabilities,
            preferred_model=preferred_model or "gpt-4o"
        )
        
        # Learning coordinator specific attributes
        self.feedback_buffer = []
        self.pattern_candidates = []
        self.min_feedback_for_pattern = 5
    
    def _get_max_concurrent_tasks(self) -> int:
        return 10  # Learning coordinator needs to handle many tasks
    
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a learning coordinator task"""
        if task.task_type == "process_feedback":
            return self._process_feedback_task(task)
        
        elif task.task_type == "identify_patterns":
            return self._identify_patterns_task(task)
        
        elif task.task_type == "evaluate_model":
            return self._evaluate_model_task(task)
        
        else:
            raise ValueError(f"Unknown task type: {task.task_type}")
    
    def _process_feedback_task(self, task: Task) -> Dict[str, Any]:
        """Process feedback and add to buffer"""
        feedback_data = task.input_data.get("feedback", {})
        if not feedback_data:
            return {"status": "error", "message": "No feedback data provided"}
        
        # Add to feedback buffer
        self.feedback_buffer.append(feedback_data)
        
        # If buffer reaches threshold, schedule pattern identification
        if len(self.feedback_buffer) >= self.min_feedback_for_pattern:
            self._schedule_pattern_identification()
        
        return {"status": "success", "feedback_count": len(self.feedback_buffer)}
    
    def _identify_patterns_task(self, task: Task) -> Dict[str, Any]:
        """Identify patterns from feedback"""
        feedback_subset = task.input_data.get("feedback_subset", [])
        if not feedback_subset:
            feedback_subset = self.feedback_buffer[-self.min_feedback_for_pattern:]
        
        # Analyze feedback for patterns
        patterns = self._analyze_feedback_for_patterns(feedback_subset)
        
        # Submit learning updates for identified patterns
        updates_submitted = []
        for pattern in patterns:
            if pattern["confidence"] >= 0.7:  # Only submit high-confidence patterns
                update_id = self._submit_pattern_as_learning_update(pattern)
                updates_submitted.append(update_id)
        
        return {
            "status": "success",
            "patterns_identified": len(patterns),
            "updates_submitted": updates_submitted
        }
    
    def _evaluate_model_task(self, task: Task) -> Dict[str, Any]:
        """Evaluate model performance"""
        model_id = task.input_data.get("model_id")
        if not model_id:
            return {"status": "error", "message": "No model_id provided"}
        
        # Evaluate model
        evaluation = self._evaluate_model(model_id)
        
        return {
            "status": "success",
            "model_id": model_id,
            "evaluation": evaluation
        }
    
    def _schedule_pattern_identification(self):
        """Schedule a pattern identification task"""
        # Create task
        task = Task(
            task_type="identify_patterns",
            description="Identify patterns from recent feedback",
            input_data={
                "feedback_subset": self.feedback_buffer[-self.min_feedback_for_pattern:]
            },
            priority=MessagePriority.LOW  # Low priority so it doesn't interfere with regular tasks
        )
        
        # Submit to orchestrator
        self.server.task_orchestrator.submit_task(task)
    
    def _analyze_feedback_for_patterns(self, feedback_subset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze feedback to identify patterns"""
        # Group feedback by agent type and action type
        grouped_feedback = {}
        for feedback in feedback_subset:
            agent_id = feedback.get("agent_id", "unknown")
            action_type = feedback.get("action_type", "unknown")
            
            # Get agent type
            agent_identity = self.server.agent_registry.get_agent_identity(agent_id)
            agent_type = agent_identity.agent_type if agent_identity else "unknown"
            
            key = f"{agent_type}:{action_type}"
            if key not in grouped_feedback:
                grouped_feedback[key] = []
            
            grouped_feedback[key].append(feedback)
        
        # Identify patterns in each group
        patterns = []
        for key, feedback_group in grouped_feedback.items():
            if len(feedback_group) < 3:  # Need at least 3 examples to identify a pattern
                continue
            
            agent_type, action_type = key.split(":")
            
            # Calculate average rating
            ratings = [f.get("rating", 0.0) for f in feedback_group]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
            
            # Only consider patterns with good or bad ratings
            if 0.2 <= avg_rating <= 0.8:
                continue  # Skip patterns with middling ratings
            
            # Identify common elements in context
            contexts = [f.get("context", {}) for f in feedback_group]
            common_elements = self._find_common_elements(contexts)
            
            if common_elements:
                # Create pattern
                pattern = {
                    "agent_type": agent_type,
                    "action_type": action_type,
                    "effectiveness": avg_rating,
                    "confidence": min(1.0, len(feedback_group) / 10),  # More feedback = higher confidence
                    "pattern": common_elements,
                    "feedback_count": len(feedback_group)
                }
                
                patterns.append(pattern)
        
        return patterns
    
    def _find_common_elements(self, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find common elements in a list of context dictionaries"""
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
    
    def _submit_pattern_as_learning_update(self, pattern: Dict[str, Any]) -> str:
        """Submit a pattern as a learning update"""
        update = LearningUpdate(
            agent_types=[pattern["agent_type"]],
            capability=pattern["action_type"],
            pattern=pattern["pattern"],
            effectiveness=pattern["effectiveness"],
            confidence=pattern["confidence"],
            supporting_evidence=[str(i) for i in range(pattern["feedback_count"])]
        )
        
        return self.server.learning_system.register_learning_update(update)
    
    def _evaluate_model(self, model_id: str) -> Dict[str, Any]:
        """Evaluate a model's performance"""
        # Get model config
        model_config = self.server.model_manager.get_model_config(model_id)
        if not model_config:
            return {"error": f"Model {model_id} not found"}
        
        # Perform evaluation
        # TODO: Implement actual model evaluation
        
        return {
            "accuracy": 0.95,
            "latency": 0.5,
            "token_efficiency": 0.8,
            "evaluation_time": time.time()
        }