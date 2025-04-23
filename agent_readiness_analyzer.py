import os
import re
import logging
import ast
import json
from collections import defaultdict
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Patterns for identifying machine learning files and code
ML_FILE_PATTERNS = [
    r'.*model\.py$',
    r'.*train\.py$',
    r'.*predict\.py$',
    r'.*inference\.py$',
    r'.*classifier\.py$',
    r'.*regressor\.py$',
    r'.*neural_network\.py$',
    r'.*ml_.*\.py$',
    r'.*ai_.*\.py$',
    r'.*algorithm\.py$',
    r'.*learning\.py$',
]

# ML libraries to detect
ML_LIBRARIES = [
    'tensorflow', 'keras', 'torch', 'sklearn', 'scikit-learn', 
    'xgboost', 'lightgbm', 'catboost', 'nltk', 'spacy',
    'gensim', 'transformers', 'huggingface', 'fastai', 'mxnet',
    'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn',
    'opencv', 'cv2'
]

# Agent-related libraries and frameworks
AGENT_LIBRARIES = [
    'langchain', 'llama_index', 'openai', 'anthropic', 'chromadb',
    'autogen', 'crewai', 'ray', 'rllib', 'gymnasium', 'gym',
    'stable_baselines3', 'transformers', 'sentence_transformers'
]

class MLComponentVisitor(ast.NodeVisitor):
    """AST visitor for identifying ML components in Python code"""
    
    def __init__(self):
        self.ml_components = {
            'imports': [],
            'classes': [],
            'functions': [],
            'hyperparameters': []
        }
    
    def visit_Import(self, node):
        """Process 'import x' statements"""
        for name in node.names:
            module = name.name.split('.')[0]  # Get the base module name
            if any(module == lib or lib in module for lib in ML_LIBRARIES + AGENT_LIBRARIES):
                self.ml_components['imports'].append({
                    'type': 'import',
                    'module': name.name,
                    'alias': name.asname,
                    'line': node.lineno
                })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Process 'from x import y' statements"""
        if node.module:
            module = node.module.split('.')[0]  # Get the base module name
            if any(module == lib or lib in module for lib in ML_LIBRARIES + AGENT_LIBRARIES):
                for name in node.names:
                    self.ml_components['imports'].append({
                        'type': 'from_import',
                        'module': node.module,
                        'name': name.name,
                        'alias': name.asname,
                        'line': node.lineno
                    })
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Process class definitions"""
        # Check if this might be an ML model class
        ml_class = False
        
        # Check for ML-related base classes
        for base in node.bases:
            if isinstance(base, ast.Name):
                if hasattr(base, 'id') and base.id in ['Model', 'Estimator', 'BaseEstimator', 'Classifier', 'Regressor']:
                    ml_class = True
                    break
            elif isinstance(base, ast.Attribute):
                if hasattr(base, 'attr') and base.attr in ['Model', 'Estimator', 'BaseEstimator', 'Classifier', 'Regressor']:
                    ml_class = True
                    break
        
        # Check for ML-related method names
        if not ml_class:
            ml_methods = ['fit', 'predict', 'transform', 'train', 'evaluate', 'forward']
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name in ml_methods:
                    ml_class = True
                    break
        
        if ml_class:
            self.ml_components['classes'].append({
                'name': node.name,
                'line': node.lineno
            })
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Process function definitions"""
        # Check if this might be an ML-related function
        ml_function = False
        
        # Check function name
        ml_function_names = ['train', 'predict', 'fit', 'evaluate', 'transform', 'process', 'preprocess', 'encode', 'decode']
        if any(name in node.name.lower() for name in ml_function_names):
            ml_function = True
        
        # Check for ML-related operations within the function
        if not ml_function:
            for item in ast.walk(node):
                if isinstance(item, ast.Call) and hasattr(item, 'func'):
                    if hasattr(item.func, 'id') and item.func.id in ['fit', 'predict', 'transform', 'train', 'evaluate']:
                        ml_function = True
                        break
                    elif hasattr(item.func, 'attr') and item.func.attr in ['fit', 'predict', 'transform', 'train', 'evaluate']:
                        ml_function = True
                        break
        
        if ml_function:
            self.ml_components['functions'].append({
                'name': node.name,
                'line': node.lineno
            })
        
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Process assignments to find hyperparameters"""
        # Check for common hyperparameter names
        hyperparameter_patterns = [
            'learning_rate', 'lr', 'batch_size', 'epochs', 'n_estimators', 
            'max_depth', 'num_layers', 'hidden_size', 'dropout', 'alpha',
            'beta', 'gamma', 'lambda', 'regularization', 'weight_decay',
            'momentum', 'optimizer', 'activation', 'layers', 'units'
        ]
        
        for target in node.targets:
            if isinstance(target, ast.Name):
                if any(pattern in target.id.lower() for pattern in hyperparameter_patterns):
                    value = None
                    if isinstance(node.value, ast.Num):
                        value = node.value.n
                    elif isinstance(node.value, ast.Str):
                        value = node.value.s
                    
                    self.ml_components['hyperparameters'].append({
                        'name': target.id,
                        'value': value,
                        'line': node.lineno
                    })
        
        self.generic_visit(node)

def find_ml_files(repo_path):
    """
    Find files that are likely related to machine learning
    
    Parameters:
    - repo_path: Path to the cloned repository
    
    Returns:
    - list: Machine learning-related files
    """
    ml_files = []
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            # Skip hidden files
            if file.startswith('.'):
                continue
                
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, repo_path)
            
            # Skip hidden directories
            if any(part.startswith('.') for part in Path(rel_path).parts):
                continue
            
            # Check if the file matches ML patterns
            if any(re.match(pattern, rel_path) for pattern in ML_FILE_PATTERNS):
                ml_files.append(rel_path)
            elif file.endswith('.py'):
                # For Python files, check the content for ML-related code
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read().lower()
                        # Check for ML library imports
                        if any(f"import {lib}" in content or f"from {lib}" in content 
                              for lib in ML_LIBRARIES + AGENT_LIBRARIES):
                            ml_files.append(rel_path)
                except Exception:
                    pass
    
    return ml_files

def analyze_ml_file(repo_path, file_path):
    """
    Analyze a Python file for ML components
    
    Parameters:
    - repo_path: Path to the repository
    - file_path: Relative path to the file
    
    Returns:
    - dict: ML components found in the file
    """
    full_path = os.path.join(repo_path, file_path)
    
    try:
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content, filename=file_path)
        
        # Visit nodes and collect ML components
        visitor = MLComponentVisitor()
        visitor.visit(tree)
        
        return visitor.ml_components
    except Exception as e:
        logger.error(f"Error analyzing ML file {file_path}: {str(e)}")
        return {
            'imports': [],
            'classes': [],
            'functions': [],
            'hyperparameters': []
        }

def evaluate_agent_readiness(ml_components):
    """
    Evaluate the agent-readiness of ML components
    
    Parameters:
    - ml_components: Dictionary of ML components found in the codebase
    
    Returns:
    - dict: Assessment of agent-readiness
    """
    assessment = {}
    
    # Check if any agent-specific libraries are used
    agent_libs_used = []
    for file_path, components in ml_components.items():
        for imp in components['imports']:
            module = imp['module']
            if any(lib in module.lower() for lib in AGENT_LIBRARIES):
                agent_libs_used.append(module)
    
    agent_libs_used = list(set(agent_libs_used))  # Remove duplicates
    
    # Assess each file
    for file_path, components in ml_components.items():
        # Calculate a readiness score based on various factors
        score = 0
        
        # Check for agent libraries
        file_agent_libs = [imp['module'] for imp in components['imports'] 
                          if any(lib in imp['module'].lower() for lib in AGENT_LIBRARIES)]
        if file_agent_libs:
            score += 3  # Significant boost for agent libraries
        
        # Check for ML libraries (less impactful than agent libraries)
        file_ml_libs = [imp['module'] for imp in components['imports'] 
                        if any(lib in imp['module'].lower() for lib in ML_LIBRARIES)]
        if file_ml_libs:
            score += 1
        
        # Check for model classes
        if components['classes']:
            score += 1
        
        # Check for hyperparameters - configurable models are more agent-ready
        if components['hyperparameters']:
            score += 2
        
        # Scale the score to 0-10
        max_possible = 7  # Max points possible from above
        normalized_score = min(round((score / max_possible) * 10, 1), 10)
        
        assessment[file_path] = normalized_score
    
    return assessment, agent_libs_used

def generate_agent_readiness_recommendations(ml_components, assessment, agent_libs_used):
    """
    Generate recommendations for improving agent-readiness
    
    Parameters:
    - ml_components: Dictionary of ML components
    - assessment: Assessment of agent-readiness
    - agent_libs_used: List of agent libraries used
    
    Returns:
    - list: Recommendations
    """
    recommendations = []
    
    # Analyze the overall agent-readiness
    avg_score = sum(assessment.values()) / len(assessment) if assessment else 0
    
    if avg_score < 3:
        recommendations.append(
            f"The codebase has low agent-readiness (average score: {avg_score:.1f}/10). Consider integrating agent-friendly libraries."
        )
    elif avg_score < 7:
        recommendations.append(
            f"The codebase has moderate agent-readiness (average score: {avg_score:.1f}/10). Enhance with more agent-specific features."
        )
    else:
        recommendations.append(
            f"The codebase has good agent-readiness (average score: {avg_score:.1f}/10). Focus on refining existing agent capabilities."
        )
    
    # Recommendations based on agent library usage
    if not agent_libs_used:
        recommendations.append(
            "No agent-specific libraries detected. Consider integrating libraries like LangChain, AutoGEN, or CrewAI."
        )
    else:
        recommendations.append(
            f"Agent libraries found: {', '.join(agent_libs_used)}. Ensure they're used consistently across the codebase."
        )
    
    # Check for consistent hyperparameters
    all_hyperparams = set()
    for file_path, components in ml_components.items():
        for param in components['hyperparameters']:
            all_hyperparams.add(param['name'])
    
    if all_hyperparams:
        recommendations.append(
            f"Standardize hyperparameter management across {len(all_hyperparams)} parameters to enable agent-controlled optimization."
        )
    
    # Check for modular structure (classes vs direct code)
    class_count = sum(len(components['classes']) for components in ml_components.values())
    if class_count < len(ml_components) / 2:  # Less classes than half the files
        recommendations.append(
            "Structure ML code using classes and interfaces for better agent interaction. Avoid script-like implementations."
        )
    
    # Specific architecture recommendations
    recommendations.append(
        "Implement a clear API layer for agents to interact with ML components."
    )
    
    recommendations.append(
        "Use configuration files or environment variables for model parameters to allow agent modification."
    )
    
    recommendations.append(
        "Add instrumentation and logging to provide feedback to agents on model performance."
    )
    
    recommendations.append(
        "Implement a callback system for agents to monitor and potentially early-stop model training."
    )
    
    return recommendations

def analyze_agent_readiness(repo_path):
    """
    Analyze agent-readiness in the repository
    
    Parameters:
    - repo_path: Path to the cloned repository
    
    Returns:
    - dict: Agent-readiness analysis results
    """
    logger.info(f"Analyzing agent-readiness for repository at {repo_path}...")
    
    # Initialize results
    results = {
        'ml_components': [],
        'assessment': {},
        'agent_libraries': [],
        'recommendations': []
    }
    
    # Find ML-related files
    ml_files = find_ml_files(repo_path)
    if not ml_files:
        logger.info("No machine learning related files found.")
        results['recommendations'] = [
            "No machine learning components detected. Consider incorporating ML capabilities.",
            "When adding ML components, design them with agent-readiness in mind from the start.",
            "Use standard libraries like TensorFlow, PyTorch, or scikit-learn with clear interfaces.",
            "Implement configurable models with well-defined parameters and clear documentation."
        ]
        return results
    
    # Analyze each ML file
    ml_components = {}
    for file_path in ml_files:
        components = analyze_ml_file(repo_path, file_path)
        if any(len(components[key]) > 0 for key in components):
            ml_components[file_path] = components
    
    # Convert to a list of dictionaries for better display
    for file_path, components in ml_components.items():
        file_info = {
            'file': file_path,
            'ml_libraries': [imp['module'] for imp in components['imports'] 
                            if any(lib in imp['module'].lower() for lib in ML_LIBRARIES)],
            'agent_libraries': [imp['module'] for imp in components['imports'] 
                               if any(lib in imp['module'].lower() for lib in AGENT_LIBRARIES)],
            'model_classes': [cls['name'] for cls in components['classes']],
            'ml_functions': [func['name'] for func in components['functions']],
            'hyperparameters': [param['name'] for param in components['hyperparameters']]
        }
        results['ml_components'].append(file_info)
    
    # Evaluate agent-readiness
    assessment, agent_libs_used = evaluate_agent_readiness(ml_components)
    if assessment:
        # Convert assessment from dict to list of dicts for better display
        assessment_list = []
        for file_path, score in assessment.items():
            assessment_list.append({
                'file': file_path,
                'score': score
            })
        
        results['assessment'] = assessment_list
    
    results['agent_libraries'] = agent_libs_used
    
    # Generate recommendations
    recommendations = generate_agent_readiness_recommendations(ml_components, assessment, agent_libs_used)
    results['recommendations'] = recommendations
    
    logger.info(f"Agent-readiness analysis complete. Found {len(ml_files)} ML-related files.")
    return results