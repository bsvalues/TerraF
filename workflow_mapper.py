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
    
    # Additional analysis for TerraFusion microservices architecture
    # This analyzes the repository for microservice patterns and plugin architecture
    microservice_analysis = analyze_microservice_patterns(repo_path, graph_data)
    
    return {
        'graph_data': graph_data,
        'microservice_analysis': microservice_analysis
    }

def analyze_microservice_patterns(repo_path: str, graph_data: Dict) -> Dict:
    """
    Analyze repository for microservice and plugin architecture patterns
    
    Parameters:
    - repo_path: Path to the repository
    - graph_data: Previously analyzed dependency graph data
    
    Returns:
    - dict: Microservice architecture analysis results
    """
    logger.info(f"Analyzing microservice architecture patterns for repository at {repo_path}...")
    
    # Initialize results
    results = {
        'microservices': [],
        'api_gateways': [],
        'plugins': [],
        'service_communications': [],
        'recommendations': []
    }
    
    try:
        # Identify potential microservices based on file structure and naming
        microservices = _identify_microservices(repo_path)
        results['microservices'] = microservices
        
        # Identify API gateways based on import patterns and file contents
        api_gateways = _identify_api_gateways(repo_path, graph_data)
        results['api_gateways'] = api_gateways
        
        # Identify plugin architecture components
        plugins = _identify_plugins(repo_path, graph_data)
        results['plugins'] = plugins
        
        # Analyze service-to-service communications
        service_comms = _analyze_service_communications(repo_path, graph_data, microservices)
        results['service_communications'] = service_comms
        
        # Generate microservice-specific recommendations
        recommendations = _generate_microservice_recommendations(microservices, api_gateways, plugins, service_comms)
        results['recommendations'] = recommendations
        
        return results
    except Exception as e:
        logger.error(f"Error analyzing microservice patterns: {str(e)}")
        return {
            'microservices': [],
            'api_gateways': [],
            'plugins': [],
            'service_communications': [],
            'recommendations': [
                "Error analyzing microservice patterns. Check the logs for details."
            ],
            'error': str(e)
        }

def _identify_microservices(repo_path: str) -> List[Dict]:
    """Identify potential microservices in the repository"""
    microservices = []
    
    # Look for microservice indicators in directory structure
    service_dirs = []
    
    # Check for common microservice directory patterns
    for pattern in ["services/", "apps/", "microservices/", "modules/"]:
        service_pattern_path = os.path.join(repo_path, pattern)
        if os.path.exists(service_pattern_path) and os.path.isdir(service_pattern_path):
            # Add subdirectories as potential services
            for item in os.listdir(service_pattern_path):
                item_path = os.path.join(service_pattern_path, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    service_dirs.append(os.path.join(pattern, item))
    
    # Look for standalone service indicators (Dockerfile, service.yml, etc.)
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden directories and common non-service directories
        if (os.path.basename(root).startswith('.') or 
            "node_modules" in root or 
            "__pycache__" in root or
            "venv" in root or
            ".git" in root):
            continue
        
        # Check for service indicators
        service_indicators = 0
        has_dockerfile = False
        has_service_config = False
        has_package_json = False
        has_requirements = False
        has_api_endpoints = False
        
        rel_path = os.path.relpath(root, repo_path)
        
        for file in files:
            if file.lower() == "dockerfile":
                has_dockerfile = True
                service_indicators += 2
            elif file.lower() in ["docker-compose.yml", "docker-compose.yaml"]:
                service_indicators += 1
            elif file.lower() in ["service.yml", "service.yaml", "manifest.yml", "manifest.yaml"]:
                has_service_config = True
                service_indicators += 2
            elif file.lower() == "package.json":
                has_package_json = True
                service_indicators += 1
            elif file.lower() == "requirements.txt" or file.lower() == "pyproject.toml":
                has_requirements = True
                service_indicators += 1
            elif file.lower() in ["api.py", "routes.py", "endpoints.py", "controller.py", "app.py", "server.py"]:
                has_api_endpoints = True
                service_indicators += 2
        
        # If enough indicators are present, consider it a microservice
        if service_indicators >= 3 or has_dockerfile or has_service_config:
            # Avoid adding if it's a child of an already identified service directory
            if not any(rel_path.startswith(sd) for sd in service_dirs):
                service_dirs.append(rel_path)
    
    # Create microservice info objects
    for service_dir in service_dirs:
        full_path = os.path.join(repo_path, service_dir)
        service_name = os.path.basename(service_dir)
        
        # Determine service type based on files
        service_type = "unknown"
        if os.path.exists(os.path.join(full_path, "requirements.txt")) or os.path.exists(os.path.join(full_path, "pyproject.toml")):
            service_type = "python"
        elif os.path.exists(os.path.join(full_path, "package.json")):
            service_type = "nodejs"
        elif os.path.exists(os.path.join(full_path, "pom.xml")):
            service_type = "java"
        elif os.path.exists(os.path.join(full_path, "go.mod")):
            service_type = "go"
        
        # Count files to determine primary language if type is unknown
        if service_type == "unknown":
            file_extensions = {".py": 0, ".js": 0, ".ts": 0, ".java": 0, ".go": 0}
            
            for root, _, files in os.walk(full_path):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in file_extensions:
                        file_extensions[ext] += 1
            
            # Determine language with most files
            if file_extensions[".py"] > file_extensions[".js"] and file_extensions[".py"] > file_extensions[".ts"] and file_extensions[".py"] > file_extensions[".java"] and file_extensions[".py"] > file_extensions[".go"]:
                service_type = "python"
            elif file_extensions[".js"] > file_extensions[".ts"]:
                service_type = "nodejs"
            elif file_extensions[".ts"] > 0:
                service_type = "typescript"
            elif file_extensions[".java"] > 0:
                service_type = "java"
            elif file_extensions[".go"] > 0:
                service_type = "go"
        
        # Analyze service files to detect dependencies and API endpoints
        api_endpoints = []
        dependencies = []
        
        # Look for API endpoints in Python files
        if service_type in ["python"]:
            for root, _, files in os.walk(full_path):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                                content = f.read()
                                
                                # Check for FastAPI routes
                                if "@app.get(" in content or "@app.post(" in content or "@router.get(" in content or "@router.post(" in content:
                                    api_endpoints.append({
                                        "file": os.path.relpath(file_path, repo_path),
                                        "type": "fastapi"
                                    })
                                # Check for Flask routes
                                elif "@app.route(" in content or "@blueprint.route(" in content:
                                    api_endpoints.append({
                                        "file": os.path.relpath(file_path, repo_path),
                                        "type": "flask"
                                    })
                        except Exception as e:
                            logger.error(f"Error reading file {file_path}: {str(e)}")
        
        # Look for API endpoints in JavaScript/TypeScript files
        elif service_type in ["nodejs", "typescript"]:
            for root, _, files in os.walk(full_path):
                for file in files:
                    if file.endswith((".js", ".ts")):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                                content = f.read()
                                
                                # Check for Express routes
                                if "app.get(" in content or "app.post(" in content or "router.get(" in content or "router.post(" in content:
                                    api_endpoints.append({
                                        "file": os.path.relpath(file_path, repo_path),
                                        "type": "express"
                                    })
                                # Check for Fastify routes
                                elif "fastify.get(" in content or "fastify.post(" in content:
                                    api_endpoints.append({
                                        "file": os.path.relpath(file_path, repo_path),
                                        "type": "fastify"
                                    })
                        except Exception as e:
                            logger.error(f"Error reading file {file_path}: {str(e)}")
        
        # Add the microservice info
        microservices.append({
            "name": service_name,
            "path": service_dir,
            "type": service_type,
            "api_endpoints": api_endpoints,
            "dependencies": dependencies
        })
    
    return microservices

def _identify_api_gateways(repo_path: str, graph_data: Dict) -> List[Dict]:
    """Identify API gateways in the repository"""
    api_gateways = []
    
    # Look for files that might be API gateways
    gateway_files = []
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, repo_path)
            
            # Skip hidden files and directories
            if (file.startswith('.') or
                "__pycache__" in rel_path or
                "node_modules" in rel_path or
                ".git" in rel_path):
                continue
            
            # Check for gateway indicators in filename
            if ("gateway" in file.lower() or 
                "proxy" in file.lower() or 
                "router" in file.lower()):
                gateway_files.append(rel_path)
            
            # For Python and JS/TS files, check content for gateway patterns
            if file.endswith((".py", ".js", ".ts")):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read().lower()
                        
                        # Check for gateway patterns in content
                        if (("api gateway" in content or "apigateway" in content) and
                            ("route" in content or "proxy" in content or "forward" in content)):
                            gateway_files.append(rel_path)
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {str(e)}")
    
    # Analyze gateway files
    for gateway_file in gateway_files:
        file_path = os.path.join(repo_path, gateway_file)
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            
            # Determine gateway type
            gateway_type = "unknown"
            routes = []
            
            if gateway_file.endswith(".py"):
                gateway_type = "python"
                
                # Check for common Python gateway frameworks
                if "import fastapi" in content.lower():
                    gateway_type = "fastapi"
                elif "import flask" in content.lower():
                    gateway_type = "flask"
                elif "import aiohttp" in content.lower():
                    gateway_type = "aiohttp"
                
                # Extract routes (simplified, would need AST parsing for accuracy)
                import re
                # Look for route patterns like @app.route("/path") or @app.get("/path")
                route_patterns = re.findall(r'@\w+\.(route|get|post|put|delete)\([\'"]([^\'"]+)[\'"]', content)
                routes = [route for _, route in route_patterns]
                
            elif gateway_file.endswith((".js", ".ts")):
                gateway_type = "nodejs"
                
                # Check for common JS/TS gateway frameworks
                if "express" in content.lower():
                    gateway_type = "express"
                elif "fastify" in content.lower():
                    gateway_type = "fastify"
                elif "koa" in content.lower():
                    gateway_type = "koa"
                elif "apollo" in content.lower() and "gateway" in content.lower():
                    gateway_type = "apollo"
                
                # Extract routes (simplified)
                import re
                # Look for route patterns like app.get("/path") or router.post("/path")
                route_patterns = re.findall(r'(?:app|router)\.(get|post|put|delete)\([\'"]([^\'"]+)[\'"]', content)
                routes = [route for _, route in route_patterns]
            
            # Add the gateway
            api_gateways.append({
                "file": gateway_file,
                "type": gateway_type,
                "routes": routes
            })
        except Exception as e:
            logger.error(f"Error analyzing gateway file {gateway_file}: {str(e)}")
    
    return api_gateways

def _identify_plugins(repo_path: str, graph_data: Dict) -> List[Dict]:
    """Identify plugin architecture components in the repository"""
    plugins = []
    
    # Look for plugin indicators in directory structure
    plugin_dirs = []
    
    # Check for common plugin directory patterns
    for pattern in ["plugins/", "extensions/", "addons/"]:
        plugin_pattern_path = os.path.join(repo_path, pattern)
        if os.path.exists(plugin_pattern_path) and os.path.isdir(plugin_pattern_path):
            # Add subdirectories as potential plugins
            for item in os.listdir(plugin_pattern_path):
                item_path = os.path.join(plugin_pattern_path, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    plugin_dirs.append(os.path.join(pattern, item))
    
    # Look for plugin loader or registration files
    plugin_loaders = []
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, repo_path)
            
            # Skip hidden files and directories
            if (file.startswith('.') or
                "__pycache__" in rel_path or
                "node_modules" in rel_path or
                ".git" in rel_path):
                continue
            
            # Check filename for plugin indicators
            if ("plugin" in file.lower() and 
                ("loader" in file.lower() or "registry" in file.lower() or "manager" in file.lower())):
                plugin_loaders.append(rel_path)
            
            # For Python and JS/TS files, check content for plugin patterns
            if file.endswith((".py", ".js", ".ts")):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read().lower()
                        
                        # Check for plugin patterns in content
                        if ((("plugin" in content or "extension" in content) and
                             ("load" in content or "register" in content)) or
                            "pluginmanager" in content.replace(" ", "").lower()):
                            plugin_loaders.append(rel_path)
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {str(e)}")
    
    # Create plugin info objects from directories
    for plugin_dir in plugin_dirs:
        full_path = os.path.join(repo_path, plugin_dir)
        plugin_name = os.path.basename(plugin_dir)
        
        # Determine plugin type
        plugin_type = "unknown"
        if os.path.exists(os.path.join(full_path, "requirements.txt")) or os.path.exists(os.path.join(full_path, "pyproject.toml")):
            plugin_type = "python"
        elif os.path.exists(os.path.join(full_path, "package.json")):
            plugin_type = "nodejs"
        elif os.path.exists(os.path.join(full_path, "plugin.xml")) or os.path.exists(os.path.join(full_path, "manifest.xml")):
            plugin_type = "xml-based"
        
        # Check for configuration files
        config_files = []
        for file in os.listdir(full_path):
            if file.lower() in ["plugin.json", "manifest.json", "config.json", "plugin.yml", "plugin.yaml"]:
                config_files.append(file)
        
        # Add the plugin
        plugins.append({
            "name": plugin_name,
            "path": plugin_dir,
            "type": plugin_type,
            "config_files": config_files
        })
    
    # Add plugin loader information
    for loader_file in plugin_loaders:
        file_path = os.path.join(repo_path, loader_file)
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            
            # Determine loader type
            loader_type = "unknown"
            
            if loader_file.endswith(".py"):
                loader_type = "python"
            elif loader_file.endswith((".js", ".ts")):
                loader_type = "nodejs"
            
            # Check if this is likely a plugin system file
            is_plugin_system = False
            if ("plugin" in content.lower() and 
                ("load" in content.lower() or "register" in content.lower() or "manager" in content.lower())):
                is_plugin_system = True
            
            if is_plugin_system:
                plugins.append({
                    "name": os.path.basename(loader_file),
                    "path": loader_file,
                    "type": f"{loader_type}-loader",
                    "is_loader": True
                })
        except Exception as e:
            logger.error(f"Error analyzing plugin loader file {loader_file}: {str(e)}")
    
    return plugins

def _analyze_service_communications(repo_path: str, graph_data: Dict, microservices: List[Dict]) -> List[Dict]:
    """Analyze communication patterns between microservices"""
    communications = []
    
    # Get microservice paths for checking
    microservice_paths = {ms["path"]: ms["name"] for ms in microservices}
    
    # Look for communication patterns in source files
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, repo_path)
            
            # Skip hidden files and directories
            if (file.startswith('.') or
                "__pycache__" in rel_path or
                "node_modules" in rel_path or
                ".git" in rel_path):
                continue
            
            # Only check source files
            if not file.endswith((".py", ".js", ".ts", ".java", ".go")):
                continue
            
            # Determine which microservice this file belongs to
            source_service = None
            for ms_path, ms_name in microservice_paths.items():
                if rel_path.startswith(ms_path):
                    source_service = ms_name
                    break
            
            # Skip if not part of a microservice
            if not source_service:
                continue
            
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                
                # Check for HTTP/API calls
                http_patterns = {
                    "python": ["requests.get", "requests.post", "requests.put", "requests.delete", 
                              "http.client", "urllib", "aiohttp.Client"],
                    "nodejs": ["fetch(", "axios.", "http.request", "https.request"],
                    "general": ["api_url", "apiUrl", "api_endpoint", "apiEndpoint", 
                               "service_url", "serviceUrl", "service_endpoint", "serviceEndpoint"]
                }
                
                # Check for message queue / event bus patterns
                mq_patterns = {
                    "python": ["kafka", "rabbitmq", "pubsub", "redis.pubsub", "nats."],
                    "nodejs": ["kafka", "amqp", "rabbitmq", "pubsub", "redis.pubsub", "nats."],
                    "general": ["message_broker", "messageBroker", "event_bus", "eventBus", 
                               "publish", "subscribe", "producer", "consumer"]
                }
                
                # Check for gRPC patterns
                grpc_patterns = {
                    "python": ["grpc.", "import grpc"],
                    "nodejs": ["@grpc/", "grpc."],
                    "general": ["rpc_client", "rpcClient", "stub."]
                }
                
                # Determine file type
                file_type = "general"
                if file.endswith(".py"):
                    file_type = "python"
                elif file.endswith((".js", ".ts")):
                    file_type = "nodejs"
                
                # Check for communication patterns
                comm_type = None
                comm_details = []
                
                # Check HTTP patterns
                for pattern in http_patterns[file_type] + http_patterns["general"]:
                    if pattern in content:
                        comm_type = "http"
                        comm_details.append(pattern)
                
                # Check message queue patterns
                for pattern in mq_patterns[file_type] + mq_patterns["general"]:
                    if pattern in content:
                        comm_type = comm_type or "message_queue"
                        comm_details.append(pattern)
                
                # Check gRPC patterns
                for pattern in grpc_patterns[file_type] + grpc_patterns["general"]:
                    if pattern in content:
                        comm_type = comm_type or "grpc"
                        comm_details.append(pattern)
                
                # If communication patterns found, add to results
                if comm_type:
                    # Try to determine target service
                    target_service = None
                    for ms_path, ms_name in microservice_paths.items():
                        ms_path_parts = ms_path.split(os.sep)
                        ms_name_parts = ms_name.split('-')
                        
                        # Check if service name appears in the content
                        if ms_name in content or any(part in content for part in ms_name_parts if len(part) > 3):
                            target_service = ms_name
                            break
                    
                    communications.append({
                        "source_service": source_service,
                        "target_service": target_service,
                        "file": rel_path,
                        "type": comm_type,
                        "details": list(set(comm_details))  # Unique patterns
                    })
            except Exception as e:
                logger.error(f"Error analyzing file {file_path} for service communications: {str(e)}")
    
    return communications

def _generate_microservice_recommendations(microservices: List[Dict], api_gateways: List[Dict], 
                                          plugins: List[Dict], service_comms: List[Dict]) -> List[str]:
    """Generate recommendations for microservice architecture optimization"""
    recommendations = []
    
    # Check if microservices are identified
    if not microservices:
        recommendations.append("No clear microservice structure detected. Consider adopting a microservice architecture with well-defined service boundaries.")
        return recommendations
    
    # Check for API gateway
    if not api_gateways:
        recommendations.append("No API gateway detected. Consider implementing an API gateway to centralize request handling and enforce cross-cutting concerns.")
    elif len(api_gateways) > 1:
        recommendations.append(f"Multiple API gateways detected ({len(api_gateways)}). Consider consolidating to a single gateway or implementing a federated gateway architecture.")
    
    # Check for plugin architecture
    if not plugins:
        recommendations.append("No plugin architecture detected. Consider implementing a plugin system to allow for extensibility and modularity.")
    
    # Check communication patterns
    comm_types = {}
    for comm in service_comms:
        comm_type = comm.get("type")
        if comm_type:
            comm_types[comm_type] = comm_types.get(comm_type, 0) + 1
    
    if not comm_types:
        recommendations.append("No clear service-to-service communication patterns detected. Consider implementing explicit communication mechanisms.")
    elif len(comm_types) > 2:
        comm_type_str = ", ".join(f"{k} ({v})" for k, v in comm_types.items())
        recommendations.append(f"Multiple communication patterns detected ({comm_type_str}). Consider standardizing on one or two protocols.")
    
    if "http" in comm_types and comm_types.get("http", 0) > 5:
        recommendations.append("Heavy use of HTTP for service communication detected. Consider using a more efficient protocol like gRPC for internal service communication.")
    
    if "message_queue" not in comm_types:
        recommendations.append("No message queue usage detected. Consider implementing event-driven architecture for better scalability and resilience.")
    
    # Check for service isolation
    if len(microservices) > 1:
        recommendations.append(f"Ensure each microservice ({len(microservices)} detected) has its own database or schema to maintain data isolation.")
    
    # Add TerraFusion-specific recommendations for microservices
    recommendations.append("Consider implementing a Model Content Protocol (MCP) for standardized communication between services.")
    recommendations.append("Implement container orchestration (like Kubernetes) to manage the deployment of microservices.")
    recommendations.append("Set up centralized logging and monitoring for all microservices.")
    recommendations.append("Implement circuit breakers for resilient service-to-service communication.")
    
    return recommendations

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