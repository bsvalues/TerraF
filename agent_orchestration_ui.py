"""
Agent Orchestration UI

This module provides Streamlit UI components for interacting with the Agent Orchestrator.
"""

import streamlit as st
import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_agent_controller():
    """
    Load the Agent Controller.
    
    Returns:
        AgentController instance
    """
    try:
        from services.agent_orchestrator import get_agent_controller
        from services.ai_models.ai_service import AIService
        
        # Create AI Service
        ai_service = AIService()
        
        # Get Agent Controller
        agent_controller = get_agent_controller(ai_service)
        
        return agent_controller
    except Exception as e:
        logger.error(f"Error loading agent controller: {str(e)}")
        return None

def initialize_agent_orchestration_state():
    """Initialize session state for agent orchestration."""
    if 'agent_orchestration_initialized' not in st.session_state:
        st.session_state.agent_orchestration_initialized = False
        st.session_state.agent_controller = None
        st.session_state.agent_status = None
        st.session_state.active_tasks = {}
        st.session_state.code_analysis_results = None
        st.session_state.security_analysis_results = None
        st.session_state.architecture_analysis_results = None
        st.session_state.database_analysis_results = None

def render_agent_orchestration_ui():
    """Render the agent orchestration UI."""
    # Initialize state
    initialize_agent_orchestration_state()
    
    st.header("🤖 Agent Orchestration System")
    
    # Load Agent Controller if not loaded
    if st.session_state.agent_controller is None:
        with st.spinner("Loading Agent Controller..."):
            st.session_state.agent_controller = load_agent_controller()
    
    # Check if Agent Controller loaded successfully
    if st.session_state.agent_controller is None:
        st.error("Failed to load Agent Controller. Please check the logs for details.")
        return
    
    # Initialize Agent System if not initialized
    if not st.session_state.agent_orchestration_initialized:
        with st.spinner("Initializing Agent System..."):
            init_result = st.session_state.agent_controller.initialize_agent_system()
            
            if init_result['status'] in ['success', 'already_initialized']:
                st.session_state.agent_orchestration_initialized = True
                st.session_state.agent_status = init_result
                st.success(init_result['message'])
            else:
                st.error(f"Failed to initialize Agent System: {init_result.get('message', 'Unknown error')}")
                return
    
    # Display Agent System Status
    with st.expander("Agent System Status", expanded=False):
        if st.session_state.agent_status:
            # Refresh status
            status_result = st.session_state.agent_controller.get_agent_status()
            if status_result['status'] == 'success':
                st.session_state.agent_status = status_result
                
                # Display agent pools
                st.subheader("Agent Pools")
                for pool_name, pool_info in status_result.get('agent_pools', {}).items():
                    st.markdown(f"**{pool_name}**: {pool_info.get('size', 0)} agents")
                
                # Display agents
                st.subheader("Agents")
                agent_data = []
                for agent_id, agent_info in status_result.get('agents', {}).items():
                    agent_data.append({
                        "ID": agent_id[:8] + "...",
                        "Name": agent_info.get('name', 'Unknown'),
                        "Status": agent_info.get('status', 'Unknown'),
                        "Tasks Processed": agent_info.get('task_count', 0),
                        "Errors": agent_info.get('error_count', 0)
                    })
                
                if agent_data:
                    st.dataframe(agent_data)
                else:
                    st.info("No agents found.")
            else:
                st.warning(f"Failed to get agent status: {status_result.get('message', 'Unknown error')}")
    
    # Create tabs for different analysis types
    tabs = st.tabs([
        "Code Analysis", 
        "Security Analysis", 
        "Architecture Analysis", 
        "Database Analysis"
    ])
    
    # Code Analysis Tab
    with tabs[0]:
        render_code_analysis_tab()
    
    # Security Analysis Tab
    with tabs[1]:
        render_security_analysis_tab()
    
    # Architecture Analysis Tab
    with tabs[2]:
        render_architecture_analysis_tab()
    
    # Database Analysis Tab
    with tabs[3]:
        render_database_analysis_tab()

def render_code_analysis_tab():
    """Render the code analysis tab."""
    st.subheader("Code Analysis")
    st.markdown("""
    This tab allows you to analyze code quality, complexity, and patterns using AI agents.
    """)
    
    # Code input
    code = st.text_area(
        "Enter code to analyze:",
        height=200,
        help="Paste the code you want to analyze"
    )
    
    # Analysis options
    col1, col2 = st.columns(2)
    
    with col1:
        language = st.selectbox(
            "Language:",
            ["python", "javascript", "typescript", "java", "c#", "go", "ruby", "php", "other"],
            help="Select the programming language"
        )
    
    with col2:
        analysis_type = st.selectbox(
            "Analysis Type:",
            ["review", "complexity", "documentation", "best_practices"],
            help="Select the type of analysis to perform"
        )
    
    # Submit button
    if st.button("Analyze Code", key="analyze_code_button", type="primary"):
        if not code:
            st.warning("Please enter code to analyze.")
            return
        
        with st.spinner("Analyzing code..."):
            # Dispatch task to agent
            result = st.session_state.agent_controller.analyze_code(
                code=code,
                language=language,
                analysis_type=analysis_type,
                wait=True,
                timeout=60.0
            )
            
            # Store result
            st.session_state.code_analysis_results = result
    
    # Display results
    if st.session_state.code_analysis_results:
        with st.expander("Analysis Results", expanded=True):
            result = st.session_state.code_analysis_results
            
            if result['status'] == 'success':
                # Display analysis results
                analysis_results = result.get('results', {})
                
                if isinstance(analysis_results, dict):
                    st.json(analysis_results)
                else:
                    st.write(analysis_results)
                
                # Add download button for JSON results
                if isinstance(analysis_results, dict):
                    st.download_button(
                        "Download Results (JSON)",
                        data=json.dumps(analysis_results, indent=2),
                        file_name="code_analysis_results.json",
                        mime="application/json"
                    )
            else:
                st.error(f"Analysis failed: {result.get('error', 'Unknown error')}")

def render_security_analysis_tab():
    """Render the security analysis tab."""
    st.subheader("Security Analysis")
    st.markdown("""
    This tab allows you to analyze code for security vulnerabilities using AI agents.
    """)
    
    # Code input
    code = st.text_area(
        "Enter code to analyze for security issues:",
        height=200,
        help="Paste the code you want to analyze for security vulnerabilities"
    )
    
    # Analysis options
    col1, col2 = st.columns(2)
    
    with col1:
        language = st.selectbox(
            "Language:",
            ["python", "javascript", "typescript", "java", "c#", "go", "ruby", "php", "other"],
            help="Select the programming language",
            key="security_language"
        )
    
    with col2:
        scan_type = st.selectbox(
            "Scan Type:",
            ["comprehensive", "quick", "focused"],
            help="Select the type of security scan to perform"
        )
    
    # Submit button
    if st.button("Analyze Security", key="analyze_security_button", type="primary"):
        if not code:
            st.warning("Please enter code to analyze for security issues.")
            return
        
        with st.spinner("Analyzing code security..."):
            # Dispatch task to agent
            result = st.session_state.agent_controller.analyze_security(
                code=code,
                language=language,
                scan_type=scan_type,
                wait=True,
                timeout=60.0
            )
            
            # Store result
            st.session_state.security_analysis_results = result
    
    # Display results
    if st.session_state.security_analysis_results:
        with st.expander("Security Analysis Results", expanded=True):
            result = st.session_state.security_analysis_results
            
            if result['status'] == 'success':
                # Display security analysis results
                security_results = result.get('results', {})
                
                if isinstance(security_results, dict):
                    st.json(security_results)
                else:
                    st.write(security_results)
                
                # Add download button for JSON results
                if isinstance(security_results, dict):
                    st.download_button(
                        "Download Security Results (JSON)",
                        data=json.dumps(security_results, indent=2),
                        file_name="security_analysis_results.json",
                        mime="application/json"
                    )
            else:
                st.error(f"Security analysis failed: {result.get('error', 'Unknown error')}")

def render_architecture_analysis_tab():
    """Render the architecture analysis tab."""
    st.subheader("Architecture Analysis")
    st.markdown("""
    This tab allows you to analyze repository architecture using AI agents.
    """)
    
    # Repository path input
    repo_path = st.text_input(
        "Repository Path:",
        value=st.session_state.get('repo_path', ''),
        help="Enter the path to the repository to analyze"
    )
    
    # Analysis options
    col1, col2 = st.columns(2)
    
    with col1:
        framework = st.text_input(
            "Framework (optional):",
            help="Enter the framework used in the repository (e.g., React, Django, Spring)"
        )
    
    with col2:
        languages = st.multiselect(
            "Languages:",
            ["python", "javascript", "typescript", "java", "c#", "go", "ruby", "php", "other"],
            help="Select the programming languages used in the repository"
        )
    
    # Submit button
    if st.button("Analyze Architecture", key="analyze_architecture_button", type="primary"):
        if not repo_path or not os.path.exists(repo_path):
            st.warning("Please enter a valid repository path.")
            return
        
        with st.spinner("Analyzing repository architecture..."):
            # Dispatch task to agent
            result = st.session_state.agent_controller.analyze_repository_architecture(
                repo_path=repo_path,
                framework=framework if framework else None,
                languages=languages if languages else None,
                wait=True,
                timeout=120.0
            )
            
            # Store result
            st.session_state.architecture_analysis_results = result
    
    # Display results
    if st.session_state.architecture_analysis_results:
        with st.expander("Architecture Analysis Results", expanded=True):
            result = st.session_state.architecture_analysis_results
            
            if result['status'] == 'success':
                # Display architecture analysis results
                architecture_results = result.get('results', {})
                
                if isinstance(architecture_results, dict):
                    # Display directory structure
                    if 'directory_structure' in architecture_results:
                        st.subheader("Directory Structure")
                        st.json(architecture_results['directory_structure'])
                    
                    # Display architecture analysis
                    if 'architecture_analysis' in architecture_results:
                        st.subheader("Architecture Analysis")
                        st.json(architecture_results['architecture_analysis'])
                    
                    # Add download button for JSON results
                    st.download_button(
                        "Download Architecture Results (JSON)",
                        data=json.dumps(architecture_results, indent=2),
                        file_name="architecture_analysis_results.json",
                        mime="application/json"
                    )
                else:
                    st.write(architecture_results)
            else:
                st.error(f"Architecture analysis failed: {result.get('error', 'Unknown error')}")

def render_database_analysis_tab():
    """Render the database analysis tab."""
    st.subheader("Database Analysis")
    st.markdown("""
    This tab allows you to analyze database schemas and usage patterns using AI agents.
    """)
    
    # Get repository path from session state
    repo_path = st.session_state.get('repo_path', '')
    
    # Database type selection
    db_type = st.selectbox(
        "Database Type:",
        ["postgresql", "mysql", "sqlite", "mongodb", "other"],
        help="Select the database type to analyze"
    )
    
    # Schema files input
    st.subheader("Schema Files")
    schema_files_str = st.text_area(
        "Enter paths to schema files (one per line):",
        height=100,
        help="Enter the paths to database schema files (SQL files, migration files, etc.)"
    )
    
    # ORM files input
    st.subheader("ORM Files")
    orm_files_str = st.text_area(
        "Enter paths to ORM files (one per line):",
        height=100,
        help="Enter the paths to ORM files (models, entities, etc.)"
    )
    
    # Parse file paths
    schema_files = [line.strip() for line in schema_files_str.split('\n') if line.strip()]
    orm_files = [line.strip() for line in orm_files_str.split('\n') if line.strip()]
    
    # Submit button
    if st.button("Analyze Database", key="analyze_database_button", type="primary"):
        if not schema_files and not orm_files:
            st.warning("Please enter at least one schema file or ORM file path.")
            return
        
        # Check if files exist
        missing_files = []
        for file_path in schema_files + orm_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            st.warning(f"The following files were not found: {', '.join(missing_files)}")
            return
        
        with st.spinner("Analyzing database structures..."):
            # Dispatch task to agent
            result = st.session_state.agent_controller.analyze_database_structures(
                schema_files=schema_files,
                orm_files=orm_files,
                db_type=db_type,
                wait=True,
                timeout=60.0
            )
            
            # Store result
            st.session_state.database_analysis_results = result
    
    # Display results
    if st.session_state.database_analysis_results:
        with st.expander("Database Analysis Results", expanded=True):
            result = st.session_state.database_analysis_results
            
            if result['status'] == 'success':
                # Display database analysis results
                database_results = result.get('results', {})
                
                if isinstance(database_results, dict):
                    st.json(database_results)
                    
                    # Add download button for JSON results
                    st.download_button(
                        "Download Database Results (JSON)",
                        data=json.dumps(database_results, indent=2),
                        file_name="database_analysis_results.json",
                        mime="application/json"
                    )
                else:
                    st.write(database_results)
            else:
                st.error(f"Database analysis failed: {result.get('error', 'Unknown error')}")

def add_agent_orchestration_to_app():
    """Add agent orchestration to the app."""
    render_agent_orchestration_ui()