"""
Workflow Visualization Module

This module provides enhanced visualization capabilities for workflow analysis,
including interactive dependency graphs, bottleneck analysis, critical path visualization,
and performance metrics dashboards.
"""

import os
import time
import logging
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_dependency_network(graph_data: Dict[str, Any], layout: str = "force") -> go.Figure:
    """
    Create an interactive network visualization of module dependencies
    
    Parameters:
    - graph_data: Graph data containing nodes and edges
    - layout: Layout algorithm to use (force, circular, radial, etc.)
    
    Returns:
    - Interactive Plotly figure
    """
    logger.info(f"Creating dependency network visualization with {layout} layout...")
    
    # Extract nodes and edges
    nodes = graph_data.get('graph', {}).get('nodes', [])
    edges = graph_data.get('graph', {}).get('edges', [])
    bottlenecks = graph_data.get('bottlenecks', [])
    
    if not nodes:
        # Return empty figure if no data
        fig = go.Figure()
        fig.add_annotation(text="No dependency data available", 
                          showarrow=False, font=dict(size=14))
        fig.update_layout(title="Module Dependencies")
        return fig
    
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add nodes
    for node in nodes:
        G.add_node(node['id'], 
                 label=node.get('label', node['id']),
                 time_complexity=node.get('time_complexity', 1),
                 memory_complexity=node.get('memory_complexity', 1))
    
    # Add edges
    for edge in edges:
        G.add_edge(edge['source'], edge['target'], weight=edge.get('weight', 1))
    
    # Create a bottleneck lookup for highlighting
    bottleneck_lookup = {b['file']: b for b in bottlenecks}
    
    # Calculate node positions based on selected layout
    if layout == "circular":
        pos = nx.circular_layout(G)
    elif layout == "spring":
        pos = nx.spring_layout(G, k=0.15, iterations=50)
    elif layout == "kamada_kawai":
        pos = nx.kamada_kawai_layout(G)
    elif layout == "spectral":
        pos = nx.spectral_layout(G)
    else:  # default to force-directed (spring layout)
        pos = nx.spring_layout(G, k=0.2, iterations=100)
    
    # Prepare node data for plotting
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    node_color = []
    
    for node_id in G.nodes():
        x, y = pos[node_id]
        node_label = G.nodes[node_id].get('label', os.path.basename(node_id))
        time_complexity = G.nodes[node_id].get('time_complexity', 1)
        memory_complexity = G.nodes[node_id].get('memory_complexity', 1)
        
        node_x.append(x)
        node_y.append(y)
        
        # Scale node size based on complexity
        size = 10 + (time_complexity + memory_complexity) / 2
        node_size.append(size)
        
        # Node color based on bottleneck status
        if node_id in bottleneck_lookup:
            # Color based on bottleneck severity
            severity = bottleneck_lookup[node_id].get('severity', 0)
            if severity > 0.5:
                color = 'rgba(255, 0, 0, 0.8)'  # Red for high severity
            elif severity > 0.3:
                color = 'rgba(255, 165, 0, 0.8)'  # Orange for medium severity
            else:
                color = 'rgba(255, 255, 0, 0.8)'  # Yellow for low severity
        else:
            color = 'rgba(64, 164, 223, 0.8)'  # Blue for normal nodes
        
        node_color.append(color)
        
        # Node tooltip
        tooltip = f"<b>{node_label}</b><br>"
        tooltip += f"File: {node_id}<br>"
        tooltip += f"Time Complexity: {time_complexity}<br>"
        tooltip += f"Memory Complexity: {memory_complexity}<br>"
        
        if node_id in bottleneck_lookup:
            b_info = bottleneck_lookup[node_id]
            tooltip += f"<b>BOTTLENECK</b><br>"
            tooltip += f"Centrality: {b_info.get('centrality', 0):.3f}<br>"
            tooltip += f"Incoming Dependencies: {b_info.get('in_degree', 0)}<br>"
            tooltip += f"Outgoing Dependencies: {b_info.get('out_degree', 0)}<br>"
            tooltip += f"Severity: {b_info.get('severity', 0):.2f}"
        
        node_text.append(tooltip)
    
    # Prepare edge data for plotting
    edge_x = []
    edge_y = []
    edge_width = []
    
    for source, target, data in G.edges(data=True):
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        
        # Add curved edges for better visibility
        # Calculate angle of the edge
        angle = np.arctan2(y1 - y0, x1 - x0)
        
        # Calculate offset for curved edges
        offset = 0.03
        mid_x = (x0 + x1) / 2 + offset * np.sin(angle)
        mid_y = (y0 + y1) / 2 - offset * np.cos(angle)
        
        # Create curved path
        edge_x.append(x0)
        edge_x.append(mid_x)
        edge_x.append(x1)
        edge_x.append(None)  # Breaks the line
        
        edge_y.append(y0)
        edge_y.append(mid_y)
        edge_y.append(y1)
        edge_y.append(None)  # Breaks the line
        
        # Edge width based on weight
        weight = data.get('weight', 1)
        edge_width.append(1 + weight * 0.5)
    
    # Create edge trace
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='rgba(128, 128, 128, 0.5)'),
        hoverinfo='none',
        mode='lines',
        showlegend=False
    )
    
    # Create arrow trace for direction indication
    arrow_x = []
    arrow_y = []
    arrow_u = []
    arrow_v = []
    
    for source, target in G.edges():
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        
        # Position the arrow 70% of the way along the edge
        arrow_pos = 0.7
        arrow_x.append(x0 + arrow_pos * (x1 - x0))
        arrow_y.append(y0 + arrow_pos * (y1 - y0))
        
        # Direction vector (normalized to small value for arrow size)
        dx = (x1 - x0) * 0.02
        dy = (y1 - y0) * 0.02
        
        arrow_u.append(dx)
        arrow_v.append(dy)
    
    # Create arrow trace
    arrow_trace = go.Scatter(
        x=arrow_x, y=arrow_y,
        mode='markers',
        marker=dict(symbol='arrow', 
                   size=8, 
                   angleref='previous',
                   angle=45,  # This is ignored due to angleref
                   color='rgba(50, 50, 50, 0.8)'),
        hoverinfo='none',
        showlegend=False
    )
    
    # Create node trace
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=[G.nodes[n].get('label', os.path.basename(n)) for n in G.nodes()],
        textposition="bottom center",
        textfont=dict(size=10, color='black'),
        marker=dict(
            showscale=False,
            size=node_size,
            color=node_color,
            line=dict(width=1, color='rgba(50, 50, 50, 0.8)')
        ),
        hoverinfo='text',
        hovertext=node_text,
        showlegend=False
    )
    
    # Create figure with all traces
    fig = go.Figure(data=[edge_trace, node_trace])
    
    # Update layout
    fig.update_layout(
        title="Module Dependencies",
        titlefont=dict(size=16),
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(248, 249, 250, 1)',
        width=800,
        height=600,
    )
    
    # Add legend for bottleneck severity
    legend_x = 1.05
    legend_y = 1.0
    
    fig.add_annotation(
        x=legend_x, y=legend_y,
        xref="paper", yref="paper",
        text="Bottleneck Severity",
        showarrow=False,
        font=dict(size=12),
        align="left"
    )
    
    fig.add_shape(
        type="rect", xref="paper", yref="paper",
        x0=legend_x, y0=legend_y-0.05, x1=legend_x+0.03, y1=legend_y-0.02,
        fillcolor="rgba(255, 0, 0, 0.8)", line=dict(width=1)
    )
    
    fig.add_annotation(
        x=legend_x+0.05, y=legend_y-0.035,
        xref="paper", yref="paper",
        text="High",
        showarrow=False,
        font=dict(size=10),
        align="left"
    )
    
    fig.add_shape(
        type="rect", xref="paper", yref="paper",
        x0=legend_x, y0=legend_y-0.09, x1=legend_x+0.03, y1=legend_y-0.06,
        fillcolor="rgba(255, 165, 0, 0.8)", line=dict(width=1)
    )
    
    fig.add_annotation(
        x=legend_x+0.05, y=legend_y-0.075,
        xref="paper", yref="paper",
        text="Medium",
        showarrow=False,
        font=dict(size=10),
        align="left"
    )
    
    fig.add_shape(
        type="rect", xref="paper", yref="paper",
        x0=legend_x, y0=legend_y-0.13, x1=legend_x+0.03, y1=legend_y-0.10,
        fillcolor="rgba(255, 255, 0, 0.8)", line=dict(width=1)
    )
    
    fig.add_annotation(
        x=legend_x+0.05, y=legend_y-0.115,
        xref="paper", yref="paper",
        text="Low",
        showarrow=False,
        font=dict(size=10),
        align="left"
    )
    
    fig.add_shape(
        type="rect", xref="paper", yref="paper",
        x0=legend_x, y0=legend_y-0.17, x1=legend_x+0.03, y1=legend_y-0.14,
        fillcolor="rgba(64, 164, 223, 0.8)", line=dict(width=1)
    )
    
    fig.add_annotation(
        x=legend_x+0.05, y=legend_y-0.155,
        xref="paper", yref="paper",
        text="Normal",
        showarrow=False,
        font=dict(size=10),
        align="left"
    )
    
    return fig

def create_bottleneck_heatmap(graph_data: Dict[str, Any]) -> go.Figure:
    """
    Create a heatmap visualization of bottlenecks and their properties
    
    Parameters:
    - graph_data: Graph data containing bottleneck information
    
    Returns:
    - Interactive Plotly heatmap
    """
    bottlenecks = graph_data.get('bottlenecks', [])
    
    if not bottlenecks:
        # Return empty figure if no bottlenecks
        fig = go.Figure()
        fig.add_annotation(text="No bottlenecks detected", 
                          showarrow=False, font=dict(size=14))
        fig.update_layout(title="Bottleneck Analysis")
        return fig
    
    # Prepare data for the heatmap
    x_labels = ['Centrality', 'In-Degree', 'Out-Degree', 'Severity']
    y_labels = [os.path.basename(b['file']) for b in bottlenecks[:10]]  # Top 10 bottlenecks
    
    # Create data matrix
    z_data = []
    for bottleneck in bottlenecks[:10]:
        # Normalize values for better visualization
        centrality = bottleneck.get('centrality', 0)
        in_degree = bottleneck.get('in_degree', 0) / 10  # Scale down for large values
        out_degree = bottleneck.get('out_degree', 0) / 10  # Scale down for large values
        severity = bottleneck.get('severity', 0)
        
        z_data.append([centrality, in_degree, out_degree, severity])
    
    # Create the heatmap figure
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=x_labels,
        y=y_labels,
        colorscale='YlOrRd',
        text=[[f"Centrality: {bottlenecks[i].get('centrality', 0):.3f}",
              f"In-Degree: {bottlenecks[i].get('in_degree', 0)}",
              f"Out-Degree: {bottlenecks[i].get('out_degree', 0)}",
              f"Severity: {bottlenecks[i].get('severity', 0):.2f}"]
              for i in range(min(10, len(bottlenecks)))],
        hoverinfo="text+y",
    ))
    
    # Update layout
    fig.update_layout(
        title="Bottleneck Analysis Heatmap",
        xaxis_title="Metrics",
        yaxis_title="Modules",
        xaxis_nticks=4,
        width=750,
        height=400,
    )
    
    return fig

def create_critical_path_sunburst(graph_data: Dict[str, Any]) -> go.Figure:
    """
    Create a sunburst visualization of critical paths and cycles
    
    Parameters:
    - graph_data: Graph data containing critical path information
    
    Returns:
    - Interactive Plotly sunburst figure
    """
    critical_paths = graph_data.get('critical_paths', [])
    
    if not critical_paths:
        # Return empty figure if no critical paths
        fig = go.Figure()
        fig.add_annotation(text="No critical paths detected", 
                          showarrow=False, font=dict(size=14))
        fig.update_layout(title="Critical Path Analysis")
        return fig
    
    # Prepare data for sunburst
    labels = []
    parents = []
    values = []
    colors = []
    
    # Add root node
    labels.append("Root")
    parents.append("")
    values.append(1)
    colors.append("#FFFFFF")  # White for the center
    
    # Add path type nodes
    path_types = {"cycle": "Circular Dependencies", "path": "Long Chains"}
    
    for path_type, display_name in path_types.items():
        paths_of_type = [p for p in critical_paths if p['type'] == path_type]
        
        if paths_of_type:
            # Add a node for this path type
            labels.append(display_name)
            parents.append("Root")
            values.append(len(paths_of_type))
            colors.append("#ADD8E6" if path_type == "path" else "#FFB6C1")  # Light blue for paths, light pink for cycles
            
            # Add nodes for each path
            for i, path in enumerate(paths_of_type):
                path_name = f"{display_name} {i+1}"
                path_length = path.get('length', 0)
                
                labels.append(path_name)
                parents.append(display_name)
                values.append(path_length)
                
                # Color based on severity
                severity = path.get('severity', 'medium')
                if severity == 'high':
                    color = "#FF6347"  # Tomato
                elif severity == 'medium':
                    color = "#FFA500"  # Orange
                else:
                    color = "#FFFF00"  # Yellow
                
                colors.append(color)
                
                # Add individual files in the path
                path_files = path.get('path', [])
                for j, file_path in enumerate(path_files):
                    file_name = os.path.basename(file_path)
                    
                    labels.append(f"{file_name} ({j+1})")
                    parents.append(path_name)
                    values.append(1)
                    colors.append("#DDDDDD")  # Light gray for individual files
    
    # Create sunburst figure
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(
            colors=colors,
            line=dict(width=0.5, color='#FFFFFF')
        ),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Parent: %{parent}',
        maxdepth=2  # Limit the depth shown initially
    ))
    
    # Update layout
    fig.update_layout(
        title="Critical Path Analysis",
        margin=dict(t=30, b=10, l=10, r=10),
        width=700,
        height=700,
    )
    
    return fig

def create_complexity_radar(optimizer_results: Dict[str, Any], top_n: int = 5) -> go.Figure:
    """
    Create a radar chart of module complexity metrics
    
    Parameters:
    - optimizer_results: Results from the workflow optimizer
    - top_n: Number of top complexity components to show
    
    Returns:
    - Interactive Plotly radar chart
    """
    # Check for required data
    if not optimizer_results or 'component_metrics' not in optimizer_results:
        # Return empty figure if data not available
        fig = go.Figure()
        fig.add_annotation(text="No complexity data available", 
                          showarrow=False, font=dict(size=14))
        fig.update_layout(title="Module Complexity Analysis")
        return fig
    
    # Get component metrics
    component_metrics = optimizer_results.get('component_metrics', [])
    
    # Sort by total complexity
    component_metrics.sort(key=lambda x: x.get('total_complexity', 0), reverse=True)
    
    # Take top N components
    top_components = component_metrics[:top_n]
    
    # Metrics to display in the radar chart
    metrics = ['cyclomatic_complexity', 'cognitive_complexity', 'dependency_complexity', 
              'tangled_code_ratio', 'change_frequency']
    
    # Metric labels
    metric_labels = [
        'Cyclomatic Complexity',
        'Cognitive Complexity',
        'Dependency Complexity',
        'Code Tangling',
        'Change Frequency'
    ]
    
    # Create figure with subplots
    fig = go.Figure()
    
    # Add a trace for each component
    for component in top_components:
        component_name = os.path.basename(component.get('file', 'Unknown'))
        values = [
            component.get('cyclomatic_complexity', 0),
            component.get('cognitive_complexity', 0),
            component.get('dependency_complexity', 0),
            component.get('tangled_code_ratio', 0) * 10,  # Scale up for visibility
            component.get('change_frequency', 0) * 5,     # Scale up for visibility
        ]
        
        # Close the polygon by appending the first value
        values.append(values[0])
        
        # Add the trace
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=metric_labels + [metric_labels[0]],  # Close the circle
            fill='toself',
            name=component_name,
            opacity=0.7
        ))
    
    # Update layout
    fig.update_layout(
        title="Module Complexity Radar Chart",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max([
                    max([c.get('cyclomatic_complexity', 0) for c in top_components]),
                    max([c.get('cognitive_complexity', 0) for c in top_components]),
                    max([c.get('dependency_complexity', 0) for c in top_components]),
                    max([c.get('tangled_code_ratio', 0) * 10 for c in top_components]),
                    max([c.get('change_frequency', 0) * 5 for c in top_components])
                ]) * 1.2]  # Add 20% for margin
            )
        ),
        showlegend=True,
        width=700,
        height=500,
    )
    
    return fig

def create_optimization_treemap(optimizer_results: Dict[str, Any]) -> go.Figure:
    """
    Create a treemap visualization of optimization recommendations
    
    Parameters:
    - optimizer_results: Results from the workflow optimizer
    
    Returns:
    - Interactive Plotly treemap
    """
    # Check for required data
    if not optimizer_results or 'recommendations' not in optimizer_results:
        # Return empty figure if data not available
        fig = go.Figure()
        fig.add_annotation(text="No optimization recommendations available", 
                          showarrow=False, font=dict(size=14))
        fig.update_layout(title="Optimization Recommendations")
        return fig
    
    # Get recommendations
    recommendations = optimizer_results.get('recommendations', [])
    
    if not recommendations:
        # Return empty figure if no recommendations
        fig = go.Figure()
        fig.add_annotation(text="No optimization recommendations available", 
                          showarrow=False, font=dict(size=14))
        fig.update_layout(title="Optimization Recommendations")
        return fig
    
    # Create hierarchical data structure
    labels = []
    parents = []
    values = []
    text = []
    colors = []
    
    # Add root
    labels.append("Optimizations")
    parents.append("")
    values.append(len(recommendations))
    text.append("All optimization recommendations")
    colors.append("#FFFFFF")
    
    # Group by impact
    impact_groups = {}
    for rec in recommendations:
        impact = rec.get('impact', 'medium').lower()
        if impact not in impact_groups:
            impact_groups[impact] = []
        impact_groups[impact].append(rec)
    
    # Add impact level nodes
    impact_colors = {
        'high': '#FF6347',  # Tomato
        'medium': '#FFA500',  # Orange
        'low': '#FFFF00'  # Yellow
    }
    
    for impact, recs in impact_groups.items():
        impact_label = f"{impact.capitalize()} Impact"
        labels.append(impact_label)
        parents.append("Optimizations")
        values.append(len(recs))
        text.append(f"{len(recs)} {impact} impact recommendations")
        colors.append(impact_colors.get(impact, '#DDDDDD'))
        
        # Group by category within each impact level
        category_groups = {}
        for rec in recs:
            category = rec.get('category', 'general')
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(rec)
        
        # Add category nodes under impact levels
        for category, cat_recs in category_groups.items():
            category_label = f"{impact.capitalize()}: {category.capitalize()}"
            labels.append(category_label)
            parents.append(impact_label)
            values.append(len(cat_recs))
            text.append(f"{len(cat_recs)} recommendations for {category}")
            
            # Lighter shade of the impact color
            color = impact_colors.get(impact, '#DDDDDD')
            # Convert to RGB, lighten, convert back
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            r = min(255, int(r * 1.2))
            g = min(255, int(g * 1.2))
            b = min(255, int(b * 1.2))
            lighter_color = f"#{r:02x}{g:02x}{b:02x}"
            
            colors.append(lighter_color)
            
            # Add individual recommendation nodes
            for i, rec in enumerate(cat_recs):
                component = rec.get('component', 'Unknown')
                component_name = os.path.basename(component)
                
                rec_label = f"{category.capitalize()}: {component_name} ({i+1})"
                labels.append(rec_label)
                parents.append(category_label)
                values.append(1)
                
                # Create detailed tooltip
                tip = f"<b>{component_name}</b><br>"
                tip += f"Component: {component}<br>"
                tip += f"Impact: {impact.capitalize()}<br>"
                tip += f"Category: {category.capitalize()}<br>"
                tip += f"Description: {rec.get('description', 'No description')}<br>"
                
                if 'before' in rec and 'after' in rec:
                    tip += f"Estimated Improvement: {rec.get('before', 0)} → {rec.get('after', 0)}"
                
                text.append(tip)
                
                # Even lighter shade
                r, g, b = int(lighter_color[1:3], 16), int(lighter_color[3:5], 16), int(lighter_color[5:7], 16)
                r = min(255, int(r * 1.1))
                g = min(255, int(g * 1.1))
                b = min(255, int(b * 1.1))
                lightest_color = f"#{r:02x}{g:02x}{b:02x}"
                
                colors.append(lightest_color)
    
    # Create treemap figure
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        text=text,
        hovertemplate='<b>%{label}</b><br>%{text}',
        marker=dict(
            colors=colors,
            line=dict(width=0.5, color='#FFFFFF')
        ),
        maxdepth=2  # Limit initial depth
    ))
    
    # Update layout
    fig.update_layout(
        title="Optimization Recommendations",
        margin=dict(t=30, b=10, l=10, r=10),
        width=800,
        height=600,
    )
    
    return fig

def create_dependency_sankey(graph_data: Dict[str, Any], max_nodes: int = 20) -> go.Figure:
    """
    Create a Sankey diagram visualization of module dependencies
    
    Parameters:
    - graph_data: Graph data containing nodes and edges
    - max_nodes: Maximum number of nodes to show (for readability)
    
    Returns:
    - Interactive Plotly Sankey diagram
    """
    # Extract nodes and edges
    nodes = graph_data.get('graph', {}).get('nodes', [])
    edges = graph_data.get('graph', {}).get('edges', [])
    
    if not nodes or not edges:
        # Return empty figure if no data
        fig = go.Figure()
        fig.add_annotation(text="No dependency data available", 
                          showarrow=False, font=dict(size=14))
        fig.update_layout(title="Module Dependencies (Sankey)")
        return fig
    
    # Limit to most important nodes if too many
    if len(nodes) > max_nodes:
        # Sort nodes by complexity
        sorted_nodes = sorted(nodes, 
                             key=lambda x: x.get('time_complexity', 0) + x.get('memory_complexity', 0),
                             reverse=True)
        
        # Take top nodes
        important_nodes = sorted_nodes[:max_nodes]
        important_node_ids = set(node['id'] for node in important_nodes)
        
        # Filter edges to only those connecting important nodes
        filtered_edges = [
            edge for edge in edges 
            if edge['source'] in important_node_ids and edge['target'] in important_node_ids
        ]
        
        nodes = important_nodes
        edges = filtered_edges
    
    # Create node lookup for Sankey indexing
    node_lookup = {node['id']: i for i, node in enumerate(nodes)}
    
    # Prepare Sankey data
    node_labels = [os.path.basename(node['id']) for node in nodes]
    link_sources = []
    link_targets = []
    link_values = []
    
    for edge in edges:
        source_id = edge['source']
        target_id = edge['target']
        
        if source_id in node_lookup and target_id in node_lookup:
            link_sources.append(node_lookup[source_id])
            link_targets.append(node_lookup[target_id])
            link_values.append(edge.get('weight', 1))
    
    # Create Sankey figure
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=node_labels,
            color="blue"
        ),
        link=dict(
            source=link_sources,
            target=link_targets,
            value=link_values
        )
    )])
    
    # Update layout
    fig.update_layout(
        title="Module Dependencies (Sankey Diagram)",
        font=dict(size=10),
        width=800,
        height=600,
    )
    
    return fig

def create_3d_dependency_graph(graph_data: Dict[str, Any]) -> go.Figure:
    """
    Create a 3D network visualization of module dependencies
    
    Parameters:
    - graph_data: Graph data containing nodes and edges
    
    Returns:
    - Interactive 3D Plotly figure
    """
    # Extract nodes and edges
    nodes = graph_data.get('graph', {}).get('nodes', [])
    edges = graph_data.get('graph', {}).get('edges', [])
    bottlenecks = graph_data.get('bottlenecks', [])
    
    if not nodes:
        # Return empty figure if no data
        fig = go.Figure()
        fig.add_annotation(text="No dependency data available", 
                          showarrow=False, font=dict(size=14))
        fig.update_layout(title="3D Module Dependencies")
        return fig
    
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add nodes
    for node in nodes:
        G.add_node(node['id'], 
                 label=node.get('label', node['id']),
                 time_complexity=node.get('time_complexity', 1),
                 memory_complexity=node.get('memory_complexity', 1))
    
    # Add edges
    for edge in edges:
        G.add_edge(edge['source'], edge['target'], weight=edge.get('weight', 1))
    
    # Create a bottleneck lookup for highlighting
    bottleneck_lookup = {b['file']: b for b in bottlenecks}
    
    # Calculate 3D positions using a force-directed layout
    pos = nx.spring_layout(G, dim=3, k=0.2, iterations=100)
    
    # Prepare node data for plotting
    node_x = []
    node_y = []
    node_z = []
    node_text = []
    node_size = []
    node_color = []
    
    for node_id in G.nodes():
        x, y, z = pos[node_id]
        node_label = G.nodes[node_id].get('label', os.path.basename(node_id))
        time_complexity = G.nodes[node_id].get('time_complexity', 1)
        memory_complexity = G.nodes[node_id].get('memory_complexity', 1)
        
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        
        # Scale node size based on complexity
        size = 5 + (time_complexity + memory_complexity) / 4
        node_size.append(size)
        
        # Node color based on bottleneck status
        if node_id in bottleneck_lookup:
            # Color based on bottleneck severity
            severity = bottleneck_lookup[node_id].get('severity', 0)
            if severity > 0.5:
                color = 'rgba(255, 0, 0, 0.8)'  # Red for high severity
            elif severity > 0.3:
                color = 'rgba(255, 165, 0, 0.8)'  # Orange for medium severity
            else:
                color = 'rgba(255, 255, 0, 0.8)'  # Yellow for low severity
        else:
            color = 'rgba(64, 164, 223, 0.8)'  # Blue for normal nodes
        
        node_color.append(color)
        
        # Node tooltip
        tooltip = f"<b>{node_label}</b><br>"
        tooltip += f"File: {node_id}<br>"
        tooltip += f"Time Complexity: {time_complexity}<br>"
        tooltip += f"Memory Complexity: {memory_complexity}<br>"
        
        if node_id in bottleneck_lookup:
            b_info = bottleneck_lookup[node_id]
            tooltip += f"<b>BOTTLENECK</b><br>"
            tooltip += f"Centrality: {b_info.get('centrality', 0):.3f}<br>"
            tooltip += f"Incoming Dependencies: {b_info.get('in_degree', 0)}<br>"
            tooltip += f"Outgoing Dependencies: {b_info.get('out_degree', 0)}<br>"
            tooltip += f"Severity: {b_info.get('severity', 0):.2f}"
        
        node_text.append(tooltip)
    
    # Prepare edge data for plotting
    edge_x = []
    edge_y = []
    edge_z = []
    
    for source, target in G.edges():
        x0, y0, z0 = pos[source]
        x1, y1, z1 = pos[target]
        
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])
    
    # Create edge trace
    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode='lines',
        line=dict(width=1, color='rgba(128, 128, 128, 0.5)'),
        hoverinfo='none'
    )
    
    # Create node trace
    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers',
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(width=0.5, color='rgba(50, 50, 50, 0.8)')
        ),
        text=node_text,
        hoverinfo='text'
    )
    
    # Create figure with all traces
    fig = go.Figure(data=[edge_trace, node_trace])
    
    # Update layout
    fig.update_layout(
        title="3D Module Dependencies",
        scene=dict(
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False),
            zaxis=dict(showticklabels=False)
        ),
        width=800,
        height=700,
        margin=dict(b=0, l=0, r=0, t=40),
    )
    
    return fig