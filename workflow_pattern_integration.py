"""
Workflow Pattern Integration Module

This module integrates the pattern recognition capabilities with the workflow
mapper to provide enhanced code analysis and better workflow recommendations.
"""

import os
import logging
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import pattern recognition API
try:
    from pattern_recognition_api import pattern_api, analyze_repository
    PATTERN_API_AVAILABLE = True
except ImportError as e:
    logger.error(f"Pattern recognition API not available: {str(e)}")
    PATTERN_API_AVAILABLE = False

# Import workflow optimizer
try:
    from workflow_optimizer import WorkflowOptimizer
    WORKFLOW_OPTIMIZER_AVAILABLE = True
except ImportError as e:
    logger.error(f"Workflow optimizer not available: {str(e)}")
    WORKFLOW_OPTIMIZER_AVAILABLE = False

class WorkflowPatternIntegration:
    """
    Integrates pattern recognition with workflow mapping to provide enhanced
    analysis and recommendations.
    """
    def __init__(self, repo_path: str):
        """
        Initialize the integration
        
        Args:
            repo_path: Path to the repository root
        """
        self.repo_path = repo_path
        self.workflow_optimizer = None
        self.pattern_analysis = None
        
        if WORKFLOW_OPTIMIZER_AVAILABLE:
            self.workflow_optimizer = WorkflowOptimizer(repo_path)
        
        if PATTERN_API_AVAILABLE:
            # Run pattern analysis
            self.pattern_analysis = analyze_repository(repo_path)
    
    def get_integrated_analysis(self) -> Dict[str, Any]:
        """
        Get integrated analysis combining workflow and pattern data
        
        Returns:
            Dictionary containing integrated analysis results
        """
        results = {
            "workflow_analysis": None,
            "pattern_analysis": None,
            "integrated_recommendations": []
        }
        
        # Get workflow analysis if available
        if self.workflow_optimizer:
            try:
                workflow_analysis = self.workflow_optimizer.analyze_all_dependencies()
                results["workflow_analysis"] = workflow_analysis
            except Exception as e:
                logger.error(f"Error analyzing workflows: {str(e)}")
        
        # Add pattern analysis if available
        if self.pattern_analysis:
            results["pattern_analysis"] = self.pattern_analysis
        
        # Generate integrated recommendations
        results["integrated_recommendations"] = self._generate_integrated_recommendations()
        
        return results
    
    def _generate_integrated_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate recommendations by combining workflow and pattern analysis
        
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Can't generate recommendations without both analyses
        if not self.workflow_optimizer or not self.pattern_analysis:
            return recommendations
        
        try:
            # Get workflow bottlenecks
            workflow_analysis = self.workflow_optimizer.analyze_all_dependencies()
            bottlenecks = workflow_analysis.get('bottlenecks', [])
            
            # Get performance patterns
            patterns = self.pattern_analysis.get('patterns', {})
            performance_patterns = patterns.get('performance_patterns', [])
            anti_patterns = patterns.get('anti_patterns', [])
            
            # Look for bottlenecks that might be caused by performance patterns
            for bottleneck in bottlenecks:
                bottleneck_file = bottleneck.get('file')
                bottleneck_function = bottleneck.get('function')
                
                # Find any performance issues in this file
                related_pattern_issues = []
                
                for pattern in performance_patterns:
                    for example in pattern.get('examples', []):
                        example_file = example.get('file_path', '')
                        
                        if bottleneck_file and bottleneck_file in example_file:
                            related_pattern_issues.append({
                                'pattern_name': pattern.get('name'),
                                'pattern_description': pattern.get('description'),
                                'severity': pattern.get('severity', 'medium')
                            })
                
                # Also check anti-patterns
                for pattern in anti_patterns:
                    for example in pattern.get('examples', []):
                        example_file = example.get('file_path', '')
                        
                        if bottleneck_file and bottleneck_file in example_file:
                            related_pattern_issues.append({
                                'pattern_name': pattern.get('name'),
                                'pattern_description': pattern.get('description'),
                                'severity': 'high'  # Anti-patterns are high severity
                            })
                
                # If we found issues, create a recommendation
                if related_pattern_issues:
                    recommendation = {
                        'workflow_component': bottleneck.get('name', ''),
                        'file': bottleneck_file,
                        'function': bottleneck_function,
                        'performance_impact': bottleneck.get('impact', 'medium'),
                        'related_patterns': related_pattern_issues,
                        'recommendation': (
                            f"Optimize the {bottleneck_function} function in {bottleneck_file}. "
                            f"This is a workflow bottleneck with {len(related_pattern_issues)} "
                            f"detected pattern issues that may be affecting performance."
                        )
                    }
                    recommendations.append(recommendation)
            
            # Look for clustering opportunities
            clusters = self.pattern_analysis.get('clusters', {})
            if clusters:
                # Identify clusters with multiple modules that could be refactored
                for cluster_id, cluster_info in clusters.items():
                    if cluster_info.get('size', 0) >= 3:  # At least 3 similar modules
                        samples = cluster_info.get('samples', [])
                        file_paths = [s.get('file_path', '') for s in samples]
                        
                        recommendation = {
                            'type': 'refactoring',
                            'cluster_id': cluster_id,
                            'file_count': len(file_paths),
                            'files': file_paths[:5],  # First 5 files
                            'recommendation': (
                                f"Consider refactoring cluster {cluster_id} with {len(file_paths)} "
                                f"similar modules. These appear to share significant code patterns "
                                f"and may benefit from extraction of common functionality."
                            )
                        }
                        recommendations.append(recommendation)
        
        except Exception as e:
            logger.error(f"Error generating integrated recommendations: {str(e)}")
        
        return recommendations
    
    def get_workflow_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get workflow optimization recommendations based on pattern analysis
        
        Returns:
            List of recommendation dictionaries
        """
        if not self.workflow_optimizer or not self.pattern_analysis:
            return []
        
        try:
            # Generate standard workflow recommendations
            standard_recommendations = self.workflow_optimizer.generate_optimization_recommendations()
            
            # Enhance with pattern analysis
            enhanced_recommendations = self._enhance_recommendations_with_patterns(standard_recommendations)
            
            return enhanced_recommendations
        except Exception as e:
            logger.error(f"Error generating workflow recommendations: {str(e)}")
            return []
    
    def _enhance_recommendations_with_patterns(self, 
                                              recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance workflow recommendations with pattern analysis insights
        
        Args:
            recommendations: List of standard workflow recommendations
            
        Returns:
            Enhanced recommendations
        """
        if not self.pattern_analysis:
            return recommendations
        
        # Get patterns
        patterns = self.pattern_analysis.get('patterns', {})
        
        # Enhance each recommendation
        for recommendation in recommendations:
            # Get relevant file
            file_path = recommendation.get('file', '')
            if not file_path:
                continue
            
            # Find patterns related to this file
            related_patterns = []
            
            # Check all pattern types
            for pattern_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    for example in pattern.get('examples', []):
                        example_file = example.get('file_path', '')
                        
                        if file_path in example_file:
                            related_patterns.append({
                                'pattern_type': pattern_type,
                                'pattern_name': pattern.get('name'),
                                'pattern_description': pattern.get('description')
                            })
            
            # Add related patterns to recommendation
            if related_patterns:
                recommendation['related_patterns'] = related_patterns
                
                # Enhance description
                recommendation['description'] = recommendation.get('description', '') + (
                    f" Additionally, {len(related_patterns)} code patterns were detected "
                    f"in this file that may affect performance or maintainability."
                )
        
        return recommendations
    
    def analyze_critical_paths(self) -> Dict[str, Any]:
        """
        Analyze critical paths in workflows and correlate with patterns
        
        Returns:
            Dictionary with critical path analysis
        """
        if not self.workflow_optimizer or not self.pattern_analysis:
            return {"error": "Workflow optimizer or pattern analysis not available"}
        
        try:
            # Get critical paths
            critical_paths = self.workflow_optimizer.analyze_critical_paths()
            
            # Get patterns
            patterns = self.pattern_analysis.get('patterns', {})
            performance_patterns = patterns.get('performance_patterns', [])
            
            # Map performance patterns to critical path components
            for path in critical_paths:
                for node in path.get('nodes', []):
                    node_file = node.get('file', '')
                    
                    # Find performance patterns in this file
                    pattern_issues = []
                    
                    for pattern in performance_patterns:
                        for example in pattern.get('examples', []):
                            example_file = example.get('file_path', '')
                            
                            if node_file and node_file in example_file:
                                pattern_issues.append({
                                    'pattern_name': pattern.get('name'),
                                    'pattern_description': pattern.get('description'),
                                    'severity': pattern.get('severity', 'medium')
                                })
                    
                    # Add pattern issues to node
                    if pattern_issues:
                        node['pattern_issues'] = pattern_issues
            
            return {"critical_paths": critical_paths}
        
        except Exception as e:
            logger.error(f"Error analyzing critical paths: {str(e)}")
            return {"error": str(e)}


# Create convenience function
def get_integrated_analysis(repo_path: str) -> Dict[str, Any]:
    """
    Get integrated analysis for a repository
    
    Args:
        repo_path: Path to the repository root
        
    Returns:
        Dictionary with integrated analysis results
    """
    integration = WorkflowPatternIntegration(repo_path)
    return integration.get_integrated_analysis()

def get_enhanced_workflow_recommendations(repo_path: str) -> List[Dict[str, Any]]:
    """
    Get enhanced workflow recommendations for a repository
    
    Args:
        repo_path: Path to the repository root
        
    Returns:
        List of recommendation dictionaries
    """
    integration = WorkflowPatternIntegration(repo_path)
    return integration.get_workflow_optimization_recommendations()

def analyze_critical_paths_with_patterns(repo_path: str) -> Dict[str, Any]:
    """
    Analyze critical paths with pattern correlation
    
    Args:
        repo_path: Path to the repository root
        
    Returns:
        Dictionary with critical path analysis
    """
    integration = WorkflowPatternIntegration(repo_path)
    return integration.analyze_critical_paths()