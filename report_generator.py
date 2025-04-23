import logging
import pandas as pd
from collections import Counter, defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_summary_report(analysis_results):
    """
    Generate a comprehensive summary report based on all analysis results
    
    Parameters:
    - analysis_results: Dict containing all analysis results
    
    Returns:
    - dict: Summary report with key findings and recommendations
    """
    logger.info("Generating summary report...")
    
    # Initialize the summary report
    summary_report = {
        'key_findings': {},
        'recommendations': {},
        'metrics': {},
        'priority_areas': []
    }
    
    # Extract repository structure information
    if 'repository_structure' in analysis_results:
        repo_structure = analysis_results['repository_structure']
        
        summary_report['metrics']['Repository Size'] = {
            'Files': repo_structure.get('file_count', 0),
            'Directories': repo_structure.get('directory_count', 0),
            'Deepest Nesting': repo_structure.get('deepest_nesting', 0)
        }
        
        # Add file type distribution
        file_types = repo_structure.get('file_types', [])
        if file_types:
            file_type_findings = []
            for file_type in file_types[:5]:  # Top 5 file types
                file_type_findings.append(
                    f"{file_type.get('extension', 'unknown')}: {file_type.get('count', 0)} files"
                )
            
            summary_report['key_findings']['Repository Structure'] = [
                f"Total of {repo_structure.get('file_count', 0)} files across {repo_structure.get('directory_count', 0)} directories",
                f"Main file types: {', '.join(file_type_findings)}"
            ]
    
    # Extract code review findings
    if 'code_review' in analysis_results:
        code_review = analysis_results['code_review']
        
        # Add metrics
        if 'metrics' in code_review:
            for metric, value in code_review.get('metrics', {}).items():
                summary_report['metrics'][metric] = value
        
        # Add key findings
        code_findings = []
        
        # Issues by type
        issues_by_type = Counter()
        for file_issue in code_review.get('files_with_issues', []):
            for detail in file_issue.get('details', []):
                for code_smell in ['long_method', 'complex_method', 'duplicated_code', 'large_class', 
                                  'magic_numbers', 'commented_code', 'nested_conditionals']:
                    if code_smell in detail:
                        issues_by_type[code_smell] += 1
        
        # Add findings about issues
        if issues_by_type:
            top_issues = issues_by_type.most_common(3)
            for issue, count in top_issues:
                code_findings.append(f"{count} instances of {issue.replace('_', ' ')}")
        
        # Add findings about complex files
        complex_files = code_review.get('top_complex_files', [])
        if complex_files:
            avg_complexity = sum(f.get('complexity', 0) for f in complex_files) / len(complex_files)
            code_findings.append(
                f"Average complexity of {avg_complexity:.1f} in the most complex files"
            )
        
        # Add findings about duplications
        duplications = code_review.get('duplications', [])
        if duplications:
            code_findings.append(f"Found {len(duplications)} instances of code duplication")
        
        if code_findings:
            summary_report['key_findings']['Code Quality'] = code_findings
        
        # Add recommendations from code review
        if 'improvement_opportunities' in code_review:
            for category, opportunities in code_review.get('improvement_opportunities', {}).items():
                if category not in summary_report['recommendations']:
                    summary_report['recommendations'][category] = []
                
                summary_report['recommendations'][category].extend(opportunities)
        
        # Add to priority areas if significant issues found
        if issues_by_type and sum(issues_by_type.values()) > 10:
            summary_report['priority_areas'].append('Code Quality')
    
    # Extract database analysis findings
    if 'database_analysis' in analysis_results:
        db_analysis = analysis_results['database_analysis']
        
        db_findings = []
        
        # Database models
        models = db_analysis.get('database_models', {})
        if models:
            db_findings.append(f"Found {len(models)} database models")
            
            # ORM frameworks
            orm_frameworks = db_analysis.get('orm_frameworks', [])
            if orm_frameworks:
                db_findings.append(f"Using {', '.join(orm_frameworks)} ORM framework(s)")
        
        # Raw SQL queries
        sql_queries = db_analysis.get('sql_queries', [])
        if sql_queries:
            db_findings.append(f"Found {len(sql_queries)} raw SQL queries")
        
        # Database redundancies
        redundancies = db_analysis.get('redundancies', [])
        if redundancies:
            db_findings.append(f"Detected {len(redundancies)} potential database redundancies")
        
        if db_findings:
            summary_report['key_findings']['Database Structure'] = db_findings
        
        # Add recommendations from database analysis
        recommendations = db_analysis.get('consolidation_recommendations', [])
        if recommendations:
            summary_report['recommendations']['Database Design'] = recommendations[:5]  # Top 5 recommendations
            
            # Add to priority areas if significant issues found
            if redundancies or len(models) > 5:
                summary_report['priority_areas'].append('Database Design')
    
    # Extract modularization findings
    if 'modularization' in analysis_results:
        modularization = analysis_results['modularization']
        
        mod_findings = []
        
        # Current modules
        current_modules = modularization.get('current_modules', [])
        if current_modules:
            mod_findings.append(f"Identified {len(current_modules)} natural modules in the codebase")
        
        # High coupling
        high_coupling = modularization.get('high_coupling', [])
        if high_coupling:
            mod_findings.append(f"Found {len(high_coupling)} files with high coupling")
        
        # Circular dependencies
        circular_deps = modularization.get('circular_dependencies', [])
        if circular_deps:
            mod_findings.append(f"Detected {len(circular_deps)} circular dependencies")
        
        if mod_findings:
            summary_report['key_findings']['Code Modularization'] = mod_findings
        
        # Add recommendations from modularization analysis
        recommendations = modularization.get('recommendations', [])
        if recommendations:
            summary_report['recommendations']['Code Architecture'] = recommendations[:5]  # Top 5 recommendations
            
            # Add to priority areas if significant issues found
            if circular_deps or (high_coupling and len(high_coupling) > 3):
                summary_report['priority_areas'].append('Code Architecture')
    
    # Extract agent readiness findings
    if 'agent_readiness' in analysis_results:
        agent_readiness = analysis_results['agent_readiness']
        
        agent_findings = []
        
        # ML components
        ml_components = agent_readiness.get('ml_components', [])
        if ml_components:
            agent_findings.append(f"Found {len(ml_components)} machine learning components")
            
            # Agent libraries
            agent_libraries = agent_readiness.get('agent_libraries', [])
            if agent_libraries:
                agent_findings.append(f"Using {', '.join(agent_libraries)} agent-friendly libraries")
            else:
                agent_findings.append("No agent-specific libraries detected")
        else:
            agent_findings.append("No machine learning components detected")
        
        # Assessment scores
        assessment = agent_readiness.get('assessment', {})
        if assessment:
            avg_score = sum(assessment.values()) / len(assessment) if assessment else 0
            agent_findings.append(f"Average agent-readiness score: {avg_score:.1f}/10")
        
        if agent_findings:
            summary_report['key_findings']['Agent Readiness'] = agent_findings
        
        # Add recommendations from agent readiness analysis
        recommendations = agent_readiness.get('recommendations', [])
        if recommendations:
            summary_report['recommendations']['Agent Integration'] = recommendations[:5]  # Top 5 recommendations
            
            # Add to priority areas if ML components but low readiness
            if ml_components and (not agent_libraries or avg_score < 5):
                summary_report['priority_areas'].append('Agent Integration')
    
    # Extract workflow patterns findings
    if 'workflow_patterns' in analysis_results:
        workflow = analysis_results['workflow_patterns']
        
        workflow_findings = []
        
        # Workflows
        workflows = workflow.get('workflows', [])
        if workflows:
            # Count pattern occurrences
            pattern_counts = Counter()
            for wf in workflows:
                for pattern in wf.get('patterns', []):
                    pattern_counts[pattern] += 1
            
            if pattern_counts:
                top_patterns = pattern_counts.most_common(3)
                patterns_str = ", ".join(f"{pattern} ({count})" for pattern, count in top_patterns)
                workflow_findings.append(f"Main workflow patterns: {patterns_str}")
            else:
                workflow_findings.append(f"Found {len(workflows)} files with workflow components")
        
        # Entry points
        entry_points = workflow.get('entry_points', [])
        if entry_points:
            workflow_findings.append(f"Identified {len(entry_points)} workflow entry points")
        
        if workflow_findings:
            summary_report['key_findings']['Workflow Patterns'] = workflow_findings
        
        # Add recommendations from workflow analysis
        recommendations = workflow.get('standardization_recommendations', [])
        if recommendations:
            summary_report['recommendations']['Workflow Standardization'] = recommendations[:5]  # Top 5 recommendations
            
            # Add to priority areas if mixed patterns detected
            if pattern_counts and len(pattern_counts) > 2:
                summary_report['priority_areas'].append('Workflow Standardization')
    
    # Ensure recommendations for all areas
    if not summary_report['recommendations']:
        summary_report['recommendations'] = {
            'General Improvements': [
                "Implement comprehensive documentation for the codebase",
                "Add or improve test coverage across the repository",
                "Standardize code formatting and style",
                "Implement continuous integration and linting",
                "Review and update dependencies to latest versions"
            ]
        }
    
    # Sort priority areas by frequency of appearance in findings
    priority_counts = Counter(summary_report['priority_areas'])
    summary_report['priority_areas'] = [area for area, _ in priority_counts.most_common()]
    
    logger.info("Summary report generation complete.")
    return summary_report
