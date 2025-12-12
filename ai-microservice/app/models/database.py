"""SQLAlchemy database models for FloodGuard."""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, CheckConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class SensorDevice(Base):
    """IoT sensor device model."""
    
    __tablename__ = "sensor_devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(
        String(50), 
        default='offline',
        nullable=False
    )
    battery_level = Column(Integer, default=100)
    last_ping = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    readings = relationship("SensorReading", back_populates="device", cascade="all, delete-orphan")
    alerts = relationship("SensorAlert", back_populates="device", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('online', 'offline', 'low_battery', 'error')",
            name='check_sensor_status'
        ),
        CheckConstraint(
            "battery_level >= 0 AND battery_level <= 100",
            name='check_battery_level'
        ),
        Index('idx_sensor_devices_status', 'status'),
    )
    
    def __repr__(self):
        return f"<SensorDevice(device_id='{self.device_id}', name='{self.name}', status='{self.status}')>"


class SensorReading(Base):
    """Time-series sensor readings model."""
    
    __tablename__ = "sensor_readings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(100), ForeignKey('sensor_devices.device_id', ondelete='CASCADE'), nullable=False)
    water_level_cm = Column(Float, nullable=False)
    temperature = Column(Float)
    humidity = Column(Integer)
    battery_voltage = Column(Float)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    device = relationship("SensorDevice", back_populates="readings")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "humidity >= 0 AND humidity <= 100",
            name='check_humidity_range'
        ),
        Index('idx_readings_device_time', 'device_id', 'timestamp', postgresql_using='btree'),
        Index('idx_readings_water_level', 'water_level_cm', 'timestamp'),
        Index('idx_readings_recent', 'created_at', postgresql_where=text("created_at > NOW() - INTERVAL '7 days'")),
    )
    
    def __repr__(self):
        return f"<SensorReading(device_id='{self.device_id}', water_level={self.water_level_cm}cm, timestamp='{self.timestamp}')>"


class SensorAlert(Base):
    """Sensor alert model for threshold breaches."""
    
    __tablename__ = "sensor_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(100), ForeignKey('sensor_devices.device_id', ondelete='CASCADE'), nullable=False)
    threshold_breached = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    severity = Column(String(50), nullable=False)
    alert_sent = Column(Boolean, default=False, server_default='false')
    status = Column(String(50), default='active', server_default='active')
    message = Column(String)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    device = relationship("SensorDevice", back_populates="alerts")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "severity IN ('low', 'medium', 'high')",
            name='check_alert_severity'
        ),
        CheckConstraint(
            "status IN ('active', 'resolved')",
            name='check_alert_status'
        ),
        Index('idx_alerts_active', 'status', 'severity', postgresql_where=text("status = 'active'")),
        Index('idx_alerts_device', 'device_id', 'timestamp'),
        Index('idx_alerts_severity', 'severity', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<SensorAlert(device_id='{self.device_id}', severity='{self.severity}', status='{self.status}')>"


class FloodEvent(Base):
    """Historical flood event model (for training data)."""
    
    __tablename__ = "flood_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    severity = Column(String(50), nullable=False)
    rainfall = Column(Float)
    description = Column(String)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "severity IN ('low', 'medium', 'high')",
            name='check_flood_severity'
        ),
        Index('idx_flood_events_location', 'latitude', 'longitude'),
        Index('idx_flood_events_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<FloodEvent(location='{self.location}', severity='{self.severity}', timestamp='{self.timestamp}')>"
