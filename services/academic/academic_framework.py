"""
Academic Research Framework

This module provides tools and utilities for academic research, including:
- Benchmark dataset management
- Experiment tracking and reproducibility
- Statistical analysis tools
- Publication-ready visualization generation
- Research paper template generation
"""
import os
import json
import logging
import time
import uuid
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from enum import Enum
from datetime import datetime

class BenchmarkType(Enum):
    """Types of benchmarks for system evaluation."""
    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    PATTERN_RECOGNITION = "pattern_recognition"
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    PERFORMANCE = "performance"
    CORRECTNESS = "correctness"
    SECURITY = "security"
    EXTENSIBILITY = "extensibility"


class ExperimentType(Enum):
    """Types of experiments that can be conducted."""
    COMPARATIVE = "comparative"
    ABLATION = "ablation"
    SCALE = "scale"
    ROBUSTNESS = "robustness"
    HUMAN_EVALUATION = "human_evaluation"
    LONGITUDINAL = "longitudinal"
    CROSS_DOMAIN = "cross_domain"


class AnalysisType(Enum):
    """Types of statistical analysis."""
    DESCRIPTIVE = "descriptive"
    INFERENTIAL = "inferential"
    CORRELATION = "correlation"
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"
    TIME_SERIES = "time_series"


class BenchmarkDataset:
    """
    Benchmark dataset for evaluating the system.
    
    This class provides functionality for:
    - Loading and managing benchmark datasets
    - Computing ground truth metrics
    - Evaluating system performance against benchmarks
    """
    
    def __init__(self, name: str, benchmark_type: Union[str, BenchmarkType],
               description: str, version: str = "1.0.0",
               storage_dir: Optional[str] = None):
        """
        Initialize a benchmark dataset.
        
        Args:
            name: Name of the benchmark
            benchmark_type: Type of benchmark
            description: Description of the benchmark
            version: Version of the benchmark
            storage_dir: Optional directory for storage
        """
        self.name = name
        
        # Convert benchmark_type to enum if string
        if isinstance(benchmark_type, str):
            benchmark_type = BenchmarkType(benchmark_type)
        
        self.benchmark_type = benchmark_type
        self.description = description
        self.version = version
        self.created_at = time.time()
        self.samples = []
        self.metadata = {}
        
        # Set up storage directory
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), 'benchmark_storage')
        
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize logger
        self.logger = logging.getLogger('benchmark_dataset')
    
    def add_sample(self, sample_id: str, data: Dict[str, Any],
                 ground_truth: Dict[str, Any],
                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a sample to the benchmark dataset.
        
        Args:
            sample_id: Unique identifier for the sample
            data: Sample data
            ground_truth: Ground truth for the sample
            metadata: Optional sample metadata
        """
        sample = {
            'id': sample_id,
            'data': data,
            'ground_truth': ground_truth,
            'metadata': metadata or {}
        }
        
        self.samples.append(sample)
        self.logger.info(f"Added sample {sample_id} to benchmark {self.name}")
    
    def remove_sample(self, sample_id: str) -> bool:
        """
        Remove a sample from the benchmark dataset.
        
        Args:
            sample_id: ID of the sample to remove
            
        Returns:
            Removal success
        """
        for i, sample in enumerate(self.samples):
            if sample['id'] == sample_id:
                del self.samples[i]
                self.logger.info(f"Removed sample {sample_id} from benchmark {self.name}")
                return True
        
        return False
    
    def get_sample(self, sample_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a sample from the benchmark dataset.
        
        Args:
            sample_id: ID of the sample to get
            
        Returns:
            Sample or None if not found
        """
        for sample in self.samples:
            if sample['id'] == sample_id:
                return sample
        
        return None
    
    def save(self) -> None:
        """Save the benchmark dataset to storage."""
        # Create directory for this benchmark
        benchmark_dir = os.path.join(self.storage_dir, self.name)
        os.makedirs(benchmark_dir, exist_ok=True)
        
        # Save metadata
        metadata = {
            'name': self.name,
            'benchmark_type': self.benchmark_type.value,
            'description': self.description,
            'version': self.version,
            'created_at': self.created_at,
            'sample_count': len(self.samples),
            'metadata': self.metadata
        }
        
        metadata_path = os.path.join(benchmark_dir, 'metadata.json')
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save samples
        samples_path = os.path.join(benchmark_dir, 'samples.json')
        
        with open(samples_path, 'w') as f:
            json.dump(self.samples, f, indent=2)
        
        self.logger.info(f"Saved benchmark {self.name} with {len(self.samples)} samples")
    
    @classmethod
    def load(cls, name: str, storage_dir: Optional[str] = None) -> 'BenchmarkDataset':
        """
        Load a benchmark dataset from storage.
        
        Args:
            name: Name of the benchmark
            storage_dir: Optional directory for storage
            
        Returns:
            Loaded benchmark dataset
        """
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), 'benchmark_storage')
        
        benchmark_dir = os.path.join(storage_dir, name)
        
        if not os.path.exists(benchmark_dir):
            raise FileNotFoundError(f"Benchmark {name} not found in {storage_dir}")
        
        # Load metadata
        metadata_path = os.path.join(benchmark_dir, 'metadata.json')
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Create benchmark dataset
        benchmark = cls(
            name=metadata['name'],
            benchmark_type=metadata['benchmark_type'],
            description=metadata['description'],
            version=metadata['version'],
            storage_dir=storage_dir
        )
        
        benchmark.created_at = metadata['created_at']
        benchmark.metadata = metadata['metadata']
        
        # Load samples
        samples_path = os.path.join(benchmark_dir, 'samples.json')
        
        with open(samples_path, 'r') as f:
            benchmark.samples = json.load(f)
        
        benchmark.logger.info(f"Loaded benchmark {name} with {len(benchmark.samples)} samples")
        return benchmark
    
    def evaluate(self, results: Dict[str, Dict[str, Any]],
               metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Evaluate results against the benchmark.
        
        Args:
            results: Dictionary mapping sample IDs to result dictionaries
            metrics: Optional list of metrics to compute
            
        Returns:
            Evaluation results
        """
        if not metrics:
            # Use default metrics based on benchmark type
            if self.benchmark_type == BenchmarkType.CODE_QUALITY:
                metrics = ['precision', 'recall', 'f1_score']
            elif self.benchmark_type == BenchmarkType.PATTERN_RECOGNITION:
                metrics = ['accuracy', 'precision', 'recall', 'f1_score']
            elif self.benchmark_type == BenchmarkType.COMPLEXITY:
                metrics = ['mean_absolute_error', 'root_mean_squared_error']
            else:
                metrics = ['accuracy', 'precision', 'recall', 'f1_score']
        
        # Compute metrics for each sample
        sample_metrics = {}
        
        for sample in self.samples:
            sample_id = sample['id']
            
            if sample_id not in results:
                continue
            
            result = results[sample_id]
            ground_truth = sample['ground_truth']
            
            # Compute metrics for this sample
            sample_metrics[sample_id] = self._compute_metrics(
                result=result,
                ground_truth=ground_truth,
                metrics=metrics
            )
        
        # Compute aggregate metrics
        aggregate_metrics = {}
        
        for metric in metrics:
            values = [m[metric] for m in sample_metrics.values() if metric in m]
            
            if values:
                aggregate_metrics[metric] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'median': np.median(values)
                }
        
        return {
            'benchmark': self.name,
            'benchmark_type': self.benchmark_type.value,
            'sample_count': len(self.samples),
            'evaluated_count': len(sample_metrics),
            'metrics': metrics,
            'sample_metrics': sample_metrics,
            'aggregate_metrics': aggregate_metrics
        }
    
    def _compute_metrics(self, result: Dict[str, Any],
                      ground_truth: Dict[str, Any],
                      metrics: List[str]) -> Dict[str, float]:
        """
        Compute metrics for a single sample.
        
        Args:
            result: Result dictionary
            ground_truth: Ground truth dictionary
            metrics: List of metrics to compute
            
        Returns:
            Dictionary of computed metrics
        """
        computed_metrics = {}
        
        for metric in metrics:
            if metric == 'accuracy':
                computed_metrics[metric] = self._compute_accuracy(result, ground_truth)
            elif metric == 'precision':
                computed_metrics[metric] = self._compute_precision(result, ground_truth)
            elif metric == 'recall':
                computed_metrics[metric] = self._compute_recall(result, ground_truth)
            elif metric == 'f1_score':
                precision = self._compute_precision(result, ground_truth)
                recall = self._compute_recall(result, ground_truth)
                
                if precision + recall > 0:
                    computed_metrics[metric] = 2 * (precision * recall) / (precision + recall)
                else:
                    computed_metrics[metric] = 0.0
            elif metric == 'mean_absolute_error':
                computed_metrics[metric] = self._compute_mae(result, ground_truth)
            elif metric == 'root_mean_squared_error':
                computed_metrics[metric] = self._compute_rmse(result, ground_truth)
        
        return computed_metrics
    
    def _compute_accuracy(self, result: Dict[str, Any],
                       ground_truth: Dict[str, Any]) -> float:
        """
        Compute accuracy metric.
        
        Args:
            result: Result dictionary
            ground_truth: Ground truth dictionary
            
        Returns:
            Accuracy value
        """
        # Implementation depends on the benchmark type and data structure
        # This is a simplified example
        if 'predictions' in result and 'labels' in ground_truth:
            predictions = result['predictions']
            labels = ground_truth['labels']
            
            if len(predictions) != len(labels):
                return 0.0
            
            correct = sum(1 for p, l in zip(predictions, labels) if p == l)
            return correct / len(predictions) if predictions else 0.0
        
        return 0.0
    
    def _compute_precision(self, result: Dict[str, Any],
                        ground_truth: Dict[str, Any]) -> float:
        """
        Compute precision metric.
        
        Args:
            result: Result dictionary
            ground_truth: Ground truth dictionary
            
        Returns:
            Precision value
        """
        # Implementation depends on the benchmark type and data structure
        # This is a simplified example
        if 'predictions' in result and 'labels' in ground_truth:
            predictions = result['predictions']
            labels = ground_truth['labels']
            
            if not predictions:
                return 0.0
            
            true_positives = sum(1 for p, l in zip(predictions, labels) if p == 1 and l == 1)
            false_positives = sum(1 for p, l in zip(predictions, labels) if p == 1 and l == 0)
            
            if true_positives + false_positives > 0:
                return true_positives / (true_positives + false_positives)
            else:
                return 0.0
        
        return 0.0
    
    def _compute_recall(self, result: Dict[str, Any],
                     ground_truth: Dict[str, Any]) -> float:
        """
        Compute recall metric.
        
        Args:
            result: Result dictionary
            ground_truth: Ground truth dictionary
            
        Returns:
            Recall value
        """
        # Implementation depends on the benchmark type and data structure
        # This is a simplified example
        if 'predictions' in result and 'labels' in ground_truth:
            predictions = result['predictions']
            labels = ground_truth['labels']
            
            true_positives = sum(1 for p, l in zip(predictions, labels) if p == 1 and l == 1)
            false_negatives = sum(1 for p, l in zip(predictions, labels) if p == 0 and l == 1)
            
            if true_positives + false_negatives > 0:
                return true_positives / (true_positives + false_negatives)
            else:
                return 0.0
        
        return 0.0
    
    def _compute_mae(self, result: Dict[str, Any],
                  ground_truth: Dict[str, Any]) -> float:
        """
        Compute mean absolute error.
        
        Args:
            result: Result dictionary
            ground_truth: Ground truth dictionary
            
        Returns:
            MAE value
        """
        # Implementation depends on the benchmark type and data structure
        # This is a simplified example
        if 'predictions' in result and 'values' in ground_truth:
            predictions = result['predictions']
            values = ground_truth['values']
            
            if len(predictions) != len(values):
                return float('inf')
            
            return np.mean([abs(p - v) for p, v in zip(predictions, values)])
        
        return float('inf')
    
    def _compute_rmse(self, result: Dict[str, Any],
                   ground_truth: Dict[str, Any]) -> float:
        """
        Compute root mean squared error.
        
        Args:
            result: Result dictionary
            ground_truth: Ground truth dictionary
            
        Returns:
            RMSE value
        """
        # Implementation depends on the benchmark type and data structure
        # This is a simplified example
        if 'predictions' in result and 'values' in ground_truth:
            predictions = result['predictions']
            values = ground_truth['values']
            
            if len(predictions) != len(values):
                return float('inf')
            
            return np.sqrt(np.mean([(p - v) ** 2 for p, v in zip(predictions, values)]))
        
        return float('inf')


class Experiment:
    """
    Experiment class for running and tracking experiments.
    
    This class provides functionality for:
    - Defining experiment protocols
    - Tracking experiment runs
    - Ensuring reproducibility
    - Analyzing results
    """
    
    def __init__(self, name: str, experiment_type: Union[str, ExperimentType],
               description: str, version: str = "1.0.0",
               storage_dir: Optional[str] = None):
        """
        Initialize an experiment.
        
        Args:
            name: Name of the experiment
            experiment_type: Type of experiment
            description: Description of the experiment
            version: Version of the experiment
            storage_dir: Optional directory for storage
        """
        self.name = name
        
        # Convert experiment_type to enum if string
        if isinstance(experiment_type, str):
            experiment_type = ExperimentType(experiment_type)
        
        self.experiment_type = experiment_type
        self.description = description
        self.version = version
        self.created_at = time.time()
        self.runs = []
        self.metadata = {}
        self.parameters = {}
        
        # Set up storage directory
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), 'experiment_storage')
        
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize logger
        self.logger = logging.getLogger('experiment')
    
    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Set experiment parameters.
        
        Args:
            parameters: Dictionary of parameter name -> value
        """
        self.parameters = parameters
        self.logger.info(f"Set parameters for experiment {self.name}")
    
    def add_run(self, run_id: str, parameters: Dict[str, Any],
              results: Dict[str, Any],
              metrics: Dict[str, float],
              metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a run to the experiment.
        
        Args:
            run_id: Unique identifier for the run
            parameters: Parameters used for the run
            results: Results of the run
            metrics: Metrics computed for the run
            metadata: Optional run metadata
        """
        run = {
            'id': run_id,
            'parameters': parameters,
            'results': results,
            'metrics': metrics,
            'timestamp': time.time(),
            'metadata': metadata or {}
        }
        
        self.runs.append(run)
        self.logger.info(f"Added run {run_id} to experiment {self.name}")
    
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a run from the experiment.
        
        Args:
            run_id: ID of the run to get
            
        Returns:
            Run or None if not found
        """
        for run in self.runs:
            if run['id'] == run_id:
                return run
        
        return None
    
    def save(self) -> None:
        """Save the experiment to storage."""
        # Create directory for this experiment
        experiment_dir = os.path.join(self.storage_dir, self.name)
        os.makedirs(experiment_dir, exist_ok=True)
        
        # Save metadata
        metadata = {
            'name': self.name,
            'experiment_type': self.experiment_type.value,
            'description': self.description,
            'version': self.version,
            'created_at': self.created_at,
            'run_count': len(self.runs),
            'parameters': self.parameters,
            'metadata': self.metadata
        }
        
        metadata_path = os.path.join(experiment_dir, 'metadata.json')
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save runs
        runs_path = os.path.join(experiment_dir, 'runs.json')
        
        with open(runs_path, 'w') as f:
            json.dump(self.runs, f, indent=2)
        
        self.logger.info(f"Saved experiment {self.name} with {len(self.runs)} runs")
    
    @classmethod
    def load(cls, name: str, storage_dir: Optional[str] = None) -> 'Experiment':
        """
        Load an experiment from storage.
        
        Args:
            name: Name of the experiment
            storage_dir: Optional directory for storage
            
        Returns:
            Loaded experiment
        """
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), 'experiment_storage')
        
        experiment_dir = os.path.join(storage_dir, name)
        
        if not os.path.exists(experiment_dir):
            raise FileNotFoundError(f"Experiment {name} not found in {storage_dir}")
        
        # Load metadata
        metadata_path = os.path.join(experiment_dir, 'metadata.json')
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Create experiment
        experiment = cls(
            name=metadata['name'],
            experiment_type=metadata['experiment_type'],
            description=metadata['description'],
            version=metadata['version'],
            storage_dir=storage_dir
        )
        
        experiment.created_at = metadata['created_at']
        experiment.parameters = metadata['parameters']
        experiment.metadata = metadata['metadata']
        
        # Load runs
        runs_path = os.path.join(experiment_dir, 'runs.json')
        
        with open(runs_path, 'r') as f:
            experiment.runs = json.load(f)
        
        experiment.logger.info(f"Loaded experiment {name} with {len(experiment.runs)} runs")
        return experiment
    
    def analyze(self, analysis_type: Union[str, AnalysisType] = AnalysisType.DESCRIPTIVE,
              parameters: Optional[List[str]] = None,
              metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze experiment results.
        
        Args:
            analysis_type: Type of analysis to perform
            parameters: Optional list of parameters to include in the analysis
            metrics: Optional list of metrics to include in the analysis
            
        Returns:
            Analysis results
        """
        # Convert analysis_type to enum if string
        if isinstance(analysis_type, str):
            analysis_type = AnalysisType(analysis_type)
        
        # Extract data from runs
        data = []
        
        for run in self.runs:
            run_data = {}
            
            # Add parameters
            for param, value in run['parameters'].items():
                if parameters is None or param in parameters:
                    run_data[f"param_{param}"] = value
            
            # Add metrics
            for metric, value in run['metrics'].items():
                if metrics is None or metric in metrics:
                    run_data[f"metric_{metric}"] = value
            
            # Add run information
            run_data['run_id'] = run['id']
            run_data['timestamp'] = run['timestamp']
            
            data.append(run_data)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Perform analysis
        if analysis_type == AnalysisType.DESCRIPTIVE:
            return self._descriptive_analysis(df, parameters, metrics)
        elif analysis_type == AnalysisType.INFERENTIAL:
            return self._inferential_analysis(df, parameters, metrics)
        elif analysis_type == AnalysisType.CORRELATION:
            return self._correlation_analysis(df, parameters, metrics)
        elif analysis_type == AnalysisType.REGRESSION:
            return self._regression_analysis(df, parameters, metrics)
        else:
            # Default to descriptive analysis
            return self._descriptive_analysis(df, parameters, metrics)
    
    def _descriptive_analysis(self, df: pd.DataFrame,
                           parameters: Optional[List[str]] = None,
                           metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform descriptive analysis on experiment results.
        
        Args:
            df: DataFrame containing run data
            parameters: Optional list of parameters to include
            metrics: Optional list of metrics to include
            
        Returns:
            Analysis results
        """
        results = {
            'experiment': self.name,
            'experiment_type': self.experiment_type.value,
            'analysis_type': AnalysisType.DESCRIPTIVE.value,
            'run_count': len(self.runs),
            'parameters': {},
            'metrics': {}
        }
        
        # Extract parameter columns
        param_cols = [col for col in df.columns if col.startswith('param_')]
        
        # Filter by specified parameters
        if parameters:
            param_cols = [col for col in param_cols if col[6:] in parameters]
        
        # Compute statistics for parameters
        for col in param_cols:
            param_name = col[6:]  # Remove 'param_' prefix
            
            # Skip non-numeric parameters
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue
            
            results['parameters'][param_name] = {
                'mean': df[col].mean(),
                'std': df[col].std(),
                'min': df[col].min(),
                'max': df[col].max(),
                'median': df[col].median()
            }
        
        # Extract metric columns
        metric_cols = [col for col in df.columns if col.startswith('metric_')]
        
        # Filter by specified metrics
        if metrics:
            metric_cols = [col for col in metric_cols if col[7:] in metrics]
        
        # Compute statistics for metrics
        for col in metric_cols:
            metric_name = col[7:]  # Remove 'metric_' prefix
            
            results['metrics'][metric_name] = {
                'mean': df[col].mean(),
                'std': df[col].std(),
                'min': df[col].min(),
                'max': df[col].max(),
                'median': df[col].median(),
                'quartiles': [
                    df[col].quantile(0.25),
                    df[col].quantile(0.5),
                    df[col].quantile(0.75)
                ]
            }
        
        return results
    
    def _inferential_analysis(self, df: pd.DataFrame,
                           parameters: Optional[List[str]] = None,
                           metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform inferential analysis on experiment results.
        
        Args:
            df: DataFrame containing run data
            parameters: Optional list of parameters to include
            metrics: Optional list of metrics to include
            
        Returns:
            Analysis results
        """
        # In a real implementation, this would perform hypothesis tests,
        # confidence intervals, etc.
        # For now, just return a placeholder
        
        return {
            'experiment': self.name,
            'experiment_type': self.experiment_type.value,
            'analysis_type': AnalysisType.INFERENTIAL.value,
            'run_count': len(self.runs),
            'note': "Inferential analysis not implemented yet"
        }
    
    def _correlation_analysis(self, df: pd.DataFrame,
                           parameters: Optional[List[str]] = None,
                           metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform correlation analysis on experiment results.
        
        Args:
            df: DataFrame containing run data
            parameters: Optional list of parameters to include
            metrics: Optional list of metrics to include
            
        Returns:
            Analysis results
        """
        results = {
            'experiment': self.name,
            'experiment_type': self.experiment_type.value,
            'analysis_type': AnalysisType.CORRELATION.value,
            'run_count': len(self.runs),
            'parameter_correlations': {},
            'metric_correlations': {},
            'parameter_metric_correlations': {}
        }
        
        # Extract parameter columns
        param_cols = [col for col in df.columns if col.startswith('param_')]
        
        # Filter by specified parameters
        if parameters:
            param_cols = [col for col in param_cols if col[6:] in parameters]
        
        # Extract metric columns
        metric_cols = [col for col in df.columns if col.startswith('metric_')]
        
        # Filter by specified metrics
        if metrics:
            metric_cols = [col for col in metric_cols if col[7:] in metrics]
        
        # Compute parameter correlations
        if len(param_cols) > 1:
            param_corr = df[param_cols].corr()
            
            for i, param1 in enumerate(param_cols):
                param_name1 = param1[6:]  # Remove 'param_' prefix
                results['parameter_correlations'][param_name1] = {}
                
                for j, param2 in enumerate(param_cols):
                    if i != j:
                        param_name2 = param2[6:]  # Remove 'param_' prefix
                        results['parameter_correlations'][param_name1][param_name2] = param_corr.loc[param1, param2]
        
        # Compute metric correlations
        if len(metric_cols) > 1:
            metric_corr = df[metric_cols].corr()
            
            for i, metric1 in enumerate(metric_cols):
                metric_name1 = metric1[7:]  # Remove 'metric_' prefix
                results['metric_correlations'][metric_name1] = {}
                
                for j, metric2 in enumerate(metric_cols):
                    if i != j:
                        metric_name2 = metric2[7:]  # Remove 'metric_' prefix
                        results['metric_correlations'][metric_name1][metric_name2] = metric_corr.loc[metric1, metric2]
        
        # Compute parameter-metric correlations
        if param_cols and metric_cols:
            param_metric_corr = df[param_cols + metric_cols].corr()
            
            for param in param_cols:
                param_name = param[6:]  # Remove 'param_' prefix
                results['parameter_metric_correlations'][param_name] = {}
                
                for metric in metric_cols:
                    metric_name = metric[7:]  # Remove 'metric_' prefix
                    results['parameter_metric_correlations'][param_name][metric_name] = param_metric_corr.loc[param, metric]
        
        return results
    
    def _regression_analysis(self, df: pd.DataFrame,
                          parameters: Optional[List[str]] = None,
                          metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform regression analysis on experiment results.
        
        Args:
            df: DataFrame containing run data
            parameters: Optional list of parameters to include
            metrics: Optional list of metrics to include
            
        Returns:
            Analysis results
        """
        # In a real implementation, this would fit regression models
        # For now, just return a placeholder
        
        return {
            'experiment': self.name,
            'experiment_type': self.experiment_type.value,
            'analysis_type': AnalysisType.REGRESSION.value,
            'run_count': len(self.runs),
            'note': "Regression analysis not implemented yet"
        }
    
    def plot(self, plot_type: str,
           x_param: Optional[str] = None,
           y_metric: Optional[str] = None,
           output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a plot of experiment results.
        
        Args:
            plot_type: Type of plot to generate
            x_param: Optional parameter to use for the x-axis
            y_metric: Optional metric to use for the y-axis
            output_file: Optional file to save the plot to
            
        Returns:
            Plot data
        """
        try:
            import matplotlib.pyplot as plt
            
            # Extract data from runs
            data = []
            
            for run in self.runs:
                run_data = {}
                
                # Add parameters
                for param, value in run['parameters'].items():
                    run_data[f"param_{param}"] = value
                
                # Add metrics
                for metric, value in run['metrics'].items():
                    run_data[f"metric_{metric}"] = value
                
                # Add run information
                run_data['run_id'] = run['id']
                run_data['timestamp'] = run['timestamp']
                
                data.append(run_data)
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # Generate plot
            plt.figure(figsize=(10, 6))
            
            if plot_type == 'line':
                self._generate_line_plot(df, x_param, y_metric)
            elif plot_type == 'scatter':
                self._generate_scatter_plot(df, x_param, y_metric)
            elif plot_type == 'bar':
                self._generate_bar_plot(df, x_param, y_metric)
            elif plot_type == 'box':
                self._generate_box_plot(df, x_param, y_metric)
            elif plot_type == 'histogram':
                self._generate_histogram_plot(df, y_metric)
            else:
                raise ValueError(f"Unknown plot type: {plot_type}")
            
            plt.title(f"{self.name} - {plot_type.capitalize()} Plot")
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Save to file if specified
            if output_file:
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                plt.close()
            
            return {
                'experiment': self.name,
                'plot_type': plot_type,
                'x_param': x_param,
                'y_metric': y_metric,
                'output_file': output_file
            }
        
        except Exception as e:
            self.logger.error(f"Error generating plot: {str(e)}")
            return {'error': str(e)}
    
    def _generate_line_plot(self, df: pd.DataFrame,
                         x_param: Optional[str] = None,
                         y_metric: Optional[str] = None) -> None:
        """
        Generate a line plot.
        
        Args:
            df: DataFrame containing run data
            x_param: Parameter to use for the x-axis
            y_metric: Metric to use for the y-axis
        """
        x_col = f"param_{x_param}" if x_param else 'timestamp'
        y_col = f"metric_{y_metric}" if y_metric else None
        
        if not y_col:
            # If no y metric specified, use all metrics
            metric_cols = [col for col in df.columns if col.startswith('metric_')]
            
            for col in metric_cols:
                metric_name = col[7:]  # Remove 'metric_' prefix
                plt.plot(df[x_col], df[col], marker='o', label=metric_name)
        else:
            plt.plot(df[x_col], df[y_col], marker='o')
        
        plt.xlabel(x_param if x_param else 'Time')
        plt.ylabel(y_metric if y_metric else 'Metrics')
        
        if not y_metric and len([col for col in df.columns if col.startswith('metric_')]) > 1:
            plt.legend()
    
    def _generate_scatter_plot(self, df: pd.DataFrame,
                            x_param: Optional[str] = None,
                            y_metric: Optional[str] = None) -> None:
        """
        Generate a scatter plot.
        
        Args:
            df: DataFrame containing run data
            x_param: Parameter to use for the x-axis
            y_metric: Metric to use for the y-axis
        """
        if not x_param or not y_metric:
            raise ValueError("Both x_param and y_metric must be specified for scatter plots")
        
        x_col = f"param_{x_param}"
        y_col = f"metric_{y_metric}"
        
        plt.scatter(df[x_col], df[y_col], alpha=0.7)
        plt.xlabel(x_param)
        plt.ylabel(y_metric)
    
    def _generate_bar_plot(self, df: pd.DataFrame,
                        x_param: Optional[str] = None,
                        y_metric: Optional[str] = None) -> None:
        """
        Generate a bar plot.
        
        Args:
            df: DataFrame containing run data
            x_param: Parameter to use for the x-axis
            y_metric: Metric to use for the y-axis
        """
        if not x_param or not y_metric:
            raise ValueError("Both x_param and y_metric must be specified for bar plots")
        
        x_col = f"param_{x_param}"
        y_col = f"metric_{y_metric}"
        
        # If x is categorical, use as is
        if pd.api.types.is_numeric_dtype(df[x_col]):
            # If x is numeric, bin it
            df['x_binned'] = pd.cut(df[x_col], bins=10)
            x_col = 'x_binned'
        
        # Compute mean y values for each x bin
        grouped = df.groupby(x_col)[y_col].mean()
        
        grouped.plot(kind='bar')
        plt.xlabel(x_param)
        plt.ylabel(y_metric)
    
    def _generate_box_plot(self, df: pd.DataFrame,
                        x_param: Optional[str] = None,
                        y_metric: Optional[str] = None) -> None:
        """
        Generate a box plot.
        
        Args:
            df: DataFrame containing run data
            x_param: Parameter to use for the x-axis
            y_metric: Metric to use for the y-axis
        """
        if not y_metric:
            raise ValueError("y_metric must be specified for box plots")
        
        y_col = f"metric_{y_metric}"
        
        if x_param:
            x_col = f"param_{x_param}"
            
            # If x is categorical, use as is
            if pd.api.types.is_numeric_dtype(df[x_col]):
                # If x is numeric, bin it
                df['x_binned'] = pd.cut(df[x_col], bins=5)
                x_col = 'x_binned'
            
            df.boxplot(column=y_col, by=x_col)
            plt.xlabel(x_param)
        else:
            plt.boxplot(df[y_col])
            plt.xticks([1], [y_metric])
        
        plt.ylabel(y_metric)
    
    def _generate_histogram_plot(self, df: pd.DataFrame,
                              y_metric: Optional[str] = None) -> None:
        """
        Generate a histogram plot.
        
        Args:
            df: DataFrame containing run data
            y_metric: Metric to use for the histogram
        """
        if not y_metric:
            raise ValueError("y_metric must be specified for histogram plots")
        
        y_col = f"metric_{y_metric}"
        
        plt.hist(df[y_col], bins=20, alpha=0.7, edgecolor='black')
        plt.xlabel(y_metric)
        plt.ylabel('Frequency')


class ResearchPaper:
    """
    Research paper generator.
    
    This class provides functionality for:
    - Generating research paper templates
    - Formatting experimental results for publication
    - Creating publication-ready figures
    """
    
    def __init__(self, title: str, authors: List[str],
               abstract: str, storage_dir: Optional[str] = None):
        """
        Initialize a research paper.
        
        Args:
            title: Paper title
            authors: List of authors
            abstract: Paper abstract
            storage_dir: Optional directory for storage
        """
        self.title = title
        self.authors = authors
        self.abstract = abstract
        self.sections = {}
        self.figures = {}
        self.tables = {}
        self.bibliography = []
        self.metadata = {}
        
        # Set up storage directory
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), 'paper_storage')
        
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize logger
        self.logger = logging.getLogger('research_paper')
    
    def add_section(self, section_name: str, content: str) -> None:
        """
        Add a section to the paper.
        
        Args:
            section_name: Name of the section
            content: Content of the section
        """
        self.sections[section_name] = content
        self.logger.info(f"Added section: {section_name}")
    
    def add_figure(self, figure_id: str, caption: str, 
                 file_path: Optional[str] = None,
                 data: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a figure to the paper.
        
        Args:
            figure_id: Unique identifier for the figure
            caption: Caption for the figure
            file_path: Optional path to the figure file
            data: Optional figure data for generation
        """
        self.figures[figure_id] = {
            'caption': caption,
            'file_path': file_path,
            'data': data
        }
        
        self.logger.info(f"Added figure: {figure_id}")
    
    def add_table(self, table_id: str, caption: str, 
                data: List[List[str]]) -> None:
        """
        Add a table to the paper.
        
        Args:
            table_id: Unique identifier for the table
            caption: Caption for the table
            data: Table data as a list of rows, each row being a list of cells
        """
        self.tables[table_id] = {
            'caption': caption,
            'data': data
        }
        
        self.logger.info(f"Added table: {table_id}")
    
    def add_reference(self, reference: Dict[str, str]) -> None:
        """
        Add a reference to the bibliography.
        
        Args:
            reference: Reference data (authors, title, year, etc.)
        """
        self.bibliography.append(reference)
        self.logger.info(f"Added reference: {reference.get('title', 'Unknown')}")
    
    def save(self) -> None:
        """Save the paper to storage."""
        # Create directory for this paper
        paper_dir = os.path.join(self.storage_dir, self._get_filename())
        os.makedirs(paper_dir, exist_ok=True)
        
        # Save metadata
        metadata = {
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'sections': list(self.sections.keys()),
            'figures': list(self.figures.keys()),
            'tables': list(self.tables.keys()),
            'bibliography_count': len(self.bibliography),
            'metadata': self.metadata
        }
        
        metadata_path = os.path.join(paper_dir, 'metadata.json')
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save sections
        sections_dir = os.path.join(paper_dir, 'sections')
        os.makedirs(sections_dir, exist_ok=True)
        
        for section_name, content in self.sections.items():
            section_path = os.path.join(sections_dir, f"{self._sanitize_filename(section_name)}.txt")
            
            with open(section_path, 'w') as f:
                f.write(content)
        
        # Save figures
        figures_dir = os.path.join(paper_dir, 'figures')
        os.makedirs(figures_dir, exist_ok=True)
        
        for figure_id, figure_data in self.figures.items():
            figure_path = os.path.join(figures_dir, f"{figure_id}.json")
            
            with open(figure_path, 'w') as f:
                json.dump(figure_data, f, indent=2)
        
        # Save tables
        tables_dir = os.path.join(paper_dir, 'tables')
        os.makedirs(tables_dir, exist_ok=True)
        
        for table_id, table_data in self.tables.items():
            table_path = os.path.join(tables_dir, f"{table_id}.json")
            
            with open(table_path, 'w') as f:
                json.dump(table_data, f, indent=2)
        
        # Save bibliography
        bibliography_path = os.path.join(paper_dir, 'bibliography.json')
        
        with open(bibliography_path, 'w') as f:
            json.dump(self.bibliography, f, indent=2)
        
        self.logger.info(f"Saved paper: {self.title}")
    
    def _get_filename(self) -> str:
        """
        Get a filename for the paper based on its title.
        
        Returns:
            Sanitized filename
        """
        return self._sanitize_filename(self.title)
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string for use as a filename.
        
        Args:
            name: String to sanitize
            
        Returns:
            Sanitized string
        """
        # Replace spaces with underscores
        name = name.replace(' ', '_')
        
        # Remove special characters
        name = ''.join(c for c in name if c.isalnum() or c in '_-')
        
        # Limit length
        name = name[:100]
        
        return name
    
    @classmethod
    def load(cls, title: str, storage_dir: Optional[str] = None) -> 'ResearchPaper':
        """
        Load a paper from storage.
        
        Args:
            title: Title of the paper (used to find the file)
            storage_dir: Optional directory for storage
            
        Returns:
            Loaded paper
        """
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), 'paper_storage')
        
        # Sanitize title for filename
        filename = title.replace(' ', '_')
        filename = ''.join(c for c in filename if c.isalnum() or c in '_-')
        filename = filename[:100]
        
        paper_dir = os.path.join(storage_dir, filename)
        
        if not os.path.exists(paper_dir):
            raise FileNotFoundError(f"Paper '{title}' not found in {storage_dir}")
        
        # Load metadata
        metadata_path = os.path.join(paper_dir, 'metadata.json')
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Create paper
        paper = cls(
            title=metadata['title'],
            authors=metadata['authors'],
            abstract=metadata['abstract'],
            storage_dir=storage_dir
        )
        
        paper.metadata = metadata.get('metadata', {})
        
        # Load sections
        sections_dir = os.path.join(paper_dir, 'sections')
        
        if os.path.exists(sections_dir):
            for section_file in os.listdir(sections_dir):
                if section_file.endswith('.txt'):
                    section_name = section_file[:-4]  # Remove '.txt'
                    section_path = os.path.join(sections_dir, section_file)
                    
                    with open(section_path, 'r') as f:
                        content = f.read()
                    
                    paper.sections[section_name] = content
        
        # Load figures
        figures_dir = os.path.join(paper_dir, 'figures')
        
        if os.path.exists(figures_dir):
            for figure_file in os.listdir(figures_dir):
                if figure_file.endswith('.json'):
                    figure_id = figure_file[:-5]  # Remove '.json'
                    figure_path = os.path.join(figures_dir, figure_file)
                    
                    with open(figure_path, 'r') as f:
                        figure_data = json.load(f)
                    
                    paper.figures[figure_id] = figure_data
        
        # Load tables
        tables_dir = os.path.join(paper_dir, 'tables')
        
        if os.path.exists(tables_dir):
            for table_file in os.listdir(tables_dir):
                if table_file.endswith('.json'):
                    table_id = table_file[:-5]  # Remove '.json'
                    table_path = os.path.join(tables_dir, table_file)
                    
                    with open(table_path, 'r') as f:
                        table_data = json.load(f)
                    
                    paper.tables[table_id] = table_data
        
        # Load bibliography
        bibliography_path = os.path.join(paper_dir, 'bibliography.json')
        
        if os.path.exists(bibliography_path):
            with open(bibliography_path, 'r') as f:
                paper.bibliography = json.load(f)
        
        paper.logger.info(f"Loaded paper: {title}")
        return paper
    
    def generate_latex(self, output_path: Optional[str] = None) -> str:
        """
        Generate LaTeX source for the paper.
        
        Args:
            output_path: Optional path to write LaTeX file
            
        Returns:
            LaTeX source
        """
        latex = []
        
        # Document class
        latex.append("\\documentclass[conference]{IEEEtran}")
        latex.append("\\usepackage{graphicx}")
        latex.append("\\usepackage{amsmath}")
        latex.append("\\usepackage{algorithm}")
        latex.append("\\usepackage{algorithmic}")
        latex.append("\\usepackage{booktabs}")
        latex.append("\\usepackage{multirow}")
        latex.append("")
        
        # Begin document
        latex.append("\\begin{document}")
        latex.append("")
        
        # Title
        latex.append(f"\\title{{{self.title}}}")
        latex.append("")
        
        # Authors
        if self.authors:
            author_str = " \\and ".join(self.authors)
            latex.append(f"\\author{{{author_str}}}")
            latex.append("")
        
        # Maketitle
        latex.append("\\maketitle")
        latex.append("")
        
        # Abstract
        latex.append("\\begin{abstract}")
        latex.append(self.abstract)
        latex.append("\\end{abstract}")
        latex.append("")
        
        # Sections
        for section_name, content in self.sections.items():
            latex.append(f"\\section{{{section_name}}}")
            latex.append(content)
            latex.append("")
        
        # Figures
        for figure_id, figure_data in self.figures.items():
            if figure_data.get('file_path'):
                latex.append("\\begin{figure}[t]")
                latex.append("\\centering")
                latex.append(f"\\includegraphics[width=\\columnwidth]{{{figure_data['file_path']}}}")
                latex.append(f"\\caption{{{figure_data['caption']}}}")
                latex.append(f"\\label{{fig:{figure_id}}}")
                latex.append("\\end{figure}")
                latex.append("")
        
        # Tables
        for table_id, table_data in self.tables.items():
            data = table_data['data']
            if data and all(isinstance(row, list) for row in data):
                latex.append("\\begin{table}[t]")
                latex.append("\\centering")
                latex.append("\\begin{tabular}{" + "c" * len(data[0]) + "}")
                latex.append("\\toprule")
                
                # Header
                latex.append(" & ".join(data[0]) + " \\\\")
                latex.append("\\midrule")
                
                # Body
                for row in data[1:]:
                    latex.append(" & ".join(row) + " \\\\")
                
                latex.append("\\bottomrule")
                latex.append("\\end{tabular}")
                latex.append(f"\\caption{{{table_data['caption']}}}")
                latex.append(f"\\label{{tab:{table_id}}}")
                latex.append("\\end{table}")
                latex.append("")
        
        # Bibliography
        if self.bibliography:
            latex.append("\\begin{thebibliography}{" + str(len(self.bibliography)) + "}")
            latex.append("")
            
            for i, ref in enumerate(self.bibliography, 1):
                if 'authors' in ref and 'title' in ref and 'year' in ref:
                    latex.append(f"\\bibitem{{{i}}}")
                    latex.append(f"{ref['authors']}, ``{ref['title']},'' {ref.get('journal', '')}, {ref.get('volume', '')}, {ref.get('number', '')}, {ref['year']}.")
                    latex.append("")
            
            latex.append("\\end{thebibliography}")
            latex.append("")
        
        # End document
        latex.append("\\end{document}")
        
        # Join and return
        latex_source = "\n".join(latex)
        
        # Write to file if requested
        if output_path:
            with open(output_path, 'w') as f:
                f.write(latex_source)
            
            self.logger.info(f"Generated LaTeX source and saved to {output_path}")
        
        return latex_source
    
    @staticmethod
    def generate_template(title: str, authors: List[str], 
                       abstract: str) -> 'ResearchPaper':
        """
        Generate a template for a research paper.
        
        Args:
            title: Paper title
            authors: List of authors
            abstract: Paper abstract
            
        Returns:
            Research paper template
        """
        paper = ResearchPaper(title, authors, abstract)
        
        # Add standard sections
        paper.add_section("Introduction", "The introduction provides background and context for the research. It should clearly state the problem being addressed and why it's important.")
        
        paper.add_section("Related Work", "This section discusses prior research related to the current work. It should highlight the gaps in existing research that the current paper aims to fill.")
        
        paper.add_section("Method", "The method section details the approach used to solve the problem. It should include enough information for others to replicate the work.")
        
        paper.add_section("Experiments", "This section describes the experimental setup and evaluation methodology. It should clearly state the research questions and how the experiments answer them.")
        
        paper.add_section("Results", "The results section presents the findings of the experiments. It should include tables and figures to illustrate the results.")
        
        paper.add_section("Discussion", "This section interprets the results and discusses their implications. It should address any limitations of the current approach and suggest future directions.")
        
        paper.add_section("Conclusion", "The conclusion summarizes the main findings and contributions of the paper. It should restate the importance of the work and its impact on the field.")
        
        return paper


class AcademicFramework:
    """
    Academic Research Framework for the Code Deep Dive Analyzer.
    
    This class provides:
    - Benchmark dataset management
    - Experiment tracking
    - Research paper generation
    - Statistical analysis tools
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the academic framework.
        
        Args:
            storage_dir: Optional directory for storage
        """
        # Set up storage directory
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), 'academic_storage')
        
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize directories
        self.benchmark_dir = os.path.join(storage_dir, 'benchmarks')
        self.experiment_dir = os.path.join(storage_dir, 'experiments')
        self.paper_dir = os.path.join(storage_dir, 'papers')
        
        os.makedirs(self.benchmark_dir, exist_ok=True)
        os.makedirs(self.experiment_dir, exist_ok=True)
        os.makedirs(self.paper_dir, exist_ok=True)
        
        # Initialize logger
        self.logger = logging.getLogger('academic_framework')
        
        # Initialize collections
        self.benchmarks = {}  # name -> BenchmarkDataset
        self.experiments = {}  # name -> Experiment
        self.papers = {}  # title -> ResearchPaper
        
        # Load existing data
        self._load_data()
    
    def _load_data(self) -> None:
        """Load existing data from storage."""
        # Load benchmarks
        for benchmark_name in os.listdir(self.benchmark_dir):
            try:
                benchmark = BenchmarkDataset.load(benchmark_name, self.benchmark_dir)
                self.benchmarks[benchmark_name] = benchmark
                self.logger.info(f"Loaded benchmark: {benchmark_name}")
            except Exception as e:
                self.logger.error(f"Error loading benchmark {benchmark_name}: {str(e)}")
        
        # Load experiments
        for experiment_name in os.listdir(self.experiment_dir):
            try:
                experiment = Experiment.load(experiment_name, self.experiment_dir)
                self.experiments[experiment_name] = experiment
                self.logger.info(f"Loaded experiment: {experiment_name}")
            except Exception as e:
                self.logger.error(f"Error loading experiment {experiment_name}: {str(e)}")
        
        # Load papers
        for paper_title in os.listdir(self.paper_dir):
            try:
                paper = ResearchPaper.load(paper_title, self.paper_dir)
                self.papers[paper.title] = paper
                self.logger.info(f"Loaded paper: {paper.title}")
            except Exception as e:
                self.logger.error(f"Error loading paper {paper_title}: {str(e)}")
    
    def create_benchmark(self, name: str, benchmark_type: Union[str, BenchmarkType],
                      description: str, version: str = "1.0.0") -> BenchmarkDataset:
        """
        Create a new benchmark dataset.
        
        Args:
            name: Name of the benchmark
            benchmark_type: Type of benchmark
            description: Description of the benchmark
            version: Version of the benchmark
            
        Returns:
            Created benchmark dataset
        """
        benchmark = BenchmarkDataset(
            name=name,
            benchmark_type=benchmark_type,
            description=description,
            version=version,
            storage_dir=self.benchmark_dir
        )
        
        self.benchmarks[name] = benchmark
        self.logger.info(f"Created benchmark: {name}")
        return benchmark
    
    def get_benchmark(self, name: str) -> Optional[BenchmarkDataset]:
        """
        Get a benchmark dataset by name.
        
        Args:
            name: Name of the benchmark
            
        Returns:
            Benchmark dataset or None if not found
        """
        return self.benchmarks.get(name)
    
    def delete_benchmark(self, name: str) -> bool:
        """
        Delete a benchmark dataset.
        
        Args:
            name: Name of the benchmark
            
        Returns:
            Deletion success
        """
        if name not in self.benchmarks:
            return False
        
        # Remove from memory
        del self.benchmarks[name]
        
        # Remove from storage
        benchmark_path = os.path.join(self.benchmark_dir, name)
        if os.path.exists(benchmark_path):
            shutil.rmtree(benchmark_path)
        
        self.logger.info(f"Deleted benchmark: {name}")
        return True
    
    def create_experiment(self, name: str, experiment_type: Union[str, ExperimentType],
                       description: str, version: str = "1.0.0") -> Experiment:
        """
        Create a new experiment.
        
        Args:
            name: Name of the experiment
            experiment_type: Type of experiment
            description: Description of the experiment
            version: Version of the experiment
            
        Returns:
            Created experiment
        """
        experiment = Experiment(
            name=name,
            experiment_type=experiment_type,
            description=description,
            version=version,
            storage_dir=self.experiment_dir
        )
        
        self.experiments[name] = experiment
        self.logger.info(f"Created experiment: {name}")
        return experiment
    
    def get_experiment(self, name: str) -> Optional[Experiment]:
        """
        Get an experiment by name.
        
        Args:
            name: Name of the experiment
            
        Returns:
            Experiment or None if not found
        """
        return self.experiments.get(name)
    
    def delete_experiment(self, name: str) -> bool:
        """
        Delete an experiment.
        
        Args:
            name: Name of the experiment
            
        Returns:
            Deletion success
        """
        if name not in self.experiments:
            return False
        
        # Remove from memory
        del self.experiments[name]
        
        # Remove from storage
        experiment_path = os.path.join(self.experiment_dir, name)
        if os.path.exists(experiment_path):
            shutil.rmtree(experiment_path)
        
        self.logger.info(f"Deleted experiment: {name}")
        return True
    
    def create_paper(self, title: str, authors: List[str],
                  abstract: str) -> ResearchPaper:
        """
        Create a new research paper.
        
        Args:
            title: Paper title
            authors: List of authors
            abstract: Paper abstract
            
        Returns:
            Created paper
        """
        paper = ResearchPaper(
            title=title,
            authors=authors,
            abstract=abstract,
            storage_dir=self.paper_dir
        )
        
        self.papers[title] = paper
        self.logger.info(f"Created paper: {title}")
        return paper
    
    def get_paper(self, title: str) -> Optional[ResearchPaper]:
        """
        Get a paper by title.
        
        Args:
            title: Paper title
            
        Returns:
            Paper or None if not found
        """
        return self.papers.get(title)
    
    def delete_paper(self, title: str) -> bool:
        """
        Delete a paper.
        
        Args:
            title: Paper title
            
        Returns:
            Deletion success
        """
        if title not in self.papers:
            return False
        
        # Remove from memory
        paper = self.papers[title]
        del self.papers[title]
        
        # Remove from storage
        paper_path = os.path.join(self.paper_dir, paper._get_filename())
        if os.path.exists(paper_path):
            shutil.rmtree(paper_path)
        
        self.logger.info(f"Deleted paper: {title}")
        return True
    
    def create_paper_from_experiment(self, experiment_name: str, title: str,
                                authors: List[str]) -> Optional[ResearchPaper]:
        """
        Create a research paper from an experiment.
        
        Args:
            experiment_name: Name of the experiment
            title: Paper title
            authors: List of authors
            
        Returns:
            Created paper or None if experiment not found
        """
        experiment = self.get_experiment(experiment_name)
        if not experiment:
            return None
        
        # Create abstract from experiment description
        abstract = f"This paper presents the results of the {experiment.name} experiment. {experiment.description}"
        
        # Create paper
        paper = self.create_paper(title, authors, abstract)
        
        # Add sections
        paper.add_section("Introduction", f"This paper presents the {experiment.name} experiment, which aims to investigate {experiment.description}.")
        
        paper.add_section("Method", f"We designed an experiment of type {experiment.experiment_type.value} to evaluate the performance of our system. The experiment parameters were as follows:\n\n" + 
                        "\n".join([f"- {key}: {value}" for key, value in experiment.parameters.items()]))
        
        # Add results section
        results_section = "We conducted the experiment with the following parameters:\n\n"
        
        # Add a table of experiment parameters
        if experiment.parameters:
            table_data = [["Parameter", "Value"]]
            for key, value in experiment.parameters.items():
                table_data.append([key, str(value)])
            
            paper.add_table("experiment_parameters", "Experiment Parameters", table_data)
            
            results_section += "See Table \\ref{tab:experiment_parameters} for the experiment parameters.\n\n"
        
        # Add results from runs
        if experiment.runs:
            results_section += "The experiment was run with various parameter configurations. The results are summarized below:\n\n"
            
            # Create a table of run results
            metrics_set = set()
            for run in experiment.runs:
                metrics_set.update(run['metrics'].keys())
            
            metrics_list = sorted(list(metrics_set))
            
            table_data = [["Run ID"] + metrics_list]
            for run in experiment.runs:
                row = [run['id']]
                for metric in metrics_list:
                    row.append(str(round(run['metrics'].get(metric, 0), 4)))
                
                table_data.append(row)
            
            paper.add_table("experiment_results", "Experiment Results", table_data)
            
            results_section += "See Table \\ref{tab:experiment_results} for the detailed results."
        
        paper.add_section("Results", results_section)
        
        # Add conclusion
        paper.add_section("Conclusion", "In this paper, we presented the results of our experiment. The findings have important implications for our understanding of the problem domain.")
        
        return paper
    
    def generate_comparison_experiment(self, name: str, systems: List[str],
                                   benchmark_name: str,
                                   description: Optional[str] = None) -> Optional[Experiment]:
        """
        Generate a comparison experiment between systems on a benchmark.
        
        Args:
            name: Name for the experiment
            systems: List of system names to compare
            benchmark_name: Name of the benchmark to use
            description: Optional description for the experiment
            
        Returns:
            Created experiment or None if benchmark not found
        """
        benchmark = self.get_benchmark(benchmark_name)
        if not benchmark:
            return None
        
        if not description:
            description = f"Comparison of {', '.join(systems)} on the {benchmark_name} benchmark"
        
        # Create experiment
        experiment = self.create_experiment(
            name=name,
            experiment_type=ExperimentType.COMPARATIVE,
            description=description
        )
        
        # Set parameters
        experiment.set_parameters({
            'systems': systems,
            'benchmark': benchmark_name,
            'metrics': ['accuracy', 'precision', 'recall', 'f1_score']
        })
        
        return experiment
    
    def generate_ablation_experiment(self, name: str, base_system: str,
                                components: List[str],
                                benchmark_name: str,
                                description: Optional[str] = None) -> Optional[Experiment]:
        """
        Generate an ablation experiment to test component importance.
        
        Args:
            name: Name for the experiment
            base_system: Name of the base system
            components: List of component names to ablate
            benchmark_name: Name of the benchmark to use
            description: Optional description for the experiment
            
        Returns:
            Created experiment or None if benchmark not found
        """
        benchmark = self.get_benchmark(benchmark_name)
        if not benchmark:
            return None
        
        if not description:
            description = f"Ablation study of {base_system} components ({', '.join(components)}) on the {benchmark_name} benchmark"
        
        # Create experiment
        experiment = self.create_experiment(
            name=name,
            experiment_type=ExperimentType.ABLATION,
            description=description
        )
        
        # Set parameters
        experiment.set_parameters({
            'base_system': base_system,
            'components': components,
            'benchmark': benchmark_name,
            'metrics': ['accuracy', 'precision', 'recall', 'f1_score']
        })
        
        return experiment
    
    def generate_baseline_benchmarks(self) -> List[str]:
        """
        Generate a set of baseline benchmarks for code analysis.
        
        Returns:
            List of created benchmark names
        """
        created_benchmarks = []
        
        # Code Quality Benchmark
        code_quality = self.create_benchmark(
            name="code_quality_baseline",
            benchmark_type=BenchmarkType.CODE_QUALITY,
            description="Baseline benchmark for evaluating code quality analysis"
        )
        
        created_benchmarks.append(code_quality.name)
        
        # Pattern Recognition Benchmark
        pattern_recognition = self.create_benchmark(
            name="pattern_recognition_baseline",
            benchmark_type=BenchmarkType.PATTERN_RECOGNITION,
            description="Baseline benchmark for evaluating design pattern recognition"
        )
        
        created_benchmarks.append(pattern_recognition.name)
        
        # Complexity Benchmark
        complexity = self.create_benchmark(
            name="complexity_baseline",
            benchmark_type=BenchmarkType.COMPLEXITY,
            description="Baseline benchmark for evaluating code complexity analysis"
        )
        
        created_benchmarks.append(complexity.name)
        
        # Maintainability Benchmark
        maintainability = self.create_benchmark(
            name="maintainability_baseline",
            benchmark_type=BenchmarkType.MAINTAINABILITY,
            description="Baseline benchmark for evaluating code maintainability analysis"
        )
        
        created_benchmarks.append(maintainability.name)
        
        # Security Benchmark
        security = self.create_benchmark(
            name="security_baseline",
            benchmark_type=BenchmarkType.SECURITY,
            description="Baseline benchmark for evaluating security vulnerability detection"
        )
        
        created_benchmarks.append(security.name)
        
        return created_benchmarks
    
    def save_all(self) -> None:
        """Save all benchmarks, experiments, and papers."""
        for benchmark in self.benchmarks.values():
            benchmark.save()
        
        for experiment in self.experiments.values():
            experiment.save()
        
        for paper in self.papers.values():
            paper.save()
        
        self.logger.info(f"Saved {len(self.benchmarks)} benchmarks, {len(self.experiments)} experiments, and {len(self.papers)} papers")
    
    def list_benchmarks(self) -> List[Dict[str, Any]]:
        """
        List all benchmarks.
        
        Returns:
            List of benchmark info dictionaries
        """
        return [
            {
                'name': benchmark.name,
                'type': benchmark.benchmark_type.value,
                'description': benchmark.description,
                'version': benchmark.version,
                'sample_count': len(benchmark.samples)
            }
            for benchmark in self.benchmarks.values()
        ]
    
    def list_experiments(self) -> List[Dict[str, Any]]:
        """
        List all experiments.
        
        Returns:
            List of experiment info dictionaries
        """
        return [
            {
                'name': experiment.name,
                'type': experiment.experiment_type.value,
                'description': experiment.description,
                'version': experiment.version,
                'run_count': len(experiment.runs)
            }
            for experiment in self.experiments.values()
        ]
    
    def list_papers(self) -> List[Dict[str, Any]]:
        """
        List all papers.
        
        Returns:
            List of paper info dictionaries
        """
        return [
            {
                'title': paper.title,
                'authors': paper.authors,
                'sections': list(paper.sections.keys()),
                'figures': len(paper.figures),
                'tables': len(paper.tables),
                'references': len(paper.bibliography)
            }
            for paper in self.papers.values()
        ]