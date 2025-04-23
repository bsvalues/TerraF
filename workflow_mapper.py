import os
import ast
import logging
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DependencyVisitor(ast.NodeVisitor):
    """AST visitor for identifying dependencies between Python modules"""
    
    def __init__(self, current_module: str):
        self.current_module = current_module
        self.dependencies = []
        self.import_from_nodes = []
        self.import_nodes = []
        self.function_calls = []
        self.class_references = []
    
    def visit_ImportFrom(self, node):
        """Process from-import statements"""
        if node.module:
            self.import_from_nodes.append({
                'module': node.module,
                'names': [name.name for name in node.names],
                'line': node.lineno
            })
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Process import statements"""
        self.import_nodes.append({
            'names': [name.name for name in node.names],
            'line': node.lineno
        })
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Process function/method calls"""
        if hasattr(node, 'func'):
            # Direct function calls like function()
            if hasattr(node.func, 'id'):
                self.function_calls.append({
                    'type': 'function',
                    'name': node.func.id,
                    'line': getattr(node, 'lineno', 0)
                })
            
            # Method calls like object.method()
            elif hasattr(node.func, 'attr') and hasattr(node.func, 'value'):
                method_name = node.func.attr
                object_name = ""
                
                # Try to get the object name
                if hasattr(node.func.value, 'id'):
                    object_name = node.func.value.id
                
                self.function_calls.append({
                    'type': 'method',
                    'object': object_name,
                    'name': method_name,
                    'line': getattr(node, 'lineno', 0)
                })
        
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Process name references"""
        if isinstance(node.ctx, ast.Load):
            # We're only interested in loading names (references)
            # ctx can be Load, Store, or Del
            self.class_references.append({
                'name': node.id,
                'line': getattr(node, 'lineno', 0)
            })
        
        self.generic_visit(node)

def get_module_path(name: str, current_path: str, repo_path: str) -> Optional[str]:
    """
    Convert a module name to a file path
    
    Parameters:
    - name: Module name
    - current_path: Path of the current module
    - repo_path: Root path of the repository
    
    Returns:
    - Optional file path corresponding to the module
    """
    current_dir = os.path.dirname(current_path)
    
    # First, try relative import
    parts = name.split('.')
    relative_path = os.path.join(current_dir, *parts) + '.py'
    
    if os.path.exists(os.path.join(repo_path, relative_path)):
        return relative_path
    
    # Then try from repo root
    absolute_path = os.path.join(*parts) + '.py'
    if os.path.exists(os.path.join(repo_path, absolute_path)):
        return absolute_path
    
    # Try as a package (look for __init__.py)
    package_path = os.path.join(*parts, '__init__.py')
    if os.path.exists(os.path.join(repo_path, package_path)):
        return package_path
    
    # Try as a package with different root
    for root, dirs, _ in os.walk(repo_path):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for directory in dirs:
            package_dir = os.path.join(root, directory)
            test_path = os.path.join(package_dir, *parts) + '.py'
            rel_path = os.path.relpath(test_path, repo_path)
            
            if os.path.exists(test_path):
                return rel_path
            
            # Also check for __init__.py
            package_init = os.path.join(package_dir, *parts, '__init__.py')
            rel_init_path = os.path.relpath(package_init, repo_path)
            
            if os.path.exists(package_init):
                return rel_init_path
    
    return None

def analyze_module_dependencies(file_path: str, repo_path: str) -> Dict:
    """
    Analyze a Python file for module dependencies
    
    Parameters:
    - file_path: Path to the file
    - repo_path: Root path of the repository
    
    Returns:
    - dict: Dependency information
    """
    full_path = os.path.join(repo_path, file_path)
    dependencies = []
    time_complexity = 0
    memory_complexity = 0
    
    try:
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
            # Calculate approximate complexity metrics
            time_complexity = content.count('for ') + content.count('while ') + 1
            memory_complexity = content.count('=') + content.count('append') + content.count('extend')
        
        # Parse the AST
        tree = ast.parse(content, filename=file_path)
        
        # Visit nodes and collect dependencies
        visitor = DependencyVisitor(file_path)
        visitor.visit(tree)
        
        # Process import statements
        for import_node in visitor.import_nodes:
            for name in import_node['names']:
                # Skip standard library imports
                if "." not in name and name.islower():
                    continue
                
                # Check if this is a project module
                module_path = get_module_path(name, file_path, repo_path)
                if module_path:
                    dependencies.append({
                        'source': file_path,
                        'target': module_path,
                        'type': 'import',
                        'weight': 1
                    })
        
        # Process from-import statements
        for import_from in visitor.import_from_nodes:
            module = import_from['module']
            
            # Skip standard library imports
            if "." not in module and module.islower():
                continue
            
            # Check if this is a project module
            module_path = get_module_path(module, file_path, repo_path)
            if module_path:
                dependencies.append({
                    'source': file_path,
                    'target': module_path,
                    'type': 'import_from',
                    'weight': 1
                })
        
        return {
            'file': file_path,
            'dependencies': dependencies,
            'time_complexity': time_complexity,
            'memory_complexity': memory_complexity
        }
    except Exception as e:
        logger.error(f"Error analyzing dependencies in {file_path}: {str(e)}")
        return {
            'file': file_path,
            'dependencies': dependencies,
            'time_complexity': time_complexity,
            'memory_complexity': memory_complexity,
            'error': str(e)
        }

def find_all_python_files(repo_path: str) -> List[str]:
    """
    Find all Python files in the repository
    
    Parameters:
    - repo_path: Path to the repository
    
    Returns:
    - list: All Python files
    """
    python_files = []
    
    for root, _, files in os.walk(repo_path):
        # Skip hidden directories
        if os.path.basename(root).startswith('.'):
            continue
        
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path)
                
                # Skip files in hidden directories
                if any(part.startswith('.') for part in rel_path.split(os.sep)):
                    continue
                
                python_files.append(rel_path)
    
    return python_files

def build_dependency_graph(repo_path: str, files: Optional[List[str]] = None) -> Dict:
    """
    Build a dependency graph for Python files in the repository
    
    Parameters:
    - repo_path: Path to the repository
    - files: Optional list of files to analyze (if None, all Python files are analyzed)
    
    Returns:
    - dict: Dependency graph information
    """
    logger.info(f"Building dependency graph for repository at {repo_path}...")
    
    start_time = time.time()
    
    # Initialize results
    results = {
        'graph': {
            'nodes': [],
            'edges': []
        },
        'metrics': {},
        'bottlenecks': [],
        'critical_paths': []
    }
    
    # Find Python files if not provided
    if files is None:
        files = find_all_python_files(repo_path)
    
    if not files:
        logger.info("No Python files found.")
        return results
    
    # Analyze each file
    module_data = {}
    all_dependencies = []
    
    for file_path in files:
        module_info = analyze_module_dependencies(file_path, repo_path)
        module_data[file_path] = module_info
        all_dependencies.extend(module_info.get('dependencies', []))
    
    # Build the graph
    G = nx.DiGraph()
    
    # Add nodes (files)
    for file_path, info in module_data.items():
        G.add_node(file_path, 
                  time_complexity=info.get('time_complexity', 1),
                  memory_complexity=info.get('memory_complexity', 1))
        
        results['graph']['nodes'].append({
            'id': file_path,
            'label': os.path.basename(file_path),
            'time_complexity': info.get('time_complexity', 1),
            'memory_complexity': info.get('memory_complexity', 1)
        })
    
    # Add edges (dependencies)
    for dep in all_dependencies:
        source = dep['source']
        target = dep['target']
        weight = dep.get('weight', 1)
        
        if source in G and target in G:
            G.add_edge(source, target, weight=weight)
            
            results['graph']['edges'].append({
                'source': source,
                'target': target,
                'weight': weight
            })
    
    # Calculate graph metrics
    try:
        # General metrics
        results['metrics']['node_count'] = G.number_of_nodes()
        results['metrics']['edge_count'] = G.number_of_edges()
        results['metrics']['average_degree'] = sum(dict(G.degree()).values()) / G.number_of_nodes()
        
        # Centrality metrics
        centrality = nx.betweenness_centrality(G)
        in_degree = dict(G.in_degree())
        out_degree = dict(G.out_degree())
        
        # Identify bottlenecks (high centrality, high in-degree)
        for node, cent in sorted(centrality.items(), key=lambda x: x[1], reverse=True):
            if cent > 0.05 or in_degree[node] > 2:  # Threshold for significance
                bottleneck_severity = cent * (in_degree[node] + 1)
                results['bottlenecks'].append({
                    'file': node,
                    'centrality': cent,
                    'in_degree': in_degree[node],
                    'out_degree': out_degree[node],
                    'severity': bottleneck_severity
                })
        
        # Sort bottlenecks by severity
        results['bottlenecks'] = sorted(results['bottlenecks'], key=lambda x: x['severity'], reverse=True)
        
        # Find critical paths (longest paths in the graph)
        try:
            # Try to find cycles first
            cycles = list(nx.simple_cycles(G))
            
            if cycles:
                for cycle in cycles[:5]:  # Limit to top 5 cycles
                    cycle_str = " -> ".join([os.path.basename(node) for node in cycle + [cycle[0]]])
                    results['critical_paths'].append({
                        'type': 'cycle',
                        'path': cycle,
                        'path_str': cycle_str,
                        'length': len(cycle),
                        'severity': 'high' if len(cycle) > 2 else 'medium'
                    })
            
            # Find longest paths
            # Calculate a topological sort if there are no cycles
            if not cycles:
                sorted_nodes = list(nx.topological_sort(G))
                
                # For each node, find the longest path ending at that node
                longest_paths = []
                for i, node in enumerate(sorted_nodes):
                    paths = []
                    for predecessor in G.predecessors(node):
                        for path in longest_paths:
                            if path[-1] == predecessor:
                                paths.append(path + [node])
                    
                    if not paths:
                        paths = [[node]]
                    else:
                        paths = sorted(paths, key=len, reverse=True)[:3]  # Keep only the 3 longest paths
                    
                    longest_paths.extend(paths)
                
                # Keep only unique paths of significant length
                unique_long_paths = {}
                for path in longest_paths:
                    if len(path) > 2:  # Only consider paths with at least 3 nodes
                        path_key = tuple(path)
                        if path_key not in unique_long_paths or len(path) > len(unique_long_paths[path_key]):
                            unique_long_paths[path_key] = path
                
                # Add the longest paths to the results
                for path in sorted(unique_long_paths.values(), key=len, reverse=True)[:5]:  # Top 5 longest paths
                    path_str = " -> ".join([os.path.basename(node) for node in path])
                    results['critical_paths'].append({
                        'type': 'path',
                        'path': path,
                        'path_str': path_str,
                        'length': len(path),
                        'severity': 'high' if len(path) > 4 else 'medium'
                    })
        except Exception as e:
            logger.error(f"Error finding critical paths: {str(e)}")
    except Exception as e:
        logger.error(f"Error calculating graph metrics: {str(e)}")
    
    elapsed_time = time.time() - start_time
    logger.info(f"Dependency graph built in {elapsed_time:.2f} seconds. Found {len(results['bottlenecks'])} bottlenecks.")
    
    return results

def visualize_dependency_graph(graph_data: Dict, highlight_bottlenecks: bool = True) -> go.Figure:
    """
    Create a visualization of the dependency graph
    
    Parameters:
    - graph_data: Dependency graph data
    - highlight_bottlenecks: Whether to highlight bottlenecks
    
    Returns:
    - plotly figure: Graph visualization
    """
    logger.info("Generating dependency graph visualization...")
    
    try:
        # Extract nodes and edges
        nodes = graph_data.get('graph', {}).get('nodes', [])
        edges = graph_data.get('graph', {}).get('edges', [])
        bottlenecks = graph_data.get('bottlenecks', [])
        
        if not nodes:
            # Return a placeholder figure if no data
            fig = go.Figure()
            fig.add_annotation(text="No dependency data available", 
                              showarrow=False, font=dict(size=14))
            return fig
        
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add nodes
        for node in nodes:
            G.add_node(node['id'], 
                     label=node['label'],
                     time_complexity=node.get('time_complexity', 1),
                     memory_complexity=node.get('memory_complexity', 1))
        
        # Add edges
        for edge in edges:
            G.add_edge(edge['source'], edge['target'], weight=edge.get('weight', 1))
        
        # Create a spring layout
        pos = nx.spring_layout(G, seed=42)  # Fixed seed for reproducibility
        
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
        
        # Create node traces
        # First, create a map of bottleneck files for quick lookup
        bottleneck_files = {b['file']: b for b in bottlenecks}
        
        # Regular nodes
        regular_node_x = []
        regular_node_y = []
        regular_node_text = []
        regular_node_size = []
        
        # Bottleneck nodes
        bottleneck_node_x = []
        bottleneck_node_y = []
        bottleneck_node_text = []
        bottleneck_node_size = []
        bottleneck_node_color = []
        
        for node in G.nodes():
            x, y = pos[node]
            
            # Calculate node size based on complexity
            time_complexity = G.nodes[node].get('time_complexity', 1)
            memory_complexity = G.nodes[node].get('memory_complexity', 1)
            size = 10 + (time_complexity + memory_complexity) / 10
            size = min(size, 30)  # Cap the size
            
            # Prepare node text
            node_label = os.path.basename(node)
            
            if node in bottleneck_files and highlight_bottlenecks:
                # This is a bottleneck
                bottleneck = bottleneck_files[node]
                
                bottleneck_node_x.append(x)
                bottleneck_node_y.append(y)
                
                # Create detailed hover text
                hover_text = (
                    f"<b>{node_label}</b><br>"
                    f"File: {node}<br>"
                    f"Centrality: {bottleneck['centrality']:.3f}<br>"
                    f"In-degree: {bottleneck['in_degree']}<br>"
                    f"Out-degree: {bottleneck['out_degree']}<br>"
                    f"Severity: {bottleneck['severity']:.2f}"
                )
                bottleneck_node_text.append(hover_text)
                
                # Adjust size for bottlenecks
                bottleneck_node_size.append(size * 1.5)
                
                # Color based on severity
                bottleneck_node_color.append(bottleneck['severity'])
            else:
                # Regular node
                regular_node_x.append(x)
                regular_node_y.append(y)
                
                # Create hover text
                hover_text = (
                    f"<b>{node_label}</b><br>"
                    f"File: {node}<br>"
                    f"Time Complexity: {time_complexity}<br>"
                    f"Memory Complexity: {memory_complexity}"
                )
                regular_node_text.append(hover_text)
                
                regular_node_size.append(size)
        
        # Regular node trace
        regular_node_trace = go.Scatter(
            x=regular_node_x, y=regular_node_y,
            mode='markers+text',
            text=[os.path.basename(node) for node in G.nodes() if node not in bottleneck_files or not highlight_bottlenecks],
            textposition="top center",
            marker=dict(
                showscale=False,
                color='rgba(135, 206, 250, 0.8)',  # light skyblue with some transparency
                size=regular_node_size,
                line=dict(width=1, color='rgba(0, 0, 0, 0.5)')
            ),
            hoverinfo='text',
            hovertext=regular_node_text,
            name='Modules'
        )
        
        # Bottleneck node trace (only if we have bottlenecks and highlighting is enabled)
        if bottleneck_node_x and highlight_bottlenecks:
            bottleneck_node_trace = go.Scatter(
                x=bottleneck_node_x, y=bottleneck_node_y,
                mode='markers+text',
                text=[os.path.basename(bottleneck_files[node]['file']) for node in bottleneck_files if highlight_bottlenecks],
                textposition="top center",
                marker=dict(
                    showscale=True,
                    colorscale='YlOrRd',
                    color=bottleneck_node_color,
                    colorbar=dict(
                        title="Bottleneck<br>Severity"
                    ),
                    size=bottleneck_node_size,
                    line=dict(width=1.5, color='rgba(0, 0, 0, 0.8)')
                ),
                hoverinfo='text',
                hovertext=bottleneck_node_text,
                name='Bottlenecks'
            )
        
        # Create figure
        traces = [edge_trace, regular_node_trace]
        if bottleneck_node_x and highlight_bottlenecks:
            traces.append(bottleneck_node_trace)
            
        fig = go.Figure(data=traces,
                      layout=go.Layout(
                          title='Module Dependency Graph',
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
                              x=0.01,
                              bgcolor="rgba(255, 255, 255, 0.5)"
                          ),
                          height=700,
                          width=900,
                          paper_bgcolor='rgba(255, 255, 255, 1)',
                          plot_bgcolor='rgba(255, 255, 255, 1)',
                          annotations=[
                              dict(
                                  text=f"Dependencies: {len(edges)}, Modules: {len(nodes)}, Bottlenecks: {len(bottlenecks)}",
                                  showarrow=False,
                                  xref="paper", yref="paper",
                                  x=0.5, y=-0.05
                              )
                          ]
                      ))
        
        return fig
    except Exception as e:
        logger.error(f"Error creating dependency graph visualization: {str(e)}")
        # Return a placeholder figure with error message
        fig = go.Figure()
        fig.add_annotation(text=f"Error creating visualization: {str(e)}", 
                          showarrow=False, font=dict(size=14, color="red"))
        return fig

def visualize_bottlenecks(graph_data: Dict) -> go.Figure:
    """
    Create a visualization of the bottlenecks
    
    Parameters:
    - graph_data: Dependency graph data
    
    Returns:
    - plotly figure: Bottlenecks visualization
    """
    logger.info("Generating bottlenecks visualization...")
    
    try:
        bottlenecks = graph_data.get('bottlenecks', [])
        
        if not bottlenecks:
            # Return a placeholder figure if no data
            fig = go.Figure()
            fig.add_annotation(text="No bottlenecks detected", 
                              showarrow=False, font=dict(size=14))
            return fig
        
        # Prepare data for the chart
        files = [os.path.basename(b['file']) for b in bottlenecks]
        centrality = [b['centrality'] for b in bottlenecks]
        in_degree = [b['in_degree'] for b in bottlenecks]
        out_degree = [b['out_degree'] for b in bottlenecks]
        severity = [b['severity'] for b in bottlenecks]
        
        # Create a horizontal bar chart for bottlenecks
        fig = go.Figure()
        
        # Add severity scatter
        fig.add_trace(go.Scatter(
            x=severity,
            y=files,
            mode='markers',
            marker=dict(
                color=severity,
                colorscale='YlOrRd',
                size=[min(s * 20, 40) for s in severity],
                colorbar=dict(title="Severity"),
                line=dict(width=1, color='black')
            ),
            name='Severity',
            hovertemplate='<b>%{y}</b><br>Severity: %{x:.2f}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title="Bottleneck Analysis",
            xaxis_title="Bottleneck Severity",
            yaxis=dict(
                title="Module",
                autorange="reversed"  # Highest severity at the top
            ),
            height=max(300, len(bottlenecks) * 30),
            margin=dict(l=10, r=10, t=30, b=10)
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error creating bottlenecks visualization: {str(e)}")
        # Return a placeholder figure with error message
        fig = go.Figure()
        fig.add_annotation(text=f"Error creating visualization: {str(e)}", 
                          showarrow=False, font=dict(size=14, color="red"))
        return fig

def visualize_critical_paths(graph_data: Dict) -> go.Figure:
    """
    Create a visualization of the critical paths
    
    Parameters:
    - graph_data: Dependency graph data
    
    Returns:
    - plotly figure: Critical paths visualization
    """
    logger.info("Generating critical paths visualization...")
    
    try:
        critical_paths = graph_data.get('critical_paths', [])
        
        if not critical_paths:
            # Return a placeholder figure if no data
            fig = go.Figure()
            fig.add_annotation(text="No critical paths detected", 
                              showarrow=False, font=dict(size=14))
            return fig
        
        # Create a Sankey diagram
        path_links_source = []
        path_links_target = []
        path_links_value = []
        path_links_color = []
        
        # Define color mapping
        color_map = {
            'high': 'rgba(255, 0, 0, 0.8)',  # red for high severity
            'medium': 'rgba(255, 165, 0, 0.8)',  # orange for medium severity
            'low': 'rgba(255, 255, 0, 0.8)'  # yellow for low severity
        }
        
        # Create a mapping of filenames to node indices
        unique_files = set()
        for path in critical_paths:
            for file in path['path']:
                unique_files.add(file)
        
        file_to_idx = {file: idx for idx, file in enumerate(unique_files)}
        
        # Generate links for each path
        for path_idx, path in enumerate(critical_paths):
            path_files = path['path']
            severity = path.get('severity', 'medium')
            
            # For cycles, add the first node again at the end
            if path['type'] == 'cycle':
                path_files = path_files + [path_files[0]]
            
            for i in range(len(path_files) - 1):
                source_idx = file_to_idx[path_files[i]]
                target_idx = file_to_idx[path_files[i+1]]
                
                path_links_source.append(source_idx)
                path_links_target.append(target_idx)
                path_links_value.append(1)  # Same weight for all links
                path_links_color.append(color_map.get(severity, 'rgba(128, 128, 128, 0.8)'))
        
        # Create labels for the nodes
        labels = [os.path.basename(file) for file in unique_files]
        
        # Create Sankey diagram
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels
            ),
            link=dict(
                source=path_links_source,
                target=path_links_target,
                value=path_links_value,
                color=path_links_color
            )
        )])
        
        # Update layout
        fig.update_layout(
            title_text="Critical Paths Analysis",
            font=dict(size=12),
            height=500,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error creating critical paths visualization: {str(e)}")
        # Return a placeholder figure with error message
        fig = go.Figure()
        fig.add_annotation(text=f"Error creating visualization: {str(e)}", 
                          showarrow=False, font=dict(size=14, color="red"))
        return fig

def analyze_workflow_dependencies(repo_path: str) -> Dict:
    """
    Analyze workflow dependencies in the repository
    
    Parameters:
    - repo_path: Path to the repository
    
    Returns:
    - dict: Workflow dependency analysis results
    """
    # First, find workflow-related files using the workflow analyzer
    from workflow_analyzer import find_workflow_files
    
    workflow_files = find_workflow_files(repo_path)
    
    # Then build a dependency graph for these files
    graph_data = build_dependency_graph(repo_path, workflow_files)
    
    return {
        'graph_data': graph_data,
        'workflow_files': workflow_files
    }

def analyze_all_dependencies(repo_path: str) -> Dict:
    """
    Analyze all dependencies in the repository
    
    Parameters:
    - repo_path: Path to the repository
    
    Returns:
    - dict: Full dependency analysis results
    """
    # Build a dependency graph for all Python files
    graph_data = build_dependency_graph(repo_path)
    
    return {
        'graph_data': graph_data
    }

def generate_optimization_recommendations(graph_data: Dict) -> List[str]:
    """
    Generate recommendations for optimizing the project workflow
    
    Parameters:
    - graph_data: Dependency graph data
    
    Returns:
    - list: Optimization recommendations
    """
    recommendations = []
    
    # Check for bottlenecks
    bottlenecks = graph_data.get('bottlenecks', [])
    if bottlenecks:
        recommendations.append(f"Refactor {len(bottlenecks)} identified bottleneck modules to reduce dependencies.")
        
        # Add specific recommendations for top bottlenecks
        for i, bottleneck in enumerate(bottlenecks[:3]):  # Top 3 bottlenecks
            file = os.path.basename(bottleneck['file'])
            if bottleneck['in_degree'] > bottleneck['out_degree']:
                recommendations.append(f"Consider breaking up {file} into smaller modules as it has a high number of incoming dependencies.")
            else:
                recommendations.append(f"Reduce the dependencies that {file} has on other modules to decrease coupling.")
    
    # Check for circular dependencies
    critical_paths = graph_data.get('critical_paths', [])
    cycles = [path for path in critical_paths if path['type'] == 'cycle']
    
    if cycles:
        recommendations.append(f"Resolve {len(cycles)} circular dependencies to improve maintainability.")
        
        # Add specific recommendations for cycles
        for i, cycle in enumerate(cycles[:2]):  # Top 2 cycles
            cycle_str = " -> ".join([os.path.basename(node) for node in cycle['path']])
            recommendations.append(f"Break the circular dependency: {cycle_str}")
    
    # Check for long dependency chains
    long_paths = [path for path in critical_paths if path['type'] == 'path' and path['length'] > 3]
    
    if long_paths:
        recommendations.append(f"Simplify {len(long_paths)} long dependency chains to reduce complexity.")
        
        # Add specific recommendations for long paths
        for i, path in enumerate(long_paths[:2]):  # Top 2 long paths
            files = [os.path.basename(node) for node in path['path']]
            start = files[0]
            end = files[-1]
            recommendations.append(f"Create a more direct dependency between {start} and {end} to reduce the dependency chain length.")
    
    # Add general recommendations
    recommendations.append("Consider implementing a dependency injection framework to reduce tight coupling between modules.")
    recommendations.append("Document module responsibilities clearly to avoid overlapping functionality.")
    recommendations.append("Implement a microservices architecture for highly dependent components to improve separation of concerns.")
    
    return recommendations