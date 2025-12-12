"""
Locust load testing script for Guardy AI Microservice.

This script simulates realistic user behavior to test API performance,
identify bottlenecks, and measure system capacity under load.

Usage:
    # Run locally with 100 users, spawn rate 10/sec, 5 minute test
    locust -f tests/load_test.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m

    # Run with web UI
    locust -f tests/load_test.py --host=http://localhost:8000

    # Run headless with specific configuration
    locust -f tests/load_test.py --host=http://localhost:8000 --users 500 --spawn-rate 50 --run-time 10m --headless
"""

from locust import HttpUser, task, between, SequentialTaskSet
import random
import json
from datetime import datetime, timedelta


class FloodPredictionTasks(SequentialTaskSet):
    """Sequential tasks simulating typical user workflow."""
    
    @task(1)
    def health_check(self):
        """Check API health (lowest priority)."""
        self.client.get("/api/v1/models/health", name="/api/v1/models/health")
    
    @task(10)
    def predict_flood_risk(self):
        """Predict flood risk for single location (high priority)."""
        payload = {
            "latitude": round(random.uniform(8.0, 10.0), 4),
            "longitude": round(random.uniform(7.0, 9.0), 4),
            "rainfall_mm": round(random.uniform(0, 200), 2),
            "temperature": round(random.uniform(20, 35), 2),
            "humidity": round(random.uniform(40, 100), 2),
            "date": random.randint(1, 28),
            "month": random.randint(1, 12),
            "day_of_year": random.randint(1, 365)
        }
        
        with self.client.post(
            "/api/v1/predict/flood-risk",
            json=payload,
            catch_response=True,
            name="/api/v1/predict/flood-risk"
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if "risk_level" in result:
                    response.success()
                else:
                    response.failure("Missing risk_level in response")
            elif response.status_code == 503:
                response.failure("Models not loaded (503)")
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
    
    @task(5)
    def predict_nowcast(self):
        """Generate nowcast predictions (medium priority)."""
        # Generate time series data (7 readings minimum)
        time_series = []
        base_time = datetime.utcnow()
        
        for i in range(10):
            reading = {
                "timestamp": (base_time - timedelta(hours=10-i)).isoformat() + "Z",
                "rainfall_mm": round(random.uniform(5, 150), 2),
                "temperature": round(random.uniform(22, 32), 2),
                "humidity": round(random.uniform(50, 95), 2)
            }
            time_series.append(reading)
        
        payload = {
            "latitude": round(random.uniform(8.0, 10.0), 4),
            "longitude": round(random.uniform(7.0, 9.0), 4),
            "historical_sequence": time_series,
            "forecast_hours": random.choice([6, 12, 24, 48])
        }
        
        with self.client.post(
            "/api/v1/predict/nowcast",
            json=payload,
            catch_response=True,
            name="/api/v1/predict/nowcast"
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if "predictions" in result and len(result["predictions"]) > 0:
                    response.success()
                else:
                    response.failure("Empty predictions")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(3)
    def detect_anomaly(self):
        """Detect sensor anomalies (medium priority)."""
        # Generate mostly normal readings with occasional anomalies
        is_anomaly = random.random() < 0.1  # 10% anomalies
        
        if is_anomaly:
            # Generate anomalous reading
            payload = {
                "device_id": f"SENSOR-{random.randint(1, 100):03d}",
                "water_level_cm": round(random.uniform(300, 500), 2),  # Extreme
                "rainfall_mm": round(random.uniform(200, 400), 2),  # Extreme
                "temperature": round(random.uniform(-10, 50), 2),  # Extreme
                "humidity": round(random.uniform(95, 100), 2),  # Very high
                "battery_voltage": round(random.uniform(2.0, 2.5), 2),  # Low battery
                "signal_strength": round(random.uniform(-110, -95), 2)  # Weak signal
            }
        else:
            # Generate normal reading
            payload = {
                "device_id": f"SENSOR-{random.randint(1, 100):03d}",
                "water_level_cm": round(random.uniform(50, 200), 2),
                "rainfall_mm": round(random.uniform(0, 50), 2),
                "temperature": round(random.uniform(20, 35), 2),
                "humidity": round(random.uniform(50, 85), 2),
                "battery_voltage": round(random.uniform(3.5, 4.2), 2),
                "signal_strength": round(random.uniform(-85, -50), 2)
            }
        
        self.client.post(
            "/api/v1/predict/anomaly",
            json=payload,
            name="/api/v1/predict/anomaly"
        )
    
    @task(4)
    def batch_prediction(self):
        """Process batch predictions (medium-high priority)."""
        # Generate 5-20 locations
        num_locations = random.randint(5, 20)
        locations = []
        
        for _ in range(num_locations):
            location = {
                "location_id": f"LOC-{random.randint(1, 1000):04d}",
                "latitude": round(random.uniform(8.0, 10.0), 4),
                "longitude": round(random.uniform(7.0, 9.0), 4),
                "rainfall_mm": round(random.uniform(0, 200), 2),
                "temperature": round(random.uniform(20, 35), 2),
                "humidity": round(random.uniform(40, 100), 2),
                "soil_moisture": round(random.uniform(20, 90), 2),
                "river_level_m": round(random.uniform(1, 15), 2)
            }
            locations.append(location)
        
        payload = {"locations": locations}
        
        with self.client.post(
            "/api/v1/predict/batch",
            json=payload,
            catch_response=True,
            name="/api/v1/predict/batch"
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if result.get("total_locations") == num_locations:
                    response.success()
                else:
                    response.failure(f"Expected {num_locations} results, got {result.get('total_locations')}")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(2)
    def get_model_status(self):
        """Check model status (low priority)."""
        self.client.get("/api/v1/models/status", name="/api/v1/models/status")
    
    @task(1)
    def get_performance_metrics(self):
        """Get performance metrics (lowest priority)."""
        self.client.get("/api/v1/metrics/performance", name="/api/v1/metrics/performance")


class FloodMonitoringUser(HttpUser):
    """Simulated user performing flood monitoring tasks."""
    
    # Wait 1-3 seconds between tasks (realistic user behavior)
    wait_time = between(1, 3)
    
    # Use sequential task set
    tasks = [FloodPredictionTasks]


class HeavyLoadUser(HttpUser):
    """Simulated user generating heavy load (batch processing)."""
    
    wait_time = between(0.5, 1.5)
    
    @task(5)
    def batch_prediction_large(self):
        """Large batch prediction (50-100 locations)."""
        num_locations = random.randint(50, 100)
        locations = []
        
        for _ in range(num_locations):
            location = {
                "location_id": f"BATCH-{random.randint(1, 10000):05d}",
                "latitude": round(random.uniform(8.0, 10.0), 4),
                "longitude": round(random.uniform(7.0, 9.0), 4),
                "rainfall_mm": round(random.uniform(0, 200), 2),
                "temperature": round(random.uniform(20, 35), 2),
                "humidity": round(random.uniform(40, 100), 2),
                "soil_moisture": round(random.uniform(20, 90), 2),
                "river_level_m": round(random.uniform(1, 15), 2)
            }
            locations.append(location)
        
        self.client.post(
            "/api/v1/predict/batch",
            json={"locations": locations},
            name="/api/v1/predict/batch (large)"
        )
    
    @task(1)
    def flood_risk_burst(self):
        """Burst of flood risk predictions."""
        for _ in range(10):
            payload = {
                "latitude": round(random.uniform(8.0, 10.0), 4),
                "longitude": round(random.uniform(7.0, 9.0), 4),
                "rainfall_mm": round(random.uniform(0, 200), 2),
                "temperature": round(random.uniform(20, 35), 2),
                "humidity": round(random.uniform(40, 100), 2),
                "date": random.randint(1, 28),
                "month": random.randint(1, 12),
                "day_of_year": random.randint(1, 365)
            }
            self.client.post("/api/v1/predict/flood-risk", json=payload, name="/api/v1/predict/flood-risk (burst)")


# Performance test configurations
"""
# Test Scenarios:

1. Normal Load Test:
   locust -f tests/load_test.py --host=http://localhost:8000 \\
          --users 50 --spawn-rate 10 --run-time 5m

2. Stress Test:
   locust -f tests/load_test.py --host=http://localhost:8000 \\
          --users 200 --spawn-rate 20 --run-time 10m

3. Spike Test:
   locust -f tests/load_test.py --host=http://localhost:8000 \\
          --users 500 --spawn-rate 100 --run-time 2m

4. Soak Test (long duration):
   locust -f tests/load_test.py --host=http://localhost:8000 \\
          --users 100 --spawn-rate 10 --run-time 1h

5. Heavy Load Test (large batches):
   locust -f tests/load_test.py --host=http://localhost:8000 \\
          --users 100 --spawn-rate 20 --run-time 10m \\
          --user-class HeavyLoadUser

Expected Results (with caching):
- Average response time: < 50ms
- P95 response time: < 150ms
- P99 response time: < 300ms
- Cache hit rate: > 60%
- Success rate: > 99.5%
- Throughput: > 500 requests/sec
"""
