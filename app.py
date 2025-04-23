import os
import streamlit as st
import tempfile
import shutil
import pandas as pd
import time
from pathlib import Path

# Import custom modules
from repository_handler import clone_repository, get_repository_structure
from code_analyzer import perform_code_review
from database_analyzer import analyze_database_structures
from modularization_analyzer import analyze_modularization
from agent_readiness_analyzer import analyze_agent_readiness
from workflow_analyzer import analyze_workflow_patterns
from report_generator import generate_summary_report
from visualizations import (
    visualize_repository_structure,
    visualize_code_complexity,
    visualize_database_relations,
    visualize_modularization_opportunities
)

# Set page configuration
st.set_page_config(
    page_title="Code Deep Dive Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'repo_path' not in st.session_state:
    st.session_state.repo_path = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()

# Function to reset the application state
def reset_app():
    if st.session_state.repo_path:
        try:
            # Clean up temp directory if it exists
            if os.path.exists(st.session_state.temp_dir):
                shutil.rmtree(st.session_state.temp_dir)
            st.session_state.temp_dir = tempfile.mkdtemp()
        except Exception as e:
            st.error(f"Error cleaning up: {str(e)}")
    
    st.session_state.repo_path = None
    st.session_state.analysis_complete = False
    st.session_state.current_step = 0
    st.session_state.analysis_results = {}

# Display header
st.title("🔍 Code Deep Dive Analyzer")
st.markdown("""
This tool performs a comprehensive analysis of GitHub repositories, 
providing insights and recommendations for improvement.
""")

# Sidebar navigation
st.sidebar.title("Navigation")

# Repository input section
with st.sidebar.expander("Repository Settings", expanded=True):
    repo_url = st.text_input(
        "GitHub Repository URL",
        value="https://github.com/bsvalues/TerraFusion.git" if not st.session_state.repo_path else "",
        placeholder="https://github.com/username/repository.git"
    )
    
    branch = st.text_input(
        "Branch (optional)",
        value="main",
        placeholder="main"
    )
    
    if st.button("Clone Repository", disabled=st.session_state.analysis_complete):
        try:
            with st.spinner("Cloning repository..."):
                repo_path = clone_repository(repo_url, branch, st.session_state.temp_dir)
                st.session_state.repo_path = repo_path
                st.session_state.current_step = 1
                st.success(f"Repository cloned successfully!")
                st.rerun()
        except Exception as e:
            st.error(f"Error cloning repository: {str(e)}")

    if st.session_state.repo_path and st.button("Reset Analysis"):
        reset_app()
        st.rerun()

# Analysis options
if st.session_state.repo_path:
    with st.sidebar.expander("Analysis Options", expanded=True):
        perform_code_review_option = st.checkbox("Code Review", value=True)
        analyze_database_option = st.checkbox("Database Analysis", value=True)
        analyze_modularization_option = st.checkbox("Modularization Analysis", value=True)
        analyze_agent_readiness_option = st.checkbox("Agent Readiness", value=True)
        analyze_workflow_option = st.checkbox("Workflow Patterns", value=True)
        
        if st.button("Start Analysis", disabled=st.session_state.analysis_complete):
            try:
                st.session_state.analysis_results = {}
                
                # Step 1: Repository Structure Analysis
                with st.spinner("Analyzing repository structure..."):
                    repo_structure = get_repository_structure(st.session_state.repo_path)
                    st.session_state.analysis_results['repository_structure'] = repo_structure
                    st.session_state.current_step = 2
                
                # Step 2: Code Review
                if perform_code_review_option:
                    with st.spinner("Performing code review..."):
                        code_review_results = perform_code_review(st.session_state.repo_path)
                        st.session_state.analysis_results['code_review'] = code_review_results
                        st.session_state.current_step = 3
                
                # Step 3: Database Analysis
                if analyze_database_option:
                    with st.spinner("Analyzing database structures..."):
                        database_results = analyze_database_structures(st.session_state.repo_path)
                        st.session_state.analysis_results['database_analysis'] = database_results
                        st.session_state.current_step = 4
                
                # Step 4: Modularization Analysis
                if analyze_modularization_option:
                    with st.spinner("Analyzing modularization opportunities..."):
                        modularization_results = analyze_modularization(st.session_state.repo_path)
                        st.session_state.analysis_results['modularization'] = modularization_results
                        st.session_state.current_step = 5
                
                # Step 5: Agent Readiness Analysis
                if analyze_agent_readiness_option:
                    with st.spinner("Analyzing agent readiness..."):
                        agent_readiness_results = analyze_agent_readiness(st.session_state.repo_path)
                        st.session_state.analysis_results['agent_readiness'] = agent_readiness_results
                        st.session_state.current_step = 6
                
                # Step 6: Workflow Pattern Analysis
                if analyze_workflow_option:
                    with st.spinner("Analyzing workflow patterns..."):
                        workflow_results = analyze_workflow_patterns(st.session_state.repo_path)
                        st.session_state.analysis_results['workflow_patterns'] = workflow_results
                        st.session_state.current_step = 7
                
                # Generate summary report
                with st.spinner("Generating summary report..."):
                    summary_report = generate_summary_report(st.session_state.analysis_results)
                    st.session_state.analysis_results['summary_report'] = summary_report
                
                st.session_state.analysis_complete = True
                st.success("Analysis completed successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")

# Display current repository information
if st.session_state.repo_path:
    st.markdown("## Repository Information")
    repo_name = os.path.basename(st.session_state.repo_path)
    st.info(f"Analyzing repository: **{repo_name}**")
    
    # Display progress
    if not st.session_state.analysis_complete:
        steps = ["Repository Cloned", "Structure Analysis", "Code Review", 
                "Database Analysis", "Modularization Analysis", 
                "Agent Readiness Analysis", "Workflow Patterns Analysis"]
        progress_value = st.session_state.current_step / len(steps)
        st.progress(progress_value)
        st.write(f"Current step: {steps[st.session_state.current_step-1] if st.session_state.current_step > 0 else 'Starting Analysis'}")

# Display analysis results if complete
if st.session_state.analysis_complete:
    # Create tabs for different analysis results
    tabs = st.tabs([
        "Summary", "Code Review", "Database Analysis", 
        "Modularization", "Agent Readiness", "Workflow Patterns", "Visualizations"
    ])
    
    # Summary Tab
    with tabs[0]:
        st.markdown("## Analysis Summary")
        summary_report = st.session_state.analysis_results.get('summary_report', {})
        
        if summary_report:
            st.markdown("### Key Findings")
            for category, findings in summary_report.get('key_findings', {}).items():
                st.subheader(category)
                for finding in findings:
                    st.markdown(f"- {finding}")
            
            st.markdown("### Recommendations")
            for category, recommendations in summary_report.get('recommendations', {}).items():
                st.subheader(category)
                for rec in recommendations:
                    st.markdown(f"- {rec}")
        else:
            st.warning("Summary report not available.")
    
    # Code Review Tab
    with tabs[1]:
        st.markdown("## Code Review Results")
        code_review = st.session_state.analysis_results.get('code_review', {})
        
        if code_review:
            # Code quality metrics
            st.subheader("Code Quality Metrics")
            metrics_df = pd.DataFrame(code_review.get('metrics', {}).items(), columns=['Metric', 'Value'])
            st.dataframe(metrics_df, use_container_width=True)
            
            # Files with issues
            st.subheader("Files with Issues")
            issues_df = pd.DataFrame(code_review.get('files_with_issues', []))
            if not issues_df.empty:
                st.dataframe(issues_df, use_container_width=True)
            else:
                st.info("No significant issues found.")
            
            # Improvement opportunities
            st.subheader("Improvement Opportunities")
            for category, opportunities in code_review.get('improvement_opportunities', {}).items():
                st.markdown(f"#### {category}")
                for opportunity in opportunities:
                    st.markdown(f"- {opportunity}")
        else:
            st.warning("Code review results not available.")
    
    # Database Analysis Tab
    with tabs[2]:
        st.markdown("## Database Analysis Results")
        db_analysis = st.session_state.analysis_results.get('database_analysis', {})
        
        if db_analysis:
            # Database files found
            st.subheader("Database Files Found")
            db_files_df = pd.DataFrame(db_analysis.get('database_files', []))
            if not db_files_df.empty:
                st.dataframe(db_files_df, use_container_width=True)
            else:
                st.info("No database files found.")
            
            # Database models
            st.subheader("Database Models")
            for model_name, model_info in db_analysis.get('database_models', {}).items():
                st.markdown(f"#### {model_name}")
                st.json(model_info)
            
            # Consolidation recommendations
            st.subheader("Consolidation Recommendations")
            for rec in db_analysis.get('consolidation_recommendations', []):
                st.markdown(f"- {rec}")
        else:
            st.warning("Database analysis results not available.")
    
    # Modularization Tab
    with tabs[3]:
        st.markdown("## Modularization Analysis")
        modularization = st.session_state.analysis_results.get('modularization', {})
        
        if modularization:
            # Current module structure
            st.subheader("Current Module Structure")
            modules_df = pd.DataFrame(modularization.get('current_modules', []))
            if not modules_df.empty:
                st.dataframe(modules_df, use_container_width=True)
            
            # Dependency graph
            st.subheader("Module Dependencies")
            if 'dependency_graph' in modularization:
                st.json(modularization['dependency_graph'])
            
            # Modularization recommendations
            st.subheader("Modularization Recommendations")
            for rec in modularization.get('recommendations', []):
                st.markdown(f"- {rec}")
        else:
            st.warning("Modularization analysis results not available.")
    
    # Agent Readiness Tab
    with tabs[4]:
        st.markdown("## Agent Readiness Analysis")
        agent_readiness = st.session_state.analysis_results.get('agent_readiness', {})
        
        if agent_readiness:
            # ML components found
            st.subheader("ML Components Found")
            ml_components_df = pd.DataFrame(agent_readiness.get('ml_components', []))
            if not ml_components_df.empty:
                st.dataframe(ml_components_df, use_container_width=True)
            else:
                st.info("No ML components found.")
            
            # Agent-readiness assessment
            st.subheader("Agent-Readiness Assessment")
            assessment_df = pd.DataFrame(agent_readiness.get('assessment', {}).items(), 
                                     columns=['Component', 'Readiness Score'])
            if not assessment_df.empty:
                st.dataframe(assessment_df, use_container_width=True)
            
            # Improvement recommendations
            st.subheader("Improvement Recommendations")
            for rec in agent_readiness.get('recommendations', []):
                st.markdown(f"- {rec}")
        else:
            st.warning("Agent readiness analysis results not available.")
    
    # Workflow Patterns Tab
    with tabs[5]:
        st.markdown("## Workflow Patterns Analysis")
        workflow = st.session_state.analysis_results.get('workflow_patterns', {})
        
        if workflow:
            # Identified workflows
            st.subheader("Identified Workflows")
            workflows_df = pd.DataFrame(workflow.get('workflows', []))
            if not workflows_df.empty:
                st.dataframe(workflows_df, use_container_width=True)
            else:
                st.info("No distinct workflows identified.")
            
            # Standardization recommendations
            st.subheader("Standardization Recommendations")
            for rec in workflow.get('standardization_recommendations', []):
                st.markdown(f"- {rec}")
        else:
            st.warning("Workflow patterns analysis results not available.")
    
    # Visualizations Tab
    with tabs[6]:
        st.markdown("## Visualizations")
        
        viz_tabs = st.tabs([
            "Repository Structure", "Code Complexity", 
            "Database Relations", "Modularization"
        ])
        
        # Repository Structure Visualization
        with viz_tabs[0]:
            st.markdown("### Repository Structure")
            if 'repository_structure' in st.session_state.analysis_results:
                fig = visualize_repository_structure(
                    st.session_state.analysis_results['repository_structure']
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Repository structure data not available.")
        
        # Code Complexity Visualization
        with viz_tabs[1]:
            st.markdown("### Code Complexity")
            if 'code_review' in st.session_state.analysis_results:
                fig = visualize_code_complexity(
                    st.session_state.analysis_results['code_review']
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Code review data not available.")
        
        # Database Relations Visualization
        with viz_tabs[2]:
            st.markdown("### Database Relations")
            if 'database_analysis' in st.session_state.analysis_results:
                fig = visualize_database_relations(
                    st.session_state.analysis_results['database_analysis']
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Database analysis data not available.")
        
        # Modularization Visualization
        with viz_tabs[3]:
            st.markdown("### Modularization Opportunities")
            if 'modularization' in st.session_state.analysis_results:
                fig = visualize_modularization_opportunities(
                    st.session_state.analysis_results['modularization']
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Modularization data not available.")

# Display footer
st.markdown("---")
st.markdown("### About This Tool")
st.markdown("""
This tool analyzes GitHub repositories to identify areas for improvement, including:
- Code quality and structure assessment
- Database consolidation opportunities
- Modularization recommendations
- Agent-readiness evaluation for ML components
- Workflow pattern standardization

The analysis results are intended to guide development teams in improving 
codebase maintainability, scalability, and overall quality.
""")
