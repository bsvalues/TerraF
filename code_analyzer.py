import os
import ast
import re
import logging
from pathlib import Path
from collections import defaultdict
from utils import count_lines_of_code, estimate_complexity

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeVisitor(ast.NodeVisitor):
    """AST visitor for analyzing Python code"""
    
    def __init__(self):
        self.classes = []
        self.functions = []
        self.imports = []
        self.global_vars = []
        self.issues = []
        self.magic_numbers = []
        self.nested_blocks = []
        
        # Track node hierarchy
        self.parent_stack = []
        
        # Track current context
        self.current_class = None
        self.current_function = None
    
    def visit_ClassDef(self, node):
        """Process class definitions"""
        # Store class info
        class_info = {
            'name': node.name,
            'line': node.lineno,
            'methods': [],
            'class_vars': [],
            'bases': [base.id if hasattr(base, 'id') else 'unknown' for base in node.bases]
        }
        self.classes.append(class_info)
        
        # Set current class context
        prev_class = self.current_class
        self.current_class = class_info
        
        # Visit children
        self.generic_visit(node)
        
        # Restore previous context
        self.current_class = prev_class
    
    def visit_FunctionDef(self, node):
        """Process function and method definitions"""
        # Calculate function complexity
        complexity = self._calculate_complexity(node)
        
        # Count parameters
        params = [arg.arg for arg in node.args.args]
        
        # Store function info
        func_info = {
            'name': node.name,
            'line': node.lineno,
            'complexity': complexity,
            'parameters': params,
            'loc': self._count_lines(node)
        }
        
        # Check if it's a method or a function
        if self.current_class:
            self.current_class['methods'].append(func_info)
        else:
            self.functions.append(func_info)
        
        # Check for long parameter lists (more than 5 parameters)
        if len(params) > 5:
            self.issues.append({
                'type': 'long_parameter_list',
                'detail': f"Function '{node.name}' has a long parameter list ({len(params)} parameters)",
                'line': node.lineno
            })
        
        # Check for long functions (more than 50 lines)
        lines = self._count_lines(node)
        if lines > 50:
            self.issues.append({
                'type': 'long_method',
                'detail': f"Function '{node.name}' is too long ({lines} lines)",
                'line': node.lineno
            })
        
        # Check for complex functions (complexity > 10)
        if complexity > 10:
            self.issues.append({
                'type': 'complex_method',
                'detail': f"Function '{node.name}' is too complex (complexity: {complexity})",
                'line': node.lineno
            })
        
        # Set current function context
        prev_function = self.current_function
        self.current_function = func_info
        
        # Remember the parent node for child nodes
        self.parent_stack.append(node)
        
        # Visit children
        self.generic_visit(node)
        
        # Restore previous context
        self.current_function = prev_function
        self.parent_stack.pop()
    
    def visit_Import(self, node):
        """Process import statements"""
        for alias in node.names:
            self.imports.append({
                'module': alias.name,
                'alias': alias.asname,
                'line': node.lineno,
                'type': 'import'
            })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Process from-import statements"""
        for alias in node.names:
            self.imports.append({
                'module': node.module,
                'name': alias.name,
                'alias': alias.asname,
                'line': node.lineno,
                'type': 'from_import'
            })
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Process assignments to find global variables"""
        # Add a parent reference (not part of the standard AST)
        node.parent_node = self.parent_stack[-1] if self.parent_stack else None
        
        # Check if it's a class variable or a global variable
        if self.current_class and not self.current_function:
            for target in node.targets:
                if hasattr(target, 'id'):
                    self.current_class['class_vars'].append({
                        'name': target.id,
                        'line': node.lineno
                    })
        elif not self.current_function and not self.current_class:
            for target in node.targets:
                if hasattr(target, 'id'):
                    self.global_vars.append({
                        'name': target.id,
                        'line': node.lineno
                    })
        
        self.generic_visit(node)
    
    def visit_Constant(self, node):
        """Process numeric literals to find magic numbers"""
        # Add a parent reference
        node.parent_node = self.parent_stack[-1] if self.parent_stack else None
        
        if isinstance(node.value, (int, float)):
            # Skip common numbers like 0, 1, -1
            if node.value not in [0, 1, -1, 2, 10, 100]:
                self.magic_numbers.append({
                    'value': node.value,
                    'line': getattr(node, 'lineno', 0)
                })
        
        self.generic_visit(node)
    
    def visit_Num(self, node):
        """Process numeric literals to find magic numbers (legacy)"""
        # Add a parent reference
        node.parent_node = self.parent_stack[-1] if self.parent_stack else None
        
        # Skip common numbers like 0, 1, -1
        if node.n not in [0, 1, -1, 2, 10, 100]:
            self.magic_numbers.append({
                'value': node.n,
                'line': getattr(node, 'lineno', 0)
            })
        
        self.generic_visit(node)
    
    def visit_If(self, node):
        """Process if statements to detect nesting"""
        # Check nesting level recursively
        nesting_level = self._check_nesting_level(node, 1)
        if nesting_level > 3:
            self.nested_blocks.append({
                'type': 'nested_conditional',
                'level': nesting_level,
                'line': node.lineno,
                'detail': f"Nested conditional statements (depth: {nesting_level})"
            })
            
            # Add to issues as well
            self.issues.append({
                'type': 'nested_conditional',
                'detail': f"Nested conditional statements (depth: {nesting_level})",
                'line': node.lineno
            })
        
        # Remember the parent node for child nodes
        self.parent_stack.append(node)
        
        # Visit children
        self.generic_visit(node)
        
        # Restore previous context
        self.parent_stack.pop()
    
    def _check_nesting_level(self, node, current_level):
        """Recursively check nesting level of conditional statements"""
        max_level = current_level
        
        # Check if and elif blocks
        for child_node in ast.iter_child_nodes(node):
            if isinstance(child_node, ast.If):
                # Add parent reference to help with navigation later
                child_node.parent_node = node
                
                # Recurse to find the deepest nesting
                child_level = self._check_nesting_level(child_node, current_level + 1)
                max_level = max(max_level, child_level)
        
        return max_level
    
    def _count_lines(self, node):
        """Count the number of lines in a node"""
        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
            return node.end_lineno - node.lineno + 1
        return 0
    
    def _calculate_complexity(self, node):
        """Calculate cyclomatic complexity of a function/method"""
        # Start with a base complexity of 1
        complexity = 1
        
        # Increment complexity for each branching statement
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.BoolOp) and isinstance(child.op, ast.And):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.BoolOp) and isinstance(child.op, ast.Or):
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
        
        # Visit nodes and collect information
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        # Count lines of code
        loc = count_lines_of_code(file_path)
        
        # Find commented code blocks
        commented_code = find_commented_code(content)
        
        # Calculate overall complexity based on various factors
        if len(visitor.functions) > 0:
            avg_func_complexity = sum(f.get('complexity', 0) for f in visitor.functions) / len(visitor.functions)
        else:
            avg_func_complexity = 0
        
        complexity_factors = [
            len(visitor.nested_blocks) * 0.5,
            len(visitor.magic_numbers) * 0.1,
            avg_func_complexity,
            len(visitor.issues) * 0.3
        ]
        
        overall_complexity = min(10, round(sum(complexity_factors)))
        
        # Create result dictionary
        result = {
            'classes': visitor.classes,
            'functions': visitor.functions,
            'imports': visitor.imports,
            'global_vars': visitor.global_vars,
            'issues': visitor.issues,
            'magic_numbers': visitor.magic_numbers,
            'nested_blocks': visitor.nested_blocks,
            'commented_code': commented_code,
            'loc': loc,
            'complexity': overall_complexity
        }
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing Python file {file_path}: {str(e)}")
        return {
            'classes': [],
            'functions': [],
            'imports': [],
            'global_vars': [],
            'issues': [{'type': 'error', 'detail': f"Error analyzing file: {str(e)}", 'line': 0}],
            'magic_numbers': [],
            'nested_blocks': [],
            'commented_code': [],
            'loc': 0,
            'complexity': 0
        }

def find_commented_code(content):
    """
    Detect blocks of commented code
    
    Parameters:
    - content: File content as string
    
    Returns:
    - list: Line numbers where commented code blocks start
    """
    commented_code = []
    lines = content.splitlines()
    
    comment_block_start = None
    consecutive_comments = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if line.startswith('#') and len(line) > 1:
            # Skip comment lines that are likely documentation
            if any(doc_starter in line.lower() for doc_starter in 
                   ['todo', 'hack', 'fixme', 'note', 'description', 'param', 'return']):
                continue
                
            # Check if this line looks like code
            code_line = line[1:].strip()
            if (
                re.match(r'(def|class|if|for|while|try|except|with|return|import|from)\s', code_line) or
                re.match(r'[a-zA-Z_][a-zA-Z0-9_]*\s*[=+-/*]', code_line) or
                code_line.endswith(':')
            ):
                if comment_block_start is None:
                    comment_block_start = i + 1  # Line numbers are 1-based
                consecutive_comments += 1
        else:
            # Reset if we've seen enough consecutive comments to call it a block
            if consecutive_comments >= 3:
                commented_code.append({
                    'line': comment_block_start,
                    'count': consecutive_comments
                })
            comment_block_start = None
            consecutive_comments = 0
    
    # Check if the file ends with a comment block
    if consecutive_comments >= 3:
        commented_code.append({
            'line': comment_block_start,
            'count': consecutive_comments
        })
    
    return commented_code

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
    
    # Check file extension
    _, ext = os.path.splitext(file_path.lower())
    
    if ext == '.py':
        # Analyze Python file using AST
        return analyze_python_file(full_path)
    else:
        # For other file types, just count lines and estimate complexity
        return {
            'loc': count_lines_of_code(full_path),
            'complexity': estimate_complexity(full_path),
            'issues': []
        }

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
    logger.info("Looking for duplicated code...")
    
    # Store file content as lines
    files_content = {}
    for file_path in file_paths:
        try:
            full_path = os.path.join(repo_path, file_path)
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            files_content[file_path] = content.splitlines()
        except Exception:
            pass
    
    # Look for duplicate blocks
    duplications = []
    
    # Dictionary to store blocks of code and their origins
    block_origins = {}
    
    # Process each file
    for file_path, lines in files_content.items():
        for i in range(len(lines) - min_lines + 1):
            # Create a block of min_lines consecutive lines
            block = '\n'.join(lines[i:i+min_lines])
            
            # Skip empty blocks or blocks with just whitespace
            if not block.strip():
                continue
                
            # Check if we've seen this block before
            if block in block_origins:
                # Found a duplication
                orig_file, orig_line = block_origins[block]
                
                # Avoid reporting duplications within the same file
                if orig_file != file_path:
                    duplications.append({
                        'file1': orig_file,
                        'start_line1': orig_line,
                        'file2': file_path,
                        'start_line2': i + 1,
                        'lines': min_lines
                    })
            else:
                # Record this block
                block_origins[block] = (file_path, i + 1)
    
    logger.info(f"Found {len(duplications)} potential code duplications")
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
        'files_analyzed': [],
        'issues': [],
        'files_with_issues': [],
        'top_complex_files': [],
        'metrics': {
            'total_loc': 0,
            'total_classes': 0,
            'total_functions': 0,
            'average_complexity': 0
        },
        'improvement_opportunities': {},
        'duplications': []
    }
    
    # Find Python files
    python_files = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            # Skip files in hidden directories
            rel_path = os.path.relpath(root, repo_path)
            if any(part.startswith('.') for part in Path(rel_path).parts):
                continue
                
            if file.endswith('.py'):
                python_files.append(os.path.join(rel_path, file))
    
    # Analyze each Python file
    total_complexity = 0
    analyzed_count = 0
    
    for file_path in python_files:
        analysis = analyze_file(repo_path, file_path)
        if analysis:
            # Count lines and complexity
            results['metrics']['total_loc'] += analysis.get('loc', 0)
            results['metrics']['total_classes'] += len(analysis.get('classes', []))
            results['metrics']['total_functions'] += len(analysis.get('functions', []))
            file_complexity = analysis.get('complexity', 0)
            total_complexity += file_complexity
            analyzed_count += 1
            
            # Track issues
            file_issues = analysis.get('issues', [])
            if file_issues:
                results['files_with_issues'].append({
                    'file': file_path,
                    'issue_count': len(file_issues),
                    'details': [issue.get('detail', '') for issue in file_issues]
                })
                
                # Group issues by type
                for issue in file_issues:
                    issue_with_file = issue.copy()
                    issue_with_file['file'] = file_path
                    results['issues'].append(issue_with_file)
            
            # Track complex files
            results['top_complex_files'].append({
                'file': file_path,
                'complexity': file_complexity,
                'loc': analysis.get('loc', 0)
            })
            
            # Record analyzed file
            results['files_analyzed'].append(file_path)
    
    # Sort complex files by complexity
    results['top_complex_files'] = sorted(
        results['top_complex_files'], 
        key=lambda x: x['complexity'], 
        reverse=True
    )[:10]  # Keep only top 10
    
    # Calculate average complexity
    if analyzed_count > 0:
        results['metrics']['average_complexity'] = total_complexity / analyzed_count
    
    # Calculate issue density (issues per 1000 lines of code)
    if results['metrics']['total_loc'] > 0:
        issue_density = len(results['issues']) * 1000 / results['metrics']['total_loc']
        results['metrics']['issue_density'] = issue_density
    else:
        results['metrics']['issue_density'] = 0
    
    # Generate improvement opportunities
    results['improvement_opportunities'] = {
        'Code Quality': [
            "Enforce consistent coding standards with a linter like flake8 or pylint",
            "Add docstrings to all public classes and functions",
            "Break down complex functions into smaller, more focused ones",
            "Reduce nesting by extracting conditions into helper functions"
        ],
        'Testing': [
            "Increase test coverage for complex modules",
            "Implement integration tests for critical component interactions",
            "Add property-based testing for data transformation functions",
            "Use mock objects to test components in isolation"
        ],
        'Architecture': [
            "Apply the Single Responsibility Principle to large classes",
            "Introduce design patterns for recurring problems",
            "Consider using dependency injection for better testability",
            "Implement proper error handling throughout the codebase"
        ]
    }
    
    # Find duplicated code
    results['duplications'] = find_duplicated_code_simple(repo_path, python_files)
    
    logger.info(f"Code review complete. Analyzed {len(results['files_analyzed'])} files.")
    return results