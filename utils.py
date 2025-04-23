import os
import re
import json
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sanitize_filename(filename):
    """
    Sanitize a filename to ensure it's valid across operating systems
    
    Parameters:
    - filename: The filename to sanitize
    
    Returns:
    - str: Sanitized filename
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
    
    # Ensure the filename is not too long (max 255 characters including extension)
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255 - len(ext)] + ext
    
    return sanitized

def create_directory_if_not_exists(directory):
    """
    Create a directory if it doesn't already exist
    
    Parameters:
    - directory: Directory path to create
    
    Returns:
    - bool: True if directory was created or already exists
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {str(e)}")
        return False

def count_lines_of_code(file_path, ignore_comments=True, ignore_blank_lines=True):
    """
    Count lines of code in a file
    
    Parameters:
    - file_path: Path to the file
    - ignore_comments: Whether to ignore comment lines
    - ignore_blank_lines: Whether to ignore blank lines
    
    Returns:
    - int: Number of lines of code
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        line_count = 0
        in_multiline_comment = False
        
        for line in lines:
            line = line.strip()
            
            # Skip blank lines if requested
            if ignore_blank_lines and not line:
                continue
            
            # Handle Python comments
            if file_path.endswith('.py'):
                # Check for multiline comments
                if '"""' in line or "'''" in line:
                    # Toggle multiline comment state
                    if line.count('"""') % 2 == 1 or line.count("'''") % 2 == 1:
                        in_multiline_comment = not in_multiline_comment
                    
                    # If the line is just a comment delimiter, skip it
                    if line.strip('\'"\t ') == '':
                        continue
                
                # Skip comment lines and lines in multiline comments if requested
                if ignore_comments and (in_multiline_comment or line.startswith('#')):
                    continue
            
            # Increment line count for valid lines
            line_count += 1
        
        return line_count
    except Exception as e:
        logger.error(f"Error counting lines in {file_path}: {str(e)}")
        return 0

def detect_programming_language(file_path):
    """
    Detect the programming language of a file based on its extension
    
    Parameters:
    - file_path: Path to the file
    
    Returns:
    - str: Detected language or 'unknown'
    """
    extension_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React',
        '.tsx': 'React TypeScript',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.less': 'Less',
        '.java': 'Java',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C/C++ Header',
        '.cs': 'C#',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.go': 'Go',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.sql': 'SQL',
        '.md': 'Markdown',
        '.json': 'JSON',
        '.xml': 'XML',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.toml': 'TOML'
    }
    
    _, ext = os.path.splitext(file_path.lower())
    return extension_map.get(ext, 'unknown')

def generate_filename_timestamp():
    """
    Generate a timestamp for use in filenames
    
    Returns:
    - str: Current timestamp formatted for filenames
    """
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def run_command(command, timeout=30):
    """
    Run a shell command with timeout
    
    Parameters:
    - command: Command to run (list or string)
    - timeout: Timeout in seconds
    
    Returns:
    - tuple: (success, output/error)
    """
    try:
        # Convert string command to list if needed
        if isinstance(command, str):
            command = command.split()
        
        # Run the command with timeout
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        
        # Check if the command was successful
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, f"Error running command: {str(e)}"

def save_analysis_results(results, output_dir=None):
    """
    Save analysis results to a JSON file
    
    Parameters:
    - results: Analysis results to save
    - output_dir: Directory to save to (default: temp directory)
    
    Returns:
    - str: Path to saved file or None if failed
    """
    try:
        # Create output directory if not provided
        if not output_dir:
            output_dir = tempfile.gettempdir()
        
        # Ensure the directory exists
        create_directory_if_not_exists(output_dir)
        
        # Generate filename with timestamp
        timestamp = generate_filename_timestamp()
        filename = f"analysis_results_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Save results to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Analysis results saved to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error saving analysis results: {str(e)}")
        return None

def load_analysis_results(filepath):
    """
    Load analysis results from a JSON file
    
    Parameters:
    - filepath: Path to the JSON file
    
    Returns:
    - dict: Loaded analysis results or None if failed
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        logger.info(f"Analysis results loaded from {filepath}")
        return results
    except Exception as e:
        logger.error(f"Error loading analysis results from {filepath}: {str(e)}")
        return None

def format_file_size(size_bytes):
    """
    Format file size in human-readable format
    
    Parameters:
    - size_bytes: Size in bytes
    
    Returns:
    - str: Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def estimate_complexity(file_path):
    """
    Estimate the complexity of a file based on language-agnostic metrics
    
    Parameters:
    - file_path: Path to the file
    
    Returns:
    - int: Estimated complexity score (0-10)
    """
    try:
        # Count lines of code
        loc = count_lines_of_code(file_path)
        
        # Basic complexity formula based on file size
        # Scale logarithmically to prevent large files from dominating
        if loc == 0:
            return 0
        
        base_complexity = min(5, 1 + int(2 * (loc / 300)))  # Files over 300 lines get base complexity of 3
        
        # Add language-specific complexity factors
        lang = detect_programming_language(file_path)
        lang_factor = {
            'Python': 1.0,        # Baseline
            'JavaScript': 1.1,    # Slightly more complex due to async/callbacks
            'TypeScript': 0.9,    # Type safety reduces complexity
            'Java': 1.2,          # More verbose, often more complex
            'C++': 1.3,           # Memory management adds complexity
            'C': 1.4,             # Low-level constructs add complexity
            'Ruby': 1.0,
            'Go': 0.9,
            'Rust': 1.1,
            'SQL': 0.8,
            'HTML': 0.5,
            'CSS': 0.6,
            'JSON': 0.3,
            'YAML': 0.4,
            'Markdown': 0.2
        }.get(lang, 1.0)
        
        # Check for complex patterns in the file
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        pattern_scores = 0
        patterns = {
            r'if\s*\(.+&&.+\)': 0.2,                # Complex conditionals
            r'if\s*\(.+\|\|.+\)': 0.2,
            r'for\s*\(.+;.+;.+\)': 0.3,             # Traditional for loops (common in C-like languages)
            r'while\s*\(': 0.2,                     # While loops
            r'switch\s*\(': 0.2,                    # Switch statements
            r'try\s*\{.+\}\s*catch': 0.3,           # Try-catch blocks
            r'function\s*\w+\s*\([^)]{40,}\)': 0.5, # Functions with many parameters
            r'class\s+\w+\s+extends': 0.2,          # Class inheritance
            r'new\s+\w+\(': 0.1,                    # Object instantiation
            r'async\s+function': 0.2,               # Async functions
            r'await\s+': 0.1,                       # Await expressions
            r'setTimeout\s*\(': 0.2,                # Timeouts (common in JS)
            r'setInterval\s*\(': 0.2,               # Intervals (common in JS)
            r'addEventListener\s*\(': 0.1,          # Event listeners (common in JS)
            r'document\.querySelector': 0.1,        # DOM manipulation (common in JS)
            r'import\s+\{.+\}\s+from': 0.1,         # ES6 imports
            r'export\s+': 0.1,                      # ES6 exports
            r'\$\(.+\)': 0.2,                       # jQuery selectors
            r'@\w+': 0.2,                           # Decorators (common in Python)
            r'def\s+__\w+__': 0.3,                  # Magic methods (common in Python)
            r'lambda\s+': 0.2,                      # Lambda expressions
            r'yield\s+': 0.2,                       # Generators
            r'SELECT.+FROM.+WHERE': 0.3,            # SQL queries
            r'JOIN.+ON': 0.3,                       # SQL joins
            r'<\?php': 0.1,                         # PHP code
            r'\[.*:.*\]': 0.1,                      # List slices (common in Python)
            r'\*args': 0.2,                         # Variable arguments (common in Python)
            r'\*\*kwargs': 0.2,                     # Variable keyword arguments (common in Python)
            r'@abstractmethod': 0.3,                # Abstract methods (common in Python)
            r'@staticmethod': 0.1,                  # Static methods (common in Python)
            r'@classmethod': 0.1,                   # Class methods (common in Python)
            r'@property': 0.1,                      # Properties (common in Python)
            r'#pragma': 0.3,                        # Compiler directives (common in C/C++)
            r'#include': 0.1,                       # Include directives (common in C/C++)
            r'#define': 0.2,                        # Define directives (common in C/C++)
            r'typedef': 0.2,                        # Type definitions (common in C/C++)
            r'template\s*<': 0.3,                   # Templates (common in C++)
            r'enum\s+': 0.1,                        # Enumerations
            r'struct\s+': 0.1,                      # Structures
            r'union\s+': 0.2,                       # Unions
            r'goto\s+': 0.5,                        # Goto statements (penalized for complexity)
            r'throw\s+': 0.2,                       # Exception throwing
            r'synchronized\s*\(': 0.3,              # Synchronized blocks (common in Java)
            r'volatile': 0.3,                       # Volatile variables (common in C/C++/Java)
            r'mutable': 0.3,                        # Mutable variables (common in C++)
            r'const\s+': 0.1,                       # Const variables
            r'static\s+': 0.1,                      # Static variables/methods
            r'virtual\s+': 0.2,                     # Virtual methods (common in C++)
            r'override\s+': 0.1,                    # Override methods (common in C#/Swift)
            r'inline\s+': 0.1,                      # Inline functions (common in C++)
            r'friend\s+': 0.3,                      # Friend declarations (common in C++)
            r'namespace\s+': 0.1                    # Namespaces (common in C++)
        }
        
        for pattern, score in patterns.items():
            if re.search(pattern, content):
                pattern_scores += score
        
        # Calculate final complexity score
        complexity = base_complexity * lang_factor + min(5, pattern_scores)
        
        # Return score rounded to nearest integer and capped at 10
        return min(10, round(complexity))
    except Exception as e:
        logger.error(f"Error estimating complexity for {file_path}: {str(e)}")
        return 0