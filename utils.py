import os
import re
import logging
import tempfile
import json
import shutil
from pathlib import Path
import subprocess
from datetime import datetime

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
    
    # Ensure it's not too long
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:240] + ext
    
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
        
        count = 0
        in_multiline_comment = False
        
        for line in lines:
            line = line.strip()
            
            # Skip blank lines if requested
            if ignore_blank_lines and not line:
                continue
            
            # Handle multi-line comments
            if ignore_comments:
                # Check for multi-line comment start/end
                if '"""' in line or "'''" in line:
                    # Count single line doc strings
                    if line.count('"""') == 2 or line.count("'''") == 2:
                        continue
                    
                    in_multiline_comment = not in_multiline_comment
                    continue
                
                # Skip if inside multi-line comment
                if in_multiline_comment:
                    continue
                
                # Skip single-line comments
                if line.startswith('#'):
                    continue
            
            count += 1
        
        return count
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
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    language_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React JSX',
        '.tsx': 'React TSX',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.java': 'Java',
        '.cs': 'C#',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.go': 'Go',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C/C++ Header',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.m': 'Objective-C',
        '.sql': 'SQL',
        '.sh': 'Shell',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.json': 'JSON',
        '.md': 'Markdown',
        '.xml': 'XML',
        '.config': 'Config',
        '.toml': 'TOML',
        '.ini': 'INI'
    }
    
    return language_map.get(ext, 'unknown')

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
        if isinstance(command, str):
            command = command.split()
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, str(e)

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
        if output_dir is None:
            output_dir = tempfile.gettempdir()
        
        # Ensure directory exists
        create_directory_if_not_exists(output_dir)
        
        # Generate filename with timestamp
        filename = f"code_analysis_{generate_filename_timestamp()}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Save JSON file
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
        logger.error(f"Error loading analysis results: {str(e)}")
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
    
    kb = size_bytes / 1024
    if kb < 1024:
        return f"{kb:.2f} KB"
    
    mb = kb / 1024
    if mb < 1024:
        return f"{mb:.2f} MB"
    
    gb = mb / 1024
    return f"{gb:.2f} GB"

def estimate_complexity(file_path):
    """
    Estimate the complexity of a file based on language-agnostic metrics
    
    Parameters:
    - file_path: Path to the file
    
    Returns:
    - int: Estimated complexity score (0-10)
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Count lines
        lines = content.splitlines()
        line_count = len(lines)
        
        # Skip very small or empty files
        if line_count < 5:
            return 0
        
        # Calculate metrics
        avg_line_length = sum(len(line) for line in lines) / line_count
        
        # Count complex syntax components
        nested_blocks = content.count('{') + content.count('(') + content.count('[')
        control_structures = (
            content.count(' if ') + content.count(' for ') + 
            content.count(' while ') + content.count(' switch ') +
            content.count(' case ')
        )
        
        # Calculate complexity score
        score = 0
        
        # Score based on file size
        if line_count > 500:
            score += 3
        elif line_count > 200:
            score += 2
        elif line_count > 100:
            score += 1
        
        # Score based on average line length
        if avg_line_length > 100:
            score += 2
        elif avg_line_length > 60:
            score += 1
        
        # Score based on code structure
        structure_score = min(5, (nested_blocks + control_structures) / 20)
        score += structure_score
        
        return min(10, int(score))
    except Exception:
        return 0
