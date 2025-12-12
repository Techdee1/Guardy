"""Pytest configuration file with fixtures for testing."""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import numpy as np
from datetime import datetime, timezone, timedelta

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_flood_risk_data():
    """Sample data for flood risk prediction tests."""
    return {
        "low_risk": {
            "latitude": 6.5244,
            "longitude": 3.3792,
            "location_name": "Lagos Test Low",
            "rainfall_mm": 10.0,
            "temperature": 28.5,
            "humidity": 65
        },
        "medium_risk": {
            "latitude": 6.5244,
            "longitude": 3.3792,
            "location_name": "Lagos Test Medium",
            "rainfall_mm": 60.0,
            "temperature": 29.0,
            "humidity": 80
        },
        "high_risk": {
            "latitude": 6.5244,
            "longitude": 3.3792,
            "location_name": "Lagos Test High",
            "rainfall_mm": 120.0,
            "temperature": 30.0,
            "humidity": 95
        }
    }


@pytest.fixture
def sample_nowcast_data():
    """Sample data for nowcast prediction tests."""
    base_time = datetime.now(timezone.utc)
    
    # Rising trend (increasing water levels)
    rising_sequence = [
        {
            "timestamp": (base_time - timedelta(minutes=60 - i*10)).isoformat(),
            "rainfall_mm": 5.0 + i * 2.0,
            "water_level_cm": 20.0 + i * 5.0,
            "temperature_c": 28.0 + i * 0.2
        }
        for i in range(7)
    ]
    
    # Stable trend (steady water levels)
    stable_sequence = [
        {
            "timestamp": (base_time - timedelta(minutes=60 - i*10)).isoformat(),
            "rainfall_mm": 2.0,
            "water_level_cm": 25.0 + np.random.uniform(-1, 1),
            "temperature_c": 28.5
        }
        for i in range(7)
    ]
    
    return {
        "rising": rising_sequence,
        "stable": stable_sequence,
        "location": {"latitude": 6.5244, "longitude": 3.3792}
    }


@pytest.fixture
def sample_anomaly_data():
    """Sample data for anomaly detection tests."""
    base_time = datetime.now(timezone.utc)
    
    return {
        "normal": {
            "sensor_id": "SENSOR_001",
            "readings": [
                {
                    "timestamp": (base_time - timedelta(minutes=30 - i*5)).isoformat(),
                    "value": 25.0 + np.random.uniform(-2, 2),
                    "battery_level": 85.0,
                    "signal_strength": -65
                }
                for i in range(7)
            ]
        },
        "anomalous": {
            "sensor_id": "SENSOR_002",
            "readings": [
                {
                    "timestamp": (base_time - timedelta(minutes=30 - i*5)).isoformat(),
                    "value": 25.0 if i < 5 else 150.0,  # Sudden spike
                    "battery_level": 85.0 if i < 6 else 15.0,  # Battery drop
                    "signal_strength": -65
                }
                for i in range(7)
            ]
        }
    }


@pytest.fixture
def sample_evacuation_data():
    """Sample data for evacuation zone prediction tests."""
    return {
        "high_risk": {
            "latitude": 6.5244,
            "longitude": 3.3792,
            "flood_probability": 0.85,
            "risk_level": "high",
            "location_name": "Lagos Island",
            "population_density": 12500,
            "include_shelters": True,
            "zone_radii": [500, 1000, 2000]
        },
        "medium_risk": {
            "latitude": 6.4474,
            "longitude": 3.4706,
            "flood_probability": 0.55,
            "risk_level": "medium",
            "location_name": "Ikeja",
            "population_density": 8000,
            "include_shelters": True,
            "zone_radii": [500, 1000]
        }
    }


@pytest.fixture
def mock_trained_models(monkeypatch):
    """Mock trained models for testing."""
    from app.ml import FloodRiskScorer, FloodNowcaster, SensorAnomalyDetector
    
    # Mock the load methods to avoid loading actual model files
    def mock_load_risk_scorer(self, model_path):
        self.is_trained = True
        return True
    
    def mock_load_nowcaster(self, model_path):
        self.is_trained = True
        return True
    
    def mock_load_anomaly(self, model_path):
        self.is_fitted = True
        return True
    
    monkeypatch.setattr(FloodRiskScorer, "load", mock_load_risk_scorer)
    monkeypatch.setattr(FloodNowcaster, "load", mock_load_nowcaster)
    monkeypatch.setattr(SensorAnomalyDetector, "load", mock_load_anomaly)
