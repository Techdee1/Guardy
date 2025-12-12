"""Tests for prediction API endpoints."""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app

client = TestClient(app)


class TestRiskPredictionEndpoint:
    """Tests for /api/v1/predict/risk endpoint."""
    
    def test_risk_prediction_success_low_risk(self):
        """Test successful risk prediction for low risk scenario."""
        response = client.post(
            "/api/v1/predict/risk",
            json={
                "latitude": 6.5244,
                "longitude": 3.3792,
                "water_level_cm": 25.0,
                "rainfall_mm": 10.0,
                "temperature": 28.5,
                "humidity": 65
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "risk_score" in data
        assert "risk_level" in data
        assert "confidence" in data
        assert "factors" in data
        assert "model_version" in data
        assert data["risk_level"] == "low"
        assert 0 <= data["risk_score"] <= 1
        assert 0 <= data["confidence"] <= 1
        assert isinstance(data["factors"], list)
    
    def test_risk_prediction_success_high_risk(self):
        """Test successful risk prediction for high risk scenario."""
        response = client.post(
            "/api/v1/predict/risk",
            json={
                "latitude": 6.5244,
                "longitude": 3.3792,
                "water_level_cm": 85.0,
                "rainfall_mm": 150.0,
                "temperature": 30.0,
                "humidity": 95
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"] == "high"
        assert data["risk_score"] >= 0.7
    
    def test_risk_prediction_minimal_params(self):
        """Test risk prediction with minimal required parameters."""
        response = client.post(
            "/api/v1/predict/risk",
            json={
                "latitude": 6.5244,
                "longitude": 3.3792,
                "water_level_cm": 45.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"] in ["low", "medium", "high"]
    
    def test_risk_prediction_invalid_latitude(self):
        """Test risk prediction with invalid latitude."""
        response = client.post(
            "/api/v1/predict/risk",
            json={
                "latitude": 95.0,  # Invalid: > 90
                "longitude": 3.3792,
                "water_level_cm": 45.0
            }
        )
        
        assert response.status_code == 422
    
    def test_risk_prediction_invalid_longitude(self):
        """Test risk prediction with invalid longitude."""
        response = client.post(
            "/api/v1/predict/risk",
            json={
                "latitude": 6.5244,
                "longitude": 200.0,  # Invalid: > 180
                "water_level_cm": 45.0
            }
        )
        
        assert response.status_code == 422
    
    def test_risk_prediction_negative_water_level(self):
        """Test risk prediction with negative water level."""
        response = client.post(
            "/api/v1/predict/risk",
            json={
                "latitude": 6.5244,
                "longitude": 3.3792,
                "water_level_cm": -10.0  # Invalid: negative
            }
        )
        
        assert response.status_code == 422
    
    def test_risk_prediction_invalid_humidity(self):
        """Test risk prediction with invalid humidity."""
        response = client.post(
            "/api/v1/predict/risk",
            json={
                "latitude": 6.5244,
                "longitude": 3.3792,
                "water_level_cm": 45.0,
                "humidity": 120  # Invalid: > 100
            }
        )
        
        assert response.status_code == 422
    
    def test_risk_prediction_missing_required_fields(self):
        """Test risk prediction with missing required fields."""
        response = client.post(
            "/api/v1/predict/risk",
            json={
                "latitude": 6.5244
                # Missing longitude and water_level_cm
            }
        )
        
        assert response.status_code == 422


class TestNowcastEndpoint:
    """Tests for /api/v1/predict/nowcast endpoint."""
    
    def test_nowcast_success_rising_trend(self):
        """Test successful nowcast with rising water level trend."""
        response = client.post(
            "/api/v1/predict/nowcast",
            json={
                "device_id": "ESP32_001",
                "historical_readings": [
                    {"water_level_cm": 20.0, "timestamp": "2025-12-11T10:00:00Z"},
                    {"water_level_cm": 25.0, "timestamp": "2025-12-11T10:05:00Z"},
                    {"water_level_cm": 30.0, "timestamp": "2025-12-11T10:10:00Z"}
                ],
                "forecast_minutes": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == "ESP32_001"
        assert "predicted_water_level_cm" in data
        assert "confidence" in data
        assert "trend" in data
        assert "forecast_minutes" in data
        assert "model_version" in data
        assert data["trend"] == "rising"
        assert data["forecast_minutes"] == 30
        assert 0 <= data["confidence"] <= 1
    
    def test_nowcast_success_falling_trend(self):
        """Test successful nowcast with falling water level trend."""
        response = client.post(
            "/api/v1/predict/nowcast",
            json={
                "device_id": "ESP32_002",
                "historical_readings": [
                    {"water_level_cm": 60.0, "timestamp": "2025-12-11T10:00:00Z"},
                    {"water_level_cm": 50.0, "timestamp": "2025-12-11T10:05:00Z"},
                    {"water_level_cm": 40.0, "timestamp": "2025-12-11T10:10:00Z"}
                ],
                "forecast_minutes": 15
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["trend"] == "falling"
        assert data["forecast_minutes"] == 15
    
    def test_nowcast_stable_trend(self):
        """Test nowcast with stable water level."""
        response = client.post(
            "/api/v1/predict/nowcast",
            json={
                "device_id": "ESP32_003",
                "historical_readings": [
                    {"water_level_cm": 35.0, "timestamp": "2025-12-11T10:00:00Z"},
                    {"water_level_cm": 35.5, "timestamp": "2025-12-11T10:05:00Z"},
                    {"water_level_cm": 35.2, "timestamp": "2025-12-11T10:10:00Z"}
                ],
                "forecast_minutes": 60
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["trend"] == "stable"
    
    def test_nowcast_insufficient_data(self):
        """Test nowcast with insufficient historical data."""
        response = client.post(
            "/api/v1/predict/nowcast",
            json={
                "device_id": "ESP32_004",
                "historical_readings": [
                    {"water_level_cm": 25.0, "timestamp": "2025-12-11T10:00:00Z"}
                ],
                "forecast_minutes": 30
            }
        )
        
        # Should fail validation (min_length=2)
        assert response.status_code == 422
    
    def test_nowcast_invalid_forecast_minutes(self):
        """Test nowcast with invalid forecast minutes."""
        response = client.post(
            "/api/v1/predict/nowcast",
            json={
                "device_id": "ESP32_005",
                "historical_readings": [
                    {"water_level_cm": 20.0, "timestamp": "2025-12-11T10:00:00Z"},
                    {"water_level_cm": 25.0, "timestamp": "2025-12-11T10:05:00Z"}
                ],
                "forecast_minutes": 45  # Invalid: must be 15, 30, or 60
            }
        )
        
        assert response.status_code == 422
    
    def test_nowcast_missing_device_id(self):
        """Test nowcast with missing device_id."""
        response = client.post(
            "/api/v1/predict/nowcast",
            json={
                "historical_readings": [
                    {"water_level_cm": 20.0, "timestamp": "2025-12-11T10:00:00Z"},
                    {"water_level_cm": 25.0, "timestamp": "2025-12-11T10:05:00Z"}
                ],
                "forecast_minutes": 30
            }
        )
        
        assert response.status_code == 422
    
    def test_nowcast_invalid_timestamp_format(self):
        """Test nowcast with invalid timestamp format."""
        response = client.post(
            "/api/v1/predict/nowcast",
            json={
                "device_id": "ESP32_006",
                "historical_readings": [
                    {"water_level_cm": 20.0, "timestamp": "invalid-timestamp"},
                    {"water_level_cm": 25.0, "timestamp": "2025-12-11T10:05:00Z"}
                ],
                "forecast_minutes": 30
            }
        )
        
        assert response.status_code == 422


class TestAnomalyDetectionEndpoint:
    """Tests for /api/v1/detect/anomaly endpoint."""
    
    def test_anomaly_detection_normal_reading(self):
        """Test anomaly detection with normal sensor reading."""
        response = client.post(
            "/api/v1/detect/anomaly",
            json={
                "device_id": "ESP32_001",
                "water_level_cm": 30.0,
                "temperature": 28.5,
                "humidity": 75,
                "battery_voltage": 3.8,
                "historical_mean": 28.0,
                "historical_std": 5.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == "ESP32_001"
        assert "is_anomaly" in data
        assert "anomaly_score" in data
        assert "anomaly_types" in data
        assert "confidence" in data
        assert "details" in data
        assert "model_version" in data
        assert isinstance(data["is_anomaly"], bool)
        assert 0 <= data["anomaly_score"] <= 1
        assert isinstance(data["anomaly_types"], list)
    
    def test_anomaly_detection_negative_value(self):
        """Test anomaly detection with negative water level."""
        response = client.post(
            "/api/v1/detect/anomaly",
            json={
                "device_id": "ESP32_002",
                "water_level_cm": -5.0,  # Anomalous: negative
                "temperature": 28.0,
                "humidity": 70,
                "battery_voltage": 3.7
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_anomaly"] is True
        assert "negative_value" in data["anomaly_types"]
        assert data["anomaly_score"] > 0.5
    
    def test_anomaly_detection_unrealistic_value(self):
        """Test anomaly detection with unrealistic water level."""
        response = client.post(
            "/api/v1/detect/anomaly",
            json={
                "device_id": "ESP32_003",
                "water_level_cm": 250.0,  # Anomalous: > 200
                "temperature": 28.0,
                "humidity": 70
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_anomaly"] is True
        assert "unrealistic_high_value" in data["anomaly_types"]
    
    def test_anomaly_detection_statistical_outlier(self):
        """Test anomaly detection with statistical outlier."""
        response = client.post(
            "/api/v1/detect/anomaly",
            json={
                "device_id": "ESP32_004",
                "water_level_cm": 80.0,
                "historical_mean": 30.0,
                "historical_std": 5.0  # 80 is 10 std deviations from mean
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_anomaly"] is True
        assert "statistical_outlier" in data["anomaly_types"]
    
    def test_anomaly_detection_temperature_anomaly(self):
        """Test anomaly detection with extreme temperature."""
        response = client.post(
            "/api/v1/detect/anomaly",
            json={
                "device_id": "ESP32_005",
                "water_level_cm": 30.0,
                "temperature": 60.0,  # Anomalous: > 50
                "humidity": 75
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_anomaly"] is True
        assert "temperature_anomaly" in data["anomaly_types"]
    
    def test_anomaly_detection_humidity_anomaly(self):
        """Test anomaly detection with invalid humidity."""
        response = client.post(
            "/api/v1/detect/anomaly",
            json={
                "device_id": "ESP32_006",
                "water_level_cm": 30.0,
                "humidity": 150  # Should fail validation (> 100)
            }
        )
        
        assert response.status_code == 422
    
    def test_anomaly_detection_battery_anomaly(self):
        """Test anomaly detection with low battery."""
        response = client.post(
            "/api/v1/detect/anomaly",
            json={
                "device_id": "ESP32_007",
                "water_level_cm": 30.0,
                "battery_voltage": 2.0  # Anomalous: < 2.5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_anomaly"] is True
        assert "battery_anomaly" in data["anomaly_types"]
    
    def test_anomaly_detection_minimal_params(self):
        """Test anomaly detection with minimal parameters."""
        response = client.post(
            "/api/v1/detect/anomaly",
            json={
                "device_id": "ESP32_008",
                "water_level_cm": 35.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "is_anomaly" in data
    
    def test_anomaly_detection_missing_device_id(self):
        """Test anomaly detection with missing device_id."""
        response = client.post(
            "/api/v1/detect/anomaly",
            json={
                "water_level_cm": 30.0
            }
        )
        
        assert response.status_code == 422


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""
    
    def test_openapi_json_accessible(self):
        """Test that OpenAPI JSON schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "/api/v1/predict/risk" in data["paths"]
        assert "/api/v1/predict/nowcast" in data["paths"]
        assert "/api/v1/detect/anomaly" in data["paths"]
    
    def test_swagger_docs_accessible(self):
        """Test that Swagger UI is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc_accessible(self):
        """Test that ReDoc is accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200
