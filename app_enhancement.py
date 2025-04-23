"""
App Enhancement Module for Code Deep Dive Analyzer

This module integrates the intelligent agent system with the Streamlit application,
providing a user interface for interacting with the AI agents and visualizing their
results.
"""

import streamlit as st
import os
import json
import time
import uuid
import logging
import threading
import queue
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict

# Import protocol server for agent management
from protocol_server import (
    ProtocolMessage, MessageType, MessagePriority, AgentIdentity, AgentCategory,
    Task, get_server, start_server, stop_server
)

# Import specialized agents for registration
from specialized_agents import register_all_agents

# Import continuous learning system
from continuous_learning import get_learning_system

# Import agent communication protocol
from agent_communication import get_protocol

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentSystemUI:
    """
    User interface for interacting with the agent system.
    
    This class provides UI components for:
    - Starting and stopping the agent system
    - Monitoring agent activity
    - Viewing agent communications
    - Inspecting learning updates
    - Triggering agent tasks
    """
    
    def __init__(self):
        """Initialize the agent system UI"""
        self.server = None
        self.agents = {}
        self.learning_system = None
        self.protocol = None
        self.system_running = False
        
        # Initialize session state for UI
        if "agent_system_initialized" not in st.session_state:
            st.session_state.agent_system_initialized = False
        
        if "agent_system_running" not in st.session_state:
            st.session_state.agent_system_running = False
        
        if "agents_registered" not in st.session_state:
            st.session_state.agents_registered = False
        
        if "active_conversations" not in st.session_state:
            st.session_state.active_conversations = []
        
        if "agent_activity_log" not in st.session_state:
            st.session_state.agent_activity_log = []
        
        if "learning_updates" not in st.session_state:
            st.session_state.learning_updates = []
    
    def render_agent_system_controls(self):
        """Render controls for starting and stopping the agent system"""
        st.header("Intelligent Agent System")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not st.session_state.agent_system_running:
                if st.button("🚀 Start Agent System", type="primary"):
                    self.start_agent_system()
            else:
                if st.button("🛑 Stop Agent System", type="primary"):
                    self.stop_agent_system()
        
        with col2:
            if st.session_state.agent_system_running and not st.session_state.agents_registered:
                if st.button("👥 Register Agents"):
                    self.register_agents()
            elif st.session_state.agent_system_running and st.session_state.agents_registered:
                st.success("Agents registered and running")
    
    def render_agent_status_dashboard(self):
        """Render a dashboard showing the status of all agents"""
        if not st.session_state.agent_system_running:
            st.info("Agent system is not running. Start it to see agent status.")
            return
        
        st.subheader("Agent Status Dashboard")
        
        # Get server instance
        server = get_server()
        
        # Get agent registry
        agent_registry = server.agent_registry
        
        # Display agent status
        if agent_registry.agents:
            agent_data = []
            for agent_id, agent in agent_registry.agents.items():
                agent_data.append({
                    "Agent ID": agent_id,
                    "Type": agent.agent_type,
                    "Status": agent.status,
                    "Last Active": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(agent.last_seen))
                })
            
            st.dataframe(agent_data)
        else:
            st.info("No agents registered yet.")
    
    def render_agent_activity_log(self):
        """Render a log of recent agent activity"""
        if not st.session_state.agent_system_running:
            return
        
        st.subheader("Agent Activity Log")
        
        # For a real implementation, this would fetch actual agent activity
        # For this example, we'll use a simulated log in session state
        
        if st.button("Refresh Activity Log"):
            # Simulate fetching new activity
            self._update_activity_log()
        
        # Display activity log
        if st.session_state.agent_activity_log:
            for entry in reversed(st.session_state.agent_activity_log[-10:]):  # Show last 10 entries
                st.markdown(f"**{entry['time']}** - {entry['agent']}: {entry['activity']}")
        else:
            st.info("No agent activity recorded yet.")
    
    def render_conversation_monitor(self):
        """Render a monitor for agent conversations"""
        if not st.session_state.agent_system_running or not st.session_state.agents_registered:
            return
        
        st.subheader("Agent Conversations")
        
        # Get protocol instance
        protocol = get_protocol()
        
        # Get active conversations
        if st.button("Refresh Conversations"):
            conversations = protocol.get_active_conversations()
            st.session_state.active_conversations = [
                {
                    "id": conv.conversation_id,
                    "initiator": conv.initiator,
                    "participants": conv.participants,
                    "pattern": conv.pattern.value,
                    "topic": conv.topic,
                    "message_count": conv.message_count,
                    "started": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(conv.started_at))
                }
                for conv in conversations
            ]
        
        # Display conversations
        if st.session_state.active_conversations:
            for conv in st.session_state.active_conversations:
                with st.expander(f"{conv['pattern']}: {conv['topic']}"):
                    st.markdown(f"**ID:** {conv['id']}")
                    st.markdown(f"**Initiator:** {conv['initiator']}")
                    st.markdown(f"**Participants:** {', '.join(conv['participants'])}")
                    st.markdown(f"**Started:** {conv['started']}")
                    st.markdown(f"**Messages:** {conv['message_count']}")
        else:
            st.info("No active conversations.")
    
    def render_learning_updates(self):
        """Render recent learning updates"""
        if not st.session_state.agent_system_running or not st.session_state.agents_registered:
            return
        
        st.subheader("Learning Updates")
        
        # For a real implementation, this would fetch actual learning updates
        # For this example, we'll use simulated updates in session state
        
        if st.button("Refresh Learning Updates"):
            # Simulate fetching learning updates
            self._update_learning_updates()
        
        # Display learning updates
        if st.session_state.learning_updates:
            for update in st.session_state.learning_updates:
                with st.expander(f"{update['capability']}: {update['effectiveness']:.2f} confidence"):
                    st.markdown(f"**ID:** {update['id']}")
                    st.markdown(f"**Agent Types:** {', '.join(update['agent_types'])}")
                    st.markdown(f"**Pattern:** {update['pattern']}")
                    st.markdown(f"**Created:** {update['created']}")
        else:
            st.info("No learning updates recorded yet.")
    
    def render_task_triggers(self):
        """Render UI for triggering agent tasks"""
        if not st.session_state.agent_system_running or not st.session_state.agents_registered:
            return
        
        st.subheader("Trigger Agent Tasks")
        
        # Get server instance
        server = get_server()
        
        # Get agent registry
        agent_registry = server.agent_registry
        
        # Create agent selection
        agents = list(agent_registry.agents.keys())
        if not agents:
            st.info("No agents available for tasks.")
            return
        
        selected_agent = st.selectbox("Select Agent", agents)
        
        # Get agent identity
        agent_identity = agent_registry.get_agent_identity(selected_agent)
        if not agent_identity:
            st.error(f"Agent {selected_agent} not found.")
            return
        
        # Create task type selection based on agent type
        task_types = self._get_agent_task_types(agent_identity.agent_type)
        selected_task = st.selectbox("Select Task", task_types)
        
        # Create task input form
        with st.form("task_input_form"):
            task_description = st.text_input("Task Description")
            
            # Custom inputs based on task type
            task_data = {}
            
            if "code_analysis" in selected_task:
                code = st.text_area("Code to Analyze", height=200)
                language = st.selectbox("Language", ["python", "javascript", "java", "csharp", "go"])
                task_data = {"code": code, "language": language}
            
            elif "pattern_detection" in selected_task:
                code = st.text_area("Code to Analyze", height=200)
                language = st.selectbox("Language", ["python", "javascript", "java", "csharp", "go"])
                task_data = {"code": code, "language": language}
            
            elif "dependency" in selected_task:
                code_files = st.text_area("Code Files (JSON format)", height=200)
                language = st.selectbox("Language", ["python", "javascript", "java", "csharp", "go"])
                try:
                    task_data = {
                        "code_files": json.loads(code_files),
                        "language": language
                    }
                except json.JSONDecodeError:
                    st.error("Invalid JSON format for code files.")
                    task_data = {"language": language}
            
            elif "consultation" in selected_task:
                query = st.text_area("Consultation Query", height=100)
                task_data = {"query": query}
            
            # Submit button
            submitted = st.form_submit_button("Submit Task")
            
            if submitted:
                if not task_description:
                    st.error("Task description is required.")
                else:
                    # Submit task
                    self._submit_agent_task(selected_agent, selected_task, task_description, task_data)
                    st.success(f"Task submitted to {selected_agent}.")
    
    def render_agent_interaction_tab(self):
        """Render a complete agent interaction tab"""
        st.title("🤖 Agent System")
        
        self.render_agent_system_controls()
        
        # Only show these sections if the agent system is running
        if st.session_state.agent_system_running:
            st.markdown("---")
            self.render_agent_status_dashboard()
            
            st.markdown("---")
            self.render_agent_activity_log()
            
            # Only show these sections if agents are registered
            if st.session_state.agents_registered:
                st.markdown("---")
                self.render_conversation_monitor()
                
                st.markdown("---")
                self.render_learning_updates()
                
                st.markdown("---")
                self.render_task_triggers()
    
    def start_agent_system(self):
        """Start the agent system"""
        try:
            # Start the protocol server
            self.server = start_server()
            self.system_running = True
            st.session_state.agent_system_running = True
            
            # Initialize learning system
            self.learning_system = get_learning_system()
            
            # Initialize protocol
            self.protocol = get_protocol()
            
            logger.info("Agent system started")
            st.success("Agent system started successfully!")
        except Exception as e:
            logger.error(f"Error starting agent system: {e}")
            st.error(f"Error starting agent system: {str(e)}")
    
    def stop_agent_system(self):
        """Stop the agent system"""
        try:
            # Stop the protocol server
            stop_server()
            self.system_running = False
            st.session_state.agent_system_running = False
            st.session_state.agents_registered = False
            
            logger.info("Agent system stopped")
            st.success("Agent system stopped successfully!")
        except Exception as e:
            logger.error(f"Error stopping agent system: {e}")
            st.error(f"Error stopping agent system: {str(e)}")
    
    def register_agents(self):
        """Register specialized agents"""
        try:
            # Register all agents
            self.agents = register_all_agents()
            st.session_state.agents_registered = True
            
            logger.info("Agents registered")
            st.success("Agents registered successfully!")
        except Exception as e:
            logger.error(f"Error registering agents: {e}")
            st.error(f"Error registering agents: {str(e)}")
    
    def _get_agent_task_types(self, agent_type: str) -> List[str]:
        """Get task types for a specific agent type"""
        # This would be based on the actual agent capabilities
        # For this example, we'll use predefined task types
        
        if "code_quality" in agent_type.lower():
            return [
                "style_analysis", 
                "bug_detection", 
                "security_analysis", 
                "performance_analysis", 
                "generate_tests"
            ]
        
        elif "architecture" in agent_type.lower():
            return [
                "detect_patterns", 
                "detect_antipatterns", 
                "analyze_architecture", 
                "map_dependencies", 
                "detect_circular_dependencies"
            ]
        
        elif "database" in agent_type.lower():
            return [
                "analyze_schema", 
                "optimize_queries", 
                "detect_redundancies"
            ]
        
        elif "documentation" in agent_type.lower():
            return [
                "generate_docs", 
                "review_docs", 
                "create_diagrams"
            ]
        
        elif "agent_readiness" in agent_type.lower():
            return [
                "evaluate_readiness", 
                "suggest_improvements"
            ]
        
        elif "learning_coordinator" in agent_type.lower():
            return [
                "process_feedback", 
                "identify_patterns", 
                "evaluate_model"
            ]
        
        # Default task types
        return ["analyze", "evaluate", "recommend"]
    
    def _submit_agent_task(self, agent_id: str, task_type: str, description: str, input_data: Dict[str, Any]):
        """Submit a task to an agent"""
        # Get server instance
        server = get_server()
        
        # Create task
        task = Task(
            task_type=task_type,
            description=description,
            input_data=input_data,
            assigned_agent=agent_id
        )
        
        # Submit task
        server.task_orchestrator.submit_task(task)
        
        # Add to activity log
        current_time = time.strftime('%H:%M:%S')
        st.session_state.agent_activity_log.append({
            "agent": agent_id,
            "activity": f"Assigned task: {task_type} - {description}",
            "time": current_time
        })
    
    def _update_activity_log(self):
        """Update the agent activity log with simulated data"""
        # In a real implementation, this would fetch actual agent activity
        # For this example, we'll simulate some activity
        
        # Get current time
        current_time = time.strftime('%H:%M:%S')
        
        # Add some simulated activity
        if self.agents:
            agent_ids = list(self.agents.keys())
            import random
            
            # Simulate 1-3 new activities
            for _ in range(random.randint(1, 3)):
                agent_id = random.choice(agent_ids)
                
                activities = [
                    "Processing task...",
                    "Analyzing code structure",
                    "Detecting design patterns",
                    "Evaluating dependency graph",
                    "Sending consultation request",
                    "Responding to negotiation",
                    "Applying learning update",
                    "Collaborating on problem solution"
                ]
                
                activity = random.choice(activities)
                
                st.session_state.agent_activity_log.append({
                    "agent": agent_id,
                    "activity": activity,
                    "time": current_time
                })
    
    def _update_learning_updates(self):
        """Update the learning updates with simulated data"""
        # In a real implementation, this would fetch actual learning updates
        # For this example, we'll simulate some updates
        
        # Get current time
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Simulate 1-2 new learning updates
        if self.agents:
            import random
            
            for _ in range(random.randint(1, 2)):
                capabilities = [
                    "code_analysis",
                    "pattern_detection",
                    "dependency_analysis",
                    "performance_optimization",
                    "test_generation",
                    "security_analysis"
                ]
                
                agent_types = ["CODE_QUALITY", "ARCHITECTURE", "DATABASE", "DOCUMENTATION"]
                
                patterns = [
                    "Improved code structure detection algorithm",
                    "Enhanced pattern recognition threshold",
                    "Refined security vulnerability detection rules",
                    "Optimized database schema analysis approach",
                    "Enhanced test coverage estimation formula"
                ]
                
                st.session_state.learning_updates.append({
                    "id": str(uuid.uuid4()),
                    "capability": random.choice(capabilities),
                    "agent_types": random.sample(agent_types, random.randint(1, 3)),
                    "pattern": random.choice(patterns),
                    "effectiveness": random.uniform(0.7, 0.95),
                    "confidence": random.uniform(0.7, 0.9),
                    "created": current_time
                })


class EnhancedAnalyzerUI:
    """
    Enhanced UI for the Code Deep Dive Analyzer.
    
    This class extends the existing Streamlit UI with:
    - Agent-assisted analysis
    - Interactive agent consultations
    - Visualization of agent insights
    """
    
    def __init__(self):
        """Initialize the enhanced analyzer UI"""
        self.agent_system_ui = AgentSystemUI()
    
    def render_enhanced_analyzer_tab(self):
        """Render the enhanced analyzer tab"""
        st.title("🔍 Enhanced Analysis")
        
        if not st.session_state.get("agent_system_running", False):
            st.warning("Please start the agent system in the Agent System tab to use enhanced analysis features.")
            return
        
        if not st.session_state.get("agents_registered", False):
            st.warning("Please register agents in the Agent System tab to use enhanced analysis features.")
            return
        
        # Enhanced analysis features
        st.subheader("Agent-Assisted Analysis")
        
        analysis_types = [
            "Comprehensive Code Quality Analysis",
            "Architecture Evaluation",
            "Dependency Graph Analysis",
            "Security Vulnerability Scan",
            "Performance Optimization Assessment",
            "Test Coverage Evaluation"
        ]
        
        selected_analysis = st.selectbox("Select Analysis Type", analysis_types)
        
        # Repository input
        repo_url = st.text_input("GitHub Repository URL", placeholder="https://github.com/username/repository")
        
        col1, col2 = st.columns(2)
        with col1:
            branch = st.text_input("Branch", "main")
        with col2:
            depth = st.slider("Analysis Depth", 1, 5, 3)
        
        # Analysis options
        st.subheader("Analysis Options")
        
        options_col1, options_col2 = st.columns(2)
        
        with options_col1:
            include_tests = st.checkbox("Include tests", value=False)
            analyze_dependencies = st.checkbox("Analyze dependencies", value=True)
        
        with options_col2:
            detect_patterns = st.checkbox("Detect design patterns", value=True)
            evaluate_security = st.checkbox("Evaluate security", value=True)
        
        # Start analysis button
        if st.button("Start Agent-Assisted Analysis", type="primary"):
            if not repo_url:
                st.error("Please enter a GitHub repository URL.")
            else:
                self._simulate_agent_analysis(repo_url, branch, selected_analysis, depth)
    
    def render_agent_consultation_tab(self):
        """Render the agent consultation tab"""
        st.title("💬 Agent Consultation")
        
        if not st.session_state.get("agent_system_running", False):
            st.warning("Please start the agent system in the Agent System tab to use consultation features.")
            return
        
        if not st.session_state.get("agents_registered", False):
            st.warning("Please register agents in the Agent System tab to use consultation features.")
            return
        
        # Agent consultation features
        st.subheader("Consult with Specialized Agents")
        
        # Initialize consultation state
        if "consultation_history" not in st.session_state:
            st.session_state.consultation_history = []
        
        if "waiting_for_response" not in st.session_state:
            st.session_state.waiting_for_response = False
        
        # Show consultation history
        for message in st.session_state.consultation_history:
            if message["sender"] == "user":
                st.markdown(f"**You:** {message['text']}")
            else:
                with st.chat_message(message["sender"]):
                    st.markdown(message["text"])
        
        # Input for new consultation
        if not st.session_state.waiting_for_response:
            consultation_question = st.text_area("Enter your question or code for analysis")
            
            consultation_type = st.radio(
                "Consultation Type",
                ["Code Quality", "Architecture", "Database", "Performance", "Security"],
                horizontal=True
            )
            
            if st.button("Submit Consultation", type="primary"):
                if not consultation_question:
                    st.error("Please enter a question or code snippet.")
                else:
                    # Add user message to history
                    st.session_state.consultation_history.append({
                        "sender": "user",
                        "text": consultation_question
                    })
                    
                    # Set waiting flag
                    st.session_state.waiting_for_response = True
                    
                    # Simulate agent response (in a real implementation, this would trigger actual agent consultation)
                    self._simulate_agent_consultation(consultation_question, consultation_type)
        else:
            # Show spinner while waiting
            with st.spinner("Agents are analyzing your request..."):
                time.sleep(3)  # Simulate processing time
                st.session_state.waiting_for_response = False
                st.rerun()
    
    def render_insight_visualization_tab(self):
        """Render the insight visualization tab"""
        st.title("📊 Agent Insights")
        
        if not st.session_state.get("agent_system_running", False):
            st.warning("Please start the agent system in the Agent System tab to use insights features.")
            return
        
        if not st.session_state.get("agents_registered", False):
            st.warning("Please register agents in the Agent System tab to use insights features.")
            return
        
        # Insight visualization features
        st.subheader("Visualized Agent Insights")
        
        # Initialize insights state
        if "agent_insights" not in st.session_state:
            st.session_state.agent_insights = []
        
        # Refresh button
        if st.button("Refresh Insights"):
            # Simulate fetching new insights (in a real implementation, this would fetch actual agent insights)
            self._simulate_agent_insights()
        
        # Show visualizations of insights
        if st.session_state.agent_insights:
            for i, insight in enumerate(st.session_state.agent_insights):
                with st.expander(f"Insight: {insight['title']}", expanded=i==0):
                    st.markdown(f"**Source:** {insight['source']}")
                    st.markdown(f"**Description:** {insight['description']}")
                    
                    if 'chart_type' in insight and insight['chart_type'] == 'bar':
                        # Create bar chart
                        import plotly.express as px
                        df = px.data.medals_long()
                        fig = px.bar(df, x="nation", y="count", color="medal", title=insight['title'])
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif 'chart_type' in insight and insight['chart_type'] == 'network':
                        # Create network visualization
                        import networkx as nx
                        import plotly.graph_objects as go
                        
                        # Create a sample graph
                        G = nx.random_geometric_graph(20, 0.3)
                        
                        # Create positions for nodes
                        pos = nx.spring_layout(G)
                        
                        # Create edges
                        edge_x = []
                        edge_y = []
                        for edge in G.edges():
                            x0, y0 = pos[edge[0]]
                            x1, y1 = pos[edge[1]]
                            edge_x.extend([x0, x1, None])
                            edge_y.extend([y0, y1, None])

                        edge_trace = go.Scatter(
                            x=edge_x, y=edge_y,
                            line=dict(width=0.5, color='#888'),
                            hoverinfo='none',
                            mode='lines')

                        # Create nodes
                        node_x = []
                        node_y = []
                        for node in G.nodes():
                            x, y = pos[node]
                            node_x.append(x)
                            node_y.append(y)

                        node_trace = go.Scatter(
                            x=node_x, y=node_y,
                            mode='markers',
                            hoverinfo='text',
                            marker=dict(
                                showscale=True,
                                colorscale='YlGnBu',
                                size=10,
                                colorbar=dict(
                                    thickness=15,
                                    title='Node Connections',
                                    xanchor='left',
                                    titleside='right'
                                )
                            )
                        )
                        
                        # Color nodes by degree
                        node_adjacencies = []
                        node_text = []
                        for node, adjacencies in enumerate(G.adjacency()):
                            node_adjacencies.append(len(adjacencies[1]))
                            node_text.append(f'Node {node} has {len(adjacencies[1])} connections')

                        node_trace.marker.color = node_adjacencies
                        node_trace.text = node_text
                        
                        # Create figure
                        fig = go.Figure(data=[edge_trace, node_trace],
                                        layout=go.Layout(
                                            title=insight['title'],
                                            showlegend=False,
                                            hovermode='closest',
                                            margin=dict(b=20,l=5,r=5,t=40),
                                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                                        )
                                       )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    else:
                        # Simple text insight
                        st.markdown(f"**Key Points:**")
                        for point in insight.get('key_points', []):
                            st.markdown(f"- {point}")
        else:
            st.info("No agent insights available. Run an analysis or refresh insights.")
    
    def _simulate_agent_analysis(self, repo_url, branch, analysis_type, depth):
        """Simulate agent analysis (in a real implementation, this would trigger actual agent analysis)"""
        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simulate analysis stages
        stages = [
            "Cloning repository...",
            "Analyzing code structure...",
            "Detecting design patterns...",
            "Evaluating dependencies...",
            "Assessing code quality...",
            "Generating recommendations..."
        ]
        
        for i, stage in enumerate(stages):
            # Update progress
            progress = (i + 1) / len(stages)
            progress_bar.progress(progress)
            status_text.text(stage)
            
            # Simulate processing time
            time.sleep(1)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Show success message
        st.success(f"Analysis of {repo_url} completed successfully!")
        
        # Show simulated results
        st.subheader("Analysis Results")
        
        # Create tabs for different result sections
        tabs = st.tabs(["Summary", "Code Quality", "Architecture", "Dependencies", "Recommendations"])
        
        with tabs[0]:  # Summary
            st.markdown("### Summary")
            st.markdown(f"**Repository:** {repo_url}")
            st.markdown(f"**Branch:** {branch}")
            st.markdown(f"**Analysis Type:** {analysis_type}")
            st.markdown(f"**Analysis Depth:** {depth}")
            
            # Overall scores
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Code Quality Score", "83/100", "+5")
            with col2:
                st.metric("Technical Debt", "Medium", "-10%")
            with col3:
                st.metric("Maintainability", "Good", "+8%")
        
        with tabs[1]:  # Code Quality
            st.markdown("### Code Quality Analysis")
            
            # Code quality metrics
            metrics_col1, metrics_col2 = st.columns(2)
            
            with metrics_col1:
                st.markdown("**Complexity Metrics:**")
                st.markdown("- Average Cyclomatic Complexity: 12.3")
                st.markdown("- Maximum Nesting Depth: 4")
                st.markdown("- Average Function Length: 28 lines")
            
            with metrics_col2:
                st.markdown("**Issues Found:**")
                st.markdown("- Potential bugs: 8")
                st.markdown("- Code smell instances: 23")
                st.markdown("- Security vulnerabilities: 3")
            
            # Code quality visualization
            import plotly.graph_objects as go
            
            fig = go.Figure(data=[
                go.Bar(name='Current', x=['Bugs', 'Code Smells', 'Vulnerabilities', 'Duplications'], y=[8, 23, 3, 12]),
                go.Bar(name='Previous Analysis', x=['Bugs', 'Code Smells', 'Vulnerabilities', 'Duplications'], y=[12, 35, 5, 18])
            ])
            
            fig.update_layout(title="Code Issues Comparison", barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        
        with tabs[2]:  # Architecture
            st.markdown("### Architecture Analysis")
            
            # Architecture findings
            st.markdown("**Detected Patterns:**")
            st.markdown("- Singleton: 2 instances")
            st.markdown("- Factory Method: 3 instances")
            st.markdown("- Observer: 1 instance")
            st.markdown("- Repository: 4 instances")
            
            st.markdown("**Architecture Issues:**")
            st.markdown("- Circular dependencies: 2 cycles detected")
            st.markdown("- God classes: 3 instances")
            st.markdown("- Lack of proper layering in UI components")
            
            # Architecture visualization placeholder
            st.markdown("**Architecture Visualization:**")
            st.info("Interactive architecture visualization would be displayed here in the actual implementation.")
        
        with tabs[3]:  # Dependencies
            st.markdown("### Dependency Analysis")
            
            # Dependency metrics
            st.markdown("**Dependency Metrics:**")
            st.markdown("- Total dependencies: 45")
            st.markdown("- External dependencies: 18")
            st.markdown("- Outdated dependencies: 7")
            st.markdown("- Security vulnerabilities in dependencies: 2")
            
            # Dependency visualization
            st.markdown("**Most Central Components:**")
            
            central_components = [
                {"Component": "DataService", "Dependents": 12, "Dependencies": 5},
                {"Component": "UserManager", "Dependents": 8, "Dependencies": 3},
                {"Component": "ApiClient", "Dependents": 7, "Dependencies": 4},
                {"Component": "Logger", "Dependents": 15, "Dependencies": 1},
                {"Component": "ConfigManager", "Dependents": 10, "Dependencies": 2}
            ]
            
            st.dataframe(central_components)
        
        with tabs[4]:  # Recommendations
            st.markdown("### Agent Recommendations")
            
            # Recommendations
            with st.expander("Code Quality Recommendations", expanded=True):
                st.markdown("1. Refactor the `ProcessManager` class to reduce cyclomatic complexity")
                st.markdown("2. Fix null reference vulnerabilities in the API client")
                st.markdown("3. Add input validation to user-facing functions")
                st.markdown("4. Reduce duplicated validation logic across controllers")
            
            with st.expander("Architecture Recommendations"):
                st.markdown("1. Break circular dependency between `UserService` and `AuthService`")
                st.markdown("2. Split `DataManager` class into smaller, focused classes")
                st.markdown("3. Introduce proper separation of concerns in UI components")
                st.markdown("4. Consider adopting a clean architecture approach to improve modularity")
            
            with st.expander("Dependency Recommendations"):
                st.markdown("1. Update 7 outdated dependencies to address security vulnerabilities")
                st.markdown("2. Consider replacing custom HTTP client with standard library")
                st.markdown("3. Consolidate multiple logging libraries to a single solution")
                st.markdown("4. Add dependency injection to improve testability")
    
    def _simulate_agent_consultation(self, question, consultation_type):
        """Simulate agent consultation response"""
        # Map consultation type to agent name
        agent_name = {
            "Code Quality": "BugHunter",
            "Architecture": "PatternDetector",
            "Database": "SchemaOptimizer",
            "Performance": "PerformanceOptimizer",
            "Security": "SecurityAnalyzer"
        }[consultation_type]
        
        # Generate response based on consultation type
        if consultation_type == "Code Quality":
            response = """
            I've analyzed your code and found several quality issues:

            1. **Potential bug**: The `process_data` function doesn't check for null inputs
            2. **Code smell**: The `UserManager` class has too many responsibilities
            3. **Maintainability issue**: Complex nested conditionals in the authentication logic

            **Recommendations:**
            - Add input validation to the `process_data` function
            - Split `UserManager` into smaller, focused classes
            - Refactor authentication logic using the Strategy pattern
            """
        
        elif consultation_type == "Architecture":
            response = """
            I've analyzed your architecture and identified these patterns and issues:

            **Patterns detected:**
            - Singleton pattern in the `ConfigManager`
            - Incomplete MVC implementation in the UI components

            **Architecture issues:**
            - Circular dependency between `UserService` and `NotificationService`
            - Lack of clear layering between business logic and data access
            - Tight coupling between UI and business logic

            **Recommendations:**
            - Complete the MVC implementation to properly separate concerns
            - Break the circular dependency by introducing an event system
            - Implement a clear layering strategy (e.g., Clean Architecture)
            """
        
        elif consultation_type == "Database":
            response = """
            I've analyzed your database structure and found these issues:

            1. **Schema issue**: The `Users` table has redundant columns that should be normalized
            2. **Query performance**: The query in `getUserReports()` is inefficient due to missing indexes
            3. **Data integrity**: Missing foreign key constraints between `Orders` and `Products`

            **Recommendations:**
            - Normalize the `Users` table by creating a separate `UserProfiles` table
            - Add an index on `created_date` column in the `Reports` table
            - Add proper foreign key constraints to ensure data integrity
            """
        
        elif consultation_type == "Performance":
            response = """
            I've analyzed your code for performance issues:

            1. **O(n²) complexity** in the `findDuplicates` function
            2. **Excessive memory usage** in the data caching strategy
            3. **Inefficient resource handling** in the file processing routines

            **Optimization opportunities:**
            - Refactor the `findDuplicates` function to use a hash-based approach (O(n) complexity)
            - Implement a more efficient caching strategy with LRU eviction
            - Use streaming for file processing to reduce memory footprint
            """
        
        elif consultation_type == "Security":
            response = """
            I've analyzed your code for security vulnerabilities:

            1. **SQL Injection vulnerability** in the query builder
            2. **Insecure authentication** with plaintext password storage
            3. **Missing input validation** in API endpoints
            4. **Insecure direct object references** in the user profile handler

            **Security recommendations:**
            - Use parameterized queries for all database operations
            - Implement proper password hashing with bcrypt
            - Add comprehensive input validation to all API endpoints
            - Implement proper authorization checks for object references
            """
        
        else:
            response = "I don't have enough information to provide a consultation on this topic."
        
        # Add response to history after a delay (to simulate thinking time)
        time.sleep(2)
        
        st.session_state.consultation_history.append({
            "sender": agent_name,
            "text": response
        })
    
    def _simulate_agent_insights(self):
        """Simulate agent insights for visualization"""
        # Clear existing insights
        st.session_state.agent_insights = []
        
        # Add simulated insights
        st.session_state.agent_insights.append({
            "title": "Code Quality Distribution",
            "source": "Code Quality Agent",
            "description": "Distribution of code quality issues across different components of the system.",
            "chart_type": "bar",
            "key_points": [
                "UI components have the highest number of code smells",
                "Data access layer has the most potential bugs",
                "Authentication module has several security vulnerabilities",
                "Overall code quality has improved by 15% since last analysis"
            ]
        })
        
        st.session_state.agent_insights.append({
            "title": "Dependency Graph Analysis",
            "source": "Architecture Agent",
            "description": "Analysis of component dependencies and identification of central components.",
            "chart_type": "network",
            "key_points": [
                "Three key components form the core of the system architecture",
                "Two circular dependencies detected between service components",
                "Logger component has the highest number of dependents",
                "Authentication service has excessive outgoing dependencies"
            ]
        })
        
        st.session_state.agent_insights.append({
            "title": "Performance Hotspots",
            "source": "Performance Optimizer Agent",
            "description": "Identification of performance bottlenecks and optimization opportunities.",
            "key_points": [
                "Data processing pipeline has several O(n²) algorithms that can be optimized",
                "Memory usage spikes during large file processing",
                "Database queries in the reporting module lack proper indexing",
                "Caching strategy could be improved for better performance"
            ]
        })
        
        st.session_state.agent_insights.append({
            "title": "Security Vulnerability Assessment",
            "source": "Security Agent",
            "description": "Analysis of security vulnerabilities and recommendations for remediation.",
            "key_points": [
                "3 high-severity security vulnerabilities found in the authentication module",
                "Input validation is missing in 42% of the API endpoints",
                "Outdated dependencies with known vulnerabilities should be updated",
                "Session management implementation has security flaws"
            ]
        })


def add_agent_system_to_app():
    """Add the agent system to the Streamlit app"""
    # Initialize session state
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "Repository Analysis"
    
    # Create UI components
    agent_system_ui = AgentSystemUI()
    enhanced_analyzer_ui = EnhancedAnalyzerUI()
    
    # Add tabs for agent system components
    tabs = st.tabs([
        "Repository Analysis", 
        "Agent System", 
        "Enhanced Analysis", 
        "Agent Consultation", 
        "Agent Insights"
    ])
    
    # Repository Analysis tab (original app)
    with tabs[0]:
        if st.session_state.current_tab == "Repository Analysis":
            pass  # The original app will be rendered in the main function
    
    # Agent System tab
    with tabs[1]:
        if st.session_state.current_tab == "Agent System":
            agent_system_ui.render_agent_interaction_tab()
    
    # Enhanced Analysis tab
    with tabs[2]:
        if st.session_state.current_tab == "Enhanced Analysis":
            enhanced_analyzer_ui.render_enhanced_analyzer_tab()
    
    # Agent Consultation tab
    with tabs[3]:
        if st.session_state.current_tab == "Agent Consultation":
            enhanced_analyzer_ui.render_agent_consultation_tab()
    
    # Agent Insights tab
    with tabs[4]:
        if st.session_state.current_tab == "Agent Insights":
            enhanced_analyzer_ui.render_insight_visualization_tab()
    
    # Update current tab to match the clicked one
    tab_names = ["Repository Analysis", "Agent System", "Enhanced Analysis", "Agent Consultation", "Agent Insights"]
    for i, tab_name in enumerate(tab_names):
        if tabs[i]._active and st.session_state.current_tab != tab_name:
            st.session_state.current_tab = tab_name
            st.rerun()