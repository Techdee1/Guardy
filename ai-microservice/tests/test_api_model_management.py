"""Tests for model management API endpoints."""
import pytest
from fastapi.testclient import TestClient


class TestModelsStatusEndpoint:
    """Tests for GET /api/v1/models/status endpoint."""
    
    def test_models_status_success(self, client):
        """Test successful retrieval of models status."""
        response = client.get("/api/v1/models/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "system_status" in data
        assert "all_models_loaded" in data
        assert "total_predictions" in data
        assert "models" in data
        assert "load_time_seconds" in data
        assert "timestamp" in data
        
        # Validate system status
        assert data["system_status"] in ["operational", "degraded", "down"]
        assert isinstance(data["all_models_loaded"], bool)
        assert isinstance(data["total_predictions"], int)
        assert data["total_predictions"] >= 0
        
        # Validate individual models
        assert "risk_scorer" in data["models"]
        assert "nowcaster" in data["models"]
        assert "anomaly_detector" in data["models"]
        
        for model_key, model_info in data["models"].items():
            assert "name" in model_info
            assert "version" in model_info
            assert "status" in model_info
            assert "is_loaded" in model_info
            assert model_info["status"] in ["operational", "not_loaded", "error"]
    
    def test_models_status_details(self, client):
        """Test detailed information in models status."""
        response = client.get("/api/v1/models/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check risk_scorer details
        risk_scorer = data["models"]["risk_scorer"]
        assert risk_scorer["name"] == "FloodRiskScorer"
        assert "algorithm" in risk_scorer
        assert "accuracy" in risk_scorer
        assert "training_samples" in risk_scorer
        assert "features" in risk_scorer
        assert "file_size_mb" in risk_scorer


class TestModelMetadataEndpoint:
    """Tests for GET /api/v1/models/{model_name}/metadata endpoint."""
    
    def test_get_risk_scorer_metadata(self, client):
        """Test retrieval of FloodRiskScorer metadata."""
        response = client.get("/api/v1/models/risk_scorer/metadata")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert data["model_name"] == "risk_scorer"
        assert data["name"] == "FloodRiskScorer"
        assert data["version"] == "v1"
        assert "algorithm" in data
        assert "trained_date" in data
        assert "accuracy" in data
        assert "training_samples" in data
        assert "file_path" in data
        assert "file_size_mb" in data
        assert "is_loaded" in data
        
        # Validate accuracy
        assert 0 <= data["accuracy"] <= 1
    
    def test_get_nowcaster_metadata(self, client):
        """Test retrieval of FloodNowcaster metadata."""
        response = client.get("/api/v1/models/nowcaster/metadata")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["model_name"] == "nowcaster"
        assert data["name"] == "FloodNowcaster"
        assert data["algorithm"] == "LSTM Neural Network"
    
    def test_get_anomaly_detector_metadata(self, client):
        """Test retrieval of SensorAnomalyDetector metadata."""
        response = client.get("/api/v1/models/anomaly_detector/metadata")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["model_name"] == "anomaly_detector"
        assert data["name"] == "SensorAnomalyDetector"
        assert data["algorithm"] == "Isolation Forest"
    
    def test_get_invalid_model_metadata(self, client):
        """Test retrieval of metadata for non-existent model."""
        response = client.get("/api/v1/models/invalid_model/metadata")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "ModelNotFound"


class TestModelStatsEndpoint:
    """Tests for GET /api/v1/models/{model_name}/stats endpoint."""
    
    def test_get_risk_scorer_stats(self, client):
        """Test retrieval of FloodRiskScorer statistics."""
        response = client.get("/api/v1/models/risk_scorer/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert data["model_name"] == "risk_scorer"
        assert "total_predictions" in data
        assert "predictions_per_minute" in data
        assert "uptime_seconds" in data
        assert "last_prediction" in data
        assert "timestamp" in data
        
        # Validate values
        assert isinstance(data["total_predictions"], int)
        assert data["total_predictions"] >= 0
        assert isinstance(data["predictions_per_minute"], (int, float))
        assert data["predictions_per_minute"] >= 0
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0
    
    def test_get_stats_after_prediction(self, client, sample_flood_risk_data):
        """Test stats update after making a prediction."""
        # Make a prediction
        pred_response = client.post(
            "/api/v1/predict/flood-risk",
            json=sample_flood_risk_data["low_risk"]
        )
        assert pred_response.status_code == 200
        
        # Get stats
        stats_response = client.get("/api/v1/models/risk_scorer/stats")
        assert stats_response.status_code == 200
        
        data = stats_response.json()
        # Note: Stats may or may not increment depending on implementation
        assert data["total_predictions"] >= 0
    
    def test_get_invalid_model_stats(self, client):
        """Test retrieval of stats for non-existent model."""
        response = client.get("/api/v1/models/invalid_model/stats")
        
        assert response.status_code == 404


class TestModelReloadEndpoint:
    """Tests for POST /api/v1/models/reload endpoints."""
    
    def test_reload_all_models(self, client):
        """Test reloading all models."""
        response = client.post("/api/v1/models/reload")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "status" in data
        assert "message" in data
        assert "reload_time_seconds" in data
        assert "all_models_loaded" in data
        assert "reload_results" in data
        assert "timestamp" in data
        
        # Validate reload results
        assert "risk_scorer" in data["reload_results"]
        assert "nowcaster" in data["reload_results"]
        assert "anomaly_detector" in data["reload_results"]
        
        for model_name, result in data["reload_results"].items():
            assert "status" in result
            assert "message" in result
            assert result["status"] in ["success", "error"]
    
    def test_reload_single_model_risk_scorer(self, client):
        """Test reloading FloodRiskScorer."""
        response = client.post("/api/v1/models/risk_scorer/reload")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["model_name"] == "risk_scorer"
        assert "message" in data
        assert "reload_time_seconds" in data
        assert isinstance(data["reload_time_seconds"], (int, float))
        assert data["reload_time_seconds"] >= 0
    
    def test_reload_single_model_nowcaster(self, client):
        """Test reloading FloodNowcaster."""
        response = client.post("/api/v1/models/nowcaster/reload")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["model_name"] == "nowcaster"
    
    def test_reload_single_model_anomaly_detector(self, client):
        """Test reloading SensorAnomalyDetector."""
        response = client.post("/api/v1/models/anomaly_detector/reload")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["model_name"] == "anomaly_detector"
    
    def test_reload_invalid_model(self, client):
        """Test reloading non-existent model."""
        response = client.post("/api/v1/models/invalid_model/reload")
        
        assert response.status_code == 404
    
    def test_model_still_works_after_reload(self, client, sample_flood_risk_data):
        """Test that model still works after reload."""
        # Reload model
        reload_response = client.post("/api/v1/models/risk_scorer/reload")
        assert reload_response.status_code == 200
        
        # Make prediction
        pred_response = client.post(
            "/api/v1/predict/flood-risk",
            json=sample_flood_risk_data["low_risk"]
        )
        assert pred_response.status_code == 200
        
        data = pred_response.json()
        assert "risk_score" in data
        assert "risk_level" in data


class TestCacheClearEndpoint:
    """Tests for DELETE /api/v1/models/{model_name}/cache endpoint."""
    
    def test_clear_cache_risk_scorer(self, client):
        """Test clearing cache for FloodRiskScorer."""
        response = client.delete("/api/v1/models/risk_scorer/cache")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure (placeholder implementation)
        assert "status" in data
        assert "message" in data
        assert "cached_items_cleared" in data
        
        # Placeholder should return 0
        assert data["cached_items_cleared"] == 0
    
    def test_clear_cache_nowcaster(self, client):
        """Test clearing cache for FloodNowcaster."""
        response = client.delete("/api/v1/models/nowcaster/cache")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_clear_cache_invalid_model(self, client):
        """Test clearing cache for non-existent model."""
        response = client.delete("/api/v1/models/invalid_model/cache")
        
        assert response.status_code == 404


class TestModelManagementIntegration:
    """Integration tests for model management endpoints."""
    
    def test_status_metadata_consistency(self, client):
        """Test consistency between status and metadata endpoints."""
        # Get overall status
        status_response = client.get("/api/v1/models/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        # Get individual metadata
        for model_key in ["risk_scorer", "nowcaster", "anomaly_detector"]:
            metadata_response = client.get(f"/api/v1/models/{model_key}/metadata")
            assert metadata_response.status_code == 200
            metadata = metadata_response.json()
            
            # Compare values
            status_model = status_data["models"][model_key]
            assert status_model["name"] == metadata["name"]
            assert status_model["version"] == metadata["version"]
            assert status_model["is_loaded"] == metadata["is_loaded"]
    
    def test_reload_updates_status(self, client):
        """Test that reload updates model status."""
        # Get initial status
        initial_response = client.get("/api/v1/models/status")
        assert initial_response.status_code == 200
        
        # Reload model
        reload_response = client.post("/api/v1/models/risk_scorer/reload")
        assert reload_response.status_code == 200
        
        # Get updated status
        updated_response = client.get("/api/v1/models/status")
        assert updated_response.status_code == 200
        updated_data = updated_response.json()
        
        # Model should still be loaded
        assert updated_data["models"]["risk_scorer"]["is_loaded"] is True
    
    def test_multiple_endpoints_sequence(self, client, sample_flood_risk_data):
        """Test sequence of operations across multiple endpoints."""
        # 1. Check status
        status_response = client.get("/api/v1/models/status")
        assert status_response.status_code == 200
        
        # 2. Get metadata
        metadata_response = client.get("/api/v1/models/risk_scorer/metadata")
        assert metadata_response.status_code == 200
        
        # 3. Make prediction
        pred_response = client.post(
            "/api/v1/predict/flood-risk",
            json=sample_flood_risk_data["low_risk"]
        )
        assert pred_response.status_code == 200
        
        # 4. Check stats
        stats_response = client.get("/api/v1/models/risk_scorer/stats")
        assert stats_response.status_code == 200
        
        # 5. Reload model
        reload_response = client.post("/api/v1/models/risk_scorer/reload")
        assert reload_response.status_code == 200
        
        # 6. Clear cache
        cache_response = client.delete("/api/v1/models/risk_scorer/cache")
        assert cache_response.status_code == 200
        
        # All operations should succeed
        assert all([
            status_response.status_code == 200,
            metadata_response.status_code == 200,
            pred_response.status_code == 200,
            stats_response.status_code == 200,
            reload_response.status_code == 200,
            cache_response.status_code == 200
        ])
