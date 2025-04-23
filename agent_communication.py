"""
Agent Communication Module for Code Deep Dive Analyzer

This module implements the agent-to-agent protocol that allows agents to communicate,
negotiate, and collaborate effectively. It provides message routing, negotiation 
protocols, consensus mechanisms, and collaboration patterns.
"""

import os
import json
import time
import uuid
import logging
import threading
import queue
from typing import Dict, List, Any, Optional, Union, Callable, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field, asdict

# Import protocol server components
from protocol_server import (
    ProtocolMessage, MessageType, MessagePriority, AgentIdentity, AgentCategory,
    Task, get_server
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CommunicationPattern(Enum):
    """Different communication patterns that agents can use"""
    REQUEST_RESPONSE = "request_response"  # Simple request and response
    BROADCAST = "broadcast"  # One-to-many communication
    SUBSCRIPTION = "subscription"  # Publish-subscribe pattern
    NEGOTIATION = "negotiation"  # Multi-step negotiation
    VOTING = "voting"  # Consensus building through voting
    DELEGATION = "delegation"  # Task delegation pattern
    CONSULTATION = "consultation"  # Expert consultation pattern


@dataclass
class ConversationContext:
    """Context for an ongoing conversation between agents"""
    conversation_id: str
    initiator: str
    participants: List[str]
    pattern: CommunicationPattern
    topic: str
    started_at: float = field(default_factory=time.time)
    last_message_at: float = field(default_factory=time.time)
    message_count: int = 0
    state: Dict[str, Any] = field(default_factory=dict)


class ConversationManager:
    """
    Manages ongoing conversations between agents.
    
    This component tracks conversation contexts, ensures proper message routing
    within conversations, and enforces conversation protocols.
    """
    
    def __init__(self):
        """Initialize the conversation manager"""
        self.server = get_server()
        self.conversations: Dict[str, ConversationContext] = {}
        self.agent_conversations: Dict[str, Set[str]] = {}  # agent_id -> {conversation_ids}
        self.pattern_handlers: Dict[CommunicationPattern, Callable] = {}
        
        # Register pattern handlers
        self._register_pattern_handlers()
    
    def _register_pattern_handlers(self):
        """Register handlers for different communication patterns"""
        self.pattern_handlers = {
            CommunicationPattern.REQUEST_RESPONSE: self._handle_request_response,
            CommunicationPattern.BROADCAST: self._handle_broadcast,
            CommunicationPattern.SUBSCRIPTION: self._handle_subscription,
            CommunicationPattern.NEGOTIATION: self._handle_negotiation,
            CommunicationPattern.VOTING: self._handle_voting,
            CommunicationPattern.DELEGATION: self._handle_delegation,
            CommunicationPattern.CONSULTATION: self._handle_consultation
        }
    
    def create_conversation(self, initiator: str, participants: List[str], pattern: CommunicationPattern, 
                           topic: str) -> str:
        """
        Create a new conversation
        
        Args:
            initiator: Agent ID that initiated the conversation
            participants: List of participant agent IDs
            pattern: Communication pattern to use
            topic: Topic of the conversation
            
        Returns:
            The conversation ID
        """
        conversation_id = str(uuid.uuid4())
        
        context = ConversationContext(
            conversation_id=conversation_id,
            initiator=initiator,
            participants=participants.copy(),
            pattern=pattern,
            topic=topic
        )
        
        # Make sure initiator is in participants
        if initiator not in context.participants:
            context.participants.append(initiator)
        
        # Store conversation
        self.conversations[conversation_id] = context
        
        # Update agent indexes
        for participant in context.participants:
            if participant not in self.agent_conversations:
                self.agent_conversations[participant] = set()
            
            self.agent_conversations[participant].add(conversation_id)
        
        logger.info(f"Created conversation {conversation_id}: {pattern.value} on '{topic}'")
        return conversation_id
    
    def add_participant(self, conversation_id: str, agent_id: str) -> bool:
        """
        Add a participant to a conversation
        
        Args:
            conversation_id: The conversation ID
            agent_id: The agent ID to add
            
        Returns:
            True if successful, False otherwise
        """
        if conversation_id not in self.conversations:
            return False
        
        context = self.conversations[conversation_id]
        
        # Already a participant
        if agent_id in context.participants:
            return True
        
        # Add to participants
        context.participants.append(agent_id)
        
        # Update agent index
        if agent_id not in self.agent_conversations:
            self.agent_conversations[agent_id] = set()
        
        self.agent_conversations[agent_id].add(conversation_id)
        
        logger.info(f"Added agent {agent_id} to conversation {conversation_id}")
        return True
    
    def remove_participant(self, conversation_id: str, agent_id: str) -> bool:
        """
        Remove a participant from a conversation
        
        Args:
            conversation_id: The conversation ID
            agent_id: The agent ID to remove
            
        Returns:
            True if successful, False otherwise
        """
        if conversation_id not in self.conversations:
            return False
        
        context = self.conversations[conversation_id]
        
        # Can't remove initiator
        if agent_id == context.initiator:
            return False
        
        # Not a participant
        if agent_id not in context.participants:
            return False
        
        # Remove from participants
        context.participants.remove(agent_id)
        
        # Update agent index
        if agent_id in self.agent_conversations:
            self.agent_conversations[agent_id].remove(conversation_id)
        
        logger.info(f"Removed agent {agent_id} from conversation {conversation_id}")
        return True
    
    def close_conversation(self, conversation_id: str) -> bool:
        """
        Close a conversation
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            True if successful, False otherwise
        """
        if conversation_id not in self.conversations:
            return False
        
        context = self.conversations[conversation_id]
        
        # Remove from all participants' indexes
        for participant in context.participants:
            if participant in self.agent_conversations:
                if conversation_id in self.agent_conversations[participant]:
                    self.agent_conversations[participant].remove(conversation_id)
        
        # Remove conversation
        del self.conversations[conversation_id]
        
        logger.info(f"Closed conversation {conversation_id}")
        return True
    
    def process_message(self, message: ProtocolMessage) -> bool:
        """
        Process a message within a conversation
        
        Args:
            message: The message to process
            
        Returns:
            True if successfully processed, False otherwise
        """
        conversation_id = message.metadata.get("conversation_id")
        if not conversation_id or conversation_id not in self.conversations:
            # Not a conversation message or unknown conversation
            return False
        
        context = self.conversations[conversation_id]
        
        # Update conversation statistics
        context.last_message_at = time.time()
        context.message_count += 1
        
        # Handle according to pattern
        handler = self.pattern_handlers.get(context.pattern)
        if handler:
            return handler(context, message)
        
        # No handler, just pass through
        return True
    
    def get_active_conversations(self, agent_id: Optional[str] = None) -> List[ConversationContext]:
        """
        Get active conversations
        
        Args:
            agent_id: Optional agent ID to filter by
            
        Returns:
            List of active conversation contexts
        """
        if agent_id:
            if agent_id not in self.agent_conversations:
                return []
            
            conversation_ids = self.agent_conversations[agent_id]
            return [self.conversations[cid] for cid in conversation_ids if cid in self.conversations]
        
        # Return all active conversations
        return list(self.conversations.values())
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationContext]:
        """
        Get a specific conversation
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            The conversation context or None if not found
        """
        return self.conversations.get(conversation_id)
    
    def _handle_request_response(self, context: ConversationContext, message: ProtocolMessage) -> bool:
        """Handle a message in a request-response conversation"""
        # Simple request-response pattern
        # Update state based on message type
        if message.message_type == MessageType.REQUEST:
            context.state["last_request"] = message.message_id
            context.state["request_time"] = time.time()
        
        elif message.message_type == MessageType.RESPONSE:
            # Check if this is a response to the last request
            last_request = context.state.get("last_request")
            if last_request and message.metadata.get("parent_message_id") == last_request:
                context.state["last_response"] = message.message_id
                context.state["response_time"] = time.time()
        
        return True
    
    def _handle_broadcast(self, context: ConversationContext, message: ProtocolMessage) -> bool:
        """Handle a message in a broadcast conversation"""
        # Broadcast pattern - ensure message goes to all participants
        if message.recipients and "ALL" not in message.recipients:
            # Add all participants as recipients
            all_recipients = set(message.recipients)
            for participant in context.participants:
                if participant != message.sender.agent_id:
                    all_recipients.add(participant)
            
            message.recipients = list(all_recipients)
        
        return True
    
    def _handle_subscription(self, context: ConversationContext, message: ProtocolMessage) -> bool:
        """Handle a message in a subscription conversation"""
        # Subscription pattern
        if message.message_type == MessageType.REQUEST:
            # Check if this is a subscription request
            if message.content.get("action") == "subscribe":
                # Add subscriber
                subscriber = message.sender.agent_id
                if "subscribers" not in context.state:
                    context.state["subscribers"] = []
                
                if subscriber not in context.state["subscribers"]:
                    context.state["subscribers"].append(subscriber)
                    
                    # Make sure they're a participant
                    self.add_participant(context.conversation_id, subscriber)
            
            # Check if this is an unsubscribe request
            elif message.content.get("action") == "unsubscribe":
                # Remove subscriber
                subscriber = message.sender.agent_id
                if "subscribers" in context.state and subscriber in context.state["subscribers"]:
                    context.state["subscribers"].remove(subscriber)
        
        elif message.message_type == MessageType.BROADCAST:
            # Ensure message goes to all subscribers
            if "subscribers" in context.state and context.state["subscribers"]:
                all_recipients = set(message.recipients) if message.recipients else set()
                for subscriber in context.state["subscribers"]:
                    if subscriber != message.sender.agent_id:
                        all_recipients.add(subscriber)
                
                message.recipients = list(all_recipients)
        
        return True
    
    def _handle_negotiation(self, context: ConversationContext, message: ProtocolMessage) -> bool:
        """Handle a message in a negotiation conversation"""
        # Negotiation pattern
        if "stage" not in context.state:
            context.state["stage"] = "proposal"
        
        if message.message_type == MessageType.REQUEST:
            # Check if this is a proposal
            if context.state["stage"] == "proposal" and message.content.get("proposal"):
                context.state["current_proposal"] = message.content["proposal"]
                context.state["proposed_by"] = message.sender.agent_id
                context.state["proposal_time"] = time.time()
                context.state["stage"] = "consideration"
        
        elif message.message_type == MessageType.RESPONSE:
            # Check if this is a response to a proposal
            if context.state["stage"] == "consideration" and context.state.get("current_proposal"):
                response_type = message.content.get("response")
                
                if response_type == "accept":
                    # Record acceptance
                    if "acceptances" not in context.state:
                        context.state["acceptances"] = []
                    
                    context.state["acceptances"].append(message.sender.agent_id)
                    
                    # Check if all participants have accepted
                    if set(context.state["acceptances"]) == set(context.participants) - {context.state["proposed_by"]}:
                        context.state["stage"] = "accepted"
                
                elif response_type == "reject":
                    # Record rejection
                    if "rejections" not in context.state:
                        context.state["rejections"] = []
                    
                    context.state["rejections"].append(message.sender.agent_id)
                    
                    # If anyone rejects, the proposal is rejected
                    context.state["stage"] = "rejected"
                
                elif response_type == "counter":
                    # Record counter proposal
                    context.state["counter_proposal"] = message.content.get("counter")
                    context.state["counter_by"] = message.sender.agent_id
                    context.state["stage"] = "counter"
        
        return True
    
    def _handle_voting(self, context: ConversationContext, message: ProtocolMessage) -> bool:
        """Handle a message in a voting conversation"""
        # Voting pattern
        if "stage" not in context.state:
            context.state["stage"] = "proposal"
        
        if message.message_type == MessageType.REQUEST:
            # Check if this is a proposal
            if context.state["stage"] == "proposal" and message.content.get("proposal"):
                context.state["current_proposal"] = message.content["proposal"]
                context.state["proposed_by"] = message.sender.agent_id
                context.state["stage"] = "voting"
                context.state["votes"] = {}
                context.state["vote_deadline"] = message.content.get("vote_deadline")
        
        elif message.message_type == MessageType.RESPONSE:
            # Check if this is a vote
            if context.state["stage"] == "voting" and message.content.get("vote") is not None:
                # Record vote
                context.state["votes"][message.sender.agent_id] = message.content["vote"]
                
                # Check if all participants have voted
                if set(context.state["votes"].keys()) == set(context.participants) - {context.state["proposed_by"]}:
                    # Count votes
                    yes_votes = sum(1 for v in context.state["votes"].values() if v)
                    no_votes = sum(1 for v in context.state["votes"].values() if not v)
                    
                    # Decision based on majority
                    if yes_votes > no_votes:
                        context.state["stage"] = "approved"
                        context.state["result"] = True
                    else:
                        context.state["stage"] = "rejected"
                        context.state["result"] = False
                    
                    # Broadcast result
                    self._broadcast_voting_result(context)
        
        return True
    
    def _broadcast_voting_result(self, context: ConversationContext):
        """Broadcast voting result to all participants"""
        # Create result message
        message = {
            "sender": {
                "agent_id": "conversation_manager",
                "agent_type": "system"
            },
            "recipients": context.participants,
            "message_type": MessageType.BROADCAST.value,
            "priority": MessagePriority.MEDIUM.value,
            "content": {
                "topic": "voting_result",
                "proposal": context.state.get("current_proposal"),
                "result": context.state.get("result"),
                "yes_votes": sum(1 for v in context.state["votes"].values() if v),
                "no_votes": sum(1 for v in context.state["votes"].values() if not v),
                "abstentions": len(context.participants) - len(context.state["votes"]) - 1  # -1 for proposer
            },
            "metadata": {
                "conversation_id": context.conversation_id
            }
        }
        
        # Send message
        self.server.message_broker.route_message(message)
    
    def _handle_delegation(self, context: ConversationContext, message: ProtocolMessage) -> bool:
        """Handle a message in a delegation conversation"""
        # Delegation pattern
        if message.message_type == MessageType.REQUEST:
            # Check if this is a delegation request
            if message.content.get("action") == "delegate":
                context.state["delegated_task"] = message.content.get("task")
                context.state["delegated_by"] = message.sender.agent_id
                context.state["delegated_to"] = message.recipients[0] if message.recipients else None
                context.state["delegation_time"] = time.time()
        
        elif message.message_type == MessageType.RESPONSE:
            # Check if this is a response to a delegation
            if context.state.get("delegated_task") and message.sender.agent_id == context.state.get("delegated_to"):
                context.state["delegation_result"] = message.content.get("result")
                context.state["delegation_completed"] = time.time()
        
        return True
    
    def _handle_consultation(self, context: ConversationContext, message: ProtocolMessage) -> bool:
        """Handle a message in a consultation conversation"""
        # Consultation pattern
        if message.message_type == MessageType.REQUEST:
            # Check if this is a consultation request
            if message.content.get("action") == "consult":
                context.state["consultation_topic"] = message.content.get("topic")
                context.state["consulted_by"] = message.sender.agent_id
                context.state["consultation_experts"] = message.recipients
                context.state["consultation_time"] = time.time()
                context.state["responses"] = {}
        
        elif message.message_type == MessageType.RESPONSE:
            # Check if this is a response to a consultation
            if context.state.get("consultation_topic") and message.sender.agent_id in context.state.get("consultation_experts", []):
                # Record response
                context.state["responses"][message.sender.agent_id] = message.content.get("opinion")
                
                # Check if all experts have responded
                if set(context.state["responses"].keys()) == set(context.state["consultation_experts"]):
                    context.state["consultation_completed"] = time.time()
                    
                    # Notify the consulter
                    self._notify_consultation_complete(context)
        
        return True
    
    def _notify_consultation_complete(self, context: ConversationContext):
        """Notify consulter that all experts have responded"""
        # Create notification message
        message = {
            "sender": {
                "agent_id": "conversation_manager",
                "agent_type": "system"
            },
            "recipients": [context.state["consulted_by"]],
            "message_type": MessageType.RESPONSE.value,
            "priority": MessagePriority.MEDIUM.value,
            "content": {
                "topic": "consultation_complete",
                "consultation_topic": context.state.get("consultation_topic"),
                "responses": context.state.get("responses")
            },
            "metadata": {
                "conversation_id": context.conversation_id
            }
        }
        
        # Send message
        self.server.message_broker.route_message(message)


class NegotiationProtocol:
    """
    Implements the negotiation protocol for agent-to-agent negotiations.
    
    This protocol allows agents to negotiate task allocation, priorities,
    and other decisions through a structured process.
    """
    
    def __init__(self):
        """Initialize the negotiation protocol"""
        self.server = get_server()
        self.conversation_manager = ConversationManager()
        self.active_negotiations: Dict[str, Dict[str, Any]] = {}  # negotiation_id -> negotiation_state
    
    def start_negotiation(self, initiator: str, participants: List[str], topic: str, 
                         proposal: Dict[str, Any], timeout: Optional[float] = None) -> str:
        """
        Start a new negotiation
        
        Args:
            initiator: Agent ID of the initiator
            participants: List of participant agent IDs
            topic: Topic of the negotiation
            proposal: Initial proposal
            timeout: Optional timeout in seconds
            
        Returns:
            The negotiation ID
        """
        # Create a conversation for the negotiation
        conversation_id = self.conversation_manager.create_conversation(
            initiator=initiator,
            participants=participants,
            pattern=CommunicationPattern.NEGOTIATION,
            topic=topic
        )
        
        # Set up negotiation state
        negotiation_state = {
            "conversation_id": conversation_id,
            "initiator": initiator,
            "participants": participants,
            "topic": topic,
            "initial_proposal": proposal,
            "current_proposal": proposal,
            "proposed_by": initiator,
            "stage": "proposal",
            "started_at": time.time(),
            "responses": {},
            "counter_proposals": [],
            "rounds": 0,
            "max_rounds": 3  # Default limit on negotiation rounds
        }
        
        # Set timeout if provided
        if timeout:
            negotiation_state["timeout"] = time.time() + timeout
        
        # Store negotiation state
        self.active_negotiations[conversation_id] = negotiation_state
        
        # Send initial proposal to all participants
        self._send_proposal(conversation_id, initiator, participants, proposal)
        
        logger.info(f"Started negotiation {conversation_id} on '{topic}'")
        return conversation_id
    
    def respond_to_proposal(self, negotiation_id: str, agent_id: str, response: str, 
                           counter_proposal: Optional[Dict[str, Any]] = None) -> bool:
        """
        Respond to a negotiation proposal
        
        Args:
            negotiation_id: The negotiation ID
            agent_id: The responding agent ID
            response: 'accept', 'reject', or 'counter'
            counter_proposal: Optional counter proposal if response is 'counter'
            
        Returns:
            True if successful, False otherwise
        """
        if negotiation_id not in self.active_negotiations:
            logger.warning(f"Unknown negotiation: {negotiation_id}")
            return False
        
        negotiation = self.active_negotiations[negotiation_id]
        
        # Check if agent is a participant
        if agent_id not in negotiation["participants"]:
            logger.warning(f"Agent {agent_id} is not a participant in negotiation {negotiation_id}")
            return False
        
        # Check if negotiation is still active
        if negotiation["stage"] not in ["proposal", "consideration"]:
            logger.warning(f"Negotiation {negotiation_id} is not in active stage: {negotiation['stage']}")
            return False
        
        # Record response
        negotiation["responses"][agent_id] = response
        
        # Handle response
        if response == "accept":
            self._handle_acceptance(negotiation_id, agent_id)
        
        elif response == "reject":
            self._handle_rejection(negotiation_id, agent_id)
        
        elif response == "counter":
            if not counter_proposal:
                logger.warning(f"Counter proposal missing for negotiation {negotiation_id}")
                return False
            
            self._handle_counter_proposal(negotiation_id, agent_id, counter_proposal)
        
        else:
            logger.warning(f"Invalid response '{response}' for negotiation {negotiation_id}")
            return False
        
        return True
    
    def get_negotiation_state(self, negotiation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of a negotiation
        
        Args:
            negotiation_id: The negotiation ID
            
        Returns:
            The negotiation state or None if not found
        """
        return self.active_negotiations.get(negotiation_id)
    
    def close_negotiation(self, negotiation_id: str, result: str, final_agreement: Optional[Dict[str, Any]] = None) -> bool:
        """
        Close a negotiation
        
        Args:
            negotiation_id: The negotiation ID
            result: 'agreement', 'rejected', or 'timeout'
            final_agreement: The final agreement if result is 'agreement'
            
        Returns:
            True if successful, False otherwise
        """
        if negotiation_id not in self.active_negotiations:
            return False
        
        negotiation = self.active_negotiations[negotiation_id]
        
        # Update state
        negotiation["stage"] = "closed"
        negotiation["result"] = result
        negotiation["closed_at"] = time.time()
        
        if result == "agreement" and final_agreement:
            negotiation["final_agreement"] = final_agreement
        
        # Notify all participants
        self._send_negotiation_result(negotiation_id, result, final_agreement)
        
        # Close conversation
        self.conversation_manager.close_conversation(negotiation_id)
        
        logger.info(f"Closed negotiation {negotiation_id} with result '{result}'")
        return True
    
    def _send_proposal(self, negotiation_id: str, sender: str, recipients: List[str], proposal: Dict[str, Any]):
        """Send a proposal to negotiation participants"""
        # Create proposal message
        message = {
            "sender": {
                "agent_id": sender,
                "agent_type": self.server.agent_registry.get_agent_identity(sender).agent_type if self.server.agent_registry.get_agent_identity(sender) else "unknown"
            },
            "recipients": recipients,
            "message_type": MessageType.REQUEST.value,
            "priority": MessagePriority.MEDIUM.value,
            "content": {
                "action": "proposal",
                "proposal": proposal
            },
            "metadata": {
                "conversation_id": negotiation_id,
                "requires_response": True
            }
        }
        
        # Send message
        self.server.message_broker.route_message(message)
    
    def _handle_acceptance(self, negotiation_id: str, agent_id: str):
        """Handle an acceptance response"""
        negotiation = self.active_negotiations[negotiation_id]
        
        # Check if all participants have accepted
        remaining = set(negotiation["participants"]) - set(negotiation["responses"].keys())
        
        if not remaining:
            # All participants have responded
            acceptances = [a for a, r in negotiation["responses"].items() if r == "accept"]
            
            if len(acceptances) == len(negotiation["participants"]) - 1:  # All except proposer
                # Agreement reached
                self.close_negotiation(negotiation_id, "agreement", negotiation["current_proposal"])
            else:
                # No agreement - move to next round if possible
                self._start_next_round(negotiation_id)
    
    def _handle_rejection(self, negotiation_id: str, agent_id: str):
        """Handle a rejection response"""
        negotiation = self.active_negotiations[negotiation_id]
        
        # Check if all participants have responded
        remaining = set(negotiation["participants"]) - set(negotiation["responses"].keys())
        
        if not remaining:
            # All participants have responded - move to next round if possible
            self._start_next_round(negotiation_id)
    
    def _handle_counter_proposal(self, negotiation_id: str, agent_id: str, counter_proposal: Dict[str, Any]):
        """Handle a counter proposal"""
        negotiation = self.active_negotiations[negotiation_id]
        
        # Add counter proposal
        negotiation["counter_proposals"].append({
            "proposal": counter_proposal,
            "proposed_by": agent_id,
            "time": time.time()
        })
        
        # Check if all participants have responded
        remaining = set(negotiation["participants"]) - set(negotiation["responses"].keys())
        
        if not remaining:
            # All participants have responded - move to next round if possible
            self._start_next_round(negotiation_id)
    
    def _start_next_round(self, negotiation_id: str):
        """Start the next round of negotiation if possible"""
        negotiation = self.active_negotiations[negotiation_id]
        
        # Check if we've reached the round limit
        if negotiation["rounds"] >= negotiation["max_rounds"]:
            # No agreement possible
            self.close_negotiation(negotiation_id, "rejected")
            return
        
        # Increment round count
        negotiation["rounds"] += 1
        
        # Check if there are counter proposals
        if not negotiation["counter_proposals"]:
            # No counter proposals - no agreement possible
            self.close_negotiation(negotiation_id, "rejected")
            return
        
        # Choose the most promising counter proposal
        # In a real implementation, this would consider various factors
        # For simplicity, we'll just take the most recent one
        counter = negotiation["counter_proposals"][-1]
        
        # Update current proposal
        negotiation["current_proposal"] = counter["proposal"]
        negotiation["proposed_by"] = counter["proposed_by"]
        
        # Reset responses
        negotiation["responses"] = {}
        
        # Send the new proposal to all participants except the proposer
        recipients = [p for p in negotiation["participants"] if p != counter["proposed_by"]]
        self._send_proposal(negotiation_id, counter["proposed_by"], recipients, counter["proposal"])
    
    def _send_negotiation_result(self, negotiation_id: str, result: str, agreement: Optional[Dict[str, Any]]):
        """Send negotiation result to all participants"""
        negotiation = self.active_negotiations[negotiation_id]
        
        # Create result message
        message = {
            "sender": {
                "agent_id": "negotiation_protocol",
                "agent_type": "system"
            },
            "recipients": negotiation["participants"],
            "message_type": MessageType.BROADCAST.value,
            "priority": MessagePriority.MEDIUM.value,
            "content": {
                "action": "negotiation_result",
                "result": result,
                "agreement": agreement,
                "rounds": negotiation["rounds"]
            },
            "metadata": {
                "conversation_id": negotiation_id
            }
        }
        
        # Send message
        self.server.message_broker.route_message(message)


class ConsensusProtocol:
    """
    Implements the consensus protocol for collective decision making.
    
    This protocol allows a group of agents to reach consensus on decisions
    through voting and other consensus mechanisms.
    """
    
    def __init__(self):
        """Initialize the consensus protocol"""
        self.server = get_server()
        self.conversation_manager = ConversationManager()
        self.active_votes: Dict[str, Dict[str, Any]] = {}  # vote_id -> vote_state
    
    def start_vote(self, initiator: str, participants: List[str], topic: str, 
                  proposal: Dict[str, Any], vote_type: str = "simple_majority",
                  timeout: Optional[float] = None) -> str:
        """
        Start a new vote
        
        Args:
            initiator: Agent ID of the initiator
            participants: List of participant agent IDs
            topic: Topic of the vote
            proposal: Proposal to vote on
            vote_type: Type of voting mechanism (simple_majority, unanimous, weighted)
            timeout: Optional timeout in seconds
            
        Returns:
            The vote ID
        """
        # Create a conversation for the vote
        conversation_id = self.conversation_manager.create_conversation(
            initiator=initiator,
            participants=participants,
            pattern=CommunicationPattern.VOTING,
            topic=topic
        )
        
        # Set up vote state
        vote_state = {
            "conversation_id": conversation_id,
            "initiator": initiator,
            "participants": participants,
            "topic": topic,
            "proposal": proposal,
            "vote_type": vote_type,
            "stage": "voting",
            "started_at": time.time(),
            "votes": {},
            "vote_weights": {p: 1.0 for p in participants}  # Default equal weights
        }
        
        # Set timeout if provided
        if timeout:
            vote_state["timeout"] = time.time() + timeout
        
        # Store vote state
        self.active_votes[conversation_id] = vote_state
        
        # Send vote request to all participants
        self._send_vote_request(conversation_id, initiator, participants, proposal, timeout)
        
        logger.info(f"Started vote {conversation_id} on '{topic}'")
        return conversation_id
    
    def cast_vote(self, vote_id: str, agent_id: str, vote: bool, reason: Optional[str] = None) -> bool:
        """
        Cast a vote
        
        Args:
            vote_id: The vote ID
            agent_id: The voting agent ID
            vote: True for Yes, False for No
            reason: Optional reason for the vote
            
        Returns:
            True if successful, False otherwise
        """
        if vote_id not in self.active_votes:
            logger.warning(f"Unknown vote: {vote_id}")
            return False
        
        vote_state = self.active_votes[vote_id]
        
        # Check if agent is a participant
        if agent_id not in vote_state["participants"]:
            logger.warning(f"Agent {agent_id} is not a participant in vote {vote_id}")
            return False
        
        # Check if vote is still active
        if vote_state["stage"] != "voting":
            logger.warning(f"Vote {vote_id} is not in voting stage: {vote_state['stage']}")
            return False
        
        # Record vote
        vote_state["votes"][agent_id] = {
            "vote": vote,
            "reason": reason,
            "time": time.time()
        }
        
        logger.info(f"Recorded vote from {agent_id} in vote {vote_id}: {'Yes' if vote else 'No'}")
        
        # Check if all votes are in
        if len(vote_state["votes"]) == len(vote_state["participants"]):
            # All votes received - tally results
            self._tally_votes(vote_id)
        
        return True
    
    def set_vote_weights(self, vote_id: str, weights: Dict[str, float]) -> bool:
        """
        Set weights for a weighted vote
        
        Args:
            vote_id: The vote ID
            weights: Dict mapping agent IDs to vote weights
            
        Returns:
            True if successful, False otherwise
        """
        if vote_id not in self.active_votes:
            return False
        
        vote_state = self.active_votes[vote_id]
        
        # Check if vote type is weighted
        if vote_state["vote_type"] != "weighted":
            logger.warning(f"Cannot set weights for non-weighted vote {vote_id}")
            return False
        
        # Check if vote is still active
        if vote_state["stage"] != "voting":
            logger.warning(f"Cannot set weights for vote {vote_id} in stage {vote_state['stage']}")
            return False
        
        # Update weights
        for agent_id, weight in weights.items():
            if agent_id in vote_state["participants"]:
                vote_state["vote_weights"][agent_id] = weight
        
        return True
    
    def get_vote_state(self, vote_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of a vote
        
        Args:
            vote_id: The vote ID
            
        Returns:
            The vote state or None if not found
        """
        return self.active_votes.get(vote_id)
    
    def close_vote(self, vote_id: str, force_result: Optional[bool] = None) -> bool:
        """
        Close a vote
        
        Args:
            vote_id: The vote ID
            force_result: Optional forced result (True for approved, False for rejected)
            
        Returns:
            True if successful, False otherwise
        """
        if vote_id not in self.active_votes:
            return False
        
        vote_state = self.active_votes[vote_id]
        
        # Tally votes if not already done
        if "result" not in vote_state and force_result is None:
            self._tally_votes(vote_id)
        
        # Set forced result if provided
        if force_result is not None:
            vote_state["result"] = force_result
            vote_state["forced"] = True
        
        # Update state
        vote_state["stage"] = "closed"
        vote_state["closed_at"] = time.time()
        
        # Notify all participants
        self._send_vote_result(vote_id)
        
        # Close conversation
        self.conversation_manager.close_conversation(vote_id)
        
        logger.info(f"Closed vote {vote_id} with result: {'approved' if vote_state['result'] else 'rejected'}")
        return True
    
    def _send_vote_request(self, vote_id: str, initiator: str, participants: List[str], 
                          proposal: Dict[str, Any], timeout: Optional[float] = None):
        """Send a vote request to participants"""
        # Create vote request message
        message = {
            "sender": {
                "agent_id": initiator,
                "agent_type": self.server.agent_registry.get_agent_identity(initiator).agent_type if self.server.agent_registry.get_agent_identity(initiator) else "unknown"
            },
            "recipients": participants,
            "message_type": MessageType.REQUEST.value,
            "priority": MessagePriority.MEDIUM.value,
            "content": {
                "action": "vote",
                "proposal": proposal,
                "timeout": timeout
            },
            "metadata": {
                "conversation_id": vote_id,
                "requires_response": True
            }
        }
        
        # Send message
        self.server.message_broker.route_message(message)
    
    def _tally_votes(self, vote_id: str):
        """Tally votes and determine result"""
        vote_state = self.active_votes[vote_id]
        
        # Get vote type
        vote_type = vote_state["vote_type"]
        
        if vote_type == "simple_majority":
            # Count yes and no votes
            yes_votes = sum(1 for v in vote_state["votes"].values() if v["vote"])
            no_votes = sum(1 for v in vote_state["votes"].values() if not v["vote"])
            
            # Determine result (tie goes to rejection)
            result = yes_votes > no_votes
        
        elif vote_type == "unanimous":
            # All must agree
            result = all(v["vote"] for v in vote_state["votes"].values())
        
        elif vote_type == "weighted":
            # Calculate weighted sum
            weighted_yes = sum(vote_state["vote_weights"][agent_id] for agent_id, v in vote_state["votes"].items() if v["vote"])
            weighted_no = sum(vote_state["vote_weights"][agent_id] for agent_id, v in vote_state["votes"].items() if not v["vote"])
            
            # Determine result (tie goes to rejection)
            result = weighted_yes > weighted_no
        
        else:
            # Default to simple majority
            yes_votes = sum(1 for v in vote_state["votes"].values() if v["vote"])
            no_votes = sum(1 for v in vote_state["votes"].values() if not v["vote"])
            result = yes_votes > no_votes
        
        # Record result
        vote_state["result"] = result
        vote_state["stage"] = "tallied"
        
        # Calculate vote statistics
        vote_state["statistics"] = {
            "participants": len(vote_state["participants"]),
            "votes_cast": len(vote_state["votes"]),
            "yes_votes": sum(1 for v in vote_state["votes"].values() if v["vote"]),
            "no_votes": sum(1 for v in vote_state["votes"].values() if not v["vote"])
        }
        
        if vote_type == "weighted":
            vote_state["statistics"]["weighted_yes"] = sum(vote_state["vote_weights"][agent_id] for agent_id, v in vote_state["votes"].items() if v["vote"])
            vote_state["statistics"]["weighted_no"] = sum(vote_state["vote_weights"][agent_id] for agent_id, v in vote_state["votes"].items() if not v["vote"])
        
        # Close the vote
        self.close_vote(vote_id)
    
    def _send_vote_result(self, vote_id: str):
        """Send vote result to all participants"""
        vote_state = self.active_votes[vote_id]
        
        # Create result message
        message = {
            "sender": {
                "agent_id": "consensus_protocol",
                "agent_type": "system"
            },
            "recipients": vote_state["participants"],
            "message_type": MessageType.BROADCAST.value,
            "priority": MessagePriority.MEDIUM.value,
            "content": {
                "action": "vote_result",
                "result": vote_state["result"],
                "statistics": vote_state["statistics"],
                "topic": vote_state["topic"],
                "proposal": vote_state["proposal"]
            },
            "metadata": {
                "conversation_id": vote_id
            }
        }
        
        # Send message
        self.server.message_broker.route_message(message)


class CollaborationCoordinator:
    """
    Coordinates collaborative work between agents.
    
    This component facilitates collaboration patterns like expert consultation,
    peer review, and collaborative problem solving.
    """
    
    def __init__(self):
        """Initialize the collaboration coordinator"""
        self.server = get_server()
        self.conversation_manager = ConversationManager()
        self.active_collaborations: Dict[str, Dict[str, Any]] = {}  # collaboration_id -> state
    
    def start_consultation(self, requester: str, experts: List[str], topic: str, 
                         query: Dict[str, Any], timeout: Optional[float] = None) -> str:
        """
        Start an expert consultation
        
        Args:
            requester: Agent ID requesting consultation
            experts: List of expert agent IDs
            topic: Topic of the consultation
            query: Consultation query
            timeout: Optional timeout in seconds
            
        Returns:
            The consultation ID
        """
        # Create a conversation for the consultation
        conversation_id = self.conversation_manager.create_conversation(
            initiator=requester,
            participants=experts + [requester],
            pattern=CommunicationPattern.CONSULTATION,
            topic=topic
        )
        
        # Set up consultation state
        consultation_state = {
            "conversation_id": conversation_id,
            "requester": requester,
            "experts": experts,
            "topic": topic,
            "query": query,
            "type": "consultation",
            "stage": "requesting",
            "started_at": time.time(),
            "responses": {},
            "aggregated_response": None
        }
        
        # Set timeout if provided
        if timeout:
            consultation_state["timeout"] = time.time() + timeout
        
        # Store consultation state
        self.active_collaborations[conversation_id] = consultation_state
        
        # Send consultation request to experts
        self._send_consultation_request(conversation_id, requester, experts, query)
        
        logger.info(f"Started consultation {conversation_id} on '{topic}'")
        return conversation_id
    
    def start_peer_review(self, author: str, reviewers: List[str], topic: str, 
                         work: Dict[str, Any], criteria: Optional[List[str]] = None,
                         timeout: Optional[float] = None) -> str:
        """
        Start a peer review process
        
        Args:
            author: Agent ID of the author
            reviewers: List of reviewer agent IDs
            topic: Topic of the review
            work: Work to be reviewed
            criteria: Optional list of review criteria
            timeout: Optional timeout in seconds
            
        Returns:
            The review ID
        """
        # Create a conversation for the review
        conversation_id = self.conversation_manager.create_conversation(
            initiator=author,
            participants=reviewers + [author],
            pattern=CommunicationPattern.CONSULTATION,  # Reuse consultation pattern
            topic=topic
        )
        
        # Default criteria if not provided
        if not criteria:
            criteria = ["correctness", "completeness", "clarity"]
        
        # Set up review state
        review_state = {
            "conversation_id": conversation_id,
            "author": author,
            "reviewers": reviewers,
            "topic": topic,
            "work": work,
            "criteria": criteria,
            "type": "peer_review",
            "stage": "reviewing",
            "started_at": time.time(),
            "reviews": {},
            "aggregated_review": None
        }
        
        # Set timeout if provided
        if timeout:
            review_state["timeout"] = time.time() + timeout
        
        # Store review state
        self.active_collaborations[conversation_id] = review_state
        
        # Send review request to reviewers
        self._send_review_request(conversation_id, author, reviewers, work, criteria)
        
        logger.info(f"Started peer review {conversation_id} on '{topic}'")
        return conversation_id
    
    def start_collaborative_solve(self, initiator: str, collaborators: List[str], topic: str, 
                                 problem: Dict[str, Any], approach: Optional[str] = None,
                                 timeout: Optional[float] = None) -> str:
        """
        Start a collaborative problem solving process
        
        Args:
            initiator: Agent ID of the initiator
            collaborators: List of collaborator agent IDs
            topic: Topic of the problem
            problem: Problem definition
            approach: Optional approach to solving the problem
            timeout: Optional timeout in seconds
            
        Returns:
            The collaboration ID
        """
        # Create a conversation for the collaboration
        conversation_id = self.conversation_manager.create_conversation(
            initiator=initiator,
            participants=collaborators + [initiator],
            pattern=CommunicationPattern.BROADCAST,  # Use broadcast for collaboration
            topic=topic
        )
        
        # Set up collaboration state
        collaboration_state = {
            "conversation_id": conversation_id,
            "initiator": initiator,
            "collaborators": collaborators,
            "topic": topic,
            "problem": problem,
            "approach": approach,
            "type": "collaborative_solve",
            "stage": "planning",
            "started_at": time.time(),
            "contributions": {},
            "solution": None
        }
        
        # Set timeout if provided
        if timeout:
            collaboration_state["timeout"] = time.time() + timeout
        
        # Store collaboration state
        self.active_collaborations[conversation_id] = collaboration_state
        
        # Send collaboration request to collaborators
        self._send_collaboration_request(conversation_id, initiator, collaborators, problem, approach)
        
        logger.info(f"Started collaborative problem solving {conversation_id} on '{topic}'")
        return conversation_id
    
    def submit_expert_response(self, consultation_id: str, expert: str, response: Dict[str, Any]) -> bool:
        """
        Submit an expert response to a consultation
        
        Args:
            consultation_id: The consultation ID
            expert: The expert agent ID
            response: The expert response
            
        Returns:
            True if successful, False otherwise
        """
        if consultation_id not in self.active_collaborations:
            logger.warning(f"Unknown consultation: {consultation_id}")
            return False
        
        collaboration = self.active_collaborations[consultation_id]
        
        # Check if this is a consultation
        if collaboration["type"] != "consultation":
            logger.warning(f"Collaboration {consultation_id} is not a consultation")
            return False
        
        # Check if agent is an expert
        if expert not in collaboration["experts"]:
            logger.warning(f"Agent {expert} is not an expert in consultation {consultation_id}")
            return False
        
        # Record response
        collaboration["responses"][expert] = {
            "response": response,
            "time": time.time()
        }
        
        logger.info(f"Recorded expert response from {expert} in consultation {consultation_id}")
        
        # Check if all experts have responded
        if len(collaboration["responses"]) == len(collaboration["experts"]):
            # All responses received - aggregate and notify requester
            self._aggregate_consultation_responses(consultation_id)
        
        return True
    
    def submit_review(self, review_id: str, reviewer: str, review: Dict[str, Any]) -> bool:
        """
        Submit a peer review
        
        Args:
            review_id: The review ID
            reviewer: The reviewer agent ID
            review: The review content
            
        Returns:
            True if successful, False otherwise
        """
        if review_id not in self.active_collaborations:
            logger.warning(f"Unknown review: {review_id}")
            return False
        
        collaboration = self.active_collaborations[review_id]
        
        # Check if this is a peer review
        if collaboration["type"] != "peer_review":
            logger.warning(f"Collaboration {review_id} is not a peer review")
            return False
        
        # Check if agent is a reviewer
        if reviewer not in collaboration["reviewers"]:
            logger.warning(f"Agent {reviewer} is not a reviewer in review {review_id}")
            return False
        
        # Record review
        collaboration["reviews"][reviewer] = {
            "review": review,
            "time": time.time()
        }
        
        logger.info(f"Recorded review from {reviewer} in peer review {review_id}")
        
        # Check if all reviewers have submitted
        if len(collaboration["reviews"]) == len(collaboration["reviewers"]):
            # All reviews received - aggregate and notify author
            self._aggregate_peer_reviews(review_id)
        
        return True
    
    def submit_contribution(self, collaboration_id: str, contributor: str, 
                          contribution: Dict[str, Any], stage: str) -> bool:
        """
        Submit a contribution to collaborative problem solving
        
        Args:
            collaboration_id: The collaboration ID
            contributor: The contributor agent ID
            contribution: The contribution content
            stage: The collaboration stage this contribution belongs to
            
        Returns:
            True if successful, False otherwise
        """
        if collaboration_id not in self.active_collaborations:
            logger.warning(f"Unknown collaboration: {collaboration_id}")
            return False
        
        collaboration = self.active_collaborations[collaboration_id]
        
        # Check if this is a collaborative solve
        if collaboration["type"] != "collaborative_solve":
            logger.warning(f"Collaboration {collaboration_id} is not a collaborative solve")
            return False
        
        # Check if agent is a collaborator or initiator
        if contributor not in collaboration["collaborators"] and contributor != collaboration["initiator"]:
            logger.warning(f"Agent {contributor} is not a collaborator in {collaboration_id}")
            return False
        
        # Record contribution
        if contributor not in collaboration["contributions"]:
            collaboration["contributions"][contributor] = []
        
        collaboration["contributions"][contributor].append({
            "contribution": contribution,
            "stage": stage,
            "time": time.time()
        })
        
        # Update collaboration stage if needed
        if stage != collaboration["stage"]:
            # Only allow progression through stages, not regression
            stages = ["planning", "analysis", "solution_development", "verification", "completed"]
            current_idx = stages.index(collaboration["stage"]) if collaboration["stage"] in stages else 0
            new_idx = stages.index(stage) if stage in stages else 0
            
            if new_idx > current_idx:
                collaboration["stage"] = stage
                # Notify all participants of stage change
                self._notify_collaboration_stage_change(collaboration_id, stage)
        
        logger.info(f"Recorded contribution from {contributor} in collaboration {collaboration_id}")
        
        # If stage is "completed", finalize the solution
        if stage == "completed":
            self._finalize_collaborative_solution(collaboration_id)
        
        return True
    
    def get_collaboration_state(self, collaboration_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of a collaboration
        
        Args:
            collaboration_id: The collaboration ID
            
        Returns:
            The collaboration state or None if not found
        """
        return self.active_collaborations.get(collaboration_id)
    
    def close_collaboration(self, collaboration_id: str) -> bool:
        """
        Close a collaboration
        
        Args:
            collaboration_id: The collaboration ID
            
        Returns:
            True if successful, False otherwise
        """
        if collaboration_id not in self.active_collaborations:
            return False
        
        collaboration = self.active_collaborations[collaboration_id]
        
        # Update state
        collaboration["stage"] = "closed"
        collaboration["closed_at"] = time.time()
        
        # Notify all participants
        if collaboration["type"] == "consultation":
            participants = [collaboration["requester"]] + collaboration["experts"]
        elif collaboration["type"] == "peer_review":
            participants = [collaboration["author"]] + collaboration["reviewers"]
        else:  # collaborative_solve
            participants = [collaboration["initiator"]] + collaboration["collaborators"]
        
        self._notify_collaboration_closed(collaboration_id, participants)
        
        # Close conversation
        self.conversation_manager.close_conversation(collaboration_id)
        
        logger.info(f"Closed collaboration {collaboration_id}")
        return True
    
    def _send_consultation_request(self, consultation_id: str, requester: str, experts: List[str], query: Dict[str, Any]):
        """Send a consultation request to experts"""
        # Create consultation request message
        message = {
            "sender": {
                "agent_id": requester,
                "agent_type": self.server.agent_registry.get_agent_identity(requester).agent_type if self.server.agent_registry.get_agent_identity(requester) else "unknown"
            },
            "recipients": experts,
            "message_type": MessageType.REQUEST.value,
            "priority": MessagePriority.MEDIUM.value,
            "content": {
                "action": "consult",
                "query": query
            },
            "metadata": {
                "conversation_id": consultation_id,
                "requires_response": True
            }
        }
        
        # Send message
        self.server.message_broker.route_message(message)
    
    def _send_review_request(self, review_id: str, author: str, reviewers: List[str], 
                            work: Dict[str, Any], criteria: List[str]):
        """Send a peer review request to reviewers"""
        # Create review request message
        message = {
            "sender": {
                "agent_id": author,
                "agent_type": self.server.agent_registry.get_agent_identity(author).agent_type if self.server.agent_registry.get_agent_identity(author) else "unknown"
            },
            "recipients": reviewers,
            "message_type": MessageType.REQUEST.value,
            "priority": MessagePriority.MEDIUM.value,
            "content": {
                "action": "review",
                "work": work,
                "criteria": criteria
            },
            "metadata": {
                "conversation_id": review_id,
                "requires_response": True
            }
        }
        
        # Send message
        self.server.message_broker.route_message(message)
    
    def _send_collaboration_request(self, collaboration_id: str, initiator: str, collaborators: List[str],
                                  problem: Dict[str, Any], approach: Optional[str]):
        """Send a collaboration request to collaborators"""
        # Create collaboration request message
        message = {
            "sender": {
                "agent_id": initiator,
                "agent_type": self.server.agent_registry.get_agent_identity(initiator).agent_type if self.server.agent_registry.get_agent_identity(initiator) else "unknown"
            },
            "recipients": collaborators,
            "message_type": MessageType.REQUEST.value,
            "priority": MessagePriority.MEDIUM.value,
            "content": {
                "action": "collaborate",
                "problem": problem,
                "approach": approach
            },
            "metadata": {
                "conversation_id": collaboration_id,
                "requires_response": True
            }
        }
        
        # Send message
        self.server.message_broker.route_message(message)
    
    def _aggregate_consultation_responses(self, consultation_id: str):
        """Aggregate expert responses and notify requester"""
        collaboration = self.active_collaborations[consultation_id]
        
        # Extract responses
        responses = {expert: data["response"] for expert, data in collaboration["responses"].items()}
        
        # In a real implementation, this would use a more sophisticated aggregation algorithm
        # based on the query type and response format
        # For simplicity, we'll just combine all responses
        aggregated = {
            "expert_responses": responses,
            "aggregated_highlights": self._extract_response_highlights(responses)
        }
        
        # Store aggregated response
        collaboration["aggregated_response"] = aggregated
        collaboration["stage"] = "completed"
        
        # Notify requester
        self._send_aggregated_consultation(consultation_id, collaboration["requester"], aggregated)
    
    def _extract_response_highlights(self, responses: Dict[str, Dict[str, Any]]) -> List[str]:
        """Extract highlights from expert responses"""
        # In a real implementation, this would analyze responses to find common points,
        # key insights, and important differences
        # For simplicity, we'll just collect any highlights included in the responses
        highlights = []
        for expert, response in responses.items():
            if "highlights" in response:
                if isinstance(response["highlights"], list):
                    highlights.extend(response["highlights"])
                elif isinstance(response["highlights"], str):
                    highlights.append(response["highlights"])
        
        return highlights
    
    def _send_aggregated_consultation(self, consultation_id: str, requester: str, aggregated: Dict[str, Any]):
        """Send aggregated consultation response to requester"""
        # Create consultation response message
        message = {
            "sender": {
                "agent_id": "collaboration_coordinator",
                "agent_type": "system"
            },
            "recipients": [requester],
            "message_type": MessageType.RESPONSE.value,
            "priority": MessagePriority.MEDIUM.value,
            "content": {
                "action": "consultation_result",
                "aggregated_response": aggregated
            },
            "metadata": {
                "conversation_id": consultation_id
            }
        }
        
        # Send message
        self.server.message_broker.route_message(message)
    
    def _aggregate_peer_reviews(self, review_id: str):
        """Aggregate peer reviews and notify author"""
        collaboration = self.active_collaborations[review_id]
        
        # Extract reviews
        reviews = {reviewer: data["review"] for reviewer, data in collaboration["reviews"].items()}
        
        # Aggregate reviews by criteria
        aggregated = {"by_criteria": {}}
        for criterion in collaboration["criteria"]:
            scores = []
            comments = []
            
            for reviewer, review in reviews.items():
                if criterion in review:
                    if "score" in review[criterion]:
                        scores.append(review[criterion]["score"])
                    if "comment" in review[criterion]:
                        comments.append(review[criterion]["comment"])
            
            aggregated["by_criteria"][criterion] = {
                "average_score": sum(scores) / len(scores) if scores else None,
                "comments": comments
            }
        
        # Add overall assessment
        overall_scores = []
        overall_comments = []
        
        for reviewer, review in reviews.items():
            if "overall" in review:
                if "score" in review["overall"]:
                    overall_scores.append(review["overall"]["score"])
                if "comment" in review["overall"]:
                    overall_comments.append(review["overall"]["comment"])
        
        aggregated["overall"] = {
            "average_score": sum(overall_scores) / len(overall_scores) if overall_scores else None,
            "comments": overall_comments
        }
        
        # Store aggregated review
        collaboration["aggregated_review"] = aggregated
        collaboration["stage"] = "completed"
        
        # Notify author
        self._send_aggregated_review(review_id, collaboration["author"], aggregated)
    
    def _send_aggregated_review(self, review_id: str, author: str, aggregated: Dict[str, Any]):
        """Send aggregated peer review to author"""
        # Create review result message
        message = {
            "sender": {
                "agent_id": "collaboration_coordinator",
                "agent_type": "system"
            },
            "recipients": [author],
            "message_type": MessageType.RESPONSE.value,
            "priority": MessagePriority.MEDIUM.value,
            "content": {
                "action": "review_result",
                "aggregated_review": aggregated
            },
            "metadata": {
                "conversation_id": review_id
            }
        }
        
        # Send message
        self.server.message_broker.route_message(message)
    
    def _notify_collaboration_stage_change(self, collaboration_id: str, new_stage: str):
        """Notify all participants of a stage change in collaborative problem solving"""
        collaboration = self.active_collaborations[collaboration_id]
        
        # Get all participants
        participants = [collaboration["initiator"]] + collaboration["collaborators"]
        
        # Create stage change message
        message = {
            "sender": {
                "agent_id": "collaboration_coordinator",
                "agent_type": "system"
            },
            "recipients": participants,
            "message_type": MessageType.BROADCAST.value,
            "priority": MessagePriority.MEDIUM.value,
            "content": {
                "action": "stage_change",
                "new_stage": new_stage,
                "previous_stage": collaboration["stage"]
            },
            "metadata": {
                "conversation_id": collaboration_id
            }
        }
        
        # Send message
        self.server.message_broker.route_message(message)
    
    def _finalize_collaborative_solution(self, collaboration_id: str):
        """Finalize solution for collaborative problem solving"""
        collaboration = self.active_collaborations[collaboration_id]
        
        # Collect all contributions
        solution_contributions = []
        for contributor, contributions in collaboration["contributions"].items():
            for contrib in contributions:
                if contrib["stage"] == "solution_development" or contrib["stage"] == "verification":
                    if "solution_component" in contrib["contribution"]:
                        solution_contributions.append({
                            "contributor": contributor,
                            "component": contrib["contribution"]["solution_component"],
                            "time": contrib["time"]
                        })
        
        # In a real implementation, this would use a sophisticated algorithm to
        # combine solution components based on their relationships and dependencies
        # For simplicity, we'll just collect all components
        solution = {
            "components": [c["component"] for c in solution_contributions],
            "contributors": list(set(c["contributor"] for c in solution_contributions)),
            "finalized_at": time.time()
        }
        
        # Store solution
        collaboration["solution"] = solution
        collaboration["stage"] = "completed"
        
        # Notify all participants
        self._notify_solution_finalized(collaboration_id)
    
    def _notify_solution_finalized(self, collaboration_id: str):
        """Notify all participants that the solution has been finalized"""
        collaboration = self.active_collaborations[collaboration_id]
        
        # Get all participants
        participants = [collaboration["initiator"]] + collaboration["collaborators"]
        
        # Create solution finalized message
        message = {
            "sender": {
                "agent_id": "collaboration_coordinator",
                "agent_type": "system"
            },
            "recipients": participants,
            "message_type": MessageType.BROADCAST.value,
            "priority": MessagePriority.HIGH.value,
            "content": {
                "action": "solution_finalized",
                "solution": collaboration["solution"]
            },
            "metadata": {
                "conversation_id": collaboration_id
            }
        }
        
        # Send message
        self.server.message_broker.route_message(message)
    
    def _notify_collaboration_closed(self, collaboration_id: str, participants: List[str]):
        """Notify all participants that a collaboration has been closed"""
        # Create collaboration closed message
        message = {
            "sender": {
                "agent_id": "collaboration_coordinator",
                "agent_type": "system"
            },
            "recipients": participants,
            "message_type": MessageType.BROADCAST.value,
            "priority": MessagePriority.LOW.value,
            "content": {
                "action": "collaboration_closed",
                "collaboration_id": collaboration_id
            },
            "metadata": {
                "conversation_id": collaboration_id
            }
        }
        
        # Send message
        self.server.message_broker.route_message(message)


# =============================================================================
# Agent-to-Agent Protocol Components
# =============================================================================

class AgentToAgentProtocol:
    """
    Main class that implements the agent-to-agent protocol.
    
    This class provides the core functionality for agent communication,
    including message routing, conversation management, and collaboration patterns.
    """
    
    def __init__(self):
        """Initialize the agent-to-agent protocol"""
        self.server = get_server()
        self.conversation_manager = ConversationManager()
        self.negotiation_protocol = NegotiationProtocol()
        self.consensus_protocol = ConsensusProtocol()
        self.collaboration_coordinator = CollaborationCoordinator()
        
        logger.info("Agent-to-agent protocol initialized")
    
    def process_message(self, message: ProtocolMessage) -> bool:
        """
        Process a message through the appropriate protocol
        
        Args:
            message: The message to process
            
        Returns:
            True if successfully processed, False otherwise
        """
        # Check if this is a conversation message
        conversation_id = message.metadata.get("conversation_id")
        if conversation_id:
            # Get conversation if it exists
            conversation = self.conversation_manager.get_conversation(conversation_id)
            
            if conversation:
                # Process through conversation manager
                return self.conversation_manager.process_message(message)
        
        # No specific protocol applies - return True to allow default routing
        return True
    
    def create_conversation(self, initiator: str, participants: List[str], 
                          pattern: CommunicationPattern, topic: str) -> str:
        """
        Create a new conversation
        
        Args:
            initiator: Agent ID that initiated the conversation
            participants: List of participant agent IDs
            pattern: Communication pattern to use
            topic: Topic of the conversation
            
        Returns:
            The conversation ID
        """
        return self.conversation_manager.create_conversation(initiator, participants, pattern, topic)
    
    def start_negotiation(self, initiator: str, participants: List[str], topic: str, 
                         proposal: Dict[str, Any], timeout: Optional[float] = None) -> str:
        """
        Start a new negotiation
        
        Args:
            initiator: Agent ID of the initiator
            participants: List of participant agent IDs
            topic: Topic of the negotiation
            proposal: Initial proposal
            timeout: Optional timeout in seconds
            
        Returns:
            The negotiation ID
        """
        return self.negotiation_protocol.start_negotiation(initiator, participants, topic, proposal, timeout)
    
    def start_vote(self, initiator: str, participants: List[str], topic: str, 
                  proposal: Dict[str, Any], vote_type: str = "simple_majority",
                  timeout: Optional[float] = None) -> str:
        """
        Start a new vote
        
        Args:
            initiator: Agent ID of the initiator
            participants: List of participant agent IDs
            topic: Topic of the vote
            proposal: Proposal to vote on
            vote_type: Type of voting mechanism (simple_majority, unanimous, weighted)
            timeout: Optional timeout in seconds
            
        Returns:
            The vote ID
        """
        return self.consensus_protocol.start_vote(initiator, participants, topic, proposal, vote_type, timeout)
    
    def start_consultation(self, requester: str, experts: List[str], topic: str, 
                         query: Dict[str, Any], timeout: Optional[float] = None) -> str:
        """
        Start an expert consultation
        
        Args:
            requester: Agent ID requesting consultation
            experts: List of expert agent IDs
            topic: Topic of the consultation
            query: Consultation query
            timeout: Optional timeout in seconds
            
        Returns:
            The consultation ID
        """
        return self.collaboration_coordinator.start_consultation(requester, experts, topic, query, timeout)
    
    def get_active_conversations(self, agent_id: Optional[str] = None) -> List[ConversationContext]:
        """
        Get active conversations
        
        Args:
            agent_id: Optional agent ID to filter by
            
        Returns:
            List of active conversation contexts
        """
        return self.conversation_manager.get_active_conversations(agent_id)


# Singleton instance
_protocol_instance = None

def get_protocol() -> AgentToAgentProtocol:
    """
    Get the singleton instance of the agent-to-agent protocol
    
    Returns:
        The agent-to-agent protocol
    """
    global _protocol_instance
    if _protocol_instance is None:
        _protocol_instance = AgentToAgentProtocol()
    
    return _protocol_instance