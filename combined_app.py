"""
Combined Code Deep Dive Analyzer

This module provides a unified interface that combines both the original and enhanced 
versions of the Code Deep Dive Analyzer.
"""
import streamlit as st
import os
import sys
import logging
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Set up page config first
st.set_page_config(
    page_title="Code Deep Dive Analyzer",
    page_icon="🔍",
    layout="wide"
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import internal modules without page config conflicts
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import from original app
from repository_handler import clone_repository, get_repository_structure
from code_analyzer import perform_code_review
from database_analyzer import analyze_database_structures
from modularization_analyzer import analyze_modularization
from agent_readiness_analyzer import analyze_agent_readiness
from workflow_analyzer import analyze_workflow_patterns
from report_generator import generate_summary_report
from utils import save_analysis_results, load_analysis_results
import visualizations

# Import API Gateway for enhanced version
try:
    from services_connector import ServicesConnector
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False

# Import agent system enhancement (conditionally, as it may not exist yet)
try:
    from app_enhancement import add_agent_system_to_app
    AGENT_SYSTEM_AVAILABLE = True
except ImportError:
    AGENT_SYSTEM_AVAILABLE = False

# Import agent orchestration UI
try:
    from agent_orchestration_ui import add_agent_orchestration_to_app
    AGENT_ORCHESTRATION_AVAILABLE = True
except ImportError:
    AGENT_ORCHESTRATION_AVAILABLE = False

# Import workflow mapper UI
try:
    from workflow_mapper_ui import render_workflow_mapper_tab, add_workflow_mapper_tab
    WORKFLOW_MAPPER_AVAILABLE = True
except ImportError:
    WORKFLOW_MAPPER_AVAILABLE = False

# Initialize state
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = "original"

def reset_app():
    """Reset app state to initial values"""
    # Only reset if not already analyzing
    if not st.session_state.get('analyzing', False):
        # Repository settings
        st.session_state.repo_url = ""
        st.session_state.repo_branch = "main"
        st.session_state.analyze_clicked = False
        st.session_state.repo_cloned = False
        st.session_state.repo_path = None
        
        # Analysis results
        st.session_state.analyze_code = True
        st.session_state.analyze_database = True
        st.session_state.analyze_modularization = True
        st.session_state.analyze_agent_readiness = True
        
        # Results storage
        st.session_state.analysis_results = {}
        st.session_state.repo_structure = None
        st.session_state.code_review = None
        st.session_state.database_analysis = None 
        st.session_state.modularization_analysis = None
        st.session_state.agent_readiness_analysis = None
        st.session_state.workflow_patterns_analysis = None
        st.session_state.summary_report = None
        
        # UI state
        st.session_state.current_tab = "Input"

def initialize_session_state():
    """Initialize session state if not already done"""
    if 'initialized' not in st.session_state:
        reset_app()
        st.session_state.initialized = True
        st.session_state.analyzing = False
        st.session_state.analysis_complete = False

def initialize_enhanced_session_state():
    """Initialize enhanced session state if not already done"""
    if 'enhanced_initialized' not in st.session_state and ENHANCED_AVAILABLE:
        # Initialize Services Connector
        st.session_state.services_connector = ServicesConnector()
        
        # Initialize services
        services = st.session_state.services_connector.initialize_all_services()
        st.session_state.initialized_services = services
        
        # Initialize service registry
        st.session_state.services_status = st.session_state.services_connector.get_service_status()
        
        # Initialize service states
        st.session_state.repository_analysis = None
        st.session_state.knowledge_graph = None
        st.session_state.model_evaluation = None
        st.session_state.agent_orchestration = None
        st.session_state.neuro_symbolic_analysis = None
        st.session_state.multimodal_analysis = None
        st.session_state.sdk_plugins = []
        st.session_state.academic_research = None
        
        # Initialize API Gateway (this was the missing part)
        try:
            st.session_state.api_gateway = st.session_state.services_connector.api_gateway_service()
            logger.info("API Gateway initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize API Gateway: {str(e)}")
            st.session_state.api_gateway = None
        
        # Initialize enhanced UI state
        st.session_state.enhanced_current_tab = "Repository Analysis"
        
        # Initialize agent orchestration state if available
        if AGENT_ORCHESTRATION_AVAILABLE:
            from agent_orchestration_ui import initialize_agent_orchestration_state
            initialize_agent_orchestration_state()
        
        # Mark as initialized
        st.session_state.enhanced_initialized = True

def update_service_status():
    """Update the status of all services"""
    if 'services_connector' in st.session_state and ENHANCED_AVAILABLE:
        st.session_state.services_status = st.session_state.services_connector.get_service_status()

########################
# ORIGINAL APP FUNCTIONS
########################

def render_header():
    """Render the app header"""
    st.title("🔍 Code Deep Dive Analyzer")
    st.markdown("""
    Perform comprehensive analysis of the code in your repository to discover improvement opportunities
    and get detailed recommendations for enhancing various aspects of your codebase.
    """)

def render_input_tab():
    """Render the input tab for repository information"""
    st.header("Repository Information")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        repo_url = st.text_input(
            "GitHub Repository URL",
            value=st.session_state.get('repo_url', ''),
            placeholder="https://github.com/username/repository",
            help="Enter the URL of the GitHub repository you want to analyze"
        )
        
        if repo_url:
            st.session_state.repo_url = repo_url
    
    with col2:
        repo_branch = st.text_input(
            "Branch",
            value=st.session_state.get('repo_branch', 'main'),
            help="Enter the branch to analyze (default: main)"
        )
        
        if repo_branch:
            st.session_state.repo_branch = repo_branch
    
    st.header("Analysis Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.analyze_code = st.checkbox(
            "Code Review",
            value=st.session_state.get('analyze_code', True),
            help="Analyze code complexity, potential issues, and improvement opportunities"
        )
        
        st.session_state.analyze_database = st.checkbox(
            "Database Analysis",
            value=st.session_state.get('analyze_database', True),
            help="Analyze database structures, models, and suggest consolidations"
        )
    
    with col2:
        st.session_state.analyze_modularization = st.checkbox(
            "Modularization Analysis",
            value=st.session_state.get('analyze_modularization', True),
            help="Analyze code dependencies and suggest modularization improvements"
        )
        
        st.session_state.analyze_agent_readiness = st.checkbox(
            "Agent Readiness Evaluation",
            value=st.session_state.get('analyze_agent_readiness', True),
            help="Evaluate how well the codebase is prepared for AI agents integration"
        )
    
    st.markdown("---")
    
    analyze_col, reset_col = st.columns([1, 5])
    
    with analyze_col:
        if st.button("Analyze Repository", type="primary", disabled=st.session_state.get('analyzing', False)):
            st.session_state.analyze_clicked = True
    
    with reset_col:
        if st.button("Reset", disabled=st.session_state.get('analyzing', False)):
            reset_app()
            st.experimental_rerun()
    
    # Trigger analysis if button was clicked
    if st.session_state.get('analyze_clicked', False) and not st.session_state.get('analyzing', False):
        run_analysis()

def run_analysis():
    """Run the repository analysis"""
    if not st.session_state.repo_url:
        st.error("Please enter a valid GitHub repository URL")
        st.session_state.analyze_clicked = False
        return
    
    st.session_state.analyzing = True
    
    try:
        # Progress bar and status
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Phase 1: Clone repository
        status_text.text("Cloning repository...")
        
        # Create a temporary directory for the repository
        import tempfile
        temp_dir = tempfile.mkdtemp()
        
        try:
            repo_path = clone_repository(
                st.session_state.repo_url,
                st.session_state.repo_branch,
                temp_dir
            )
            
            st.session_state.repo_path = repo_path
            st.session_state.repo_cloned = True
            
            progress_bar.progress(10)
            status_text.text("Repository cloned successfully! Analyzing repository structure...")
            
            # Phase 2: Analyze repository structure
            repo_structure = get_repository_structure(repo_path)
            st.session_state.repo_structure = repo_structure
            st.session_state.analysis_results['repository_structure'] = repo_structure
            
            progress_bar.progress(20)
            
            # Proceed with selected analyses
            if st.session_state.analyze_code:
                status_text.text("Performing code review...")
                code_review = perform_code_review(repo_path)
                st.session_state.code_review = code_review
                st.session_state.analysis_results['code_review'] = code_review
                progress_bar.progress(40)
                
            if st.session_state.analyze_database:
                status_text.text("Analyzing database structures...")
                database_analysis = analyze_database_structures(repo_path)
                st.session_state.database_analysis = database_analysis
                st.session_state.analysis_results['database_analysis'] = database_analysis
                progress_bar.progress(60)
                
            if st.session_state.analyze_modularization:
                status_text.text("Analyzing modularization opportunities...")
                modularization_analysis = analyze_modularization(repo_path)
                st.session_state.modularization_analysis = modularization_analysis
                st.session_state.analysis_results['modularization'] = modularization_analysis
                progress_bar.progress(80)
                
            if st.session_state.analyze_agent_readiness:
                status_text.text("Evaluating agent readiness...")
                agent_readiness_analysis = analyze_agent_readiness(repo_path)
                st.session_state.agent_readiness_analysis = agent_readiness_analysis
                st.session_state.analysis_results['agent_readiness'] = agent_readiness_analysis
                progress_bar.progress(85)
            
            # Analyze workflow patterns
            status_text.text("Analyzing workflow patterns...")
            workflow_patterns_analysis = analyze_workflow_patterns(repo_path)
            st.session_state.workflow_patterns_analysis = workflow_patterns_analysis
            st.session_state.analysis_results['workflow_patterns'] = workflow_patterns_analysis
            progress_bar.progress(90)
            
            # Generate summary report
            status_text.text("Generating summary report...")
            summary_report = generate_summary_report(st.session_state.analysis_results)
            st.session_state.summary_report = summary_report
            
            # Mark analysis as complete
            progress_bar.progress(100)
            status_text.text("Analysis complete!")
            time.sleep(1)
            status_text.empty()
            progress_bar.empty()
            
            st.session_state.analysis_complete = True
            st.session_state.current_tab = "Summary"
            
        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
            logger.error(f"Analysis error: {str(e)}")
        finally:
            # Clean up temporary directory, but keep the state for display
            # This prevents file access issues during the Streamlit session
            # shutil.rmtree(temp_dir)
            pass
    
    finally:
        st.session_state.analyzing = False
        st.session_state.analyze_clicked = False

def render_summary_tab():
    """Render the summary tab with analysis results"""
    if not st.session_state.get('analysis_complete', False):
        st.info("No analysis has been performed yet. Please enter a repository URL and click 'Analyze Repository'.")
        return
    
    st.header("Analysis Summary")
    
    # Display repository info
    repo_url = st.session_state.repo_url
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    
    st.markdown(f"""
    ### Repository: [{repo_name}]({repo_url})
    Branch: `{st.session_state.repo_branch}`
    """)
    
    # Display key findings from summary report
    summary_report = st.session_state.summary_report
    if summary_report and 'key_findings' in summary_report:
        key_findings = summary_report['key_findings']
        
        if key_findings:
            st.subheader("Key Findings")
            
            # Create columns for key findings
            col1, col2 = st.columns(2)
            
            # Distribute findings across columns
            findings_list = list(key_findings.items())
            half_length = len(findings_list) // 2 + len(findings_list) % 2
            
            for i, (category, findings) in enumerate(findings_list):
                with col1 if i < half_length else col2:
                    with st.expander(category, expanded=True):
                        for finding in findings:
                            st.markdown(f"• {finding}")
    
    # Display recommendations
    if summary_report and 'recommendations' in summary_report:
        recommendations = summary_report['recommendations']
        
        if recommendations:
            st.subheader("Recommendations")
            
            recommendation_tabs = st.tabs(list(recommendations.keys()))
            
            for i, (category, recs) in enumerate(recommendations.items()):
                with recommendation_tabs[i]:
                    for j, rec in enumerate(recs):
                        st.markdown(f"{j+1}. {rec}")
    
    # Add export option
    st.markdown("---")
    if st.button("Export Analysis Results"):
        # Save results to a file
        results_file = save_analysis_results(st.session_state.analysis_results)
        
        if results_file:
            with open(results_file, 'rb') as f:
                st.download_button(
                    label="Download Analysis Results (JSON)",
                    data=f,
                    file_name=f"code_analysis_{repo_name}.json",
                    mime="application/json"
                )

def render_original_app():
    """Render the original app UI"""
    # Initialize state
    initialize_session_state()
    
    # Render header
    render_header()
    
    # Create tabs
    current_tab = st.session_state.get('current_tab', 'Input')
    
    # Define tabs list
    tabs_list = ["Input", "Summary", "Repository Structure", "Code Review", 
               "Database Analysis", "Modularization", "Agent Readiness", 
               "Workflow Patterns"]
    
    # Add Intelligent Workflow Mapper tab if available
    if WORKFLOW_MAPPER_AVAILABLE:
        tabs_list = add_workflow_mapper_tab(tabs_list)
    
    tabs = st.tabs(tabs_list)
    
    # Render content for selected tab
    with tabs[0]:  # Input tab
        render_input_tab()
    
    with tabs[1]:  # Summary tab
        render_summary_tab()
    
    # Add other tabs for Repository Structure, Code Review, Database Analysis, etc.
    # We're only implementing a subset for brevity
    
    # Add the Intelligent Workflow Mapper tab if available
    if WORKFLOW_MAPPER_AVAILABLE:
        # Find the index of the Intelligent Workflow Mapper tab
        if "Intelligent Workflow Mapper" in tabs_list:
            mapper_tab_index = tabs_list.index("Intelligent Workflow Mapper")
            with tabs[mapper_tab_index]:
                render_workflow_mapper_tab()

########################
# ENHANCED APP FUNCTIONS
########################

def render_enhanced_header():
    """Render the enhanced app header"""
    st.title("🧠 Enhanced Code Deep Dive Analyzer")
    st.markdown("""
    Advanced analysis of codebases using AI-powered tools, multi-repository knowledge graphs,
    neuro-symbolic reasoning, and academic research framework.
    """)

def render_service_status():
    """Render the service status panel"""
    with st.expander("Service Status", expanded=False):
        if not st.session_state.get('services_status'):
            st.info("No service status available. Initializing services...")
            return
            
        col1, col2, col3 = st.columns(3)
        
        services = list(st.session_state.services_status.items())
        column_size = len(services) // 3 + (len(services) % 3 > 0)
        
        for i, (service_name, status) in enumerate(services):
            column = i // column_size
            
            if column == 0:
                with col1:
                    render_service_status_indicator(service_name, status)
            elif column == 1:
                with col2:
                    render_service_status_indicator(service_name, status)
            else:
                with col3:
                    render_service_status_indicator(service_name, status)
        
        if st.button("Refresh Service Status"):
            update_service_status()
            st.rerun()

def render_service_status_indicator(service_name: str, status: str):
    """Render a status indicator for a service"""
    if status == "online":
        st.success(f"{service_name.capitalize()}: {status}")
    elif status == "offline":
        st.error(f"{service_name.capitalize()}: {status}")
    elif status == "degraded":
        st.warning(f"{service_name.capitalize()}: {status}")
    elif status == "starting":
        st.info(f"{service_name.capitalize()}: {status}")
    else:
        st.info(f"{service_name.capitalize()}: {status}")

def render_enhanced_tabs():
    """Render the enhanced app tabs"""
    # Import database migration UI if available
    DATABASE_MIGRATIONS_AVAILABLE = True
    try:
        import database_migration_ui
    except ImportError:
        DATABASE_MIGRATIONS_AVAILABLE = False
    
    tabs = st.tabs([
        "Repository Analysis",
        "Knowledge Graph",
        "Neuro-Symbolic Reasoning",
        "Multimodal Analysis",
        "Agent Orchestration",
        "Academic Research",
        "SDK & Plugins",
        "Database Migrations"
    ])
    
    with tabs[0]:
        render_repository_analysis_tab()
    
    with tabs[1]:
        render_knowledge_graph_tab()
    
    # Agent Orchestration tab
    with tabs[4]:
        render_agent_orchestration_tab()
        
    # Database Migrations tab
    with tabs[7]:
        if DATABASE_MIGRATIONS_AVAILABLE:
            database_migration_ui.render_migration_ui()
        else:
            st.warning("Database Migration UI is not available.")
    
    # Add other tabs from the enhanced app...
    # These would be copied from the enhanced_app.py
    
def render_repository_analysis_tab():
    """Render the repository analysis tab"""
    st.header("Repository Analysis")
    
    if not ENHANCED_AVAILABLE:
        st.warning("Enhanced services are not available. Make sure all services are properly installed.")
        return
    
    # Repository input form
    with st.form("repository_analysis_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            repo_url = st.text_input(
                "Repository URL",
                placeholder="https://github.com/username/repository",
                help="Enter the URL of the GitHub repository you want to analyze"
            )
        
        with col2:
            repo_branch = st.text_input(
                "Branch",
                value="main",
                help="Enter the branch to analyze (default: main)"
            )
        
        # Analysis options
        st.subheader("Analysis Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            analyze_code = st.checkbox(
                "Code Review",
                value=True,
                help="Analyze code complexity, potential issues, and improvement opportunities"
            )
            
            analyze_database = st.checkbox(
                "Database Analysis",
                value=True,
                help="Analyze database structures, models, and suggest consolidations"
            )
        
        with col2:
            analyze_modularization = st.checkbox(
                "Modularization Analysis",
                value=True,
                help="Analyze code dependencies and suggest modularization improvements"
            )
            
            analyze_agent_readiness = st.checkbox(
                "Agent Readiness Evaluation",
                value=True,
                help="Evaluate how well the codebase is prepared for AI agents integration"
            )
        
        # Submit button
        submitted = st.form_submit_button("Analyze Repository", type="primary")
        
        if submitted:
            if not repo_url:
                st.error("Please enter a valid repository URL")
            else:
                # Prepare parameters
                parameters = {
                    'repo_url': repo_url,
                    'repo_branch': repo_branch,
                    'analyze_code': analyze_code,
                    'analyze_database': analyze_database,
                    'analyze_modularization': analyze_modularization,
                    'analyze_agent_readiness': analyze_agent_readiness
                }
                
                # Run analysis
                with st.spinner("Analyzing repository..."):
                    try:
                        # Execute cross-service operation
                        gateway = st.session_state.api_gateway
                        results = gateway.execute_cross_service_operation(
                            operation_name="analyze_repository",
                            parameters=parameters
                        )
                        
                        # Store results
                        st.session_state.repository_analysis = results
                        
                        st.success("Repository analysis complete!")
                    except Exception as e:
                        st.error(f"Error analyzing repository: {str(e)}")
                        logger.error(f"Repository analysis error: {str(e)}")
    
    # Display results if available
    if st.session_state.get('repository_analysis'):
        results = st.session_state.repository_analysis
        
        if 'error' in results:
            st.error(f"Analysis error: {results['error']}")
            
            # Show partial results if available
            if 'partial_results' in results and results['partial_results']:
                st.warning("Partial results are available")
                results = results['partial_results']
            else:
                return
        
        # Display repository info
        st.markdown("---")
        st.subheader("Analysis Results")
        
        # Basic stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Files", results.get('file_count', 0))
        
        with col2:
            st.metric("Commits", results.get('commit_count', 0))
        
        with col3:
            st.metric("Branches", results.get('branch_count', 0))
        
        # Add additional result display

def render_agent_orchestration_tab():
    """Render the agent orchestration tab"""
    if not AGENT_ORCHESTRATION_AVAILABLE:
        st.warning("Agent Orchestration is not available. Please check that the agent_orchestration_ui.py file exists.")
        return
    
    # Use the agent orchestration UI
    from agent_orchestration_ui import add_agent_orchestration_to_app
    add_agent_orchestration_to_app()

def render_knowledge_graph_tab():
    """Render the knowledge graph tab"""
    st.header("Knowledge Graph")
    
    if not ENHANCED_AVAILABLE:
        st.warning("Enhanced services are not available. Make sure all services are properly installed.")
        return
    
    # Check if knowledge graph service is available
    if st.session_state.services_status.get('knowledge_graph') != 'online':
        st.warning("Knowledge Graph service is not available. Please check service status.")
        return
    
    # Knowledge graph operations
    st.subheader("Knowledge Graph Operations")
    
    operation = st.selectbox(
        "Select Operation",
        ["Create New Graph", "View Existing Graph", "Add Repository to Graph", "Find Patterns"]
    )
    
    if operation == "Create New Graph":
        with st.form("create_graph_form"):
            graph_name = st.text_input(
                "Graph Name",
                placeholder="my_knowledge_graph",
                help="Enter a name for the new knowledge graph"
            )
            
            submitted = st.form_submit_button("Create Graph")
            
            if submitted:
                if not graph_name:
                    st.error("Please enter a valid graph name")
                else:
                    st.info(f"Creating knowledge graph '{graph_name}'...")
                    # This would call the knowledge graph service

def render_enhanced_app():
    """Render the enhanced app UI"""
    # Initialize enhanced state
    initialize_enhanced_session_state()
    
    # Render header
    render_enhanced_header()
    
    # Render service status
    render_service_status()
    
    # Render tabs
    render_enhanced_tabs()

def main():
    """Main function for the app"""
    # App mode selector in sidebar
    st.sidebar.title("Code Deep Dive Analyzer")
    
    app_mode = st.sidebar.radio(
        "Select Application Version",
        ["Original", "Enhanced"],
        index=0 if st.session_state.app_mode == "original" else 1
    )
    
    # Update state
    st.session_state.app_mode = app_mode.lower()
    
    # Display selected app
    if st.session_state.app_mode == "original":
        st.sidebar.info("Running original version with base features")
        render_original_app()
    else:
        st.sidebar.info("Running enhanced version with advanced features")
        
        if not ENHANCED_AVAILABLE:
            st.sidebar.warning("Note: Enhanced features are not available. Some services may not be properly installed.")
        else:
            st.sidebar.success("All enhanced services are available!")
        
        render_enhanced_app()

if __name__ == "__main__":
    main()