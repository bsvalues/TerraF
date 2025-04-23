import os
import re
import ast
import logging
from pathlib import Path
from collections import defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowVisitor(ast.NodeVisitor):
    """AST visitor for identifying workflow patterns in Python code"""
    
    def __init__(self):
        self.workflow_components = {
            'entry_points': [],
            'operations': [],
            'patterns': set()
        }
        
        # Track current class/function for context
        self.current_context = None
    
    def visit_ClassDef(self, node):
        """Process class definitions"""
        prev_context = self.current_context
        self.current_context = f"class:{node.name}"
        
        # Check for workflow-related class names
        workflow_class_patterns = [
            'workflow', 'pipeline', 'process', 'task', 'job', 'executor',
            'scheduler', 'orchestrator', 'runner', 'manager', 'handler'
        ]
        
        if any(pattern in node.name.lower() for pattern in workflow_class_patterns):
            self.workflow_components['patterns'].add('class_based_workflow')
            
            # Record this class as a workflow component
            self.workflow_components['operations'].append({
                'type': 'workflow_class',
                'name': node.name,
                'line': node.lineno
            })
        
        # Continue visiting child nodes
        self.generic_visit(node)
        self.current_context = prev_context
    
    def visit_FunctionDef(self, node):
        """Process function definitions"""
        prev_context = self.current_context
        self.current_context = f"function:{node.name}"
        
        # Check for workflow-related function names
        workflow_func_patterns = [
            'run', 'execute', 'process', 'pipeline', 'workflow', 'task',
            'job', 'schedule', 'orchestrate', 'handle', 'manage', 'dispatch'
        ]
        
        # Check for main entry points
        if node.name == 'main' or hasattr(node, 'decorator_list') and any(
            hasattr(d, 'id') and d.id == 'main' for d in node.decorator_list
        ):
            self.workflow_components['entry_points'].append({
                'type': 'main_function',
                'name': node.name,
                'line': node.lineno
            })
            self.workflow_components['patterns'].add('script_entry_point')
            
        # Check for other workflow-related functions
        elif any(pattern in node.name.lower() for pattern in workflow_func_patterns):
            # Record this function as a workflow component
            self.workflow_components['operations'].append({
                'type': 'workflow_function',
                'name': node.name,
                'line': node.lineno
            })
            
            # If this has decorators, it might be a task definition
            if hasattr(node, 'decorator_list') and node.decorator_list:
                decorator_names = []
                for decorator in node.decorator_list:
                    if hasattr(decorator, 'id'):
                        decorator_names.append(decorator.id)
                    elif hasattr(decorator, 'attr'):
                        decorator_names.append(decorator.attr)
                
                if decorator_names:
                    for name in decorator_names:
                        task_decorators = ['task', 'job', 'step', 'workflow', 'process']
                        if any(td in name.lower() for td in task_decorators):
                            self.workflow_components['patterns'].add('decorated_tasks')
                            break
        
        # Continue visiting child nodes
        self.generic_visit(node)
        self.current_context = prev_context
    
    def visit_Call(self, node):
        """Process function/method calls"""
        # Check for workflow-related calls
        if hasattr(node, 'func'):
            # Direct function calls like run_workflow()
            if hasattr(node.func, 'id'):
                func_name = node.func.id
                workflow_func_calls = [
                    'run', 'execute', 'process', 'pipeline', 'workflow', 'task',
                    'job', 'schedule', 'orchestrate', 'handle', 'manage', 'dispatch'
                ]
                
                if any(pattern in func_name.lower() for pattern in workflow_func_calls):
                    self.workflow_components['operations'].append({
                        'type': 'workflow_call',
                        'name': func_name,
                        'line': getattr(node, 'lineno', 0)
                    })
                    
                    # Identify specific patterns
                    if func_name.lower() in ['run', 'execute']:
                        self.workflow_components['patterns'].add('imperative_workflow')
            
            # Method calls like executor.run()
            elif hasattr(node.func, 'attr') and hasattr(node.func, 'value'):
                method_name = node.func.attr
                workflow_method_calls = [
                    'run', 'execute', 'process', 'start', 'submit', 'schedule',
                    'orchestrate', 'dispatch', 'handle', 'manage'
                ]
                
                if any(pattern in method_name.lower() for pattern in workflow_method_calls):
                    # Try to get the object name
                    object_name = ""
                    if hasattr(node.func.value, 'id'):
                        object_name = node.func.value.id
                    
                    self.workflow_components['operations'].append({
                        'type': 'workflow_method_call',
                        'object': object_name,
                        'method': method_name,
                        'line': getattr(node, 'lineno', 0)
                    })
                    
                    # Identify specific patterns
                    workflow_objects = ['workflow', 'pipeline', 'executor', 'runner', 'manager']
                    if object_name and any(pattern in object_name.lower() for pattern in workflow_objects):
                        self.workflow_components['patterns'].add('object_oriented_workflow')
        
        # Continue visiting child nodes
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Process from-import statements"""
        if node.module:
            workflow_modules = [
                'workflow', 'pipeline', 'task', 'job', 'executor', 'scheduler',
                'orchestrator', 'airflow', 'prefect', 'dagster', 'luigi', 'dask'
            ]
            
            if any(pattern in node.module.lower() for pattern in workflow_modules):
                for name in node.names:
                    self.workflow_components['operations'].append({
                        'type': 'workflow_import',
                        'module': node.module,
                        'name': name.name,
                        'line': node.lineno
                    })
                    
                    # Identify specific frameworks
                    if 'airflow' in node.module.lower():
                        self.workflow_components['patterns'].add('airflow')
                    elif 'prefect' in node.module.lower():
                        self.workflow_components['patterns'].add('prefect')
                    elif 'dagster' in node.module.lower():
                        self.workflow_components['patterns'].add('dagster')
                    elif 'luigi' in node.module.lower():
                        self.workflow_components['patterns'].add('luigi')
                    elif 'dask' in node.module.lower():
                        self.workflow_components['patterns'].add('dask')
                    else:
                        self.workflow_components['patterns'].add('custom_workflow_framework')
        
        # Continue visiting child nodes
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Process import statements"""
        workflow_modules = [
            'workflow', 'pipeline', 'airflow', 'prefect', 'dagster', 'luigi', 'dask'
        ]
        
        for name in node.names:
            if any(pattern in name.name.lower() for pattern in workflow_modules):
                self.workflow_components['operations'].append({
                    'type': 'workflow_import',
                    'module': name.name,
                    'line': node.lineno
                })
                
                # Identify specific frameworks
                if 'airflow' in name.name.lower():
                    self.workflow_components['patterns'].add('airflow')
                elif 'prefect' in name.name.lower():
                    self.workflow_components['patterns'].add('prefect')
                elif 'dagster' in name.name.lower():
                    self.workflow_components['patterns'].add('dagster')
                elif 'luigi' in name.name.lower():
                    self.workflow_components['patterns'].add('luigi')
                elif 'dask' in name.name.lower():
                    self.workflow_components['patterns'].add('dask')
                else:
                    self.workflow_components['patterns'].add('custom_workflow_framework')
        
        # Continue visiting child nodes
        self.generic_visit(node)

def find_workflow_files(repo_path):
    """
    Find files that are likely related to workflows
    
    Parameters:
    - repo_path: Path to the cloned repository
    
    Returns:
    - list: Workflow-related files
    """
    workflow_files = []
    
    # Patterns to identify workflow-related files
    workflow_file_patterns = [
        r'.*workflow.*\.py$',
        r'.*pipeline.*\.py$',
        r'.*task.*\.py$',
        r'.*job.*\.py$',
        r'.*process.*\.py$',
        r'.*executor.*\.py$',
        r'.*scheduler.*\.py$',
        r'.*orchestrat.*\.py$',
        r'.*runner.*\.py$',
        r'.*manager.*\.py$',
        r'dags/.*\.py$',  # Airflow DAGs
        r'flows/.*\.py$',  # Prefect flows
        r'pipelines/.*\.py$',  # Generic pipelines directory
    ]
    
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
                
                # Check if the file matches workflow patterns by name
                if any(re.match(pattern, rel_path) for pattern in workflow_file_patterns):
                    workflow_files.append(rel_path)
                    continue
                
                # Check file content for workflow-related code
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read().lower()
                        
                        # Check for workflow-related imports and class/function declarations
                        workflow_indicators = [
                            'import workflow', 'from workflow', 
                            'import pipeline', 'from pipeline',
                            'class workflow', 'def workflow',
                            'class pipeline', 'def pipeline',
                            'import airflow', 'from airflow',
                            'import prefect', 'from prefect',
                            'import dagster', 'from dagster',
                            'import luigi', 'from luigi',
                            'import dask', 'from dask.distributed'
                        ]
                        
                        if any(indicator in content for indicator in workflow_indicators):
                            workflow_files.append(rel_path)
                except Exception:
                    pass  # Skip files that can't be read
    
    return workflow_files

def analyze_workflow_file(repo_path, file_path):
    """
    Analyze a Python file for workflow components
    
    Parameters:
    - repo_path: Path to the repository
    - file_path: Relative path to the file
    
    Returns:
    - dict: Workflow components found in the file
    """
    full_path = os.path.join(repo_path, file_path)
    
    try:
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content, filename=file_path)
        
        # Visit nodes and collect workflow components
        visitor = WorkflowVisitor()
        visitor.visit(tree)
        
        # Add file path to the workflow components dictionary
        workflow_components = visitor.workflow_components
        workflow_components['file'] = file_path
        
        return workflow_components
    except Exception as e:
        logger.error(f"Error analyzing workflow file {file_path}: {str(e)}")
        return {
            'file': file_path,
            'entry_points': [],
            'operations': [],
            'patterns': set()
        }

def identify_workflow_patterns(workflows):
    """
    Identify common workflow patterns from analyzed components
    
    Parameters:
    - workflows: List of workflow component dictionaries
    
    Returns:
    - list: Identified workflow patterns
    """
    # Count pattern occurrences across all files
    pattern_counts = defaultdict(int)
    all_patterns = set()
    
    for workflow in workflows:
        patterns = workflow.get('patterns', set())
        for pattern in patterns:
            pattern_counts[pattern] += 1
            all_patterns.add(pattern)
    
    # Determine primary patterns based on frequency
    primary_patterns = []
    for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
        primary_patterns.append({
            'name': pattern,
            'count': count
        })
    
    return primary_patterns

def generate_standardization_recommendations(workflows, patterns):
    """
    Generate recommendations for standardizing workflow patterns
    
    Parameters:
    - workflows: List of workflow component dictionaries
    - patterns: List of identified workflow patterns
    
    Returns:
    - list: Standardization recommendations
    """
    recommendations = []
    
    # Count pattern frequencies
    pattern_names = [p['name'] for p in patterns]
    
    # Check for mixed patterns
    if len(pattern_names) > 1:
        recommendations.append(
            f"Standardize on a single workflow pattern across the codebase. Currently using {len(pattern_names)} different patterns."
        )
        
        # Recommend based on most common pattern
        if pattern_names:
            most_common = pattern_names[0]
            pretty_name = most_common.replace('_', ' ').title()
            recommendations.append(
                f"Consider adopting the '{pretty_name}' pattern as the standard across all repositories."
            )
    
    # Check for framework adoption
    framework_patterns = ['airflow', 'prefect', 'dagster', 'luigi', 'dask']
    used_frameworks = [p for p in pattern_names if p in framework_patterns]
    
    if not used_frameworks:
        recommendations.append(
            "Consider adopting a mature workflow orchestration framework like Airflow, Prefect, or Dagster."
        )
    elif len(used_frameworks) > 1:
        recommendations.append(
            f"Standardize on a single workflow framework. Currently using multiple frameworks: {', '.join(used_frameworks)}."
        )
    
    # Add general recommendations
    recommendations.append(
        "Define a central workflow registry to keep track of all workflows in the ecosystem."
    )
    
    recommendations.append(
        "Implement consistent error handling and logging across all workflow components."
    )
    
    recommendations.append(
        "Add workflow version tracking to manage changes and dependencies."
    )
    
    # Check for entry points consistency
    entry_point_types = set()
    for workflow in workflows:
        for entry_point in workflow.get('entry_points', []):
            entry_point_types.add(entry_point.get('type', 'unknown'))
    
    if len(entry_point_types) > 1:
        recommendations.append(
            f"Standardize workflow entry points. Currently using {len(entry_point_types)} different types."
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
        'patterns': [],
        'standardization_recommendations': []
    }
    
    # Find workflow-related files
    workflow_files = find_workflow_files(repo_path)
    if not workflow_files:
        logger.info("No workflow-related files found.")
        results['standardization_recommendations'] = [
            "No explicit workflow patterns detected. Consider implementing standardized workflows.",
            "Define reusable workflow components that can be shared across the codebase.",
            "Implement a consistent workflow orchestration mechanism.",
            "Add centralized logging and monitoring for workflows.",
            "Create documentation templates for workflow processes."
        ]
        return results
    
    # Analyze each workflow file
    workflows = []
    all_entry_points = []
    
    for file_path in workflow_files:
        workflow_components = analyze_workflow_file(repo_path, file_path)
        
        # Only include files with actual workflow components
        if workflow_components.get('operations') or workflow_components.get('entry_points'):
            workflows.append(workflow_components)
            all_entry_points.extend(workflow_components.get('entry_points', []))
    
    # Store results
    results['workflows'] = workflows
    results['entry_points'] = all_entry_points
    
    # Identify common patterns
    patterns = identify_workflow_patterns(workflows)
    results['patterns'] = patterns
    
    # Generate recommendations
    recommendations = generate_standardization_recommendations(workflows, patterns)
    results['standardization_recommendations'] = recommendations
    
    logger.info(f"Workflow analysis complete. Found {len(workflows)} workflow files and {len(patterns)} workflow patterns.")
    return results