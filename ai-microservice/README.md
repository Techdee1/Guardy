# 🌊 Guardy AI Microservice

**Advanced Flood Prediction & Early Warning System**

A production-ready FastAPI microservice providing real-time flood risk assessment, nowcasting, anomaly detection, and evacuation zone planning using state-of-the-art machine learning models.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-56%20passing-success.svg)](./tests/)
[![Coverage](https://img.shields.io/badge/coverage->80%25-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [ML Models](#-ml-models)
- [Quick Start](#-quick-start)
- [API Documentation](#-api-documentation)
- [Deployment](#-deployment)
- [Development](#-development)
- [Testing](#-testing)
- [Contributing](#-contributing)

---

## ✨ Features

### Core Capabilities
- 🎯 **Flood Risk Prediction** - 96.99% accuracy ensemble model (Random Forest + Gradient Boosting)
- 📈 **Nowcasting** - LSTM-based 1-7 day flood forecasting with 93.3% accuracy
- 🔍 **Anomaly Detection** - Isolation Forest for sensor malfunction detection (98.5% F1-score)
- 🚨 **Evacuation Planning** - Real-time evacuation zone generation with GeoJSON output
- 📊 **Batch Processing** - Process up to 100 locations simultaneously
- 🔄 **Hot-Reload** - Update ML models without server downtime

### Operational Features
- ⚡ High-performance async API
- 📝 Comprehensive request/response validation
- 🔐 Production-ready error handling
- 📊 Real-time model health monitoring
- 🎨 Interactive Swagger UI documentation
- 🧪 56+ comprehensive tests (>80% coverage)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
│        (Web Dashboard, Mobile App, IoT Devices)             │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS/REST
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Prediction  │  │    Model     │  │  Evacuation  │     │
│  │   Endpoints  │  │  Management  │  │    Zones     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────────┬──────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │  Flood   │   │  LSTM    │   │ Isolation│
    │   Risk   │   │ Nowcast  │   │  Forest  │
    │  Scorer  │   │  Model   │   │ Detector │
    └──────────┘   └──────────┘   └──────────┘
```

---

## 🤖 ML Models

### 1. Flood Risk Scorer
**Algorithm:** Random Forest + Gradient Boosting Ensemble  
**Accuracy:** 96.99%  
**Features:** 8 environmental and meteorological indicators  
**Use Case:** Real-time flood risk assessment for any location

**Key Features Analyzed:**
- Rainfall intensity (mm)
- Temperature & humidity
- Historical rainfall patterns (7-day & 30-day averages)
- Location-specific risk factors

**Model File:** `models/flood_risk_scorer_v1.pkl` (1.42 MB)

---

### 2. Flood Nowcaster
**Algorithm:** LSTM Neural Network  
**Accuracy:** 93.3%  
**Architecture:** 2-layer LSTM (64, 32 units) + Dropout (0.2)  
**Forecast Horizons:** 1, 3, 6, 12, 24 hours  
**Sequence Length:** 7 time steps

**Use Case:** Short-term flood prediction for early warning systems

**Model File:** `models/nowcast_lstm_v1.h5` (0.43 MB)

---

### 3. Sensor Anomaly Detector
**Algorithm:** Isolation Forest  
**F1-Score:** 98.5%  
**Features:** 6 sensor health indicators  
**Use Case:** Detecting malfunctioning or compromised sensors

**Detects:**
- Sensor malfunctions
- Battery failures
- Signal loss
- Abnormal readings
- Data transmission errors

**Model File:** `models/anomaly_detector_v1.pkl` (0.71 MB)

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **PostgreSQL 14+** (optional for persistence)
- **8GB RAM** (minimum)
- **2GB disk space** (for models and data)

### Installation

```bash
# Clone the repository
git clone https://github.com/HenryTech12/Guardy.git
cd Guardy/ai-microservice

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the `ai-microservice/` directory:

```env
# Application
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# Database (optional)
DATABASE_URL=postgresql://user:password@localhost:5432/floodguard
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=floodguard
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password

# API Configuration
API_V1_PREFIX=/api/v1
MAX_BATCH_SIZE=100

# Model Paths
MODELS_DIR=./models
DATA_DIR=./data
LOGS_DIR=./logs
```

### Run the Server

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs (Swagger UI)
- **ReDoc:** http://localhost:8000/redoc
- **Health:** http://localhost:8000/api/v1/models/health

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Prediction Endpoints

#### 1. Flood Risk Assessment
```http
POST /predict/flood-risk
```

Assess flood risk for a specific location based on current conditions.

**Request:**
```json
{
  "latitude": 6.5244,
  "longitude": 3.3792,
  "location_name": "Lagos",
  "rainfall_mm": 85.0,
  "temperature": 28.5,
  "humidity": 80
}
```

**Response:**
```json
{
  "flood_probability": 0.87,
  "risk_score": 87.0,
  "risk_level": "high",
  "confidence": 0.94,
  "model_version": "flood_risk_scorer_v1",
  "predicted_at": "2024-12-12T10:30:00Z",
  "top_contributing_factors": [
    {"rainfall_mm": 0.35},
    {"humidity": 0.22},
    {"temperature": 0.18}
  ],
  "recommended_action": "Immediate evacuation recommended"
}
```

---

#### 2. Flood Nowcast
```http
POST /predict/nowcast
```

Generate multi-horizon flood forecasts (1-24 hours).

**Request:**
```json
{
  "latitude": 6.5244,
  "longitude": 3.3792,
  "historical_data": [
    {
      "timestamp": "2024-12-12T09:00:00Z",
      "rainfall_mm": 10.0,
      "water_level_cm": 25.0,
      "temperature_c": 28.0
    }
  ],
  "forecast_horizons": [1, 6, 12, 24]
}
```

---

#### 3. Anomaly Detection
```http
POST /predict/anomaly
```

Detect anomalies in sensor readings.

---

#### 4. Batch Prediction
```http
POST /predict/batch
```

Process multiple locations simultaneously (max 100).

---

#### 5. Evacuation Zones
```http
POST /predict/evacuation-zones
```

Generate evacuation zones with GeoJSON output.

**Request:**
```json
{
  "latitude": 6.5244,
  "longitude": 3.3792,
  "flood_probability": 0.85,
  "risk_level": "high",
  "location_name": "Lagos Island",
  "population_density": 12500,
  "include_shelters": true,
  "zone_radii": [500, 1000, 2000]
}
```

**Response:**
- Evacuation zones with priority levels
- GeoJSON FeatureCollection
- Nearby shelters
- Estimated affected population
- Evacuation time estimates

---

### Model Management Endpoints

#### 6. System Status
```http
GET /models/status
```

Get comprehensive system and model health status.

---

#### 7. Model Metadata
```http
GET /models/{model_name}/metadata
```

Get detailed metadata for specific model.

---

#### 8. Model Statistics
```http
GET /models/{model_name}/stats
```

Get usage statistics for specific model.

---

#### 9. Reload Models
```http
POST /models/reload
POST /models/{model_name}/reload
```

Hot-reload models without server restart.

---

#### 10. Health Check
```http
GET /models/health
```

Basic health check endpoint.

---

### Complete API Examples

See [docs/API_EXAMPLES.md](./docs/API_EXAMPLES.md) for complete curl commands and response examples.

---

## 🚀 Deployment

### Docker Deployment

```bash
# Build image
docker build -t guardy-ai:latest .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  guardy-ai:latest
```

### Docker Compose

```bash
docker-compose up -d
```

### Cloud Platforms

- **Railway:** One-click deployment
- **Render:** Auto-deploy from GitHub
- **Google Cloud Run:** Serverless deployment

---

## 🛠️ Development

### Project Structure

```
ai-microservice/
├── app/
│   ├── api/v1/
│   │   ├── __init__.py
│   │   ├── predictions.py         # Prediction endpoints (1,338 lines)
│   │   └── model_management.py    # Management endpoints (500+ lines)
│   ├── ml/
│   │   ├── flood_risk_scorer.py   # Risk scoring model
│   │   ├── flood_nowcaster.py     # LSTM nowcaster
│   │   └── anomaly_detector.py    # Anomaly detection
│   ├── models/                     # Pydantic models
│   ├── schemas/                    # Request/response schemas
│   ├── utils/                      # Helper functions
│   ├── config.py                   # Configuration
│   ├── database.py                 # Database connection
│   └── main.py                     # FastAPI application
├── models/                         # Trained ML models
├── data/                           # Training datasets
├── tests/                          # Test suites (56 tests)
├── scripts/                        # Utility scripts
├── notebooks/                      # Jupyter notebooks
├── docs/                           # Documentation
└── examples/                       # Example scripts
```

### Adding New Endpoints

1. Define Pydantic schemas in `app/schemas/`
2. Implement endpoint in appropriate router
3. Add tests in `tests/`
4. Update API documentation

### Training Models

```bash
# Flood risk scorer
python scripts/train_risk_scorer.py

# Nowcaster
python scripts/train_nowcaster.py

# Anomaly detector
python scripts/train_anomaly_detector.py
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Specific test suite
pytest tests/test_api_predictions.py -v
pytest tests/test_api_model_management.py -v
pytest tests/test_integration.py -v
```

**Test Coverage:**
- 56 comprehensive tests
- >80% code coverage
- Unit, integration, and end-to-end tests

See [tests/README.md](./tests/README.md) for detailed testing guide.

---

## 📊 Performance

- **p95 Latency:** <200ms (single prediction)
- **Throughput:** 100+ req/sec (single worker)
- **Batch Processing:** Up to 100 locations/request
- **Model Loading:** <500ms (all 3 models)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

## 👥 Authors

- **HenryTech12** - *Initial work* - [GitHub](https://github.com/HenryTech12)

---

## 🙏 Acknowledgments

- FastAPI framework by Sebastián Ramírez
- Scikit-learn & TensorFlow communities
- OpenWeatherMap for weather data API
- Contributors and testers

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/HenryTech12/Guardy/issues)
- **Documentation:** [Full Docs](./docs/)
- **API Examples:** [docs/API_EXAMPLES.md](./docs/API_EXAMPLES.md)

---

**Built with ❤️ for flood-prone communities**
