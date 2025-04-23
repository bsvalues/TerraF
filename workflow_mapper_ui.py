"""
Intelligent Workflow Mapper UI Component

This module provides the UI components for visualizing project dependencies
and identifying potential bottlenecks in the codebase using the workflow_mapper.py
functionality.
"""
import streamlit as st
import os
import sys
import logging
import time
from typing import Dict, Any, List, Optional, Union
import plotly.graph_objects as go

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import dependencies
try:
    from workflow_mapper import (
        build_dependency_graph, 
        visualize_dependency_graph,
        visualize_bottlenecks,
        visualize_critical_paths,
        generate_optimization_recommendations,
        analyze_workflow_dependencies,
        analyze_all_dependencies
    )
    WORKFLOW_MAPPER_AVAILABLE = True
except ImportError:
    logger.error("Workflow mapper functionality not available.")
    WORKFLOW_MAPPER_AVAILABLE = False

def initialize_workflow_mapper_state():
    """Initialize session state for workflow mapper"""
    if 'workflow_mapper_initialized' not in st.session_state:
        st.session_state.workflow_mapper_initialized = True
        st.session_state.dependency_graph_data = None
        st.session_state.workflow_dependencies_data = None
        st.session_state.dependency_analysis_mode = "workflow"  # or "all"
        st.session_state.highlight_bottlenecks = True
        st.session_state.optimization_recommendations = []

def render_workflow_mapper_tab():
    """Render the Intelligent Workflow Mapper tab"""
    # Initialize state if not already done
    initialize_workflow_mapper_state()
    
    st.header("🔄 Intelligent Workflow Mapper")
    st.markdown("""
    Visualize project dependencies and identify potential bottlenecks in your codebase.
    This analysis helps you understand complex relationships between modules and optimize your workflow.
    """)
    
    # Check if repository is available
    if not st.session_state.get('repo_path'):
        st.info("Please analyze a repository first to use the Workflow Mapper.")
        return
    
    # Check if workflow mapper is available
    if not WORKFLOW_MAPPER_AVAILABLE:
        st.error("Workflow mapper functionality is not available. Please check the installation.")
        return
    
    # Dependency analysis options
    st.subheader("Analysis Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_mode = st.radio(
            "Dependency Analysis Mode",
            ["Workflow-focused", "All Dependencies"],
            index=0 if st.session_state.dependency_analysis_mode == "workflow" else 1,
            help="Analyze only workflow-related files or all project dependencies"
        )
        
        st.session_state.dependency_analysis_mode = "workflow" if analysis_mode == "Workflow-focused" else "all"
    
    with col2:
        st.session_state.highlight_bottlenecks = st.checkbox(
            "Highlight Bottlenecks", 
            value=st.session_state.get('highlight_bottlenecks', True),
            help="Highlight bottleneck modules in the visualization"
        )
        
        # Add a button to run the analysis
        if st.button("Analyze Dependencies", type="primary"):
            with st.spinner("Analyzing project dependencies..."):
                run_dependency_analysis()
    
    # Show results if available
    if st.session_state.get('dependency_graph_data'):
        display_dependency_analysis_results()

def run_dependency_analysis():
    """Run the dependency analysis based on the selected mode"""
    try:
        repo_path = st.session_state.repo_path
        
        if st.session_state.dependency_analysis_mode == "workflow":
            # Analyze workflow-related dependencies
            st.info("Analyzing workflow-related dependencies...")
            workflow_data = analyze_workflow_dependencies(repo_path)
            
            st.session_state.workflow_dependencies_data = workflow_data
            st.session_state.dependency_graph_data = workflow_data.get('graph_data')
            
        else:
            # Analyze all dependencies
            st.info("Analyzing all project dependencies...")
            all_data = analyze_all_dependencies(repo_path)
            
            st.session_state.workflow_dependencies_data = None
            st.session_state.dependency_graph_data = all_data.get('graph_data')
        
        # Generate recommendations
        if st.session_state.dependency_graph_data:
            st.session_state.optimization_recommendations = generate_optimization_recommendations(
                st.session_state.dependency_graph_data
            )
            
            st.success("Dependency analysis completed successfully!")
        else:
            st.warning("No dependency data was generated.")
    
    except Exception as e:
        st.error(f"Error during dependency analysis: {str(e)}")
        logger.error(f"Dependency analysis error: {str(e)}")

def display_dependency_analysis_results():
    """Display the results of the dependency analysis"""
    st.subheader("Dependency Visualization")
    
    # Display the dependency graph
    try:
        graph_data = st.session_state.dependency_graph_data
        
        if graph_data:
            # Main dependency graph
            st.markdown("### Module Dependency Graph")
            
            fig = visualize_dependency_graph(
                graph_data, 
                highlight_bottlenecks=st.session_state.highlight_bottlenecks
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display metrics
            metrics = graph_data.get('metrics', {})
            if metrics:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Modules", metrics.get('node_count', 0))
                
                with col2:
                    st.metric("Dependencies", metrics.get('edge_count', 0))
                
                with col3:
                    st.metric("Avg. Dependencies", round(metrics.get('average_degree', 0), 2))
            
            # Display bottlenecks if any
            bottlenecks = graph_data.get('bottlenecks', [])
            if bottlenecks:
                st.markdown("### Bottleneck Analysis")
                st.markdown(f"Found **{len(bottlenecks)}** potential bottlenecks in the codebase.")
                
                # Bottleneck visualization
                bottleneck_fig = visualize_bottlenecks(graph_data)
                st.plotly_chart(bottleneck_fig, use_container_width=True)
                
                # Display detailed bottleneck information
                with st.expander("Detailed Bottleneck Information", expanded=False):
                    st.markdown("#### Top Bottlenecks")
                    
                    for i, bottleneck in enumerate(bottlenecks[:10]):  # Show top 10
                        severity = bottleneck.get('severity', 0)
                        severity_color = (
                            "🔴" if severity > 0.5 else 
                            "🟠" if severity > 0.3 else 
                            "🟡"
                        )
                        
                        st.markdown(f"{severity_color} **{os.path.basename(bottleneck['file'])}**")
                        st.markdown(f"""
                        - **File:** `{bottleneck['file']}`
                        - **Centrality:** {bottleneck['centrality']:.3f}
                        - **Incoming Dependencies:** {bottleneck['in_degree']}
                        - **Outgoing Dependencies:** {bottleneck['out_degree']}
                        - **Severity Score:** {bottleneck['severity']:.2f}
                        """)
                        
                        if i < len(bottlenecks) - 1:
                            st.markdown("---")
            
            # Display critical paths if any
            critical_paths = graph_data.get('critical_paths', [])
            if critical_paths:
                st.markdown("### Critical Path Analysis")
                
                # Separate cycles and long paths
                cycles = [p for p in critical_paths if p['type'] == 'cycle']
                long_paths = [p for p in critical_paths if p['type'] == 'path']
                
                if cycles:
                    st.markdown(f"Found **{len(cycles)}** circular dependencies.")
                
                if long_paths:
                    st.markdown(f"Found **{len(long_paths)}** long dependency chains.")
                
                # Critical paths visualization
                critical_path_fig = visualize_critical_paths(graph_data)
                st.plotly_chart(critical_path_fig, use_container_width=True)
                
                # Display detailed critical path information
                with st.expander("Detailed Critical Path Information", expanded=False):
                    if cycles:
                        st.markdown("#### Circular Dependencies")
                        
                        for i, cycle in enumerate(cycles):
                            st.markdown(f"**Cycle {i+1}** (Length: {cycle['length']})")
                            st.markdown(f"- **Path:** {cycle['path_str']}")
                            st.markdown(f"- **Severity:** {cycle['severity']}")
                            
                            if i < len(cycles) - 1:
                                st.markdown("---")
                    
                    if long_paths:
                        st.markdown("#### Long Dependency Chains")
                        
                        for i, path in enumerate(long_paths):
                            st.markdown(f"**Path {i+1}** (Length: {path['length']})")
                            st.markdown(f"- **Path:** {path['path_str']}")
                            st.markdown(f"- **Severity:** {path['severity']}")
                            
                            if i < len(long_paths) - 1:
                                st.markdown("---")
            
            # Display optimization recommendations
            recommendations = st.session_state.get('optimization_recommendations', [])
            if recommendations:
                st.markdown("### Optimization Recommendations")
                
                for i, recommendation in enumerate(recommendations):
                    st.markdown(f"{i+1}. {recommendation}")
        else:
            st.info("No dependency graph data available. Please run the analysis first.")
    
    except Exception as e:
        st.error(f"Error displaying dependency analysis results: {str(e)}")
        logger.error(f"Error displaying results: {str(e)}")

def add_workflow_mapper_tab(tabs_list: List[str]) -> List[str]:
    """
    Add the Workflow Mapper tab to the provided tabs list
    
    Parameters:
    - tabs_list: The existing list of tabs
    
    Returns:
    - Updated list of tabs with Workflow Mapper added
    """
    if "Intelligent Workflow Mapper" not in tabs_list:
        # Add after Workflow Patterns but before any enhanced tabs
        if "Workflow Patterns" in tabs_list:
            index = tabs_list.index("Workflow Patterns") + 1
            tabs_list.insert(index, "Intelligent Workflow Mapper")
        else:
            tabs_list.append("Intelligent Workflow Mapper")
    
    return tabs_list