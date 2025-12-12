# 🌊 Guardy AI - API Examples

Complete examples for all API endpoints with curl commands, request bodies, and responses.

## Table of Contents

- [Authentication](#authentication)
- [Prediction Endpoints](#prediction-endpoints)
  - [1. Flood Risk Assessment](#1-flood-risk-assessment)
  - [2. Nowcast Prediction](#2-nowcast-prediction)
  - [3. Anomaly Detection](#3-anomaly-detection)
  - [4. Batch Prediction](#4-batch-prediction)
  - [5. Evacuation Zones](#5-evacuation-zones)
- [Model Management Endpoints](#model-management-endpoints)
  - [6. System Status](#6-system-status)
  - [7. Model Metadata](#7-model-metadata)
  - [8. Model Statistics](#8-model-statistics)
  - [9. Reload All Models](#9-reload-all-models)
  - [10. Reload Specific Model](#10-reload-specific-model)
  - [11. Clear Model Cache](#11-clear-model-cache)
- [Health Endpoints](#health-endpoints)
  - [12. Health Check](#12-health-check)
- [Error Responses](#error-responses)
- [Best Practices](#best-practices)

---

## Authentication

Currently, the API does not require authentication for development. For production deployment, consider implementing:

- API Key authentication
- OAuth 2.0
- JWT tokens

---

## Prediction Endpoints

### 1. Flood Risk Assessment

Assess flood risk for a specific location based on weather conditions.

**Endpoint:** `POST /api/v1/predict/flood-risk`

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/predict/flood-risk" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "LOC-001",
    "latitude": 9.0820,
    "longitude": 8.6753,
    "rainfall_mm": 150.5,
    "temperature": 28.3,
    "humidity": 85.2,
    "soil_moisture": 72.5,
    "river_level_m": 8.5,
    "historical_data": {
      "avg_rainfall_7d": 120.3,
      "max_rainfall_24h": 180.0,
      "flood_events_30d": 2
    }
  }'
```

**Response (200 OK):**

```json
{
  "location_id": "LOC-001",
  "risk_level": "high",
  "risk_score": 0.87,
  "confidence": 0.92,
  "factors": {
    "rainfall_contribution": 0.35,
    "river_level_contribution": 0.28,
    "soil_moisture_contribution": 0.15,
    "historical_contribution": 0.09
  },
  "recommendation": "Immediate evacuation recommended. Activate emergency response protocols.",
  "timestamp": "2024-12-02T10:30:00Z"
}
```

**High Risk Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/predict/flood-risk" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "CRITICAL-ZONE-01",
    "latitude": 9.0820,
    "longitude": 8.6753,
    "rainfall_mm": 250.0,
    "temperature": 29.0,
    "humidity": 95.0,
    "soil_moisture": 85.0,
    "river_level_m": 12.5
  }'
```

**Low Risk Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/predict/flood-risk" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "SAFE-ZONE-01",
    "latitude": 9.0820,
    "longitude": 8.6753,
    "rainfall_mm": 5.0,
    "temperature": 25.0,
    "humidity": 50.0,
    "soil_moisture": 35.0,
    "river_level_m": 2.0
  }'
```

---

### 2. Nowcast Prediction

Generate flood predictions for 1-7 days ahead using time series analysis.

**Endpoint:** `POST /api/v1/predict/nowcast`

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/predict/nowcast" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "LOC-001",
    "time_series": [
      {
        "timestamp": "2024-12-01T00:00:00Z",
        "rainfall_mm": 45.2,
        "river_level_m": 5.3,
        "temperature": 27.5,
        "humidity": 78.0
      },
      {
        "timestamp": "2024-12-01T06:00:00Z",
        "rainfall_mm": 52.8,
        "river_level_m": 5.8,
        "temperature": 28.1,
        "humidity": 82.0
      },
      {
        "timestamp": "2024-12-01T12:00:00Z",
        "rainfall_mm": 68.5,
        "river_level_m": 6.5,
        "temperature": 29.0,
        "humidity": 85.5
      },
      {
        "timestamp": "2024-12-01T18:00:00Z",
        "rainfall_mm": 85.3,
        "river_level_m": 7.2,
        "temperature": 28.8,
        "humidity": 88.0
      },
      {
        "timestamp": "2024-12-02T00:00:00Z",
        "rainfall_mm": 95.0,
        "river_level_m": 7.8,
        "temperature": 28.5,
        "humidity": 90.0
      }
    ],
    "forecast_horizon_hours": 168
  }'
```

**Response (200 OK):**

```json
{
  "location_id": "LOC-001",
  "predictions": [
    {
      "timestamp": "2024-12-02T06:00:00Z",
      "flood_probability": 0.12,
      "predicted_rainfall_mm": 42.5,
      "predicted_river_level_m": 5.8,
      "confidence": 0.88
    },
    {
      "timestamp": "2024-12-02T12:00:00Z",
      "flood_probability": 0.18,
      "predicted_rainfall_mm": 55.3,
      "predicted_river_level_m": 6.2,
      "confidence": 0.85
    },
    {
      "timestamp": "2024-12-03T00:00:00Z",
      "flood_probability": 0.45,
      "predicted_rainfall_mm": 120.0,
      "predicted_river_level_m": 8.5,
      "confidence": 0.78
    }
  ],
  "trend": "rising",
  "peak_risk_time": "2024-12-03T12:00:00Z",
  "alert_level": "watch"
}
```

**Custom Horizon Example (24 hours):**

```bash
curl -X POST "http://localhost:8000/api/v1/predict/nowcast" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "LOC-002",
    "time_series": [...],
    "forecast_horizon_hours": 24
  }'
```

---

### 3. Anomaly Detection

Detect unusual sensor readings that may indicate equipment malfunction or extreme weather.

**Endpoint:** `POST /api/v1/predict/anomaly`

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/predict/anomaly" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "SENSOR-001",
    "readings": [
      {
        "timestamp": "2024-12-02T10:00:00Z",
        "rainfall_mm": 45.2,
        "temperature": 28.5,
        "humidity": 75.0,
        "river_level_m": 5.3
      },
      {
        "timestamp": "2024-12-02T10:05:00Z",
        "rainfall_mm": 48.1,
        "temperature": 28.6,
        "humidity": 76.2,
        "river_level_m": 5.4
      },
      {
        "timestamp": "2024-12-02T10:10:00Z",
        "rainfall_mm": 255.0,
        "temperature": 15.0,
        "humidity": 99.0,
        "river_level_m": 18.5
      }
    ]
  }'
```

**Response (200 OK):**

```json
{
  "sensor_id": "SENSOR-001",
  "anomalies_detected": 1,
  "anomaly_details": [
    {
      "timestamp": "2024-12-02T10:10:00Z",
      "anomaly_score": 0.92,
      "is_anomaly": true,
      "affected_metrics": [
        "rainfall_mm",
        "temperature",
        "river_level_m"
      ],
      "severity": "critical",
      "possible_causes": [
        "Sensor malfunction",
        "Extreme weather event",
        "Data transmission error"
      ]
    }
  ],
  "overall_health": "warning",
  "recommendation": "Investigate sensor SENSOR-001 immediately. Anomalous readings detected."
}
```

**Normal Readings Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/predict/anomaly" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "SENSOR-002",
    "readings": [
      {"timestamp": "2024-12-02T10:00:00Z", "rainfall_mm": 10.5, "temperature": 26.0, "humidity": 65.0, "river_level_m": 3.2},
      {"timestamp": "2024-12-02T10:05:00Z", "rainfall_mm": 11.2, "temperature": 26.1, "humidity": 65.5, "river_level_m": 3.3},
      {"timestamp": "2024-12-02T10:10:00Z", "rainfall_mm": 10.8, "temperature": 26.0, "humidity": 65.8, "river_level_m": 3.3}
    ]
  }'
```

---

### 4. Batch Prediction

Process multiple locations simultaneously for efficient monitoring.

**Endpoint:** `POST /api/v1/predict/batch`

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {
        "location_id": "LOC-001",
        "latitude": 9.0820,
        "longitude": 8.6753,
        "rainfall_mm": 150.5,
        "temperature": 28.3,
        "humidity": 85.2,
        "soil_moisture": 72.5,
        "river_level_m": 8.5
      },
      {
        "location_id": "LOC-002",
        "latitude": 9.1234,
        "longitude": 8.7890,
        "rainfall_mm": 45.0,
        "temperature": 26.5,
        "humidity": 68.0,
        "soil_moisture": 45.0,
        "river_level_m": 4.2
      },
      {
        "location_id": "LOC-003",
        "latitude": 9.2000,
        "longitude": 8.8000,
        "rainfall_mm": 200.0,
        "temperature": 29.0,
        "humidity": 92.0,
        "soil_moisture": 88.0,
        "river_level_m": 11.5
      }
    ]
  }'
```

**Response (200 OK):**

```json
{
  "total_locations": 3,
  "processed": 3,
  "failed": 0,
  "results": [
    {
      "location_id": "LOC-001",
      "risk_level": "high",
      "risk_score": 0.87,
      "confidence": 0.92
    },
    {
      "location_id": "LOC-002",
      "risk_level": "low",
      "risk_score": 0.15,
      "confidence": 0.95
    },
    {
      "location_id": "LOC-003",
      "risk_level": "very_high",
      "risk_score": 0.96,
      "confidence": 0.89
    }
  ],
  "summary": {
    "very_high_risk": 1,
    "high_risk": 1,
    "medium_risk": 0,
    "low_risk": 1
  },
  "processing_time_ms": 156
}
```

**Large Batch Example (50 locations):**

```bash
# Generate 50 locations programmatically
python -c '
import json
locations = []
for i in range(50):
    locations.append({
        "location_id": f"LOC-{i:03d}",
        "latitude": 9.0 + i * 0.01,
        "longitude": 8.6 + i * 0.01,
        "rainfall_mm": 50.0 + i * 2,
        "temperature": 25.0 + i * 0.1,
        "humidity": 60.0 + i * 0.5,
        "soil_moisture": 40.0 + i * 0.8,
        "river_level_m": 4.0 + i * 0.1
    })
print(json.dumps({"locations": locations}))
' | curl -X POST "http://localhost:8000/api/v1/predict/batch" \
  -H "Content-Type: application/json" \
  -d @-
```

---

### 5. Evacuation Zones

Generate evacuation zones and shelter recommendations based on flood risk.

**Endpoint:** `POST /api/v1/predict/evacuation-zones`

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/predict/evacuation-zones" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "FLOOD-ZONE-001",
    "latitude": 9.0820,
    "longitude": 8.6753,
    "current_risk_score": 0.87,
    "affected_radius_km": 5.0,
    "population_density": 2500,
    "infrastructure": {
      "schools": 12,
      "hospitals": 3,
      "bridges": 8
    }
  }'
```

**Response (200 OK):**

```json
{
  "evacuation_zones": [
    {
      "zone_id": "EVAC-001-RED",
      "priority": "immediate",
      "radius_km": 2.0,
      "estimated_population": 10000,
      "risk_level": "critical",
      "evacuation_routes": [
        {"route_id": "R-001", "direction": "northwest", "distance_km": 8.5},
        {"route_id": "R-002", "direction": "northeast", "distance_km": 10.2}
      ]
    },
    {
      "zone_id": "EVAC-001-ORANGE",
      "priority": "high",
      "radius_km": 3.5,
      "estimated_population": 15000,
      "risk_level": "high",
      "evacuation_routes": [
        {"route_id": "R-003", "direction": "west", "distance_km": 12.0}
      ]
    }
  ],
  "shelters": [
    {
      "shelter_id": "SHELTER-001",
      "name": "Community Center North",
      "latitude": 9.1520,
      "longitude": 8.7253,
      "capacity": 5000,
      "distance_km": 9.2,
      "available": true,
      "facilities": ["medical", "food", "water", "communications"]
    },
    {
      "shelter_id": "SHELTER-002",
      "name": "Sports Stadium West",
      "latitude": 9.0920,
      "longitude": 8.5753,
      "capacity": 8000,
      "distance_km": 11.5,
      "available": true,
      "facilities": ["medical", "food", "water", "power"]
    }
  ],
  "geojson": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Polygon",
          "coordinates": [[[8.6753, 9.0820], [8.6953, 9.0820], [8.6953, 9.1020], [8.6753, 9.1020], [8.6753, 9.0820]]]
        },
        "properties": {
          "zone_id": "EVAC-001-RED",
          "priority": "immediate",
          "risk_level": "critical"
        }
      }
    ]
  },
  "total_affected_population": 25000,
  "evacuation_time_estimate_hours": 6,
  "generated_at": "2024-12-02T10:30:00Z"
}
```

**Custom Radius Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/predict/evacuation-zones" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "FLOOD-ZONE-002",
    "latitude": 9.0820,
    "longitude": 8.6753,
    "current_risk_score": 0.65,
    "affected_radius_km": 10.0
  }'
```

---

## Model Management Endpoints

### 6. System Status

Get comprehensive status of all ML models and system health.

**Endpoint:** `GET /api/v1/models/status`

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/models/status"
```

**Response (200 OK):**

```json
{
  "status": "healthy",
  "models": {
    "risk_scorer": {
      "loaded": true,
      "version": "1.0.0",
      "last_updated": "2024-12-01T08:00:00Z",
      "file_size_mb": 1.42,
      "accuracy": 0.9699
    },
    "nowcaster": {
      "loaded": true,
      "version": "1.0.0",
      "last_updated": "2024-12-01T08:00:00Z",
      "file_size_mb": 0.43,
      "accuracy": 0.933
    },
    "anomaly_detector": {
      "loaded": true,
      "version": "1.0.0",
      "last_updated": "2024-12-01T08:00:00Z",
      "file_size_mb": 0.71,
      "f1_score": 0.985
    }
  },
  "system": {
    "uptime_seconds": 86400,
    "total_predictions": 15234,
    "average_response_time_ms": 45,
    "memory_usage_mb": 512.8,
    "cpu_usage_percent": 23.5
  },
  "timestamp": "2024-12-02T10:30:00Z"
}
```

---

### 7. Model Metadata

Get detailed metadata for a specific model.

**Endpoint:** `GET /api/v1/models/{model_name}/metadata`

**Request (FloodRiskScorer):**

```bash
curl -X GET "http://localhost:8000/api/v1/models/risk_scorer/metadata"
```

**Response (200 OK):**

```json
{
  "model_name": "risk_scorer",
  "version": "1.0.0",
  "type": "ensemble",
  "algorithm": "Random Forest + Gradient Boosting",
  "training_data": {
    "samples": 50000,
    "features": 15,
    "date_range": "2020-01-01 to 2024-11-30"
  },
  "performance": {
    "accuracy": 0.9699,
    "precision": 0.95,
    "recall": 0.94,
    "f1_score": 0.945
  },
  "features": [
    "rainfall_mm",
    "temperature",
    "humidity",
    "soil_moisture",
    "river_level_m",
    "historical_avg_rainfall_7d",
    "historical_max_rainfall_24h",
    "historical_flood_events_30d",
    "latitude",
    "longitude",
    "elevation",
    "land_use",
    "drainage_capacity",
    "population_density",
    "distance_to_water_body"
  ],
  "output": {
    "risk_levels": ["very_low", "low", "medium", "high", "very_high"],
    "threshold_values": [0.2, 0.4, 0.6, 0.8]
  },
  "file_path": "/workspaces/Guardy/ai-microservice/models/flood_risk_scorer_v1.pkl",
  "file_size_mb": 1.42,
  "last_modified": "2024-12-01T08:00:00Z",
  "checksum": "a3f5e9c2d1b8f7e4a2c9d8f1e3b5a7c2"
}
```

**Request (FloodNowcaster):**

```bash
curl -X GET "http://localhost:8000/api/v1/models/nowcaster/metadata"
```

**Request (AnomalyDetector):**

```bash
curl -X GET "http://localhost:8000/api/v1/models/anomaly_detector/metadata"
```

---

### 8. Model Statistics

Get usage statistics for a specific model.

**Endpoint:** `GET /api/v1/models/{model_name}/stats`

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/models/risk_scorer/stats"
```

**Response (200 OK):**

```json
{
  "model_name": "risk_scorer",
  "statistics": {
    "total_predictions": 8542,
    "predictions_today": 1234,
    "average_inference_time_ms": 12.5,
    "p95_inference_time_ms": 25.0,
    "p99_inference_time_ms": 45.0,
    "cache_hit_rate": 0.68,
    "error_rate": 0.002
  },
  "predictions_by_risk_level": {
    "very_low": 2156,
    "low": 3421,
    "medium": 1892,
    "high": 856,
    "very_high": 217
  },
  "hourly_usage": [
    {"hour": "00:00", "count": 245},
    {"hour": "01:00", "count": 189},
    {"hour": "02:00", "count": 167}
  ],
  "last_updated": "2024-12-02T10:30:00Z"
}
```

---

### 9. Reload All Models

Hot-reload all ML models without server downtime.

**Endpoint:** `POST /api/v1/models/reload`

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/models/reload" \
  -H "Content-Type: application/json"
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "All models reloaded successfully",
  "models_reloaded": [
    {
      "name": "risk_scorer",
      "status": "success",
      "reload_time_ms": 1245,
      "previous_version": "1.0.0",
      "new_version": "1.0.1"
    },
    {
      "name": "nowcaster",
      "status": "success",
      "reload_time_ms": 856,
      "previous_version": "1.0.0",
      "new_version": "1.0.1"
    },
    {
      "name": "anomaly_detector",
      "status": "success",
      "reload_time_ms": 432,
      "previous_version": "1.0.0",
      "new_version": "1.0.1"
    }
  ],
  "total_reload_time_ms": 2533,
  "timestamp": "2024-12-02T10:35:00Z"
}
```

---

### 10. Reload Specific Model

Reload a single model without affecting others.

**Endpoint:** `POST /api/v1/models/{model_name}/reload`

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/models/risk_scorer/reload" \
  -H "Content-Type: application/json"
```

**Response (200 OK):**

```json
{
  "status": "success",
  "model_name": "risk_scorer",
  "message": "Model 'risk_scorer' reloaded successfully",
  "reload_time_ms": 1245,
  "previous_version": "1.0.0",
  "new_version": "1.0.1",
  "file_size_mb": 1.45,
  "checksum": "b4g6f0d3e2c9g8f5b3d0e9g2f4c6b8d3",
  "timestamp": "2024-12-02T10:36:00Z"
}
```

---

### 11. Clear Model Cache

Clear prediction cache for a specific model to force fresh predictions.

**Endpoint:** `DELETE /api/v1/models/{model_name}/cache`

**Request:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/models/risk_scorer/cache"
```

**Response (200 OK):**

```json
{
  "status": "success",
  "model_name": "risk_scorer",
  "message": "Cache cleared for model 'risk_scorer'",
  "entries_cleared": 1547,
  "memory_freed_mb": 23.8,
  "timestamp": "2024-12-02T10:37:00Z"
}
```

---

## Health Endpoints

### 12. Health Check

Simple endpoint to verify API availability.

**Endpoint:** `GET /api/v1/models/health`

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/models/health"
```

**Response (200 OK):**

```json
{
  "status": "healthy",
  "timestamp": "2024-12-02T10:30:00Z",
  "version": "1.0.0",
  "uptime_seconds": 86400
}
```

**Response (503 Service Unavailable - Models not loaded):**

```json
{
  "status": "unhealthy",
  "error": "Models not loaded",
  "timestamp": "2024-12-02T10:30:00Z"
}
```

---

## Error Responses

### 400 Bad Request - Invalid Input

```json
{
  "detail": "Validation error",
  "errors": [
    {
      "loc": ["body", "rainfall_mm"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "temperature"],
      "msg": "value is not a valid float",
      "type": "type_error.float"
    }
  ]
}
```

### 422 Unprocessable Entity - Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "latitude"],
      "msg": "ensure this value is greater than -90",
      "type": "value_error.number.not_gt",
      "ctx": {"limit_value": -90}
    }
  ]
}
```

### 503 Service Unavailable - Models Not Loaded

```json
{
  "detail": "ML models are not loaded. Please try again later or contact support."
}
```

### 500 Internal Server Error

```json
{
  "detail": "An unexpected error occurred during prediction",
  "error_id": "err_abc123xyz",
  "timestamp": "2024-12-02T10:30:00Z"
}
```

---

## Best Practices

### 1. Input Validation

Always validate inputs before sending requests:

```bash
# ✅ Good - All required fields present
curl -X POST "http://localhost:8000/api/v1/predict/flood-risk" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "LOC-001",
    "latitude": 9.0820,
    "longitude": 8.6753,
    "rainfall_mm": 150.5,
    "temperature": 28.3,
    "humidity": 85.2,
    "soil_moisture": 72.5,
    "river_level_m": 8.5
  }'

# ❌ Bad - Missing required fields
curl -X POST "http://localhost:8000/api/v1/predict/flood-risk" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "LOC-001",
    "latitude": 9.0820,
    "longitude": 8.6753
  }'
```

### 2. Batch Processing

Use batch endpoints for multiple locations:

```bash
# ✅ Good - Batch request (1 API call)
curl -X POST "http://localhost:8000/api/v1/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{"locations": [...]}'

# ❌ Bad - Multiple individual requests (N API calls)
for location in "${locations[@]}"; do
  curl -X POST "http://localhost:8000/api/v1/predict/flood-risk" -d "$location"
done
```

### 3. Error Handling

Always handle errors gracefully:

```bash
response=$(curl -s -w "\n%{http_code}" \
  -X POST "http://localhost:8000/api/v1/predict/flood-risk" \
  -H "Content-Type: application/json" \
  -d '{"location_id": "LOC-001", ...}')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
  echo "Success: $body"
elif [ "$http_code" -eq 503 ]; then
  echo "Service temporarily unavailable. Retrying..."
  sleep 5
  # Retry logic
else
  echo "Error $http_code: $body"
fi
```

### 4. Rate Limiting

Respect rate limits and implement backoff:

```bash
# Implement exponential backoff
attempt=0
max_attempts=3
while [ $attempt -lt $max_attempts ]; do
  response=$(curl -s -w "%{http_code}" ...)
  if [ "$response" -eq 429 ]; then
    sleep $((2 ** attempt))
    ((attempt++))
  else
    break
  fi
done
```

### 5. Caching

Cache predictions for identical inputs:

```bash
# Use consistent location_id for caching benefits
location_id="LOC-001"  # Consistent ID enables cache hits
```

### 6. Monitoring

Monitor API health regularly:

```bash
# Health check every 60 seconds
watch -n 60 'curl -s http://localhost:8000/api/v1/models/health | jq'
```

### 7. Timeouts

Set appropriate timeouts:

```bash
# Set 30-second timeout for predictions
curl --max-time 30 \
  -X POST "http://localhost:8000/api/v1/predict/flood-risk" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### 8. Compression

Enable compression for large responses:

```bash
curl --compressed \
  -X POST "http://localhost:8000/api/v1/predict/batch" \
  -H "Content-Type: application/json" \
  -H "Accept-Encoding: gzip" \
  -d '{...}'
```

---

## Production Deployment Considerations

### Environment Variables

```bash
export API_BASE_URL="https://api.guardy.example.com"
export API_KEY="your-api-key-here"
export REQUEST_TIMEOUT=30
export MAX_RETRIES=3
```

### Authenticated Requests (Future)

```bash
curl -X POST "${API_BASE_URL}/api/v1/predict/flood-risk" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### Load Testing

```bash
# Use Apache Bench for load testing
ab -n 1000 -c 10 -p request.json -T application/json \
  http://localhost:8000/api/v1/predict/flood-risk

# Use wrk for advanced testing
wrk -t12 -c400 -d30s \
  -s post.lua \
  http://localhost:8000/api/v1/predict/flood-risk
```

---

## Support

For issues or questions:
- **GitHub Issues**: https://github.com/HenryTech12/Guardy/issues
- **Email**: support@guardy.example.com
- **Documentation**: https://github.com/HenryTech12/Guardy/blob/master/ai-microservice/README.md

---

**Last Updated**: December 2, 2024  
**API Version**: 1.0.0
