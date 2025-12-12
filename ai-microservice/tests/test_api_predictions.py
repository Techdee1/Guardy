"""Comprehensive tests for all prediction API endpoints."""
import pytest
from fastapi.testclient import TestClient


class TestFloodRiskEndpoint:
    """Tests for POST /api/v1/predict/flood-risk endpoint."""
    
    def test_flood_risk_low(self, client, sample_flood_risk_data):
        """Test flood risk prediction for low risk scenario."""
        response = client.post(
            "/api/v1/predict/flood-risk",
            json=sample_flood_risk_data["low_risk"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "flood_probability" in data
        assert "risk_score" in data
        assert "risk_level" in data
        assert "confidence" in data
        assert "top_contributing_factors" in data
        assert "predicted_at" in data
        
        # Validate values
        assert 0 <= data["flood_probability"] <= 1
        assert 0 <= data["risk_score"] <= 100
        assert 0 <= data["confidence"] <= 1
        assert data["risk_level"] in ["very_low", "low", "moderate", "high", "extreme"]
        assert isinstance(data["top_contributing_factors"], list)
    
    def test_flood_risk_high(self, client, sample_flood_risk_data):
        """Test flood risk prediction for high risk scenario."""
        response = client.post(
            "/api/v1/predict/flood-risk",
            json=sample_flood_risk_data["high_risk"]
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"] in ["high", "extreme"]
        assert data["risk_score"] >= 60.0
    
    def test_flood_risk_validation_latitude(self, client):
        """Test validation for invalid latitude."""
        response = client.post(
            "/api/v1/predict/flood-risk",
            json={
                "latitude": 95.0,  # Invalid
                "longitude": 3.3792,
                "rainfall_mm": 10.0,
                "temperature": 28.0,
                "humidity": 65
            }
        )
        
        assert response.status_code == 422
    
    def test_flood_risk_validation_negative_rainfall(self, client):
        """Test validation for negative rainfall."""
        response = client.post(
            "/api/v1/predict/flood-risk",
            json={
                "latitude": 6.5244,
                "longitude": 3.3792,
                "rainfall_mm": -5.0,  # Invalid
                "temperature": 28.0,
                "humidity": 65
            }
        )
        
        assert response.status_code == 422
    
    def test_flood_risk_minimal_params(self, client):
        """Test with only required parameters."""
        response = client.post(
            "/api/v1/predict/flood-risk",
            json={
                "latitude": 6.5244,
                "longitude": 3.3792,
                "rainfall_mm": 10.0,
                "temperature": 28.0,
                "humidity": 65
            }
        )
        
        assert response.status_code == 200


class TestNowcastEndpoint:
    """Tests for POST /api/v1/predict/nowcast endpoint."""
    
    def test_nowcast_rising_trend(self, client, sample_nowcast_data):
        """Test nowcast for rising water level trend."""
        response = client.post(
            "/api/v1/predict/nowcast",
            json={
                **sample_nowcast_data["location"],
                "historical_data": sample_nowcast_data["rising"],
                "forecast_horizons": [1, 3, 6, 12, 24]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "predictions" in data
        assert "confidence" in data
        assert "trend" in data
        assert "timestamp" in data
        
        # Validate predictions
        assert len(data["predictions"]) == 5  # 5 horizons
        for pred in data["predictions"]:
            assert "horizon_hours" in pred
            assert "predicted_level" in pred
            assert "confidence" in pred
            assert pred["predicted_level"] >= 0
    
    def test_nowcast_stable_trend(self, client, sample_nowcast_data):
        """Test nowcast for stable water level trend."""
        response = client.post(
            "/api/v1/predict/nowcast",
            json={
                **sample_nowcast_data["location"],
                "historical_data": sample_nowcast_data["stable"],
                "forecast_horizons": [1, 6, 12]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["trend"] in ["stable", "rising", "falling"]
    
    def test_nowcast_insufficient_data(self, client):
        """Test nowcast with insufficient historical data."""
        response = client.post(
            "/api/v1/predict/nowcast",
            json={
                "latitude": 6.5244,
                "longitude": 3.3792,
                "historical_data": [],  # Empty
                "forecast_horizons": [1, 6]
            }
        )
        
        assert response.status_code in [400, 422]
    
    def test_nowcast_single_horizon(self, client, sample_nowcast_data):
        """Test nowcast with single forecast horizon."""
        response = client.post(
            "/api/v1/predict/nowcast",
            json={
                **sample_nowcast_data["location"],
                "historical_data": sample_nowcast_data["rising"],
                "forecast_horizons": [6]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 1


class TestAnomalyDetectionEndpoint:
    """Tests for POST /api/v1/predict/anomaly endpoint."""
    
    def test_anomaly_normal_readings(self, client, sample_anomaly_data):
        """Test anomaly detection with normal sensor readings."""
        response = client.post(
            "/api/v1/predict/anomaly",
            json=sample_anomaly_data["normal"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "is_anomaly" in data
        assert "anomaly_score" in data
        assert "confidence" in data
        assert "anomaly_types" in data
        assert "timestamp" in data
        
        # Validate values
        assert isinstance(data["is_anomaly"], bool)
        assert -1 <= data["anomaly_score"] <= 1
        assert 0 <= data["confidence"] <= 1
        assert isinstance(data["anomaly_types"], list)
    
    def test_anomaly_anomalous_readings(self, client, sample_anomaly_data):
        """Test anomaly detection with anomalous sensor readings."""
        response = client.post(
            "/api/v1/predict/anomaly",
            json=sample_anomaly_data["anomalous"]
        )
        
        assert response.status_code == 200
        data = response.json()
        # Note: May or may not detect as anomaly depending on model sensitivity
        assert "is_anomaly" in data
        assert "anomaly_score" in data
    
    def test_anomaly_missing_sensor_id(self, client):
        """Test anomaly detection without sensor_id."""
        response = client.post(
            "/api/v1/predict/anomaly",
            json={
                "readings": [
                    {
                        "timestamp": "2024-12-12T10:00:00Z",
                        "value": 25.0,
                        "battery_level": 85.0,
                        "signal_strength": -65
                    }
                ]
            }
        )
        
        assert response.status_code == 422


class TestBatchPredictionEndpoint:
    """Tests for POST /api/v1/predict/batch endpoint."""
    
    def test_batch_single_location(self, client, sample_flood_risk_data):
        """Test batch prediction with single location."""
        response = client.post(
            "/api/v1/predict/batch",
            json={
                "locations": [sample_flood_risk_data["low_risk"]]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "predictions" in data
        assert "total_processed" in data
        assert "timestamp" in data
        
        # Validate predictions
        assert len(data["predictions"]) == 1
        assert data["total_processed"] == 1
        
        pred = data["predictions"][0]
        assert "location_index" in pred
        assert "risk_score" in pred
        assert "risk_level" in pred
    
    def test_batch_multiple_locations(self, client, sample_flood_risk_data):
        """Test batch prediction with multiple locations."""
        response = client.post(
            "/api/v1/predict/batch",
            json={
                "locations": [
                    sample_flood_risk_data["low_risk"],
                    sample_flood_risk_data["medium_risk"],
                    sample_flood_risk_data["high_risk"]
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["predictions"]) == 3
        assert data["total_processed"] == 3
        
        # Verify different risk levels
        risk_levels = [p["risk_level"] for p in data["predictions"]]
        assert len(set(risk_levels)) > 1  # Should have variety
    
    def test_batch_max_limit(self, client, sample_flood_risk_data):
        """Test batch prediction with maximum allowed locations."""
        # Create 100 locations
        locations = [sample_flood_risk_data["low_risk"].copy() for _ in range(100)]
        
        response = client.post(
            "/api/v1/predict/batch",
            json={"locations": locations}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_processed"] == 100
    
    def test_batch_exceed_limit(self, client, sample_flood_risk_data):
        """Test batch prediction exceeding maximum limit."""
        # Create 101 locations (over limit)
        locations = [sample_flood_risk_data["low_risk"].copy() for _ in range(101)]
        
        response = client.post(
            "/api/v1/predict/batch",
            json={"locations": locations}
        )
        
        assert response.status_code == 422
    
    def test_batch_empty_list(self, client):
        """Test batch prediction with empty locations list."""
        response = client.post(
            "/api/v1/predict/batch",
            json={"locations": []}
        )
        
        assert response.status_code == 422


class TestEvacuationZonesEndpoint:
    """Tests for POST /api/v1/predict/evacuation-zones endpoint."""
    
    def test_evacuation_zones_high_risk(self, client, sample_evacuation_data):
        """Test evacuation zone generation for high risk area."""
        response = client.post(
            "/api/v1/predict/evacuation-zones",
            json=sample_evacuation_data["high_risk"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "zones" in data
        assert "shelters" in data
        assert "location" in data
        assert "center_point" in data
        assert "risk_level" in data
        assert "flood_probability" in data
        assert "geojson" in data
        assert "generated_at" in data
        
        # Validate zones
        assert len(data["zones"]) == 3  # 3 radii specified
        for zone in data["zones"]:
            assert "zone_id" in zone
            assert "radius_meters" in zone
            assert "priority" in zone
            assert "estimated_affected" in zone or "estimated_population" in zone
            assert "evacuation_time_minutes" in zone
        
        # Validate GeoJSON
        assert data["geojson"]["type"] == "FeatureCollection"
        assert "features" in data["geojson"]
    
    def test_evacuation_zones_medium_risk(self, client, sample_evacuation_data):
        """Test evacuation zone generation for medium risk area."""
        response = client.post(
            "/api/v1/predict/evacuation-zones",
            json=sample_evacuation_data["medium_risk"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["zones"]) == 2  # 2 radii specified
        assert data["risk_level"] in ["very_low", "low", "moderate", "high", "extreme"]
    
    def test_evacuation_zones_without_shelters(self, client):
        """Test evacuation zones without shelter recommendations."""
        response = client.post(
            "/api/v1/predict/evacuation-zones",
            json={
                "latitude": 6.5244,
                "longitude": 3.3792,
                "flood_probability": 0.75,
                "risk_level": "high",
                "location_name": "Test Area",
                "population_density": 10000,
                "include_shelters": False,
                "zone_radii": [500, 1000]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["shelters"]) == 0  # No shelters included
    
    def test_evacuation_zones_custom_radii(self, client):
        """Test evacuation zones with custom radii."""
        response = client.post(
            "/api/v1/predict/evacuation-zones",
            json={
                "latitude": 6.5244,
                "longitude": 3.3792,
                "flood_probability": 0.65,
                "risk_level": "medium",
                "location_name": "Custom Area",
                "population_density": 8000,
                "include_shelters": True,
                "zone_radii": [250, 750, 1500, 3000]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["zones"]) == 4  # 4 custom radii
    
    def test_evacuation_zones_geojson_structure(self, client, sample_evacuation_data):
        """Test GeoJSON structure of evacuation zones."""
        response = client.post(
            "/api/v1/predict/evacuation-zones",
            json=sample_evacuation_data["high_risk"]
        )
        
        assert response.status_code == 200
        geojson = response.json()["geojson"]
        
        # Validate GeoJSON structure
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) > 0
        
        # Check first feature
        feature = geojson["features"][0]
        assert "type" in feature
        assert "geometry" in feature
        assert "properties" in feature
        assert feature["geometry"]["type"] == "Polygon"
        assert "coordinates" in feature["geometry"]


class TestHealthEndpoint:
    """Tests for GET /api/v1/models/health endpoint."""
    
    def test_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/api/v1/models/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "status" in data
        assert "models" in data
        assert "timestamp" in data
        
        # Validate models status
        assert "risk_scorer" in data["models"]
        assert "nowcaster" in data["models"]
        assert "anomaly_detector" in data["models"]
        
        for model_name, model_status in data["models"].items():
            assert "loaded" in model_status
            assert isinstance(model_status["loaded"], bool)
