import os
import re
import logging
import ast
import networkx as nx
from collections import defaultdict
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Common workflow patterns to look for
WORKFLOW_PATTERNS = {
    'pipeline': ['pipeline', 'process', 'flow', 'workflow', 'orchestrator'],
    'event_driven': ['event', 'subscribe', 'publish', 'listener', 'callback', 'handler', 'hook'],
    'batch_processing': ['batch', 'job', 'scheduler', 'cron', 'task', 'queue'],
    'microservice': ['service', 'api', 'endpoint', 'route', 'controller', 'server'],
    'etl': ['extract', 'transform', 'load', 'etl', 'data_pipeline'],
}

class WorkflowVisitor(ast.NodeVisitor):
    """AST visitor for identifying workflow patterns in Python code"""
    
    def __init__(self):
        self.workflow_patterns = {
            'functions': [],
            'classes': [],
            'imports': [],
            'identified_patterns': set()
        }
    
    def visit_Import(self, node):
        """Process 'import x' statements"""
        workflow_libraries = [
            'celery', 'airflow', 'luigi', 'prefect', 'dask', 'ray', 
            'apache_beam', 'flask', 'fastapi', 'django', 'tornado',
            'asyncio', 'aiohttp', 'rabbitmq', 'kafka', 'redis',
            'zmq', 'grpc', 'boto3', 'kubernetes'
        ]
        
        for name in node.names:
            module = name.name.split('.')[0]  # Get the base module name
            if module in workflow_libraries:
                self.workflow_patterns['imports'].append({
                    'type': 'import',
                    'module': name.name,
                    'alias': name.asname,
                    'line': node.lineno
                })
                
                # Add to identified patterns
                self._categorize_workflow_library(module)
        
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Process 'from x import y' statements"""
        workflow_libraries = [
            'celery', 'airflow', 'luigi', 'prefect', 'dask', 'ray', 
            'apache_beam', 'flask', 'fastapi', 'django', 'tornado',
            'asyncio', 'aiohttp', 'rabbitmq', 'kafka', 'redis',
            'zmq', 'grpc', 'boto3', 'kubernetes'
        ]
        
        if node.module:
            module = node.module.split('.')[0]  # Get the base module name
            if module in workflow_libraries:
                for name in node.names:
                    self.workflow_patterns['imports'].append({
                        'type': 'from_import',
                        'module': node.module,
                        'name': name.name,
                        'alias': name.asname,
                        'line': node.lineno
                    })
                
                # Add to identified patterns
                self._categorize_workflow_library(module)
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Process class definitions"""
        class_name = node.name.lower()
        
        # Check if the class name matches workflow patterns
        matched_pattern = None
        for pattern_type, keywords in WORKFLOW_PATTERNS.items():
            if any(keyword in class_name for keyword in keywords):
                matched_pattern = pattern_type
                break
        
        if matched_pattern:
            self.workflow_patterns['classes'].append({
                'name': node.name,
                'pattern': matched_pattern,
                'line': node.lineno
            })
            self.workflow_patterns['identified_patterns'].add(matched_pattern)
        
        # Check for workflow-related methods
        workflow_methods = False
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_name = item.name.lower()
                for pattern_type, keywords in WORKFLOW_PATTERNS.items():
                    if any(keyword in method_name for keyword in keywords):
                        workflow_methods = True
                        self.workflow_patterns['identified_patterns'].add(pattern_type)
                        break
        
        if workflow_methods and not matched_pattern:
            self.workflow_patterns['classes'].append({
                'name': node.name,
                'pattern': 'contains_workflow_methods',
                'line': node.lineno
            })
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Process function definitions"""
        function_name = node.name.lower()
        
        # Check if the function name matches workflow patterns
        matched_pattern = None
        for pattern_type, keywords in WORKFLOW_PATTERNS.items():
            if any(keyword in function_name for keyword in keywords):
                matched_pattern = pattern_type
                break
        
        if matched_pattern:
            self.workflow_patterns['functions'].append({
                'name': node.name,
                'pattern': matched_pattern,
                'line': node.lineno
            })
            self.workflow_patterns['identified_patterns'].add(matched_pattern)
        
        self.generic_visit(node)
    
    def _categorize_workflow_library(self, module):
        """Categorize a workflow library into a pattern type"""
        module = module.lower()
        
        # Map libraries to pattern types
        library_patterns = {
            'celery': 'batch_processing',
            'airflow': 'pipeline',
            'luigi': 'pipeline',
            'prefect': 'pipeline',
            'dask': 'batch_processing',
            'ray': 'batch_processing',
            'apache_beam': 'pipeline',
            'flask': 'microservice',
            'fastapi': 'microservice',
            'django': 'microservice',
            'tornado': 'microservice',
            'asyncio': 'event_driven',
            'aiohttp': 'microservice',
            'rabbitmq': 'event_driven',
            'kafka': 'event_driven',
            'redis': 'event_driven',
            'zmq': 'event_driven',
            'grpc': 'microservice',
            'boto3': 'etl',
            'kubernetes': 'orchestration'
        }
        
        if module in library_patterns:
            self.workflow_patterns['identified_patterns'].add(library_patterns[module])

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

def analyze_file_for_workflows(repo_path, file_path):
    """
    Analyze a Python file for workflow patterns
    
    Parameters:
    - repo_path: Path to the repository
    - file_path: Relative path to the file
    
    Returns:
    - dict: Workflow patterns found in the file
    """
    full_path = os.path.join(repo_path, file_path)
    
    try:
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content, filename=file_path)
        
        # Visit nodes and collect workflow patterns
        visitor = WorkflowVisitor()
        visitor.visit(tree)
        
        # Convert identified_patterns from set to list for serialization
        patterns = visitor.workflow_patterns
        patterns['identified_patterns'] = list(patterns['identified_patterns'])
        
        return patterns
    except Exception as e:
        logger.error(f"Error analyzing workflows in {file_path}: {str(e)}")
        return {
            'functions': [],
            'classes': [],
            'imports': [],
            'identified_patterns': []
        }

def identify_workflow_entry_points(workflow_components):
    """
    Identify potential workflow entry points in the codebase
    
    Parameters:
    - workflow_components: Dictionary of workflow components found in the codebase
    
    Returns:
    - list: Potential workflow entry points
    """
    entry_points = []
    
    # Common patterns for entry points
    entry_point_patterns = [
        'main', 'run', 'start', 'execute', 'app', 'server',
        'cli', 'command', 'entrypoint', 'handler'
    ]
    
    for file_path, components in workflow_components.items():
        # Check for main function or __main__ block
        if any(func['name'] == 'main' for func in components['functions']):
            entry_points.append({
                'file': file_path,
                'type': 'main_function',
                'description': 'Contains a main() function'
            })
        elif '__main__' in file_path or 'main.py' in file_path.lower():
            entry_points.append({
                'file': file_path,
                'type': 'main_module',
                'description': 'Appears to be a main module or script'
            })
        
        # Check for functions with entry point-like names
        for func in components['functions']:
            if any(pattern in func['name'].lower() for pattern in entry_point_patterns):
                entry_points.append({
                    'file': file_path,
                    'type': 'entry_function',
                    'description': f"Contains potential entry function: {func['name']}"
                })
                break
        
        # Check for Flask/FastAPI app definitions
        if any('flask' in imp['module'].lower() or 'fastapi' in imp['module'].lower() 
              for imp in components['imports']):
            entry_points.append({
                'file': file_path,
                'type': 'web_app',
                'description': 'Contains web application definition'
            })
    
    return entry_points

def generate_standardization_recommendations(workflow_components, patterns_by_file):
    """
    Generate recommendations for workflow standardization
    
    Parameters:
    - workflow_components: Dictionary of workflow components
    - patterns_by_file: Dictionary of patterns by file
    
    Returns:
    - list: Standardization recommendations
    """
    recommendations = []
    
    # Count the occurrence of each pattern
    pattern_counts = defaultdict(int)
    for patterns in patterns_by_file.values():
        for pattern in patterns:
            pattern_counts[pattern] += 1
    
    # Determine dominant patterns
    total_files = len(patterns_by_file)
    dominant_patterns = [pattern for pattern, count in pattern_counts.items() 
                        if count >= total_files * 0.2]  # At least 20% of files
    
    if dominant_patterns:
        recommendations.append(
            f"Dominant workflow patterns detected: {', '.join(dominant_patterns)}. "
            f"Consider standardizing around these patterns."
        )
    
    # Check for mixed patterns in the same file
    mixed_pattern_files = [file for file, patterns in patterns_by_file.items() 
                          if len(patterns) > 1]
    if mixed_pattern_files:
        recommendations.append(
            f"Found {len(mixed_pattern_files)} files with mixed workflow patterns. "
            f"Consider separating concerns to improve maintainability."
        )
    
    # Check for inconsistent library usage
    library_usage = defaultdict(set)
    for file_path, components in workflow_components.items():
        for imp in components['imports']:
            module = imp['module'].split('.')[0]
            if module in ['celery', 'airflow', 'luigi', 'prefect', 'dask', 'ray', 
                         'flask', 'fastapi', 'django', 'asyncio', 'kafka']:
                library_usage[module].add(file_path)
    
    # Look for libraries used in only a few files
    for library, files in library_usage.items():
        if 1 < len(files) < total_files * 0.2:  # Used in more than 1 but less than 20% of files
            recommendations.append(
                f"Library '{library}' is used inconsistently in {len(files)} files. "
                f"Consider standardizing on a single workflow framework."
            )
    
    # General recommendations
    recommendations.append(
        "Implement a unified error handling and logging strategy across all workflows."
    )
    
    recommendations.append(
        "Create common interfaces for similar workflow components to ensure consistency."
    )
    
    recommendations.append(
        "Document workflow entry points and dependencies for easier onboarding and maintenance."
    )
    
    # Pattern-specific recommendations
    if 'pipeline' in pattern_counts:
        recommendations.append(
            "For data pipelines, ensure consistent monitoring, error handling, and retrying mechanisms."
        )
    
    if 'event_driven' in pattern_counts:
        recommendations.append(
            "For event-driven components, standardize event schemas and handling patterns."
        )
    
    if 'microservice' in pattern_counts:
        recommendations.append(
            "For microservices, implement consistent API conventions and documentation."
        )
    
    if 'batch_processing' in pattern_counts:
        recommendations.append(
            "For batch processes, standardize job scheduling, monitoring, and failure recovery."
        )
    
    return recommendations

def analyze_workflow_patterns(repo_path):
    """
    Analyze workflow patterns in the repository
    
    Parameters:
    - repo_path: Path to the cloned repository
    
    Returns:
    - dict: Workflow analysis results
    """
    logger.info(f"Analyzing workflow patterns for repository at {repo_path}...")
    
    # Initialize results
    results = {
        'workflows': [],
        'entry_points': [],
        'standardization_recommendations': []
    }
    
    # Find all Python files
    python_files = find_python_files(repo_path)
    if not python_files:
        logger.info("No Python files found.")
        return results
    
    # Analyze each file for workflow patterns
    workflow_components = {}
    patterns_by_file = {}
    
    for file_path in python_files:
        components = analyze_file_for_workflows(repo_path, file_path)
        patterns = components.get('identified_patterns', [])
        
        if patterns:
            workflow_components[file_path] = components
            patterns_by_file[file_path] = patterns
    
    if not workflow_components:
        logger.info("No workflow patterns found.")
        results['standardization_recommendations'] = [
            "No clear workflow patterns detected. Consider implementing structured workflows.",
            "Adopt a consistent framework for task orchestration (e.g., Airflow, Prefect, Celery).",
            "Implement clear entry points and execution flows for better maintainability.",
            "Document process flows and dependencies between components."
        ]
        return results
    
    # Convert to a list of dictionaries for better display
    for file_path, patterns in patterns_by_file.items():
        results['workflows'].append({
            'file': file_path,
            'patterns': patterns,
            'workflow_classes': [cls['name'] for cls in workflow_components[file_path]['classes']],
            'workflow_functions': [func['name'] for func in workflow_components[file_path]['functions']]
        })
    
    # Identify workflow entry points
    entry_points = identify_workflow_entry_points(workflow_components)
    results['entry_points'] = entry_points
    
    # Generate standardization recommendations
    recommendations = generate_standardization_recommendations(workflow_components, patterns_by_file)
    results['standardization_recommendations'] = recommendations
    
    logger.info(f"Workflow analysis complete. Found patterns in {len(workflow_components)} files.")
    return results
