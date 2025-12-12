"""
Performance optimization utilities.

This module provides utilities for profiling, batch processing optimization,
and performance monitoring.
"""

import time
import functools
import asyncio
from typing import Callable, Any, List, Dict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import numpy as np
from loguru import logger

from app.config import settings


# Global thread pool for CPU-bound tasks
_thread_pool = ThreadPoolExecutor(max_workers=settings.WORKER_THREADS)


def timeit(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function that logs execution time
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = (time.perf_counter() - start_time) * 1000  # Convert to ms
            logger.debug(f"⏱️ {func.__name__} took {elapsed:.2f}ms")
            return result
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.error(f"❌ {func.__name__} failed after {elapsed:.2f}ms: {e}")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.debug(f"⏱️ {func.__name__} took {elapsed:.2f}ms")
            return result
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.error(f"❌ {func.__name__} failed after {elapsed:.2f}ms: {e}")
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


async def run_in_threadpool(func: Callable, *args, **kwargs) -> Any:
    """
    Run CPU-bound function in thread pool.
    
    Args:
        func: Function to run
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Function result
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_thread_pool, functools.partial(func, *args, **kwargs))


def batch_predict_vectorized(
    model: Any,
    features_list: List[np.ndarray],
    batch_size: int = 32
) -> List[Any]:
    """
    Optimize batch predictions using vectorization.
    
    Args:
        model: ML model with predict method
        features_list: List of feature arrays
        batch_size: Batch size for processing
        
    Returns:
        List of predictions
    """
    # Stack features into single array for vectorized operations
    features_array = np.vstack(features_list)
    
    # Process in batches to manage memory
    predictions = []
    total_samples = len(features_array)
    
    for i in range(0, total_samples, batch_size):
        batch = features_array[i:i + batch_size]
        batch_predictions = model.predict(batch)
        predictions.extend(batch_predictions)
    
    return predictions


async def parallel_predictions(
    prediction_func: Callable,
    requests: List[Dict[str, Any]],
    max_concurrent: int = 10
) -> List[Dict[str, Any]]:
    """
    Execute multiple predictions concurrently.
    
    Args:
        prediction_func: Async prediction function
        requests: List of request dictionaries
        max_concurrent: Maximum concurrent predictions
        
    Returns:
        List of prediction results
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_predict(request: Dict[str, Any]) -> Dict[str, Any]:
        async with semaphore:
            try:
                return await prediction_func(request)
            except Exception as e:
                logger.error(f"Prediction failed for request: {e}")
                return {"error": str(e), "request": request}
    
    # Execute all predictions concurrently with semaphore limit
    tasks = [bounded_predict(req) for req in requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return results


class PerformanceMonitor:
    """Track and report performance metrics."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.request_times: List[float] = []
        self.total_requests: int = 0
        self.failed_requests: int = 0
        self.cache_hits: int = 0
        self.cache_misses: int = 0
    
    def record_request(self, duration_ms: float, cached: bool = False, failed: bool = False):
        """
        Record request metrics.
        
        Args:
            duration_ms: Request duration in milliseconds
            cached: Whether result was from cache
            failed: Whether request failed
        """
        self.total_requests += 1
        
        if failed:
            self.failed_requests += 1
        else:
            self.request_times.append(duration_ms)
        
        if cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.request_times:
            return {
                "total_requests": self.total_requests,
                "failed_requests": self.failed_requests,
                "success_rate": 0.0,
                "cache_hit_rate": 0.0
            }
        
        times_array = np.array(self.request_times)
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": len(self.request_times),
            "failed_requests": self.failed_requests,
            "success_rate": len(self.request_times) / max(self.total_requests, 1),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hits / max(self.cache_hits + self.cache_misses, 1),
            "avg_response_time_ms": float(np.mean(times_array)),
            "median_response_time_ms": float(np.median(times_array)),
            "p95_response_time_ms": float(np.percentile(times_array, 95)),
            "p99_response_time_ms": float(np.percentile(times_array, 99)),
            "min_response_time_ms": float(np.min(times_array)),
            "max_response_time_ms": float(np.max(times_array)),
        }
    
    def reset(self):
        """Reset all metrics."""
        self.request_times.clear()
        self.total_requests = 0
        self.failed_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0


# Global performance monitor
performance_monitor = PerformanceMonitor()
