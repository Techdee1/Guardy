"""Tests for ML model stubs."""
import pytest
from datetime import datetime, timezone, timedelta
from app.ml import FloodRiskScorer, FloodNowcaster, SensorAnomalyDetector


class TestFloodRiskScorer:
    """Tests for FloodRiskScorer stub."""
    
    def test_initialization(self):
        """Test model initialization."""
        scorer = FloodRiskScorer()
        assert scorer is not None
        assert scorer.is_trained == False
    
    def test_predict_low_risk(self):
        """Test prediction with low risk inputs."""
        scorer = FloodRiskScorer()
        result = scorer.predict(
            latitude=6.5244,
            longitude=3.3792,
            water_level_cm=15.0,
            rainfall_mm=10.0,
        )
        
        assert "risk_score" in result
        assert "risk_level" in result
        assert "confidence" in result
        assert "factors" in result
        assert result["risk_level"] == "low"
        assert 0 <= result["risk_score"] <= 1
        assert 0 <= result["confidence"] <= 1
    
    def test_predict_medium_risk(self):
        """Test prediction with medium risk inputs."""
        scorer = FloodRiskScorer()
        result = scorer.predict(
            latitude=6.5244,
            longitude=3.3792,
            water_level_cm=35.0,
            rainfall_mm=60.0,
        )
        
        assert result["risk_level"] == "medium"
        assert result["risk_score"] >= 0.4
    
    def test_predict_high_risk(self):
        """Test prediction with high risk inputs."""
        scorer = FloodRiskScorer()
        result = scorer.predict(
            latitude=6.5244,
            longitude=3.3792,
            water_level_cm=55.0,
            rainfall_mm=120.0,
            humidity=90,
        )
        
        assert result["risk_level"] == "high"
        assert result["risk_score"] >= 0.7
        assert len(result["factors"]) > 0
    
    def test_predict_batch(self):
        """Test batch prediction."""
        scorer = FloodRiskScorer()
        features = [
            {"latitude": 6.5244, "longitude": 3.3792, "water_level_cm": 15.0},
            {"latitude": 6.4474, "longitude": 3.4706, "water_level_cm": 55.0, "rainfall_mm": 120.0},
        ]
        
        results = scorer.predict_batch(features)
        assert len(results) == 2
        assert results[0]["risk_level"] == "low"
        assert results[1]["risk_level"] == "high"  # Water level 55cm + heavy rainfall should trigger high risk


class TestFloodNowcaster:
    """Tests for FloodNowcaster stub."""
    
    def test_initialization(self):
        """Test model initialization."""
        nowcaster = FloodNowcaster()
        assert nowcaster is not None
        assert nowcaster.sequence_length == 10
    
    def test_predict_insufficient_data(self):
        """Test prediction with insufficient data."""
        nowcaster = FloodNowcaster()
        result = nowcaster.predict(
            device_id="ESP32_001",
            historical_readings=[],
            forecast_minutes=30,
        )
        
        assert "error" in result
        assert result["confidence"] == 0.0
    
    def test_predict_rising_trend(self):
        """Test prediction with rising water level trend."""
        nowcaster = FloodNowcaster()
        base_time = datetime.now(timezone.utc)
        
        readings = [
            {
                "water_level_cm": 20.0,
                "timestamp": (base_time - timedelta(minutes=10)).isoformat(),
            },
            {
                "water_level_cm": 25.0,
                "timestamp": (base_time - timedelta(minutes=5)).isoformat(),
            },
            {
                "water_level_cm": 30.0,
                "timestamp": base_time.isoformat(),
            },
        ]
        
        result = nowcaster.predict(
            device_id="ESP32_001",
            historical_readings=readings,
            forecast_minutes=30,
        )
        
        assert result["device_id"] == "ESP32_001"
        assert result["trend"] == "rising"
        assert result["predicted_water_level_cm"] is not None
        assert result["confidence"] > 0
        assert result["forecast_minutes"] == 30
    
    def test_predict_falling_trend(self):
        """Test prediction with falling water level trend."""
        nowcaster = FloodNowcaster()
        base_time = datetime.now(timezone.utc)
        
        readings = [
            {
                "water_level_cm": 40.0,
                "timestamp": (base_time - timedelta(minutes=10)).isoformat(),
            },
            {
                "water_level_cm": 30.0,
                "timestamp": base_time.isoformat(),
            },
        ]
        
        result = nowcaster.predict(
            device_id="ESP32_001",
            historical_readings=readings,
            forecast_minutes=15,
        )
        
        assert result["trend"] == "falling"
    
    def test_predict_batch(self):
        """Test batch prediction."""
        nowcaster = FloodNowcaster()
        base_time = datetime.now(timezone.utc)
        
        device_readings = {
            "ESP32_001": [
                {"water_level_cm": 20.0, "timestamp": base_time.isoformat()},
                {"water_level_cm": 25.0, "timestamp": base_time.isoformat()},
            ],
            "ESP32_002": [
                {"water_level_cm": 30.0, "timestamp": base_time.isoformat()},
                {"water_level_cm": 28.0, "timestamp": base_time.isoformat()},
            ],
        }
        
        results = nowcaster.predict_batch(device_readings, forecast_minutes=30)
        assert len(results) == 2


class TestSensorAnomalyDetector:
    """Tests for SensorAnomalyDetector stub."""
    
    def test_initialization(self):
        """Test model initialization."""
        detector = SensorAnomalyDetector()
        assert detector is not None
        assert detector.is_trained == False
    
    def test_detect_normal_reading(self):
        """Test detection with normal reading."""
        detector = SensorAnomalyDetector()
        result = detector.detect(
            device_id="ESP32_001",
            water_level_cm=25.0,
            temperature=28.5,
            humidity=75,
            battery_voltage=3.8,
        )
        
        assert result["device_id"] == "ESP32_001"
        assert result["is_anomaly"] == False
        assert result["anomaly_score"] < 0.3
        assert result["anomaly_types"] == ["none"]
    
    def test_detect_negative_value_anomaly(self):
        """Test detection of negative water level."""
        detector = SensorAnomalyDetector()
        result = detector.detect(
            device_id="ESP32_001",
            water_level_cm=-5.0,
        )
        
        assert result["is_anomaly"] == True
        assert result["anomaly_score"] == 1.0
        assert "negative_value" in result["anomaly_types"]
    
    def test_detect_unrealistic_high_value(self):
        """Test detection of unrealistically high water level."""
        detector = SensorAnomalyDetector()
        result = detector.detect(
            device_id="ESP32_001",
            water_level_cm=250.0,
        )
        
        assert result["is_anomaly"] == True
        assert "unrealistic_high_value" in result["anomaly_types"]
    
    def test_detect_statistical_outlier(self):
        """Test detection of statistical outlier."""
        detector = SensorAnomalyDetector()
        result = detector.detect(
            device_id="ESP32_001",
            water_level_cm=80.0,
            historical_mean=25.0,
            historical_std=5.0,
        )
        
        assert result["is_anomaly"] == True
        assert "statistical_outlier" in result["anomaly_types"]
        assert "z_score" in result["details"]
    
    def test_detect_temperature_anomaly(self):
        """Test detection of temperature anomaly."""
        detector = SensorAnomalyDetector()
        result = detector.detect(
            device_id="ESP32_001",
            water_level_cm=25.0,
            temperature=60.0,  # Unrealistically high
        )
        
        assert result["is_anomaly"] == True
        assert "temperature_anomaly" in result["anomaly_types"]
    
    def test_detect_invalid_humidity(self):
        """Test detection of invalid humidity."""
        detector = SensorAnomalyDetector()
        result = detector.detect(
            device_id="ESP32_001",
            water_level_cm=25.0,
            humidity=150,  # Out of range
        )
        
        assert result["is_anomaly"] == True
        assert "invalid_humidity" in result["anomaly_types"]
    
    def test_detect_battery_anomaly(self):
        """Test detection of battery anomaly."""
        detector = SensorAnomalyDetector()
        result = detector.detect(
            device_id="ESP32_001",
            water_level_cm=25.0,
            battery_voltage=2.0,  # Too low
        )
        
        assert result["is_anomaly"] == True
        assert "battery_anomaly" in result["anomaly_types"]
    
    def test_detect_batch(self):
        """Test batch anomaly detection."""
        detector = SensorAnomalyDetector()
        readings = [
            {"device_id": "ESP32_001", "water_level_cm": 25.0},
            {"device_id": "ESP32_002", "water_level_cm": -10.0},  # Anomaly
        ]
        
        results = detector.detect_batch(readings)
        assert len(results) == 2
        assert results[0]["is_anomaly"] == False
        assert results[1]["is_anomaly"] == True
    
    def test_get_statistics(self):
        """Test statistics calculation."""
        detector = SensorAnomalyDetector()
        readings = [20.0, 25.0, 30.0, 22.0, 28.0]
        
        stats = detector.get_statistics("ESP32_001", readings)
        
        assert stats["device_id"] == "ESP32_001"
        assert stats["mean"] is not None
        assert stats["std"] is not None
        assert stats["min"] == 20.0
        assert stats["max"] == 30.0
        assert stats["count"] == 5
    
    def test_get_statistics_empty(self):
        """Test statistics with empty readings."""
        detector = SensorAnomalyDetector()
        stats = detector.get_statistics("ESP32_001", [])
        
        assert stats["mean"] is None
        assert stats["count"] == 0
