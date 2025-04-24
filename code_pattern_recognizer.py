"""
Code Pattern Recognizer Module

This module applies machine learning techniques to identify patterns,
anti-patterns, and code smells in codebases. It uses a combination of
static analysis, natural language processing of comments, and machine
learning to recognize complex patterns that would be difficult to
detect with rule-based systems alone.
"""

import os
import re
import ast
import logging
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional, Union, Tuple, Set
import pickle
import tempfile

# ML libraries
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN, KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# We're using scikit-learn models exclusively for better compatibility
TENSORFLOW_AVAILABLE = False
logger = logging.getLogger(__name__)
logger.info("Using scikit-learn models for pattern recognition.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodePatternRecognizer:
    """
    Machine learning-based code pattern recognizer
    
    This class uses various ML techniques to identify patterns in code:
    1. Unsupervised learning to find clusters of similar code
    2. Anomaly detection to find unusual code patterns
    3. Feature extraction to identify important code characteristics
    4. Neural networks to recognize complex patterns
    """
    
    def __init__(self, repo_path: str):
        """
        Initialize the pattern recognizer
        
        Args:
            repo_path: Path to the repository
        """
        self.repo_path = repo_path
        self.code_samples = []
        self.function_embeddings = {}
        self.class_embeddings = {}
        self.file_embeddings = {}
        self.pattern_database = {}
        self.anomaly_detector = None
        self.vectorizer = None
        self.code_clusters = None
        self.neural_model = None
        self.is_trained = False
        
        # Patterns to recognize (initially empty, will be filled during learning)
        self.patterns = {
            "code_smells": [],
            "anti_patterns": [],
            "design_patterns": [],
            "performance_patterns": [],
            "security_patterns": []
        }
        
    def extract_code_samples(self, file_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Extract code samples from the repository
        
        Args:
            file_paths: Optional list of specific file paths to analyze
            
        Returns:
            List of extracted code samples with metadata
        """
        logger.info("Extracting code samples from repository...")
        
        # Find Python files if not provided
        if file_paths is None:
            file_paths = []
            for root, _, files in os.walk(self.repo_path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.repo_path)
                        file_paths.append(rel_path)
        
        # Extract samples from each file
        samples = []
        
        for file_path in file_paths:
            full_path = os.path.join(self.repo_path, file_path)
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                # Parse the AST
                try:
                    tree = ast.parse(content)
                    
                    # Extract functions and methods
                    functions = self._extract_functions(tree, file_path, content)
                    samples.extend(functions)
                    
                    # Extract classes
                    classes = self._extract_classes(tree, file_path, content)
                    samples.extend(classes)
                    
                except SyntaxError:
                    logger.warning(f"Syntax error in {file_path}, skipping AST-based extraction")
                    
                    # Fall back to regex-based extraction for files with syntax errors
                    fallback_samples = self._extract_with_regex(content, file_path)
                    samples.extend(fallback_samples)
                    
            except Exception as e:
                logger.error(f"Error extracting from {file_path}: {str(e)}")
        
        logger.info(f"Extracted {len(samples)} code samples")
        self.code_samples = samples
        return samples
    
    def _extract_functions(self, tree: ast.AST, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Extract functions and methods from AST"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Get function source
                start_line = node.lineno
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                
                # Extract the function source code
                lines = content.splitlines()[start_line-1:end_line]
                source_code = '\n'.join(lines)
                
                # Extract docstring if present
                docstring = ast.get_docstring(node) or ""
                
                # Extract parameters
                params = []
                for arg in node.args.args:
                    param_name = arg.arg
                    
                    # Get parameter type if available
                    param_type = ""
                    if hasattr(arg, 'annotation') and arg.annotation is not None:
                        if isinstance(arg.annotation, ast.Name):
                            param_type = arg.annotation.id
                        elif isinstance(arg.annotation, ast.Subscript):
                            if isinstance(arg.annotation.value, ast.Name):
                                param_type = arg.annotation.value.id
                    
                    params.append({
                        'name': param_name,
                        'type': param_type
                    })
                
                # Extract return type if available
                return_type = ""
                if node.returns:
                    if isinstance(node.returns, ast.Name):
                        return_type = node.returns.id
                    elif isinstance(node.returns, ast.Subscript):
                        if isinstance(node.returns.value, ast.Name):
                            return_type = node.returns.value.id
                
                # Calculate cyclomatic complexity
                visitor = ComplexityVisitor()
                visitor.visit(node)
                complexity = visitor.complexity
                
                # Create function sample
                function_sample = {
                    'type': 'function',
                    'name': node.name,
                    'file_path': file_path,
                    'start_line': start_line,
                    'end_line': end_line,
                    'source_code': source_code,
                    'docstring': docstring,
                    'parameters': params,
                    'return_type': return_type,
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                    'complexity': complexity,
                    'code_length': len(source_code),
                    'line_count': end_line - start_line + 1
                }
                
                functions.append(function_sample)
        
        return functions
    
    def _extract_classes(self, tree: ast.AST, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Extract classes from AST"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Get class source
                start_line = node.lineno
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                
                # Extract the class source code
                lines = content.splitlines()[start_line-1:end_line]
                source_code = '\n'.join(lines)
                
                # Extract docstring if present
                docstring = ast.get_docstring(node) or ""
                
                # Extract base classes
                base_classes = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_classes.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        parts = []
                        current = base
                        while isinstance(current, ast.Attribute):
                            parts.insert(0, current.attr)
                            current = current.value
                        if isinstance(current, ast.Name):
                            parts.insert(0, current.id)
                        base_classes.append('.'.join(parts))
                
                # Extract methods
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                        methods.append(item.name)
                
                # Create class sample
                class_sample = {
                    'type': 'class',
                    'name': node.name,
                    'file_path': file_path,
                    'start_line': start_line,
                    'end_line': end_line,
                    'source_code': source_code,
                    'docstring': docstring,
                    'base_classes': base_classes,
                    'methods': methods,
                    'code_length': len(source_code),
                    'line_count': end_line - start_line + 1
                }
                
                classes.append(class_sample)
        
        return classes
    
    def _extract_with_regex(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Fallback extraction using regex for files with syntax errors"""
        samples = []
        
        # Extract functions and methods with regex
        function_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        for match in re.finditer(function_pattern, content):
            func_name = match.group(1)
            start_pos = match.start()
            
            # Find the line number
            line_num = content[:start_pos].count('\n') + 1
            
            # Simple extraction of the function body
            # This is a fallback, so we don't need to be too sophisticated
            lines = content.splitlines()[line_num-1:]
            func_lines = []
            
            in_func = True
            indent_level = None
            
            for line in lines:
                if indent_level is None and line.strip():
                    # Set the indentation level from the first non-empty line
                    indent_level = len(line) - len(line.lstrip())
                    func_lines.append(line)
                elif indent_level is not None:
                    if line.strip() and not line.startswith(' ' * indent_level) and not line.startswith('\t'):
                        # If we find a line with less indentation, we've exited the function
                        break
                    func_lines.append(line)
            
            source_code = '\n'.join(func_lines)
            
            # Create a simple function sample
            function_sample = {
                'type': 'function',
                'name': func_name,
                'file_path': file_path,
                'start_line': line_num,
                'end_line': line_num + len(func_lines) - 1,
                'source_code': source_code,
                'docstring': '',
                'parameters': [],
                'return_type': '',
                'is_async': False,
                'complexity': 1,  # Default complexity
                'code_length': len(source_code),
                'line_count': len(func_lines)
            }
            
            samples.append(function_sample)
        
        # Extract classes with regex
        class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            start_pos = match.start()
            
            # Find the line number
            line_num = content[:start_pos].count('\n') + 1
            
            # Simple extraction of the class body
            lines = content.splitlines()[line_num-1:]
            class_lines = []
            
            in_class = True
            indent_level = None
            
            for line in lines:
                if indent_level is None and line.strip():
                    # Set the indentation level from the first non-empty line
                    indent_level = len(line) - len(line.lstrip())
                    class_lines.append(line)
                elif indent_level is not None:
                    if line.strip() and not line.startswith(' ' * indent_level) and not line.startswith('\t'):
                        # If we find a line with less indentation, we've exited the class
                        break
                    class_lines.append(line)
            
            source_code = '\n'.join(class_lines)
            
            # Create a simple class sample
            class_sample = {
                'type': 'class',
                'name': class_name,
                'file_path': file_path,
                'start_line': line_num,
                'end_line': line_num + len(class_lines) - 1,
                'source_code': source_code,
                'docstring': '',
                'base_classes': [],
                'methods': [],
                'code_length': len(source_code),
                'line_count': len(class_lines)
            }
            
            samples.append(class_sample)
        
        return samples
    
    def generate_code_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Generate vectorized embeddings for code samples
        
        Returns:
            Dictionary mapping sample IDs to their embeddings
        """
        logger.info("Generating code embeddings...")
        
        if not self.code_samples:
            logger.warning("No code samples available. Run extract_code_samples first.")
            return {}
        
        # Extract source code for vectorization
        texts = []
        sample_ids = []
        
        for i, sample in enumerate(self.code_samples):
            # Use the source code as the text to vectorize
            source_code = sample['source_code']
            
            # Remove comments
            source_code = re.sub(r'#.*$', '', source_code, flags=re.MULTILINE)
            
            # Remove docstring
            if sample.get('docstring'):
                source_code = source_code.replace(sample['docstring'], '')
            
            # Add identifier to keep track of which embedding corresponds to which sample
            sample_id = f"{sample['type']}_{i}"
            sample_ids.append(sample_id)
            texts.append(source_code)
        
        # Create TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words='english',
            norm='l2'
        )
        
        # Generate embeddings
        try:
            X = self.vectorizer.fit_transform(texts)
            
            # Convert sparse matrix to numpy array
            X_dense = X.toarray()
            
            # Create a dictionary mapping sample IDs to embeddings
            embeddings = {}
            for i, sample_id in enumerate(sample_ids):
                embeddings[sample_id] = X_dense[i]
            
            # Store embeddings by type
            for i, sample in enumerate(self.code_samples):
                sample_id = f"{sample['type']}_{i}"
                if sample['type'] == 'function':
                    self.function_embeddings[sample['name']] = embeddings[sample_id]
                elif sample['type'] == 'class':
                    self.class_embeddings[sample['name']] = embeddings[sample_id]
                
                # Also store by file path
                file_path = sample['file_path']
                if file_path not in self.file_embeddings:
                    self.file_embeddings[file_path] = []
                self.file_embeddings[file_path].append(embeddings[sample_id])
            
            logger.info(f"Generated embeddings for {len(embeddings)} code samples")
            return embeddings
        
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return {}
    
    def identify_code_clusters(self, n_clusters: int = 5) -> Dict[str, Any]:
        """
        Identify clusters of similar code
        
        Args:
            n_clusters: Number of clusters to identify
            
        Returns:
            Dictionary containing cluster analysis results
        """
        logger.info(f"Identifying code clusters (k={n_clusters})...")
        
        # Check if we have embeddings
        if not hasattr(self, 'vectorizer') or self.vectorizer is None:
            logger.warning("No embeddings available. Run generate_code_embeddings first.")
            return {}
        
        # Prepare data
        sample_ids = []
        embeddings_list = []
        
        for i, sample in enumerate(self.code_samples):
            sample_id = f"{sample['type']}_{i}"
            sample_ids.append(sample_id)
            
            if sample['type'] == 'function' and sample['name'] in self.function_embeddings:
                embeddings_list.append(self.function_embeddings[sample['name']])
            elif sample['type'] == 'class' and sample['name'] in self.class_embeddings:
                embeddings_list.append(self.class_embeddings[sample['name']])
            else:
                # Skip samples without embeddings
                sample_ids.pop()
                continue
        
        if not embeddings_list:
            logger.warning("No valid embeddings found for clustering.")
            return {}
        
        # Convert to numpy array
        X = np.array(embeddings_list)
        
        # Apply dimensionality reduction for better clustering
        pca = PCA(n_components=min(50, X.shape[1]))
        X_reduced = pca.fit_transform(X)
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_reduced)
        
        # Run KMeans clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(X_scaled)
        
        # Organize samples by cluster
        clusters = defaultdict(list)
        for i, cluster_id in enumerate(cluster_labels):
            sample_id = sample_ids[i]
            sample_idx = int(sample_id.split('_')[1])
            sample = self.code_samples[sample_idx]
            
            clusters[int(cluster_id)].append({
                'id': sample_id,
                'name': sample['name'],
                'type': sample['type'],
                'file_path': sample['file_path']
            })
        
        # Calculate cluster statistics
        cluster_stats = {}
        for cluster_id, samples in clusters.items():
            types = Counter([s['type'] for s in samples])
            cluster_stats[cluster_id] = {
                'size': len(samples),
                'types': dict(types),
                'samples': samples[:10]  # limit to 10 examples
            }
        
        # Store the clustering results
        self.code_clusters = {
            'algorithm': 'kmeans',
            'n_clusters': n_clusters,
            'clusters': dict(cluster_stats),
            'pca': pca,
            'scaler': scaler,
            'kmeans': kmeans
        }
        
        logger.info(f"Identified {len(clusters)} code clusters")
        return self.code_clusters
    
    def detect_code_anomalies(self, contamination: float = 0.05) -> List[Dict[str, Any]]:
        """
        Detect anomalous code patterns using isolation forest
        
        Args:
            contamination: Expected proportion of anomalies
            
        Returns:
            List of detected anomalies with details
        """
        logger.info(f"Detecting code anomalies (contamination={contamination})...")
        
        # Check if we have embeddings
        if not hasattr(self, 'vectorizer') or self.vectorizer is None:
            logger.warning("No embeddings available. Run generate_code_embeddings first.")
            return []
        
        # Prepare data
        sample_ids = []
        embeddings_list = []
        complexity_list = []
        
        for i, sample in enumerate(self.code_samples):
            sample_id = f"{sample['type']}_{i}"
            
            if sample['type'] == 'function' and sample['name'] in self.function_embeddings:
                sample_ids.append(sample_id)
                embeddings_list.append(self.function_embeddings[sample['name']])
                complexity_list.append(sample.get('complexity', 1))
            elif sample['type'] == 'class' and sample['name'] in self.class_embeddings:
                sample_ids.append(sample_id)
                embeddings_list.append(self.class_embeddings[sample['name']])
                complexity_list.append(len(sample.get('methods', [])))
        
        if not embeddings_list:
            logger.warning("No valid embeddings found for anomaly detection.")
            return []
        
        # Convert to numpy array
        X = np.array(embeddings_list)
        
        # Add complexity as a feature
        complexity_array = np.array(complexity_list).reshape(-1, 1)
        X_with_complexity = np.hstack([X, complexity_array])
        
        # Apply dimensionality reduction
        pca = PCA(n_components=min(50, X_with_complexity.shape[1]))
        X_reduced = pca.fit_transform(X_with_complexity)
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_reduced)
        
        # Fit isolation forest
        isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_jobs=-1
        )
        
        # Predict anomalies (-1 for anomalies, 1 for normal)
        y_pred = isolation_forest.fit_predict(X_scaled)
        
        # Calculate anomaly scores
        anomaly_scores = isolation_forest.decision_function(X_scaled)
        
        # Collect anomalies
        anomalies = []
        for i, pred in enumerate(y_pred):
            if pred == -1:  # Anomaly
                sample_id = sample_ids[i]
                sample_idx = int(sample_id.split('_')[1])
                sample = self.code_samples[sample_idx]
                
                anomaly = {
                    'id': sample_id,
                    'name': sample['name'],
                    'type': sample['type'],
                    'file_path': sample['file_path'],
                    'start_line': sample['start_line'],
                    'end_line': sample['end_line'],
                    'anomaly_score': float(anomaly_scores[i]),
                    'complexity': sample.get('complexity', 1),
                    'code_length': sample.get('code_length', 0),
                    'line_count': sample.get('line_count', 0)
                }
                
                anomalies.append(anomaly)
        
        # Sort anomalies by anomaly score (most anomalous first)
        anomalies.sort(key=lambda x: x['anomaly_score'])
        
        # Store the anomaly detector
        self.anomaly_detector = {
            'isolation_forest': isolation_forest,
            'pca': pca,
            'scaler': scaler
        }
        
        logger.info(f"Detected {len(anomalies)} code anomalies")
        return anomalies
    
    def train_neural_pattern_recognizer(self, train_ratio: float = 0.8) -> Dict[str, Any]:
        """
        Train a model to recognize code patterns
        
        Args:
            train_ratio: Ratio of data to use for training
            
        Returns:
            Dictionary with training results
        """
        logger.info("Training pattern recognizer...")
        
        # Check if we have embeddings
        if not hasattr(self, 'vectorizer') or self.vectorizer is None:
            logger.warning("No embeddings available. Run generate_code_embeddings first.")
            return {}
        
        # Prepare data
        X = []
        y_complexity = []
        sample_info = []
        
        for i, sample in enumerate(self.code_samples):
            if sample['type'] == 'function' and sample['name'] in self.function_embeddings:
                # Feature vector: embedding + other features
                embedding = self.function_embeddings[sample['name']]
                
                # Additional features
                features = [
                    sample.get('line_count', 0) / 100,  # Normalize line count
                    sample.get('complexity', 1) / 10,   # Normalize complexity
                    len(sample.get('parameters', [])) / 10,  # Normalize param count
                    1 if sample.get('docstring', '') else 0  # Has docstring
                ]
                
                # Combine embedding and features
                feature_vector = np.concatenate([embedding, features])
                
                X.append(feature_vector)
                y_complexity.append(sample.get('complexity', 1))
                
                sample_info.append({
                    'id': f"{sample['type']}_{i}",
                    'name': sample['name'],
                    'type': sample['type'],
                    'file_path': sample['file_path']
                })
            
            elif sample['type'] == 'class' and sample['name'] in self.class_embeddings:
                # Feature vector: embedding + other features
                embedding = self.class_embeddings[sample['name']]
                
                # Additional features
                features = [
                    sample.get('line_count', 0) / 100,  # Normalize line count
                    len(sample.get('methods', [])) / 10,  # Normalize method count
                    len(sample.get('base_classes', [])) / 5,  # Normalize inheritance depth
                    1 if sample.get('docstring', '') else 0  # Has docstring
                ]
                
                # Combine embedding and features
                feature_vector = np.concatenate([embedding, features])
                
                X.append(feature_vector)
                y_complexity.append(len(sample.get('methods', [])))
                
                sample_info.append({
                    'id': f"{sample['type']}_{i}",
                    'name': sample['name'],
                    'type': sample['type'],
                    'file_path': sample['file_path']
                })
        
        if not X:
            logger.warning("No valid samples found for pattern recognition.")
            return {}
        
        # Convert to numpy arrays
        X = np.array(X)
        y_complexity = np.array(y_complexity)
        
        # Split data
        n_samples = len(X)
        n_train = int(n_samples * train_ratio)
        
        # Random indices for train/test split
        indices = np.random.permutation(n_samples)
        train_idx, test_idx = indices[:n_train], indices[n_train:]
        
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y_complexity[train_idx], y_complexity[test_idx]
        
        # Standardize features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Training results
        history = {}
        
        # Using scikit-learn models for pattern recognition
        from sklearn.ensemble import GradientBoostingRegressor
        
        # Train a gradient boosting model
        model = GradientBoostingRegressor(
            n_estimators=100, 
            learning_rate=0.1, 
            max_depth=3,
            random_state=42
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        from sklearn.metrics import mean_squared_error, mean_absolute_error
        
        y_pred = model.predict(X_test_scaled)
        test_mse = mean_squared_error(y_test, y_pred)
        test_mae = mean_absolute_error(y_test, y_pred)
        
        # Store the model
        self.neural_model = {
            'model': model,
            'scaler': scaler,
            'test_loss': test_mse,
            'test_mae': test_mae
        }
        
        # Create a simple history for consistency
        history = {'loss': [test_mse], 'val_loss': [test_mse], 'mae': [test_mae], 'val_mae': [test_mae]}
        
        logger.info(f"Gradient Boosting Regressor trained. Test MAE: {test_mae:.4f}")
        
        self.is_trained = True
        
        return {
            'test_loss': self.neural_model['test_loss'],
            'test_mae': self.neural_model['test_mae'],
            'history': history
        }
    
    def save_model(self, model_path: str) -> bool:
        """
        Save the trained model and related data
        
        Args:
            model_path: Path to save the model
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create model directory if it doesn't exist
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            # Save neural model
            if self.neural_model and 'model' in self.neural_model:
                # We only support scikit-learn models
                model_type = 'sklearn'
            else:
                model_type = None
            
            # Create a dictionary with everything to save
            save_data = {
                'function_embeddings': self.function_embeddings,
                'class_embeddings': self.class_embeddings,
                'file_embeddings': self.file_embeddings,
                'pattern_database': self.pattern_database,
                'code_clusters': self.code_clusters,
                'patterns': self.patterns,
                'is_trained': self.is_trained,
                'model_type': model_type
            }
            
            # Save vectorizer
            if self.vectorizer:
                save_data['vectorizer'] = self.vectorizer
            
            # Save anomaly detector
            if self.anomaly_detector:
                save_data['anomaly_detector'] = self.anomaly_detector
            
            # Save scaler from neural model
            if self.neural_model and 'scaler' in self.neural_model:
                save_data['neural_scaler'] = self.neural_model['scaler']
            
            # For scikit-learn models, save the model directly
            if model_type == 'sklearn' and 'model' in self.neural_model:
                save_data['sklearn_model'] = self.neural_model['model']
            
            # Save to file
            with open(model_path, 'wb') as f:
                pickle.dump(save_data, f)
            
            logger.info(f"Model saved to {model_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            return False
    
    def load_model(self, model_path: str) -> bool:
        """
        Load a trained model and related data
        
        Args:
            model_path: Path to load the model from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load saved data
            with open(model_path, 'rb') as f:
                save_data = pickle.load(f)
            
            # Restore saved attributes
            self.function_embeddings = save_data.get('function_embeddings', {})
            self.class_embeddings = save_data.get('class_embeddings', {})
            self.file_embeddings = save_data.get('file_embeddings', {})
            self.pattern_database = save_data.get('pattern_database', {})
            self.code_clusters = save_data.get('code_clusters', None)
            self.patterns = save_data.get('patterns', {})
            self.is_trained = save_data.get('is_trained', False)
            model_type = save_data.get('model_type', None)
            
            # Restore vectorizer
            if 'vectorizer' in save_data:
                self.vectorizer = save_data['vectorizer']
            
            # Restore anomaly detector
            if 'anomaly_detector' in save_data:
                self.anomaly_detector = save_data['anomaly_detector']
            
            # Handle model loading based on type
            if model_type == 'sklearn':
                # Load scikit-learn model
                if 'sklearn_model' in save_data:
                    self.neural_model = {
                        'model': save_data['sklearn_model'],
                        'scaler': save_data.get('neural_scaler', None),
                        'test_loss': save_data.get('test_loss', 0),
                        'test_mae': save_data.get('test_mae', 0)
                    }
            elif model_type == 'tensorflow':
                # Skip TensorFlow models as we're not supporting them
                logger.warning("TensorFlow models are not supported in this version")
                return False
            
            logger.info(f"Model loaded from {model_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
    
    def identify_patterns(self, min_pattern_size: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify common code patterns in the repository
        
        Args:
            min_pattern_size: Minimum number of occurrences to consider a pattern
            
        Returns:
            Dictionary of identified patterns by category
        """
        logger.info("Identifying code patterns...")
        
        if not self.code_samples:
            logger.warning("No code samples available. Run extract_code_samples first.")
            return {}
        
        # Initialize pattern collections
        patterns = {
            "code_smells": [],
            "anti_patterns": [],
            "design_patterns": [],
            "performance_patterns": [],
            "security_patterns": []
        }
        
        # Find code smells
        patterns["code_smells"] = self._identify_code_smells(min_occurrences=min_pattern_size)
        
        # Find anti-patterns
        patterns["anti_patterns"] = self._identify_anti_patterns(min_occurrences=min_pattern_size)
        
        # Find design patterns
        patterns["design_patterns"] = self._identify_design_patterns(min_occurrences=min_pattern_size)
        
        # Find performance patterns
        patterns["performance_patterns"] = self._identify_performance_patterns(min_occurrences=min_pattern_size)
        
        # Find security patterns
        patterns["security_patterns"] = self._identify_security_patterns(min_occurrences=min_pattern_size)
        
        # Update the stored patterns
        self.patterns = patterns
        
        # Count total patterns
        total_patterns = sum(len(patterns[category]) for category in patterns)
        logger.info(f"Identified {total_patterns} code patterns")
        
        return patterns
    
    def _identify_code_smells(self, min_occurrences: int = 3) -> List[Dict[str, Any]]:
        """Identify common code smells"""
        code_smells = []
        
        # High cyclomatic complexity functions
        complexity_threshold = 10
        complex_functions = [
            sample for sample in self.code_samples
            if sample['type'] == 'function' and sample.get('complexity', 0) > complexity_threshold
        ]
        
        if len(complex_functions) >= min_occurrences:
            code_smells.append({
                'name': 'High Cyclomatic Complexity',
                'type': 'code_smell',
                'category': 'complexity',
                'severity': 'high',
                'description': f'Functions with cyclomatic complexity > {complexity_threshold}',
                'occurrences': len(complex_functions),
                'examples': complex_functions[:5]  # First 5 examples
            })
        
        # Long functions
        line_threshold = 50
        long_functions = [
            sample for sample in self.code_samples
            if sample['type'] == 'function' and sample.get('line_count', 0) > line_threshold
        ]
        
        if len(long_functions) >= min_occurrences:
            code_smells.append({
                'name': 'Long Function',
                'type': 'code_smell',
                'category': 'size',
                'severity': 'medium',
                'description': f'Functions with more than {line_threshold} lines',
                'occurrences': len(long_functions),
                'examples': long_functions[:5]  # First 5 examples
            })
        
        # Large classes
        class_size_threshold = 200
        large_classes = [
            sample for sample in self.code_samples
            if sample['type'] == 'class' and sample.get('line_count', 0) > class_size_threshold
        ]
        
        if len(large_classes) >= min_occurrences:
            code_smells.append({
                'name': 'Large Class',
                'type': 'code_smell',
                'category': 'size',
                'severity': 'medium',
                'description': f'Classes with more than {class_size_threshold} lines',
                'occurrences': len(large_classes),
                'examples': large_classes[:5]  # First 5 examples
            })
        
        # Functions with too many parameters
        param_threshold = 5
        many_param_functions = [
            sample for sample in self.code_samples
            if sample['type'] == 'function' and len(sample.get('parameters', [])) > param_threshold
        ]
        
        if len(many_param_functions) >= min_occurrences:
            code_smells.append({
                'name': 'Too Many Parameters',
                'type': 'code_smell',
                'category': 'design',
                'severity': 'medium',
                'description': f'Functions with more than {param_threshold} parameters',
                'occurrences': len(many_param_functions),
                'examples': many_param_functions[:5]  # First 5 examples
            })
        
        # Missing docstrings
        missing_docstring_functions = [
            sample for sample in self.code_samples
            if sample['type'] == 'function' and not sample.get('docstring', '').strip()
        ]
        
        if len(missing_docstring_functions) >= min_occurrences:
            code_smells.append({
                'name': 'Missing Documentation',
                'type': 'code_smell',
                'category': 'documentation',
                'severity': 'low',
                'description': 'Functions lacking docstrings',
                'occurrences': len(missing_docstring_functions),
                'examples': missing_docstring_functions[:5]  # First 5 examples
            })
        
        # Identify duplicate code based on embeddings similarity
        if self.function_embeddings:
            # Convert function embeddings to a list
            names = list(self.function_embeddings.keys())
            embeddings = np.array(list(self.function_embeddings.values()))
            
            # Compute similarity matrix
            similarity_matrix = embeddings @ embeddings.T
            
            # Find highly similar functions (but not identical)
            similar_pairs = []
            for i in range(len(names)):
                for j in range(i+1, len(names)):
                    similarity = similarity_matrix[i, j]
                    if similarity > 0.8:  # High similarity threshold
                        similar_pairs.append((names[i], names[j], similarity))
            
            # Group similar functions
            if len(similar_pairs) >= min_occurrences:
                code_smells.append({
                    'name': 'Duplicate Code',
                    'type': 'code_smell',
                    'category': 'duplication',
                    'severity': 'high',
                    'description': 'Highly similar functions that might indicate code duplication',
                    'occurrences': len(similar_pairs),
                    'similar_pairs': similar_pairs[:10]  # First 10 similar pairs
                })
        
        return code_smells
    
    def _identify_anti_patterns(self, min_occurrences: int = 3) -> List[Dict[str, Any]]:
        """Identify common anti-patterns"""
        anti_patterns = []
        
        # Find God classes
        method_threshold = 15
        god_classes = [
            sample for sample in self.code_samples
            if sample['type'] == 'class' and len(sample.get('methods', [])) > method_threshold
        ]
        
        if len(god_classes) >= min_occurrences:
            anti_patterns.append({
                'name': 'God Class',
                'type': 'anti_pattern',
                'category': 'design',
                'severity': 'high',
                'description': f'Classes with more than {method_threshold} methods',
                'occurrences': len(god_classes),
                'examples': god_classes[:5]  # First 5 examples
            })
        
        # Identify circular imports if we have file embeddings
        if self.file_embeddings:
            # This would require deeper analysis of imports
            # We'll just check for potential import statements in the code
            circular_import_candidates = []
            
            for i, sample in enumerate(self.code_samples):
                if sample['type'] == 'function':
                    code = sample['source_code']
                    if 'import' in code.lower() and 'circular' in code.lower():
                        circular_import_candidates.append(sample)
            
            if len(circular_import_candidates) >= min_occurrences:
                anti_patterns.append({
                    'name': 'Potential Circular Imports',
                    'type': 'anti_pattern',
                    'category': 'imports',
                    'severity': 'medium',
                    'description': 'Code potentially dealing with circular imports',
                    'occurrences': len(circular_import_candidates),
                    'examples': circular_import_candidates[:5]  # First 5 examples
                })
        
        # Detect potential spaghetti code - high complexity functions with many lines
        complexity_threshold = 15
        line_threshold = 100
        spaghetti_code = [
            sample for sample in self.code_samples
            if sample['type'] == 'function' 
            and sample.get('complexity', 0) > complexity_threshold
            and sample.get('line_count', 0) > line_threshold
        ]
        
        if len(spaghetti_code) >= min_occurrences:
            anti_patterns.append({
                'name': 'Spaghetti Code',
                'type': 'anti_pattern',
                'category': 'complexity',
                'severity': 'high',
                'description': f'Complex, long functions that are difficult to understand',
                'occurrences': len(spaghetti_code),
                'examples': spaghetti_code[:5]  # First 5 examples
            })
        
        return anti_patterns
    
    def _identify_design_patterns(self, min_occurrences: int = 2) -> List[Dict[str, Any]]:
        """Identify common design patterns"""
        design_patterns = []
        
        # Singleton pattern
        singleton_candidates = []
        for sample in self.code_samples:
            if sample['type'] == 'class':
                code = sample['source_code'].lower()
                # Look for singleton pattern indicators
                if ('instance' in code or '_instance' in code) and '__new__' in code:
                    singleton_candidates.append(sample)
        
        if len(singleton_candidates) >= min_occurrences:
            design_patterns.append({
                'name': 'Singleton Pattern',
                'type': 'design_pattern',
                'category': 'creational',
                'description': 'Classes implementing the Singleton pattern',
                'occurrences': len(singleton_candidates),
                'examples': singleton_candidates[:5]  # First 5 examples
            })
        
        # Factory pattern
        factory_candidates = []
        for sample in self.code_samples:
            if sample['type'] == 'class':
                name = sample['name'].lower()
                if 'factory' in name:
                    factory_candidates.append(sample)
            elif sample['type'] == 'function':
                name = sample['name'].lower()
                if 'create' in name or 'build' in name or 'factory' in name:
                    factory_candidates.append(sample)
        
        if len(factory_candidates) >= min_occurrences:
            design_patterns.append({
                'name': 'Factory Pattern',
                'type': 'design_pattern',
                'category': 'creational',
                'description': 'Classes or functions implementing the Factory pattern',
                'occurrences': len(factory_candidates),
                'examples': factory_candidates[:5]  # First 5 examples
            })
        
        # Observer pattern
        observer_candidates = []
        for sample in self.code_samples:
            if sample['type'] == 'class':
                name = sample['name'].lower()
                code = sample['source_code'].lower()
                if ('observer' in name or 'listener' in name or 'event' in name) and \
                   ('subscribe' in code or 'register' in code or 'add_listener' in code):
                    observer_candidates.append(sample)
        
        if len(observer_candidates) >= min_occurrences:
            design_patterns.append({
                'name': 'Observer Pattern',
                'type': 'design_pattern',
                'category': 'behavioral',
                'description': 'Classes implementing the Observer pattern',
                'occurrences': len(observer_candidates),
                'examples': observer_candidates[:5]  # First 5 examples
            })
        
        return design_patterns
    
    def _identify_performance_patterns(self, min_occurrences: int = 2) -> List[Dict[str, Any]]:
        """Identify performance patterns"""
        performance_patterns = []
        
        # Caching pattern
        caching_candidates = []
        for sample in self.code_samples:
            code = sample['source_code'].lower()
            name = sample['name'].lower()
            if 'cache' in code or 'memo' in code or 'lru_cache' in code or \
               'cache' in name or 'memo' in name:
                caching_candidates.append(sample)
        
        if len(caching_candidates) >= min_occurrences:
            performance_patterns.append({
                'name': 'Caching/Memoization',
                'type': 'performance_pattern',
                'category': 'optimization',
                'description': 'Code using caching or memoization for performance',
                'occurrences': len(caching_candidates),
                'examples': caching_candidates[:5]  # First 5 examples
            })
        
        # Lazy loading pattern
        lazy_loading_candidates = []
        for sample in self.code_samples:
            code = sample['source_code'].lower()
            name = sample['name'].lower()
            if 'lazy' in code or 'on_demand' in code or 'lazy' in name or 'load_when_needed' in name:
                lazy_loading_candidates.append(sample)
        
        if len(lazy_loading_candidates) >= min_occurrences:
            performance_patterns.append({
                'name': 'Lazy Loading',
                'type': 'performance_pattern',
                'category': 'optimization',
                'description': 'Code implementing lazy loading for performance',
                'occurrences': len(lazy_loading_candidates),
                'examples': lazy_loading_candidates[:5]  # First 5 examples
            })
        
        # Connection pooling pattern
        pooling_candidates = []
        for sample in self.code_samples:
            code = sample['source_code'].lower()
            name = sample['name'].lower()
            if 'pool' in code or 'connection_pool' in code or 'pool' in name:
                pooling_candidates.append(sample)
        
        if len(pooling_candidates) >= min_occurrences:
            performance_patterns.append({
                'name': 'Connection/Resource Pooling',
                'type': 'performance_pattern',
                'category': 'optimization',
                'description': 'Code implementing resource pooling for performance',
                'occurrences': len(pooling_candidates),
                'examples': pooling_candidates[:5]  # First 5 examples
            })
        
        # Algorithmic complexity patterns
        nested_loop_candidates = []
        for sample in self.code_samples:
            if sample['type'] == 'function':
                code = sample['source_code'].lower()
                
                # Look for nested loops (O(n²) or worse)
                has_nested_loops = False
                if ('for ' in code or 'while ' in code) and \
                   ('for ' in code.split('for ', 1)[1] or 'while ' in code.split('for ', 1)[1]):
                    has_nested_loops = True
                
                if has_nested_loops:
                    nested_loop_candidates.append(sample)
        
        if len(nested_loop_candidates) >= min_occurrences:
            performance_patterns.append({
                'name': 'Nested Loops',
                'type': 'performance_pattern',
                'category': 'algorithm',
                'severity': 'medium',
                'description': 'Nested loops can lead to O(n²) or worse time complexity',
                'occurrences': len(nested_loop_candidates),
                'examples': nested_loop_candidates[:5]  # First 5 examples
            })
        
        # Inefficient string manipulation
        string_concat_candidates = []
        for sample in self.code_samples:
            if sample['type'] == 'function':
                code = sample['source_code'].lower()
                
                # Check for inefficient string concatenation
                if '+= ' in code and ('str' in code or '"' in code and '+= "' in code):
                    string_concat_candidates.append(sample)
        
        if len(string_concat_candidates) >= min_occurrences:
            performance_patterns.append({
                'name': 'Inefficient String Concatenation',
                'type': 'performance_pattern',
                'category': 'memory',
                'severity': 'low',
                'description': 'Using join() instead of += for string concatenation is more efficient',
                'occurrences': len(string_concat_candidates),
                'examples': string_concat_candidates[:5]
            })
        
        # Expensive operations in loops
        exp_loop_candidates = []
        for sample in self.code_samples:
            if sample['type'] == 'function':
                code = sample['source_code'].lower()
                
                # Check for CPU-intensive operations in loops
                if ('for ' in code or 'while ' in code) and \
                   ('sort(' in code or 'deepcopy(' in code or 'json.loads(' in code):
                    exp_loop_candidates.append(sample)
        
        if len(exp_loop_candidates) >= min_occurrences:
            performance_patterns.append({
                'name': 'Expensive Operations in Loop',
                'type': 'performance_pattern',
                'category': 'algorithm',
                'severity': 'high',
                'description': 'Expensive operations inside loops can severely impact performance',
                'occurrences': len(exp_loop_candidates),
                'examples': exp_loop_candidates[:5]
            })
        
        # Asynchronous processing pattern
        async_candidates = []
        for sample in self.code_samples:
            code = sample['source_code'].lower()
            if 'async ' in code or 'await ' in code or 'asyncio' in code:
                async_candidates.append(sample)
        
        if len(async_candidates) >= min_occurrences:
            performance_patterns.append({
                'name': 'Asynchronous Processing',
                'type': 'performance_pattern',
                'category': 'concurrency',
                'severity': 'positive',
                'description': 'Code using asynchronous processing for improved performance',
                'occurrences': len(async_candidates),
                'examples': async_candidates[:5]
            })
        
        # Thread/worker pool pattern
        thread_candidates = []
        for sample in self.code_samples:
            code = sample['source_code'].lower()
            if 'thread' in code or 'threading' in code or 'concurrent.futures' in code:
                thread_candidates.append(sample)
        
        if len(thread_candidates) >= min_occurrences:
            performance_patterns.append({
                'name': 'Multi-threading/Worker Pool',
                'type': 'performance_pattern',
                'category': 'concurrency',
                'severity': 'positive',
                'description': 'Code using multi-threading or worker pools for parallel processing',
                'occurrences': len(thread_candidates),
                'examples': thread_candidates[:5]
            })
        
        return performance_patterns
    
    def _identify_security_patterns(self, min_occurrences: int = 2) -> List[Dict[str, Any]]:
        """Identify security patterns"""
        security_patterns = []
        
        # Input validation pattern
        validation_candidates = []
        for sample in self.code_samples:
            code = sample['source_code'].lower()
            name = sample['name'].lower()
            if ('validate' in code or 'sanitize' in code or 'escape' in code or 
                'validate' in name or 'sanitize' in name):
                validation_candidates.append(sample)
        
        if len(validation_candidates) >= min_occurrences:
            security_patterns.append({
                'name': 'Input Validation',
                'type': 'security_pattern',
                'category': 'data_validation',
                'description': 'Code implementing input validation or sanitization',
                'occurrences': len(validation_candidates),
                'examples': validation_candidates[:5]  # First 5 examples
            })
        
        # Authentication/Authorization pattern
        auth_candidates = []
        for sample in self.code_samples:
            code = sample['source_code'].lower()
            name = sample['name'].lower()
            if ('auth' in code or 'login' in code or 'permission' in code or 
                'role' in code or 'auth' in name or 'login' in name):
                auth_candidates.append(sample)
        
        if len(auth_candidates) >= min_occurrences:
            security_patterns.append({
                'name': 'Authentication/Authorization',
                'type': 'security_pattern',
                'category': 'access_control',
                'description': 'Code implementing authentication or authorization',
                'occurrences': len(auth_candidates),
                'examples': auth_candidates[:5]  # First 5 examples
            })
        
        # Secure communication pattern
        secure_comm_candidates = []
        for sample in self.code_samples:
            code = sample['source_code'].lower()
            if ('ssl' in code or 'tls' in code or 'https' in code or 
                'encrypt' in code or 'decrypt' in code):
                secure_comm_candidates.append(sample)
        
        if len(secure_comm_candidates) >= min_occurrences:
            security_patterns.append({
                'name': 'Secure Communication',
                'type': 'security_pattern',
                'category': 'encryption',
                'description': 'Code implementing secure communication or encryption',
                'occurrences': len(secure_comm_candidates),
                'examples': secure_comm_candidates[:5]  # First 5 examples
            })
        
        return security_patterns
    
    def analyze_repository(self, file_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run a complete analysis of the repository
        
        Args:
            file_paths: Optional list of specific file paths to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        logger.info("Running complete repository analysis...")
        
        # Extract code samples
        self.extract_code_samples(file_paths)
        
        # Generate code embeddings
        self.generate_code_embeddings()
        
        # Identify code clusters
        self.identify_code_clusters(n_clusters=6)
        
        # Detect code anomalies
        anomalies = self.detect_code_anomalies(contamination=0.05)
        
        # Train the neural pattern recognizer
        self.train_neural_pattern_recognizer()
        
        # Identify patterns
        patterns = self.identify_patterns(min_pattern_size=2)
        
        # Compile results
        results = {
            'code_samples_count': len(self.code_samples),
            'function_count': len([s for s in self.code_samples if s['type'] == 'function']),
            'class_count': len([s for s in self.code_samples if s['type'] == 'class']),
            'clusters': self.code_clusters['clusters'] if self.code_clusters else {},
            'anomalies': anomalies,
            'patterns': patterns
        }
        
        # Save the model for future use
        model_dir = os.path.join(self.repo_path, 'model_storage')
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, 'code_pattern_model.pkl')
        self.save_model(model_path)
        
        logger.info("Repository analysis complete")
        return results


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor for calculating cyclomatic complexity"""
    
    def __init__(self):
        self.complexity = 1  # Start with 1 for the function itself
    
    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_Try(self, node):
        self.complexity += len(node.handlers)  # Add 1 for each except block
        self.generic_visit(node)
    
    def visit_BoolOp(self, node):
        if isinstance(node.op, ast.And) or isinstance(node.op, ast.Or):
            self.complexity += len(node.values) - 1  # Add complexity for each boolean operator
        self.generic_visit(node)
