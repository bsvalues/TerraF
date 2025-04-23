import os
import re
import logging
import ast
import networkx as nx
import pandas as pd
from collections import defaultdict
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImportVisitor(ast.NodeVisitor):
    """AST visitor for tracking imports in a Python file"""
    
    def __init__(self):
        self.imports = []
    
    def visit_Import(self, node):
        """Process 'import x' statements"""
        for name in node.names:
            self.imports.append({
                'type': 'import',
                'module': name.name,
                'alias': name.asname,
                'line': node.lineno
            })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Process 'from x import y' statements"""
        if node.module:
            for name in node.names:
                self.imports.append({
                    'type': 'from_import',
                    'module': node.module,
                    'name': name.name,
                    'alias': name.asname,
                    'line': node.lineno,
                    'level': node.level  # For relative imports
                })
        self.generic_visit(node)

def analyze_file_imports(file_path):
    """
    Analyze imports in a Python file
    
    Parameters:
    - file_path: Path to the Python file
    
    Returns:
    - list: Imported modules
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content, filename=file_path)
        
        # Visit nodes and collect imports
        visitor = ImportVisitor()
        visitor.visit(tree)
        
        return visitor.imports
    except Exception as e:
        logger.error(f"Error analyzing imports in {file_path}: {str(e)}")
        return []

def find_python_files(repo_path):
    """
    Find all Python files in the repository
    
    Parameters:
    - repo_path: Path to the cloned repository
    
    Returns:
    - list: Python files with relative paths
    """
    python_files = []
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            # Skip hidden files
            if file.startswith('.'):
                continue
                
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path)
                
                # Skip hidden directories
                if any(part.startswith('.') for part in Path(rel_path).parts):
                    continue
                
                python_files.append(rel_path)
    
    return python_files

def normalize_import_path(import_path, current_file, repo_path):
    """
    Normalize a potentially relative import path to an absolute one
    
    Parameters:
    - import_path: Import path to normalize
    - current_file: File containing the import
    - repo_path: Repository root path
    
    Returns:
    - str: Normalized import path
    """
    # Handle relative imports
    if import_path.startswith('.'):
        current_dir = os.path.dirname(current_file)
        
        # Count the number of dots for how far up to go
        dots = len(re.match(r'\.+', import_path).group())
        
        # Go up the required number of levels
        for _ in range(dots):
            current_dir = os.path.dirname(current_dir)
        
        # Remove the dots from the import path
        import_path = import_path[dots:]
        
        # Combine with the current directory
        if current_dir:
            normalized_path = current_dir.replace(os.path.sep, '.') + '.' + import_path
        else:
            normalized_path = import_path
    else:
        normalized_path = import_path
    
    return normalized_path

def create_dependency_graph(repo_path, python_files):
    """
    Create a dependency graph based on imports
    
    Parameters:
    - repo_path: Path to the cloned repository
    - python_files: List of Python files
    
    Returns:
    - networkx.DiGraph: Dependency graph
    """
    # Create a directed graph
    G = nx.DiGraph()
    
    # Map from module path to file path
    module_to_file = {}
    
    # First, map module paths to file paths
    for file_path in python_files:
        # Convert file path to module path
        module_path = os.path.splitext(file_path)[0].replace(os.path.sep, '.')
        module_to_file[module_path] = file_path
        
        # Also add the file to the graph
        G.add_node(file_path, type='file')
    
    # Now analyze imports for each file
    for file_path in python_files:
        full_path = os.path.join(repo_path, file_path)
        imports = analyze_file_imports(full_path)
        
        for imp in imports:
            if imp['type'] == 'import':
                module = imp['module']
            else:  # from_import
                module = imp['module']
            
            # Skip standard library and third-party modules
            if not any(module.startswith(f) for f in module_to_file.keys()):
                continue
            
            # Get the most specific match
            best_match = None
            for m in module_to_file:
                if module == m or module.startswith(m + '.'):
                    if best_match is None or len(m) > len(best_match):
                        best_match = m
            
            if best_match:
                target_file = module_to_file[best_match]
                G.add_edge(file_path, target_file, label=module)
    
    return G

def identify_modules(G):
    """
    Identify natural modules in the codebase based on dependencies
    
    Parameters:
    - G: Dependency graph
    
    Returns:
    - list: Identified modules
    """
    modules = []
    
    # Use community detection algorithms to find natural modules
    try:
        import community as community_louvain
        
        # Convert directed graph to undirected for community detection
        G_undirected = G.to_undirected()
        
        # Apply Louvain method for community detection
        partition = community_louvain.best_partition(G_undirected)
        
        # Group files by community
        communities = defaultdict(list)
        for node, community_id in partition.items():
            communities[community_id].append(node)
        
        # Create modules from communities
        for community_id, files in communities.items():
            if len(files) > 1:  # Skip single-file communities
                module_name = f"module_{community_id}"
                
                # Try to infer a better name based on common path prefixes
                common_prefix = os.path.commonpath(files) if files else ""
                if common_prefix:
                    module_name = common_prefix.replace(os.path.sep, '_')
                
                modules.append({
                    'name': module_name,
                    'files': files,
                    'size': len(files)
                })
    except ImportError:
        # Fallback: use directory structure to identify modules
        dirs = defaultdict(list)
        for node in G.nodes():
            directory = os.path.dirname(node)
            if directory:
                dirs[directory].append(node)
        
        for directory, files in dirs.items():
            if len(files) > 1:
                modules.append({
                    'name': directory.replace(os.path.sep, '_'),
                    'files': files,
                    'size': len(files)
                })
    
    return modules

def find_highly_connected_files(G):
    """
    Find files with many dependencies (high coupling)
    
    Parameters:
    - G: Dependency graph
    
    Returns:
    - list: Files with high coupling
    """
    high_coupling = []
    
    # Calculate in-degree and out-degree for each node
    for node in G.nodes():
        in_degree = G.in_degree(node)
        out_degree = G.out_degree(node)
        
        # Consider files with high combined degree as highly coupled
        if in_degree + out_degree > 5:  # Arbitrary threshold
            high_coupling.append({
                'file': node,
                'in_degree': in_degree,
                'out_degree': out_degree,
                'total_degree': in_degree + out_degree
            })
    
    # Sort by total degree (most coupled first)
    high_coupling.sort(key=lambda x: x['total_degree'], reverse=True)
    
    return high_coupling

def find_circular_dependencies(G):
    """
    Find circular dependencies in the code
    
    Parameters:
    - G: Dependency graph
    
    Returns:
    - list: Circular dependency cycles
    """
    cycles = []
    
    try:
        # Find simple cycles in the graph
        simple_cycles = list(nx.simple_cycles(G))
        
        # Filter to keep only meaningful cycles (length > 1)
        cycles = [cycle for cycle in simple_cycles if len(cycle) > 1]
    except Exception as e:
        logger.error(f"Error finding circular dependencies: {str(e)}")
    
    return cycles

def generate_modularization_recommendations(modules, high_coupling, cycles):
    """
    Generate recommendations for improving code modularization
    
    Parameters:
    - modules: Identified modules
    - high_coupling: Files with high coupling
    - cycles: Circular dependency cycles
    
    Returns:
    - list: Recommendations
    """
    recommendations = []
    
    # Recommendations for breaking circular dependencies
    if cycles:
        recommendations.append(
            f"Break {len(cycles)} circular dependencies by introducing interfaces or restructuring the code."
        )
        
        # More specific recommendations for the first few cycles
        for i, cycle in enumerate(cycles[:3]):
            cycle_str = " -> ".join(cycle)
            recommendations.append(
                f"Circular dependency {i+1}: {cycle_str}. Consider extracting shared functionality to a common module."
            )
    
    # Recommendations for reducing coupling
    if high_coupling:
        recommendations.append(
            f"Reduce coupling in {len(high_coupling)} highly connected files by extracting functionality into smaller, focused modules."
        )
        
        # More specific recommendations for the most coupled files
        for coupling in high_coupling[:3]:
            file = coupling['file']
            total = coupling['total_degree']
            recommendations.append(
                f"High coupling in {file} with {total} dependencies. Consider breaking it down into smaller components."
            )
    
    # Recommendations for formalizing identified modules
    if modules:
        recommendations.append(
            f"Formalize {len(modules)} natural modules identified in the codebase."
        )
        
        # More specific recommendations for larger modules
        large_modules = [m for m in modules if m['size'] >= 5]
        for module in large_modules[:3]:
            recommendations.append(
                f"Create a formal module for '{module['name']}' containing {module['size']} files."
            )
    
    # General recommendations
    recommendations.append(
        "Apply the Single Responsibility Principle: each class or module should have only one reason to change."
    )
    
    recommendations.append(
        "Use dependency injection to reduce direct dependencies between components."
    )
    
    recommendations.append(
        "Create clear interfaces between modules to minimize coupling."
    )
    
    return recommendations

def analyze_modularization(repo_path):
    """
    Analyze modularization opportunities in the repository
    
    Parameters:
    - repo_path: Path to the cloned repository
    
    Returns:
    - dict: Modularization analysis results
    """
    logger.info(f"Analyzing modularization opportunities for repository at {repo_path}...")
    
    # Initialize results
    results = {
        'current_modules': [],
        'dependency_graph': {},
        'high_coupling': [],
        'circular_dependencies': [],
        'recommendations': []
    }
    
    # Find all Python files
    python_files = find_python_files(repo_path)
    if not python_files:
        logger.info("No Python files found.")
        return results
    
    # Create dependency graph
    G = create_dependency_graph(repo_path, python_files)
    
    # Identify current modules
    modules = identify_modules(G)
    if modules:
        # Convert to a format suitable for display
        results['current_modules'] = [
            {
                'name': module['name'],
                'file_count': module['size'],
                'files': module['files'][:5] + (['...'] if len(module['files']) > 5 else [])
            }
            for module in modules
        ]
    
    # Find files with high coupling
    high_coupling = find_highly_connected_files(G)
    if high_coupling:
        results['high_coupling'] = high_coupling
    
    # Find circular dependencies
    cycles = find_circular_dependencies(G)
    if cycles:
        results['circular_dependencies'] = [
            {'cycle': cycle}
            for cycle in cycles
        ]
    
    # Convert graph to a serializable format
    node_list = []
    for node in G.nodes():
        node_list.append({
            'id': node,
            'type': 'file'
        })
    
    edge_list = []
    for u, v, data in G.edges(data=True):
        edge_list.append({
            'source': u,
            'target': v,
            'label': data.get('label', '')
        })
    
    results['dependency_graph'] = {
        'nodes': node_list,
        'edges': edge_list
    }
    
    # Generate recommendations
    recommendations = generate_modularization_recommendations(modules, high_coupling, cycles)
    results['recommendations'] = recommendations
    
    logger.info(f"Modularization analysis complete. Found {len(modules)} potential modules.")
    return results
