import os
import re
import json
import logging
import datetime
import networkx as nx
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict

# Import existing modules
from workflow_analyzer import analyze_workflow_file, find_workflow_files, identify_workflow_patterns
from workflow_mapper import build_dependency_graph

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowOptimizer:
    """
    Analyzes workflows and provides optimization recommendations
    based on performance, complexity, and structure analysis.
    """
    
    def __init__(self, repo_path: str = '.'):
        """
        Initialize the optimizer with a repository path
        
        Args:
            repo_path: Path to the repository (defaults to current directory)
        """
        self.repo_path = repo_path
        self.workflow_files = []
        self.workflow_analyses = []
        self.dependency_graph = None
        self.optimization_recommendations = []
        self.performance_metrics = {}
        self.workflow_patterns = []
        self.complexity_scores = {}
        
    def analyze_repository(self) -> Dict[str, Any]:
        """
        Perform a comprehensive analysis of the repository workflows
        
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Analyzing repository at {self.repo_path} for workflow optimization...")
        
        # Step 1: Find workflow-related files
        self.workflow_files = find_workflow_files(self.repo_path)
        logger.info(f"Found {len(self.workflow_files)} workflow-related files")
        
        # Step 2: Analyze each workflow file
        self.workflow_analyses = []
        for file_path in self.workflow_files:
            analysis = analyze_workflow_file(self.repo_path, file_path)
            self.workflow_analyses.append(analysis)
        
        # Step 3: Identify common workflow patterns
        self.workflow_patterns = identify_workflow_patterns(self.workflow_analyses)
        
        # Step 4: Build dependency graph
        self.dependency_graph = build_dependency_graph(self.repo_path, self.workflow_files)
        
        # Step 5: Calculate complexity metrics
        self._calculate_complexity_metrics()
        
        # Step 6: Generate optimization recommendations
        self._generate_recommendations()
        
        # Return the comprehensive analysis
        return {
            'workflow_files': self.workflow_files,
            'workflow_patterns': self.workflow_patterns,
            'complexity_scores': self.complexity_scores,
            'dependency_graph': self.dependency_graph,
            'optimization_recommendations': self.optimization_recommendations,
            'performance_metrics': self.performance_metrics,
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    def _calculate_complexity_metrics(self) -> None:
        """Calculate complexity metrics for workflows"""
        logger.info("Calculating workflow complexity metrics...")
        
        # Initialize complexity metrics
        self.complexity_scores = {}
        
        # Get the full dependency graph
        graph_data = self.dependency_graph
        
        if not graph_data or 'graph' not in graph_data:
            logger.warning("No dependency graph available for complexity calculation")
            return
        
        # Create a NetworkX graph from the dependency data
        G = nx.DiGraph()
        
        # Add nodes
        for node in graph_data['graph']['nodes']:
            G.add_node(node['id'], 
                      time_complexity=node.get('time_complexity', 1),
                      memory_complexity=node.get('memory_complexity', 1))
                      
        # Add edges
        for edge in graph_data['graph']['edges']:
            if edge['source'] in G and edge['target'] in G:
                G.add_edge(edge['source'], edge['target'], weight=edge.get('weight', 1))
        
        # Calculate per-file complexity metrics
        for file_path in self.workflow_files:
            if file_path in G:
                # Base complexity from the node attributes
                time_complexity = G.nodes[file_path].get('time_complexity', 1)
                memory_complexity = G.nodes[file_path].get('memory_complexity', 1)
                
                # Structural complexity based on incoming and outgoing dependencies
                in_degree = G.in_degree(file_path)
                out_degree = G.out_degree(file_path)
                
                # Convert degree views to integers
                in_degree_value = in_degree if isinstance(in_degree, int) else 0
                out_degree_value = out_degree if isinstance(out_degree, int) else 0
                
                # Centrality measures
                try:
                    # How important is this file in connecting different parts of the codebase
                    betweenness = nx.betweenness_centrality(G).get(file_path, 0)
                    
                    # How many steps away from other files
                    closeness = nx.closeness_centrality(G).get(file_path, 0)
                except Exception as e:
                    logger.warning(f"Error calculating centrality metrics: {str(e)}")
                    betweenness = 0
                    closeness = 0
                    
                # Calculate a composite complexity score
                structural_complexity = in_degree_value + out_degree_value
                connectivity_score = (betweenness * 10) + (closeness * 5)
                
                # Overall complexity is a weighted combination of all factors
                overall_complexity = (
                    (time_complexity * 0.3) + 
                    (memory_complexity * 0.2) + 
                    (structural_complexity * 0.25) + 
                    (connectivity_score * 0.25)
                )
                
                # Store the complexity scores
                self.complexity_scores[file_path] = {
                    'time_complexity': time_complexity,
                    'memory_complexity': memory_complexity,
                    'structural_complexity': structural_complexity,
                    'connectivity_score': connectivity_score,
                    'overall_complexity': overall_complexity,
                    'in_degree': in_degree_value,
                    'out_degree': out_degree_value
                }
        
        # Calculate system-level complexity metrics
        if self.complexity_scores:
            try:
                # Average complexity
                avg_complexity = sum(s['overall_complexity'] for s in self.complexity_scores.values()) / len(self.complexity_scores)
                
                # Highest complexity components
                sorted_complexities = sorted(
                    [(file, data['overall_complexity']) for file, data in self.complexity_scores.items()],
                    key=lambda x: x[1],
                    reverse=True
                )
                
                highest_complexity = [
                    {'file': file, 'complexity': complexity}
                    for file, complexity in sorted_complexities[:5]  # Top 5 most complex
                ]
                
                # Calculate cyclomatic complexity of the system
                try:
                    # Number of strongly connected components
                    strongly_connected = list(nx.strongly_connected_components(G))
                    
                    # Cyclomatic complexity = edges - nodes + 2 * connected components
                    cyclomatic = (
                        G.number_of_edges() - 
                        G.number_of_nodes() + 
                        2 * len(strongly_connected)
                    )
                except Exception as e:
                    logger.warning(f"Error calculating cyclomatic complexity: {str(e)}")
                    cyclomatic = 0
                    strongly_connected = []
                
                # Store system-level metrics
                self.performance_metrics['complexity'] = {
                    'average_complexity': avg_complexity,
                    'highest_complexity_components': highest_complexity,
                    'cyclomatic_complexity': cyclomatic,
                    'strongly_connected_components': len(strongly_connected)
                }
                
            except Exception as e:
                logger.error(f"Error calculating system-level complexity: {str(e)}")
    
    def _identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify workflow bottlenecks from the dependency graph"""
        bottlenecks = []
        
        # Check if we have a dependency graph with bottlenecks identified
        if not self.dependency_graph or 'bottlenecks' not in self.dependency_graph:
            return bottlenecks
            
        # Extract the bottlenecks from the dependency graph
        graph_bottlenecks = self.dependency_graph.get('bottlenecks', [])
        
        for bottleneck in graph_bottlenecks:
            # Enhance bottleneck information with complexity data if available
            file_path = bottleneck.get('file', '')
            complexity_data = self.complexity_scores.get(file_path, {})
            
            bottlenecks.append({
                'file': file_path,
                'severity': bottleneck.get('severity', 0),
                'centrality': bottleneck.get('centrality', 0),
                'in_degree': bottleneck.get('in_degree', 0),
                'out_degree': bottleneck.get('out_degree', 0),
                'complexity': complexity_data.get('overall_complexity', 0),
                'type': 'dependency_bottleneck',
                'impact': 'high' if bottleneck.get('severity', 0) > 0.5 else 'medium'
            })
        
        return bottlenecks
    
    def _identify_critical_paths(self) -> List[Dict[str, Any]]:
        """Identify critical paths in the workflow"""
        critical_paths = []
        
        # Check if we have critical paths in the dependency graph
        if not self.dependency_graph or 'critical_paths' not in self.dependency_graph:
            return critical_paths
            
        # Extract critical paths from the dependency graph
        graph_critical_paths = self.dependency_graph.get('critical_paths', [])
        
        for path in graph_critical_paths:
            path_type = path.get('type', '')
            path_nodes = path.get('path', [])
            
            # Calculate the total complexity of the path
            total_complexity = sum(
                self.complexity_scores.get(node, {}).get('overall_complexity', 1)
                for node in path_nodes
            )
            
            critical_paths.append({
                'path': path_nodes,
                'path_str': path.get('path_str', ''),
                'length': path.get('length', 0),
                'type': path_type,
                'total_complexity': total_complexity,
                'severity': path.get('severity', 'medium'),
                'is_cycle': path_type == 'cycle'
            })
        
        return critical_paths
    
    def _generate_recommendations(self) -> None:
        """Generate optimization recommendations based on analyses"""
        logger.info("Generating workflow optimization recommendations...")
        
        recommendations = []
        
        # 1. Identify bottlenecks
        bottlenecks = self._identify_bottlenecks()
        
        # 2. Identify critical paths
        critical_paths = self._identify_critical_paths()
        
        # 3. Generate bottleneck recommendations
        if bottlenecks:
            for bottleneck in bottlenecks[:3]:  # Focus on top 3 bottlenecks
                file_name = os.path.basename(bottleneck['file'])
                severity = bottleneck['severity']
                
                if severity > 0.7:
                    impact_level = "high"
                    urgency = "high"
                elif severity > 0.4:
                    impact_level = "medium"
                    urgency = "medium"
                else:
                    impact_level = "low"
                    urgency = "low"
                
                recommendations.append({
                    'type': 'bottleneck_refactoring',
                    'component': bottleneck['file'],
                    'impact': impact_level,
                    'urgency': urgency,
                    'description': f"Refactor the bottleneck component '{file_name}' to reduce dependencies.",
                    'details': f"This component has {bottleneck['in_degree']} incoming and {bottleneck['out_degree']} outgoing dependencies, making it a central bottleneck in the workflow.",
                    'suggestions': [
                        f"Break '{file_name}' into smaller, more focused modules",
                        "Reduce the number of cross-module dependencies",
                        "Consider using dependency injection to decouple components"
                    ]
                })
        
        # 4. Generate critical path recommendations
        if critical_paths:
            # Cycles are particularly problematic
            cycles = [path for path in critical_paths if path['is_cycle']]
            
            if cycles:
                for cycle in cycles[:2]:  # Focus on top 2 cycles
                    nodes = [os.path.basename(node) for node in cycle['path']]
                    nodes_str = " -> ".join(nodes)
                    
                    recommendations.append({
                        'type': 'circular_dependency',
                        'components': cycle['path'],
                        'impact': 'high',
                        'urgency': 'high',
                        'description': f"Resolve circular dependency cycle: {nodes_str}",
                        'details': "Circular dependencies can cause maintenance problems, testing difficulties, and potentially runtime issues.",
                        'suggestions': [
                            "Extract common functionality to a separate module",
                            "Use interfaces or design patterns to break the cycle",
                            "Redesign the component boundaries to eliminate circular references"
                        ]
                    })
            
            # Long linear paths can also be inefficient
            long_paths = [path for path in critical_paths if not path['is_cycle'] and path['length'] > 3]
            
            if long_paths:
                for path in long_paths[:2]:  # Focus on top 2 long paths
                    recommendations.append({
                        'type': 'long_execution_path',
                        'components': path['path'],
                        'impact': 'medium',
                        'urgency': 'medium',
                        'description': f"Optimize long execution path ({path['length']} steps)",
                        'details': f"Long sequential execution chains can impact performance and reliability: {path['path_str']}",
                        'suggestions': [
                            "Look for opportunities to parallelize steps in the path",
                            "Consider caching intermediate results for frequently executed paths",
                            "Evaluate if all steps are necessary for every execution"
                        ]
                    })
        
        # 5. Complexity-based recommendations
        high_complexity_files = sorted(
            [(file, data['overall_complexity']) for file, data in self.complexity_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )[:3]  # Top 3 most complex
        
        for file_path, complexity in high_complexity_files:
            if complexity > 50:  # Threshold for high complexity
                urgency = "high"
            elif complexity > 30:
                urgency = "medium"
            else:
                urgency = "low"
                
            file_name = os.path.basename(file_path)
            
            recommendations.append({
                'type': 'complexity_reduction',
                'component': file_path,
                'impact': 'medium',
                'urgency': urgency,
                'description': f"Reduce complexity in '{file_name}'",
                'details': f"This file has high overall complexity ({complexity:.1f}) which can lead to maintenance issues and bugs.",
                'suggestions': [
                    "Break down large functions into smaller, more focused ones",
                    "Reduce nesting levels in control structures",
                    "Extract complex logic into separate, well-tested functions",
                    "Consider applying design patterns to simplify the structure"
                ]
            })
        
        # 6. Standardization recommendations
        
        # Check for mixed workflow patterns
        if len(self.workflow_patterns) > 1:
            pattern_names = [p['name'] for p in self.workflow_patterns]
            recommendations.append({
                'type': 'standardization',
                'component': 'all',
                'impact': 'medium',
                'urgency': 'medium',
                'description': "Standardize workflow patterns across the codebase",
                'details': f"Currently using multiple workflow patterns: {', '.join(pattern_names)}",
                'suggestions': [
                    f"Adopt '{pattern_names[0].replace('_', ' ').title()}' as the standard pattern",
                    "Create shared workflow utilities to encourage standardization",
                    "Refactor outlier components to follow the standard pattern"
                ]
            })
        
        # 7. Check for orchestration framework usage
        framework_patterns = {'airflow', 'prefect', 'dagster', 'luigi', 'dask'}
        used_frameworks = {p['name'] for p in self.workflow_patterns if p['name'] in framework_patterns}
        
        if not used_frameworks:
            # No framework is being used
            recommendations.append({
                'type': 'framework_adoption',
                'component': 'all',
                'impact': 'high',
                'urgency': 'medium',
                'description': "Adopt a mature workflow orchestration framework",
                'details': "No standard workflow framework is currently in use, which may lead to reliability and scalability issues.",
                'suggestions': [
                    "Evaluate and adopt a workflow framework like Airflow, Prefect, or Dagster",
                    "Implement a proof-of-concept with the selected framework",
                    "Gradually migrate existing workflows to the new framework"
                ]
            })
        elif len(used_frameworks) > 1:
            # Multiple frameworks are being used
            recommendations.append({
                'type': 'framework_standardization',
                'component': 'all',
                'impact': 'medium',
                'urgency': 'medium',
                'description': "Standardize on a single workflow framework",
                'details': f"Currently using multiple workflow frameworks: {', '.join(used_frameworks)}",
                'suggestions': [
                    f"Select one framework as the standard (recommend: {list(used_frameworks)[0]})",
                    "Create a migration plan for workflows using other frameworks",
                    "Establish guidelines for new workflow development"
                ]
            })
        
        # 8. Parallel execution recommendations
        parallel_patterns = {'dask', 'parallel_workflow', 'concurrent_execution'}
        uses_parallelism = any(p['name'] in parallel_patterns for p in self.workflow_patterns)
        
        if not uses_parallelism and (critical_paths or bottlenecks):
            recommendations.append({
                'type': 'parallelization',
                'component': 'all',
                'impact': 'high',
                'urgency': 'medium',
                'description': "Implement parallel execution for performance-critical workflows",
                'details': "Current workflows appear to be primarily sequential, which can limit throughput and performance.",
                'suggestions': [
                    "Identify independent workflow steps that can be executed in parallel",
                    "Implement concurrent execution using threading, multiprocessing, or async/await",
                    "Consider using Dask for distributed computing capabilities"
                ]
            })
        
        # Store the recommendations
        self.optimization_recommendations = recommendations
        logger.info(f"Generated {len(recommendations)} workflow optimization recommendations")
    
    def get_optimization_recommendations(self, 
                                         component_filter: Optional[str] = None,
                                         impact_filter: Optional[str] = None,
                                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get workflow optimization recommendations with optional filtering
        
        Args:
            component_filter: Filter by component name (partial match)
            impact_filter: Filter by impact level ('high', 'medium', 'low')
            limit: Maximum number of recommendations to return
            
        Returns:
            List of optimization recommendations
        """
        # If no recommendations yet, generate them
        if not self.optimization_recommendations:
            self._generate_recommendations()
            
        # Apply filters
        filtered_recommendations = self.optimization_recommendations
        
        if component_filter:
            filtered_recommendations = [
                rec for rec in filtered_recommendations
                if component_filter.lower() in str(rec.get('component', '')).lower()
            ]
            
        if impact_filter:
            filtered_recommendations = [
                rec for rec in filtered_recommendations
                if rec.get('impact', '').lower() == impact_filter.lower()
            ]
            
        # Sort by impact and urgency
        impact_priority = {'high': 3, 'medium': 2, 'low': 1}
        urgency_priority = {'high': 3, 'medium': 2, 'low': 1}
        
        sorted_recommendations = sorted(
            filtered_recommendations,
            key=lambda x: (
                impact_priority.get(x.get('impact', 'low'), 0),
                urgency_priority.get(x.get('urgency', 'low'), 0)
            ),
            reverse=True
        )
        
        # Apply limit
        return sorted_recommendations[:limit]
    
    def optimize_workflow(self, component: str) -> Dict[str, Any]:
        """
        Generate a detailed optimization plan for a specific component
        
        Args:
            component: Path to the component to optimize
            
        Returns:
            Dictionary with optimization plan details
        """
        logger.info(f"Generating optimization plan for {component}...")
        
        # Get recommendations specific to this component
        recommendations = self.get_optimization_recommendations(component_filter=component)
        
        if not recommendations:
            return {
                'component': component,
                'status': 'no_recommendations',
                'message': f"No specific optimization recommendations for {component}",
                'timestamp': datetime.datetime.now().isoformat()
            }
            
        # Get complexity data for this component
        complexity_data = self.complexity_scores.get(component, {})
        
        # Find this component in bottlenecks
        bottleneck_data = None
        for bottleneck in self._identify_bottlenecks():
            if bottleneck['file'] == component:
                bottleneck_data = bottleneck
                break
                
        # Create an optimization plan
        optimization_plan = {
            'component': component,
            'recommendations': recommendations,
            'complexity_profile': complexity_data,
            'bottleneck_data': bottleneck_data,
            'estimated_effort': self._estimate_optimization_effort(component, recommendations),
            'implementation_steps': self._generate_implementation_steps(component, recommendations),
            'expected_benefits': self._estimate_optimization_benefits(component, recommendations),
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        return optimization_plan
    
    def _estimate_optimization_effort(self, component: str, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate the effort required to implement the recommendations"""
        # Base effort on number and type of recommendations
        num_recommendations = len(recommendations)
        
        # Weight by recommendation type
        type_weights = {
            'bottleneck_refactoring': 3.0,
            'circular_dependency': 2.5,
            'complexity_reduction': 2.0,
            'long_execution_path': 1.5,
            'standardization': 1.0,
            'framework_adoption': 4.0,
            'framework_standardization': 3.0,
            'parallelization': 2.5
        }
        
        weighted_effort = sum(
            type_weights.get(rec.get('type', ''), 1.0) 
            for rec in recommendations
        )
        
        # Get component complexity
        complexity = self.complexity_scores.get(component, {}).get('overall_complexity', 1)
        
        # Calculate time estimates
        if complexity > 50 or weighted_effort > 10:
            effort_level = "high"
            days_estimate = (weighted_effort * complexity) / 50
        elif complexity > 20 or weighted_effort > 5:
            effort_level = "medium"
            days_estimate = (weighted_effort * complexity) / 100
        else:
            effort_level = "low"
            days_estimate = (weighted_effort * complexity) / 200
            
        # Ensure reasonable bounds
        days_estimate = max(0.5, min(30, days_estimate))
        
        return {
            'level': effort_level,
            'days_estimate': round(days_estimate, 1),
            'factors': {
                'recommendations_count': num_recommendations,
                'weighted_effort': round(weighted_effort, 1),
                'component_complexity': round(complexity, 1)
            }
        }
    
    def _generate_implementation_steps(self, component: str, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate step-by-step implementation steps for the recommendations"""
        implementation_steps = []
        
        # Group recommendations by type
        recommendations_by_type = defaultdict(list)
        for rec in recommendations:
            rec_type = rec.get('type', 'other')
            recommendations_by_type[rec_type].append(rec)
            
        # Define implementation steps based on recommendation types
        step_number = 1
        
        # First address circular dependencies as they're most problematic
        if 'circular_dependency' in recommendations_by_type:
            for rec in recommendations_by_type['circular_dependency']:
                components = rec.get('components', [])
                components_str = ", ".join([os.path.basename(c) for c in components])
                
                implementation_steps.append({
                    'step': step_number,
                    'title': f"Resolve circular dependency between {components_str}",
                    'description': "Break the circular dependency by restructuring component relationships",
                    'tasks': [
                        "Identify the specific dependencies causing the cycle",
                        "Extract shared functionality to a separate module",
                        "Implement interfaces to decouple the components",
                        "Validate that the cycle is resolved while maintaining functionality"
                    ]
                })
                step_number += 1
                
        # Then address bottlenecks
        if 'bottleneck_refactoring' in recommendations_by_type:
            for rec in recommendations_by_type['bottleneck_refactoring']:
                component_name = os.path.basename(rec.get('component', ''))
                
                implementation_steps.append({
                    'step': step_number,
                    'title': f"Refactor bottleneck component: {component_name}",
                    'description': "Reduce the centrality of this component to improve maintainability",
                    'tasks': [
                        "Analyze incoming and outgoing dependencies",
                        "Identify responsibilities that can be moved to other components",
                        "Break down the component into smaller, focused modules",
                        "Update dependencies to reference the new structure"
                    ]
                })
                step_number += 1
                
        # Address complexity issues
        if 'complexity_reduction' in recommendations_by_type:
            for rec in recommendations_by_type['complexity_reduction']:
                component_name = os.path.basename(rec.get('component', ''))
                
                implementation_steps.append({
                    'step': step_number,
                    'title': f"Reduce complexity in {component_name}",
                    'description': "Simplify the internal structure to improve maintainability and reliability",
                    'tasks': [
                        "Identify the most complex methods/functions",
                        "Break down large functions into smaller, focused ones",
                        "Reduce nesting levels in control structures",
                        "Extract complex logic into separate, well-tested functions",
                        "Apply appropriate design patterns to simplify the structure"
                    ]
                })
                step_number += 1
                
        # Address long execution paths
        if 'long_execution_path' in recommendations_by_type:
            for rec in recommendations_by_type['long_execution_path']:
                components = [os.path.basename(c) for c in rec.get('components', [])]
                
                implementation_steps.append({
                    'step': step_number,
                    'title': f"Optimize execution path with {len(components)} steps",
                    'description': "Improve performance by optimizing the execution chain",
                    'tasks': [
                        "Review the complete execution path to understand dependencies",
                        "Identify steps that can be executed in parallel",
                        "Implement caching for intermediate results",
                        "Consider lazy loading for resource-intensive operations",
                        "Add performance monitoring to validate improvements"
                    ]
                })
                step_number += 1
                
        # Address standardization
        if 'standardization' in recommendations_by_type:
            implementation_steps.append({
                'step': step_number,
                'title': "Standardize workflow patterns",
                'description': "Adopt consistent workflow patterns across the codebase",
                'tasks': [
                    "Document the chosen standard workflow pattern",
                    "Create shared utilities to support the standard pattern",
                    "Gradually refactor components to follow the standard",
                    "Add code reviews specifically for workflow pattern compliance"
                ]
            })
            step_number += 1
            
        # Address framework adoption/standardization
        if 'framework_adoption' in recommendations_by_type:
            implementation_steps.append({
                'step': step_number,
                'title': "Adopt a workflow orchestration framework",
                'description': "Implement a mature workflow framework to improve reliability and scalability",
                'tasks': [
                    "Evaluate and select an appropriate framework (Airflow, Prefect, or Dagster)",
                    "Create a small proof-of-concept implementation",
                    "Develop a migration strategy for existing workflows",
                    "Implement framework-specific monitoring and error handling",
                    "Train the team on the new framework"
                ]
            })
            step_number += 1
        elif 'framework_standardization' in recommendations_by_type:
            frameworks = set()
            for rec in recommendations_by_type['framework_standardization']:
                if 'details' in rec:
                    # Extract framework names from the details
                    frameworks_str = rec['details'].split('frameworks:')[1].strip()
                    frameworks.update([f.strip() for f in frameworks_str.split(',')])
            
            primary_framework = list(frameworks)[0] if frameworks else "the selected framework"
            
            implementation_steps.append({
                'step': step_number,
                'title': f"Standardize on {primary_framework} framework",
                'description': "Consolidate to a single workflow framework for consistency",
                'tasks': [
                    f"Document {primary_framework} as the standard framework",
                    "Create a migration plan for workflows using other frameworks",
                    "Establish design patterns and best practices for the framework",
                    "Provide training and support for teams during migration"
                ]
            })
            step_number += 1
            
        # Address parallelization
        if 'parallelization' in recommendations_by_type:
            implementation_steps.append({
                'step': step_number,
                'title': "Implement parallel execution patterns",
                'description': "Improve performance by executing independent tasks in parallel",
                'tasks': [
                    "Identify workflow segments that can be executed independently",
                    "Implement appropriate concurrency mechanisms (threading, multiprocessing, async)",
                    "Add synchronization points where results need to be combined",
                    "Implement error handling for parallel tasks",
                    "Validate performance improvements with benchmarks"
                ]
            })
            step_number += 1
            
        return implementation_steps
    
    def _estimate_optimization_benefits(self, component: str, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate the benefits of implementing the optimization recommendations"""
        # Count recommendations by impact
        impact_counts = defaultdict(int)
        for rec in recommendations:
            impact = rec.get('impact', 'low')
            impact_counts[impact] += 1
            
        # Total impact score
        impact_weights = {'high': 3, 'medium': 2, 'low': 1}
        impact_score = sum(impact_weights[impact] * count for impact, count in impact_counts.items())
        
        # Scale by component complexity if available
        complexity = self.complexity_scores.get(component, {}).get('overall_complexity', 1)
        weighted_impact = impact_score * (1 + min(1, complexity / 50))
        
        # Calculate expected benefits
        if weighted_impact > 15 or impact_counts['high'] >= 2:
            performance_benefit = "high"
            maintainability_benefit = "high"
            reliability_benefit = "high"
        elif weighted_impact > 8 or impact_counts['high'] >= 1:
            performance_benefit = "medium"
            maintainability_benefit = "high"
            reliability_benefit = "medium"
        elif weighted_impact > 4:
            performance_benefit = "medium"
            maintainability_benefit = "medium"
            reliability_benefit = "medium"
        else:
            performance_benefit = "low"
            maintainability_benefit = "medium"
            reliability_benefit = "low"
            
        # Special adjustments by recommendation types
        has_type = {rec.get('type', ''): True for rec in recommendations}
        
        if has_type.get('parallelization', False):
            performance_benefit = "high"
            
        if has_type.get('circular_dependency', False):
            reliability_benefit = "high"
            maintainability_benefit = "high"
            
        if has_type.get('framework_adoption', False):
            reliability_benefit = "high"
            
        if has_type.get('complexity_reduction', False):
            maintainability_benefit = "high"
            
        return {
            'performance': performance_benefit,
            'maintainability': maintainability_benefit,
            'reliability': reliability_benefit,
            'impact_score': round(weighted_impact, 1),
            'factors': {
                'impact_counts': dict(impact_counts),
                'component_complexity': round(complexity, 1)
            }
        }