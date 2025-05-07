"""
Agent Communication Protocol for TerraFlow Platform

This module defines the enhanced communication protocol for agent-to-agent
communication within the TerraFlow platform, featuring standardized message
formats, reliable delivery mechanisms, comprehensive error handling,
and message validation.
"""

import json
import time
import uuid
import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessagePriority(Enum):
    """Priority levels for messages"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MessageType(Enum):
    """Types of messages that can be exchanged between agents"""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    ALERT = "alert"
    LEARNING_UPDATE = "learning_update"
    HEARTBEAT = "heartbeat"
    STATUS_UPDATE = "status_update"
    CAPABILITY_DISCOVERY = "capability_discovery"

class MessageStatus(Enum):
    """Status of a message in the system"""
    CREATED = "created"
    SENT = "sent"
    DELIVERED = "delivered"
    PROCESSED = "processed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class MessageMetadata:
    """Metadata for a message"""
    created_at: float = field(default_factory=time.time)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: Optional[str] = None
    path: List[str] = field(default_factory=list)
    ttl: int = 60  # Time to live in seconds
    retries: int = 0
    max_retries: int = 3
    status: MessageStatus = MessageStatus.CREATED
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result["status"] = self.status.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageMetadata':
        """Create from dictionary"""
        data_copy = data.copy()
        data_copy["status"] = MessageStatus(data_copy["status"])
        return cls(**data_copy)

@dataclass
class Message:
    """
    Message for agent-to-agent communication.
    
    This class represents a message in the enhanced agent communication protocol.
    """
    message_id: str
    sender_id: str
    recipients: List[str]
    message_type: MessageType
    content: Dict[str, Any]
    metadata: MessageMetadata = field(default_factory=MessageMetadata)
    priority: MessagePriority = MessagePriority.MEDIUM
    
    def __post_init__(self):
        """Ensure message_type is a MessageType enum"""
        if isinstance(self.message_type, str):
            self.message_type = MessageType(self.message_type)
        
        if isinstance(self.priority, str):
            self.priority = MessagePriority(self.priority)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary for serialization"""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipients": self.recipients,
            "message_type": self.message_type.value,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
            "priority": self.priority.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create a message from a dictionary"""
        data_copy = data.copy()
        data_copy["metadata"] = MessageMetadata.from_dict(data_copy.get("metadata", {}))
        return cls(**data_copy)
    
    def to_json(self) -> str:
        """Convert the message to JSON"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create a message from JSON"""
        return cls.from_dict(json.loads(json_str))

class MessageValidator:
    """Validator for message format and content"""
    
    @staticmethod
    def validate_message(message: Message) -> bool:
        """
        Validate a message for required fields and format
        
        Args:
            message: The message to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check required fields
            if not message.message_id or not isinstance(message.message_id, str):
                logger.error(f"Invalid message_id: {message.message_id}")
                return False
                
            if not message.sender_id or not isinstance(message.sender_id, str):
                logger.error(f"Invalid sender_id: {message.sender_id}")
                return False
                
            if not isinstance(message.recipients, list):
                logger.error(f"Recipients must be a list: {message.recipients}")
                return False
                
            if not message.recipients:
                logger.error("Recipients list cannot be empty")
                return False
                
            if not isinstance(message.content, dict):
                logger.error(f"Content must be a dictionary: {message.content}")
                return False
            
            # Validate metadata
            if message.metadata.retries > message.metadata.max_retries:
                logger.error(f"Retries {message.metadata.retries} exceed max_retries {message.metadata.max_retries}")
                return False
                
            if message.metadata.ttl <= 0:
                logger.error(f"TTL must be positive: {message.metadata.ttl}")
                return False
            
            # Message-type specific validation
            if message.message_type == MessageType.RESPONSE:
                if "request_id" not in message.content:
                    logger.error("Response messages must include request_id in content")
                    return False
            
            return True
            
        except Exception as e:
            logger.exception(f"Error validating message: {str(e)}")
            return False

class MessageBroker:
    """
    Message broker for reliable message delivery
    
    This class handles message routing, delivery confirmation,
    and retry logic for failed message delivery attempts.
    """
    
    def __init__(self):
        """Initialize the message broker"""
        self.subscribers = {}  # type: Dict[str, List[Callable[[Message], None]]]
        self.messages = {}  # type: Dict[str, Message]
        self.delivery_confirmations = set()  # type: set[str]
    
    def publish(self, message: Message) -> bool:
        """
        Publish a message to its recipients
        
        Args:
            message: The message to publish
            
        Returns:
            bool: True if message was accepted for delivery, False otherwise
        """
        # Validate message
        if not MessageValidator.validate_message(message):
            logger.error(f"Message validation failed for {message.message_id}")
            return False
        
        # Store message
        self.messages[message.message_id] = message
        
        # Update status
        message.metadata.status = MessageStatus.SENT
        
        # Deliver to recipients
        for recipient in message.recipients:
            if recipient in self.subscribers:
                for callback in self.subscribers[recipient]:
                    try:
                        callback(message)
                        logger.debug(f"Message {message.message_id} delivered to {recipient}")
                    except Exception as e:
                        logger.error(f"Error delivering message {message.message_id} to {recipient}: {str(e)}")
                        # Mark for retry if applicable
                        if message.metadata.retries < message.metadata.max_retries:
                            message.metadata.retries += 1
                            message.metadata.status = MessageStatus.RETRYING
                            # In a real implementation, we would queue for retry
                            # For now, we just log the retry
                            logger.info(f"Message {message.message_id} queued for retry ({message.metadata.retries}/{message.metadata.max_retries})")
                        else:
                            message.metadata.status = MessageStatus.FAILED
                            logger.error(f"Max retries exceeded for message {message.message_id}")
            else:
                logger.warning(f"No subscribers for recipient {recipient}")
        
        # Check if all recipients received the message
        if message.metadata.status != MessageStatus.RETRYING and message.metadata.status != MessageStatus.FAILED:
            message.metadata.status = MessageStatus.DELIVERED
            logger.info(f"Message {message.message_id} delivered to all recipients")
        
        return True
    
    def subscribe(self, agent_id: str, callback: Callable[[Message], None]):
        """
        Subscribe to messages for a specific agent
        
        Args:
            agent_id: The ID of the agent subscribing
            callback: The callback function to invoke when a message is received
        """
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []
        
        self.subscribers[agent_id].append(callback)
        logger.info(f"Agent {agent_id} subscribed to messages")
    
    def unsubscribe(self, agent_id: str):
        """
        Unsubscribe from messages
        
        Args:
            agent_id: The ID of the agent unsubscribing
        """
        if agent_id in self.subscribers:
            del self.subscribers[agent_id]
            logger.info(f"Agent {agent_id} unsubscribed from messages")
    
    def confirm_delivery(self, message_id: str, recipient_id: str):
        """
        Confirm delivery of a message to a recipient
        
        Args:
            message_id: The ID of the message
            recipient_id: The ID of the recipient
        """
        confirmation_key = f"{message_id}:{recipient_id}"
        self.delivery_confirmations.add(confirmation_key)
        logger.debug(f"Delivery confirmation received for {confirmation_key}")
        
        # Check if all recipients have confirmed delivery
        if message_id in self.messages:
            message = self.messages[message_id]
            all_confirmed = True
            
            for recipient in message.recipients:
                if f"{message_id}:{recipient}" not in self.delivery_confirmations:
                    all_confirmed = False
                    break
            
            if all_confirmed:
                message.metadata.status = MessageStatus.PROCESSED
                logger.info(f"Message {message_id} processed by all recipients")
    
    def get_message_status(self, message_id: str) -> Optional[MessageStatus]:
        """
        Get the status of a message
        
        Args:
            message_id: The ID of the message
            
        Returns:
            MessageStatus: The status of the message, or None if not found
        """
        if message_id in self.messages:
            return self.messages[message_id].metadata.status
        return None

# Helper functions for creating common message types
def create_request_message(
    sender_id: str,
    recipients: List[str],
    content: Dict[str, Any],
    priority: MessagePriority = MessagePriority.MEDIUM,
    metadata: Optional[MessageMetadata] = None
) -> Message:
    """
    Create a request message
    
    Args:
        sender_id: ID of the sending agent
        recipients: List of recipient agent IDs
        content: Message content
        priority: Message priority
        metadata: Optional message metadata
        
    Returns:
        Message: A new request message
    """
    message_id = str(uuid.uuid4())
    return Message(
        message_id=message_id,
        sender_id=sender_id,
        recipients=recipients,
        message_type=MessageType.REQUEST,
        content=content,
        priority=priority,
        metadata=metadata or MessageMetadata(correlation_id=message_id)
    )

def create_response_message(
    sender_id: str,
    recipients: List[str],
    request_id: str,
    content: Dict[str, Any],
    priority: MessagePriority = MessagePriority.MEDIUM,
    metadata: Optional[MessageMetadata] = None
) -> Message:
    """
    Create a response message
    
    Args:
        sender_id: ID of the sending agent
        recipients: List of recipient agent IDs
        request_id: ID of the request this is responding to
        content: Message content (should include request_id)
        priority: Message priority
        metadata: Optional message metadata
        
    Returns:
        Message: A new response message
    """
    # Ensure request_id is in content
    content_with_request_id = content.copy()
    content_with_request_id["request_id"] = request_id
    
    message_id = str(uuid.uuid4())
    
    # Create metadata with correlation ID matching the request ID
    if metadata is None:
        metadata = MessageMetadata(correlation_id=request_id)
    else:
        metadata.correlation_id = request_id
    
    return Message(
        message_id=message_id,
        sender_id=sender_id,
        recipients=recipients,
        message_type=MessageType.RESPONSE,
        content=content_with_request_id,
        priority=priority,
        metadata=metadata
    )

def create_broadcast_message(
    sender_id: str,
    recipients: List[str],
    content: Dict[str, Any],
    priority: MessagePriority = MessagePriority.MEDIUM,
    metadata: Optional[MessageMetadata] = None
) -> Message:
    """
    Create a broadcast message
    
    Args:
        sender_id: ID of the sending agent
        recipients: List of recipient agent IDs (often all agents)
        content: Message content
        priority: Message priority
        metadata: Optional message metadata
        
    Returns:
        Message: A new broadcast message
    """
    message_id = str(uuid.uuid4())
    return Message(
        message_id=message_id,
        sender_id=sender_id,
        recipients=recipients,
        message_type=MessageType.BROADCAST,
        content=content,
        priority=priority,
        metadata=metadata or MessageMetadata(correlation_id=message_id)
    )

def create_alert_message(
    sender_id: str,
    recipients: List[str],
    alert_type: str,
    alert_message: str,
    details: Optional[Dict[str, Any]] = None,
    priority: MessagePriority = MessagePriority.HIGH,
    metadata: Optional[MessageMetadata] = None
) -> Message:
    """
    Create an alert message
    
    Args:
        sender_id: ID of the sending agent
        recipients: List of recipient agent IDs
        alert_type: Type of alert
        alert_message: Alert message
        details: Additional alert details
        priority: Message priority
        metadata: Optional message metadata
        
    Returns:
        Message: A new alert message
    """
    message_id = str(uuid.uuid4())
    content = {
        "alert_type": alert_type,
        "alert_message": alert_message,
        "details": details or {}
    }
    
    return Message(
        message_id=message_id,
        sender_id=sender_id,
        recipients=recipients,
        message_type=MessageType.ALERT,
        content=content,
        priority=priority,
        metadata=metadata or MessageMetadata(correlation_id=message_id)
    )

def create_heartbeat_message(
    sender_id: str,
    recipients: List[str],
    status: str,
    metrics: Optional[Dict[str, Any]] = None,
    priority: MessagePriority = MessagePriority.LOW,
    metadata: Optional[MessageMetadata] = None
) -> Message:
    """
    Create a heartbeat message
    
    Args:
        sender_id: ID of the sending agent
        recipients: List of recipient agent IDs (usually just the controller)
        status: Agent status
        metrics: Optional agent metrics
        priority: Message priority
        metadata: Optional message metadata
        
    Returns:
        Message: A new heartbeat message
    """
    message_id = str(uuid.uuid4())
    content = {
        "status": status,
        "timestamp": time.time(),
        "metrics": metrics or {}
    }
    
    return Message(
        message_id=message_id,
        sender_id=sender_id,
        recipients=recipients,
        message_type=MessageType.HEARTBEAT,
        content=content,
        priority=priority,
        metadata=metadata or MessageMetadata(correlation_id=message_id)
    )

def create_capability_discovery_message(
    sender_id: str,
    recipients: List[str],
    capabilities: List[str],
    details: Optional[Dict[str, Any]] = None,
    priority: MessagePriority = MessagePriority.MEDIUM,
    metadata: Optional[MessageMetadata] = None
) -> Message:
    """
    Create a capability discovery message
    
    Args:
        sender_id: ID of the sending agent
        recipients: List of recipient agent IDs
        capabilities: List of capabilities the agent provides
        details: Optional capability details
        priority: Message priority
        metadata: Optional message metadata
        
    Returns:
        Message: A new capability discovery message
    """
    message_id = str(uuid.uuid4())
    content = {
        "capabilities": capabilities,
        "details": details or {}
    }
    
    return Message(
        message_id=message_id,
        sender_id=sender_id,
        recipients=recipients,
        message_type=MessageType.CAPABILITY_DISCOVERY,
        content=content,
        priority=priority,
        metadata=metadata or MessageMetadata(correlation_id=message_id)
    )