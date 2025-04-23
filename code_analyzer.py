import os
import ast
import re
import logging
from collections import defaultdict
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeVisitor(ast.NodeVisitor):
    """AST visitor for analyzing Python code"""
    
    def __init__(self):
        self.imports = []
        self.functions = []
        self.classes = []
        self.global_vars = []
        self.issues = []
        self.complexity = 0
        self.magic_numbers = []
        self.max_nested_level = 0
    
    def visit_ClassDef(self, node):
        """Process class definitions"""
        # Calculate class size
        class_size = self._count_lines(node)
        
        # Check for large classes
        if class_size > 100:
            self.issues.append({
                'type': 'large_class',
                'message': f"Class '{node.name}' is too large ({class_size} lines)",
                'line': node.lineno
            })
        
        # Record class info
        self.classes.append({
            'name': node.name,
            'line': node.lineno,
            'size': class_size,
            'methods': len([m for m in node.body if isinstance(m, ast.FunctionDef)])
        })
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Process function and method definitions"""
        # Calculate function size and complexity
        func_size = self._count_lines(node)
        complexity = self._calculate_complexity(node)
        
        # Check for long methods
        if func_size > 30:
            self.issues.append({
                'type': 'long_method',
                'message': f"Function '{node.name}' is too long ({func_size} lines)",
                'line': node.lineno
            })
        
        # Check for complex methods
        if complexity > 10:
            self.issues.append({
                'type': 'complex_method',
                'message': f"Function '{node.name}' is too complex (complexity: {complexity})",
                'line': node.lineno
            })
        
        # Check for too many parameters
        if len(node.args.args) > 5:
            self.issues.append({
                'type': 'too_many_parameters',
                'message': f"Function '{node.name}' has too many parameters ({len(node.args.args)})",
                'line': node.lineno
            })
        
        # Record function info
        self.functions.append({
            'name': node.name,
            'line': node.lineno,
            'size': func_size,
            'complexity': complexity,
            'params': len(node.args.args)
        })
        
        # Check for nested conditionals
        self._check_nesting_level(node, 0)
        
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Process import statements"""
        for name in node.names:
            self.imports.append({
                'type': 'import',
                'module': name.name,
                'alias': name.asname,
                'line': node.lineno
            })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Process from-import statements"""
        for name in node.names:
            self.imports.append({
                'type': 'from_import',
                'module': node.module,
                'name': name.name,
                'alias': name.asname,
                'line': node.lineno
            })
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Process assignments to find global variables"""
        for target in node.targets:
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                # Check if this is at the module level (global)
                if isinstance(target.ctx, ast.Store) and hasattr(node, 'parent_node') and isinstance(node.parent_node, ast.Module):
                    self.global_vars.append({
                        'name': target.id,
                        'value': node.value.value if hasattr(node.value, 'value') else str(node.value),
                        'line': node.lineno
                    })
        self.generic_visit(node)
    
    def visit_Constant(self, node):
        """Process numeric literals to find magic numbers"""
        # Skip literals in global scope
        if hasattr(node, 'parent_node') and not isinstance(node.parent_node, ast.Module):
            # Only consider numeric constants that aren't 0, 1, or -1
            if isinstance(node.value, (int, float)) and node.value not in [0, 1, -1]:
                self.magic_numbers.append({
                    'value': node.value,
                    'line': getattr(node, 'lineno', 0)
                })
        self.generic_visit(node)
    
    # For compatibility with Python 3.7 and earlier
    def visit_Num(self, node):
        """Process numeric literals to find magic numbers (legacy)"""
        # Skip literals in global scope
        if hasattr(node, 'parent_node') and not isinstance(node.parent_node, ast.Module):
            # Only consider numeric constants that aren't 0, 1, or -1
            if node.n not in [0, 1, -1]:
                self.magic_numbers.append({
                    'value': node.n,
                    'line': getattr(node, 'lineno', 0)
                })
        self.generic_visit(node)
    
    def visit_If(self, node):
        """Process if statements to detect nesting"""
        self._check_nesting_level(node, 0)
        self.generic_visit(node)
    
    def _check_nesting_level(self, node, current_level):
        """Recursively check nesting level of conditional statements"""
        # Check conditional blocks (if, for, while)
        if isinstance(node, (ast.If, ast.For, ast.While)):
            next_level = current_level + 1
            self.max_nested_level = max(self.max_nested_level, next_level)
            
            # Flag deeply nested conditions
            if next_level >= 3:
                self.issues.append({
                    'type': 'nested_conditionals',
                    'message': f"Deeply nested conditional blocks (level {next_level})",
                    'line': node.lineno
                })
            
            # Recursively check the body
            for item in node.body:
                self._check_nesting_level(item, next_level)
            
            # Check else branch if it exists
            if hasattr(node, 'orelse') and node.orelse:
                for item in node.orelse:
                    self._check_nesting_level(item, 
                                             current_level if isinstance(node, ast.If) else next_level)
    
    def _count_lines(self, node):
        """Count the number of lines in a node"""
        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
            return node.end_lineno - node.lineno + 1
        return 5  # Default fallback if line information is not available
    
    def _calculate_complexity(self, node):
        """Calculate cyclomatic complexity of a function/method"""
        complexity = 1  # Base complexity
        
        # Count control flow statements
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.BoolOp) and isinstance(child.op, ast.And):
                complexity += len(child.values) - 1
        
        return complexity

def analyze_python_file(file_path):
    """
    Analyze a Python file using AST
    
    Parameters:
    - file_path: Path to the Python file
    
    Returns:
    - dict: Analysis results
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content, filename=file_path)
        
        # Augment AST with parent references
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent_node = node
        
        # Visit nodes
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        # Look for commented out code
        commented_code = find_commented_code(content)
        
        # Add commented code as an issue
        for line in commented_code:
            visitor.issues.append({
                'type': 'commented_code',
                'message': "Commented-out code detected",
                'line': line
            })
        
        # Calculate overall complexity
        total_complexity = sum(func['complexity'] for func in visitor.functions)
        average_complexity = total_complexity / len(visitor.functions) if visitor.functions else 0
        
        # Generate summary metrics
        metrics = {
            'lines_of_code': len(content.splitlines()),
            'function_count': len(visitor.functions),
            'class_count': len(visitor.classes),
            'import_count': len(visitor.imports),
            'average_complexity': round(average_complexity, 2),
            'max_nested_level': visitor.max_nested_level
        }
        
        # Categorize issues by type
        issues_by_type = defaultdict(list)
        for issue in visitor.issues:
            issues_by_type[issue['type']].append(issue)
        
        return {
            'metrics': metrics,
            'functions': visitor.functions,
            'classes': visitor.classes,
            'imports': visitor.imports,
            'global_vars': visitor.global_vars,
            'issues': visitor.issues,
            'magic_numbers': visitor.magic_numbers
        }
    except Exception as e:
        logger.error(f"Error analyzing file {file_path}: {str(e)}")
        return {
            'metrics': {},
            'functions': [],
            'classes': [],
            'imports': [],
            'global_vars': [],
            'issues': [{
                'type': 'error',
                'message': f"Error analyzing file: {str(e)}",
                'line': 0
            }],
            'magic_numbers': []
        }

def find_commented_code(content):
    """
    Detect blocks of commented code
    
    Parameters:
    - content: File content as string
    
    Returns:
    - list: Line numbers where commented code blocks start
    """
    lines = content.splitlines()
    commented_code_lines = []
    
    # Pattern to detect code-like comments (e.g., conditionals, functions, classes)
    code_patterns = [
        r'^\s*#\s*(def|class|if|for|while|return|import|from)',
        r'^\s*#\s*[a-zA-Z0-9_]+\s*=',
        r'^\s*#\s*[a-zA-Z0-9_]+\(',
    ]
    
    for i, line in enumerate(lines):
        for pattern in code_patterns:
            if re.search(pattern, line):
                # Add 1 to convert from 0-index to 1-index for line numbers
                commented_code_lines.append(i + 1)
                break
    
    return commented_code_lines

def analyze_file(repo_path, file_path):
    """
    Analyze a file based on its extension
    
    Parameters:
    - repo_path: Path to the repository
    - file_path: Relative path to the file
    
    Returns:
    - dict: Analysis results or None if file type is not supported
    """
    full_path = os.path.join(repo_path, file_path)
    
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext == '.py':
        return analyze_python_file(full_path)
    
    # Add support for other file types as needed
    
    return None

def count_file_lines(file_path):
    """Count the number of lines in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return len(f.readlines())
    except Exception:
        return 0

def find_duplicated_code_simple(repo_path, file_paths, min_lines=5):
    """
    A simple approach to find potential code duplications
    
    Parameters:
    - repo_path: Path to the repository
    - file_paths: List of file paths to analyze
    - min_lines: Minimum consecutive lines to consider as duplication
    
    Returns:
    - list: Potential code duplications
    """
    duplications = []
    
    # Extract all file contents
    file_contents = {}
    for file_path in file_paths:
        try:
            full_path = os.path.join(repo_path, file_path)
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                file_contents[file_path] = f.readlines()
        except Exception:
            continue
    
    # Simple sliding window approach to find duplicated blocks
    for file1, lines1 in file_contents.items():
        for i in range(len(lines1) - min_lines + 1):
            block = ''.join(lines1[i:i+min_lines])
            if not block.strip():  # Skip empty blocks
                continue
                
            # Look for this block in other files
            for file2, lines2 in file_contents.items():
                if file1 == file2:  # Skip same file
                    continue
                    
                for j in range(len(lines2) - min_lines + 1):
                    compare_block = ''.join(lines2[j:j+min_lines])
                    if block == compare_block:
                        # Found a duplication
                        duplications.append({
                            'file1': file1,
                            'start_line1': i + 1,  # 1-based line numbers
                            'file2': file2,
                            'start_line2': j + 1,  # 1-based line numbers
                            'lines': min_lines
                        })
    
    return duplications

def perform_code_review(repo_path):
    """
    Perform a comprehensive code review of the repository
    
    Parameters:
    - repo_path: Path to the cloned repository
    
    Returns:
    - dict: Code review results
    """
    logger.info(f"Performing code review for repository at {repo_path}...")
    
    # Initialize results
    results = {
        'metrics': {},
        'top_complex_files': [],
        'files_with_issues': [],
        'duplications': [],
        'improvement_opportunities': {}
    }
    
    # Find all Python files
    python_files = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith('.py'):
                if any(part.startswith('.') for part in Path(root).parts):
                    continue  # Skip hidden directories
                
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path)
                python_files.append(rel_path)
    
    if not python_files:
        logger.info("No Python files found.")
        results['improvement_opportunities']['General'] = [
            "No Python files found in the repository."
        ]
        return results
    
    # Analyze each Python file
    total_loc = 0
    total_functions = 0
    total_classes = 0
    total_complexity = 0
    total_issues = 0
    
    file_analyses = {}
    for file_path in python_files:
        analysis = analyze_file(repo_path, file_path)
        if analysis:
            file_analyses[file_path] = analysis
            
            # Accumulate metrics
            total_loc += analysis.get('metrics', {}).get('lines_of_code', 0)
            total_functions += len(analysis.get('functions', []))
            total_classes += len(analysis.get('classes', []))
            
            for func in analysis.get('functions', []):
                total_complexity += func.get('complexity', 0)
            
            total_issues += len(analysis.get('issues', []))
            
            # Record files with issues
            if analysis.get('issues', []):
                results['files_with_issues'].append({
                    'file': file_path,
                    'issue_count': len(analysis['issues']),
                    'details': [issue['message'] for issue in analysis['issues']]
                })
    
    # Calculate overall metrics
    results['metrics'] = {
        'total_files': len(python_files),
        'total_loc': total_loc,
        'total_functions': total_functions,
        'total_classes': total_classes,
        'average_loc_per_file': round(total_loc / len(python_files) if python_files else 0, 2),
        'average_complexity': round(total_complexity / total_functions if total_functions else 0, 2),
        'issue_density': round(total_issues / total_loc * 1000 if total_loc else 0, 2)  # Issues per 1000 lines
    }
    
    # Find most complex files
    complex_files = []
    for file_path, analysis in file_analyses.items():
        # Calculate file complexity as sum of function complexities
        file_complexity = sum(func.get('complexity', 0) for func in analysis.get('functions', []))
        
        complex_files.append({
            'file': file_path,
            'complexity': file_complexity,
            'loc': analysis.get('metrics', {}).get('lines_of_code', 0),
            'functions': len(analysis.get('functions', [])),
            'issues': len(analysis.get('issues', []))
        })
    
    # Sort by complexity and take top 10
    complex_files.sort(key=lambda x: x['complexity'], reverse=True)
    results['top_complex_files'] = complex_files[:10]
    
    # Find code duplications
    results['duplications'] = find_duplicated_code_simple(repo_path, python_files)
    
    # Generate improvement opportunities
    improvement_opportunities = {}
    
    # Add general recommendations
    general_recs = [
        "Use consistent code formatting throughout the codebase",
        "Add comprehensive docstrings to all public functions and classes",
        "Implement unit tests for critical functionality",
        "Remove unused imports and dead code"
    ]
    improvement_opportunities['General'] = general_recs
    
    # Add recommendations based on issues
    if results['files_with_issues']:
        code_quality_recs = []
        
        # Check for common issues
        issue_counts = defaultdict(int)
        for file_issue in results['files_with_issues']:
            for detail in file_issue['details']:
                for issue_type in ['long method', 'complex method', 'too many parameters', 
                                  'nested conditionals', 'commented code', 'magic numbers']:
                    if issue_type in detail.lower():
                        issue_counts[issue_type] += 1
        
        # Add specific recommendations based on issue prevalence
        if issue_counts.get('long method', 0) > 0:
            code_quality_recs.append(
                f"Refactor {issue_counts['long method']} long methods by extracting helper functions"
            )
        
        if issue_counts.get('complex method', 0) > 0:
            code_quality_recs.append(
                f"Simplify {issue_counts['complex method']} complex methods by reducing branching logic"
            )
        
        if issue_counts.get('nested conditionals', 0) > 0:
            code_quality_recs.append(
                f"Flatten nested conditionals in {issue_counts['nested conditionals']} locations using guard clauses or intermediate variables"
            )
        
        if issue_counts.get('commented code', 0) > 0:
            code_quality_recs.append(
                f"Remove or properly document {issue_counts['commented code']} instances of commented-out code"
            )
        
        improvement_opportunities['Code Quality'] = code_quality_recs
    
    # Add recommendations for complex files
    if results['top_complex_files']:
        refactoring_recs = [
            f"Split the {len(results['top_complex_files'])} most complex files into smaller, focused modules",
            "Apply the Single Responsibility Principle to large classes",
            "Use design patterns to improve code organization"
        ]
        improvement_opportunities['Refactoring'] = refactoring_recs
    
    # Add recommendations for code duplications
    if results['duplications']:
        duplication_recs = [
            f"Extract {len(results['duplications'])} duplicated code blocks into reusable functions or classes",
            "Implement a consistent utility module for common operations",
            "Use inheritance or composition to share common functionality between classes"
        ]
        improvement_opportunities['Code Duplication'] = duplication_recs
    
    results['improvement_opportunities'] = improvement_opportunities
    
    logger.info(f"Code review complete. Found {total_issues} issues across {len(results['files_with_issues'])} files.")
    return results