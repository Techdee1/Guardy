"""
Performance metrics endpoints for monitoring and profiling.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from loguru import logger

from app.utils.performance import performance_monitor
from app.cache import cache_manager


# Create router
router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.get(
    "/performance",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get performance metrics",
    description="Get detailed performance statistics including response times and cache metrics",
)
async def get_performance_metrics():
    """
    Retrieve comprehensive performance metrics for API monitoring.
    
    Returns detailed statistics on request times, success rates, cache performance,
    and system resource utilization. Use this endpoint for dashboards, alerting,
    and performance optimization.
    
    Returns:
        Dict[str, Any]: Performance metrics containing:
            - request_metrics: Request counts, success/failure rates
            - response_times: Average, median, p95, p99 response times
            - cache_metrics: Cache hits, misses, hit rate
            - system_metrics: Redis statistics if available
    
    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/v1/metrics/performance"
        ```
    """
    try:
        # Get request performance metrics
        perf_stats = performance_monitor.get_stats()
        
        # Get cache statistics
        cache_stats = await cache_manager.get_stats()
        
        return {
            "request_metrics": {
                "total_requests": perf_stats.get("total_requests", 0),
                "successful_requests": perf_stats.get("successful_requests", 0),
                "failed_requests": perf_stats.get("failed_requests", 0),
                "success_rate": perf_stats.get("success_rate", 0.0),
            },
            "response_times_ms": {
                "average": perf_stats.get("avg_response_time_ms", 0.0),
                "median": perf_stats.get("median_response_time_ms", 0.0),
                "p95": perf_stats.get("p95_response_time_ms", 0.0),
                "p99": perf_stats.get("p99_response_time_ms", 0.0),
                "min": perf_stats.get("min_response_time_ms", 0.0),
                "max": perf_stats.get("max_response_time_ms", 0.0),
            },
            "cache_metrics": {
                "hits": perf_stats.get("cache_hits", 0),
                "misses": perf_stats.get("cache_misses", 0),
                "hit_rate": perf_stats.get("cache_hit_rate", 0.0),
            },
            "redis_metrics": cache_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "MetricsError", "message": "Failed to retrieve performance metrics"}
        )


@router.post(
    "/performance/reset",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Reset performance metrics",
    description="Reset all performance counters and statistics",
)
async def reset_performance_metrics():
    """
    Reset all performance metrics counters.
    
    Clears all accumulated statistics including request counts, response times,
    and cache metrics. Useful for benchmarking or testing scenarios.
    
    Returns:
        Dict[str, str]: Status message
    
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/v1/metrics/performance/reset"
        ```
    """
    try:
        performance_monitor.reset()
        logger.info("Performance metrics reset")
        return {"status": "success", "message": "Performance metrics reset successfully"}
        
    except Exception as e:
        logger.error(f"Error resetting performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ResetError", "message": "Failed to reset performance metrics"}
        )
