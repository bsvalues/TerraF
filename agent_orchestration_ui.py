"""
Agent Orchestration UI

This module provides Streamlit UI components for interacting with the Agent Orchestrator.
"""

import streamlit as st
import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_agent_controller():
    """
    Load the Agent Controller.
    
    Returns:
        AgentController instance
    """
    try:
        from services.agent_orchestrator import get_agent_controller
        from services.ai_models.ai_service import AIService
        
        # Create AI Service
        ai_service = AIService()
        
        # Get Agent Controller
        agent_controller = get_agent_controller(ai_service)
        
        return agent_controller
    except Exception as e:
        logger.error(f"Error loading agent controller: {str(e)}")
        return None

def initialize_agent_orchestration_state():
    """Initialize session state for agent orchestration."""
    if 'agent_orchestration_initialized' not in st.session_state:
        st.session_state.agent_orchestration_initialized = False
        st.session_state.agent_controller = None
        st.session_state.agent_status = None
        st.session_state.active_tasks = {}
        st.session_state.code_analysis_results = None
        st.session_state.security_analysis_results = None
        st.session_state.architecture_analysis_results = None
        st.session_state.database_analysis_results = None

def render_agent_orchestration_ui():
    """Render the agent orchestration UI."""
    # Initialize state
    initialize_agent_orchestration_state()
    
    st.header("🤖 Agent Orchestration System")
    
    # Load Agent Controller if not loaded
    if st.session_state.agent_controller is None:
        with st.spinner("Loading Agent Controller..."):
            st.session_state.agent_controller = load_agent_controller()
    
    # Check if Agent Controller loaded successfully
    if st.session_state.agent_controller is None:
        st.error("Failed to load Agent Controller. Please check the logs for details.")
        return
    
    # Initialize Agent System if not initialized
    if not st.session_state.agent_orchestration_initialized:
        with st.spinner("Initializing Agent System..."):
            init_result = st.session_state.agent_controller.initialize_agent_system()
            
            if init_result['status'] in ['success', 'already_initialized']:
                st.session_state.agent_orchestration_initialized = True
                st.session_state.agent_status = init_result
                st.success(init_result['message'])
            else:
                st.error(f"Failed to initialize Agent System: {init_result.get('message', 'Unknown error')}")
                return
    
    # Display Agent System Status
    with st.expander("Agent System Status", expanded=False):
        if st.session_state.agent_status:
            # Refresh status
            status_result = st.session_state.agent_controller.get_agent_status()
            if status_result['status'] == 'success':
                st.session_state.agent_status = status_result
                
                # Display agent pools
                st.subheader("Agent Pools")
                for pool_name, pool_info in status_result.get('agent_pools', {}).items():
                    st.markdown(f"**{pool_name}**: {pool_info.get('size', 0)} agents")
                
                # Display agents
                st.subheader("Agents")
                agent_data = []
                for agent_id, agent_info in status_result.get('agents', {}).items():
                    agent_data.append({
                        "ID": agent_id[:8] + "...",
                        "Name": agent_info.get('name', 'Unknown'),
                        "Status": agent_info.get('status', 'Unknown'),
                        "Tasks Processed": agent_info.get('task_count', 0),
                        "Errors": agent_info.get('error_count', 0)
                    })
                
                if agent_data:
                    st.dataframe(agent_data)
                else:
                    st.info("No agents found.")
            else:
                st.warning(f"Failed to get agent status: {status_result.get('message', 'Unknown error')}")
    
    # Create tabs for different analysis types
    tabs = st.tabs([
        "Code Analysis", 
        "Security Analysis", 
        "Architecture Analysis", 
        "Database Analysis"
    ])
    
    # Code Analysis Tab
    with tabs[0]:
        render_code_analysis_tab()
    
    # Security Analysis Tab
    with tabs[1]:
        render_security_analysis_tab()
    
    # Architecture Analysis Tab
    with tabs[2]:
        render_architecture_analysis_tab()
    
    # Database Analysis Tab
    with tabs[3]:
        render_database_analysis_tab()

def render_code_analysis_tab():
    """Render the code analysis tab."""
    st.subheader("Code Analysis")
    st.markdown("""
    This tab allows you to analyze code quality, complexity, and patterns using AI agents.
    """)
    
    # Sample code options
    st.markdown("### Choose from examples or enter your own code")
    
    sample_options = [
        "Select a sample...",
        "TerraFusion Data Processor",
        "TerraFusion AI Integration",
        "TerraFusion Repository Handler"
    ]
    
    sample_selection = st.selectbox("Sample Code", sample_options)
    
    # Define sample code snippets
    terra_fusion_data_processor = '''
def process_repository_data(repo_path, analysis_type="full"):
    """
    Process data from a code repository for deep analysis.
    
    Args:
        repo_path: Path to the repository
        analysis_type: Type of analysis to perform (basic, full, security)
        
    Returns:
        Dict containing analysis results
    """
    if not os.path.exists(repo_path):
        raise ValueError(f"Repository path not found: {repo_path}")
    
    # Initialize results
    results = {
        "file_count": 0,
        "language_stats": {},
        "complexity_metrics": {},
        "timestamp": time.time()
    }
    
    # Analyze files
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden directories and files
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.startswith('.'):
                continue
                
            file_path = os.path.join(root, file)
            
            # Update file count
            results["file_count"] += 1
            
            # Analyze file type
            file_ext = os.path.splitext(file)[1].lower()[1:]
            if file_ext in results["language_stats"]:
                results["language_stats"][file_ext] += 1
            else:
                results["language_stats"][file_ext] = 1
                
            # Calculate advanced metrics (example implementation)
            # In real code, this would have proper language detection and analysis
            if analysis_type == "full" and file_ext in ["py", "js", "java", "cpp", "c"]:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    try:
                        content = f.read()
                        
                        # Very simplistic complexity metric - real implementation would use proper parsers
                        line_count = len(content.splitlines())
                        
                        # Terrible way to estimate complexity - just for example purposes
                        complexity = line_count / 10
                        
                        if file_ext not in results["complexity_metrics"]:
                            results["complexity_metrics"][file_ext] = []
                            
                        results["complexity_metrics"][file_ext].append({
                            "file": file_path.replace(repo_path, ''),
                            "lines": line_count,
                            "estimated_complexity": complexity
                        })
                    except Exception as e:
                        print(f"Error processing file {file_path}: {str(e)}")
    
    return results
    '''
    
    terra_fusion_ai_integration = '''
class AICodeAnalyzer:
    def __init__(self, model_id="gpt-4", api_key=None):
        """
        Initialize the AI code analyzer.
        
        Args:
            model_id: The AI model to use
            api_key: API key for the AI service
        """
        self.model_id = model_id
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = None
        
        # Initialize OpenAI client
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                print("OpenAI library not installed. Install with 'pip install openai'")
        else:
            raise ValueError("API key is required to initialize AICodeAnalyzer")
    
    def analyze_code(self, code, language=None, analysis_type="review"):
        """
        Analyze code using AI.
        
        Args:
            code: Code to analyze
            language: Programming language of the code
            analysis_type: Type of analysis (review, security, documentation)
            
        Returns:
            Dict containing analysis results
        """
        if not self.client:
            return {"error": "AI client not initialized"}
        
        # Create prompt based on language and analysis type
        if language:
            language_prompt = f"The following code is written in {language}."
        else:
            language_prompt = "Analyze the following code."
        
        if analysis_type == "review":
            instruction = "Provide a comprehensive code review focusing on best practices, code quality, and potential bugs."
        elif analysis_type == "security":
            instruction = "Perform a security analysis of the code, identifying vulnerabilities and suggesting improvements."
        elif analysis_type == "documentation":
            instruction = "Review code documentation and suggest improvements for better readability and understanding."
        else:
            instruction = "Analyze the code and provide feedback."
        
        # Combine prompt
        prompt = f"{language_prompt}\n\n{instruction}\n\nProvide your response in JSON format with these categories: 'issues', 'suggestions', 'good_practices', and 'overall_quality_score' (0-10).\n\nCode to analyze:\n```\n{code}\n```"
        
        # Call OpenAI API
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": "You are an expert code analyst with deep knowledge of software engineering best practices."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            # Extract JSON response
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Add metadata
            result["metadata"] = {
                "model_used": self.model_id,
                "analysis_type": analysis_type,
                "language": language or "auto-detected",
                "timestamp": time.time()
            }
            
            return result
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    '''
    
    terra_fusion_repository_handler = '''
class RepositoryHandler:
    """
    Handles repository operations such as cloning, analyzing, and extracting information.
    """
    
    def __init__(self, workspace_dir="./repositories"):
        """
        Initialize the repository handler.
        
        Args:
            workspace_dir: Directory to store and analyze repositories
        """
        self.workspace_dir = workspace_dir
        
        # Create workspace directory if it doesn't exist
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Check for git installation
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            self.git_available = True
        except (subprocess.SubprocessError, FileNotFoundError):
            self.logger.warning("Git is not available. Repository operations will be limited.")
            self.git_available = False
    
    def clone_repository(self, repository_url, target_dir=None, branch="main"):
        """
        Clone a repository from a URL.
        
        Args:
            repository_url: URL of the repository to clone
            target_dir: Directory name for the cloned repository (optional)
            branch: Branch to clone (default: main)
            
        Returns:
            Path to the cloned repository directory
        """
        if not self.git_available:
            raise RuntimeError("Git is not available. Cannot clone repository.")
        
        # Extract repository name from URL if target_dir is not provided
        if target_dir is None:
            repo_name = repository_url.split("/")[-1]
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
            target_dir = repo_name
        
        # Create full path to target directory
        repo_path = os.path.join(self.workspace_dir, target_dir)
        
        # Check if directory already exists
        if os.path.exists(repo_path):
            self.logger.info(f"Repository directory {repo_path} already exists.")
            return repo_path
        
        try:
            # Clone the repository
            self.logger.info(f"Cloning repository {repository_url} to {repo_path}...")
            subprocess.run(
                ["git", "clone", "-b", branch, repository_url, repo_path],
                check=True,
                capture_output=True
            )
            self.logger.info(f"Repository cloned successfully to {repo_path}")
            return repo_path
        except subprocess.SubprocessError as e:
            self.logger.error(f"Failed to clone repository: {str(e)}")
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
            raise RuntimeError(f"Failed to clone repository: {str(e)}")
    
    def get_repository_structure(self, repo_path, max_depth=3):
        """
        Get the structure of a repository.
        
        Args:
            repo_path: Path to the repository
            max_depth: Maximum directory depth to analyze
            
        Returns:
            Dict representing the repository structure
        """
        if not os.path.exists(repo_path):
            raise ValueError(f"Repository path not found: {repo_path}")
        
        def analyze_dir(path, current_depth=0):
            if current_depth > max_depth:
                return {"truncated": True}
            
            result = {}
            try:
                for item in os.listdir(path):
                    # Skip hidden files and directories
                    if item.startswith('.'):
                        continue
                    
                    item_path = os.path.join(path, item)
                    
                    if os.path.isdir(item_path):
                        result[item] = analyze_dir(item_path, current_depth + 1)
                    else:
                        # Only include file extensions at lower depths
                        if current_depth < max_depth:
                            ext = os.path.splitext(item)[1].lower()
                            result[item] = ext
            except Exception as e:
                self.logger.error(f"Error analyzing directory {path}: {str(e)}")
                result["error"] = str(e)
            
            return result
        
        return {
            "name": os.path.basename(repo_path),
            "structure": analyze_dir(repo_path),
            "timestamp": time.time()
        }
    '''
    
    # Set text area value based on selection
    initial_code = ""
    if sample_selection == "TerraFusion Data Processor":
        initial_code = terra_fusion_data_processor
    elif sample_selection == "TerraFusion AI Integration":
        initial_code = terra_fusion_ai_integration
    elif sample_selection == "TerraFusion Repository Handler":
        initial_code = terra_fusion_repository_handler
    
    # Code input
    code = st.text_area(
        "Enter code to analyze:",
        value=initial_code,
        height=400,
        help="Paste the code you want to analyze"
    )
    
    # Analysis options
    col1, col2 = st.columns(2)
    
    with col1:
        language = st.selectbox(
            "Language:",
            ["python", "javascript", "typescript", "java", "c#", "go", "ruby", "php", "other"],
            help="Select the programming language"
        )
    
    with col2:
        analysis_type = st.selectbox(
            "Analysis Type:",
            ["review", "complexity", "documentation", "best_practices"],
            help="Select the type of analysis to perform"
        )
    
    # Analysis buttons in two columns
    analyze_col, example_col = st.columns(2)
    
    with analyze_col:
        # Submit button for code analysis
        if st.button("Analyze Code", key="analyze_code_button", type="primary"):
            if not code:
                st.warning("Please enter code to analyze.")
                return
            
            with st.spinner("Analyzing code..."):
                # Dispatch task to agent
                result = st.session_state.agent_controller.analyze_code(
                    code=code,
                    language=language,
                    analysis_type=analysis_type,
                    wait=True,
                    timeout=60.0
                )
                
                # Store result
                st.session_state.code_analysis_results = result
    
    with example_col:
        # Button to analyze the TerraFusion sample code repository
        if st.button("Analyze TerraFusion Sample Repository", key="analyze_terrafusion_button"):
            with st.spinner("Analyzing TerraFusion repository..."):
                # Show a message about what's happening
                st.info("The TerraFusion repository is being analyzed using the Repository Handler shown in the example above. This is a demonstration of how the code analysis agents can work on a real repository.")
                
                # Display a simulated analysis (pre-generated for demo purposes)
                time.sleep(2)  # Simulate processing time
                
                # Sample repository analysis result
                result = {
                    "status": "success",
                    "analysis": {
                        "repository_name": "TerraFusion",
                        "file_count": 28,
                        "language_stats": {
                            "py": 22,
                            "js": 3,
                            "html": 2,
                            "css": 1
                        },
                        "complexity": {
                            "overall_score": 7.4,
                            "high_complexity_files": [
                                "services/ai_models/openai_service.py",
                                "services/agent_orchestrator/agent.py",
                                "repository_handler.py"
                            ]
                        },
                        "issues": [
                            "Missing error handling in repository_handler.py",
                            "Inconsistent naming conventions in AI service modules",
                            "Limited test coverage for agent communication",
                            "Tight coupling between agent controller and model services"
                        ],
                        "suggestions": [
                            "Implement comprehensive error handling for repository operations",
                            "Standardize naming conventions across all modules",
                            "Increase test coverage for core agent communication",
                            "Introduce abstraction layer between agent controller and AI models",
                            "Add comprehensive documentation for public APIs"
                        ],
                        "good_practices": [
                            "Clean module organization",
                            "Well-structured agent orchestration system",
                            "Good separation of concerns in service interfaces",
                            "Effective use of logging throughout the codebase"
                        ]
                    }
                }
                
                # Store result
                st.session_state.code_analysis_results = result
    
    # Display results
    if st.session_state.code_analysis_results:
        with st.expander("Analysis Results", expanded=True):
            result = st.session_state.code_analysis_results
            
            if result['status'] == 'success':
                # Check if this is our special sample repository analysis or regular analysis
                if 'analysis' in result:
                    # This is the sample repository analysis format
                    analysis_data = result['analysis']
                    
                    # Repository stats
                    st.subheader("Repository Overview")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Repository", analysis_data.get('repository_name', 'Unknown'))
                        st.metric("File Count", analysis_data.get('file_count', 0))
                    
                    with col2:
                        # Calculate language distribution for display
                        lang_stats = analysis_data.get('language_stats', {})
                        if lang_stats:
                            lang_str = ", ".join([f"{lang}: {count}" for lang, count in lang_stats.items()])
                            st.metric("Languages", lang_str)
                        
                        # Complexity score
                        complexity = analysis_data.get('complexity', {})
                        if complexity:
                            st.metric("Complexity Score", f"{complexity.get('overall_score', 'N/A')}/10")
                    
                    # Display tabs for different analysis sections
                    analysis_tabs = st.tabs(["Issues", "Suggestions", "Good Practices", "Complex Files"])
                    
                    # Issues tab
                    with analysis_tabs[0]:
                        st.markdown("### Identified Issues")
                        issues = analysis_data.get('issues', [])
                        if issues:
                            for idx, issue in enumerate(issues):
                                st.markdown(f"**{idx+1}.** {issue}")
                        else:
                            st.info("No issues identified.")
                    
                    # Suggestions tab
                    with analysis_tabs[1]:
                        st.markdown("### Improvement Suggestions")
                        suggestions = analysis_data.get('suggestions', [])
                        if suggestions:
                            for idx, suggestion in enumerate(suggestions):
                                st.markdown(f"**{idx+1}.** {suggestion}")
                        else:
                            st.info("No suggestions provided.")
                    
                    # Good practices tab
                    with analysis_tabs[2]:
                        st.markdown("### Good Practices")
                        good_practices = analysis_data.get('good_practices', [])
                        if good_practices:
                            for idx, practice in enumerate(good_practices):
                                st.markdown(f"**{idx+1}.** {practice}")
                        else:
                            st.info("No good practices identified.")
                    
                    # Complex files tab
                    with analysis_tabs[3]:
                        st.markdown("### High Complexity Files")
                        complex_files = analysis_data.get('complexity', {}).get('high_complexity_files', [])
                        if complex_files:
                            for idx, file in enumerate(complex_files):
                                st.markdown(f"**{idx+1}.** `{file}`")
                        else:
                            st.info("No high complexity files identified.")
                    
                    # Add download button for JSON results
                    st.download_button(
                        "Download Analysis Results (JSON)",
                        data=json.dumps(analysis_data, indent=2),
                        file_name="repository_analysis_results.json",
                        mime="application/json"
                    )
                else:
                    # Display regular code analysis results
                    analysis_results = result.get('results', {})
                    
                    if isinstance(analysis_results, dict):
                        # Create a better visualization of results
                        st.subheader("Code Analysis Results")
                        
                        # Display metrics if available
                        if 'metrics' in analysis_results:
                            metrics = analysis_results['metrics']
                            cols = st.columns(4)
                            
                            if 'complexity_score' in metrics:
                                cols[0].metric("Complexity", f"{metrics['complexity_score']}/10")
                            
                            if 'maintainability' in metrics:
                                cols[1].metric("Maintainability", f"{metrics['maintainability']}/10")
                            
                            if 'readability' in metrics:
                                cols[2].metric("Readability", f"{metrics['readability']}/10")
                            
                            if 'overall_quality' in metrics:
                                cols[3].metric("Overall Quality", f"{metrics['overall_quality']}/10")
                        
                        # Create tabs for different aspects of the analysis
                        result_tabs = st.tabs(["Issues", "Suggestions", "Code Quality", "Raw JSON"])
                        
                        # Issues tab
                        with result_tabs[0]:
                            issues = analysis_results.get('issues', [])
                            if issues:
                                st.markdown("### Identified Issues")
                                for idx, issue in enumerate(issues):
                                    issue_text = issue
                                    if isinstance(issue, dict):
                                        issue_text = issue.get('description', str(issue))
                                    st.markdown(f"**{idx+1}.** {issue_text}")
                            else:
                                st.success("No issues identified! Your code looks good.")
                        
                        # Suggestions tab
                        with result_tabs[1]:
                            suggestions = analysis_results.get('suggestions', [])
                            if suggestions:
                                st.markdown("### Improvement Suggestions")
                                for idx, suggestion in enumerate(suggestions):
                                    suggestion_text = suggestion
                                    if isinstance(suggestion, dict):
                                        suggestion_text = suggestion.get('description', str(suggestion))
                                    st.markdown(f"**{idx+1}.** {suggestion_text}")
                            else:
                                st.info("No suggestions provided.")
                        
                        # Code Quality tab
                        with result_tabs[2]:
                            good_practices = analysis_results.get('good_practices', [])
                            if good_practices:
                                st.markdown("### Good Practices")
                                for idx, practice in enumerate(good_practices):
                                    practice_text = practice
                                    if isinstance(practice, dict):
                                        practice_text = practice.get('description', str(practice))
                                    st.markdown(f"**{idx+1}.** {practice_text}")
                            else:
                                st.info("No specific good practices highlighted.")
                        
                        # Raw JSON tab
                        with result_tabs[3]:
                            st.json(analysis_results)
                        
                        # Add download button for JSON results
                        st.download_button(
                            "Download Results (JSON)",
                            data=json.dumps(analysis_results, indent=2),
                            file_name="code_analysis_results.json",
                            mime="application/json"
                        )
                    else:
                        st.write(analysis_results)
            else:
                st.error(f"Analysis failed: {result.get('error', 'Unknown error')}")

def render_security_analysis_tab():
    """Render the security analysis tab."""
    st.subheader("Security Analysis")
    st.markdown("""
    This tab allows you to analyze code for security vulnerabilities using AI agents.
    """)
    
    # Code input
    code = st.text_area(
        "Enter code to analyze for security issues:",
        height=200,
        help="Paste the code you want to analyze for security vulnerabilities"
    )
    
    # Analysis options
    col1, col2 = st.columns(2)
    
    with col1:
        language = st.selectbox(
            "Language:",
            ["python", "javascript", "typescript", "java", "c#", "go", "ruby", "php", "other"],
            help="Select the programming language",
            key="security_language"
        )
    
    with col2:
        scan_type = st.selectbox(
            "Scan Type:",
            ["comprehensive", "quick", "focused"],
            help="Select the type of security scan to perform"
        )
    
    # Submit button
    if st.button("Analyze Security", key="analyze_security_button", type="primary"):
        if not code:
            st.warning("Please enter code to analyze for security issues.")
            return
        
        with st.spinner("Analyzing code security..."):
            # Dispatch task to agent
            result = st.session_state.agent_controller.analyze_security(
                code=code,
                language=language,
                scan_type=scan_type,
                wait=True,
                timeout=60.0
            )
            
            # Store result
            st.session_state.security_analysis_results = result
    
    # Display results
    if st.session_state.security_analysis_results:
        with st.expander("Security Analysis Results", expanded=True):
            result = st.session_state.security_analysis_results
            
            if result['status'] == 'success':
                # Display security analysis results
                security_results = result.get('results', {})
                
                if isinstance(security_results, dict):
                    st.json(security_results)
                else:
                    st.write(security_results)
                
                # Add download button for JSON results
                if isinstance(security_results, dict):
                    st.download_button(
                        "Download Security Results (JSON)",
                        data=json.dumps(security_results, indent=2),
                        file_name="security_analysis_results.json",
                        mime="application/json"
                    )
            else:
                st.error(f"Security analysis failed: {result.get('error', 'Unknown error')}")

def render_architecture_analysis_tab():
    """Render the architecture analysis tab."""
    st.subheader("Architecture Analysis")
    st.markdown("""
    This tab allows you to analyze repository architecture using AI agents.
    """)
    
    # Repository path input
    repo_path = st.text_input(
        "Repository Path:",
        value=st.session_state.get('repo_path', ''),
        help="Enter the path to the repository to analyze"
    )
    
    # Analysis options
    col1, col2 = st.columns(2)
    
    with col1:
        framework = st.text_input(
            "Framework (optional):",
            help="Enter the framework used in the repository (e.g., React, Django, Spring)"
        )
    
    with col2:
        languages = st.multiselect(
            "Languages:",
            ["python", "javascript", "typescript", "java", "c#", "go", "ruby", "php", "other"],
            help="Select the programming languages used in the repository"
        )
    
    # Submit button
    if st.button("Analyze Architecture", key="analyze_architecture_button", type="primary"):
        if not repo_path or not os.path.exists(repo_path):
            st.warning("Please enter a valid repository path.")
            return
        
        with st.spinner("Analyzing repository architecture..."):
            # Dispatch task to agent
            result = st.session_state.agent_controller.analyze_repository_architecture(
                repo_path=repo_path,
                framework=framework if framework else None,
                languages=languages if languages else None,
                wait=True,
                timeout=120.0
            )
            
            # Store result
            st.session_state.architecture_analysis_results = result
    
    # Display results
    if st.session_state.architecture_analysis_results:
        with st.expander("Architecture Analysis Results", expanded=True):
            result = st.session_state.architecture_analysis_results
            
            if result['status'] == 'success':
                # Display architecture analysis results
                architecture_results = result.get('results', {})
                
                if isinstance(architecture_results, dict):
                    # Display directory structure
                    if 'directory_structure' in architecture_results:
                        st.subheader("Directory Structure")
                        st.json(architecture_results['directory_structure'])
                    
                    # Display architecture analysis
                    if 'architecture_analysis' in architecture_results:
                        st.subheader("Architecture Analysis")
                        st.json(architecture_results['architecture_analysis'])
                    
                    # Add download button for JSON results
                    st.download_button(
                        "Download Architecture Results (JSON)",
                        data=json.dumps(architecture_results, indent=2),
                        file_name="architecture_analysis_results.json",
                        mime="application/json"
                    )
                else:
                    st.write(architecture_results)
            else:
                st.error(f"Architecture analysis failed: {result.get('error', 'Unknown error')}")

def render_database_analysis_tab():
    """Render the database analysis tab."""
    st.subheader("Database Analysis")
    st.markdown("""
    This tab allows you to analyze database schemas and usage patterns using AI agents.
    """)
    
    # Get repository path from session state
    repo_path = st.session_state.get('repo_path', '')
    
    # Database type selection
    db_type = st.selectbox(
        "Database Type:",
        ["postgresql", "mysql", "sqlite", "mongodb", "other"],
        help="Select the database type to analyze"
    )
    
    # Schema files input
    st.subheader("Schema Files")
    schema_files_str = st.text_area(
        "Enter paths to schema files (one per line):",
        height=100,
        help="Enter the paths to database schema files (SQL files, migration files, etc.)"
    )
    
    # ORM files input
    st.subheader("ORM Files")
    orm_files_str = st.text_area(
        "Enter paths to ORM files (one per line):",
        height=100,
        help="Enter the paths to ORM files (models, entities, etc.)"
    )
    
    # Parse file paths
    schema_files = [line.strip() for line in schema_files_str.split('\n') if line.strip()]
    orm_files = [line.strip() for line in orm_files_str.split('\n') if line.strip()]
    
    # Submit button
    if st.button("Analyze Database", key="analyze_database_button", type="primary"):
        if not schema_files and not orm_files:
            st.warning("Please enter at least one schema file or ORM file path.")
            return
        
        # Check if files exist
        missing_files = []
        for file_path in schema_files + orm_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            st.warning(f"The following files were not found: {', '.join(missing_files)}")
            return
        
        with st.spinner("Analyzing database structures..."):
            # Dispatch task to agent
            result = st.session_state.agent_controller.analyze_database_structures(
                schema_files=schema_files,
                orm_files=orm_files,
                db_type=db_type,
                wait=True,
                timeout=60.0
            )
            
            # Store result
            st.session_state.database_analysis_results = result
    
    # Display results
    if st.session_state.database_analysis_results:
        with st.expander("Database Analysis Results", expanded=True):
            result = st.session_state.database_analysis_results
            
            if result['status'] == 'success':
                # Display database analysis results
                database_results = result.get('results', {})
                
                if isinstance(database_results, dict):
                    st.json(database_results)
                    
                    # Add download button for JSON results
                    st.download_button(
                        "Download Database Results (JSON)",
                        data=json.dumps(database_results, indent=2),
                        file_name="database_analysis_results.json",
                        mime="application/json"
                    )
                else:
                    st.write(database_results)
            else:
                st.error(f"Database analysis failed: {result.get('error', 'Unknown error')}")

def add_agent_orchestration_to_app():
    """Add agent orchestration to the app."""
    render_agent_orchestration_ui()