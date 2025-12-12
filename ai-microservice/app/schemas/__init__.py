"""Pydantic schemas for API requests and responses."""

# Prediction schemas
from app.schemas.predictions import (
    # Enums
    RiskLevel,
    AnomalySeverity,
    
    # Flood Risk
    FloodRiskRequest,
    FloodRiskResponse,
    
    # Nowcasting
    WeatherSequence,
    NowcastRequest,
    HorizonPrediction,
    NowcastResponse,
    
    # Anomaly Detection
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    
    # Batch
    BatchFloodRiskRequest,
    BatchFloodRiskResponse,
    
    # Health
    ModelHealthResponse,
    SystemHealthResponse,
    
    # Evacuation Zones
    EvacuationZoneRequest,
    EvacuationZoneResponse,
    EvacuationZone,
    ShelterInfo,
)

# Common schemas
from app.schemas.common import (
    # Response wrappers
    Status,
    ErrorDetail,
    ErrorResponse,
    ValidationErrorResponse,
    SuccessResponse,
    PaginatedResponse,
    PaginationMeta,
    
    # Common types
    LocationData,
    TimeRange,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    
    # Enums
    ModelType,
    DataSource,
    AlertLevel,
)

__all__ = [
    # Prediction enums
    "RiskLevel",
    "AnomalySeverity",
    
    # Flood Risk
    "FloodRiskRequest",
    "FloodRiskResponse",
    
    # Nowcasting
    "WeatherSequence",
    "NowcastRequest",
    "HorizonPrediction",
    "NowcastResponse",
    
    # Anomaly Detection
    "AnomalyDetectionRequest",
    "AnomalyDetectionResponse",
    
    # Batch
    "BatchFloodRiskRequest",
    "BatchFloodRiskResponse",
    
    # Health
    "ModelHealthResponse",
    "SystemHealthResponse",
    
    # Evacuation Zones
    "EvacuationZoneRequest",
    "EvacuationZoneResponse",
    "EvacuationZone",
    "ShelterInfo",
    
    # Common
    "Status",
    "ErrorDetail",
    "ErrorResponse",
    "ValidationErrorResponse",
    "SuccessResponse",
    "PaginatedResponse",
    "PaginationMeta",
    "LocationData",
    "TimeRange",
    "GeoJSONFeature",
    "GeoJSONFeatureCollection",
    "ModelType",
    "DataSource",
    "AlertLevel",
]
