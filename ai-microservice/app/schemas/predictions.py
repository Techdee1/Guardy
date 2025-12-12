"""
Pydantic schemas for ML prediction endpoints.

This module defines request/response models for:
- Flood Risk Prediction (FloodRiskScorer)
- Flood Nowcasting (FloodNowcaster)
- Sensor Anomaly Detection (SensorAnomalyDetector)
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Literal, Any
from datetime import datetime
from enum import Enum


# ==================== Enums ====================

class RiskLevel(str, Enum):
    """Risk level categories."""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


class AnomalySeverity(str, Enum):
    """Anomaly severity levels."""
    NORMAL = "normal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ==================== Flood Risk Prediction Schemas ====================

class FloodRiskRequest(BaseModel):
    """Request schema for flood risk prediction."""
    
    # Location
    latitude: float = Field(..., ge=-90, le=90, description="Location latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Location longitude")
    location_name: Optional[str] = Field(None, description="Location name (e.g., Lagos, Lokoja)")
    
    # Weather conditions
    rainfall_mm: float = Field(..., ge=0, description="Current rainfall in millimeters")
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: int = Field(..., ge=0, le=100, description="Humidity percentage")
    
    # Temporal context
    date: Optional[datetime] = Field(None, description="Date for prediction (defaults to now)")
    
    # Historical context (optional, will use defaults if not provided)
    rainfall_7d_mean: Optional[float] = Field(None, ge=0, description="7-day average rainfall")
    rainfall_30d_mean: Optional[float] = Field(None, ge=0, description="30-day average rainfall")
    
    model_config = ConfigDict(protected_namespaces=(), json_schema_extra={
        "example": {
            "latitude": 6.5244,
            "longitude": 3.3792,
            "location_name": "Lagos",
            "rainfall_mm": 85.0,
            "temperature": 28.5,
            "humidity": 80,
            "date": "2024-08-15T14:30:00",
            "rainfall_7d_mean": 45.5,
            "rainfall_30d_mean": 32.1
        }
    })


class FloodRiskResponse(BaseModel):
    """Response schema for flood risk prediction."""
    
    # Prediction results
    flood_probability: float = Field(..., ge=0, le=1, description="Probability of flood occurrence (0-1)")
    risk_score: float = Field(..., ge=0, le=100, description="Risk score (0-100)")
    risk_level: RiskLevel = Field(..., description="Risk level category")
    
    # Confidence and metadata
    confidence: float = Field(..., ge=0, le=1, description="Model confidence (0-1)")
    model_version: str = Field(..., description="Model version used")
    predicted_at: datetime = Field(..., description="Prediction timestamp")
    
    # Additional insights
    top_contributing_factors: List[Dict[str, float]] = Field(
        ..., 
        description="Top features contributing to the prediction"
    )
    
    # Recommendations
    recommended_action: str = Field(..., description="Recommended action based on risk level")
    
    model_config = ConfigDict(protected_namespaces=(), json_schema_extra={
        "example": {
            "flood_probability": 0.87,
            "risk_score": 87.0,
            "risk_level": "high",
            "confidence": 0.94,
            "model_version": "flood_risk_scorer_v1",
            "predicted_at": "2024-08-15T14:30:00",
            "top_contributing_factors": [
                {"rainfall_7d_mean": 0.285},
                {"rainfall_7d_max": 0.128},
                {"day_of_year": 0.095}
            ],
            "recommended_action": "Issue flood alert and prepare evacuation routes"
        }
    })


# ==================== Flood Nowcasting Schemas ====================

class WeatherSequence(BaseModel):
    """Historical weather sequence for nowcasting."""
    
    timestamp: datetime = Field(..., description="Timestamp of reading")
    rainfall_mm: float = Field(..., ge=0, description="Rainfall in millimeters")
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: int = Field(..., ge=0, le=100, description="Humidity percentage")


class NowcastRequest(BaseModel):
    """Request schema for flood nowcasting."""
    
    # Location
    latitude: float = Field(..., ge=-90, le=90, description="Location latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Location longitude")
    location_name: Optional[str] = Field(None, description="Location name")
    
    # Historical sequence (minimum 7 days for LSTM)
    weather_sequence: List[WeatherSequence] = Field(
        ..., 
        min_length=7,
        description="Historical weather data (minimum 7 readings)"
    )
    
    # Forecast horizons
    forecast_horizons: Optional[List[int]] = Field(
        default=[1, 3, 6, 12, 24],
        description="Forecast horizons in hours"
    )
    
    @field_validator('weather_sequence')
    @classmethod
    def validate_sequence_length(cls, v):
        if len(v) < 7:
            raise ValueError("weather_sequence must contain at least 7 readings")
        return v
    
    model_config = ConfigDict(protected_namespaces=(), json_schema_extra={
        "example": {
            "latitude": 7.7989,
            "longitude": 6.7397,
            "location_name": "Lokoja",
            "weather_sequence": [
                {"timestamp": "2024-08-08T00:00:00", "rainfall_mm": 12.5, "temperature": 27.5, "humidity": 75},
                {"timestamp": "2024-08-09T00:00:00", "rainfall_mm": 18.2, "temperature": 28.1, "humidity": 78},
                {"timestamp": "2024-08-10T00:00:00", "rainfall_mm": 25.7, "temperature": 27.8, "humidity": 82},
                {"timestamp": "2024-08-11T00:00:00", "rainfall_mm": 45.3, "temperature": 26.9, "humidity": 85},
                {"timestamp": "2024-08-12T00:00:00", "rainfall_mm": 52.1, "temperature": 26.5, "humidity": 88},
                {"timestamp": "2024-08-13T00:00:00", "rainfall_mm": 68.4, "temperature": 26.2, "humidity": 90},
                {"timestamp": "2024-08-14T00:00:00", "rainfall_mm": 75.6, "temperature": 26.0, "humidity": 92}
            ],
            "forecast_horizons": [1, 3, 6, 12, 24]
        }
    })


class HorizonPrediction(BaseModel):
    """Prediction for a specific time horizon."""
    
    hours_ahead: int = Field(..., description="Hours into the future")
    flood_probability: float = Field(..., ge=0, le=1, description="Flood probability (0-1)")
    risk_level: RiskLevel = Field(..., description="Risk level for this horizon")
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")
    forecast_time: datetime = Field(..., description="Forecasted timestamp")


class NowcastResponse(BaseModel):
    """Response schema for flood nowcasting."""
    
    # Predictions for each horizon
    predictions: List[HorizonPrediction] = Field(..., description="Predictions for each time horizon")
    
    # Overall assessment
    max_risk_horizon: int = Field(..., description="Hours ahead with highest flood risk")
    max_risk_probability: float = Field(..., ge=0, le=1, description="Highest probability across all horizons")
    
    # Model metadata
    model_version: str = Field(..., description="Model version used")
    predicted_at: datetime = Field(..., description="Prediction timestamp")
    sequence_length: int = Field(..., description="Number of historical readings used")
    
    # Recommendations
    early_warning: bool = Field(..., description="Whether early warning should be issued")
    recommended_action: str = Field(..., description="Recommended action")
    
    model_config = ConfigDict(protected_namespaces=(), json_schema_extra={
        "example": {
            "predictions": [
                {"hours_ahead": 1, "flood_probability": 0.65, "risk_level": "moderate", "confidence": 0.92, "forecast_time": "2024-08-15T15:00:00"},
                {"hours_ahead": 3, "flood_probability": 0.78, "risk_level": "high", "confidence": 0.88, "forecast_time": "2024-08-15T17:00:00"},
                {"hours_ahead": 6, "flood_probability": 0.85, "risk_level": "high", "confidence": 0.82, "forecast_time": "2024-08-15T20:00:00"},
                {"hours_ahead": 12, "flood_probability": 0.91, "risk_level": "extreme", "confidence": 0.75, "forecast_time": "2024-08-16T02:00:00"},
                {"hours_ahead": 24, "flood_probability": 0.88, "risk_level": "high", "confidence": 0.65, "forecast_time": "2024-08-16T14:00:00"}
            ],
            "max_risk_horizon": 12,
            "max_risk_probability": 0.91,
            "model_version": "nowcast_lstm_v1",
            "predicted_at": "2024-08-15T14:00:00",
            "sequence_length": 7,
            "early_warning": True,
            "recommended_action": "Issue evacuation warning for 12-hour window"
        }
    })


# ==================== Anomaly Detection Schemas ====================

class AnomalyDetectionRequest(BaseModel):
    """Request schema for sensor anomaly detection."""
    
    # Sensor identification
    device_id: str = Field(..., description="Sensor device ID")
    location_name: Optional[str] = Field(None, description="Sensor location")
    
    # Sensor readings
    rainfall_mm: float = Field(..., ge=0, description="Rainfall reading in millimeters")
    temperature: float = Field(..., description="Temperature reading in Celsius")
    humidity: int = Field(..., ge=0, le=100, description="Humidity reading percentage")
    
    # Additional sensor metrics (optional)
    rainfall_7d_mean: Optional[float] = Field(None, ge=0, description="7-day average rainfall")
    temperature_deviation: Optional[float] = Field(None, description="Temperature deviation from normal")
    
    # Reading metadata
    timestamp: datetime = Field(..., description="Reading timestamp")
    
    model_config = ConfigDict(protected_namespaces=(), json_schema_extra={
        "example": {
            "device_id": "SENSOR_LAG_001",
            "location_name": "Lagos",
            "rainfall_mm": 245.8,
            "temperature": 42.5,
            "humidity": 15,
            "rainfall_7d_mean": 35.2,
            "temperature_deviation": 12.5,
            "timestamp": "2024-08-15T14:30:00"
        }
    })


class AnomalyDetectionResponse(BaseModel):
    """Response schema for sensor anomaly detection."""
    
    # Detection results
    is_anomaly: bool = Field(..., description="Whether reading is anomalous")
    anomaly_score: float = Field(..., description="Anomaly score (lower = more anomalous)")
    severity: AnomalySeverity = Field(..., description="Anomaly severity level")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence")
    
    # Details
    anomalous_features: List[str] = Field(..., description="Features identified as anomalous")
    threshold: float = Field(..., description="Anomaly score threshold")
    
    # Recommendations
    recommended_action: str = Field(..., description="Recommended action")
    requires_maintenance: bool = Field(..., description="Whether sensor maintenance is needed")
    
    # Model metadata
    model_version: str = Field(..., description="Model version used")
    detected_at: datetime = Field(..., description="Detection timestamp")
    
    model_config = ConfigDict(protected_namespaces=(), json_schema_extra={
        "example": {
            "is_anomaly": True,
            "anomaly_score": -0.710,
            "severity": "high",
            "confidence": 0.89,
            "anomalous_features": ["rainfall_mm", "temperature", "humidity"],
            "threshold": -0.407,
            "recommended_action": "Inspect sensor for malfunction or extreme weather event",
            "requires_maintenance": True,
            "model_version": "anomaly_detector_v1",
            "detected_at": "2024-08-15T14:30:00"
        }
    })


# ==================== Batch Prediction Schemas ====================

class BatchFloodRiskRequest(BaseModel):
    """Request schema for batch flood risk predictions."""
    
    predictions: List[FloodRiskRequest] = Field(
        ..., 
        min_length=1,
        max_length=100,
        description="List of prediction requests (max 100)"
    )
    
    @field_validator('predictions')
    @classmethod
    def validate_batch_size(cls, v):
        if len(v) > 100:
            raise ValueError("Batch size cannot exceed 100 predictions")
        return v


class BatchFloodRiskResponse(BaseModel):
    """Response schema for batch flood risk predictions."""
    
    predictions: List[FloodRiskResponse] = Field(..., description="List of prediction results")
    total_predictions: int = Field(..., description="Total number of predictions")
    high_risk_count: int = Field(..., description="Number of high/extreme risk predictions")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")


# ==================== Health Check Schemas ====================

class ModelHealthResponse(BaseModel):
    """Response schema for model health check."""
    
    model_config = ConfigDict(protected_namespaces = ())
    
    model_name: str = Field(..., description="Model name")
    status: Literal["healthy", "degraded", "unavailable"] = Field(..., description="Model status")
    version: str = Field(..., description="Model version")
    last_loaded: datetime = Field(..., description="Last time model was loaded")
    predictions_count: int = Field(..., description="Total predictions made")
    avg_inference_time_ms: float = Field(..., description="Average inference time")
    error_rate: float = Field(..., ge=0, le=1, description="Prediction error rate")


class SystemHealthResponse(BaseModel):
    """Response schema for system health check."""
    
    status: Literal["healthy", "degraded", "down"] = Field(..., description="Overall system status")
    models: List[ModelHealthResponse] = Field(..., description="Status of all models")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    cpu_usage_percent: float = Field(..., ge=0, le=100, description="CPU usage percentage")
    
    model_config = ConfigDict(protected_namespaces=(), json_schema_extra={
        "example": {
            "status": "healthy",
            "models": [
                {
                    "model_name": "FloodRiskScorer",
                    "status": "healthy",
                    "version": "v1",
                    "last_loaded": "2024-08-15T10:00:00",
                    "predictions_count": 1547,
                    "avg_inference_time_ms": 2.3,
                    "error_rate": 0.001
                }
            ],
            "uptime_seconds": 86400,
            "memory_usage_mb": 512.5,
            "cpu_usage_percent": 15.2
        }
    })


# ============================================================================
# EVACUATION ZONE SCHEMAS
# ============================================================================

class EvacuationZoneRequest(BaseModel):
    """Request for generating evacuation zones."""
    
    latitude: float = Field(..., ge=-90, le=90, description="Center point latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Center point longitude")
    flood_probability: float = Field(..., ge=0, le=1, description="Flood probability (0-1)")
    risk_level: RiskLevel = Field(..., description="Risk level category")
    location_name: Optional[str] = Field(None, description="Human-readable location name")
    population_density: Optional[int] = Field(None, ge=0, description="Population per km²")
    include_shelters: bool = Field(default=True, description="Include shelter recommendations")
    zone_radii: Optional[list[int]] = Field(
        default=[500, 1000, 2000],
        description="Evacuation zone radii in meters"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "latitude": 28.6139,
            "longitude": 77.2090,
            "flood_probability": 0.75,
            "risk_level": "high",
            "location_name": "New Delhi",
            "population_density": 11320,
            "include_shelters": True,
            "zone_radii": [500, 1000, 2000]
        }
    })


class ShelterInfo(BaseModel):
    """Information about an evacuation shelter."""
    
    name: str = Field(..., description="Shelter name")
    latitude: float = Field(..., description="Shelter latitude")
    longitude: float = Field(..., description="Shelter longitude")
    capacity: int = Field(..., ge=0, description="Maximum capacity (people)")
    distance_meters: float = Field(..., ge=0, description="Distance from flood point (meters)")
    available_resources: list[str] = Field(
        default_factory=list,
        description="Available resources (food, water, medical, etc.)"
    )
    contact: Optional[str] = Field(None, description="Emergency contact number")


class EvacuationZone(BaseModel):
    """Single evacuation zone with details."""
    
    zone_id: str = Field(..., description="Unique zone identifier")
    radius_meters: int = Field(..., ge=0, description="Zone radius in meters")
    priority: str = Field(..., description="Priority level (immediate/high/medium/low)")
    estimated_affected: Optional[int] = Field(None, ge=0, description="Estimated affected population")
    evacuation_time_minutes: int = Field(..., ge=0, description="Recommended evacuation time")
    recommended_routes: list[str] = Field(
        default_factory=list,
        description="Recommended evacuation routes"
    )


class EvacuationZoneResponse(BaseModel):
    """Response with evacuation zones as GeoJSON."""
    
    location: str = Field(..., description="Location name")
    center_point: tuple[float, float] = Field(..., description="Center point (lat, lon)")
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    flood_probability: float = Field(..., ge=0, le=1, description="Flood probability")
    zones: list[EvacuationZone] = Field(..., description="Evacuation zone details")
    shelters: Optional[list[ShelterInfo]] = Field(None, description="Nearby evacuation shelters")
    geojson: Dict[str, Any] = Field(..., description="GeoJSON FeatureCollection with zones")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "location": "New Delhi",
            "center_point": [28.6139, 77.2090],
            "risk_level": "high",
            "flood_probability": 0.75,
            "zones": [
                {
                    "zone_id": "zone_500m",
                    "radius_meters": 500,
                    "priority": "immediate",
                    "estimated_affected": 5000,
                    "evacuation_time_minutes": 15,
                    "recommended_routes": ["Route A to North", "Route B to East"]
                }
            ],
            "shelters": [
                {
                    "name": "Community Center A",
                    "latitude": 28.620,
                    "longitude": 77.215,
                    "capacity": 2000,
                    "distance_meters": 1200,
                    "available_resources": ["food", "water", "medical"],
                    "contact": "+91-11-2345-6789"
                }
            ],
            "geojson": {
                "type": "FeatureCollection",
                "features": []
            },
            "generated_at": "2024-08-15T14:30:00"
        }
    })
