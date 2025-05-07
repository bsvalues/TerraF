"""
Analytics Pipeline for System Telemetry

This module implements an analytics pipeline for collecting, processing,
and analyzing system telemetry data across the TerraFlow platform.
"""

import os
import json
import time
import uuid
import logging
import threading
import datetime
import statistics
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Set, Tuple, Union, TypeVar
from dataclasses import dataclass, field
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics that can be collected"""
    COUNTER = "counter"  # Accumulating value (e.g., request count)
    GAUGE = "gauge"  # Value that can go up and down (e.g., memory usage)
    HISTOGRAM = "histogram"  # Distribution of values (e.g., response times)
    SUMMARY = "summary"  # Statistical summary of values
    TIMER = "timer"  # Time duration for operations

class DataRetention(Enum):
    """Data retention policies for metrics"""
    REAL_TIME = "real_time"  # Real-time data only (few minutes)
    SHORT_TERM = "short_term"  # Short-term data (hours)
    MEDIUM_TERM = "medium_term"  # Medium-term data (days)
    LONG_TERM = "long_term"  # Long-term data (weeks)
    PERMANENT = "permanent"  # Permanent data (never deleted)

class Aggregation(Enum):
    """Aggregation methods for metrics"""
    SUM = "sum"  # Sum of values
    AVG = "avg"  # Average of values
    MIN = "min"  # Minimum value
    MAX = "max"  # Maximum value
    COUNT = "count"  # Count of values
    PERCENTILE = "percentile"  # Percentile of values

@dataclass
class MetricDefinition:
    """Definition of a metric"""
    name: str
    description: str
    metric_type: MetricType
    unit: str = ""
    tags: List[str] = field(default_factory=list)
    retention: DataRetention = DataRetention.MEDIUM_TERM
    aggregations: List[Aggregation] = field(default_factory=list)
    
    def __post_init__(self):
        # Ensure metric name is valid
        if not self.name:
            raise ValueError("Metric name cannot be empty")
        
        # Set default aggregations based on metric type
        if not self.aggregations:
            if self.metric_type == MetricType.COUNTER:
                self.aggregations = [Aggregation.SUM, Aggregation.COUNT]
            elif self.metric_type == MetricType.GAUGE:
                self.aggregations = [Aggregation.AVG, Aggregation.MIN, Aggregation.MAX]
            elif self.metric_type == MetricType.HISTOGRAM:
                self.aggregations = [Aggregation.AVG, Aggregation.MIN, Aggregation.MAX, Aggregation.PERCENTILE]
            elif self.metric_type == MetricType.SUMMARY:
                self.aggregations = [Aggregation.AVG, Aggregation.MIN, Aggregation.MAX, Aggregation.PERCENTILE]
            elif self.metric_type == MetricType.TIMER:
                self.aggregations = [Aggregation.AVG, Aggregation.MIN, Aggregation.MAX, Aggregation.PERCENTILE]

@dataclass
class MetricValue:
    """Value of a metric"""
    metric_name: str
    value: Union[int, float, List[Union[int, float]]]
    timestamp: float
    dimensions: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        # Ensure timestamp is a float
        self.timestamp = float(self.timestamp)

@dataclass
class AggregatedMetric:
    """Aggregated metric value"""
    metric_name: str
    aggregation: Aggregation
    value: Union[int, float, Dict[str, Union[int, float]]]
    start_time: float
    end_time: float
    dimensions: Dict[str, str] = field(default_factory=dict)
    sample_count: int = 0
    
    def __post_init__(self):
        # Ensure timestamps are floats
        self.start_time = float(self.start_time)
        self.end_time = float(self.end_time)

class MetricRegistry:
    """
    Registry for metric definitions
    
    This class manages metric definitions and provides
    methods for registering and retrieving metrics.
    """
    
    def __init__(self):
        """Initialize a new metric registry"""
        self.metrics = {}  # name -> MetricDefinition
        self.metric_tags = defaultdict(set)  # tag -> Set[metric_name]
    
    def register_metric(self, definition: MetricDefinition) -> bool:
        """
        Register a new metric definition
        
        Args:
            definition: The metric definition to register
            
        Returns:
            bool: True if the metric was registered, False if it already exists
        """
        if definition.name in self.metrics:
            logger.warning(f"Metric {definition.name} already registered")
            return False
        
        self.metrics[definition.name] = definition
        
        # Update tag index
        for tag in definition.tags:
            self.metric_tags[tag].add(definition.name)
        
        logger.info(f"Registered metric {definition.name}")
        return True
    
    def get_metric(self, name: str) -> Optional[MetricDefinition]:
        """
        Get a metric definition by name
        
        Args:
            name: Name of the metric
            
        Returns:
            Optional[MetricDefinition]: The metric definition, or None if not found
        """
        return self.metrics.get(name)
    
    def get_metrics_by_tag(self, tag: str) -> List[MetricDefinition]:
        """
        Get all metric definitions with a specific tag
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List[MetricDefinition]: List of metric definitions with the tag
        """
        metric_names = self.metric_tags.get(tag, set())
        return [self.metrics[name] for name in metric_names if name in self.metrics]
    
    def get_all_metrics(self) -> List[MetricDefinition]:
        """
        Get all registered metric definitions
        
        Returns:
            List[MetricDefinition]: List of all metric definitions
        """
        return list(self.metrics.values())
    
    def get_metric_names(self) -> List[str]:
        """
        Get all registered metric names
        
        Returns:
            List[str]: List of all metric names
        """
        return list(self.metrics.keys())

class InMemoryMetricStore:
    """
    In-memory storage for metric values
    
    This class provides in-memory storage for recent metric values,
    with support for aggregation and expiration.
    """
    
    def __init__(self, max_age_seconds: Dict[DataRetention, int] = None, max_points: Dict[DataRetention, int] = None):
        """
        Initialize a new in-memory metric store
        
        Args:
            max_age_seconds: Maximum age in seconds for each retention policy
            max_points: Maximum number of data points for each retention policy
        """
        # Initialize default max age (how long to keep data)
        self.max_age_seconds = max_age_seconds or {
            DataRetention.REAL_TIME: 5 * 60,  # 5 minutes
            DataRetention.SHORT_TERM: 4 * 60 * 60,  # 4 hours
            DataRetention.MEDIUM_TERM: 2 * 24 * 60 * 60,  # 2 days
            DataRetention.LONG_TERM: 14 * 24 * 60 * 60,  # 14 days
            DataRetention.PERMANENT: 365 * 24 * 60 * 60  # 1 year (effectively permanent)
        }
        
        # Initialize default max points (how many data points to keep)
        self.max_points = max_points or {
            DataRetention.REAL_TIME: 300,  # 1 point per second for 5 minutes
            DataRetention.SHORT_TERM: 240,  # 1 point per minute for 4 hours
            DataRetention.MEDIUM_TERM: 576,  # 1 point per 5 minutes for 2 days
            DataRetention.LONG_TERM: 336,  # 1 point per hour for 14 days
            DataRetention.PERMANENT: 365  # 1 point per day for 1 year
        }
        
        # Storage for raw metric values
        self.raw_metrics = defaultdict(lambda: defaultdict(deque))  # name -> dimensions_key -> deque[MetricValue]
        
        # Storage for aggregated metrics
        self.aggregated_metrics = {}  # (name, aggregation, retention, dimensions_key) -> List[AggregatedMetric]
        
        # Storage for the latest values
        self.latest_values = {}  # (name, dimensions_key) -> MetricValue
        
        # Start cleanup thread
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()
    
    def stop(self):
        """Stop the cleanup thread"""
        self.running = False
        if self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=1.0)
    
    def store_metric(self, metric: MetricValue):
        """
        Store a new metric value
        
        Args:
            metric: The metric value to store
        """
        # Get the dimensions key (for grouping by dimensions)
        dimensions_key = self._get_dimensions_key(metric.dimensions)
        
        # Store in raw metrics
        raw_metrics_key = (metric.metric_name, dimensions_key)
        self.raw_metrics[metric.metric_name][dimensions_key].append(metric)
        
        # Update latest value
        self.latest_values[(metric.metric_name, dimensions_key)] = metric
    
    def get_latest_value(self, metric_name: str, dimensions: Optional[Dict[str, str]] = None) -> Optional[MetricValue]:
        """
        Get the latest value for a metric
        
        Args:
            metric_name: Name of the metric
            dimensions: Optional dimensions to filter by
            
        Returns:
            Optional[MetricValue]: The latest metric value, or None if not found
        """
        dimensions_key = self._get_dimensions_key(dimensions or {})
        return self.latest_values.get((metric_name, dimensions_key))
    
    def get_raw_values(self, metric_name: str, dimensions: Optional[Dict[str, str]] = None,
                     start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[MetricValue]:
        """
        Get raw values for a metric
        
        Args:
            metric_name: Name of the metric
            dimensions: Optional dimensions to filter by
            start_time: Optional start time (timestamp)
            end_time: Optional end time (timestamp)
            
        Returns:
            List[MetricValue]: List of metric values
        """
        # Set default times
        if end_time is None:
            end_time = time.time()
            
        if start_time is None:
            start_time = end_time - 3600  # 1 hour
        
        # Get dimensions key
        dimensions_key = self._get_dimensions_key(dimensions or {})
        
        # Get raw values
        raw_values = list(self.raw_metrics.get(metric_name, {}).get(dimensions_key, []))
        
        # Filter by time range
        return [m for m in raw_values if start_time <= m.timestamp <= end_time]
    
    def get_aggregated_values(self, metric_name: str, aggregation: Aggregation,
                            dimensions: Optional[Dict[str, str]] = None,
                            retention: DataRetention = DataRetention.MEDIUM_TERM,
                            start_time: Optional[float] = None,
                            end_time: Optional[float] = None) -> List[AggregatedMetric]:
        """
        Get aggregated values for a metric
        
        Args:
            metric_name: Name of the metric
            aggregation: Aggregation method
            dimensions: Optional dimensions to filter by
            retention: Data retention policy
            start_time: Optional start time (timestamp)
            end_time: Optional end time (timestamp)
            
        Returns:
            List[AggregatedMetric]: List of aggregated metric values
        """
        # Set default times
        if end_time is None:
            end_time = time.time()
            
        if start_time is None:
            start_time = end_time - 3600  # 1 hour
        
        # Get dimensions key
        dimensions_key = self._get_dimensions_key(dimensions or {})
        
        # Get aggregated values
        aggregated_key = (metric_name, aggregation, retention, dimensions_key)
        aggregated_values = self.aggregated_metrics.get(aggregated_key, [])
        
        # Filter by time range
        return [m for m in aggregated_values if m.start_time >= start_time and m.end_time <= end_time]
    
    def aggregate_metrics(self, metric_registry: MetricRegistry):
        """
        Aggregate metrics based on their definitions
        
        Args:
            metric_registry: Registry of metric definitions
        """
        now = time.time()
        
        # Define time window sizes for each retention policy
        window_sizes = {
            DataRetention.REAL_TIME: 60,  # 1 minute windows
            DataRetention.SHORT_TERM: 15 * 60,  # 15 minute windows
            DataRetention.MEDIUM_TERM: 60 * 60,  # 1 hour windows
            DataRetention.LONG_TERM: 24 * 60 * 60,  # 1 day windows
            DataRetention.PERMANENT: 7 * 24 * 60 * 60  # 1 week windows
        }
        
        # Determine current window end times
        window_ends = {}
        for retention, window_size in window_sizes.items():
            # Round down to the nearest window
            window_ends[retention] = now - (now % window_size)
        
        # Process each metric
        for metric_name, dimensions_dict in self.raw_metrics.items():
            # Get metric definition
            definition = metric_registry.get_metric(metric_name)
            if definition is None:
                continue
            
            # Get retention policy
            retention = definition.retention
            
            # Get aggregation methods
            aggregations = definition.aggregations
            
            # Get window size
            window_size = window_sizes[retention]
            
            # Get window end time
            window_end = window_ends[retention]
            
            # Calculate window start time
            window_start = window_end - window_size
            
            # Process each dimension combination
            for dimensions_key, metrics in dimensions_dict.items():
                # Parse dimensions from key
                dimensions = self._parse_dimensions_key(dimensions_key)
                
                # Get metrics in the window
                window_metrics = [m for m in metrics if window_start <= m.timestamp < window_end]
                
                # Skip if no metrics in the window
                if not window_metrics:
                    continue
                
                # Get values
                values = [m.value for m in window_metrics]
                
                # Perform aggregations
                for aggregation in aggregations:
                    # Calculate aggregated value
                    aggregated_value = self._calculate_aggregation(values, aggregation, definition.metric_type)
                    
                    # Create aggregated metric
                    aggregated_metric = AggregatedMetric(
                        metric_name=metric_name,
                        aggregation=aggregation,
                        value=aggregated_value,
                        start_time=window_start,
                        end_time=window_end,
                        dimensions=dimensions,
                        sample_count=len(window_metrics)
                    )
                    
                    # Store aggregated metric
                    aggregated_key = (metric_name, aggregation, retention, dimensions_key)
                    
                    if aggregated_key not in self.aggregated_metrics:
                        self.aggregated_metrics[aggregated_key] = []
                    
                    # Check if we already have an aggregation for this window
                    existing = False
                    for i, existing_metric in enumerate(self.aggregated_metrics[aggregated_key]):
                        if existing_metric.start_time == window_start and existing_metric.end_time == window_end:
                            # Replace existing aggregation
                            self.aggregated_metrics[aggregated_key][i] = aggregated_metric
                            existing = True
                            break
                    
                    if not existing:
                        # Add new aggregation
                        self.aggregated_metrics[aggregated_key].append(aggregated_metric)
    
    def _calculate_aggregation(self, values: List[Union[int, float]], aggregation: Aggregation,
                             metric_type: MetricType) -> Union[int, float, Dict[str, Union[int, float]]]:
        """
        Calculate an aggregation for a set of values
        
        Args:
            values: List of values to aggregate
            aggregation: Aggregation method
            metric_type: Type of metric
            
        Returns:
            Union[int, float, Dict[str, Union[int, float]]]: Aggregated value
        """
        if not values:
            return 0
        
        # Handle histogram/summary values
        if metric_type in [MetricType.HISTOGRAM, MetricType.SUMMARY] and isinstance(values[0], list):
            # Flatten list of lists
            flat_values = [v for sublist in values for v in sublist]
            values = flat_values
        
        # Calculate aggregation
        if aggregation == Aggregation.SUM:
            return sum(values)
        elif aggregation == Aggregation.AVG:
            return sum(values) / len(values)
        elif aggregation == Aggregation.MIN:
            return min(values)
        elif aggregation == Aggregation.MAX:
            return max(values)
        elif aggregation == Aggregation.COUNT:
            return len(values)
        elif aggregation == Aggregation.PERCENTILE:
            # Calculate multiple percentiles
            values.sort()
            percentiles = [50, 90, 95, 99]
            result = {}
            
            for p in percentiles:
                idx = int(len(values) * p / 100)
                if idx >= len(values):
                    idx = len(values) - 1
                result[f"p{p}"] = values[idx]
            
            return result
        
        # Default
        return sum(values)
    
    def _cleanup_loop(self):
        """Background thread for cleaning up old metric data"""
        cleanup_interval = 60  # 1 minute
        
        while self.running:
            try:
                # Clean up expired data
                self._cleanup_expired_data()
                
                # Limit data points
                self._limit_data_points()
                
            except Exception as e:
                logger.error(f"Error in metric store cleanup loop: {str(e)}")
            
            # Sleep for cleanup interval
            for _ in range(cleanup_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def _cleanup_expired_data(self):
        """Clean up expired metric data"""
        now = time.time()
        
        # Clean up raw metrics
        for metric_name, dimensions_dict in list(self.raw_metrics.items()):
            # Get metric definition and retention
            for dimensions_key, metrics in list(dimensions_dict.items()):
                # Remove expired metrics
                expired_count = 0
                while metrics and now - metrics[0].timestamp > self.max_age_seconds[DataRetention.REAL_TIME]:
                    metrics.popleft()
                    expired_count += 1
                
                # Remove empty dimension entries
                if not metrics:
                    del self.raw_metrics[metric_name][dimensions_key]
            
            # Remove empty metric entries
            if not self.raw_metrics[metric_name]:
                del self.raw_metrics[metric_name]
        
        # Clean up aggregated metrics
        for key, metrics in list(self.aggregated_metrics.items()):
            metric_name, aggregation, retention, dimensions_key = key
            
            # Remove expired metrics
            max_age = self.max_age_seconds[retention]
            metrics[:] = [m for m in metrics if now - m.end_time <= max_age]
            
            # Remove empty entries
            if not metrics:
                del self.aggregated_metrics[key]
        
        # Clean up latest values
        for key, metric in list(self.latest_values.items()):
            if now - metric.timestamp > self.max_age_seconds[DataRetention.REAL_TIME]:
                del self.latest_values[key]
    
    def _limit_data_points(self):
        """Limit the number of data points for each metric"""
        # Limit raw metrics
        for metric_name, dimensions_dict in self.raw_metrics.items():
            for dimensions_key, metrics in dimensions_dict.items():
                while len(metrics) > self.max_points[DataRetention.REAL_TIME]:
                    metrics.popleft()
        
        # Limit aggregated metrics
        for key, metrics in self.aggregated_metrics.items():
            metric_name, aggregation, retention, dimensions_key = key
            
            # Limit data points for this retention
            max_points = self.max_points[retention]
            if len(metrics) > max_points:
                # Sort by end time (newest first)
                metrics.sort(key=lambda m: m.end_time, reverse=True)
                
                # Keep only the newest
                metrics[:] = metrics[:max_points]
    
    def _get_dimensions_key(self, dimensions: Dict[str, str]) -> str:
        """Get a key for dimensions dictionary"""
        # Sort dimensions for consistent keys
        items = sorted(dimensions.items())
        return ":".join(f"{k}={v}" for k, v in items)
    
    def _parse_dimensions_key(self, dimensions_key: str) -> Dict[str, str]:
        """Parse dimensions from a key"""
        if not dimensions_key:
            return {}
        
        dimensions = {}
        for part in dimensions_key.split(":"):
            if "=" in part:
                k, v = part.split("=", 1)
                dimensions[k] = v
        
        return dimensions

class MetricsCollector:
    """
    Metrics collector for the TerraFlow platform
    
    This class provides methods for collecting metrics from
    various sources in the platform.
    """
    
    def __init__(self, metric_registry: MetricRegistry, metric_store: InMemoryMetricStore):
        """
        Initialize a new metrics collector
        
        Args:
            metric_registry: Registry of metric definitions
            metric_store: Store for metric values
        """
        self.metric_registry = metric_registry
        self.metric_store = metric_store
        self.counters = defaultdict(lambda: defaultdict(int))  # (name, dimensions_key) -> value
        self.gauges = {}  # (name, dimensions_key) -> value
        
        # Create standard metrics if they don't exist
        self._create_standard_metrics()
    
    def _create_standard_metrics(self):
        """Create standard metrics for the platform"""
        # System metrics
        self.metric_registry.register_metric(MetricDefinition(
            name="system.memory.used",
            description="Amount of memory used by the system",
            metric_type=MetricType.GAUGE,
            unit="bytes",
            tags=["system", "memory"],
            retention=DataRetention.MEDIUM_TERM
        ))
        
        self.metric_registry.register_metric(MetricDefinition(
            name="system.cpu.usage",
            description="CPU usage percentage",
            metric_type=MetricType.GAUGE,
            unit="percent",
            tags=["system", "cpu"],
            retention=DataRetention.MEDIUM_TERM
        ))
        
        self.metric_registry.register_metric(MetricDefinition(
            name="system.disk.used",
            description="Amount of disk space used",
            metric_type=MetricType.GAUGE,
            unit="bytes",
            tags=["system", "disk"],
            retention=DataRetention.MEDIUM_TERM
        ))
        
        # Application metrics
        self.metric_registry.register_metric(MetricDefinition(
            name="application.requests.count",
            description="Number of requests received",
            metric_type=MetricType.COUNTER,
            unit="requests",
            tags=["application", "requests"],
            retention=DataRetention.MEDIUM_TERM
        ))
        
        self.metric_registry.register_metric(MetricDefinition(
            name="application.requests.latency",
            description="Request latency",
            metric_type=MetricType.HISTOGRAM,
            unit="milliseconds",
            tags=["application", "requests", "latency"],
            retention=DataRetention.MEDIUM_TERM
        ))
        
        self.metric_registry.register_metric(MetricDefinition(
            name="application.errors.count",
            description="Number of errors",
            metric_type=MetricType.COUNTER,
            unit="errors",
            tags=["application", "errors"],
            retention=DataRetention.MEDIUM_TERM
        ))
        
        # Cache metrics
        self.metric_registry.register_metric(MetricDefinition(
            name="cache.hits",
            description="Number of cache hits",
            metric_type=MetricType.COUNTER,
            unit="hits",
            tags=["cache"],
            retention=DataRetention.MEDIUM_TERM
        ))
        
        self.metric_registry.register_metric(MetricDefinition(
            name="cache.misses",
            description="Number of cache misses",
            metric_type=MetricType.COUNTER,
            unit="misses",
            tags=["cache"],
            retention=DataRetention.MEDIUM_TERM
        ))
        
        # Database metrics
        self.metric_registry.register_metric(MetricDefinition(
            name="database.queries.count",
            description="Number of database queries",
            metric_type=MetricType.COUNTER,
            unit="queries",
            tags=["database", "queries"],
            retention=DataRetention.MEDIUM_TERM
        ))
        
        self.metric_registry.register_metric(MetricDefinition(
            name="database.queries.latency",
            description="Database query latency",
            metric_type=MetricType.HISTOGRAM,
            unit="milliseconds",
            tags=["database", "queries", "latency"],
            retention=DataRetention.MEDIUM_TERM
        ))
        
        # Agent metrics
        self.metric_registry.register_metric(MetricDefinition(
            name="agent.tasks.count",
            description="Number of tasks processed by agents",
            metric_type=MetricType.COUNTER,
            unit="tasks",
            tags=["agent", "tasks"],
            retention=DataRetention.MEDIUM_TERM
        ))
        
        self.metric_registry.register_metric(MetricDefinition(
            name="agent.tasks.duration",
            description="Duration of agent tasks",
            metric_type=MetricType.HISTOGRAM,
            unit="milliseconds",
            tags=["agent", "tasks", "duration"],
            retention=DataRetention.MEDIUM_TERM
        ))
    
    def increment_counter(self, name: str, value: int = 1, dimensions: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric
        
        Args:
            name: Name of the metric
            value: Value to increment by
            dimensions: Optional dimensions for the metric
        """
        # Check if metric exists
        metric_def = self.metric_registry.get_metric(name)
        if metric_def is None:
            logger.warning(f"Metric {name} not registered")
            return
        
        # Check metric type
        if metric_def.metric_type != MetricType.COUNTER:
            logger.warning(f"Metric {name} is not a counter")
            return
        
        # Get dimensions key
        dimensions_key = self._get_dimensions_key(dimensions or {})
        
        # Increment counter
        self.counters[(name, dimensions_key)] += value
        
        # Create metric value
        metric = MetricValue(
            metric_name=name,
            value=self.counters[(name, dimensions_key)],
            timestamp=time.time(),
            dimensions=dimensions or {}
        )
        
        # Store metric
        self.metric_store.store_metric(metric)
    
    def set_gauge(self, name: str, value: Union[int, float], dimensions: Optional[Dict[str, str]] = None):
        """
        Set a gauge metric
        
        Args:
            name: Name of the metric
            value: Value to set
            dimensions: Optional dimensions for the metric
        """
        # Check if metric exists
        metric_def = self.metric_registry.get_metric(name)
        if metric_def is None:
            logger.warning(f"Metric {name} not registered")
            return
        
        # Check metric type
        if metric_def.metric_type != MetricType.GAUGE:
            logger.warning(f"Metric {name} is not a gauge")
            return
        
        # Get dimensions key
        dimensions_key = self._get_dimensions_key(dimensions or {})
        
        # Set gauge
        self.gauges[(name, dimensions_key)] = value
        
        # Create metric value
        metric = MetricValue(
            metric_name=name,
            value=value,
            timestamp=time.time(),
            dimensions=dimensions or {}
        )
        
        # Store metric
        self.metric_store.store_metric(metric)
    
    def record_histogram(self, name: str, value: Union[int, float], dimensions: Optional[Dict[str, str]] = None):
        """
        Record a value for a histogram metric
        
        Args:
            name: Name of the metric
            value: Value to record
            dimensions: Optional dimensions for the metric
        """
        # Check if metric exists
        metric_def = self.metric_registry.get_metric(name)
        if metric_def is None:
            logger.warning(f"Metric {name} not registered")
            return
        
        # Check metric type
        if metric_def.metric_type != MetricType.HISTOGRAM:
            logger.warning(f"Metric {name} is not a histogram")
            return
        
        # Create metric value
        metric = MetricValue(
            metric_name=name,
            value=value,
            timestamp=time.time(),
            dimensions=dimensions or {}
        )
        
        # Store metric
        self.metric_store.store_metric(metric)
    
    def record_timer(self, name: str, duration_ms: Union[int, float], dimensions: Optional[Dict[str, str]] = None):
        """
        Record a timer duration
        
        Args:
            name: Name of the metric
            duration_ms: Duration in milliseconds
            dimensions: Optional dimensions for the metric
        """
        # Check if metric exists
        metric_def = self.metric_registry.get_metric(name)
        if metric_def is None:
            logger.warning(f"Metric {name} not registered")
            return
        
        # Check metric type
        if metric_def.metric_type != MetricType.TIMER:
            logger.warning(f"Metric {name} is not a timer")
            return
        
        # Create metric value
        metric = MetricValue(
            metric_name=name,
            value=duration_ms,
            timestamp=time.time(),
            dimensions=dimensions or {}
        )
        
        # Store metric
        self.metric_store.store_metric(metric)
    
    def time_execution(self, name: str, dimensions: Optional[Dict[str, str]] = None):
        """
        Context manager for timing execution
        
        Args:
            name: Name of the metric
            dimensions: Optional dimensions for the metric
            
        Returns:
            A context manager that times execution
        """
        return TimerContext(self, name, dimensions)
    
    def _get_dimensions_key(self, dimensions: Dict[str, str]) -> str:
        """Get a key for dimensions dictionary"""
        # Sort dimensions for consistent keys
        items = sorted(dimensions.items())
        return ":".join(f"{k}={v}" for k, v in items)

class TimerContext:
    """Context manager for timing execution"""
    
    def __init__(self, collector: MetricsCollector, name: str, dimensions: Optional[Dict[str, str]] = None):
        """
        Initialize a new timer context
        
        Args:
            collector: Metrics collector
            name: Name of the metric
            dimensions: Optional dimensions for the metric
        """
        self.collector = collector
        self.name = name
        self.dimensions = dimensions or {}
        self.start_time = None
    
    def __enter__(self):
        """Start the timer"""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the timer and record the duration"""
        if self.start_time is not None:
            duration_ms = (time.time() - self.start_time) * 1000
            self.collector.record_timer(self.name, duration_ms, self.dimensions)

class AnalyticsPipeline:
    """
    Analytics pipeline for the TerraFlow platform
    
    This class provides a pipeline for collecting, processing,
    and analyzing telemetry data across the platform.
    """
    
    def __init__(self, data_dir: str = "data/metrics"):
        """
        Initialize a new analytics pipeline
        
        Args:
            data_dir: Directory for storing metrics data
        """
        # Create data directory
        os.makedirs(data_dir, exist_ok=True)
        
        # Create components
        self.metric_registry = MetricRegistry()
        self.metric_store = InMemoryMetricStore()
        self.metrics_collector = MetricsCollector(self.metric_registry, self.metric_store)
        
        # Aggregation interval in seconds
        self.aggregation_interval = 60  # 1 minute
        
        # Start aggregation thread
        self.running = True
        self.aggregation_thread = threading.Thread(target=self._aggregation_loop)
        self.aggregation_thread.daemon = True
        self.aggregation_thread.start()
    
    def stop(self):
        """Stop the analytics pipeline"""
        self.running = False
        self.metric_store.stop()
        if self.aggregation_thread.is_alive():
            self.aggregation_thread.join(timeout=1.0)
    
    def register_metric(self, definition: MetricDefinition) -> bool:
        """
        Register a new metric definition
        
        Args:
            definition: The metric definition to register
            
        Returns:
            bool: True if the metric was registered, False if it already exists
        """
        return self.metric_registry.register_metric(definition)
    
    def increment_counter(self, name: str, value: int = 1, dimensions: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric
        
        Args:
            name: Name of the metric
            value: Value to increment by
            dimensions: Optional dimensions for the metric
        """
        self.metrics_collector.increment_counter(name, value, dimensions)
    
    def set_gauge(self, name: str, value: Union[int, float], dimensions: Optional[Dict[str, str]] = None):
        """
        Set a gauge metric
        
        Args:
            name: Name of the metric
            value: Value to set
            dimensions: Optional dimensions for the metric
        """
        self.metrics_collector.set_gauge(name, value, dimensions)
    
    def record_histogram(self, name: str, value: Union[int, float], dimensions: Optional[Dict[str, str]] = None):
        """
        Record a value for a histogram metric
        
        Args:
            name: Name of the metric
            value: Value to record
            dimensions: Optional dimensions for the metric
        """
        self.metrics_collector.record_histogram(name, value, dimensions)
    
    def record_timer(self, name: str, duration_ms: Union[int, float], dimensions: Optional[Dict[str, str]] = None):
        """
        Record a timer duration
        
        Args:
            name: Name of the metric
            duration_ms: Duration in milliseconds
            dimensions: Optional dimensions for the metric
        """
        self.metrics_collector.record_timer(name, duration_ms, dimensions)
    
    def time_execution(self, name: str, dimensions: Optional[Dict[str, str]] = None):
        """
        Context manager for timing execution
        
        Args:
            name: Name of the metric
            dimensions: Optional dimensions for the metric
            
        Returns:
            A context manager that times execution
        """
        return self.metrics_collector.time_execution(name, dimensions)
    
    def get_metric_value(self, name: str, dimensions: Optional[Dict[str, str]] = None) -> Optional[Union[int, float]]:
        """
        Get the latest value for a metric
        
        Args:
            name: Name of the metric
            dimensions: Optional dimensions to filter by
            
        Returns:
            Optional[Union[int, float]]: The latest metric value, or None if not found
        """
        metric_value = self.metric_store.get_latest_value(name, dimensions)
        if metric_value:
            return metric_value.value
        return None
    
    def get_metric_values(self, name: str, dimensions: Optional[Dict[str, str]] = None,
                        start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[MetricValue]:
        """
        Get raw values for a metric
        
        Args:
            name: Name of the metric
            dimensions: Optional dimensions to filter by
            start_time: Optional start time (timestamp)
            end_time: Optional end time (timestamp)
            
        Returns:
            List[MetricValue]: List of metric values
        """
        return self.metric_store.get_raw_values(name, dimensions, start_time, end_time)
    
    def get_aggregated_values(self, name: str, aggregation: Aggregation,
                            dimensions: Optional[Dict[str, str]] = None,
                            retention: DataRetention = DataRetention.MEDIUM_TERM,
                            start_time: Optional[float] = None,
                            end_time: Optional[float] = None) -> List[AggregatedMetric]:
        """
        Get aggregated values for a metric
        
        Args:
            name: Name of the metric
            aggregation: Aggregation method
            dimensions: Optional dimensions to filter by
            retention: Data retention policy
            start_time: Optional start time (timestamp)
            end_time: Optional end time (timestamp)
            
        Returns:
            List[AggregatedMetric]: List of aggregated metric values
        """
        return self.metric_store.get_aggregated_values(name, aggregation, dimensions, retention, start_time, end_time)
    
    def _aggregation_loop(self):
        """Background thread for aggregating metrics"""
        while self.running:
            try:
                # Aggregate metrics
                self.metric_store.aggregate_metrics(self.metric_registry)
                
            except Exception as e:
                logger.error(f"Error in aggregation loop: {str(e)}")
            
            # Sleep for aggregation interval
            for _ in range(self.aggregation_interval):
                if not self.running:
                    break
                time.sleep(1)