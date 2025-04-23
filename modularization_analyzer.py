import os
import logging
import ast
import networkx as nx
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
        if node.module:  # Ensure the module exists
            for name in node.names:
                self.imports.append({
                    'type': 'from_import',
                    'module': node.module,
                    'name': name.name,
                    'alias': name.asname,
                    'line': node.lineno
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
    # Handle standard library and third-party imports
    if not import_path.startswith('.'):
        return import_path
    
    # Handle relative imports
    current_dir = os.path.dirname(current_file)
    level = 0
    
    # Count leading dots for relative imports
    while import_path.startswith('.'):
        import_path = import_path[1:]
        level += 1
    
    # Move up the directory tree based on the number of dots
    target_dir = current_dir
    for _ in range(level - 1):
        target_dir = os.path.dirname(target_dir)
    
    # If there's a specific module after the dots, append it
    if import_path:
        normalized_path = os.path.join(target_dir, import_path.replace('.', '/'))
    else:
        normalized_path = target_dir
    
    # Convert to relative path from repo root
    try:
        rel_path = os.path.relpath(normalized_path, repo_path)
        return rel_path.replace('/', '.')
    except ValueError:
        # In case of paths outside the repository
        return import_path

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
    
    # Add all files as nodes
    for file_path in python_files:
        # Use the file path without extension as node ID
        node_id = os.path.splitext(file_path)[0].replace('/', '.')
        G.add_node(node_id, file_path=file_path)
    
    # Process imports in each file
    for file_path in python_files:
        full_path = os.path.join(repo_path, file_path)
        imports = analyze_file_imports(full_path)
        
        # Use the file path without extension as source node
        source_node = os.path.splitext(file_path)[0].replace('/', '.')
        
        for imp in imports:
            if imp['type'] == 'import':
                # Handle direct imports (import x)
                target_module = imp['module'].split('.')[0]  # Use first part of the import
            else:
                # Handle from-imports (from x import y)
                target_module = imp['module'].split('.')[0]  # Use first part of the import
            
            # Check if this is a local module (exists in the repository)
            local_module = False
            for py_file in python_files:
                py_module = os.path.splitext(py_file)[0].replace('/', '.')
                if py_module == target_module or py_module.endswith('.' + target_module):
                    local_module = True
                    # Add edge from the current file to the imported module
                    G.add_edge(source_node, py_module)
            
            # If not found as a direct match, try to handle relative imports
            if not local_module and imp['type'] == 'from_import' and imp['module'].startswith('.'):
                normalized_module = normalize_import_path(imp['module'], file_path, repo_path)
                
                # Check if the normalized module exists in the repository
                for py_file in python_files:
                    py_module = os.path.splitext(py_file)[0].replace('/', '.')
                    if py_module == normalized_module or py_module.endswith('.' + normalized_module):
                        # Add edge from the current file to the imported module
                        G.add_edge(source_node, py_module)
    
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
    
    # Attempt to identify modules using community detection
    try:
        # Convert to undirected graph for community detection
        G_undirected = G.to_undirected()
        
        # Use connected components as a simple clustering method
        connected_components = list(nx.connected_components(G_undirected))
        
        # Extract modules
        for i, component in enumerate(connected_components):
            # Skip tiny components (likely isolated files)
            if len(component) <= 1:
                continue
                
            # Find a suitable module name (based on common prefixes or directory structure)
            component_files = [G.nodes[node]['file_path'] for node in component if 'file_path' in G.nodes[node]]
            
            # Try to find a common directory
            common_dirs = defaultdict(int)
            for file_path in component_files:
                dir_path = os.path.dirname(file_path)
                if dir_path:
                    common_dirs[dir_path] += 1
            
            # Get the most common directory
            module_name = f"module_{i}"
            if common_dirs:
                most_common_dir = max(common_dirs.items(), key=lambda x: x[1])[0]
                if most_common_dir:
                    module_name = most_common_dir.replace('/', '.')
            
            modules.append({
                'name': module_name,
                'files': component_files,
                'size': len(component)
            })
    except Exception as e:
        logger.error(f"Error identifying modules: {str(e)}")
        
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
        total_degree = in_degree + out_degree
        
        # Consider a file as highly coupled if it has many connections
        if total_degree > 5:  # Arbitrary threshold, adjust as needed
            file_path = G.nodes[node].get('file_path', 'unknown')
            high_coupling.append({
                'file': file_path,
                'in_degree': in_degree,
                'out_degree': out_degree,
                'total_degree': total_degree
            })
    
    # Sort by total degree (highest first)
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
        # Find all simple cycles in the graph
        simple_cycles = list(nx.simple_cycles(G))
        
        # Convert node names to file paths for better readability
        for cycle in simple_cycles:
            cycle_files = []
            for node in cycle:
                file_path = G.nodes[node].get('file_path', node)
                cycle_files.append(file_path)
            
            cycles.append(cycle_files)
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
    
    # Recommendations based on identified modules
    if modules:
        module_sizes = [module['size'] for module in modules]
        avg_module_size = sum(module_sizes) / len(modules)
        
        if avg_module_size > 10:  # If modules are too large on average
            recommendations.append(
                "Consider splitting large modules into smaller, more focused components."
            )
        
        recommendations.append(
            f"Organize code into {len(modules)} well-defined modules based on the identified natural clusters."
        )
    else:
        recommendations.append(
            "Consider organizing the codebase into modules based on functionality or domain concepts."
        )
    
    # Recommendations based on high coupling
    if high_coupling:
        recommendations.append(
            f"Reduce coupling in {len(high_coupling)} highly connected files by extracting common functionality into utility modules."
        )
        
        for file in high_coupling[:3]:  # Top 3 most coupled files
            recommendations.append(
                f"Refactor '{file['file']}' to reduce its {file['total_degree']} dependencies."
            )
    
    # Recommendations based on circular dependencies
    if cycles:
        recommendations.append(
            f"Resolve {len(cycles)} circular dependencies that create tight coupling between modules."
        )
        
        for cycle in cycles[:3]:  # Top 3 cycles
            cycle_str = " → ".join(cycle)
            recommendations.append(
                f"Break the circular dependency: {cycle_str}"
            )
    
    # General recommendations
    recommendations.append(
        "Apply the Dependency Inversion Principle to decouple high-level modules from low-level implementation details."
    )
    
    recommendations.append(
        "Create clear interfaces between modules to reduce coupling and improve maintainability."
    )
    
    recommendations.append(
        "Consider introducing a layered architecture to separate concerns (e.g., presentation, business logic, data access)."
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
    logger.info(f"Analyzing modularization for repository at {repo_path}...")
    
    # Initialize results
    results = {
        'dependency_graph': {},
        'current_modules': [],
        'highly_coupled_files': [],
        'circular_dependencies': [],
        'recommendations': []
    }
    
    # Find all Python files
    python_files = find_python_files(repo_path)
    if not python_files:
        logger.info("No Python files found.")
        results['recommendations'] = [
            "No Python files found to analyze modularization.",
            "Consider organizing your code into Python modules as you develop."
        ]
        return results
    
    # Create dependency graph
    G = create_dependency_graph(repo_path, python_files)
    
    # Convert graph to serializable format
    serializable_graph = {
        'nodes': [{'id': node, 'file': G.nodes[node].get('file_path', 'unknown')} for node in G.nodes()],
        'edges': [{'source': source, 'target': target} for source, target in G.edges()]
    }
    results['dependency_graph'] = serializable_graph
    
    # Identify natural modules
    modules = identify_modules(G)
    if modules:
        results['current_modules'] = modules
    
    # Find highly coupled files
    high_coupling = find_highly_connected_files(G)
    if high_coupling:
        results['highly_coupled_files'] = high_coupling
    
    # Find circular dependencies
    cycles = find_circular_dependencies(G)
    if cycles:
        results['circular_dependencies'] = cycles
    
    # Generate modularization recommendations
    recommendations = generate_modularization_recommendations(modules, high_coupling, cycles)
    if recommendations:
        results['recommendations'] = recommendations
    
    logger.info(f"Modularization analysis complete. Found {len(modules)} potential modules and {len(cycles)} circular dependencies.")
    return results