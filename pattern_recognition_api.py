"""
Pattern Recognition API

This module provides a simple API interface for programmatic access to the
pattern recognition capabilities of the TerraFusion platform.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import pattern recognizer
try:
    from code_pattern_recognizer import CodePatternRecognizer
    PATTERN_RECOGNIZER_AVAILABLE = True
except ImportError as e:
    logger.error(f"Pattern recognizer not available: {str(e)}")
    PATTERN_RECOGNIZER_AVAILABLE = False

class PatternRecognitionAPI:
    """
    API interface for pattern recognition capabilities
    """
    def __init__(self):
        """Initialize the API"""
        self.recognizer = None
        self.cache_dir = "pattern_recognition_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def analyze_repository(self, repo_path: str, file_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze a repository for code patterns
        
        Args:
            repo_path: Path to the repository root
            file_paths: Optional list of specific files to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        if not PATTERN_RECOGNIZER_AVAILABLE:
            logger.error("Pattern recognizer not available")
            return {"error": "Pattern recognizer not available"}
        
        # Initialize recognizer if needed
        if self.recognizer is None or self.recognizer.repo_path != repo_path:
            self.recognizer = CodePatternRecognizer(repo_path)
        
        # Run analysis
        try:
            results = self.recognizer.analyze_repository(file_paths)
            
            # Cache results
            cache_path = os.path.join(self.cache_dir, f"{os.path.basename(repo_path)}_analysis.json")
            with open(cache_path, 'w') as f:
                json.dump(results, f, default=str)
            
            return results
        except Exception as e:
            logger.error(f"Error analyzing repository: {str(e)}")
            return {"error": str(e)}
    
    def get_patterns(self, repo_path: str, pattern_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get patterns from a repository
        
        Args:
            repo_path: Path to the repository root
            pattern_type: Optional pattern type filter (design_patterns, anti_patterns, etc.)
            
        Returns:
            Dictionary containing patterns
        """
        cache_path = os.path.join(self.cache_dir, f"{os.path.basename(repo_path)}_analysis.json")
        
        # Check if cached results exist
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    results = json.load(f)
                
                if 'patterns' not in results:
                    return {"error": "No patterns found in cached results"}
                
                # Filter by pattern type if specified
                if pattern_type:
                    if pattern_type in results['patterns']:
                        return {pattern_type: results['patterns'][pattern_type]}
                    else:
                        return {pattern_type: []}
                else:
                    return {"patterns": results['patterns']}
            except Exception as e:
                logger.error(f"Error loading cached results: {str(e)}")
        
        # If no cached results or error, run analysis
        return self.analyze_repository(repo_path)
    
    def get_anomalies(self, repo_path: str) -> Dict[str, Any]:
        """
        Get code anomalies from a repository
        
        Args:
            repo_path: Path to the repository root
            
        Returns:
            Dictionary containing anomalies
        """
        cache_path = os.path.join(self.cache_dir, f"{os.path.basename(repo_path)}_analysis.json")
        
        # Check if cached results exist
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    results = json.load(f)
                
                if 'anomalies' not in results:
                    return {"error": "No anomalies found in cached results"}
                
                return {"anomalies": results['anomalies']}
            except Exception as e:
                logger.error(f"Error loading cached results: {str(e)}")
        
        # If no cached results or error, run analysis
        return self.analyze_repository(repo_path)
    
    def get_clusters(self, repo_path: str) -> Dict[str, Any]:
        """
        Get code clusters from a repository
        
        Args:
            repo_path: Path to the repository root
            
        Returns:
            Dictionary containing clusters
        """
        cache_path = os.path.join(self.cache_dir, f"{os.path.basename(repo_path)}_analysis.json")
        
        # Check if cached results exist
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    results = json.load(f)
                
                if 'clusters' not in results:
                    return {"error": "No clusters found in cached results"}
                
                return {"clusters": results['clusters']}
            except Exception as e:
                logger.error(f"Error loading cached results: {str(e)}")
        
        # If no cached results or error, run analysis
        return self.analyze_repository(repo_path)
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a single file for code patterns
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        if not PATTERN_RECOGNIZER_AVAILABLE:
            logger.error("Pattern recognizer not available")
            return {"error": "Pattern recognizer not available"}
        
        # Get repo path (parent directory)
        repo_path = os.path.dirname(file_path)
        
        # Initialize recognizer if needed
        if self.recognizer is None or self.recognizer.repo_path != repo_path:
            self.recognizer = CodePatternRecognizer(repo_path)
        
        # Run analysis on single file
        try:
            results = self.recognizer.analyze_repository([file_path])
            return results
        except Exception as e:
            logger.error(f"Error analyzing file: {str(e)}")
            return {"error": str(e)}

# Initialize API instance
pattern_api = PatternRecognitionAPI()

def analyze_repository(repo_path: str, file_paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """Convenience function to analyze a repository"""
    return pattern_api.analyze_repository(repo_path, file_paths)

def get_patterns(repo_path: str, pattern_type: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to get patterns"""
    return pattern_api.get_patterns(repo_path, pattern_type)

def get_anomalies(repo_path: str) -> Dict[str, Any]:
    """Convenience function to get anomalies"""
    return pattern_api.get_anomalies(repo_path)

def get_clusters(repo_path: str) -> Dict[str, Any]:
    """Convenience function to get clusters"""
    return pattern_api.get_clusters(repo_path)

def analyze_file(file_path: str) -> Dict[str, Any]:
    """Convenience function to analyze a single file"""
    return pattern_api.analyze_file(file_path)