"""Example usage of the FloodGuard AI Microservice API."""
import requests
from datetime import datetime, timedelta

# API base URL
API_URL = "http://localhost:8000"


def test_health_check():
    """Test the health check endpoint."""
    print("\n" + "="*60)
    print("Testing Health Check Endpoint")
    print("="*60)
    
    response = requests.get(f"{API_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def test_risk_prediction():
    """Test flood risk prediction."""
    print("\n" + "="*60)
    print("Testing Risk Prediction Endpoint")
    print("="*60)
    
    # Example: High risk scenario (Lagos, Nigeria during heavy rainfall)
    payload = {
        "latitude": 6.5244,
        "longitude": 3.3792,
        "water_level_cm": 85.0,
        "rainfall_mm": 120.0,
        "temperature": 28.5,
        "humidity": 90
    }
    
    print(f"Request Payload: {payload}")
    response = requests.post(f"{API_URL}/api/v1/predict/risk", json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Risk Score: {result['risk_score']:.2f}")
        print(f"Risk Level: {result['risk_level'].upper()}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Contributing Factors: {', '.join(result['factors'])}")
        print(f"Model Version: {result['model_version']}")
    else:
        print(f"Error: {response.json()}")
    
    return response.status_code == 200


def test_nowcasting():
    """Test flood nowcasting."""
    print("\n" + "="*60)
    print("Testing Nowcasting Endpoint")
    print("="*60)
    
    # Example: Water level rising over past 30 minutes
    base_time = datetime.now()
    historical_readings = [
        {
            "water_level_cm": 20.0,
            "timestamp": (base_time - timedelta(minutes=30)).isoformat() + "Z"
        },
        {
            "water_level_cm": 35.0,
            "timestamp": (base_time - timedelta(minutes=20)).isoformat() + "Z"
        },
        {
            "water_level_cm": 50.0,
            "timestamp": (base_time - timedelta(minutes=10)).isoformat() + "Z"
        },
        {
            "water_level_cm": 65.0,
            "timestamp": base_time.isoformat() + "Z"
        }
    ]
    
    payload = {
        "device_id": "ESP32_001",
        "historical_readings": historical_readings,
        "forecast_minutes": 30
    }
    
    print(f"Device ID: {payload['device_id']}")
    print(f"Historical Readings: {len(historical_readings)} data points")
    print(f"Forecast Horizon: {payload['forecast_minutes']} minutes")
    
    response = requests.post(f"{API_URL}/api/v1/predict/nowcast", json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Trend: {result['trend'].upper()}")
        if result['predicted_water_level_cm']:
            print(f"Predicted Water Level: {result['predicted_water_level_cm']:.2f} cm")
            print(f"Forecast Timestamp: {result['forecast_timestamp']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Model Version: {result['model_version']}")
    else:
        print(f"Error: {response.json()}")
    
    return response.status_code == 200


def test_anomaly_detection():
    """Test anomaly detection."""
    print("\n" + "="*60)
    print("Testing Anomaly Detection Endpoint")
    print("="*60)
    
    # Example 1: Normal reading
    print("\n--- Test 1: Normal Sensor Reading ---")
    payload = {
        "device_id": "ESP32_001",
        "water_level_cm": 30.0,
        "temperature": 28.5,
        "humidity": 75,
        "battery_voltage": 3.8,
        "historical_mean": 28.0,
        "historical_std": 5.0
    }
    
    response = requests.post(f"{API_URL}/api/v1/detect/anomaly", json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Is Anomaly: {result['is_anomaly']}")
        print(f"Anomaly Score: {result['anomaly_score']:.2f}")
        print(f"Anomaly Types: {', '.join(result['anomaly_types']) if result['anomaly_types'] else 'None'}")
        print(f"Confidence: {result['confidence']:.2f}")
    
    # Example 2: Anomalous reading (negative value)
    print("\n--- Test 2: Anomalous Reading (Negative Value) ---")
    payload = {
        "device_id": "ESP32_002",
        "water_level_cm": -5.0,
        "temperature": 28.0,
        "humidity": 70
    }
    
    response = requests.post(f"{API_URL}/api/v1/detect/anomaly", json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Is Anomaly: {result['is_anomaly']}")
        print(f"Anomaly Score: {result['anomaly_score']:.2f}")
        print(f"Anomaly Types: {', '.join(result['anomaly_types'])}")
        print(f"Confidence: {result['confidence']:.2f}")
    
    # Example 3: Battery anomaly
    print("\n--- Test 3: Low Battery Alert ---")
    payload = {
        "device_id": "ESP32_003",
        "water_level_cm": 35.0,
        "temperature": 28.0,
        "humidity": 75,
        "battery_voltage": 2.0  # Low battery
    }
    
    response = requests.post(f"{API_URL}/api/v1/detect/anomaly", json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Is Anomaly: {result['is_anomaly']}")
        print(f"Anomaly Score: {result['anomaly_score']:.2f}")
        print(f"Anomaly Types: {', '.join(result['anomaly_types'])}")
        print(f"Confidence: {result['confidence']:.2f}")
    
    return True


def main():
    """Run all example tests."""
    print("\n" + "="*60)
    print("FloodGuard AI Microservice - API Examples")
    print("="*60)
    print("\nMake sure the API server is running:")
    print("  cd /workspaces/Guardy/ai-microservice")
    print("  source venv/bin/activate")
    print("  python -m uvicorn app.main:app --reload")
    print("\nThen run this script in another terminal.")
    
    try:
        # Test endpoints
        if test_health_check():
            print("\n✅ Health check passed")
        
        if test_risk_prediction():
            print("\n✅ Risk prediction passed")
        
        if test_nowcasting():
            print("\n✅ Nowcasting passed")
        
        if test_anomaly_detection():
            print("\n✅ Anomaly detection passed")
        
        print("\n" + "="*60)
        print("All API tests completed successfully!")
        print("="*60)
        print("\nNext steps:")
        print("  1. Review the API responses")
        print("  2. Test with your own data")
        print("  3. Integrate with frontend (CORS already configured)")
        print("  4. Check /docs for interactive API documentation")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
