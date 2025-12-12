"""
Test model management endpoints.

This script demonstrates how to use the model management API endpoints
for monitoring, reloading, and managing ML models.

Requires a running FastAPI server at http://localhost:8000
"""

import requests
import json


BASE_URL = "http://localhost:8000/api/v1/models"


def test_models_status():
    """Test comprehensive models status endpoint."""
    print("\n" + "="*70)
    print("TEST 1: Get Models Status")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/status")
        response.raise_for_status()
        
        result = response.json()
        
        print(f"\nSystem Status: {result['system_status'].upper()}")
        print(f"All Models Loaded: {result['all_models_loaded']}")
        print(f"Total Predictions: {result['total_predictions']:,}")
        print(f"Load Time: {result['load_time_seconds']:.2f}s")
        
        print(f"\n{'='*70}")
        print("MODEL DETAILS:")
        print(f"{'='*70}")
        
        for model_key, model_info in result['models'].items():
            status_emoji = "✅" if model_info['status'] == "operational" else "❌"
            print(f"\n{status_emoji} {model_info['name']} ({model_key})")
            print(f"   Version: {model_info['version']}")
            print(f"   Algorithm: {model_info['algorithm']}")
            print(f"   Accuracy: {model_info['accuracy']:.2%}")
            print(f"   Training Samples: {model_info['training_samples']:,}")
            print(f"   Features: {model_info['features']}")
            print(f"   File Size: {model_info['file_size_mb']:.2f} MB")
            print(f"   Status: {model_info['status']}")
            print(f"   Predictions: {model_info['prediction_count']:,}")
            if model_info.get('last_prediction'):
                print(f"   Last Prediction: {model_info['last_prediction']}")
        
        print(f"\n✅ Status check complete!")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")


def test_model_metadata():
    """Test individual model metadata endpoint."""
    print("\n" + "="*70)
    print("TEST 2: Get Model Metadata")
    print("="*70)
    
    model_names = ["risk_scorer", "nowcaster", "anomaly_detector"]
    
    for model_name in model_names:
        print(f"\n--- {model_name} ---")
        
        try:
            response = requests.get(f"{BASE_URL}/{model_name}/metadata")
            response.raise_for_status()
            
            result = response.json()
            
            print(f"Name: {result['name']}")
            print(f"Version: {result['version']}")
            print(f"Algorithm: {result['algorithm']}")
            print(f"Trained: {result['trained_date']}")
            print(f"Accuracy: {result['accuracy']:.2%}")
            print(f"Training Samples: {result['training_samples']:,}")
            print(f"File: {result['file_path']} ({result['file_size_mb']:.2f} MB)")
            print(f"Loaded: {result['is_loaded']}")
            print(f"Predictions: {result['prediction_count']}")
            
            if result.get('feature_importance'):
                print(f"Feature Importance: {len(result['feature_importance'])} features")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
    
    print(f"\n✅ Metadata retrieval complete!")


def test_model_stats():
    """Test model statistics endpoint."""
    print("\n" + "="*70)
    print("TEST 3: Get Model Statistics")
    print("="*70)
    
    model_names = ["risk_scorer", "nowcaster", "anomaly_detector"]
    
    for model_name in model_names:
        try:
            response = requests.get(f"{BASE_URL}/{model_name}/stats")
            response.raise_for_status()
            
            result = response.json()
            
            print(f"\n{result['model_name']}:")
            print(f"  Total Predictions: {result['total_predictions']:,}")
            print(f"  Predictions/min: {result['predictions_per_minute']:.2f}")
            print(f"  Uptime: {result['uptime_seconds']:.2f}s")
            print(f"  Last Prediction: {result.get('last_prediction', 'Never')}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error for {model_name}: {e}")
    
    print(f"\n✅ Statistics retrieval complete!")


def test_reload_all_models():
    """Test reloading all models."""
    print("\n" + "="*70)
    print("TEST 4: Reload All Models")
    print("="*70)
    
    print("\n⚠️  WARNING: This will reload all models from disk.")
    print("   This may cause brief service interruption.")
    
    user_input = input("\nProceed with reload? (yes/no): ")
    
    if user_input.lower() != 'yes':
        print("Reload cancelled.")
        return
    
    try:
        print("\n🔄 Initiating model reload...")
        response = requests.post(f"{BASE_URL}/reload")
        response.raise_for_status()
        
        result = response.json()
        
        print(f"\nStatus: {result['status'].upper()}")
        print(f"Message: {result['message']}")
        print(f"Reload Time: {result['reload_time_seconds']:.2f}s")
        print(f"All Models Loaded: {result['all_models_loaded']}")
        
        print(f"\n{'='*70}")
        print("RELOAD RESULTS:")
        print(f"{'='*70}")
        
        for model_name, reload_info in result['reload_results'].items():
            status_emoji = "✅" if reload_info['status'] == "success" else "❌"
            print(f"{status_emoji} {model_name}: {reload_info['message']}")
        
        if result.get('errors'):
            print(f"\nErrors:")
            for error in result['errors']:
                print(f"  ❌ {error}")
        
        print(f"\n✅ Reload operation complete!")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")


def test_reload_single_model():
    """Test reloading a single model."""
    print("\n" + "="*70)
    print("TEST 5: Reload Single Model")
    print("="*70)
    
    print("\nAvailable models:")
    print("  1. risk_scorer")
    print("  2. nowcaster")
    print("  3. anomaly_detector")
    
    model_name = input("\nEnter model name (or 'skip' to skip): ")
    
    if model_name.lower() == 'skip':
        print("Reload cancelled.")
        return
    
    if model_name not in ["risk_scorer", "nowcaster", "anomaly_detector"]:
        print(f"❌ Invalid model name: {model_name}")
        return
    
    try:
        print(f"\n🔄 Reloading {model_name}...")
        response = requests.post(f"{BASE_URL}/{model_name}/reload")
        response.raise_for_status()
        
        result = response.json()
        
        print(f"\nStatus: {result['status'].upper()}")
        print(f"Message: {result['message']}")
        print(f"Reload Time: {result['reload_time_seconds']:.2f}s")
        
        print(f"\n✅ {model_name} reloaded successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")


def test_clear_cache():
    """Test cache clearing endpoint (placeholder)."""
    print("\n" + "="*70)
    print("TEST 6: Clear Model Cache")
    print("="*70)
    
    print("\nNote: This is a placeholder endpoint (Task 11: Performance Optimization)")
    
    model_name = "risk_scorer"
    
    try:
        response = requests.delete(f"{BASE_URL}/{model_name}/cache")
        response.raise_for_status()
        
        result = response.json()
        
        print(f"\nStatus: {result['status']}")
        print(f"Message: {result['message']}")
        print(f"Items Cleared: {result['cached_items_cleared']}")
        
        print(f"\n✅ Cache clearing tested (not yet implemented)!")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")


def test_invalid_model():
    """Test error handling for invalid model name."""
    print("\n" + "="*70)
    print("TEST 7: Error Handling (Invalid Model)")
    print("="*70)
    
    invalid_model = "invalid_model_123"
    
    try:
        print(f"\nTrying to get metadata for '{invalid_model}'...")
        response = requests.get(f"{BASE_URL}/{invalid_model}/metadata")
        response.raise_for_status()
        
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
            print(f"✅ Got expected 404 error!")
            error_data = e.response.json()
            print(f"Error: {error_data['detail']['error']}")
            print(f"Message: {error_data['detail']['message']}")
        else:
            print(f"❌ Unexpected error: {e}")


def main():
    """Run all model management tests."""
    print("\n" + "="*70)
    print("GUARDY AI - MODEL MANAGEMENT API TESTS")
    print("="*70)
    print(f"\nBase URL: {BASE_URL}")
    print("Make sure the API server is running: uvicorn app.main:app --reload")
    
    # Run all tests
    test_models_status()
    test_model_metadata()
    test_model_stats()
    test_invalid_model()
    test_clear_cache()
    
    # Interactive tests
    test_reload_all_models()
    test_reload_single_model()
    
    print("\n" + "="*70)
    print("ALL MODEL MANAGEMENT TESTS COMPLETED")
    print("="*70)
    print("\n💡 TIP: Use these endpoints to monitor model health in production")
    print("   and hot-reload models when deploying new versions!\n")


if __name__ == "__main__":
    main()
