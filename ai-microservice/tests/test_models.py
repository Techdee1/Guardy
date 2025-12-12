"""Tests for database models."""
import pytest
from datetime import datetime, timezone
from app.models.database import SensorDevice, SensorReading, SensorAlert, FloodEvent


def test_sensor_device_creation():
    """Test creating a SensorDevice instance."""
    device = SensorDevice(
        device_id="ESP32_001",
        name="Test Sensor",
        location="Test Location",
        latitude=6.5244,
        longitude=3.3792,
        status="online",
        battery_level=85
    )
    
    assert device.device_id == "ESP32_001"
    assert device.name == "Test Sensor"
    assert device.latitude == 6.5244
    assert device.longitude == 3.3792
    assert device.status == "online"
    assert device.battery_level == 85


def test_sensor_reading_creation():
    """Test creating a SensorReading instance."""
    reading = SensorReading(
        device_id="ESP32_001",
        water_level_cm=25.5,
        temperature=28.3,
        humidity=75,
        battery_voltage=3.8,
        timestamp=datetime.now(timezone.utc)
    )
    
    assert reading.device_id == "ESP32_001"
    assert reading.water_level_cm == 25.5
    assert reading.temperature == 28.3
    assert reading.humidity == 75
    assert reading.battery_voltage == 3.8
    assert reading.timestamp is not None


def test_sensor_alert_creation():
    """Test creating a SensorAlert instance."""
    alert = SensorAlert(
        device_id="ESP32_001",
        threshold_breached="water_level",
        value=55.0,
        threshold=50.0,
        severity="high",
        status="active",  # Explicitly set since we're not using database
        message="Critical water level breach",
        timestamp=datetime.now(timezone.utc)
    )
    
    assert alert.device_id == "ESP32_001"
    assert alert.threshold_breached == "water_level"
    assert alert.value == 55.0
    assert alert.threshold == 50.0
    assert alert.severity == "high"
    assert alert.status == "active"


def test_flood_event_creation():
    """Test creating a FloodEvent instance."""
    event = FloodEvent(
        location="Lekki, Lagos",
        latitude=6.4474,
        longitude=3.4706,
        severity="medium",
        rainfall=85.5,
        description="Heavy rainfall causing localized flooding",
        timestamp=datetime.now(timezone.utc)
    )
    
    assert event.location == "Lekki, Lagos"
    assert event.latitude == 6.4474
    assert event.longitude == 3.4706
    assert event.severity == "medium"
    assert event.rainfall == 85.5


def test_sensor_device_repr():
    """Test SensorDevice string representation."""
    device = SensorDevice(
        device_id="ESP32_001",
        name="Test Sensor",
        latitude=6.5244,
        longitude=3.3792,
        status="online"
    )
    
    repr_str = repr(device)
    assert "SensorDevice" in repr_str
    assert "ESP32_001" in repr_str
    assert "Test Sensor" in repr_str
    assert "online" in repr_str


def test_sensor_reading_repr():
    """Test SensorReading string representation."""
    timestamp = datetime.now(timezone.utc)
    reading = SensorReading(
        device_id="ESP32_001",
        water_level_cm=25.5,
        timestamp=timestamp
    )
    
    repr_str = repr(reading)
    assert "SensorReading" in repr_str
    assert "ESP32_001" in repr_str
    assert "25.5" in repr_str
