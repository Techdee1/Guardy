# Database Models Documentation

## Overview
SQLAlchemy ORM models for the FloodGuard AI microservice, matching the PostgreSQL schema defined in `database/sensor_tables.sql`.

## Models

### 1. SensorDevice
IoT sensor device model for ESP32 ultrasonic sensors.

**Table**: `sensor_devices`

**Fields**:
- `id` (UUID): Primary key
- `device_id` (str): Unique device identifier (e.g., "ESP32_001")
- `name` (str): Device display name
- `location` (str): Human-readable location
- `latitude` (float): GPS latitude
- `longitude` (float): GPS longitude
- `status` (str): Device status ('online', 'offline', 'low_battery', 'error')
- `battery_level` (int): Battery percentage (0-100)
- `last_ping` (datetime): Last communication timestamp
- `created_at` (datetime): Record creation timestamp
- `updated_at` (datetime): Last update timestamp

**Relationships**:
- `readings`: One-to-many with SensorReading (cascade delete)
- `alerts`: One-to-many with SensorAlert (cascade delete)

### 2. SensorReading
Time-series sensor readings for water level monitoring.

**Table**: `sensor_readings`

**Fields**:
- `id` (UUID): Primary key
- `device_id` (str): Foreign key to sensor_devices
- `water_level_cm` (float): Water level in centimeters
- `temperature` (float): Temperature in Celsius
- `humidity` (int): Humidity percentage (0-100)
- `battery_voltage` (float): Battery voltage
- `timestamp` (datetime): Reading timestamp
- `created_at` (datetime): Record creation timestamp

**Relationships**:
- `device`: Many-to-one with SensorDevice

**Indexes**:
- `idx_readings_device_time`: Composite index on (device_id, timestamp)
- `idx_readings_water_level`: Index on (water_level_cm, timestamp)
- `idx_readings_recent`: Partial index for last 7 days

### 3. SensorAlert
Alert model for threshold breaches.

**Table**: `sensor_alerts`

**Fields**:
- `id` (UUID): Primary key
- `device_id` (str): Foreign key to sensor_devices
- `threshold_breached` (str): Type of threshold (e.g., "water_level")
- `value` (float): Actual value that triggered alert
- `threshold` (float): Threshold value that was breached
- `severity` (str): Alert severity ('low', 'medium', 'high')
- `alert_sent` (bool): Whether notification was sent
- `status` (str): Alert status ('active', 'resolved')
- `message` (str): Alert message/description
- `timestamp` (datetime): Alert timestamp
- `resolved_at` (datetime): Resolution timestamp
- `created_at` (datetime): Record creation timestamp

**Relationships**:
- `device`: Many-to-one with SensorDevice

**Indexes**:
- `idx_alerts_active`: Partial index on active alerts
- `idx_alerts_device`: Composite index on (device_id, timestamp)
- `idx_alerts_severity`: Composite index on (severity, timestamp)

### 4. FloodEvent
Historical flood event model for ML training data.

**Table**: `flood_events`

**Fields**:
- `id` (UUID): Primary key
- `location` (str): Event location name
- `latitude` (float): GPS latitude
- `longitude` (float): GPS longitude
- `severity` (str): Flood severity ('low', 'medium', 'high')
- `rainfall` (float): Rainfall amount in mm
- `description` (str): Event description
- `timestamp` (datetime): Event timestamp
- `created_at` (datetime): Record creation timestamp

**Indexes**:
- `idx_flood_events_location`: Composite index on (latitude, longitude)
- `idx_flood_events_timestamp`: Index on timestamp

## Usage Example

```python
from app.database import SessionLocal
from app.models import SensorDevice, SensorReading
from datetime import datetime, timezone

# Create database session
db = SessionLocal()

# Query sensor devices
devices = db.query(SensorDevice).filter(
    SensorDevice.status == 'online'
).all()

# Query recent readings for a device
readings = db.query(SensorReading).filter(
    SensorReading.device_id == 'ESP32_001',
    SensorReading.timestamp > datetime.now(timezone.utc) - timedelta(hours=24)
).order_by(SensorReading.timestamp.desc()).all()

# Close session
db.close()
```

## Database Connection

The models use SQLAlchemy's declarative base from `app.database` module:
- Engine: Created from `DATABASE_URL` in settings
- Session management: Via `get_db()` dependency injection
- Connection pooling: Enabled with `pool_pre_ping=True`

## Testing

Model tests are in `tests/test_models.py`:
- Unit tests for model creation
- Validation of field constraints
- Testing relationships and repr methods

Run tests with:
```bash
pytest tests/test_models.py -v
```
