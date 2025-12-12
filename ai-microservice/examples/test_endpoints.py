"""
Test API endpoints with sample requests.

This script demonstrates how to use the Guardy AI API endpoints.
Requires a running FastAPI server at http://localhost:8000
"""

import requests
from datetime import datetime, timedelta
import json


BASE_URL = "http://localhost:8000/api/v1"


def test_flood_risk_prediction():
    """Test flood risk prediction endpoint."""
    print("\n" + "="*60)
    print("TEST 1: Flood Risk Prediction")
    print("="*60)
    
    # Sample request
    request_data = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "rainfall_mm": 85.5,
        "temperature": 28.3,
        "humidity": 88.0,
        "date": "2024-07-15",
        "month": 7,
        "day_of_year": 196,
        "location_name": "New Delhi, India"
    }
    
    print("\nRequest:")
    print(json.dumps(request_data, indent=2))
    
    try:
        response = requests.post(f"{BASE_URL}/predict/flood-risk", json=request_data)
        response.raise_for_status()
        
        result = response.json()
        print("\nResponse:")
        print(json.dumps(result, indent=2))
        print(f"\n✅ Flood Risk: {result['risk_level']} (probability: {result['flood_probability']:.1%})")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")


def test_nowcast():
    """Test flood nowcasting endpoint."""
    print("\n" + "="*60)
    print("TEST 2: Flood Nowcasting")
    print("="*60)
    
    # Generate 7 days of historical data
    historical_sequence = []
    base_time = datetime.now() - timedelta(days=7)
    
    for i in range(7):
        reading_time = base_time + timedelta(days=i)
        historical_sequence.append({
            "rainfall_mm": 20.0 + i * 5,  # Increasing rainfall
            "temperature": 27.0 - i * 0.5,
            "humidity": 75.0 + i * 2,
            "timestamp": reading_time.isoformat()
        })
    
    request_data = {
        "latitude": 23.0225,
        "longitude": 72.5714,
        "location": "Ahmedabad, Gujarat",
        "historical_sequence": historical_sequence,
        "forecast_hours": [1, 3, 6, 12, 24]
    }
    
    print("\nRequest (7 historical readings):")
    print(f"Location: {request_data['location']}")
    print(f"Forecast horizons: {request_data['forecast_hours']} hours")
    
    try:
        response = requests.post(f"{BASE_URL}/predict/nowcast", json=request_data)
        response.raise_for_status()
        
        result = response.json()
        print("\nResponse:")
        print(f"Overall Risk: {result['overall_risk_level']}")
        print(f"Trend: {result['trend']}")
        print("\nPredictions:")
        for pred in result['predictions']:
            warning = "⚠️ EARLY WARNING" if pred['early_warning'] else ""
            print(f"  {pred['hours_ahead']:2d}h: {pred['flood_probability']:.1%} - {pred['risk_level']} {warning}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")


def test_anomaly_detection():
    """Test sensor anomaly detection endpoint."""
    print("\n" + "="*60)
    print("TEST 3: Sensor Anomaly Detection")
    print("="*60)
    
    # Test case 1: Normal reading
    print("\n--- Case 1: Normal Reading ---")
    request_data = {
        "device_id": "SENSOR-001",
        "water_level_cm": 45.2,
        "rainfall_mm": 12.5,
        "temperature": 26.8,
        "humidity": 72.0,
        "battery_voltage": 3.7,
        "signal_strength": -65,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(f"{BASE_URL}/predict/anomaly", json=request_data)
        response.raise_for_status()
        
        result = response.json()
        print(f"Anomaly: {result['is_anomaly']}")
        print(f"Severity: {result['anomaly_severity']}")
        print(f"Explanation: {result['explanation']}")
        print(f"Maintenance Required: {result['maintenance_required']}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
    
    # Test case 2: Anomalous reading
    print("\n--- Case 2: Anomalous Reading ---")
    request_data = {
        "device_id": "SENSOR-002",
        "water_level_cm": 500.0,  # Suspicious high value
        "rainfall_mm": 250.0,     # Very high rainfall
        "temperature": 55.0,      # Abnormally high
        "humidity": 105.0,        # Impossible value
        "battery_voltage": 2.1,   # Low battery
        "signal_strength": -105,  # Weak signal
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(f"{BASE_URL}/predict/anomaly", json=request_data)
        response.raise_for_status()
        
        result = response.json()
        print(f"Anomaly: {result['is_anomaly']}")
        print(f"Severity: {result['anomaly_severity']}")
        print(f"Explanation: {result['explanation']}")
        print(f"Maintenance Required: {result['maintenance_required']}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")


def test_batch_prediction():
    """Test batch flood risk prediction endpoint."""
    print("\n" + "="*60)
    print("TEST 4: Batch Flood Risk Prediction")
    print("="*60)
    
    # Multiple locations
    locations = [
        {
            "latitude": 28.6139,
            "longitude": 77.2090,
            "rainfall_mm": 75.0,
            "temperature": 30.0,
            "humidity": 80.0,
            "date": "2024-07-15",
            "month": 7,
            "day_of_year": 196,
            "location_name": "New Delhi"
        },
        {
            "latitude": 19.0760,
            "longitude": 72.8777,
            "rainfall_mm": 120.0,
            "temperature": 28.0,
            "humidity": 90.0,
            "date": "2024-07-15",
            "month": 7,
            "day_of_year": 196,
            "location_name": "Mumbai"
        },
        {
            "latitude": 13.0827,
            "longitude": 80.2707,
            "rainfall_mm": 50.0,
            "temperature": 32.0,
            "humidity": 75.0,
            "date": "2024-07-15",
            "month": 7,
            "day_of_year": 196,
            "location_name": "Chennai"
        }
    ]
    
    request_data = {"locations": locations}
    
    print(f"\nRequesting predictions for {len(locations)} locations...")
    
    try:
        response = requests.post(f"{BASE_URL}/predict/batch", json=request_data)
        response.raise_for_status()
        
        result = response.json()
        print(f"\nSuccessful predictions: {result['successful_predictions']}/{result['total_locations']}")
        
        for i, pred in enumerate(result['predictions']):
            location = locations[i]['location_name']
            print(f"\n{location}:")
            print(f"  Risk Level: {pred['risk_level']}")
            print(f"  Probability: {pred['flood_probability']:.1%}")
            print(f"  Factors: {', '.join(pred['contributing_factors'])}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")


def test_model_health():
    test_evacuation_zones()
    """Test model health check endpoint."""
    print("\n" + "="*60)
    print("TEST 5: Model Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/models/health")
        response.raise_for_status()
        
        result = response.json()
        print("\nModel Status:")
        print(f"All Models Loaded: {result['all_models_loaded']}")
        print(f"System Uptime: {result['system_uptime_seconds']:.2f}s")
        
        print("\nFloodRiskScorer:")
        scorer = result['risk_scorer']
        print(f"  Loaded: {scorer['is_loaded']}")
        print(f"  Accuracy: {scorer['accuracy']:.2%}")
        print(f"  Version: {scorer['model_version']}")
        
        print("\nFloodNowcaster:")
        nowcaster = result['nowcaster']
        print(f"  Loaded: {nowcaster['is_loaded']}")
        print(f"  Accuracy: {nowcaster['accuracy']:.2%}")
        print(f"  Version: {nowcaster['model_version']}")
        
        print("\nAnomalyDetector:")
        anomaly = result['anomaly_detector']
        print(f"  Loaded: {anomaly['is_loaded']}")
        print(f"  Accuracy: {anomaly['accuracy']:.2%}")
        print(f"  Version: {anomaly['model_version']}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("GUARDY AI API - ENDPOINT TESTS")
    print("="*60)
    print(f"\nBase URL: {BASE_URL}")
    print("Make sure the API server is running: uvicorn app.main:app --reload")
    
    # Run all tests
    test_flood_risk_prediction()
    test_nowcast()
    test_anomaly_detection()
    test_batch_prediction()
    test_model_health()
    test_evacuation_zones()
    test_model_management()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)
    print("\n💡 TIP: For detailed model management tests, run: python examples/test_model_management.py\n")


def test_model_management():
    """Test model management endpoints."""
    print("\n" + "="*60)
    print("TEST 7: Model Management")
    print("="*60)
    
    try:
        # Test models status
        print("\n1. Getting models status...")
        response = requests.get(f"{BASE_URL}/models/status")
        response.raise_for_status()
        
        status = response.json()
        print(f"   System Status: {status['system_status']}")
        print(f"   All Models Loaded: {status['all_models_loaded']}")
        print(f"   Total Predictions: {status['total_predictions']}")
        
        # Test individual model metadata
        print("\n2. Getting risk_scorer metadata...")
        response = requests.get(f"{BASE_URL}/models/risk_scorer/metadata")
        response.raise_for_status()
        
        metadata = response.json()
        print(f"   Model: {metadata['name']}")
        print(f"   Version: {metadata['version']}")
        print(f"   Accuracy: {metadata['accuracy']:.2%}")
        
        # Test model stats
        print("\n3. Getting nowcaster stats...")
        response = requests.get(f"{BASE_URL}/models/nowcaster/stats")
        response.raise_for_status()
        
        stats = response.json()
        print(f"   Total Predictions: {stats['total_predictions']}")
        print(f"   Predictions/min: {stats['predictions_per_minute']:.2f}")
        
        print(f"\n✅ Model management tests passed!")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()


def test_evacuation_zones():
    """Test evacuation zone generation endpoint."""
    print("\n" + "="*60)
    print("TEST 6: Evacuation Zone Generation")
    print("="*60)
    
    request_data = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "flood_probability": 0.75,
        "risk_level": "high",
        "location_name": "New Delhi",
        "population_density": 11320,
        "include_shelters": True,
        "zone_radii": [500, 1000, 2000]
    }
    
    print(f"\nGenerating evacuation zones for {request_data['location_name']}...")
    print(f"Risk Level: {request_data['risk_level']} ({request_data['flood_probability']:.0%})")
    
    try:
        response = requests.post(f"{BASE_URL}/predict/evacuation-zones", json=request_data)
        response.raise_for_status()
        
        result = response.json()
        print(f"\n✅ Generated {len(result['zones'])} evacuation zones")
        
        for zone in result['zones']:
            print(f"\nZone {zone['zone_id']}:")
            print(f"  Priority: {zone['priority']}")
            print(f"  Affected: ~{zone['estimated_affected']:,} people")
            print(f"  Time: {zone['evacuation_time_minutes']} minutes")
        
        if result.get('shelters'):
            print(f"\nShelters: {len(result['shelters'])} available")
            for shelter in result['shelters'][:2]:  # Show first 2
                print(f"  - {shelter['name']} ({shelter['capacity']} capacity)")
        
        print(f"\nGeoJSON Features: {len(result['geojson']['features'])}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
