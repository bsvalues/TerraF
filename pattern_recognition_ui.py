"""
Pattern Recognition UI Module

This module provides a Streamlit UI for the code pattern recognizer.
It allows users to analyze repositories for code patterns, including
design patterns, anti-patterns, code smells, and performance patterns.
"""

import streamlit as st
import os
import time
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union

# Optional imports
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Plotly not available. Visualizations will be limited.")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import code pattern recognizer
try:
    from code_pattern_recognizer import CodePatternRecognizer
    PATTERN_RECOGNIZER_AVAILABLE = True
except ImportError as e:
    logger.error(f"Pattern recognizer not available: {str(e)}")
    PATTERN_RECOGNIZER_AVAILABLE = False

# Define placeholder function if the pattern recognizer is not available
if not PATTERN_RECOGNIZER_AVAILABLE:
    class CodePatternRecognizer:
        def __init__(self, repo_path):
            pass
            
        def analyze_repository(self):
            return {}


def initialize_pattern_recognition_state():
    """Initialize session state for pattern recognition"""
    if 'pattern_recognition_initialized' not in st.session_state:
        st.session_state.pattern_recognition_initialized = True
        st.session_state.pattern_recognizer = None
        st.session_state.pattern_analysis_results = None
        st.session_state.selected_pattern_category = None
        st.session_state.selected_pattern = None
        st.session_state.pattern_details = None
        st.session_state.code_anomalies = None
        st.session_state.code_clusters = None


def render_pattern_recognition_tab():
    """Render the Pattern Recognition tab"""
    # Initialize state if not already done
    initialize_pattern_recognition_state()

    st.header("🧠 Machine Learning Code Pattern Recognition")
    st.markdown("""
    Utilize machine learning techniques to identify code patterns, anti-patterns, and code smells.
    This advanced analysis can uncover patterns that rule-based methods might miss.
    """)

    # Check if repository is available
    if not st.session_state.get('repo_path'):
        st.info("Please analyze a repository first to use the Pattern Recognition tool.")
        return

    # Check if pattern recognizer is available
    if not PATTERN_RECOGNIZER_AVAILABLE:
        st.error("Pattern Recognition module is not available. Please check the installation.")
        return

    # Repository and analysis options
    st.subheader("Pattern Analysis Options")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Run Full Pattern Analysis", type="primary"):
            with st.spinner("Running machine learning pattern analysis..."):
                run_pattern_analysis()

    with col2:
        if st.session_state.pattern_recognizer is not None:
            st.success("Pattern Recognizer initialized")
            available_models = "Yes" if st.session_state.pattern_recognizer.is_trained else "No"
            st.info(f"Trained models available: {available_models}")
        else:
            st.info("Initialize the pattern recognizer to start analysis")

    # Show results if available
    if st.session_state.pattern_analysis_results:
        display_pattern_analysis_results()
    elif st.session_state.pattern_recognizer and st.session_state.pattern_recognizer.is_trained:
        st.info("Pattern recognizer is trained. Run the analysis to see results.")


def run_pattern_analysis():
    """Run the pattern analysis on the repository"""
    try:
        repo_path = st.session_state.repo_path

        # Initialize the pattern recognizer if not already done
        if st.session_state.pattern_recognizer is None:
            st.session_state.pattern_recognizer = CodePatternRecognizer(repo_path)

        # Run the analysis
        results = st.session_state.pattern_recognizer.analyze_repository()

        # Store results
        st.session_state.pattern_analysis_results = results
        st.session_state.code_anomalies = results.get('anomalies', [])
        st.session_state.code_clusters = results.get('clusters', {})

        st.success("Pattern analysis completed successfully")

    except Exception as e:
        st.error(f"Error during pattern analysis: {str(e)}")
        logger.error(f"Pattern analysis error: {str(e)}")


def display_pattern_analysis_results():
    """Display the results of the pattern analysis"""
    results = st.session_state.pattern_analysis_results

    # Create tabs for different result types
    pattern_tabs = st.tabs([
        "Pattern Overview", 
        "Design Patterns", 
        "Anti-Patterns", 
        "Code Smells", 
        "Performance Patterns",
        "Anomalies"
    ])

    with pattern_tabs[0]:  # Pattern Overview
        st.markdown("### Repository Pattern Analysis")

        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Code Samples", results.get('code_samples_count', 0))
        
        with col2:
            st.metric("Functions", results.get('function_count', 0))
        
        with col3:
            st.metric("Classes", results.get('class_count', 0))
        
        with col4:
            # Calculate total patterns
            total_patterns = sum(
                len(results.get('patterns', {}).get(cat, []))
                for cat in ['code_smells', 'anti_patterns', 'design_patterns', 'performance_patterns', 'security_patterns']
            )
            st.metric("Patterns Detected", total_patterns)
        
        # Display pattern distribution
        st.markdown("### Pattern Distribution")
        
        try:
            # Prepare data for chart
            pattern_counts = {
                "Design Patterns": len(results.get('patterns', {}).get('design_patterns', [])),
                "Anti-Patterns": len(results.get('patterns', {}).get('anti_patterns', [])),
                "Code Smells": len(results.get('patterns', {}).get('code_smells', [])),
                "Performance Patterns": len(results.get('patterns', {}).get('performance_patterns', [])),
                "Security Patterns": len(results.get('patterns', {}).get('security_patterns', []))
            }
            
            pattern_df = pd.DataFrame({
                "Pattern Type": list(pattern_counts.keys()),
                "Count": list(pattern_counts.values())
            })
            
            if PLOTLY_AVAILABLE:
                # Create chart with Plotly
                fig = px.bar(
                    pattern_df,
                    x="Pattern Type",
                    y="Count",
                    title="Pattern Distribution",
                    color="Pattern Type",
                    color_discrete_sequence=px.colors.qualitative.Plotly
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                # If Plotly is not available, show tabular data with a simple bar chart
                st.write("Pattern Distribution (interactive visualization not available):")
                st.dataframe(pattern_df)
                
                # Create a simple bar chart using Streamlit's built-in charting
                st.bar_chart(pattern_df.set_index('Pattern Type'))
        
        except Exception as e:
            st.error(f"Error generating pattern distribution chart: {str(e)}")
            # Show raw counts as fallback
            st.write({k: v for k, v in pattern_counts.items() if v > 0})
        
        # Display code cluster visualization
        st.markdown("### Code Clusters")
        st.markdown("""
        The following visualization shows clusters of similar code identified by the machine learning algorithm.
        This can help identify areas of related functionality and potential for refactoring.
        """)
        
        clusters = st.session_state.code_clusters
        if clusters:
            try:
                # Prepare data for plot
                nodes = []
                # Define fallback colors in case Plotly is not available
                default_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
                
                if PLOTLY_AVAILABLE:
                    cluster_colors = px.colors.qualitative.Plotly
                else:
                    cluster_colors = default_colors
                
                for cluster_id, cluster_info in clusters.items():
                    cluster_color = cluster_colors[int(cluster_id) % len(cluster_colors)]
                    
                    # Add main cluster node
                    nodes.append({
                        "id": f"cluster_{cluster_id}",
                        "label": f"Cluster {cluster_id}",
                        "size": cluster_info.get('size', 1) * 2,
                        "color": cluster_color,
                        "shape": "dot"
                    })
                    
                    # Add sample nodes
                    for sample in cluster_info.get('samples', [])[:5]:  # Limit to 5 per cluster
                        sample_id = sample.get('id', '')
                        sample_name = sample.get('name', 'Unknown')
                        sample_type = sample.get('type', 'Unknown')
                        
                        nodes.append({
                            "id": sample_id,
                            "label": f"{sample_name} ({sample_type})",
                            "size": 10,
                            "color": cluster_color,
                            "shape": "triangle" if sample_type == "class" else "square",
                            "parent": f"cluster_{cluster_id}"
                        })
                
                # Convert to DataFrame for visualization
                nodes_df = pd.DataFrame(nodes)
                
                # Try to create a plotly visualization first
                if PLOTLY_AVAILABLE:
                    try:
                        # Create edges data
                        edges = []
                        for node in nodes:
                            if 'parent' in node:
                                source_id = node['id']
                                target_id = node['parent']
                                edges.append((source_id, target_id))
                        
                        # Create a plotly network graph
                        edge_x = []
                        edge_y = []
                        
                        node_x = np.random.rand(len(nodes)) * 10
                        node_y = np.random.rand(len(nodes)) * 10
                        node_positions = {node['id']: (x, y) for node, x, y in zip(nodes, node_x, node_y)}
                        
                        # Create edges
                        for edge in edges:
                            x0, y0 = node_positions[edge[0]]
                            x1, y1 = node_positions[edge[1]]
                            edge_x.extend([x0, x1, None])
                            edge_y.extend([y0, y1, None])
                        
                        # Create edge trace
                        edge_trace = go.Scatter(
                            x=edge_x, y=edge_y,
                            line=dict(width=0.5, color='#888'),
                            hoverinfo='none',
                            mode='lines')
                        
                        # Create node trace
                        node_trace = go.Scatter(
                            x=node_x, y=node_y,
                            mode='markers',
                            hoverinfo='text',
                            marker=dict(
                                showscale=True,
                                colorscale='YlGnBu',
                                size=[node['size'] * 5 for node in nodes],
                                color=[i for i in range(len(nodes))],
                                line=dict(width=2)))
                        
                        # Add node information for hover
                        node_info = [f"{node['label']}" for node in nodes]
                        node_trace.text = node_info
                        
                        # Create the figure
                        fig = go.Figure(data=[edge_trace, node_trace],
                                    layout=go.Layout(
                                        title='Code Cluster Network',
                                        showlegend=False,
                                        hovermode='closest',
                                        margin=dict(b=20, l=5, r=5, t=40),
                                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
                        
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating Plotly network visualization: {str(e)}")
                        # Try networkx/matplotlib as fallback
                        try_networkx = True
                else:
                    # If Plotly not available, try networkx/matplotlib
                    try_networkx = True
                
                # Try networkx visualization as fallback or if plotly not available
                try_networkx = False  # Set to True to enable networkx visualization (but may fail)
                if try_networkx:
                    try:
                        import networkx as nx
                        import matplotlib.pyplot as plt
                        
                        G = nx.Graph()
                        
                        # Add nodes
                        for node in nodes:
                            G.add_node(node['id'], label=node['label'], size=node['size'], color=node['color'])
                        
                        # Add edges
                        for node in nodes:
                            if 'parent' in node:
                                G.add_edge(node['id'], node['parent'])
                        
                        # Create positions
                        pos = nx.spring_layout(G, seed=42)
                        
                        # Create a figure
                        plt.figure(figsize=(10, 8))
                        
                        # Draw nodes
                        for node_type, node_shape in [("dot", 'o'), ("triangle", '^'), ("square", 's')]:
                            node_list = [n for n in G.nodes if n in nodes_df['id'].values and nodes_df[nodes_df['id'] == n]['shape'].values[0] == node_type]
                            node_colors = [nodes_df[nodes_df['id'] == n]['color'].values[0] for n in node_list]
                            node_sizes = [nodes_df[nodes_df['id'] == n]['size'].values[0] * 100 for n in node_list]
                            
                            if node_list:
                                nx.draw_networkx_nodes(
                                    G, pos,
                                    nodelist=node_list,
                                    node_color=node_colors,
                                    node_size=node_sizes,
                                    node_shape=node_shape,
                                    alpha=0.8
                                )
                        
                        # Draw edges
                        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5)
                        
                        # Draw labels
                        nx.draw_networkx_labels(
                            G, pos,
                            font_size=10,
                            font_family="sans-serif"
                        )
                        
                        plt.axis("off")
                        plt.tight_layout()
                        
                        # Display
                        st.pyplot(plt)
                    except Exception as e:
                        st.error(f"Error creating NetworkX visualization: {str(e)}")
                        st.write("Displaying table of cluster data instead:")
                        st.dataframe(nodes_df)
                
                # Show cluster details
                with st.expander("Cluster Details"):
                    for cluster_id, cluster_info in clusters.items():
                        st.markdown(f"**Cluster {cluster_id}**")
                        st.markdown(f"Size: {cluster_info.get('size', 0)} code samples")
                        
                        # Show type distribution
                        types = cluster_info.get('types', {})
                        if types:
                            st.markdown("Type distribution:")
                            for type_name, count in types.items():
                                st.markdown(f"- {type_name}: {count}")
                        
                        # Show samples
                        samples = cluster_info.get('samples', [])
                        if samples:
                            st.markdown("Samples:")
                            for sample in samples:
                                st.markdown(f"- {sample.get('name', 'Unknown')} ({sample.get('type', 'Unknown')})")
                        
                        st.markdown("---")
            
            except Exception as e:
                st.error(f"Error visualizing code clusters: {str(e)}")
                st.markdown("Cluster details:")
                st.json(clusters)
        else:
            st.info("No code clusters available.")

    with pattern_tabs[1]:  # Design Patterns
        display_pattern_category('design_patterns', "Design Patterns")

    with pattern_tabs[2]:  # Anti-Patterns
        display_pattern_category('anti_patterns', "Anti-Patterns")

    with pattern_tabs[3]:  # Code Smells
        display_pattern_category('code_smells', "Code Smells")

    with pattern_tabs[4]:  # Performance Patterns
        display_pattern_category('performance_patterns', "Performance Patterns")

    with pattern_tabs[5]:  # Anomalies
        display_code_anomalies()


def display_pattern_category(category: str, display_name: str):
    """Display patterns in a category"""
    results = st.session_state.pattern_analysis_results
    patterns = results.get('patterns', {}).get(category, [])
    
    st.markdown(f"### {display_name}")
    
    if not patterns:
        st.info(f"No {display_name.lower()} detected.")
        return
    
    st.markdown(f"Detected {len(patterns)} {display_name.lower()} in the codebase.")
    
    # Create metrics row
    # Group patterns by severity if they have it
    severity_counts = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
    for pattern in patterns:
        severity = pattern.get('severity', 'unknown').lower()
        severity_counts[severity] += 1
    
    # Show severity metrics if applicable
    if severity_counts["high"] > 0 or severity_counts["medium"] > 0 or severity_counts["low"] > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Patterns", len(patterns))
        
        with col2:
            st.metric("High Severity", severity_counts["high"], delta=None, delta_color="inverse")
        
        with col3:
            st.metric("Medium Severity", severity_counts["medium"], delta=None, delta_color="inverse")
        
        with col4:
            st.metric("Low Severity", severity_counts["low"], delta=None)
    
    # Create pattern entries
    for i, pattern in enumerate(patterns):
        # Determine color based on severity
        severity = pattern.get('severity', 'unknown').lower()
        severity_color = {
            'high': 'red',
            'medium': 'orange',
            'low': 'blue',
            'unknown': 'gray'
        }.get(severity, 'gray')
        
        # Format pattern name with severity indicator
        severity_indicator = f"🔴 " if severity == 'high' else f"🟠 " if severity == 'medium' else f"🔵 " if severity == 'low' else ""
        pattern_title = f"{severity_indicator}**{pattern.get('name', 'Unknown Pattern')}**"
        
        with st.expander(pattern_title, expanded=i==0):
            # Two-column layout for pattern details
            detail_col1, detail_col2 = st.columns([3, 1])
            
            with detail_col1:
                st.markdown(f"**Description:** {pattern.get('description', 'No description available')}")
                
                if 'category' in pattern:
                    st.markdown(f"**Category:** {pattern.get('category', '').replace('_', ' ').title()}")
                
                if 'occurrences' in pattern:
                    st.markdown(f"**Occurrences:** {pattern.get('occurrences', 0)}")
                
                # Show examples if available
                if 'examples' in pattern and pattern['examples']:
                    st.markdown("**Examples:**")
                    for example in pattern['examples']:
                        file_path = example.get('file_path', 'Unknown')
                        name = example.get('name', 'Unknown')
                        line_start = example.get('start_line', 0)
                        line_end = example.get('end_line', 0)
                        
                        st.markdown(f"- `{name}` in `{file_path}` (lines {line_start}-{line_end})")
            
            with detail_col2:
                # Visual representation of severity
                if 'severity' in pattern:
                    st.markdown(f"""
                    <div style="
                        height: 100px;
                        background: linear-gradient(to top, {severity_color}, white);
                        border-radius: 5px;
                        text-align: center;
                        padding-top: 10px;
                        margin-bottom: 15px;
                    ">
                        <h3 style="color: black;">Severity</h3>
                        <h2>{severity.upper()}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Additional metrics
                if 'occurrences' in pattern:
                    st.metric("Occurrences", pattern.get('occurrences', 0))
            
            # Show similar pairs for duplicate code patterns
            if 'similar_pairs' in pattern:
                st.markdown("**Similar Function Pairs:**")
                for pair in pattern['similar_pairs']:
                    if len(pair) >= 3:
                        func1, func2, similarity = pair
                        st.markdown(f"- `{func1}` and `{func2}` (similarity: {similarity:.2f})")
            
            # View example code if available
            if 'examples' in pattern and pattern['examples'] and 'source_code' in pattern['examples'][0]:
                example = pattern['examples'][0]
                with st.expander("View Example Code"):
                    st.code(example.get('source_code', ''), language='python')


def display_code_anomalies():
    """Display code anomalies detected by machine learning"""
    anomalies = st.session_state.code_anomalies
    
    st.markdown("### Code Anomalies")
    st.markdown("""
    Anomalies are unusual code patterns detected by machine learning that don't match common patterns.
    These might indicate unique solutions, bugs, or inconsistencies in the codebase.
    """)
    
    if not anomalies:
        st.info("No code anomalies detected.")
        return
    
    st.markdown(f"Detected {len(anomalies)} anomalies in the codebase.")
    
    # Display anomaly metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Anomalies", len(anomalies))
    
    with col2:
        # Count anomalies by type
        func_anomalies = sum(1 for a in anomalies if a.get('type') == 'function')
        st.metric("Function Anomalies", func_anomalies)
    
    with col3:
        class_anomalies = sum(1 for a in anomalies if a.get('type') == 'class')
        st.metric("Class Anomalies", class_anomalies)
    
    # Plot anomaly scores
    try:
        anomaly_df = pd.DataFrame([
            {
                'id': a.get('id', 'Unknown'),
                'name': a.get('name', 'Unknown'),
                'type': a.get('type', 'Unknown'),
                'complexity': a.get('complexity', 0),
                'line_count': a.get('line_count', 0),
                'anomaly_score': abs(a.get('anomaly_score', 0))  # Absolute value for visualization
            }
            for a in anomalies
        ])
        
        if PLOTLY_AVAILABLE:
            # Create interactive scatter plot with Plotly
            fig = px.scatter(
                anomaly_df,
                x='complexity',
                y='line_count',
                size='anomaly_score',
                color='type',
                hover_name='name',
                title='Code Anomalies by Complexity and Size',
                labels={
                    'complexity': 'Cyclomatic Complexity',
                    'line_count': 'Lines of Code',
                    'anomaly_score': 'Anomaly Score',
                    'type': 'Type'
                }
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            # If Plotly is not available, show tabular data
            st.write("Anomaly data (interactive visualization not available):")
            st.dataframe(anomaly_df)
    
    except Exception as e:
        st.error(f"Error visualizing anomalies: {str(e)}")
        # Show raw data as fallback
        st.write("Anomaly data:")
        st.dataframe(pd.DataFrame(anomalies))
    
    # Display anomaly details
    for i, anomaly in enumerate(anomalies):
        name = anomaly.get('name', 'Unknown')
        anomaly_score = anomaly.get('anomaly_score', 0)
        
        with st.expander(f"Anomaly: {name} (Score: {abs(anomaly_score):.3f})", expanded=i==0):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Type:** {anomaly.get('type', 'Unknown')}")
                st.markdown(f"**File:** {anomaly.get('file_path', 'Unknown')}")
                st.markdown(f"**Lines:** {anomaly.get('start_line', 0)}-{anomaly.get('end_line', 0)}")
                st.markdown(f"**Complexity:** {anomaly.get('complexity', 0)}")
                st.markdown(f"**Line Count:** {anomaly.get('line_count', 0)}")
            
            with col2:
                # Visual representation of anomaly score
                st.markdown(f"""
                <div style="
                    height: 100px;
                    background: linear-gradient(to top, rgba(255,0,0,{min(abs(anomaly_score)*2, 1.0)}), white);
                    border-radius: 5px;
                    text-align: center;
                    padding-top: 10px;
                    margin-bottom: 15px;
                ">
                    <h3 style="color: black;">Anomaly Score</h3>
                    <h2>{abs(anomaly_score):.3f}</h2>
                </div>
                """, unsafe_allow_html=True)


def add_pattern_recognition_tab():
    """Add the pattern recognition tab to the main UI"""
    return render_pattern_recognition_tab

def add_integrated_analysis_tab():
    """Add the integrated analysis tab to the main UI"""
    return render_integrated_analysis_tab

def render_integrated_analysis_tab():
    """Render the integrated analysis tab with workflow and pattern integration"""
    # Import integrated analysis module
    try:
        from workflow_pattern_integration import (
            WorkflowPatternIntegration, 
            get_integrated_analysis,
            get_enhanced_workflow_recommendations,
            analyze_critical_paths_with_patterns
        )
        INTEGRATION_AVAILABLE = True
    except ImportError as e:
        logger.error(f"Workflow pattern integration not available: {str(e)}")
        INTEGRATION_AVAILABLE = False
    
    st.header("🔄 Integrated Pattern & Workflow Analysis")
    st.markdown("""
    This advanced analysis integrates machine learning pattern recognition with workflow mapping
    to provide deeper insights and more targeted optimization recommendations.
    """)
    
    # Check if repository is available
    if not st.session_state.get('repo_path'):
        st.info("Please analyze a repository first to use the Integrated Analysis tool.")
        return
    
    # Check if integration module is available
    if not INTEGRATION_AVAILABLE:
        st.error("Workflow-Pattern Integration module is not available. Please check the installation.")
        return
    
    # Initialize session state for integrated analysis
    if 'integrated_analysis_results' not in st.session_state:
        st.session_state.integrated_analysis_results = None
    
    if 'enhanced_workflow_recommendations' not in st.session_state:
        st.session_state.enhanced_workflow_recommendations = None
    
    if 'critical_paths_analysis' not in st.session_state:
        st.session_state.critical_paths_analysis = None
    
    # Repository path
    repo_path = st.session_state.repo_path
    
    # Analysis options
    st.subheader("Integrated Analysis Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Run Integrated Analysis", type="primary"):
            with st.spinner("Running integrated pattern and workflow analysis..."):
                try:
                    results = get_integrated_analysis(repo_path)
                    st.session_state.integrated_analysis_results = results
                    st.success("Integrated analysis completed")
                except Exception as e:
                    st.error(f"Error running integrated analysis: {str(e)}")
                    logger.error(f"Integrated analysis error: {str(e)}")
    
    with col2:
        if st.button("Generate Enhanced Recommendations"):
            with st.spinner("Generating enhanced recommendations..."):
                try:
                    recommendations = get_enhanced_workflow_recommendations(repo_path)
                    st.session_state.enhanced_workflow_recommendations = recommendations
                    st.success("Recommendations generated")
                except Exception as e:
                    st.error(f"Error generating recommendations: {str(e)}")
                    logger.error(f"Recommendations error: {str(e)}")
    
    with col3:
        if st.button("Analyze Critical Paths"):
            with st.spinner("Analyzing critical paths with pattern correlation..."):
                try:
                    critical_paths = analyze_critical_paths_with_patterns(repo_path)
                    st.session_state.critical_paths_analysis = critical_paths
                    st.success("Critical path analysis completed")
                except Exception as e:
                    st.error(f"Error analyzing critical paths: {str(e)}")
                    logger.error(f"Critical path analysis error: {str(e)}")
    
    # Display results if available
    if st.session_state.integrated_analysis_results:
        display_integrated_analysis_results()
    
    if st.session_state.enhanced_workflow_recommendations:
        display_enhanced_recommendations()
    
    if st.session_state.critical_paths_analysis:
        display_critical_paths_analysis()

def display_integrated_analysis_results():
    """Display the results of the integrated analysis"""
    st.subheader("Integrated Analysis Results")
    
    results = st.session_state.integrated_analysis_results
    
    # Show integrated recommendations
    recommendations = results.get('integrated_recommendations', [])
    if recommendations:
        st.markdown("### 🔍 Key Optimization Opportunities")
        
        for i, recommendation in enumerate(recommendations):
            with st.expander(f"Recommendation {i+1}: {recommendation.get('workflow_component', 'Component')}"):
                st.markdown(f"**Recommendation:** {recommendation.get('recommendation', '')}")
                
                st.markdown("**File:** " + recommendation.get('file', 'N/A'))
                st.markdown("**Function:** " + recommendation.get('function', 'N/A'))
                st.markdown("**Performance Impact:** " + recommendation.get('performance_impact', 'Medium'))
                
                st.markdown("#### Related Patterns:")
                for pattern in recommendation.get('related_patterns', []):
                    severity_color = "orange"
                    if pattern.get('severity') == 'high':
                        severity_color = "red"
                    elif pattern.get('severity') == 'low':
                        severity_color = "blue"
                    elif pattern.get('severity') == 'positive':
                        severity_color = "green"
                    
                    st.markdown(f"<span style='color:{severity_color}'>●</span> **{pattern.get('pattern_name')}**: {pattern.get('pattern_description')}", unsafe_allow_html=True)
    else:
        st.info("No integrated recommendations found. This could be because there are no significant correlations between workflow bottlenecks and code patterns.")
    
    # Show refactoring opportunities
    refactoring = [r for r in recommendations if r.get('type') == 'refactoring']
    if refactoring:
        st.markdown("### 🔄 Refactoring Opportunities")
        
        for i, recommendation in enumerate(refactoring):
            with st.expander(f"Refactoring {i+1}: Cluster {recommendation.get('cluster_id', '')}"):
                st.markdown(f"**Recommendation:** {recommendation.get('recommendation', '')}")
                
                st.markdown(f"**File Count:** {recommendation.get('file_count', 0)}")
                
                st.markdown("**Sample Files:**")
                for file in recommendation.get('files', []):
                    st.markdown(f"- `{file}`")

def display_enhanced_recommendations():
    """Display enhanced workflow recommendations"""
    st.subheader("Enhanced Workflow Recommendations")
    
    recommendations = st.session_state.enhanced_workflow_recommendations
    
    if not recommendations:
        st.info("No enhanced workflow recommendations available.")
        return
    
    for i, recommendation in enumerate(recommendations):
        with st.expander(f"Recommendation {i+1}: {recommendation.get('name', 'Optimization')}"):
            st.markdown(f"**Description:** {recommendation.get('description', '')}")
            
            st.markdown("**Details:**")
            st.markdown(f"- **File:** {recommendation.get('file', 'N/A')}")
            st.markdown(f"- **Priority:** {recommendation.get('priority', 'Medium')}")
            st.markdown(f"- **Effort:** {recommendation.get('effort', 'Medium')}")
            
            # Show related patterns if available
            related_patterns = recommendation.get('related_patterns', [])
            if related_patterns:
                st.markdown("#### Related Code Patterns:")
                for pattern in related_patterns:
                    st.markdown(f"- **{pattern.get('pattern_name')}** ({pattern.get('pattern_type')}): {pattern.get('pattern_description')}")

def display_critical_paths_analysis():
    """Display critical paths analysis with pattern correlation"""
    st.subheader("Critical Paths with Pattern Analysis")
    
    analysis = st.session_state.critical_paths_analysis
    
    if not analysis or 'error' in analysis:
        st.info("No critical path analysis available or an error occurred.")
        if 'error' in analysis:
            st.error(f"Error: {analysis['error']}")
        return
    
    critical_paths = analysis.get('critical_paths', [])
    if not critical_paths:
        st.info("No critical paths identified in the workflow.")
        return
    
    st.markdown("### 🛑 Critical Path Analysis")
    st.markdown("""
    Critical paths represent the workflow sequences that determine the overall execution time.
    Optimizing these paths will have the most significant impact on performance.
    """)
    
    for i, path in enumerate(critical_paths):
        with st.expander(f"Critical Path {i+1}: {path.get('name', f'Path {i+1}')}"):
            st.markdown(f"**Path Length:** {len(path.get('nodes', []))} nodes")
            
            # Draw a simple visualization of the path
            dot_color = "red"
            path_html = ""
            
            for j, node in enumerate(path.get('nodes', [])):
                node_name = node.get('name', f'Node {j+1}')
                
                # Check if node has pattern issues
                has_issues = 'pattern_issues' in node and node['pattern_issues']
                node_color = "red" if has_issues else "gray"
                
                # Add node to path
                path_html += f'<span style="color:{node_color};">●</span> {node_name}'
                
                # Add connector if not the last node
                if j < len(path.get('nodes', [])) - 1:
                    path_html += ' <span style="color:gray;">→</span> '
            
            st.markdown(f"<div style='background-color:#f0f0f0; padding:10px; border-radius:5px;'>{path_html}</div>", unsafe_allow_html=True)
            
            # Show nodes with pattern issues
            nodes_with_issues = [n for n in path.get('nodes', []) if 'pattern_issues' in n and n['pattern_issues']]
            
            if nodes_with_issues:
                st.markdown("#### Nodes with Performance Issues:")
                
                for node in nodes_with_issues:
                    st.markdown(f"**{node.get('name', 'Node')}** ({node.get('file', 'Unknown file')})")
                    
                    for issue in node.get('pattern_issues', []):
                        severity_color = "orange"
                        if issue.get('severity') == 'high':
                            severity_color = "red"
                        elif issue.get('severity') == 'low':
                            severity_color = "blue"
                        
                        st.markdown(f"<span style='color:{severity_color}'>●</span> {issue.get('pattern_name')}: {issue.get('pattern_description')}", unsafe_allow_html=True)