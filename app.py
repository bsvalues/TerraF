import streamlit as st
import os
import tempfile
import shutil
import logging
import time
from pathlib import Path
from collections import defaultdict

# Import analyzer modules
from repository_handler import clone_repository, get_repository_structure
from code_analyzer import perform_code_review
from database_analyzer import analyze_database_structures
from modularization_analyzer import analyze_modularization
from agent_readiness_analyzer import analyze_agent_readiness
from workflow_analyzer import analyze_workflow_patterns
from report_generator import generate_summary_report
from utils import save_analysis_results, load_analysis_results
import visualizations

# Import agent system enhancement (conditionally, as it may not exist yet)
try:
    from app_enhancement import add_agent_system_to_app
    AGENT_SYSTEM_AVAILABLE = True
except ImportError:
    AGENT_SYSTEM_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define app title and initial state
st.set_page_config(
    page_title="Code Deep Dive Analyzer",
    page_icon="🔍",
    layout="wide"
)

def reset_app():
    """Reset app state to initial values"""
    # Only reset if not already analyzing
    if not st.session_state.get('analyzing', False):
        # Repository settings
        st.session_state.repo_url = ""
        st.session_state.repo_branch = "main"
        st.session_state.analyze_clicked = False
        st.session_state.repo_cloned = False
        st.session_state.repo_path = None
        
        # Analysis results
        st.session_state.analyze_code = True
        st.session_state.analyze_database = True
        st.session_state.analyze_modularization = True
        st.session_state.analyze_agent_readiness = True
        
        # Results storage
        st.session_state.analysis_results = {}
        st.session_state.repo_structure = None
        st.session_state.code_review = None
        st.session_state.database_analysis = None 
        st.session_state.modularization_analysis = None
        st.session_state.agent_readiness_analysis = None
        st.session_state.workflow_patterns_analysis = None
        st.session_state.summary_report = None
        
        # UI state
        st.session_state.current_tab = "Input"

def initialize_session_state():
    """Initialize session state if not already done"""
    if 'initialized' not in st.session_state:
        reset_app()
        st.session_state.initialized = True
        st.session_state.analyzing = False
        st.session_state.analysis_complete = False

def render_header():
    """Render the app header"""
    st.title("🔍 Code Deep Dive Analyzer")
    st.markdown("""
    Perform comprehensive analysis of the code in your repository to discover improvement opportunities
    and get detailed recommendations for enhancing various aspects of your codebase.
    """)

def render_input_tab():
    """Render the input tab for repository information"""
    st.header("Repository Information")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        repo_url = st.text_input(
            "GitHub Repository URL",
            value=st.session_state.get('repo_url', ''),
            placeholder="https://github.com/username/repository",
            help="Enter the URL of the GitHub repository you want to analyze"
        )
        
        if repo_url:
            st.session_state.repo_url = repo_url
    
    with col2:
        repo_branch = st.text_input(
            "Branch",
            value=st.session_state.get('repo_branch', 'main'),
            help="Enter the branch to analyze (default: main)"
        )
        
        if repo_branch:
            st.session_state.repo_branch = repo_branch
    
    st.header("Analysis Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.analyze_code = st.checkbox(
            "Code Review",
            value=st.session_state.get('analyze_code', True),
            help="Analyze code complexity, potential issues, and improvement opportunities"
        )
        
        st.session_state.analyze_database = st.checkbox(
            "Database Analysis",
            value=st.session_state.get('analyze_database', True),
            help="Analyze database structures, models, and suggest consolidations"
        )
    
    with col2:
        st.session_state.analyze_modularization = st.checkbox(
            "Modularization Analysis",
            value=st.session_state.get('analyze_modularization', True),
            help="Analyze code dependencies and suggest modularization improvements"
        )
        
        st.session_state.analyze_agent_readiness = st.checkbox(
            "Agent Readiness Evaluation",
            value=st.session_state.get('analyze_agent_readiness', True),
            help="Evaluate how well the codebase is prepared for AI agents integration"
        )
    
    st.markdown("---")
    
    analyze_col, reset_col = st.columns([1, 5])
    
    with analyze_col:
        if st.button("Analyze Repository", type="primary", disabled=st.session_state.get('analyzing', False)):
            st.session_state.analyze_clicked = True
    
    with reset_col:
        if st.button("Reset", disabled=st.session_state.get('analyzing', False)):
            reset_app()
            st.experimental_rerun()
    
    # Trigger analysis if button was clicked
    if st.session_state.get('analyze_clicked', False) and not st.session_state.get('analyzing', False):
        run_analysis()

def run_analysis():
    """Run the repository analysis"""
    if not st.session_state.repo_url:
        st.error("Please enter a valid GitHub repository URL")
        st.session_state.analyze_clicked = False
        return
    
    st.session_state.analyzing = True
    
    try:
        # Progress bar and status
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Phase 1: Clone repository
        status_text.text("Cloning repository...")
        
        # Create a temporary directory for the repository
        temp_dir = tempfile.mkdtemp()
        
        try:
            repo_path = clone_repository(
                st.session_state.repo_url,
                st.session_state.repo_branch,
                temp_dir
            )
            
            st.session_state.repo_path = repo_path
            st.session_state.repo_cloned = True
            
            progress_bar.progress(10)
            status_text.text("Repository cloned successfully! Analyzing repository structure...")
            
            # Phase 2: Analyze repository structure
            repo_structure = get_repository_structure(repo_path)
            st.session_state.repo_structure = repo_structure
            st.session_state.analysis_results['repository_structure'] = repo_structure
            
            progress_bar.progress(20)
            
            # Proceed with selected analyses
            if st.session_state.analyze_code:
                status_text.text("Performing code review...")
                code_review = perform_code_review(repo_path)
                st.session_state.code_review = code_review
                st.session_state.analysis_results['code_review'] = code_review
                progress_bar.progress(40)
                
            if st.session_state.analyze_database:
                status_text.text("Analyzing database structures...")
                database_analysis = analyze_database_structures(repo_path)
                st.session_state.database_analysis = database_analysis
                st.session_state.analysis_results['database_analysis'] = database_analysis
                progress_bar.progress(60)
                
            if st.session_state.analyze_modularization:
                status_text.text("Analyzing modularization opportunities...")
                modularization_analysis = analyze_modularization(repo_path)
                st.session_state.modularization_analysis = modularization_analysis
                st.session_state.analysis_results['modularization'] = modularization_analysis
                progress_bar.progress(80)
                
            if st.session_state.analyze_agent_readiness:
                status_text.text("Evaluating agent readiness...")
                agent_readiness_analysis = analyze_agent_readiness(repo_path)
                st.session_state.agent_readiness_analysis = agent_readiness_analysis
                st.session_state.analysis_results['agent_readiness'] = agent_readiness_analysis
                progress_bar.progress(85)
            
            # Analyze workflow patterns
            status_text.text("Analyzing workflow patterns...")
            workflow_patterns_analysis = analyze_workflow_patterns(repo_path)
            st.session_state.workflow_patterns_analysis = workflow_patterns_analysis
            st.session_state.analysis_results['workflow_patterns'] = workflow_patterns_analysis
            progress_bar.progress(90)
            
            # Generate summary report
            status_text.text("Generating summary report...")
            summary_report = generate_summary_report(st.session_state.analysis_results)
            st.session_state.summary_report = summary_report
            
            # Mark analysis as complete
            progress_bar.progress(100)
            status_text.text("Analysis complete!")
            time.sleep(1)
            status_text.empty()
            progress_bar.empty()
            
            st.session_state.analysis_complete = True
            st.session_state.current_tab = "Summary"
            
        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
            logger.error(f"Analysis error: {str(e)}")
        finally:
            # Clean up temporary directory, but keep the state for display
            # This prevents file access issues during the Streamlit session
            # shutil.rmtree(temp_dir)
            pass
    
    finally:
        st.session_state.analyzing = False
        st.session_state.analyze_clicked = False

def render_summary_tab():
    """Render the summary tab with analysis results"""
    if not st.session_state.get('analysis_complete', False):
        st.info("No analysis has been performed yet. Please enter a repository URL and click 'Analyze Repository'.")
        return
    
    st.header("Analysis Summary")
    
    # Display repository info
    repo_url = st.session_state.repo_url
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    
    st.markdown(f"""
    ### Repository: [{repo_name}]({repo_url})
    Branch: `{st.session_state.repo_branch}`
    """)
    
    # Display key findings from summary report
    summary_report = st.session_state.summary_report
    if summary_report and 'key_findings' in summary_report:
        key_findings = summary_report['key_findings']
        
        if key_findings:
            st.subheader("Key Findings")
            
            # Create columns for key findings
            col1, col2 = st.columns(2)
            
            # Distribute findings across columns
            findings_list = list(key_findings.items())
            half_length = len(findings_list) // 2 + len(findings_list) % 2
            
            for i, (category, findings) in enumerate(findings_list):
                with col1 if i < half_length else col2:
                    with st.expander(category, expanded=True):
                        for finding in findings:
                            st.markdown(f"• {finding}")
    
    # Display recommendations
    if summary_report and 'recommendations' in summary_report:
        recommendations = summary_report['recommendations']
        
        if recommendations:
            st.subheader("Recommendations")
            
            recommendation_tabs = st.tabs(list(recommendations.keys()))
            
            for i, (category, recs) in enumerate(recommendations.items()):
                with recommendation_tabs[i]:
                    for j, rec in enumerate(recs):
                        st.markdown(f"{j+1}. {rec}")
    
    # Add export option
    st.markdown("---")
    if st.button("Export Analysis Results"):
        # Save results to a file
        results_file = save_analysis_results(st.session_state.analysis_results)
        
        if results_file:
            with open(results_file, 'rb') as f:
                st.download_button(
                    label="Download Analysis Results (JSON)",
                    data=f,
                    file_name=f"code_analysis_{repo_name}.json",
                    mime="application/json"
                )

def render_repo_structure_tab():
    """Render the repository structure tab"""
    if not st.session_state.get('repo_structure'):
        st.info("Repository structure analysis has not been performed yet.")
        return
    
    st.header("Repository Structure Analysis")
    
    repo_structure = st.session_state.repo_structure
    
    # Display basic statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Files", repo_structure.get('file_count', 0))
    
    with col2:
        st.metric("Directories", repo_structure.get('directory_count', 0))
    
    with col3:
        deepest_nesting = repo_structure.get('deepest_nesting', 0)
        st.metric("Deepest Nesting", deepest_nesting)
    
    # Display file types
    st.subheader("File Types Distribution")
    
    # Create visualization of file types
    file_types_fig = visualizations.visualize_repository_structure(repo_structure)
    st.plotly_chart(file_types_fig, use_container_width=True)
    
    # Display top-level directories
    st.subheader("Top-Level Directories")
    
    top_dirs = repo_structure.get('top_level_dirs', [])
    if top_dirs:
        for directory in sorted(top_dirs):
            st.markdown(f"• `{directory}`")
    else:
        st.info("No top-level directories found.")
    
    # Display largest files
    st.subheader("Largest Files")
    
    largest_files = repo_structure.get('largest_files', [])
    if largest_files:
        largest_files_data = []
        for file in largest_files:
            # Convert size to readable format
            size_bytes = file.get('size', 0)
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            
            largest_files_data.append({
                "File": file.get('path', 'Unknown'),
                "Size": size_str
            })
        
        import pandas as pd
        st.dataframe(pd.DataFrame(largest_files_data))
    else:
        st.info("No file size information available.")

def render_code_review_tab():
    """Render the code review tab"""
    if not st.session_state.get('code_review'):
        st.info("Code review analysis has not been performed yet.")
        return
    
    st.header("Code Review Analysis")
    
    code_review = st.session_state.code_review
    
    # Display metrics
    metrics = code_review.get('metrics', {})
    if metrics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Lines of Code", metrics.get('total_loc', 0))
        
        with col2:
            st.metric("Functions", metrics.get('total_functions', 0))
        
        with col3:
            st.metric("Classes", metrics.get('total_classes', 0))
        
        with col4:
            avg_complexity = metrics.get('average_complexity', 0)
            st.metric("Avg. Complexity", f"{avg_complexity:.2f}")
    
    # Display code complexity visualization
    st.subheader("Code Complexity Analysis")
    
    complexity_fig = visualizations.visualize_code_complexity(code_review)
    st.plotly_chart(complexity_fig, use_container_width=True)
    
    # Display files with issues
    st.subheader("Files with Issues")
    
    files_with_issues = code_review.get('files_with_issues', [])
    if files_with_issues:
        # Group issues by file
        for file_issue in files_with_issues:
            with st.expander(f"{file_issue.get('file', 'Unknown')} ({file_issue.get('issue_count', 0)} issues)"):
                for detail in file_issue.get('details', []):
                    st.markdown(f"• {detail}")
    else:
        st.info("No significant code issues found.")
    
    # Display improvement opportunities
    st.subheader("Improvement Opportunities")
    
    opportunities = code_review.get('improvement_opportunities', {})
    if opportunities:
        opportunity_tabs = st.tabs(list(opportunities.keys()))
        
        for i, (category, recs) in enumerate(opportunities.items()):
            with opportunity_tabs[i]:
                for rec in recs:
                    st.markdown(f"• {rec}")
    else:
        st.info("No improvement opportunities identified.")
    
    # Display duplications if any
    duplications = code_review.get('duplications', [])
    if duplications:
        st.subheader("Potential Code Duplications")
        
        for dup in duplications:
            st.markdown(f"""
            **Duplicate code found in:**
            - {dup.get('file1', 'Unknown')} (line {dup.get('start_line1', 0)})
            - {dup.get('file2', 'Unknown')} (line {dup.get('start_line2', 0)})
            
            Duplicate block length: {dup.get('lines', 0)} lines
            """)
    
def render_database_tab():
    """Render the database analysis tab"""
    if not st.session_state.get('database_analysis'):
        st.info("Database analysis has not been performed yet.")
        return
    
    st.header("Database Structure Analysis")
    
    db_analysis = st.session_state.database_analysis
    
    # Display database files
    db_files = db_analysis.get('database_files', [])
    if db_files:
        st.subheader(f"Database Files ({len(db_files)})")
        
        for file in db_files:
            st.markdown(f"• `{file.get('path', 'Unknown')}`")
    else:
        st.info("No database-related files found in the repository.")
        return
    
    # Display database models
    models = db_analysis.get('database_models', {})
    if models:
        st.subheader(f"Database Models ({len(models)})")
        
        # Create visualization of database relations
        relations_fig = visualizations.visualize_database_relations(db_analysis)
        st.plotly_chart(relations_fig, use_container_width=True)
        
        # Display detailed model information
        for model_name, model_info in models.items():
            with st.expander(f"Model: {model_name}"):
                # Display ORM type
                orm_type = model_info.get('orm', 'unknown').upper()
                st.markdown(f"**ORM Framework:** {orm_type}")
                
                # Display table name if available
                if 'tablename' in model_info:
                    st.markdown(f"**Table Name:** `{model_info['tablename']}`")
                
                # Display fields
                fields = model_info.get('fields', {})
                if fields:
                    st.markdown("**Fields:**")
                    
                    field_rows = []
                    for field_name, field_info in fields.items():
                        field_type = field_info.get('type', 'unknown')
                        field_args = field_info.get('args', {})
                        
                        # Extract important field attributes
                        attributes = []
                        if 'primary_key' in field_args and field_args['primary_key']:
                            attributes.append("Primary Key")
                        if 'unique' in field_args and field_args['unique']:
                            attributes.append("Unique")
                        if 'nullable' in field_args and not field_args['nullable']:
                            attributes.append("Not Null")
                        
                        field_rows.append({
                            "Field": field_name,
                            "Type": field_type,
                            "Attributes": ", ".join(attributes)
                        })
                    
                    import pandas as pd
                    st.dataframe(pd.DataFrame(field_rows))
                
                # Display relationships if available
                relationships = model_info.get('relationships', {})
                if relationships:
                    st.markdown("**Relationships:**")
                    
                    for rel_name, rel_info in relationships.items():
                        target = rel_info.get('target', 'unknown')
                        st.markdown(f"• `{rel_name}` → `{target}`")
    
    # Display raw SQL queries if any
    sql_queries = db_analysis.get('raw_sql_queries', [])
    if sql_queries:
        st.subheader(f"Raw SQL Queries ({len(sql_queries)})")
        
        for query in sql_queries:
            with st.expander(f"SQL Query in {query.get('file', 'Unknown')}"):
                st.code(query.get('query', ''), language="sql")
    
    # Display redundancies if any
    redundancies = db_analysis.get('redundancies', [])
    if redundancies:
        st.subheader(f"Potential Database Redundancies ({len(redundancies)})")
        
        for redundancy in redundancies:
            redundancy_type = redundancy.get('type', 'unknown').replace('_', ' ').title()
            
            if redundancy_type == "Similar Models":
                similarity = redundancy.get('similarity', 0) * 100
                common_fields = redundancy.get('common_fields', [])
                
                st.markdown(f"""
                **Similar Models:**
                - {redundancy.get('model1', 'Unknown')}
                - {redundancy.get('model2', 'Unknown')}
                
                Similarity: {similarity:.1f}%
                
                Common fields: {', '.join(f'`{field}`' for field in common_fields)}
                """)
            elif redundancy_type == "Inconsistent Field Types":
                st.markdown(f"""
                **Inconsistent Field Types:**
                Field `{redundancy.get('field', 'unknown')}` has different types in:
                - {redundancy.get('models', ['Unknown'])[0]}: {redundancy.get('types', ['unknown'])[0]}
                - {redundancy.get('models', ['Unknown', 'Unknown'])[1]}: {redundancy.get('types', ['unknown', 'unknown'])[1]}
                """)
    
    # Display consolidation recommendations
    recommendations = db_analysis.get('consolidation_recommendations', [])
    if recommendations:
        st.subheader("Database Improvement Recommendations")
        
        for i, rec in enumerate(recommendations):
            st.markdown(f"{i+1}. {rec}")

def render_modularization_tab():
    """Render the modularization analysis tab"""
    if not st.session_state.get('modularization_analysis'):
        st.info("Modularization analysis has not been performed yet.")
        return
    
    st.header("Code Modularization Analysis")
    
    modularization = st.session_state.modularization_analysis
    
    # Display dependency graph visualization
    st.subheader("Module Dependency Graph")
    
    dependency_fig = visualizations.visualize_modularization_opportunities(modularization)
    st.plotly_chart(dependency_fig, use_container_width=True)
    
    # Display natural modules
    modules = modularization.get('current_modules', [])
    if modules:
        st.subheader(f"Natural Module Clusters ({len(modules)})")
        
        for module in modules:
            with st.expander(f"Module: {module.get('name', 'Unknown')} ({module.get('size', 0)} files)"):
                for file in module.get('files', []):
                    st.markdown(f"• `{file}`")
    
    # Display highly coupled files
    high_coupling = modularization.get('highly_coupled_files', [])
    if high_coupling:
        st.subheader(f"Highly Coupled Files ({len(high_coupling)})")
        
        coupling_data = []
        for file in high_coupling:
            coupling_data.append({
                "File": file.get('file', 'Unknown'),
                "Incoming Dependencies": file.get('in_degree', 0),
                "Outgoing Dependencies": file.get('out_degree', 0),
                "Total": file.get('total_degree', 0)
            })
        
        import pandas as pd
        st.dataframe(pd.DataFrame(coupling_data).sort_values(by="Total", ascending=False))
    
    # Display circular dependencies
    cycles = modularization.get('circular_dependencies', [])
    if cycles:
        st.subheader(f"Circular Dependencies ({len(cycles)})")
        
        for i, cycle in enumerate(cycles):
            st.markdown(f"**Cycle {i+1}:** {' → '.join(cycle)} → {cycle[0]}")
    
    # Display recommendations
    recommendations = modularization.get('recommendations', [])
    if recommendations:
        st.subheader("Modularization Recommendations")
        
        for i, rec in enumerate(recommendations):
            st.markdown(f"{i+1}. {rec}")

def render_agent_readiness_tab():
    """Render the agent readiness evaluation tab"""
    if not st.session_state.get('agent_readiness_analysis'):
        st.info("Agent readiness analysis has not been performed yet.")
        return
    
    st.header("AI Agent Readiness Evaluation")
    
    agent_readiness = st.session_state.agent_readiness_analysis
    
    # Display ML components
    ml_components = agent_readiness.get('ml_components', [])
    if ml_components:
        st.subheader(f"Machine Learning Components ({len(ml_components)})")
        
        for component in ml_components:
            with st.expander(f"ML Component: {component.get('file', 'Unknown')}"):
                # Display ML libraries
                ml_libs = component.get('ml_libraries', [])
                if ml_libs:
                    st.markdown(f"**ML Libraries:** {', '.join(ml_libs)}")
                
                # Display agent libraries
                agent_libs = component.get('agent_libraries', [])
                if agent_libs:
                    st.markdown(f"**Agent Libraries:** {', '.join(agent_libs)}")
                
                # Display model classes
                model_classes = component.get('model_classes', [])
                if model_classes:
                    st.markdown("**Model Classes:**")
                    for cls in model_classes:
                        st.markdown(f"• `{cls}`")
                
                # Display ML functions
                ml_functions = component.get('ml_functions', [])
                if ml_functions:
                    st.markdown("**ML Functions:**")
                    for func in ml_functions:
                        st.markdown(f"• `{func}`")
                
                # Display hyperparameters
                hyperparameters = component.get('hyperparameters', [])
                if hyperparameters:
                    st.markdown("**Hyperparameters:**")
                    for param in hyperparameters:
                        st.markdown(f"• `{param}`")
    else:
        st.info("No machine learning components found in the repository.")
    
    # Display agent readiness assessment
    assessment = agent_readiness.get('assessment', [])
    if assessment:
        st.subheader("Agent Readiness Assessment")
        
        # Calculate average score
        scores = [item.get('score', 0) for item in assessment]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Display score gauge
        import plotly.graph_objects as go
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Agent Readiness Score"},
            gauge={
                'axis': {'range': [0, 10]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 3], 'color': "lightcoral"},
                    {'range': [3, 7], 'color': "lightyellow"},
                    {'range': [7, 10], 'color': "lightgreen"},
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': avg_score
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display individual component scores
        st.markdown("### Component Scores")
        
        import pandas as pd
        assessment_data = []
        for item in assessment:
            assessment_data.append({
                "File": item.get('file', 'Unknown'),
                "Score": item.get('score', 0)
            })
        
        st.dataframe(pd.DataFrame(assessment_data).sort_values(by="Score", ascending=False))
    
    # Display agent libraries used
    agent_libs = agent_readiness.get('agent_libraries', [])
    if agent_libs:
        st.subheader("Agent Libraries Used")
        
        for lib in agent_libs:
            st.markdown(f"• {lib}")
    
    # Display recommendations
    recommendations = agent_readiness.get('recommendations', [])
    if recommendations:
        st.subheader("Agent Readiness Recommendations")
        
        for i, rec in enumerate(recommendations):
            st.markdown(f"{i+1}. {rec}")

def render_workflow_tab():
    """Render the workflow patterns analysis tab"""
    if not st.session_state.get('workflow_patterns_analysis'):
        st.info("Workflow patterns analysis has not been performed yet.")
        return
    
    st.header("Workflow Patterns Analysis")
    
    workflow_analysis = st.session_state.workflow_patterns_analysis
    
    # Display workflow files
    workflows = workflow_analysis.get('workflows', [])
    if workflows:
        st.subheader(f"Workflow Components ({len(workflows)})")
        
        # Group workflows by pattern
        patterns_to_files = defaultdict(list)
        
        for workflow in workflows:
            file_path = workflow.get('file', 'Unknown')
            for pattern in workflow.get('patterns', set()):
                patterns_to_files[pattern].append(file_path)
        
        # Create tabs for each pattern
        if patterns_to_files:
            pattern_tabs = st.tabs(list(patterns_to_files.keys()))
            
            for i, (pattern, files) in enumerate(patterns_to_files.items()):
                with pattern_tabs[i]:
                    pretty_pattern = pattern.replace('_', ' ').title()
                    st.markdown(f"**{pretty_pattern}** pattern found in {len(files)} files")
                    
                    for file in files:
                        st.markdown(f"• `{file}`")
        else:
            for workflow in workflows:
                file_path = workflow.get('file', 'Unknown')
                entry_points = len(workflow.get('entry_points', []))
                operations = len(workflow.get('operations', []))
                
                st.markdown(f"• `{file_path}` - {entry_points} entry points, {operations} workflow operations")
    else:
        st.info("No workflow components found in the repository.")
    
    # Display entry points
    entry_points = workflow_analysis.get('entry_points', [])
    if entry_points:
        st.subheader(f"Workflow Entry Points ({len(entry_points)})")
        
        # Group by entry point type
        entry_types = defaultdict(list)
        for entry in entry_points:
            entry_type = entry.get('type', 'unknown')
            entry_types[entry_type].append(entry)
        
        # Display by type
        for entry_type, entries in entry_types.items():
            pretty_type = entry_type.replace('_', ' ').title()
            with st.expander(f"{pretty_type} ({len(entries)})"):
                for entry in entries:
                    st.markdown(f"• `{entry.get('name', 'Unknown')}` in line {entry.get('line', 0)}")
    
    # Display identified patterns
    patterns = workflow_analysis.get('patterns', [])
    if patterns:
        st.subheader("Identified Workflow Patterns")
        
        # Create a bar chart of pattern frequencies
        import pandas as pd
        pattern_data = []
        
        for pattern in patterns:
            pattern_data.append({
                "Pattern": pattern.get('name', 'unknown').replace('_', ' ').title(),
                "Count": pattern.get('count', 0)
            })
        
        pattern_df = pd.DataFrame(pattern_data)
        
        import plotly.express as px
        fig = px.bar(pattern_df, x='Pattern', y='Count', 
                   title='Workflow Pattern Distribution',
                   labels={'Pattern': 'Pattern Type', 'Count': 'Frequency'},
                   color='Count')
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Display recommendations
    recommendations = workflow_analysis.get('standardization_recommendations', [])
    if recommendations:
        st.subheader("Workflow Standardization Recommendations")
        
        for i, rec in enumerate(recommendations):
            st.markdown(f"{i+1}. {rec}")

def main():
    """Main application function"""
    initialize_session_state()
    
    # Check if agent system enhancement is available and should be used
    if AGENT_SYSTEM_AVAILABLE and st.session_state.get('use_agent_system', True):
        # Add the agent system UI to the app
        add_agent_system_to_app()
        
        # The add_agent_system_to_app function will handle rendering the original app
        # in the first tab, so we can return here
        return
    
    # Original app rendering (used if agent system is not available)
    render_header()
    
    # Define tabs
    tabs = ["Input", "Summary", "Repository Structure", "Code Review", "Database Analysis", 
            "Modularization Analysis", "Agent Readiness", "Workflow Patterns"]
    
    # Set current tab from session state if available
    current_tab = st.session_state.get('current_tab', 'Input')
    if current_tab not in tabs:
        current_tab = 'Input'
    
    # Get current tab index
    current_tab_idx = tabs.index(current_tab)
    
    # Display tabs
    tab_items = st.tabs(tabs)
    
    # Render appropriate content for the active tab
    with tab_items[0]:  # Input
        if current_tab == 'Input':
            render_input_tab()
    
    with tab_items[1]:  # Summary
        if current_tab == 'Summary':
            render_summary_tab()
    
    with tab_items[2]:  # Repository Structure
        if current_tab == 'Repository Structure':
            render_repo_structure_tab()
    
    with tab_items[3]:  # Code Review
        if current_tab == 'Code Review':
            render_code_review_tab()
    
    with tab_items[4]:  # Database Analysis
        if current_tab == 'Database Analysis':
            render_database_tab()
    
    with tab_items[5]:  # Modularization Analysis
        if current_tab == 'Modularization Analysis':
            render_modularization_tab()
    
    with tab_items[6]:  # Agent Readiness
        if current_tab == 'Agent Readiness':
            render_agent_readiness_tab()
            
    with tab_items[7]:  # Workflow Patterns
        if current_tab == 'Workflow Patterns':
            render_workflow_tab()
    
    # Handle tab switching
    if st.session_state.get('current_tab') != tabs[current_tab_idx]:
        st.session_state.current_tab = tabs[current_tab_idx]

if __name__ == "__main__":
    main()