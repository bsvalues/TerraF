import logging
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from collections import Counter, defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def visualize_repository_structure(repo_structure):
    """
    Create a sunburst visualization of the repository structure
    
    Parameters:
    - repo_structure: Repository structure data
    
    Returns:
    - plotly figure: Sunburst chart of repository structure
    """
    logger.info("Generating repository structure visualization...")
    
    try:
        # Extract file types for visualization
        file_types = repo_structure.get('file_types', [])
        
        # Create sunburst data
        labels = ['Repository']
        parents = ['']
        values = [1]
        
        # Add file types
        for file_type in file_types:
            ext = file_type.get('extension', 'unknown')
            count = file_type.get('count', 0)
            
            # Skip very small counts for readability
            if count < 2:
                continue
                
            labels.append(ext)
            parents.append('Repository')
            values.append(count)
        
        # Create the sunburst chart
        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            textinfo="label+value",
            hoverinfo="label+value+percent parent"
        ))
        
        fig.update_layout(
            title="Repository File Structure",
            margin=dict(t=30, l=0, r=0, b=0),
            height=500
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error creating repository structure visualization: {str(e)}")
        # Return a placeholder figure with error message
        fig = go.Figure()
        fig.add_annotation(text=f"Error creating visualization: {str(e)}", 
                          showarrow=False, font=dict(size=14, color="red"))
        return fig

def visualize_code_complexity(code_review):
    """
    Create a visualization of code complexity
    
    Parameters:
    - code_review: Code review results
    
    Returns:
    - plotly figure: Complexity visualization
    """
    logger.info("Generating code complexity visualization...")
    
    try:
        # Extract complex files data
        complex_files = code_review.get('top_complex_files', [])
        
        if not complex_files:
            # Return a placeholder figure if no data
            fig = go.Figure()
            fig.add_annotation(text="No complexity data available", 
                              showarrow=False, font=dict(size=14))
            return fig
        
        # Prepare data for visualization
        files = [f.get('file', 'unknown') for f in complex_files]
        complexity = [f.get('complexity', 0) for f in complex_files]
        loc = [f.get('loc', 0) for f in complex_files]
        
        # Create bubble chart
        fig = go.Figure()
        
        # Add scatter plot with size representing lines of code
        fig.add_trace(go.Scatter(
            x=complexity,
            y=list(range(len(files))),
            text=files,
            mode='markers',
            marker=dict(
                size=[min(max(10, l / 10), 50) for l in loc],  # Scale LOC to reasonable marker sizes
                color=complexity,
                colorscale='Viridis',
                colorbar=dict(title="Complexity"),
                line=dict(width=1, color='black')
            ),
            hovertemplate='<b>%{text}</b><br>Complexity: %{x}<br>Lines of Code: %{marker.size:.0f}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title="Code Complexity Analysis",
            xaxis_title="Complexity",
            yaxis=dict(
                title="Files",
                tickvals=list(range(len(files))),
                ticktext=files,
                automargin=True
            ),
            height=max(400, len(files) * 30),  # Dynamic height based on number of files
            margin=dict(l=10, r=10, t=30, b=10)
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error creating code complexity visualization: {str(e)}")
        # Return a placeholder figure with error message
        fig = go.Figure()
        fig.add_annotation(text=f"Error creating visualization: {str(e)}", 
                          showarrow=False, font=dict(size=14, color="red"))
        return fig

def visualize_database_relations(db_analysis):
    """
    Create a visualization of database relations
    
    Parameters:
    - db_analysis: Database analysis results
    
    Returns:
    - plotly figure: Relations visualization
    """
    logger.info("Generating database relations visualization...")
    
    try:
        # Extract database models
        models = db_analysis.get('database_models', {})
        
        if not models:
            # Return a placeholder figure if no data
            fig = go.Figure()
            fig.add_annotation(text="No database models available", 
                              showarrow=False, font=dict(size=14))
            return fig
        
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add model nodes
        for model_name in models.keys():
            G.add_node(model_name)
        
        # Add relationship edges
        for model_name, model_info in models.items():
            # Handle different ORM types
            if model_info.get('orm') == 'sqlalchemy' and 'relationships' in model_info:
                for rel_name, rel_info in model_info.get('relationships', {}).items():
                    target = rel_info.get('target')
                    if target:
                        G.add_edge(model_name, target, label=rel_name)
            
            # Basic field-based relationships (look for foreign keys)
            for field_name, field_info in model_info.get('fields', {}).items():
                if 'ForeignKey' in str(field_info.get('type', '')) or field_name.endswith('_id'):
                    # Try to guess the target model
                    if field_name.endswith('_id'):
                        target = field_name[:-3].title()  # Convert user_id to User
                        if target in models:
                            G.add_edge(model_name, target, label=field_name)
        
        # If the graph is empty, return a placeholder
        if not G.edges():
            fig = go.Figure()
            fig.add_annotation(text="No relationships detected between models", 
                              showarrow=False, font=dict(size=14))
            return fig
        
        # Create a spring layout
        pos = nx.spring_layout(G)
        
        # Create edge traces
        edge_x = []
        edge_y = []
        edge_text = []
        
        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_text.append(edge[2].get('label', ''))
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Create node traces
        node_x = []
        node_y = []
        node_text = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="top center",
            marker=dict(
                showscale=False,
                color='skyblue',
                size=15,
                line=dict(width=2, color='black')
            ),
            hoverinfo='text'
        )
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                      layout=go.Layout(
                          title='Database Model Relationships',
                          showlegend=False,
                          hovermode='closest',
                          margin=dict(b=20, l=5, r=5, t=40),
                          xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                          yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                          height=600
                      ))
        
        return fig
    except Exception as e:
        logger.error(f"Error creating database relations visualization: {str(e)}")
        # Return a placeholder figure with error message
        fig = go.Figure()
        fig.add_annotation(text=f"Error creating visualization: {str(e)}", 
                          showarrow=False, font=dict(size=14, color="red"))
        return fig

def visualize_modularization_opportunities(modularization):
    """
    Create a visualization of modularization opportunities
    
    Parameters:
    - modularization: Modularization analysis results
    
    Returns:
    - plotly figure: Modularization visualization
    """
    logger.info("Generating modularization visualization...")
    
    try:
        # Extract dependency graph
        graph_data = modularization.get('dependency_graph', {})
        
        if not graph_data or 'nodes' not in graph_data or 'edges' not in graph_data:
            # Return a placeholder figure if no data
            fig = go.Figure()
            fig.add_annotation(text="No dependency graph data available", 
                              showarrow=False, font=dict(size=14))
            return fig
        
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add nodes
        for node in graph_data.get('nodes', []):
            G.add_node(node.get('id'), file=node.get('file', 'unknown'))
        
        # Add edges
        for edge in graph_data.get('edges', []):
            G.add_edge(edge.get('source'), edge.get('target'))
        
        # Check if the graph is too large for visualization
        if len(G.nodes()) > 50:
            # Find the most central nodes
            centrality = nx.betweenness_centrality(G)
            top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:50]
            
            # Create a subgraph with just the most important nodes
            nodes_to_keep = [node for node, _ in top_nodes]
            G = G.subgraph(nodes_to_keep)
        
        # Find circular dependencies
        try:
            cycles = list(nx.simple_cycles(G))
            cycle_nodes = set()
            for cycle in cycles:
                cycle_nodes.update(cycle)
        except:
            cycles = []
            cycle_nodes = set()
        
        # Create a spring layout
        pos = nx.spring_layout(G)
        
        # Create edge traces
        edge_x = []
        edge_y = []
        
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Create regular node trace
        regular_node_x = []
        regular_node_y = []
        regular_node_text = []
        
        # Create cycle node trace (highlight nodes in cycles)
        cycle_node_x = []
        cycle_node_y = []
        cycle_node_text = []
        
        for node in G.nodes():
            x, y = pos[node]
            file_path = G.nodes[node].get('file', node)
            
            if node in cycle_nodes:
                cycle_node_x.append(x)
                cycle_node_y.append(y)
                cycle_node_text.append(file_path)
            else:
                regular_node_x.append(x)
                regular_node_y.append(y)
                regular_node_text.append(file_path)
        
        regular_node_trace = go.Scatter(
            x=regular_node_x, y=regular_node_y,
            mode='markers',
            hovertext=regular_node_text,
            marker=dict(
                showscale=False,
                color='skyblue',
                size=10,
                line=dict(width=1, color='black')
            ),
            name='Modules'
        )
        
        cycle_node_trace = go.Scatter(
            x=cycle_node_x, y=cycle_node_y,
            mode='markers',
            hovertext=cycle_node_text,
            marker=dict(
                showscale=False,
                color='red',
                size=12,
                line=dict(width=1, color='black')
            ),
            name='Circular Dependencies'
        )
        
        # Create figure
        traces = [edge_trace, regular_node_trace]
        if cycle_node_x:  # Only add cycle trace if there are cycles
            traces.append(cycle_node_trace)
            
        fig = go.Figure(data=traces,
                      layout=go.Layout(
                          title='Module Dependency Graph',
                          showlegend=True,
                          hovermode='closest',
                          margin=dict(b=20, l=5, r=5, t=40),
                          xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                          yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                          height=600
                      ))
        
        # Add annotation if subgraph was created
        if len(G.nodes()) < len(graph_data.get('nodes', [])):
            fig.add_annotation(
                text=f"Showing only the {len(G.nodes())} most central modules out of {len(graph_data.get('nodes', []))}",
                xref="paper", yref="paper",
                x=0.5, y=1,
                showarrow=False
            )
        
        return fig
    except Exception as e:
        logger.error(f"Error creating modularization visualization: {str(e)}")
        # Return a placeholder figure with error message
        fig = go.Figure()
        fig.add_annotation(text=f"Error creating visualization: {str(e)}", 
                          showarrow=False, font=dict(size=14, color="red"))
        return fig