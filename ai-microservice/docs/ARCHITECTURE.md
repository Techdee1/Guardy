# FloodGuard AI Microservice - Current Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ FloodRisk   │  │  Weather     │  │    Emergency           │ │
│  │ Monitor     │  │  Monitor     │  │    Form                │ │
│  └─────────────┘  └──────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS Requests
                              │
        ┌─────────────────────┴──────────────────────┐
        │                                             │
        ▼                                             ▼
┌───────────────────┐                    ┌──────────────────────┐
│   JAVA BACKEND    │                    │   AI MICROSERVICE    │
│  (Spring Boot)    │                    │     (FastAPI)        │
│                   │                    │                      │
│  REST API         │                    │  ML API Endpoints:   │
│  - Alerts         │                    │  ├─ POST /predict/   │
│  - Sensors        │                    │  │   risk           │
│  - Users          │                    │  ├─ POST /predict/   │
│  - Reports        │                    │  │   nowcast        │
│                   │                    │  └─ POST /detect/    │
│                   │                    │     anomaly          │
└─────────┬─────────┘                    └──────────┬───────────┘
          │                                         │
          └─────────────┬───────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │    POSTGRESQL DB       │
            │                        │
            │  Tables:               │
            │  - sensor_devices      │
            │  - sensor_readings     │
            │  - sensor_alerts       │
            │  - flood_events        │
            │  - users               │
            │  - alert_subscriptions │
            └────────────────────────┘
```

## AI Microservice Architecture (Current Implementation)

```
ai-microservice/
│
├── app/
│   ├── main.py ──────────────┐ FastAPI Application
│   │                          │ ✅ Lifespan events
│   │                          │ ✅ CORS middleware
│   │                          │ ✅ Global exception handler
│   │
│   ├── config.py ─────────────┐ Configuration
│   │                          │ ✅ Pydantic Settings
│   │                          │ ✅ Database credentials
│   │                          │ ✅ Environment variables
│   │
│   ├── database.py ───────────┐ Database Connection
│   │                          │ ✅ SQLAlchemy engine
│   │                          │ ✅ Session management
│   │                          │ ✅ PostgreSQL connection pool
│   │
│   ├── schemas/
│   │   └── predictions.py ───┐ Request/Response Schemas
│   │                          │ ✅ RiskPredictionRequest/Response
│   │                          │ ✅ NowcastRequest/Response
│   │                          │ ✅ AnomalyDetectionRequest/Response
│   │
│   ├── models/
│   │   └── database.py ───────┐ ORM Models
│   │                          │ ✅ SensorDevice
│   │                          │ ✅ SensorReading
│   │                          │ ✅ SensorAlert
│   │                          │ ✅ FloodEvent
│   │
│   ├── ml/
│   │   ├── flood_risk_scorer.py ──┐ ML Models (Stubs)
│   │   ├── flood_nowcaster.py     │ ✅ FloodRiskScorer
│   │   └── anomaly_detector.py ───┘ ✅ FloodNowcaster
│   │                                 ✅ SensorAnomalyDetector
│   │
│   └── api/
│       └── v1/
│           └── predictions.py ─────┐ API Endpoints
│                                    │ ✅ POST /api/v1/predict/risk
│                                    │ ✅ POST /api/v1/predict/nowcast
│                                    │ ✅ POST /api/v1/detect/anomaly
│
├── tests/
│   ├── test_main.py ────────────── 4 tests ✅
│   ├── test_models.py ──────────── 6 tests ✅
│   ├── test_ml_models.py ───────── 21 tests ✅
│   └── test_predictions_api.py ─── 27 tests ✅
│                                    ────────────
│                                    58 TOTAL ✅
│
├── examples/
│   └── api_usage.py ────────────── Usage examples
│
├── docs/
│   ├── DATABASE_MODELS.md ──────── Model documentation
│   └── PHASE_2_2_SUMMARY.md ────── Phase summary
│
├── data/
│   ├── training/ ───────────────── (Future: training data)
│   ├── validation/ ─────────────── (Future: validation data)
│   └── test/ ───────────────────── (Future: test data)
│
├── models/ ─────────────────────── (Future: trained models)
│   ├── flood_risk_scorer.pkl
│   ├── lstm_nowcaster.h5
│   └── anomaly_detector.pkl
│
├── notebooks/ ──────────────────── (Future: training notebooks)
│   ├── train_risk_scorer.ipynb
│   ├── train_lstm_nowcaster.ipynb
│   └── model_evaluation.ipynb
│
└── scripts/ ────────────────────── (Future: utility scripts)
    ├── collect_training_data.py
    └── prepare_lstm_data.py
```

## API Request Flow

```
┌─────────────┐
│   CLIENT    │
│  (Browser)  │
└──────┬──────┘
       │
       │ POST /api/v1/predict/risk
       │ {latitude, longitude, water_level_cm, ...}
       │
       ▼
┌──────────────────────────────────────────────────────┐
│              FastAPI Application                      │
│                                                       │
│  1. Request Reception                                 │
│     ├─ CORS Check ✓                                  │
│     └─ Route Matching: /api/v1/predict/risk          │
│                                                       │
│  2. Request Validation (Pydantic)                     │
│     ├─ RiskPredictionRequest schema                  │
│     ├─ Check latitude: -90 to 90 ✓                   │
│     ├─ Check longitude: -180 to 180 ✓                │
│     └─ Check water_level_cm: >= 0 ✓                  │
│                                                       │
│  3. Endpoint Handler                                  │
│     └─ predictions.predict_flood_risk()               │
│                                                       │
│  4. ML Model Invocation                               │
│     └─ FloodRiskScorer.predict()                      │
│         ├─ Water level factor (0.6 if > 50cm)        │
│         ├─ Rainfall factor (0.3 if > 100mm)          │
│         ├─ Humidity factor (0.1 if > 85%)            │
│         └─ Calculate total risk_score                │
│                                                       │
│  5. Response Formatting                               │
│     ├─ RiskPredictionResponse schema                 │
│     └─ JSON serialization                            │
│                                                       │
└──────────────────┬───────────────────────────────────┘
                   │
                   │ 200 OK
                   │ {risk_score, risk_level, confidence, ...}
                   │
                   ▼
           ┌───────────────┐
           │    CLIENT     │
           │   (Browser)   │
           └───────────────┘
```

## ML Model Evolution Path

```
Current (Phase 2.2):                Future (Phase 6.2):
┌──────────────────┐               ┌──────────────────┐
│  ML MODEL STUBS  │               │  TRAINED MODELS  │
├──────────────────┤               ├──────────────────┤
│                  │               │                  │
│ FloodRiskScorer  │  ──────────▶  │ Random Forest +  │
│ - Threshold-     │               │ Gradient Boost   │
│   based logic    │               │ (trained on      │
│ - Simple rules   │               │ historical data) │
│                  │               │                  │
│ FloodNowcaster   │  ──────────▶  │ LSTM Neural Net  │
│ - Linear         │               │ (TensorFlow)     │
│   extrapolation  │               │ - 2 layers       │
│                  │               │ - 64/32 units    │
│                  │               │                  │
│ AnomalyDetector  │  ──────────▶  │ Isolation Forest │
│ - Rule-based     │               │ (scikit-learn)   │
│   checks         │               │ (trained on      │
│                  │               │ normal patterns) │
└──────────────────┘               └──────────────────┘
```

## Data Flow

```
┌─────────────┐
│   ESP32     │ ──┐
│  Sensor 1   │   │
└─────────────┘   │
                  │ HTTP POST
┌─────────────┐   │ {water_level, temp, ...}
│   ESP32     │ ──┤
│  Sensor 2   │   │                    ┌──────────────┐
└─────────────┘   │                    │   JAVA       │
                  ├──────────────────▶ │   BACKEND    │
┌─────────────┐   │                    └──────┬───────┘
│   ESP32     │ ──┤                           │
│  Sensor N   │   │                           │ INSERT
└─────────────┘   │                           │
                  │                           ▼
                                    ┌──────────────────┐
                  │                 │   PostgreSQL     │
                  │                 │  sensor_readings │
                  │                 └────────┬─────────┘
                  │                          │
                  │                          │ SELECT
                  │                          │
                  │                          ▼
                  │                 ┌──────────────────┐
                  │                 │   AI SERVICE     │
                  │                 │                  │
                  │                 │  1. Fetch data   │
                  │                 │  2. Predict risk │
                  └────────────────▶│  3. Detect       │
                    Prediction         │     anomalies    │
                    Request            └────────┬─────────┘
                                               │
                                               │ Response
                                               │
                                               ▼
                                       ┌──────────────┐
                                       │   FRONTEND   │
                                       │  Dashboard   │
                                       └──────────────┘
```

## Deployment Architecture (Future)

```
┌─────────────────────────────────────────────────────────┐
│                      CLOUD (AWS/Azure/GCP)              │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │            Load Balancer / API Gateway          │   │
│  └────────────┬─────────────────────┬──────────────┘   │
│               │                     │                   │
│        ┌──────▼─────────┐   ┌──────▼──────────┐        │
│        │  Java Backend  │   │  AI Microservice│        │
│        │  (Container)   │   │   (Container)   │        │
│        │                │   │                 │        │
│        │  - Spring Boot │   │  - FastAPI      │        │
│        │  - Port 8080   │   │  - Port 8000    │        │
│        │  - 2+ replicas │   │  - 2+ replicas  │        │
│        └────────┬───────┘   └─────────┬───────┘        │
│                 │                     │                 │
│                 └──────────┬──────────┘                 │
│                            │                            │
│                  ┌─────────▼──────────┐                 │
│                  │   PostgreSQL DB    │                 │
│                  │   (Managed)        │                 │
│                  └────────────────────┘                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Status Summary

### ✅ Completed (Phases 0-2.2)
- [x] Project structure
- [x] Virtual environment
- [x] Dependencies installed
- [x] Configuration management
- [x] Database models
- [x] ML model stubs
- [x] API endpoints
- [x] Request/response validation
- [x] Comprehensive testing (58 tests)
- [x] Documentation
- [x] Example usage scripts

### ⏳ Pending (Phases 3-7)
- [ ] Data collection from PostgreSQL
- [ ] Feature engineering
- [ ] Train actual ML models
- [ ] Model evaluation
- [ ] LSTM time-series preparation
- [ ] Model loading & caching
- [ ] Performance optimization
- [ ] Integration testing
- [ ] Deployment guide

### 🎯 Ready For
- ✅ Frontend integration (CORS configured)
- ✅ Local development testing
- ✅ API documentation review (/docs)
- ✅ Example API calls (examples/api_usage.py)
- ⏳ Production deployment (needs real trained models)
- ⏳ Historical data collection
- ⏳ Model training phase
