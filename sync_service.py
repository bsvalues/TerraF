import os
import logging
import time
import threading
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Callable
import pandas as pd
import numpy as np
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sync_service')

class BatchConfiguration:
    """Configuration for synchronization batch processing."""
    
    def __init__(
        self,
        initial_size: int = 50,
        min_size: int = 10,
        max_size: int = 500,
        increment_factor: float = 1.2,
        decrement_factor: float = 0.8,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 80.0,
        target_latency: float = 0.5
    ):
        """
        Initialize batch configuration parameters.
        
        Args:
            initial_size: Initial batch size
            min_size: Minimum allowed batch size
            max_size: Maximum allowed batch size
            increment_factor: Factor to increase batch size by
            decrement_factor: Factor to decrease batch size by
            cpu_threshold: CPU usage threshold (percentage)
            memory_threshold: Memory usage threshold (percentage)
            target_latency: Target latency for batch processing (seconds)
        """
        self.initial_size = initial_size
        self.min_size = min_size
        self.max_size = max_size
        self.increment_factor = increment_factor
        self.decrement_factor = decrement_factor
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.target_latency = target_latency

class SyncMetrics:
    """Class for tracking synchronization metrics."""
    
    def __init__(self):
        """Initialize sync metrics."""
        self.reset()
    
    def reset(self):
        """Reset all metrics."""
        self.start_time = time.time()
        self.end_time = None
        self.total_items = 0
        self.successful_items = 0
        self.failed_items = 0
        self.skipped_items = 0
        self.batch_counts = []
        self.batch_times = []
        self.errors = []
        self.current_batch_size = 0
        self.cpu_usage = []
        self.memory_usage = []
        self.network_usage = []
        self.disk_usage = []
    
    def record_batch(self, size: int, duration: float):
        """
        Record batch processing metrics.
        
        Args:
            size: Batch size
            duration: Processing duration in seconds
        """
        self.batch_counts.append(size)
        self.batch_times.append(duration)
        self.current_batch_size = size
    
    def record_result(self, success_count: int, fail_count: int, skip_count: int):
        """
        Record processing results.
        
        Args:
            success_count: Number of successful items
            fail_count: Number of failed items
            skip_count: Number of skipped items
        """
        self.total_items += success_count + fail_count + skip_count
        self.successful_items += success_count
        self.failed_items += fail_count
        self.skipped_items += skip_count
    
    def record_error(self, error: str):
        """
        Record an error.
        
        Args:
            error: Error message
        """
        self.errors.append(error)
    
    def record_system_metrics(self, cpu: float, memory: float, network: float, disk: float):
        """
        Record system resource metrics.
        
        Args:
            cpu: CPU usage percentage
            memory: Memory usage percentage
            network: Network usage (MB/s)
            disk: Disk usage percentage
        """
        self.cpu_usage.append(cpu)
        self.memory_usage.append(memory)
        self.network_usage.append(network)
        self.disk_usage.append(disk)
    
    def complete(self):
        """Mark metrics collection as complete."""
        self.end_time = time.time()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all collected metrics.
        
        Returns:
            Dictionary of metrics
        """
        duration = (self.end_time or time.time()) - self.start_time
        
        avg_batch_time = sum(self.batch_times) / len(self.batch_times) if self.batch_times else 0
        avg_batch_size = sum(self.batch_counts) / len(self.batch_counts) if self.batch_counts else 0
        
        throughput = self.successful_items / duration if duration > 0 else 0
        error_rate = self.failed_items / self.total_items if self.total_items > 0 else 0
        
        avg_cpu = sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
        avg_memory = sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0
        
        return {
            "duration_seconds": duration,
            "total_items": self.total_items,
            "successful_items": self.successful_items,
            "failed_items": self.failed_items,
            "skipped_items": self.skipped_items,
            "throughput_items_per_second": throughput,
            "error_rate": error_rate,
            "avg_batch_size": avg_batch_size,
            "avg_batch_time_seconds": avg_batch_time,
            "current_batch_size": self.current_batch_size,
            "avg_cpu_usage": avg_cpu,
            "avg_memory_usage": avg_memory,
            "error_count": len(self.errors),
            "recent_errors": self.errors[-5:] if self.errors else []
        }
    
    def get_time_series_data(self) -> Dict[str, List[Any]]:
        """
        Get time series data for metrics visualization.
        
        Returns:
            Dictionary of time series data
        """
        timestamps = [self.start_time + i * 5 for i in range(len(self.cpu_usage))]
        
        return {
            "timestamps": timestamps,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "network_usage": self.network_usage,
            "disk_usage": self.disk_usage,
            "batch_sizes": self.batch_counts,
            "batch_times": self.batch_times
        }

class PerformanceOptimizer:
    """Optimizer for sync performance based on system metrics."""
    
    def __init__(self, batch_config: BatchConfiguration):
        """
        Initialize performance optimizer.
        
        Args:
            batch_config: Batch configuration parameters
        """
        self.batch_config = batch_config
        self.current_batch_size = batch_config.initial_size
    
    def adjust_batch_size(self, resource_metrics: Dict[str, Any], latency: float) -> int:
        """
        Adjust batch size based on system metrics.
        
        Args:
            resource_metrics: Dictionary of resource metrics
            latency: Current batch processing latency
        
        Returns:
            New batch size
        """
        cpu_usage = resource_metrics.get("cpu", 0)
        memory_usage = resource_metrics.get("memory", 0)
        
        # Decrease batch size if resources are constrained
        if cpu_usage > self.batch_config.cpu_threshold or memory_usage > self.batch_config.memory_threshold:
            new_size = max(
                int(self.current_batch_size * self.batch_config.decrement_factor),
                self.batch_config.min_size
            )
            logger.info(f"Decreasing batch size to {new_size} due to resource constraints")
            self.current_batch_size = new_size
            return new_size
        
        # Adjust based on latency
        if latency > self.batch_config.target_latency * 1.5:
            # Processing is too slow, decrease batch size
            new_size = max(
                int(self.current_batch_size * self.batch_config.decrement_factor),
                self.batch_config.min_size
            )
            logger.info(f"Decreasing batch size to {new_size} due to high latency")
            self.current_batch_size = new_size
            return new_size
        elif latency < self.batch_config.target_latency * 0.5 and cpu_usage < self.batch_config.cpu_threshold * 0.7:
            # Processing is fast and resources are available, increase batch size
            new_size = min(
                int(self.current_batch_size * self.batch_config.increment_factor),
                self.batch_config.max_size
            )
            logger.info(f"Increasing batch size to {new_size} due to low latency and available resources")
            self.current_batch_size = new_size
            return new_size
        
        # Keep current batch size
        return self.current_batch_size
    
    def get_current_batch_size(self) -> int:
        """
        Get current batch size.
        
        Returns:
            Current batch size
        """
        return self.current_batch_size
    
    def reset(self):
        """Reset to initial batch size."""
        self.current_batch_size = self.batch_config.initial_size

class SyncService:
    """
    Service for managing synchronization operations between systems.
    
    This service handles batched synchronization operations with adaptive
    batch sizing based on system performance and resource usage.
    """
    
    def __init__(
        self,
        batch_config: Optional[BatchConfiguration] = None,
        resource_monitor: Optional[Callable[[], Dict[str, Any]]] = None
    ):
        """
        Initialize the sync service.
        
        Args:
            batch_config: Batch configuration parameters
            resource_monitor: Function to monitor system resources
        """
        self.batch_config = batch_config or BatchConfiguration()
        self.resource_monitor = resource_monitor or self._default_resource_monitor
        self.optimizer = PerformanceOptimizer(self.batch_config)
        self.metrics = SyncMetrics()
        
        self._running = False
        self._paused = False
        self._worker_thread = None
        self._queue = queue.Queue()
        self._lock = threading.Lock()
        self._metrics_thread = None
    
    def _default_resource_monitor(self) -> Dict[str, Any]:
        """
        Default resource monitoring implementation.
        
        Returns:
            Dictionary of resource metrics
        """
        # Simulate resource metrics with random values
        # In a real implementation, this would use platform-specific APIs
        return {
            "cpu": 30 + 20 * np.random.random(),  # 30-50% CPU usage
            "memory": 40 + 20 * np.random.random(),  # 40-60% memory usage
            "network": 5 + 5 * np.random.random(),  # 5-10 MB/s network usage
            "disk": 30 + 10 * np.random.random(),  # 30-40% disk usage
        }
    
    def start(self):
        """Start the sync service."""
        with self._lock:
            if self._running:
                logger.warning("Sync service is already running")
                return
            
            self._running = True
            self._paused = False
            self.metrics.reset()
            
            # Start worker thread
            self._worker_thread = threading.Thread(target=self._worker_loop)
            self._worker_thread.daemon = True
            self._worker_thread.start()
            
            # Start metrics collection thread
            self._metrics_thread = threading.Thread(target=self._collect_metrics)
            self._metrics_thread.daemon = True
            self._metrics_thread.start()
            
            logger.info("Sync service started")
    
    def stop(self):
        """Stop the sync service."""
        with self._lock:
            if not self._running:
                logger.warning("Sync service is not running")
                return
            
            self._running = False
            self._paused = False
            
            # Wait for worker thread to terminate
            if self._worker_thread and self._worker_thread.is_alive():
                self._worker_thread.join(timeout=5.0)
            
            # Wait for metrics thread to terminate
            if self._metrics_thread and self._metrics_thread.is_alive():
                self._metrics_thread.join(timeout=5.0)
            
            # Complete metrics collection
            self.metrics.complete()
            
            logger.info("Sync service stopped")
    
    def pause(self):
        """Pause the sync service."""
        with self._lock:
            if not self._running:
                logger.warning("Sync service is not running")
                return
            
            self._paused = True
            logger.info("Sync service paused")
    
    def resume(self):
        """Resume the sync service."""
        with self._lock:
            if not self._running:
                logger.warning("Sync service is not running")
                return
            
            self._paused = False
            logger.info("Sync service resumed")
    
    def is_running(self) -> bool:
        """
        Check if the sync service is running.
        
        Returns:
            True if running, False otherwise
        """
        with self._lock:
            return self._running
    
    def is_paused(self) -> bool:
        """
        Check if the sync service is paused.
        
        Returns:
            True if paused, False otherwise
        """
        with self._lock:
            return self._paused
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current sync metrics.
        
        Returns:
            Dictionary of metrics
        """
        return self.metrics.get_metrics()
    
    def get_time_series_data(self) -> Dict[str, List[Any]]:
        """
        Get time series data for metrics visualization.
        
        Returns:
            Dictionary of time series data
        """
        return self.metrics.get_time_series_data()
    
    def get_current_batch_size(self) -> int:
        """
        Get current batch size.
        
        Returns:
            Current batch size
        """
        return self.optimizer.get_current_batch_size()
    
    def set_batch_config(self, config: BatchConfiguration):
        """
        Set new batch configuration.
        
        Args:
            config: New batch configuration
        """
        with self._lock:
            self.batch_config = config
            self.optimizer = PerformanceOptimizer(config)
    
    def _worker_loop(self):
        """Main worker loop for processing sync operations."""
        while self._running:
            if self._paused:
                time.sleep(0.5)
                continue
            
            try:
                # Get current batch size
                batch_size = self.optimizer.get_current_batch_size()
                
                # Simulate batch processing
                batch_start_time = time.time()
                
                # Simulate processing success/failure
                success_count = int(batch_size * (0.9 + 0.1 * np.random.random()))
                fail_count = int(batch_size * 0.05 * np.random.random())
                skip_count = batch_size - success_count - fail_count
                
                # Simulate processing time (proportional to batch size but with some randomness)
                processing_time = 0.01 * batch_size * (0.8 + 0.4 * np.random.random())
                time.sleep(processing_time)
                
                batch_end_time = time.time()
                batch_duration = batch_end_time - batch_start_time
                
                # Record metrics
                self.metrics.record_batch(batch_size, batch_duration)
                self.metrics.record_result(success_count, fail_count, skip_count)
                
                # Simulate occasional errors
                if np.random.random() < 0.1:
                    error_message = f"Simulated error in batch processing: {np.random.choice(['network timeout', 'API error', 'data validation failure'])}"
                    self.metrics.record_error(error_message)
                
                # Get resource metrics
                resource_metrics = self.resource_monitor()
                
                # Update batch size based on performance
                self.optimizer.adjust_batch_size(resource_metrics, batch_duration)
                
                # Short sleep to prevent tight loop
                time.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Error in worker loop: {str(e)}")
                time.sleep(1.0)
    
    def _collect_metrics(self):
        """Thread for collecting system metrics."""
        while self._running:
            try:
                # Collect system metrics
                resource_metrics = self.resource_monitor()
                
                # Record system metrics
                self.metrics.record_system_metrics(
                    resource_metrics.get("cpu", 0),
                    resource_metrics.get("memory", 0),
                    resource_metrics.get("network", 0),
                    resource_metrics.get("disk", 0)
                )
                
                # Collect metrics every 5 seconds
                time.sleep(5.0)
            
            except Exception as e:
                logger.error(f"Error collecting metrics: {str(e)}")
                time.sleep(5.0)

# Singleton instance for global access
_default_service = None

def get_sync_service() -> SyncService:
    """
    Get the default sync service instance.
    
    Returns:
        Default sync service instance
    """
    global _default_service
    
    if _default_service is None:
        _default_service = SyncService()
    
    return _default_service