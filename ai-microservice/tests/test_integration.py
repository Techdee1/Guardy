"""Integration tests for end-to-end workflows."""
import pytest
from fastapi.testclient import TestClient
import time


class TestFloodMonitoringWorkflow:
    """Integration tests for complete flood monitoring workflow."""
    
    def test_flood_detection_and_evacuation_workflow(self, client, sample_flood_risk_data, sample_evacuation_data):
        """Test complete workflow from risk detection to evacuation planning."""
        # Step 1: Assess flood risk
        risk_response = client.post(
            "/api/v1/predict/flood-risk",
            json=sample_flood_risk_data["high_risk"]
        )
        assert risk_response.status_code == 200
        risk_data = risk_response.json()
        
        # Verify high risk detected
        assert risk_data["risk_level"] in ["high", "critical"]
        flood_probability = risk_data["risk_score"]
        
        # Step 2: Generate evacuation zones based on risk
        evacuation_response = client.post(
            "/api/v1/predict/evacuation-zones",
            json={
                **sample_evacuation_data["high_risk"],
                "flood_probability": flood_probability
            }
        )
        assert evacuation_response.status_code == 200
        evacuation_data = evacuation_response.json()
        
        # Verify evacuation zones created
        assert len(evacuation_data["zones"]) > 0
        assert evacuation_data["evacuation_priority"] in ["immediate", "high"]
        assert evacuation_data["total_affected_population"] > 0
        
        # Step 3: Check model health after operations
        health_response = client.get("/api/v1/models/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        
        # Verify models are still operational
        assert health_data["status"] == "healthy"
        assert all(model["loaded"] for model in health_data["models"].values())
    
    def test_multi_location_monitoring_workflow(self, client, sample_flood_risk_data):
        """Test monitoring multiple locations simultaneously."""
        # Step 1: Batch predict for multiple locations
        locations = [
            sample_flood_risk_data["low_risk"],
            sample_flood_risk_data["medium_risk"],
            sample_flood_risk_data["high_risk"]
        ]
        
        batch_response = client.post(
            "/api/v1/predict/batch",
            json={"locations": locations}
        )
        assert batch_response.status_code == 200
        batch_data = batch_response.json()
        
        # Verify all locations processed
        assert batch_data["total_processed"] == 3
        assert len(batch_data["predictions"]) == 3
        
        # Step 2: For each high-risk location, get evacuation zones
        high_risk_locations = [
            pred for pred in batch_data["predictions"]
            if pred["risk_level"] in ["high", "critical"]
        ]
        
        for location in high_risk_locations:
            evac_response = client.post(
                "/api/v1/predict/evacuation-zones",
                json={
                    "latitude": locations[location["location_index"]]["latitude"],
                    "longitude": locations[location["location_index"]]["longitude"],
                    "flood_probability": location["risk_score"],
                    "risk_level": location["risk_level"],
                    "location_name": f"Location_{location['location_index']}",
                    "population_density": 10000,
                    "include_shelters": True,
                    "zone_radii": [500, 1000]
                }
            )
            assert evac_response.status_code == 200


class TestTimeSeriesPredictionWorkflow:
    """Integration tests for time-series prediction workflow."""
    
    def test_nowcast_to_risk_assessment_workflow(self, client, sample_nowcast_data, sample_flood_risk_data):
        """Test workflow from nowcast to risk assessment."""
        # Step 1: Get nowcast predictions
        nowcast_response = client.post(
            "/api/v1/predict/nowcast",
            json={
                **sample_nowcast_data["location"],
                "historical_data": sample_nowcast_data["rising"],
                "forecast_horizons": [1, 6, 12, 24]
            }
        )
        assert nowcast_response.status_code == 200
        nowcast_data = nowcast_response.json()
        
        # Step 2: For each forecast horizon, assess risk
        for prediction in nowcast_data["predictions"]:
            predicted_level = prediction["predicted_level"]
            
            # Assess risk with predicted water level
            risk_response = client.post(
                "/api/v1/predict/flood-risk",
                json={
                    **sample_flood_risk_data["medium_risk"],
                    "water_level_cm": predicted_level
                }
            )
            assert risk_response.status_code == 200
            risk_data = risk_response.json()
            
            # Verify risk assessment completed
            assert "risk_score" in risk_data
            assert "risk_level" in risk_data
    
    def test_continuous_monitoring_simulation(self, client, sample_flood_risk_data):
        """Simulate continuous monitoring over time."""
        # Simulate 5 consecutive readings
        readings = []
        
        for i in range(5):
            # Simulate increasing water levels
            data = sample_flood_risk_data["low_risk"].copy()
            data["water_level_cm"] = 15.0 + (i * 10.0)  # Increasing levels
            data["rainfall_mm"] = 10.0 + (i * 15.0)
            
            response = client.post(
                "/api/v1/predict/flood-risk",
                json=data
            )
            assert response.status_code == 200
            
            result = response.json()
            readings.append({
                "iteration": i,
                "water_level": data["water_level_cm"],
                "risk_score": result["risk_score"],
                "risk_level": result["risk_level"]
            })
        
        # Verify risk escalation over time
        risk_scores = [r["risk_score"] for r in readings]
        # Risk should generally increase (allowing some variability)
        assert risk_scores[-1] > risk_scores[0]


class TestAnomalyDetectionWorkflow:
    """Integration tests for sensor anomaly detection workflow."""
    
    def test_sensor_validation_workflow(self, client, sample_anomaly_data, sample_flood_risk_data):
        """Test workflow for validating sensor readings before risk assessment."""
        # Step 1: Check sensor readings for anomalies
        anomaly_response = client.post(
            "/api/v1/predict/anomaly",
            json=sample_anomaly_data["normal"]
        )
        assert anomaly_response.status_code == 200
        anomaly_data = anomaly_response.json()
        
        # Step 2: If no anomaly, proceed with risk assessment
        if not anomaly_data["is_anomaly"]:
            # Extract latest sensor reading
            latest_reading = sample_anomaly_data["normal"]["readings"][-1]
            
            # Use sensor data for risk prediction
            risk_response = client.post(
                "/api/v1/predict/flood-risk",
                json={
                    **sample_flood_risk_data["low_risk"],
                    "water_level_cm": latest_reading["value"]
                }
            )
            assert risk_response.status_code == 200
        else:
            # If anomaly detected, don't trust the reading
            pass
    
    def test_multi_sensor_anomaly_detection(self, client, sample_anomaly_data):
        """Test anomaly detection across multiple sensors."""
        sensors = ["normal", "anomalous"]
        results = []
        
        for sensor_type in sensors:
            response = client.post(
                "/api/v1/predict/anomaly",
                json=sample_anomaly_data[sensor_type]
            )
            assert response.status_code == 200
            
            data = response.json()
            results.append({
                "sensor_id": sample_anomaly_data[sensor_type]["sensor_id"],
                "is_anomaly": data["is_anomaly"],
                "anomaly_score": data["anomaly_score"]
            })
        
        # Verify detection completed for all sensors
        assert len(results) == 2


class TestModelReliabilityWorkflow:
    """Integration tests for model reliability and operations."""
    
    def test_prediction_after_model_reload(self, client, sample_flood_risk_data):
        """Test that predictions work correctly after model reload."""
        # Step 1: Make initial prediction
        initial_response = client.post(
            "/api/v1/predict/flood-risk",
            json=sample_flood_risk_data["medium_risk"]
        )
        assert initial_response.status_code == 200
        initial_data = initial_response.json()
        
        # Step 2: Reload model
        reload_response = client.post("/api/v1/models/risk_scorer/reload")
        assert reload_response.status_code == 200
        
        # Step 3: Make prediction again with same data
        after_reload_response = client.post(
            "/api/v1/predict/flood-risk",
            json=sample_flood_risk_data["medium_risk"]
        )
        assert after_reload_response.status_code == 200
        after_reload_data = after_reload_response.json()
        
        # Results should be similar (within reasonable range)
        assert after_reload_data["risk_level"] == initial_data["risk_level"]
        assert abs(after_reload_data["risk_score"] - initial_data["risk_score"]) < 0.2
    
    def test_model_health_monitoring(self, client, sample_flood_risk_data):
        """Test continuous health monitoring during predictions."""
        # Check initial health
        health_before = client.get("/api/v1/models/status")
        assert health_before.status_code == 200
        
        # Make multiple predictions
        for _ in range(5):
            pred_response = client.post(
                "/api/v1/predict/flood-risk",
                json=sample_flood_risk_data["low_risk"]
            )
            assert pred_response.status_code == 200
        
        # Check health after predictions
        health_after = client.get("/api/v1/models/status")
        assert health_after.status_code == 200
        
        # System should still be operational
        health_data = health_after.json()
        assert health_data["system_status"] == "operational"
        assert health_data["all_models_loaded"] is True
    
    def test_error_recovery_workflow(self, client):
        """Test system behavior when handling errors."""
        # Try to reload non-existent model (should fail gracefully)
        reload_response = client.post("/api/v1/models/invalid_model/reload")
        assert reload_response.status_code == 404
        
        # Verify system still operational
        health_response = client.get("/api/v1/models/status")
        assert health_response.status_code == 200
        
        # Verify valid models still work
        metadata_response = client.get("/api/v1/models/risk_scorer/metadata")
        assert metadata_response.status_code == 200


class TestPerformanceWorkflow:
    """Integration tests for performance and scalability."""
    
    def test_concurrent_predictions(self, client, sample_flood_risk_data):
        """Test handling multiple concurrent predictions."""
        # Make 10 predictions rapidly
        responses = []
        
        for i in range(10):
            data = sample_flood_risk_data["low_risk"].copy()
            data["latitude"] += (i * 0.01)  # Slightly different locations
            
            response = client.post(
                "/api/v1/predict/flood-risk",
                json=data
            )
            responses.append(response)
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        
        # Verify predictions are valid
        for response in responses:
            data = response.json()
            assert "risk_score" in data
            assert "risk_level" in data
    
    def test_large_batch_processing(self, client, sample_flood_risk_data):
        """Test processing maximum batch size."""
        # Create 50 locations
        locations = []
        for i in range(50):
            location = sample_flood_risk_data["low_risk"].copy()
            location["latitude"] += (i * 0.01)
            location["longitude"] += (i * 0.01)
            locations.append(location)
        
        # Process batch
        batch_response = client.post(
            "/api/v1/predict/batch",
            json={"locations": locations}
        )
        
        assert batch_response.status_code == 200
        batch_data = batch_response.json()
        
        # All should be processed
        assert batch_data["total_processed"] == 50
        assert len(batch_data["predictions"]) == 50


class TestDataValidationWorkflow:
    """Integration tests for data validation and error handling."""
    
    def test_invalid_data_handling(self, client):
        """Test system handles invalid data gracefully."""
        # Test 1: Invalid latitude
        response1 = client.post(
            "/api/v1/predict/flood-risk",
            json={
                "latitude": 999.0,
                "longitude": 3.3792,
                "rainfall_mm": 10.0,
                "water_level_cm": 15.0
            }
        )
        assert response1.status_code == 422
        
        # Test 2: Missing required field
        response2 = client.post(
            "/api/v1/predict/flood-risk",
            json={
                "latitude": 6.5244,
                "longitude": 3.3792
                # Missing rainfall_mm and water_level_cm
            }
        )
        assert response2.status_code == 422
        
        # Test 3: Negative values where not allowed
        response3 = client.post(
            "/api/v1/predict/flood-risk",
            json={
                "latitude": 6.5244,
                "longitude": 3.3792,
                "rainfall_mm": -10.0,  # Negative
                "water_level_cm": 15.0
            }
        )
        assert response3.status_code == 422
        
        # System should still be healthy after errors
        health_response = client.get("/api/v1/models/health")
        assert health_response.status_code == 200
