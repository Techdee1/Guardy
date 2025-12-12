"""
Automated test for model management endpoints (non-interactive).

This script runs all model management tests without user prompts.
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
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        return False


def test_model_metadata():
    """Test individual model metadata endpoint."""
    print("\n" + "="*70)
    print("TEST 2: Get Model Metadata")
    print("="*70)
    
    model_names = ["risk_scorer", "nowcaster", "anomaly_detector"]
    success_count = 0
    
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
            
            success_count += 1
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
    
    print(f"\n✅ Metadata retrieval complete! ({success_count}/{len(model_names)} successful)")
    return success_count == len(model_names)


def test_model_stats():
    """Test model statistics endpoint."""
    print("\n" + "="*70)
    print("TEST 3: Get Model Statistics")
    print("="*70)
    
    model_names = ["risk_scorer", "nowcaster", "anomaly_detector"]
    success_count = 0
    
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
            
            success_count += 1
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error for {model_name}: {e}")
    
    print(f"\n✅ Statistics retrieval complete! ({success_count}/{len(model_names)} successful)")
    return success_count == len(model_names)


def test_clear_cache():
    """Test cache clearing endpoint (placeholder)."""
    print("\n" + "="*70)
    print("TEST 4: Clear Model Cache")
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
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        return False


def test_invalid_model():
    """Test error handling for invalid model name."""
    print("\n" + "="*70)
    print("TEST 5: Error Handling (Invalid Model)")
    print("="*70)
    
    invalid_model = "invalid_model_123"
    
    try:
        print(f"\nTrying to get metadata for '{invalid_model}'...")
        response = requests.get(f"{BASE_URL}/{invalid_model}/metadata")
        response.raise_for_status()
        print(f"❌ Should have gotten 404 error!")
        return False
        
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
            print(f"✅ Got expected 404 error!")
            error_data = e.response.json()
            print(f"Error: {error_data['detail']['error']}")
            print(f"Message: {error_data['detail']['message']}")
            return True
        else:
            print(f"❌ Unexpected error: {e}")
            return False


def test_reload_single_model():
    """Test reloading a single model (automated - risk_scorer)."""
    print("\n" + "="*70)
    print("TEST 6: Reload Single Model (Automated)")
    print("="*70)
    
    model_name = "risk_scorer"
    
    try:
        print(f"\n🔄 Reloading {model_name}...")
        response = requests.post(f"{BASE_URL}/{model_name}/reload")
        response.raise_for_status()
        
        result = response.json()
        
        print(f"\nStatus: {result['status'].upper()}")
        print(f"Message: {result['message']}")
        print(f"Reload Time: {result['reload_time_seconds']:.2f}s")
        
        print(f"\n✅ {model_name} reloaded successfully!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False


def main():
    """Run all model management tests."""
    print("\n" + "="*70)
    print("GUARDY AI - MODEL MANAGEMENT API TESTS (AUTOMATED)")
    print("="*70)
    print(f"\nBase URL: {BASE_URL}")
    print("Testing all endpoints automatically...\n")
    
    results = {
        "System Status": test_models_status(),
        "Model Metadata": test_model_metadata(),
        "Model Statistics": test_model_stats(),
        "Cache Clearing": test_clear_cache(),
        "Error Handling": test_invalid_model(),
        "Model Reload": test_reload_single_model(),
    }
    
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print(f"\n{'='*70}")
    print(f"TOTAL: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    print(f"{'='*70}")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed")
    
    print("\n💡 TIP: Use these endpoints to monitor model health in production")
    print("   and hot-reload models when deploying new versions!\n")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
