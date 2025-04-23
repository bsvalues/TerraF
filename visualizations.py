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
            hovertemplate='<b>%{label}</b><br>Files: %{value}<br>',
            maxdepth=2
        ))
        
        fig.update_layout(
            title="Repository File Type Distribution",
            margin=dict(t=30, l=0, r=0, b=0)
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error creating repository structure visualization: {str(e)}")
        
        # Return a fallback visualization
        return create_fallback_visualization(
            "Repository Structure", 
            "Error creating visualization"
        )

def visualize_code_complexity(code_review):
    """
    Create a visualization of code complexity metrics
    
    Parameters:
    - code_review: Code review analysis data
    
    Returns:
    - plotly figure: Visualization of code complexity
    """
    logger.info("Generating code complexity visualization...")
    
    try:
        # Get complex files data
        complex_files = code_review.get('top_complex_files', [])
        
        if complex_files:
            # Prepare data for visualization
            files = [f.get('file', '').split('/')[-1] for f in complex_files]
            complexity = [f.get('complexity', 0) for f in complex_files]
            loc = [f.get('loc', 0) for f in complex_files]
            
            # Create a bubble chart
            fig = go.Figure()
            
            # Add a scatter trace for complexity vs. LOC
            fig.add_trace(go.Scatter(
                x=loc,
                y=complexity,
                mode='markers',
                marker=dict(
                    size=[min(c/2, 50) for c in complexity],  # Size based on complexity, but capped
                    color=complexity,
                    colorscale='Viridis',
                    colorbar=dict(title="Complexity"),
                    showscale=True
                ),
                text=files,
                hovertemplate='<b>%{text}</b><br>Complexity: %{y}<br>Lines: %{x}<br>'
            ))
            
            fig.update_layout(
                title="Code Complexity vs. Size",
                xaxis_title="Lines of Code",
                yaxis_title="Cyclomatic Complexity",
                hovermode='closest'
            )
            
            return fig
        else:
            # Create a bar chart of issue types if no complex files data
            issue_counts = defaultdict(int)
            for file_issue in code_review.get('files_with_issues', []):
                for detail in file_issue.get('details', []):
                    for issue_type in ['long_method', 'complex_method', 'large_class', 
                                      'magic_numbers', 'commented_code', 'nested_conditionals']:
                        if issue_type in detail:
                            issue_counts[issue_type.replace('_', ' ')] += 1
            
            if issue_counts:
                issues = list(issue_counts.keys())
                counts = list(issue_counts.values())
                
                fig = go.Figure([go.Bar(x=issues, y=counts)])
                
                fig.update_layout(
                    title="Code Issues by Type",
                    xaxis_title="Issue Type",
                    yaxis_title="Count",
                    yaxis=dict(rangemode='nonnegative')
                )
                
                return fig
            
            return create_fallback_visualization(
                "Code Complexity", 
                "No complexity data available"
            )
    except Exception as e:
        logger.error(f"Error creating code complexity visualization: {str(e)}")
        
        # Return a fallback visualization
        return create_fallback_visualization(
            "Code Complexity", 
            "Error creating visualization"
        )

def visualize_database_relations(database_analysis):
    """
    Create a visualization of database relations
    
    Parameters:
    - database_analysis: Database analysis data
    
    Returns:
    - plotly figure: Visualization of database relations
    """
    logger.info("Generating database relations visualization...")
    
    try:
        # Extract database models
        models = database_analysis.get('database_models', {})
        
        if models:
            # Create a directed graph
            G = nx.DiGraph()
            
            # Add nodes for each model
            for model_name in models:
                G.add_node(model_name, type='model')
            
            # Add edges for relationships
            for model_name, model_info in models.items():
                for relationship in model_info.get('relationships', []):
                    related_model = relationship.get('related_model')
                    if related_model in models:
                        G.add_edge(model_name, related_model, 
                                  relation=relationship.get('type', 'relationship'))
            
            # Create a network visualization
            if len(G.nodes) > 1:
                # Create positions for nodes using spring layout
                pos = nx.spring_layout(G, seed=42)
                
                # Create edge traces
                edge_x = []
                edge_y = []
                edge_texts = []
                
                for edge in G.edges(data=True):
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                    edge_texts.append(edge[2].get('relation', 'relationship'))
                
                edge_trace = go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=1, color='#888'),
                    hoverinfo='none',
                    mode='lines')
                
                # Create node traces
                node_x = []
                node_y = []
                node_text = []
                
                for node in G.nodes():
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)
                    
                    # Format node text with model fields
                    fields = []
                    if node in models:
                        for field in models[node].get('fields', []):
                            fields.append(f"{field.get('name')}: {field.get('type', '')}")
                    
                    text = f"<b>{node}</b><br>" + "<br>".join(fields[:5])
                    if len(fields) > 5:
                        text += "<br>..."
                    
                    node_text.append(text)
                
                node_trace = go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers',
                    hoverinfo='text',
                    marker=dict(
                        showscale=False,
                        colorscale='YlGnBu',
                        size=15,
                        line_width=2))
                
                node_trace.text = node_text
                
                # Create the figure
                fig = go.Figure(data=[edge_trace, node_trace],
                             layout=go.Layout(
                                title="Database Model Relationships",
                                titlefont_size=16,
                                showlegend=False,
                                hovermode='closest',
                                margin=dict(b=20,l=5,r=5,t=40),
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                            ))
                
                return fig
            else:
                # Create a bar chart of model field counts
                model_field_counts = {}
                for model_name, model_info in models.items():
                    model_field_counts[model_name] = len(model_info.get('fields', []))
                
                if model_field_counts:
                    model_names = list(model_field_counts.keys())
                    field_counts = list(model_field_counts.values())
                    
                    fig = go.Figure([go.Bar(x=model_names, y=field_counts, 
                                          text=field_counts, textposition='auto')])
                    
                    fig.update_layout(
                        title="Database Model Fields",
                        xaxis_title="Model",
                        yaxis_title="Number of Fields",
                        yaxis=dict(rangemode='nonnegative')
                    )
                    
                    return fig
        
        # If no models or visualization failed, create a pie chart of file types
        db_files = database_analysis.get('database_files', [])
        if db_files:
            # Count files by extension
            file_types = Counter()
            for file_info in db_files:
                ext = file_info.get('path', '').split('.')[-1]
                file_types[ext] += 1
            
            if file_types:
                labels = list(file_types.keys())
                values = list(file_types.values())
                
                fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
                
                fig.update_layout(
                    title="Database Files by Type"
                )
                
                return fig
        
        return create_fallback_visualization(
            "Database Relations", 
            "No database models available"
        )
    except Exception as e:
        logger.error(f"Error creating database relations visualization: {str(e)}")
        
        # Return a fallback visualization
        return create_fallback_visualization(
            "Database Relations", 
            "Error creating visualization"
        )

def visualize_modularization_opportunities(modularization):
    """
    Create a visualization of modularization opportunities
    
    Parameters:
    - modularization: Modularization analysis data
    
    Returns:
    - plotly figure: Visualization of modularization opportunities
    """
    logger.info("Generating modularization opportunities visualization...")
    
    try:
        # Try to create a visualization of the dependency graph
        dependency_graph = modularization.get('dependency_graph', {})
        
        if dependency_graph and 'nodes' in dependency_graph and 'edges' in dependency_graph:
            nodes = dependency_graph['nodes']
            edges = dependency_graph['edges']
            
            if nodes and edges and len(nodes) <= 30:  # Only create network vis for small to medium graphs
                # Create a directed graph
                G = nx.DiGraph()
                
                # Add nodes
                for node in nodes:
                    G.add_node(node['id'], type=node.get('type', 'file'))
                
                # Add edges
                for edge in edges:
                    G.add_edge(edge['source'], edge['target'], label=edge.get('label', ''))
                
                # Create positions for nodes using spring layout
                pos = nx.spring_layout(G, seed=42)
                
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
                    line=dict(width=0.7, color='#888'),
                    hoverinfo='none',
                    mode='lines')
                
                # Create node traces
                node_x = []
                node_y = []
                node_sizes = []
                node_colors = []
                node_text = []
                
                # Calculate node degrees for sizing
                degrees = dict(G.degree())
                
                for node in G.nodes():
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)
                    
                    # Size based on degree
                    degree = degrees[node]
                    node_sizes.append(10 + degree * 3)
                    
                    # Color based on in-degree vs out-degree
                    in_degree = G.in_degree(node)
                    out_degree = G.out_degree(node)
                    
                    if in_degree > out_degree:
                        # More dependencies on this node
                        node_colors.append('rgba(31, 119, 180, 0.8)')  # Blue
                    elif out_degree > in_degree:
                        # This node depends on many others
                        node_colors.append('rgba(255, 127, 14, 0.8)')  # Orange
                    else:
                        # Balanced dependencies
                        node_colors.append('rgba(44, 160, 44, 0.8)')  # Green
                    
                    # Node text
                    file_name = node.split('/')[-1]
                    node_text.append(f"<b>{file_name}</b><br>File: {node}<br>In: {in_degree}, Out: {out_degree}")
                
                node_trace = go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers',
                    hoverinfo='text',
                    marker=dict(
                        color=node_colors,
                        size=node_sizes,
                        line=dict(width=1, color='#333')
                    ))
                
                node_trace.text = node_text
                
                # Create the figure
                fig = go.Figure(data=[edge_trace, node_trace],
                             layout=go.Layout(
                                title="Module Dependencies",
                                titlefont_size=16,
                                showlegend=False,
                                hovermode='closest',
                                margin=dict(b=20,l=5,r=5,t=40),
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                annotations=[
                                    dict(
                                        text="Blue: Depended on by others<br>Orange: Depends on others<br>Green: Balanced",
                                        showarrow=False,
                                        xref="paper", yref="paper",
                                        x=0.01, y=0.01
                                    )
                                ]
                            ))
                
                return fig
        
        # Alternative: Create a visualization of natural modules
        modules = modularization.get('current_modules', [])
        if modules:
            module_names = [m.get('name', 'Unknown') for m in modules]
            file_counts = [m.get('file_count', 0) for m in modules]
            
            # Create a bar chart of modules by file count
            fig = go.Figure([go.Bar(
                x=module_names,
                y=file_counts,
                text=file_counts,
                textposition='auto',
                marker_color='rgb(55, 83, 109)'
            )])
            
            fig.update_layout(
                title="Natural Modules by Size",
                xaxis_title="Module",
                yaxis_title="Number of Files",
                yaxis=dict(rangemode='nonnegative')
            )
            
            return fig
        
        # Alternative: Create a visualization of high coupling files
        high_coupling = modularization.get('high_coupling', [])
        if high_coupling:
            files = [h.get('file', '').split('/')[-1] for h in high_coupling]
            in_degrees = [h.get('in_degree', 0) for h in high_coupling]
            out_degrees = [h.get('out_degree', 0) for h in high_coupling]
            
            # Create a stacked bar chart of in-degree vs out-degree
            fig = go.Figure(data=[
                go.Bar(name='Incoming Dependencies', x=files, y=in_degrees),
                go.Bar(name='Outgoing Dependencies', x=files, y=out_degrees)
            ])
            
            fig.update_layout(
                title="Files with High Coupling",
                xaxis_title="File",
                yaxis_title="Dependencies",
                barmode='stack',
                yaxis=dict(rangemode='nonnegative')
            )
            
            return fig
        
        return create_fallback_visualization(
            "Modularization Opportunities", 
            "No modularization data available"
        )
    except Exception as e:
        logger.error(f"Error creating modularization visualization: {str(e)}")
        
        # Return a fallback visualization
        return create_fallback_visualization(
            "Modularization Opportunities", 
            "Error creating visualization"
        )

def create_fallback_visualization(title, message):
    """
    Create a fallback visualization when data is missing or an error occurs
    
    Parameters:
    - title: Title for the visualization
    - message: Message to display
    
    Returns:
    - plotly figure: Simple fallback visualization
    """
    fig = go.Figure()
    
    fig.add_annotation(
        text=message,
        font=dict(size=14),
        showarrow=False,
        xref="paper", yref="paper",
        x=0.5, y=0.5
    )
    
    fig.update_layout(
        title=title,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
    
    return fig
