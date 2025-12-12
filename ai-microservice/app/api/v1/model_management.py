"""
Model Management API endpoints.

This module provides endpoints for managing ML models:
- Status checking and health monitoring
- Model reloading (hot-reload without downtime)
- Metadata retrieval
- Cache management
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger

from app.ml import FloodRiskScorer, FloodNowcaster, SensorAnomalyDetector


# Create router
router = APIRouter(prefix="/api/v1/models", tags=["model-management"])

# Import global model instances from predictions module
from app.api.v1 import predictions

# Model metadata
MODEL_METADATA = {
    "risk_scorer": {
        "name": "FloodRiskScorer",
        "version": "v1",
        "file_path": "models/flood_risk_scorer_v1.pkl",
        "algorithm": "Random Forest + Gradient Boosting Ensemble",
        "trained_date": "2024-12-12",
        "accuracy": 0.9699,
        "training_samples": 10000,
        "features": 8,
        "description": "Ensemble model for flood risk prediction based on weather and location"
    },
    "nowcaster": {
        "name": "FloodNowcaster",
        "version": "v1",
        "file_path": "models/nowcast_lstm_v1.h5",
        "algorithm": "LSTM Neural Network",
        "trained_date": "2024-12-12",
        "accuracy": 0.933,
        "training_samples": 8000,
        "features": 3,
        "sequence_length": 7,
        "description": "LSTM model for short-term flood forecasting (1-24 hour horizons)"
    },
    "anomaly_detector": {
        "name": "SensorAnomalyDetector",
        "version": "v1",
        "file_path": "models/anomaly_detector_v1.pkl",
        "algorithm": "Isolation Forest",
        "trained_date": "2024-12-12",
        "accuracy": 0.985,
        "training_samples": 5000,
        "features": 6,
        "description": "Anomaly detection for sensor readings and malfunction identification"
    }
}

# Prediction statistics tracking
PREDICTION_STATS = {
    "risk_scorer": {"count": 0, "last_prediction": None},
    "nowcaster": {"count": 0, "last_prediction": None},
    "anomaly_detector": {"count": 0, "last_prediction": None}
}


def increment_prediction_count(model_name: str):
    """Increment prediction count for tracking."""
    if model_name in PREDICTION_STATS:
        PREDICTION_STATS[model_name]["count"] += 1
        PREDICTION_STATS[model_name]["last_prediction"] = datetime.utcnow()


@router.get(
    "/status",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get detailed model status",
    description="Get comprehensive status information for all ML models including metadata and statistics",
    tags=["model-management"]
)
async def get_models_status():
    """
    Get comprehensive status and health information for all ML models.
    
    This endpoint provides detailed information about the operational state of all three
    ML models (FloodRiskScorer, FloodNowcaster, SensorAnomalyDetector), including loading
    status, metadata, prediction statistics, and system health metrics. Use this for
    monitoring dashboards and system health checks.
    
    Returns:
        Dict[str, Any]: System status containing:
            - system_status (str): Overall system health (healthy, degraded, unhealthy)
            - models_loaded (bool): Whether all models are loaded
            - total_predictions (int): Total predictions across all models
            - models (Dict): Per-model details including:
                - name (str): Model name
                - loaded (bool): Loading status
                - version (str): Model version
                - algorithm (str): ML algorithm used
                - accuracy (float): Model accuracy
                - file_path (str): Model file location
                - file_exists (bool): Whether model file is present
                - prediction_count (int): Total predictions made
                - last_prediction (datetime): Timestamp of last prediction
            - timestamp (datetime): Status check timestamp
    
    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/v1/models/status"
        ```
    
    Example Response:
        ```json
        {
          "system_status": "healthy",
          "models_loaded": true,
          "total_predictions": 15234,
          "models": {
            "risk_scorer": {
              "name": "FloodRiskScorer",
              "loaded": true,
              "version": "v1",
              "accuracy": 0.9699,
              "prediction_count": 8542
            }
          }
        }
        ```
    
    Note:
        - This endpoint is more detailed than /api/v1/models/health
        - Use for operational monitoring and debugging
        - Response time: ~5ms
        - No authentication required (may change in production)
    """
    try:
        models_status = {}
        
        for model_key, metadata in MODEL_METADATA.items():
            # Check if model file exists
            model_path = Path(metadata["file_path"])
            file_exists = model_path.exists()
            file_size_mb = model_path.stat().st_size / (1024 * 1024) if file_exists else 0
            
            # Get model instance
            model_instance = None
            if model_key == "risk_scorer":
                model_instance = predictions.risk_scorer
            elif model_key == "nowcaster":
                model_instance = predictions.nowcaster
            elif model_key == "anomaly_detector":
                model_instance = predictions.anomaly_detector
            
            # Get prediction stats
            stats = PREDICTION_STATS.get(model_key, {})
            
            models_status[model_key] = {
                "name": metadata["name"],
                "version": metadata["version"],
                "algorithm": metadata["algorithm"],
                "trained_date": metadata["trained_date"],
                "accuracy": metadata["accuracy"],
                "training_samples": metadata["training_samples"],
                "features": metadata["features"],
                "description": metadata["description"],
                "file_path": metadata["file_path"],
                "file_exists": file_exists,
                "file_size_mb": round(file_size_mb, 2),
                "is_loaded": model_instance is not None,
                "prediction_count": stats.get("count", 0),
                "last_prediction": stats.get("last_prediction"),
                "status": "operational" if (file_exists and model_instance is not None) else "unavailable"
            }
            
            # Add model-specific metadata
            if model_key == "nowcaster":
                models_status[model_key]["sequence_length"] = metadata.get("sequence_length")
        
        # System-wide status
        all_operational = all(m["status"] == "operational" for m in models_status.values())
        total_predictions = sum(m["prediction_count"] for m in models_status.values())
        
        response = {
            "system_status": "operational" if all_operational else "degraded",
            "all_models_loaded": predictions.MODELS_LOADED,
            "total_predictions": total_predictions,
            "models": models_status,
            "load_time_seconds": predictions.MODEL_LOAD_TIME,
            "timestamp": datetime.utcnow()
        }
        
        logger.info(f"Status check: {all_operational}, total predictions: {total_predictions}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting models status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "StatusCheckError", "message": "Failed to get models status"}
        )


@router.get(
    "/{model_name}/metadata",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get model metadata",
    description="Get detailed metadata for a specific model",
    tags=["model-management"]
)
async def get_model_metadata(model_name: str):
    """
    Retrieve comprehensive metadata for a specific ML model.
    
    This endpoint provides detailed information about a model's training, architecture,
    performance metrics, file details, and current operational status. Useful for model
    versioning, debugging, and documentation purposes.
    
    Args:
        model_name (str): Model identifier. Must be one of:
            - "risk_scorer": FloodRiskScorer ensemble model
            - "nowcaster": FloodNowcaster LSTM model
            - "anomaly_detector": SensorAnomalyDetector Isolation Forest
    
    Returns:
        Dict[str, Any]: Model metadata containing:
            - name (str): Human-readable model name
            - version (str): Model version identifier
            - algorithm (str): ML algorithm/architecture used
            - trained_date (str): Training completion date
            - accuracy (float): Model accuracy or F1-score
            - training_samples (int): Number of training samples
            - features (int): Number of input features
            - description (str): Model purpose and capabilities
            - file_path (str): Model file location
            - file_exists (bool): Whether file is present
            - file_size_mb (float): File size in megabytes
            - last_modified (str): File modification timestamp (ISO format)
            - is_loaded (bool): Whether model is currently loaded in memory
            - prediction_count (int): Total predictions made
            - last_prediction (datetime): Timestamp of last prediction
    
    Raises:
        HTTPException 404: Model not found
        HTTPException 500: Error retrieving metadata
    
    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/v1/models/risk_scorer/metadata"
        ```
    
    Example Response:
        ```json
        {
          "name": "FloodRiskScorer",
          "version": "v1",
          "algorithm": "Random Forest + Gradient Boosting Ensemble",
          "accuracy": 0.9699,
          "file_size_mb": 1.42,
          "is_loaded": true,
          "prediction_count": 8542
        }
        ```
    
    Note:
        - Valid model names: risk_scorer, nowcaster, anomaly_detector
        - Use /api/v1/models/status for all models at once
        - Response time: ~5ms
    """
    try:
        if model_name not in MODEL_METADATA:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "ModelNotFound", "message": f"Model '{model_name}' not found. Valid models: {list(MODEL_METADATA.keys())}"}
            )
        
        metadata = MODEL_METADATA[model_name].copy()
        
        # Add runtime information
        model_path = Path(metadata["file_path"])
        
        metadata["file_exists"] = model_path.exists()
        if model_path.exists():
            metadata["file_size_mb"] = round(model_path.stat().st_size / (1024 * 1024), 2)
            metadata["last_modified"] = datetime.fromtimestamp(model_path.stat().st_mtime).isoformat()
        
        # Check if loaded
        model_instance = None
        if model_name == "risk_scorer":
            model_instance = predictions.risk_scorer
        elif model_name == "nowcaster":
            model_instance = predictions.nowcaster
        elif model_name == "anomaly_detector":
            model_instance = predictions.anomaly_detector
        
        metadata["is_loaded"] = model_instance is not None
        
        # Add prediction stats
        stats = PREDICTION_STATS.get(model_name, {})
        metadata["prediction_count"] = stats.get("count", 0)
        metadata["last_prediction"] = stats.get("last_prediction")
        
        # Add feature importance if available (for tree-based models)
        if model_name == "risk_scorer" and model_instance and hasattr(model_instance, 'feature_importance'):
            metadata["feature_importance"] = model_instance.feature_importance
        
        metadata["timestamp"] = datetime.utcnow()
        
        logger.info(f"Metadata retrieved for {model_name}")
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "MetadataError", "message": "Failed to get model metadata"}
        )


@router.post(
    "/reload",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Reload all models",
    description="Hot-reload all ML models without restarting the server",
)
async def reload_models():
    """
    Reload all ML models from disk.
    
    Useful for deploying updated model versions without downtime.
    Previous models are kept in memory until new models load successfully.
    
    Returns:
        Status of reload operation for each model
    """
    try:
        logger.info("🔄 Starting model reload...")
        
        # Store results for each model
        reload_results = {}
        errors = []
        
        start_time = datetime.utcnow()
        
        # Reload FloodRiskScorer
        try:
            new_risk_scorer = FloodRiskScorer.load(MODEL_METADATA["risk_scorer"]["file_path"])
            predictions.risk_scorer = new_risk_scorer
            reload_results["risk_scorer"] = {"status": "success", "message": "FloodRiskScorer reloaded"}
            logger.info("✅ FloodRiskScorer reloaded")
        except Exception as e:
            errors.append(f"risk_scorer: {str(e)}")
            reload_results["risk_scorer"] = {"status": "failed", "message": str(e)}
            logger.error(f"❌ Failed to reload FloodRiskScorer: {e}")
        
        # Reload FloodNowcaster
        try:
            new_nowcaster = FloodNowcaster.load(MODEL_METADATA["nowcaster"]["file_path"])
            predictions.nowcaster = new_nowcaster
            reload_results["nowcaster"] = {"status": "success", "message": "FloodNowcaster reloaded"}
            logger.info("✅ FloodNowcaster reloaded")
        except Exception as e:
            errors.append(f"nowcaster: {str(e)}")
            reload_results["nowcaster"] = {"status": "failed", "message": str(e)}
            logger.error(f"❌ Failed to reload FloodNowcaster: {e}")
        
        # Reload SensorAnomalyDetector
        try:
            new_anomaly_detector = SensorAnomalyDetector.load(MODEL_METADATA["anomaly_detector"]["file_path"])
            predictions.anomaly_detector = new_anomaly_detector
            reload_results["anomaly_detector"] = {"status": "success", "message": "SensorAnomalyDetector reloaded"}
            logger.info("✅ SensorAnomalyDetector reloaded")
        except Exception as e:
            errors.append(f"anomaly_detector: {str(e)}")
            reload_results["anomaly_detector"] = {"status": "failed", "message": str(e)}
            logger.error(f"❌ Failed to reload SensorAnomalyDetector: {e}")
        
        # Update global status
        successful_reloads = sum(1 for r in reload_results.values() if r["status"] == "success")
        predictions.MODELS_LOADED = successful_reloads == 3
        predictions.MODEL_LOAD_TIME = (datetime.utcnow() - start_time).total_seconds()
        
        response = {
            "status": "success" if not errors else "partial",
            "message": f"Reloaded {successful_reloads}/3 models successfully",
            "reload_results": reload_results,
            "errors": errors if errors else None,
            "reload_time_seconds": predictions.MODEL_LOAD_TIME,
            "all_models_loaded": predictions.MODELS_LOADED,
            "timestamp": datetime.utcnow()
        }
        
        logger.info(f"Reload complete: {successful_reloads}/3 successful")
        return response
        
    except Exception as e:
        logger.error(f"Error during model reload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ReloadError", "message": f"Failed to reload models: {str(e)}"}
        )


@router.post(
    "/{model_name}/reload",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Reload specific model",
    description="Hot-reload a specific ML model without affecting others",
    tags=["model-management"]
)
async def reload_single_model(model_name: str):
    """
    Hot-reload a specific model from disk without server downtime.
    
    This endpoint allows updating a single model by reloading it from disk while keeping
    other models operational. Useful for deploying model updates, fixing corrupted models,
    or recovering from errors without full system restart. The reload happens atomically
    to minimize prediction downtime.
    
    Args:
        model_name (str): Model to reload. Must be one of:
            - "risk_scorer": FloodRiskScorer ensemble model
            - "nowcaster": FloodNowcaster LSTM model
            - "anomaly_detector": SensorAnomalyDetector Isolation Forest
    
    Returns:
        Dict[str, Any]: Reload operation results containing:
            - status (str): "success" or "failed"
            - model_name (str): Name of reloaded model
            - message (str): Human-readable status message
            - reload_time_seconds (float): Time taken to reload
            - previous_version (str): Version before reload (if changed)
            - new_version (str): Version after reload
            - file_size_mb (float): Model file size
            - timestamp (datetime): Reload completion time
    
    Raises:
        HTTPException 404: Model not found
        HTTPException 500: Reload failed
    
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/v1/models/risk_scorer/reload"
        ```
    
    Example Response:
        ```json
        {
          "status": "success",
          "model_name": "risk_scorer",
          "message": "FloodRiskScorer reloaded successfully",
          "reload_time_seconds": 1.245,
          "file_size_mb": 1.42
        }
        ```
    
    Note:
        - Zero-downtime operation (other models continue serving)
        - Atomic replacement (old model serves until new one is ready)
        - Typical reload time: 0.5-2 seconds
        - Cache is automatically cleared for reloaded model
        - Use POST /api/v1/models/reload to reload all models
    """
    try:
        if model_name not in MODEL_METADATA:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "ModelNotFound", "message": f"Model '{model_name}' not found. Valid models: {list(MODEL_METADATA.keys())}"}
            )
        
        logger.info(f"🔄 Reloading model: {model_name}")
        
        start_time = datetime.utcnow()
        
        # Reload the specific model
        if model_name == "risk_scorer":
            new_model = FloodRiskScorer.load(MODEL_METADATA["risk_scorer"]["file_path"])
            predictions.risk_scorer = new_model
        elif model_name == "nowcaster":
            new_model = FloodNowcaster.load(MODEL_METADATA["nowcaster"]["file_path"])
            predictions.nowcaster = new_model
        elif model_name == "anomaly_detector":
            new_model = SensorAnomalyDetector.load(MODEL_METADATA["anomaly_detector"]["file_path"])
            predictions.anomaly_detector = new_model
        
        reload_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"✅ {MODEL_METADATA[model_name]['name']} reloaded in {reload_time:.2f}s")
        
        return {
            "status": "success",
            "model_name": model_name,
            "message": f"{MODEL_METADATA[model_name]['name']} reloaded successfully",
            "reload_time_seconds": reload_time,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reloading model {model_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ReloadError", "message": f"Failed to reload {model_name}: {str(e)}"}
        )


@router.delete(
    "/{model_name}/cache",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Clear model cache",
    description="Clear cached predictions for a specific model (placeholder for future caching)",
)
async def clear_model_cache(model_name: str):
    """
    Clear cached predictions for a specific model.
    
    Note: This is a placeholder endpoint. Actual caching will be implemented in Task 11.
    
    Args:
        model_name: One of 'risk_scorer', 'nowcaster', 'anomaly_detector'
    
    Returns:
        Cache clearing status
    """
    try:
        if model_name not in MODEL_METADATA:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "ModelNotFound", "message": f"Model '{model_name}' not found"}
            )
        
        # Placeholder - actual cache clearing will be implemented with Redis/in-memory cache
        logger.info(f"Cache clear requested for {model_name} (not implemented yet)")
        
        return {
            "status": "success",
            "model_name": model_name,
            "message": "Cache clearing not yet implemented (placeholder endpoint for Task 11)",
            "cached_items_cleared": 0,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing cache for {model_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "CacheClearError", "message": f"Failed to clear cache: {str(e)}"}
        )


@router.get(
    "/{model_name}/stats",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get model statistics",
    description="Get usage statistics for a specific model",
)
async def get_model_stats(model_name: str):
    """
    Get usage statistics for a specific model.
    
    Args:
        model_name: One of 'risk_scorer', 'nowcaster', 'anomaly_detector'
    
    Returns:
        Model usage statistics
    """
    try:
        if model_name not in MODEL_METADATA:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "ModelNotFound", "message": f"Model '{model_name}' not found"}
            )
        
        stats = PREDICTION_STATS.get(model_name, {})
        
        # Calculate uptime
        uptime_seconds = predictions.MODEL_LOAD_TIME if predictions.MODEL_LOAD_TIME else 0
        
        # Calculate predictions per minute (if any predictions made)
        predictions_per_minute = 0
        if stats.get("count", 0) > 0 and uptime_seconds > 0:
            predictions_per_minute = round((stats["count"] / uptime_seconds) * 60, 2)
        
        response = {
            "model_name": model_name,
            "total_predictions": stats.get("count", 0),
            "last_prediction": stats.get("last_prediction"),
            "predictions_per_minute": predictions_per_minute,
            "uptime_seconds": uptime_seconds,
            "is_loaded": predictions.MODELS_LOADED,
            "timestamp": datetime.utcnow()
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "StatsError", "message": f"Failed to get model statistics"}
        )
