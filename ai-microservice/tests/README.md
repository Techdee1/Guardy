# Testing Guide

This directory contains comprehensive test suites for the Guardy AI Microservice.

## Test Structure

```
tests/
├── conftest.py                      # Pytest fixtures and configuration
├── test_api_predictions.py          # Prediction endpoint tests (23 tests)
├── test_api_model_management.py     # Model management endpoint tests (21 tests)
├── test_integration.py              # End-to-end integration tests (12 tests)
├── test_ml_models.py                # ML model unit tests (existing)
└── test_main.py                     # Main app tests (existing)
```

**Total: 56 new comprehensive tests**

## Test Coverage

### Prediction API Tests (`test_api_predictions.py`)
- **FloodRiskEndpoint** (5 tests)
  - Low/high risk scenarios
  - Validation (latitude, longitude, negative values)
  - Minimal parameters

- **NowcastEndpoint** (4 tests)
  - Rising/stable trends
  - Insufficient data handling
  - Single/multiple forecast horizons

- **AnomalyDetectionEndpoint** (3 tests)
  - Normal sensor readings
  - Anomalous readings detection
  - Missing required fields

- **BatchPredictionEndpoint** (5 tests)
  - Single/multiple locations
  - Maximum batch size (100)
  - Empty list validation
  - Exceeding limits

- **EvacuationZonesEndpoint** (5 tests)
  - High/medium risk zones
  - With/without shelters
  - Custom radii
  - GeoJSON structure validation

- **HealthEndpoint** (1 test)
  - Model health check

### Model Management Tests (`test_api_model_management.py`)
- **ModelsStatusEndpoint** (2 tests)
  - System-wide status
  - Detailed model information

- **ModelMetadataEndpoint** (4 tests)
  - Individual model metadata (risk_scorer, nowcaster, anomaly_detector)
  - Invalid model handling

- **ModelStatsEndpoint** (3 tests)
  - Statistics retrieval
  - Stats updates after predictions
  - Invalid model handling

- **ModelReloadEndpoint** (6 tests)
  - Reload all models
  - Reload individual models
  - Invalid model handling
  - Predictions after reload

- **CacheClearEndpoint** (3 tests)
  - Cache clearing per model
  - Invalid model handling

- **Integration** (3 tests)
  - Status/metadata consistency
  - Reload updates status
  - Multi-endpoint sequence workflows

### Integration Tests (`test_integration.py`)
- **FloodMonitoringWorkflow** (2 tests)
  - Full detection → evacuation workflow
  - Multi-location monitoring

- **TimeSeriesPredictionWorkflow** (2 tests)
  - Nowcast → risk assessment
  - Continuous monitoring simulation

- **AnomalyDetectionWorkflow** (2 tests)
  - Sensor validation workflow
  - Multi-sensor detection

- **ModelReliabilityWorkflow** (3 tests)
  - Predictions after reload
  - Health monitoring during operations
  - Error recovery

- **PerformanceWorkflow** (2 tests)
  - Concurrent predictions
  - Large batch processing

- **DataValidationWorkflow** (1 test)
  - Invalid data handling

## Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio httpx

# Ensure API server is running
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Suites
```bash
# Prediction API tests only
pytest tests/test_api_predictions.py -v

# Model management tests only
pytest tests/test_api_model_management.py -v

# Integration tests only
pytest tests/test_integration.py -v
```

### Run with Coverage
```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

### Run Specific Test Class or Function
```bash
# Run single test class
pytest tests/test_api_predictions.py::TestFloodRiskEndpoint -v

# Run single test function
pytest tests/test_api_predictions.py::TestFloodRiskEndpoint::test_flood_risk_low -v
```

### Run Tests with Output
```bash
# Show print statements
pytest tests/ -v -s

# Show only failed tests
pytest tests/ -v --tb=short

# Stop on first failure
pytest tests/ -v -x
```

## Test Fixtures

### Available Fixtures (in `conftest.py`)
- `client` - FastAPI TestClient instance
- `sample_flood_risk_data` - Low/medium/high risk scenarios
- `sample_nowcast_data` - Time series data (rising/stable trends)
- `sample_anomaly_data` - Normal/anomalous sensor readings
- `sample_evacuation_data` - High/medium risk evacuation scenarios
- `mock_trained_models` - Mock models for testing without loading actual files

## Test Data Examples

### Flood Risk Prediction
```python
{
    "latitude": 6.5244,
    "longitude": 3.3792,
    "rainfall_mm": 120.0,
    "temperature": 30.0,
    "humidity": 95
}
```

### Nowcast Prediction
```python
{
    "latitude": 6.5244,
    "longitude": 3.3792,
    "historical_data": [
        {
            "timestamp": "2024-12-12T10:00:00Z",
            "rainfall_mm": 10.0,
            "water_level_cm": 25.0,
            "temperature_c": 28.0
        }
    ],
    "forecast_horizons": [1, 6, 12, 24]
}
```

### Anomaly Detection
```python
{
    "sensor_id": "SENSOR_001",
    "readings": [
        {
            "timestamp": "2024-12-12T10:00:00Z",
            "value": 25.0,
            "battery_level": 85.0,
            "signal_strength": -65
        }
    ]
}
```

## Expected Test Results

When all tests pass, you should see:
```
============================== test session starts ==============================
collected 56 items

tests/test_api_predictions.py::TestFloodRiskEndpoint::test_flood_risk_low PASSED
tests/test_api_predictions.py::TestFloodRiskEndpoint::test_flood_risk_high PASSED
...
tests/test_integration.py::TestDataValidationWorkflow::test_invalid_data_handling PASSED

============================== 56 passed in 5.23s ================================
```

## Coverage Goals

Target: **>80% code coverage**

Key areas covered:
- ✅ All API endpoints (12 endpoints)
- ✅ Request validation
- ✅ Response schemas
- ✅ Error handling
- ✅ Model management operations
- ✅ End-to-end workflows
- ✅ Edge cases and boundary conditions

## Continuous Integration

### GitHub Actions Workflow
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest tests/ --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Troubleshooting

### Tests Failing with 503 Errors
- Ensure the API server is running: `uvicorn app.main:app --reload`
- Check models are loaded: `curl http://localhost:8000/api/v1/models/health`

### Tests Failing with 422 Validation Errors
- Check request data matches the Pydantic schemas in `app/schemas/predictions.py`
- Verify all required fields are provided

### Import Errors
- Ensure you're running tests from the `ai-microservice` directory
- Check that `conftest.py` is adding the app directory to Python path

### Slow Tests
- Use `-n auto` with `pytest-xdist` for parallel execution:
  ```bash
  pip install pytest-xdist
  pytest tests/ -n auto
  ```

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure tests pass locally
3. Run coverage check: `pytest --cov=app --cov-report=term`
4. Aim for >80% coverage for new code
5. Add test data to `conftest.py` fixtures if reusable

## Notes

- Tests use FastAPI's `TestClient` which doesn't require a running server (but lifespan events may not trigger)
- For integration tests that require actual server state, consider running against live server
- Mock data fixtures ensure consistent, reproducible test results
- Tests are independent and can run in any order
