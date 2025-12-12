"""
Common schemas used across the API.

This module defines base models, error responses, and shared utilities.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict
from datetime import datetime
from enum import Enum


class Status(str, Enum):
    """API response status."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field that caused the error (if applicable)")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    status: Status = Field(default=Status.ERROR, description="Response status")
    error: ErrorDetail = Field(..., description="Error details")
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "error",
            "error": {
                "code": "INVALID_INPUT",
                "message": "Humidity must be between 0 and 100",
                "field": "humidity",
                "details": {"provided_value": 150}
            },
            "request_id": "req_abc123",
            "timestamp": "2024-08-15T14:30:00"
        }
    })


class ValidationErrorResponse(BaseModel):
    """Response for validation errors."""
    
    status: Status = Field(default=Status.ERROR, description="Response status")
    errors: list[ErrorDetail] = Field(..., description="List of validation errors")
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class SuccessResponse(BaseModel):
    """Standard success response wrapper."""
    
    status: Status = Field(default=Status.SUCCESS, description="Response status")
    data: Any = Field(..., description="Response data")
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there's a next page")
    has_prev: bool = Field(..., description="Whether there's a previous page")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    
    status: Status = Field(default=Status.SUCCESS, description="Response status")
    data: list[Any] = Field(..., description="List of items")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class LocationData(BaseModel):
    """Location information."""
    
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    name: Optional[str] = Field(None, description="Location name")
    state: Optional[str] = Field(None, description="State/region")
    country: Optional[str] = Field(default="Nigeria", description="Country")


class TimeRange(BaseModel):
    """Time range for queries."""
    
    start_time: datetime = Field(..., description="Start timestamp")
    end_time: datetime = Field(..., description="End timestamp")
    
    @property
    def duration_hours(self) -> float:
        """Calculate duration in hours."""
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600


class GeoJSONFeature(BaseModel):
    """GeoJSON feature for spatial data."""
    
    type: str = Field(default="Feature", description="GeoJSON type")
    geometry: Dict[str, Any] = Field(..., description="GeoJSON geometry")
    properties: Dict[str, Any] = Field(..., description="Feature properties")


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON feature collection."""
    
    type: str = Field(default="FeatureCollection", description="GeoJSON type")
    features: list[GeoJSONFeature] = Field(..., description="List of features")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [3.3792, 6.5244]
                    },
                    "properties": {
                        "name": "Lagos",
                        "risk_level": "high",
                        "flood_probability": 0.87
                    }
                }
            ]
        }
    })


# ==================== Common Enums ====================

class ModelType(str, Enum):
    """Available model types."""
    FLOOD_RISK_SCORER = "flood_risk_scorer"
    FLOOD_NOWCASTER = "flood_nowcaster"
    ANOMALY_DETECTOR = "anomaly_detector"


class DataSource(str, Enum):
    """Data source types."""
    SENSOR = "sensor"
    SATELLITE = "satellite"
    MANUAL = "manual"
    API = "api"


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    EMERGENCY = "emergency"
