import os
import ast
import re
import logging
import pandas as pd
from collections import defaultdict
import subprocess
import sys
import tempfile
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of common code smells to look for
CODE_SMELLS = {
    'long_method': {'threshold': 50, 'description': 'Methods with too many lines'},
    'long_parameter_list': {'threshold': 5, 'description': 'Methods with too many parameters'},
    'duplicated_code': {'description': 'Similar code patterns repeated across files'},
    'large_class': {'threshold': 300, 'description': 'Classes with too many lines'},
    'complex_method': {'threshold': 10, 'description': 'Methods with high cyclomatic complexity'},
    'dead_code': {'description': 'Code that is never executed'},
    'commented_code': {'description': 'Commented out code blocks'},
    'magic_numbers': {'description': 'Hardcoded numeric literals'},
    'nested_conditionals': {'threshold': 3, 'description': 'Deeply nested if statements'},
    'global_variables': {'description': 'Overuse of global variables'}
}

class CodeVisitor(ast.NodeVisitor):
    """AST visitor for analyzing Python code"""
    
    def __init__(self):
        self.stats = {
            'functions': [],
            'classes': [],
            'imports': [],
            'complexity': 0,
            'lines': 0,
            'global_vars': [],
            'issues': []
        }
        self.current_class = None
        self.current_function = None
        
    def visit_ClassDef(self, node):
        """Process class definitions"""
        class_info = {
            'name': node.name,
            'line': node.lineno,
            'methods': [],
            'attributes': [],
            'size': self._count_lines(node)
        }
        
        prev_class = self.current_class
        self.current_class = class_info
        self.stats['classes'].append(class_info)
        
        # Check for large class
        if class_info['size'] > CODE_SMELLS['large_class']['threshold']:
            self.stats['issues'].append({
                'type': 'large_class',
                'message': f"Large class '{node.name}' with {class_info['size']} lines",
                'line': node.lineno
            })
        
        # Visit all nodes within the class
        self.generic_visit(node)
        
        self.current_class = prev_class
        
    def visit_FunctionDef(self, node):
        """Process function and method definitions"""
        # Determine if this is a method or standalone function
        is_method = self.current_class is not None
        
        func_info = {
            'name': node.name,
            'line': node.lineno,
            'params': len(node.args.args),
            'size': self._count_lines(node),
            'complexity': self._calculate_complexity(node),
            'is_method': is_method
        }
        
        prev_function = self.current_function
        self.current_function = func_info
        
        if is_method:
            self.current_class['methods'].append(func_info)
        else:
            self.stats['functions'].append(func_info)
        
        # Check for long parameter list
        if func_info['params'] > CODE_SMELLS['long_parameter_list']['threshold']:
            self.stats['issues'].append({
                'type': 'long_parameter_list',
                'message': f"Function/method '{node.name}' has {func_info['params']} parameters",
                'line': node.lineno
            })
        
        # Check for long method
        if func_info['size'] > CODE_SMELLS['long_method']['threshold']:
            self.stats['issues'].append({
                'type': 'long_method',
                'message': f"Long function/method '{node.name}' with {func_info['size']} lines",
                'line': node.lineno
            })
        
        # Check for complex method
        if func_info['complexity'] > CODE_SMELLS['complex_method']['threshold']:
            self.stats['issues'].append({
                'type': 'complex_method',
                'message': f"Complex function/method '{node.name}' with complexity {func_info['complexity']}",
                'line': node.lineno
            })
        
        # Visit all nodes within the function
        self.generic_visit(node)
        
        self.current_function = prev_function
    
    def visit_Import(self, node):
        """Process import statements"""
        for name in node.names:
            self.stats['imports'].append({
                'name': name.name,
                'line': node.lineno,
                'alias': name.asname
            })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Process from-import statements"""
        for name in node.names:
            self.stats['imports'].append({
                'name': f"{node.module}.{name.name}" if node.module else name.name,
                'line': node.lineno,
                'alias': name.asname
            })
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Process assignments to find global variables"""
        if self.current_function is None and self.current_class is None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.stats['global_vars'].append({
                        'name': target.id,
                        'line': node.lineno
                    })
        self.generic_visit(node)
    
    def visit_Num(self, node):
        """Process numeric literals to find magic numbers"""
        # Skip 0, 1, -1 as they're common and not usually considered magic numbers
        if not (node.n == 0 or node.n == 1 or node.n == -1):
            self.stats['issues'].append({
                'type': 'magic_number',
                'message': f"Magic number: {node.n}",
                'line': getattr(node, 'lineno', 0)
            })
        self.generic_visit(node)
    
    def visit_If(self, node):
        """Process if statements to detect nesting"""
        self._check_nesting_level(node, 1)
        self.generic_visit(node)
    
    def _check_nesting_level(self, node, current_level):
        """Recursively check nesting level of conditional statements"""
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.If):
                if current_level >= CODE_SMELLS['nested_conditionals']['threshold']:
                    self.stats['issues'].append({
                        'type': 'nested_conditionals',
                        'message': f"Deeply nested conditional (level {current_level + 1})",
                        'line': child.lineno
                    })
                self._check_nesting_level(child, current_level + 1)
    
    def _count_lines(self, node):
        """Count the number of lines in a node"""
        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
            return node.end_lineno - node.lineno + 1
        return 0
    
    def _calculate_complexity(self, node):
        """Calculate cyclomatic complexity of a function/method"""
        # Start with 1 for the function itself
        complexity = 1
        
        # Count branches that increase complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.BoolOp) and isinstance(child.op, (ast.And, ast.Or)):
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
        
        # Count total lines
        total_lines = len(content.splitlines())
        
        # Parse the AST
        tree = ast.parse(content, filename=file_path)
        
        # Visit nodes and collect stats
        visitor = CodeVisitor()
        visitor.visit(tree)
        visitor.stats['lines'] = total_lines
        
        # Look for commented code
        commented_code = find_commented_code(content)
        if commented_code:
            for line in commented_code:
                visitor.stats['issues'].append({
                    'type': 'commented_code',
                    'message': 'Commented out code block',
                    'line': line
                })
        
        return visitor.stats
    except Exception as e:
        logger.error(f"Error analyzing file {file_path}: {str(e)}")
        return {
            'error': str(e),
            'functions': [],
            'classes': [],
            'imports': [],
            'complexity': 0,
            'lines': 0,
            'global_vars': [],
            'issues': []
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
    comment_blocks = []
    in_block = False
    block_start = 0
    consecutive_comments = 0
    
    # Patterns that suggest code in comments
    code_patterns = [
        r'^\s*#\s*(def|class|import|from|if|for|while|return|print|with)',
        r'^\s*#\s*[a-zA-Z0-9_\.]+\s*=',
        r'^\s*#\s*[a-zA-Z0-9_\.]+\(',
    ]
    
    for i, line in enumerate(lines):
        if any(re.match(pattern, line) for pattern in code_patterns):
            if not in_block:
                in_block = True
                block_start = i + 1  # 1-based line numbers
            consecutive_comments += 1
        elif line.strip().startswith('#'):
            if in_block:
                consecutive_comments += 1
        else:
            if in_block and consecutive_comments >= 3:  # Consider 3+ consecutive code-like comments as a block
                comment_blocks.append(block_start)
            in_block = False
            consecutive_comments = 0
    
    # Check if the file ends with a comment block
    if in_block and consecutive_comments >= 3:
        comment_blocks.append(block_start)
    
    return comment_blocks

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
    
    # Skip binary files and very large files
    try:
        if os.path.getsize(full_path) > 1024 * 1024:  # Skip files larger than 1MB
            return None
    except Exception:
        return None
    
    # Python files
    if ext == '.py':
        return analyze_python_file(full_path)
    
    # For other file types, just return basic info for now
    return {
        'type': ext[1:] if ext else 'unknown',
        'size': os.path.getsize(full_path),
        'lines': count_file_lines(full_path)
    }

def count_file_lines(file_path):
    """Count the number of lines in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0

def find_duplicated_code(repo_path, file_paths):
    """
    Find potentially duplicated code across files
    
    Parameters:
    - repo_path: Path to the repository
    - file_paths: List of file paths to analyze
    
    Returns:
    - list: Potential code duplications
    """
    # Only analyze Python files for duplications
    python_files = [f for f in file_paths if f.endswith('.py')]
    
    if len(python_files) < 2:
        return []
    
    # Try to use external tools if available
    try:
        # Create a temporary file with the list of files to analyze
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            for file_path in python_files:
                temp_file.write(os.path.join(repo_path, file_path) + '\n')
            temp_file_path = temp_file.name
        
        # Try to use CPD from PMD if available
        try:
            result = subprocess.run(
                ['pmd', 'cpd', '--minimum-tokens', '100', '--files', temp_file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # Parse CPD output
                duplications = parse_cpd_output(result.stdout)
                return duplications
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        # Fallback to a simpler approach
        return find_duplicated_code_simple(repo_path, python_files)
    except Exception as e:
        logger.error(f"Error finding duplicated code: {str(e)}")
        return []
    finally:
        # Clean up temp file
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass

def parse_cpd_output(output):
    """Parse CPD output to extract duplication information"""
    duplications = []
    
    # Example pattern for CPD output
    pattern = r'Found a (\d+) token duplication in the following files:'
    
    for match in re.finditer(pattern, output):
        tokens = int(match.group(1))
        if tokens >= 100:  # Only consider significant duplications
            # Extract the file information
            end_pos = output.find('=====================================================================', match.end())
            if end_pos == -1:
                end_pos = len(output)
            
            duplication_text = output[match.end():end_pos].strip()
            
            # Extract files involved
            files_involved = []
            for line in duplication_text.splitlines():
                if 'Starting at line' in line:
                    file_match = re.match(r'(.+):Starting at line (\d+)', line.strip())
                    if file_match:
                        files_involved.append({
                            'file': file_match.group(1),
                            'line': int(file_match.group(2))
                        })
            
            if files_involved:
                duplications.append({
                    'tokens': tokens,
                    'files': files_involved
                })
    
    return duplications

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
    # Read all file contents
    file_contents = {}
    for file_path in file_paths:
        try:
            full_path = os.path.join(repo_path, file_path)
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = [line.strip() for line in f.readlines()]
                # Skip files with too few lines
                if len(lines) < min_lines:
                    continue
                file_contents[file_path] = lines
        except Exception:
            continue
    
    # Find potential duplications
    duplications = []
    
    # Generate chunks of consecutive lines
    file_chunks = {}
    for file_path, lines in file_contents.items():
        chunks = {}
        for i in range(len(lines) - min_lines + 1):
            chunk = '\n'.join(lines[i:i+min_lines])
            # Skip very short chunks or chunks with only whitespace/comments
            if len(chunk) < 50 or all(line.startswith('#') or not line for line in lines[i:i+min_lines]):
                continue
            if chunk not in chunks:
                chunks[chunk] = []
            chunks[chunk].append(i + 1)  # 1-based line numbers
        file_chunks[file_path] = chunks
    
    # Compare chunks across files
    processed_chunks = set()
    for file1, chunks1 in file_chunks.items():
        for file2, chunks2 in file_chunks.items():
            if file1 >= file2:  # Avoid comparing the same file pair twice
                continue
            
            # Find common chunks
            for chunk in set(chunks1.keys()) & set(chunks2.keys()):
                if chunk in processed_chunks:
                    continue
                
                processed_chunks.add(chunk)
                
                # Record the duplication
                duplications.append({
                    'files': [
                        {'file': file1, 'lines': chunks1[chunk]},
                        {'file': file2, 'lines': chunks2[chunk]}
                    ],
                    'size': min_lines,
                    'content': chunk[:100] + '...' if len(chunk) > 100 else chunk
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
        'files_with_issues': [],
        'improvement_opportunities': {},
        'top_complex_files': [],
        'duplications': []
    }
    
    # Find all files to analyze
    all_files = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            # Skip hidden files and directories
            if file.startswith('.') or '/.' in root:
                continue
                
            # Get the relative path
            rel_path = os.path.relpath(os.path.join(root, file), repo_path)
            all_files.append(rel_path)
    
    # Filter for relevant file types to analyze
    code_files = [f for f in all_files if any(f.endswith(ext) for ext in ['.py', '.js', '.java', '.ts', '.rb', '.go', '.c', '.cpp', '.cs'])]
    
    # Analyze each file
    file_stats = []
    total_issues = 0
    
    for file_path in code_files:
        try:
            file_analysis = analyze_file(repo_path, file_path)
            if file_analysis:
                file_stats.append({
                    'path': file_path,
                    'analysis': file_analysis
                })
                
                # Count issues
                issues = file_analysis.get('issues', [])
                if issues:
                    total_issues += len(issues)
                    results['files_with_issues'].append({
                        'file': file_path,
                        'issues': len(issues),
                        'details': [f"{issue['type']} (line {issue['line']}): {issue['message']}" 
                                   for issue in issues]
                    })
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {str(e)}")
    
    # Look for code duplications
    results['duplications'] = find_duplicated_code(repo_path, code_files)
    
    # Calculate overall metrics
    if file_stats:
        # Count total lines of code
        total_loc = sum(stat['analysis'].get('lines', 0) for stat in file_stats)
        
        # Count functions and classes
        total_functions = sum(len(stat['analysis'].get('functions', [])) for stat in file_stats)
        total_classes = sum(len(stat['analysis'].get('classes', [])) for stat in file_stats)
        
        # Calculate average complexity
        complexity_values = []
        for stat in file_stats:
            functions = stat['analysis'].get('functions', [])
            methods = []
            for cls in stat['analysis'].get('classes', []):
                methods.extend(cls.get('methods', []))
            
            for func in functions + methods:
                if 'complexity' in func:
                    complexity_values.append(func['complexity'])
        
        avg_complexity = sum(complexity_values) / len(complexity_values) if complexity_values else 0
        
        # Gather metrics
        results['metrics'] = {
            'Files Analyzed': len(file_stats),
            'Total Lines of Code': total_loc,
            'Total Functions': total_functions,
            'Total Classes': total_classes,
            'Average Complexity': round(avg_complexity, 2),
            'Total Issues': total_issues,
            'Issues per 1000 Lines': round((total_issues / total_loc) * 1000, 2) if total_loc else 0,
            'Code Duplications': len(results['duplications'])
        }
        
        # Identify top complex files
        file_complexity = []
        for stat in file_stats:
            path = stat['path']
            complexity = 0
            # Sum complexity of all functions and methods in the file
            for func in stat['analysis'].get('functions', []):
                complexity += func.get('complexity', 0)
            for cls in stat['analysis'].get('classes', []):
                for method in cls.get('methods', []):
                    complexity += method.get('complexity', 0)
            
            file_complexity.append({
                'file': path,
                'complexity': complexity,
                'loc': stat['analysis'].get('lines', 0)
            })
        
        # Sort by complexity and take top 10
        results['top_complex_files'] = sorted(
            file_complexity, 
            key=lambda x: x['complexity'], 
            reverse=True
        )[:10]
    
    # Generate improvement opportunities based on findings
    improvement_opportunities = defaultdict(list)
    
    # Check for duplicated code
    if results['duplications']:
        improvement_opportunities['Code Duplication'].append(
            f"Found {len(results['duplications'])} instances of duplicated code. Consider refactoring into reusable functions/modules."
        )
    
    # Check for complex files
    complex_files = [f for f in results.get('top_complex_files', []) 
                    if f['complexity'] > 50]  # Arbitrary threshold
    if complex_files:
        improvement_opportunities['Code Complexity'].append(
            f"Found {len(complex_files)} files with high complexity. Consider breaking down large functions and classes."
        )
    
    # Check for files with many issues
    problem_files = [f for f in results.get('files_with_issues', []) 
                    if f['issues'] > 5]  # Arbitrary threshold
    if problem_files:
        improvement_opportunities['Code Quality'].append(
            f"Found {len(problem_files)} files with significant quality issues. Address code smells and follow best practices."
        )
    
    # Add general recommendations based on found issues
    issue_types = set()
    for file_issue in results.get('files_with_issues', []):
        for detail in file_issue.get('details', []):
            for smell in CODE_SMELLS:
                if smell in detail:
                    issue_types.add(smell)
    
    if 'long_method' in issue_types:
        improvement_opportunities['Code Structure'].append(
            "Several long methods detected. Extract functionality into smaller, focused methods."
        )
    
    if 'long_parameter_list' in issue_types:
        improvement_opportunities['Code Design'].append(
            "Methods with many parameters found. Consider using parameter objects or restructuring."
        )
    
    if 'large_class' in issue_types:
        improvement_opportunities['Code Organization'].append(
            "Large classes detected. Split into smaller, more focused classes following single responsibility principle."
        )
    
    if 'complex_method' in issue_types:
        improvement_opportunities['Code Complexity'].append(
            "Complex methods found. Simplify logic, extract helper methods, and reduce nested conditionals."
        )
    
    if 'nested_conditionals' in issue_types:
        improvement_opportunities['Code Readability'].append(
            "Deeply nested conditionals detected. Use guard clauses, extract methods, or simplify logic."
        )
    
    if 'commented_code' in issue_types:
        improvement_opportunities['Code Cleanliness'].append(
            "Found commented-out code blocks. Remove unused code to improve maintenance."
        )
    
    if 'magic_numbers' in issue_types:
        improvement_opportunities['Code Maintainability'].append(
            "Magic numbers detected. Replace with named constants for better readability and maintenance."
        )
    
    # Add general recommendations if we don't have many specific ones
    if len(improvement_opportunities) < 3:
        improvement_opportunities['Documentation'].append(
            "Improve inline documentation and comments to explain complex logic and business rules."
        )
        improvement_opportunities['Testing'].append(
            "Increase test coverage, especially for complex components and critical business logic."
        )
        improvement_opportunities['Naming Conventions'].append(
            "Ensure consistent naming conventions for variables, functions, and classes."
        )
    
    results['improvement_opportunities'] = dict(improvement_opportunities)
    
    logger.info(f"Code review complete. Found {total_issues} issues across {len(file_stats)} files.")
    return results
