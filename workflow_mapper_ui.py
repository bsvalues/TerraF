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
    from workflow_optimizer import WorkflowOptimizer
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
        st.session_state.workflow_optimizer = None
        st.session_state.optimizer_results = None
        st.session_state.selected_component_for_optimization = None
        st.session_state.component_optimization_plan = None
        
        # Set default repo path if not already set
        if 'repo_path' not in st.session_state:
            st.session_state.repo_path = os.getcwd()

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
            
            # Reset microservice analysis for workflow mode
            if 'microservice_analysis' in st.session_state:
                del st.session_state.microservice_analysis
            
        else:
            # Analyze all dependencies
            st.info("Analyzing all project dependencies...")
            all_data = analyze_all_dependencies(repo_path)
            
            st.session_state.workflow_dependencies_data = None
            st.session_state.dependency_graph_data = all_data.get('graph_data')
            
            # Store microservice analysis if available
            if 'microservice_analysis' in all_data:
                st.session_state.microservice_analysis = all_data['microservice_analysis']
                st.info(f"Detected {len(all_data['microservice_analysis'].get('microservices', []))} microservices in the TerraFusion architecture.")
        
        # Generate recommendations and run workflow optimization
        if st.session_state.dependency_graph_data:
            # Generate traditional recommendations
            st.session_state.optimization_recommendations = generate_optimization_recommendations(
                st.session_state.dependency_graph_data
            )
            
            # Initialize and run the workflow optimizer
            st.info("Running advanced workflow optimization analysis...")
            workflow_optimizer = WorkflowOptimizer(repo_path)
            optimization_results = workflow_optimizer.analyze_repository()
            
            # Store optimizer and results in session state
            st.session_state.workflow_optimizer = workflow_optimizer
            st.session_state.optimizer_results = optimization_results
            
            st.success("Dependency analysis and workflow optimization completed successfully!")
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
            # Show tabs for different visualization types
            viz_tabs = st.tabs(["Module Dependencies", "Bottleneck Analysis", "Critical Paths", "Microservice Architecture", "Optimization Recommendations"])
            
            with viz_tabs[0]:  # Module Dependencies
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
            
            with viz_tabs[1]:  # Bottleneck Analysis
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
                else:
                    st.info("No bottlenecks detected in the codebase.")
            
            with viz_tabs[2]:  # Critical Paths
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
                else:
                    st.info("No critical paths detected in the codebase.")
            
            with viz_tabs[3]:  # Microservice Architecture
                # Display microservice architecture analysis
                microservice_analysis = st.session_state.get('microservice_analysis')
                
            with viz_tabs[4]:  # Optimization Recommendations
                st.markdown("### Workflow Optimization Recommendations")
                
                # Check if we have optimization results
                optimizer_results = st.session_state.get('optimizer_results')
                if optimizer_results:
                    # Display summary metrics
                    st.markdown("#### Workflow Complexity Overview")
                    
                    complexity_metrics = optimizer_results.get('performance_metrics', {}).get('complexity', {})
                    if complexity_metrics:
                        cols = st.columns(3)
                        with cols[0]:
                            st.metric("Average Complexity", f"{complexity_metrics.get('average_complexity', 0):.1f}")
                        with cols[1]:
                            st.metric("Cyclomatic Complexity", complexity_metrics.get('cyclomatic_complexity', 0))
                        with cols[2]:
                            st.metric("Connected Components", complexity_metrics.get('strongly_connected_components', 0))
                    
                    # Display highest complexity components
                    high_complexity = complexity_metrics.get('highest_complexity_components', [])
                    if high_complexity:
                        st.markdown("#### Highest Complexity Components")
                        for item in high_complexity:
                            st.markdown(f"- **{os.path.basename(item['file'])}**: {item['complexity']:.1f}")
                    
                    # Display optimization recommendations
                    optimizer = st.session_state.get('workflow_optimizer')
                    if optimizer:
                        st.markdown("#### Recommended Optimizations")
                        
                        # Filtering options
                        col1, col2 = st.columns(2)
                        with col1:
                            impact_filter = st.selectbox(
                                "Filter by Impact",
                                ["All", "High", "Medium", "Low"],
                                index=0
                            )
                        
                        with col2:
                            component_filter = st.text_input(
                                "Filter by Component",
                                ""
                            )
                        
                        # Convert filters to appropriate format for the optimizer
                        impact = impact_filter.lower() if impact_filter != "All" else None
                        component = component_filter if component_filter else None
                        
                        # Get recommendations with filters
                        recommendations = optimizer.get_optimization_recommendations(
                            component_filter=component,
                            impact_filter=impact
                        )
                        
                        if recommendations:
                            st.markdown(f"Found **{len(recommendations)}** optimization recommendations")
                            
                            # Show recommendations with expandable details
                            for i, rec in enumerate(recommendations):
                                # Determine icon based on impact
                                impact_icon = {
                                    'high': '🔴',
                                    'medium': '🟠',
                                    'low': '🟡'
                                }.get(rec.get('impact', 'low'), '⚪')
                                
                                # Determine icon based on type
                                type_icon = {
                                    'bottleneck_refactoring': '🔄',
                                    'circular_dependency': '🔁',
                                    'complexity_reduction': '📉',
                                    'long_execution_path': '⛓️',
                                    'standardization': '📋',
                                    'framework_adoption': '🧰',
                                    'framework_standardization': '🔧',
                                    'parallelization': '⚡'
                                }.get(rec.get('type', ''), '🔨')
                                
                                # Format the title
                                title = f"{impact_icon} {type_icon} **{rec.get('description', 'Optimization Recommendation')}**"
                                
                                with st.expander(title, expanded=i==0):
                                    st.markdown(f"**Type:** {rec.get('type', '').replace('_', ' ').title()}")
                                    st.markdown(f"**Impact:** {rec.get('impact', 'Unknown').title()}")
                                    st.markdown(f"**Urgency:** {rec.get('urgency', 'Unknown').title()}")
                                    
                                    if 'details' in rec:
                                        st.markdown(f"**Details:** {rec['details']}")
                                    
                                    if 'component' in rec and rec['component'] != 'all':
                                        st.markdown(f"**Component:** `{rec['component']}`")
                                    
                                    if 'components' in rec:
                                        components = rec['components']
                                        if isinstance(components, list) and components:
                                            st.markdown("**Affected Components:**")
                                            for comp in components:
                                                st.markdown(f"- `{comp}`")
                                    
                                    if 'suggestions' in rec:
                                        st.markdown("**Suggested Actions:**")
                                        for suggestion in rec['suggestions']:
                                            st.markdown(f"- {suggestion}")
                                    
                                    # Add a button to get detailed optimization plan
                                    if 'component' in rec and rec['component'] != 'all':
                                        component_path = rec['component']
                                        if st.button(f"Generate Optimization Plan for {os.path.basename(component_path)}", key=f"opt_plan_{i}"):
                                            with st.spinner(f"Generating optimization plan for {os.path.basename(component_path)}..."):
                                                optimization_plan = optimizer.optimize_workflow(component_path)
                                                st.session_state.component_optimization_plan = optimization_plan
                                                st.session_state.selected_component_for_optimization = component_path
                            
                            # Display the detailed optimization plan if available
                            if st.session_state.get('component_optimization_plan'):
                                plan = st.session_state.component_optimization_plan
                                component = st.session_state.selected_component_for_optimization
                                
                                st.markdown(f"### Optimization Plan for {os.path.basename(component)}")
                                
                                # Effort estimation
                                effort = plan.get('estimated_effort', {})
                                effort_level = effort.get('level', 'unknown')
                                effort_days = effort.get('days_estimate', 0)
                                
                                effort_color = {
                                    'high': '🔴',
                                    'medium': '🟠',
                                    'low': '🟢'
                                }.get(effort_level, '⚪')
                                
                                st.markdown(f"**Estimated Effort:** {effort_color} {effort_level.title()} ({effort_days} days)")
                                
                                # Expected benefits
                                benefits = plan.get('expected_benefits', {})
                                if benefits:
                                    st.markdown("**Expected Benefits:**")
                                    benefit_cols = st.columns(3)
                                    
                                    benefit_icons = {
                                        'high': '🟢',
                                        'medium': '🟠',
                                        'low': '🔴'
                                    }
                                    
                                    with benefit_cols[0]:
                                        perf = benefits.get('performance', 'unknown')
                                        st.markdown(f"Performance: {benefit_icons.get(perf, '⚪')} {perf.title()}")
                                        
                                    with benefit_cols[1]:
                                        maint = benefits.get('maintainability', 'unknown')
                                        st.markdown(f"Maintainability: {benefit_icons.get(maint, '⚪')} {maint.title()}")
                                        
                                    with benefit_cols[2]:
                                        rel = benefits.get('reliability', 'unknown')
                                        st.markdown(f"Reliability: {benefit_icons.get(rel, '⚪')} {rel.title()}")
                                
                                # Implementation steps
                                steps = plan.get('implementation_steps', [])
                                if steps:
                                    st.markdown("**Implementation Steps:**")
                                    
                                    for step in steps:
                                        step_num = step.get('step', 0)
                                        title = step.get('title', 'Implementation Step')
                                        description = step.get('description', '')
                                        
                                        with st.expander(f"Step {step_num}: {title}"):
                                            st.markdown(description)
                                            
                                            tasks = step.get('tasks', [])
                                            if tasks:
                                                st.markdown("**Tasks:**")
                                                for task in tasks:
                                                    st.markdown(f"- {task}")
                        else:
                            st.info("No optimization recommendations match the current filters.")
                else:
                    st.info("Run the dependency analysis to generate optimization recommendations.")
                if microservice_analysis:
                    st.markdown("### TerraFusion Microservice Architecture Analysis")
                    
                    # Show microservices
                    microservices = microservice_analysis.get('microservices', [])
                    if microservices:
                        st.markdown(f"#### Detected Microservices ({len(microservices)})")
                        
                        ms_cols = st.columns(min(len(microservices), 3))
                        for i, microservice in enumerate(microservices):
                            col_index = i % len(ms_cols)
                            with ms_cols[col_index]:
                                ms_name = microservice.get('name', 'Unknown')
                                ms_type = microservice.get('type', 'unknown')
                                ms_path = microservice.get('path', '')
                                ms_endpoints = microservice.get('api_endpoints', [])
                                
                                # Determine icon based on service type
                                icon = "🔹"
                                if ms_type == "python":
                                    icon = "🐍"
                                elif ms_type in ["nodejs", "typescript"]:
                                    icon = "🟢"
                                elif ms_type == "java":
                                    icon = "☕"
                                elif ms_type == "go":
                                    icon = "🔵"
                                
                                st.markdown(f"##### {icon} {ms_name}")
                                st.markdown(f"**Type:** {ms_type}")
                                st.markdown(f"**Path:** `{ms_path}`")
                                
                                if ms_endpoints:
                                    with st.expander(f"API Endpoints ({len(ms_endpoints)})", expanded=False):
                                        for endpoint in ms_endpoints:
                                            st.markdown(f"- `{endpoint.get('file')}` ({endpoint.get('type')})")
                        
                        # Create a visualization of the microservice architecture
                        st.markdown("#### Microservice Architecture Visualization")
                        
                        # Create a placeholder for the graph
                        if len(microservices) > 0:
                            try:
                                import plotly.graph_objects as go
                                import networkx as nx
                                
                                # Create a graph for visualization
                                G = nx.DiGraph()
                                
                                # Add microservice nodes
                                for ms in microservices:
                                    G.add_node(ms['name'], 
                                             type=ms['type'], 
                                             path=ms['path'])
                                
                                # Add connections between services
                                service_comms = microservice_analysis.get('service_communications', [])
                                for comm in service_comms:
                                    source = comm.get('source_service')
                                    target = comm.get('target_service')
                                    comm_type = comm.get('type')
                                    
                                    if source and target:
                                        G.add_edge(source, target, type=comm_type)
                                
                                # Create a spring layout
                                pos = nx.spring_layout(G, seed=42)
                                
                                # Create edge traces
                                edge_x = []
                                edge_y = []
                                edge_text = []
                                
                                for edge in G.edges(data=True):
                                    x0, y0 = pos[edge[0]]
                                    x1, y1 = pos[edge[1]]
                                    
                                    edge_x.extend([x0, x1, None])
                                    edge_y.extend([y0, y1, None])
                                    
                                    edge_text.append(edge[2].get('type', 'connection'))
                                
                                edge_trace = go.Scatter(
                                    x=edge_x, y=edge_y,
                                    line=dict(width=1.5, color='rgba(50, 50, 50, 0.8)'),
                                    hoverinfo='none',
                                    mode='lines'
                                )
                                
                                # Create node traces based on service type
                                node_types = set(nx.get_node_attributes(G, 'type').values())
                                
                                node_traces = []
                                
                                for node_type in node_types:
                                    nodes_of_type = [n for n, data in G.nodes(data=True) if data.get('type') == node_type]
                                    
                                    node_x = []
                                    node_y = []
                                    node_text = []
                                    
                                    for node in nodes_of_type:
                                        x, y = pos[node]
                                        node_x.append(x)
                                        node_y.append(y)
                                        node_text.append(node)
                                    
                                    # Determine color based on type
                                    color = 'rgba(31, 119, 180, 0.8)'  # Default blue
                                    if node_type == 'python':
                                        color = 'rgba(44, 160, 44, 0.8)'  # Green
                                    elif node_type in ['nodejs', 'typescript']:
                                        color = 'rgba(255, 127, 14, 0.8)'  # Orange
                                    elif node_type == 'java':
                                        color = 'rgba(214, 39, 40, 0.8)'  # Red
                                    elif node_type == 'go':
                                        color = 'rgba(148, 103, 189, 0.8)'  # Purple
                                    
                                    node_trace = go.Scatter(
                                        x=node_x, y=node_y,
                                        mode='markers+text',
                                        text=node_text,
                                        textposition="top center",
                                        marker=dict(
                                            showscale=False,
                                            color=color,
                                            size=20,
                                            line=dict(width=1, color='rgba(0, 0, 0, 0.8)')
                                        ),
                                        hoverinfo='text',
                                        hovertext=node_text,
                                        name=node_type
                                    )
                                    
                                    node_traces.append(node_trace)
                                
                                # Create figure
                                fig = go.Figure(data=[edge_trace] + node_traces,
                                              layout=go.Layout(
                                                  title='Microservice Architecture',
                                                  titlefont=dict(size=16),
                                                  showlegend=True,
                                                  hovermode='closest',
                                                  margin=dict(b=20, l=5, r=5, t=40),
                                                  xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                                  yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                                  legend=dict(
                                                      yanchor="top",
                                                      y=0.99,
                                                      xanchor="left",
                                                      x=0.01
                                                  ),
                                                  height=600,
                                                  paper_bgcolor='rgba(255, 255, 255, 1)',
                                                  plot_bgcolor='rgba(255, 255, 255, 1)'
                                              ))
                                
                                st.plotly_chart(fig, use_container_width=True)
                            except Exception as e:
                                st.error(f"Error creating microservice visualization: {str(e)}")
                    else:
                        st.info("No microservices detected in the codebase.")
                    
                    # Show API gateways
                    api_gateways = microservice_analysis.get('api_gateways', [])
                    if api_gateways:
                        st.markdown(f"#### API Gateways ({len(api_gateways)})")
                        
                        for i, gateway in enumerate(api_gateways):
                            file = gateway.get('file', 'Unknown')
                            gateway_type = gateway.get('type', 'unknown')
                            routes = gateway.get('routes', [])
                            
                            st.markdown(f"**Gateway {i+1}:** `{file}` ({gateway_type})")
                            
                            if routes:
                                st.markdown(f"Routes: {', '.join(routes)}")
                    
                    # Show plugin architecture
                    plugins = microservice_analysis.get('plugins', [])
                    if plugins:
                        st.markdown(f"#### Plugin Architecture ({len(plugins)})")
                        
                        # Separate plugins and loaders
                        regular_plugins = [p for p in plugins if not p.get('is_loader', False)]
                        loaders = [p for p in plugins if p.get('is_loader', False)]
                        
                        plugin_cols = st.columns(2)
                        with plugin_cols[0]:
                            st.markdown(f"**Plugins ({len(regular_plugins)})**")
                            for plugin in regular_plugins:
                                name = plugin.get('name', 'Unknown')
                                plugin_type = plugin.get('type', 'unknown')
                                config_files = plugin.get('config_files', [])
                                
                                st.markdown(f"- **{name}** ({plugin_type})")
                                if config_files:
                                    st.markdown(f"  Config: {', '.join(config_files)}")
                        
                        with plugin_cols[1]:
                            st.markdown(f"**Plugin Loaders ({len(loaders)})**")
                            for loader in loaders:
                                name = loader.get('name', 'Unknown')
                                loader_type = loader.get('type', 'unknown')
                                
                                st.markdown(f"- **{name}** ({loader_type})")
                    
                    # Show recommendations for microservice architecture
                    recommendations = microservice_analysis.get('recommendations', [])
                    if recommendations:
                        st.markdown("#### TerraFusion-Specific Recommendations")
                        
                        for i, recommendation in enumerate(recommendations):
                            st.markdown(f"{i+1}. {recommendation}")
                else:
                    st.info("No microservice architecture analysis data available. Please run the analysis with 'All Dependencies' mode.")
            
            # Display optimization recommendations at the bottom
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