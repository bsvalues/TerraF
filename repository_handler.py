import os
import git
import tempfile
import shutil
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clone_repository(repo_url, branch='main', temp_dir=None):
    """
    Clone a GitHub repository to a temporary directory
    
    Parameters:
    - repo_url: URL of the GitHub repository
    - branch: Branch to clone (default: main)
    - temp_dir: Directory to clone into (if None, creates a new temp dir)
    
    Returns:
    - str: Path to the cloned repository
    """
    try:
        if not temp_dir:
            temp_dir = tempfile.mkdtemp()
            
        # Extract repository name from URL for the folder name
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_path = os.path.join(temp_dir, repo_name)
        
        # Clone the repository
        logger.info(f"Cloning repository {repo_url} to {repo_path}...")
        git.Repo.clone_from(repo_url, repo_path, branch=branch)
        
        logger.info(f"Repository cloned successfully to {repo_path}")
        return repo_path
    except git.GitCommandError as e:
        logger.error(f"Git command error: {str(e)}")
        raise Exception(f"Failed to clone repository: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise Exception(f"An unexpected error occurred: {str(e)}")

def get_repository_structure(repo_path):
    """
    Analyze the structure of a repository
    
    Parameters:
    - repo_path: Path to the cloned repository
    
    Returns:
    - dict: Repository structure information including file types, directories, etc.
    """
    try:
        logger.info(f"Analyzing repository structure at {repo_path}...")
        
        # Initialize structure information
        structure = {
            'file_count': 0,
            'directory_count': 0,
            'file_types': {},
            'top_level_dirs': [],
            'file_paths': [],
            'largest_files': [],
            'deepest_nesting': 0
        }
        
        # Skip hidden files and directories
        def should_skip(path):
            parts = path.split(os.sep)
            return any(part.startswith('.') for part in parts if part)
        
        # Walk through the repository
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories like .git
            if should_skip(os.path.relpath(root, repo_path)):
                continue
                
            # Calculate relative path from repo root
            rel_path = os.path.relpath(root, repo_path)
            
            # Count directories
            if rel_path != '.':
                structure['directory_count'] += 1
                
                # Track top-level directories
                if os.path.dirname(rel_path) == '':
                    structure['top_level_dirs'].append(rel_path)
            
            # Calculate nesting level
            nesting_level = len(Path(rel_path).parts)
            structure['deepest_nesting'] = max(structure['deepest_nesting'], nesting_level)
            
            # Process files
            for file in files:
                # Skip hidden files
                if file.startswith('.'):
                    continue
                    
                full_path = os.path.join(root, file)
                rel_file_path = os.path.relpath(full_path, repo_path)
                
                # Count file
                structure['file_count'] += 1
                
                # Track file path
                structure['file_paths'].append(rel_file_path)
                
                # Categorize by file extension
                _, ext = os.path.splitext(file)
                ext = ext.lower()
                if ext:
                    structure['file_types'][ext] = structure['file_types'].get(ext, 0) + 1
                else:
                    structure['file_types']['no_extension'] = structure['file_types'].get('no_extension', 0) + 1
                
                # Track largest files
                try:
                    file_size = os.path.getsize(full_path)
                    structure['largest_files'].append({
                        'path': rel_file_path,
                        'size': file_size
                    })
                except Exception:
                    pass
        
        # Sort and limit largest files list
        structure['largest_files'] = sorted(
            structure['largest_files'], 
            key=lambda x: x['size'], 
            reverse=True
        )[:10]
        
        # Convert file types to sorted list for better display
        structure['file_types'] = [
            {'extension': ext, 'count': count}
            for ext, count in sorted(structure['file_types'].items(), key=lambda x: x[1], reverse=True)
        ]
        
        logger.info(f"Repository structure analysis complete. Found {structure['file_count']} files.")
        return structure
    except Exception as e:
        logger.error(f"Error analyzing repository structure: {str(e)}")
        raise Exception(f"Failed to analyze repository structure: {str(e)}")
    
def get_file_content(repo_path, file_path):
    """
    Read the content of a file in the repository
    
    Parameters:
    - repo_path: Path to the cloned repository
    - file_path: Relative path to the file within the repository
    
    Returns:
    - str: Content of the file
    """
    try:
        full_path = os.path.join(repo_path, file_path)
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return None
