"""
Redis-based Message Broker Implementation

This module implements a message broker using Redis for reliable message
delivery, persistence, and distributed communication across the TerraFlow
platform's agent ecosystem.
"""

import json
import time
import uuid
import logging
import threading
from typing import Dict, List, Any, Optional, Callable, Set
import redis

from infrastructure.architecture.agent_communication_protocol import (
    Message, MessageStatus, MessageMetadata, MessageValidator, MessageType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisMessageBroker:
    """
    Redis-based implementation of the message broker for reliable
    message delivery across distributed agents.
    """
    
    def __init__(self, redis_host="localhost", redis_port=6379, redis_db=0, redis_password=None):
        """
        Initialize the Redis message broker
        
        Args:
            redis_host: Redis host
            redis_port: Redis port
            redis_db: Redis database
            redis_password: Redis password
        """
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True
        )
        
        # Keys and channels
        self.message_key_prefix = "terraflow:message:"
        self.queue_key_prefix = "terraflow:queue:"
        self.subscription_channel_prefix = "terraflow:channel:"
        self.status_key_prefix = "terraflow:message_status:"
        self.retry_queue_key = "terraflow:retry_queue"
        self.delivery_confirm_key_prefix = "terraflow:delivery_confirm:"
        
        # Local tracking of callbacks by agent ID
        self.callbacks = {}  # type: Dict[str, List[Callable[[Message], None]]]
        
        # Set of processed message IDs to avoid duplicates
        self.processed_messages = set()  # type: Set[str]
        
        # Message processing threads
        self.pubsub_thread = None
        self.retry_thread = None
        self.running = False
    
    def start(self):
        """Start the message broker threads"""
        self.running = True
        
        # Start Redis pubsub thread for real-time message delivery
        pubsub = self.redis_client.pubsub()
        
        # Start retry thread for failed messages
        self.retry_thread = threading.Thread(target=self._retry_loop)
        self.retry_thread.daemon = True
        self.retry_thread.start()
        
        logger.info("Redis message broker started")
    
    def stop(self):
        """Stop the message broker threads"""
        self.running = False
        
        # Stop pubsub thread
        if self.pubsub_thread:
            self.pubsub_thread.stop()
        
        # Retry thread will exit on next iteration due to self.running = False
        
        logger.info("Redis message broker stopped")
    
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
        
        # Update status and store message
        message.metadata.status = MessageStatus.SENT
        self._store_message(message)
        
        # Add message to each recipient's queue
        for recipient in message.recipients:
            recipient_queue_key = f"{self.queue_key_prefix}{recipient}"
            self.redis_client.rpush(recipient_queue_key, message.message_id)
            
            # Publish to recipient's channel for real-time delivery
            recipient_channel = f"{self.subscription_channel_prefix}{recipient}"
            self.redis_client.publish(recipient_channel, message.message_id)
            
            logger.debug(f"Message {message.message_id} queued for {recipient}")
        
        logger.info(f"Message {message.message_id} published to {len(message.recipients)} recipients")
        return True
    
    def subscribe(self, agent_id: str, callback: Callable[[Message], None]):
        """
        Subscribe to messages for a specific agent
        
        Args:
            agent_id: The ID of the agent subscribing
            callback: The callback function to invoke when a message is received
        """
        # Store callback locally
        if agent_id not in self.callbacks:
            self.callbacks[agent_id] = []
        
        self.callbacks[agent_id].append(callback)
        
        # Subscribe to agent's channel in Redis
        if not self.pubsub_thread:
            # Initialize pubsub if not already done
            pubsub = self.redis_client.pubsub()
            
            # Subscribe to agent's channel
            agent_channel = f"{self.subscription_channel_prefix}{agent_id}"
            pubsub.subscribe(**{agent_channel: self._message_handler})
            
            # Start pubsub thread
            self.pubsub_thread = pubsub.run_in_thread(sleep_time=0.01)
            
            logger.info(f"Started pubsub thread and subscribed agent {agent_id}")
        else:
            # Add subscription to existing pubsub
            agent_channel = f"{self.subscription_channel_prefix}{agent_id}"
            self.pubsub_thread.subscribe(agent_channel, self._message_handler)
            
            logger.info(f"Added subscription for agent {agent_id} to existing pubsub")
        
        # Check for any queued messages and process them
        self._process_queued_messages(agent_id)
        
        logger.info(f"Agent {agent_id} subscribed to messages")
    
    def unsubscribe(self, agent_id: str):
        """
        Unsubscribe from messages
        
        Args:
            agent_id: The ID of the agent unsubscribing
        """
        # Remove callbacks
        if agent_id in self.callbacks:
            del self.callbacks[agent_id]
        
        # Unsubscribe from Redis channel
        if self.pubsub_thread:
            agent_channel = f"{self.subscription_channel_prefix}{agent_id}"
            self.pubsub_thread.unsubscribe(agent_channel)
        
        logger.info(f"Agent {agent_id} unsubscribed from messages")
    
    def confirm_delivery(self, message_id: str, recipient_id: str):
        """
        Confirm delivery of a message to a recipient
        
        Args:
            message_id: The ID of the message
            recipient_id: The ID of the recipient
        """
        # Store delivery confirmation
        confirmation_key = f"{self.delivery_confirm_key_prefix}{message_id}"
        self.redis_client.sadd(confirmation_key, recipient_id)
        
        # Get message and check if all recipients have confirmed
        message_data = self.redis_client.get(f"{self.message_key_prefix}{message_id}")
        if not message_data:
            logger.warning(f"Cannot confirm delivery: Message {message_id} not found")
            return
        
        message = Message.from_json(message_data)
        
        # Check if all recipients have confirmed
        confirmed_recipients = self.redis_client.smembers(confirmation_key)
        
        if set(confirmed_recipients) >= set(message.recipients):
            # All recipients have confirmed, update status
            message.metadata.status = MessageStatus.PROCESSED
            self._store_message(message)
            
            logger.info(f"Message {message_id} processed by all recipients")
    
    def get_message_status(self, message_id: str) -> Optional[MessageStatus]:
        """
        Get the status of a message
        
        Args:
            message_id: The ID of the message
            
        Returns:
            MessageStatus: The status of the message, or None if not found
        """
        status_key = f"{self.status_key_prefix}{message_id}"
        status_value = self.redis_client.get(status_key)
        
        if status_value:
            return MessageStatus(status_value)
        
        return None
    
    def _store_message(self, message: Message):
        """
        Store a message in Redis
        
        Args:
            message: The message to store
        """
        # Store message data
        message_key = f"{self.message_key_prefix}{message.message_id}"
        self.redis_client.set(message_key, message.to_json())
        
        # Set expiration based on TTL
        ttl = message.metadata.ttl if message.metadata.ttl > 0 else 3600  # Default 1 hour
        self.redis_client.expire(message_key, ttl)
        
        # Store message status
        status_key = f"{self.status_key_prefix}{message.message_id}"
        self.redis_client.set(status_key, message.metadata.status.value)
        self.redis_client.expire(status_key, ttl)
    
    def _message_handler(self, message):
        """
        Handle message from Redis pubsub
        
        Args:
            message: Redis pubsub message
        """
        if message["type"] != "message":
            return
        
        # Extract message ID from channel name
        channel = message["channel"]
        agent_id = channel.split(":")[-1]
        
        # Get message ID from data
        message_id = message["data"]
        
        # Avoid processing the same message twice
        if message_id in self.processed_messages:
            return
        
        self.processed_messages.add(message_id)
        
        # Get message data
        message_key = f"{self.message_key_prefix}{message_id}"
        message_data = self.redis_client.get(message_key)
        
        if not message_data:
            logger.warning(f"Message {message_id} not found in Redis")
            return
        
        # Parse message
        try:
            msg = Message.from_json(message_data)
            
            # Deliver to callbacks
            if agent_id in self.callbacks:
                for callback in self.callbacks[agent_id]:
                    try:
                        callback(msg)
                    except Exception as e:
                        logger.error(f"Error in callback for {agent_id}: {str(e)}")
            
            # Remove from agent's queue
            queue_key = f"{self.queue_key_prefix}{agent_id}"
            self.redis_client.lrem(queue_key, 0, message_id)
            
            # Confirm delivery
            self.confirm_delivery(message_id, agent_id)
            
        except Exception as e:
            logger.error(f"Error processing message {message_id}: {str(e)}")
    
    def _process_queued_messages(self, agent_id: str):
        """
        Process queued messages for an agent
        
        Args:
            agent_id: Agent ID
        """
        queue_key = f"{self.queue_key_prefix}{agent_id}"
        
        # Get all queued message IDs
        queued_messages = self.redis_client.lrange(queue_key, 0, -1)
        
        for message_id in queued_messages:
            # Skip already processed messages
            if message_id in self.processed_messages:
                continue
            
            # Get message data
            message_key = f"{self.message_key_prefix}{message_id}"
            message_data = self.redis_client.get(message_key)
            
            if message_data:
                try:
                    msg = Message.from_json(message_data)
                    
                    # Deliver to callbacks
                    if agent_id in self.callbacks:
                        for callback in self.callbacks[agent_id]:
                            try:
                                callback(msg)
                                self.processed_messages.add(message_id)
                            except Exception as e:
                                logger.error(f"Error in callback for {agent_id}: {str(e)}")
                    
                    # Remove from queue
                    self.redis_client.lrem(queue_key, 0, message_id)
                    
                    # Confirm delivery
                    self.confirm_delivery(message_id, agent_id)
                    
                except Exception as e:
                    logger.error(f"Error processing queued message {message_id}: {str(e)}")
    
    def _retry_loop(self):
        """Background thread for retrying failed messages"""
        while self.running:
            try:
                # Check for messages to retry
                retry_time = time.time()
                
                # Get retry schedule
                retry_schedule = self.redis_client.zrangebyscore(
                    self.retry_queue_key, 0, retry_time
                )
                
                for message_id in retry_schedule:
                    # Get message
                    message_key = f"{self.message_key_prefix}{message_id}"
                    message_data = self.redis_client.get(message_key)
                    
                    if message_data:
                        try:
                            msg = Message.from_json(message_data)
                            
                            # Check if max retries reached
                            if msg.metadata.retries >= msg.metadata.max_retries:
                                # Mark as failed
                                msg.metadata.status = MessageStatus.FAILED
                                self._store_message(msg)
                                
                                # Remove from retry queue
                                self.redis_client.zrem(self.retry_queue_key, message_id)
                                
                                logger.error(f"Max retries exceeded for message {message_id}")
                                continue
                            
                            # Increment retry count
                            msg.metadata.retries += 1
                            msg.metadata.status = MessageStatus.RETRYING
                            self._store_message(msg)
                            
                            # Retry delivery
                            for recipient in msg.recipients:
                                # Check if already delivered to this recipient
                                confirmation_key = f"{self.delivery_confirm_key_prefix}{message_id}"
                                if self.redis_client.sismember(confirmation_key, recipient):
                                    continue
                                
                                # Add to recipient's queue
                                recipient_queue_key = f"{self.queue_key_prefix}{recipient}"
                                self.redis_client.rpush(recipient_queue_key, message_id)
                                
                                # Publish to recipient's channel
                                recipient_channel = f"{self.subscription_channel_prefix}{recipient}"
                                self.redis_client.publish(recipient_channel, message_id)
                                
                                logger.info(f"Retrying message {message_id} delivery to {recipient} (attempt {msg.metadata.retries})")
                            
                            # Schedule next retry with exponential backoff
                            if msg.metadata.retries < msg.metadata.max_retries:
                                next_retry = time.time() + (2 ** msg.metadata.retries)
                                self.redis_client.zadd(self.retry_queue_key, {message_id: next_retry})
                            else:
                                # Remove from retry queue
                                self.redis_client.zrem(self.retry_queue_key, message_id)
                            
                        except Exception as e:
                            logger.error(f"Error retrying message {message_id}: {str(e)}")
                    else:
                        # Message not found, remove from retry queue
                        self.redis_client.zrem(self.retry_queue_key, message_id)
            
            except Exception as e:
                logger.error(f"Error in retry loop: {str(e)}")
            
            # Sleep for a short interval
            time.sleep(1)
    
    def schedule_retry(self, message_id: str, delay: float = 1.0):
        """
        Schedule a message for retry
        
        Args:
            message_id: The ID of the message to retry
            delay: Delay in seconds before retry
        """
        retry_time = time.time() + delay
        self.redis_client.zadd(self.retry_queue_key, {message_id: retry_time})
        logger.info(f"Scheduled message {message_id} for retry at {retry_time}")


# Helper functions for working with the Redis broker

def create_redis_broker(host="localhost", port=6379, db=0, password=None) -> RedisMessageBroker:
    """
    Create a Redis message broker
    
    Args:
        host: Redis host
        port: Redis port
        db: Redis database
        password: Redis password
        
    Returns:
        RedisMessageBroker: A new Redis message broker
    """
    broker = RedisMessageBroker(redis_host=host, redis_port=port, redis_db=db, redis_password=password)
    broker.start()
    return broker