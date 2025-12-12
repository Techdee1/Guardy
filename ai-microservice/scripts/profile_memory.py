"""
Memory profiling script for identifying memory leaks and optimization opportunities.

Usage:
    python scripts/profile_memory.py
"""

import asyncio
import time
from memory_profiler import profile
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, '/workspaces/Guardy/ai-microservice')

from app.ml import FloodRiskScorer, FloodNowcaster, SensorAnomalyDetector


@profile
def profile_flood_risk_scorer():
    """Profile FloodRiskScorer memory usage."""
    print("\n=== Profiling FloodRiskScorer ===")
    
    # Load model
    model = FloodRiskScorer.load("models/flood_risk_scorer_v1.pkl")
    
    # Generate test data
    test_data = pd.DataFrame({
        'latitude': np.random.uniform(8, 10, 1000),
        'longitude': np.random.uniform(7, 9, 1000),
        'rainfall_mm': np.random.uniform(0, 200, 1000),
        'temperature': np.random.uniform(20, 35, 1000),
        'humidity': np.random.uniform(40, 100, 1000),
        'date': np.random.randint(1, 29, 1000),
        'month': np.random.randint(1, 13, 1000),
        'day_of_year': np.random.randint(1, 366, 1000)
    })
    
    # Run predictions
    for i in range(10):
        result = model.predict_risk_score(test_data.iloc[[i]])
        print(f"Prediction {i+1}: {result['risk_scores'][0]:.4f}")
    
    print("✅ FloodRiskScorer profiling complete")


@profile
def profile_flood_nowcaster():
    """Profile FloodNowcaster memory usage."""
    print("\n=== Profiling FloodNowcaster ===")
    
    # Load model
    model = FloodNowcaster.load("models/nowcast_lstm_v1.h5")
    
    # Generate test sequences
    for i in range(10):
        sequence = np.random.rand(7, 3).astype(np.float32)
        result = model.predict_nowcast(sequence, hours_ahead=[1, 6, 24])
        print(f"Nowcast {i+1}: {list(result.keys())}")
    
    print("✅ FloodNowcaster profiling complete")


@profile
def profile_anomaly_detector():
    """Profile SensorAnomalyDetector memory usage."""
    print("\n=== Profiling SensorAnomalyDetector ===")
    
    # Load model
    model = SensorAnomalyDetector.load("models/anomaly_detector_v1.pkl")
    
    # Generate test data
    test_data = pd.DataFrame({
        'water_level_cm': np.random.uniform(50, 200, 100),
        'rainfall_mm': np.random.uniform(0, 50, 100),
        'temperature': np.random.uniform(20, 35, 100),
        'humidity': np.random.uniform(50, 85, 100),
        'battery_voltage': np.random.uniform(3.5, 4.2, 100),
        'signal_strength': np.random.uniform(-85, -50, 100)
    })
    
    # Run predictions
    for i in range(10):
        result = model.detect_anomaly(test_data.iloc[[i]])
        print(f"Anomaly detection {i+1}: {result['is_anomaly'][0]}")
    
    print("✅ SensorAnomalyDetector profiling complete")


@profile
def profile_batch_processing():
    """Profile batch prediction memory usage."""
    print("\n=== Profiling Batch Processing ===")
    
    model = FloodRiskScorer.load("models/flood_risk_scorer_v1.pkl")
    
    # Generate large batch
    batch_sizes = [10, 50, 100, 500]
    
    for batch_size in batch_sizes:
        test_data = pd.DataFrame({
            'latitude': np.random.uniform(8, 10, batch_size),
            'longitude': np.random.uniform(7, 9, batch_size),
            'rainfall_mm': np.random.uniform(0, 200, batch_size),
            'temperature': np.random.uniform(20, 35, batch_size),
            'humidity': np.random.uniform(40, 100, batch_size),
            'date': np.random.randint(1, 29, batch_size),
            'month': np.random.randint(1, 13, batch_size),
            'day_of_year': np.random.randint(1, 366, batch_size)
        })
        
        start_time = time.time()
        result = model.predict_risk_score(test_data)
        elapsed = time.time() - start_time
        
        print(f"Batch size {batch_size}: {elapsed:.4f}s ({elapsed/batch_size*1000:.2f}ms per prediction)")
    
    print("✅ Batch processing profiling complete")


if __name__ == "__main__":
    print("🔍 Starting memory profiling...")
    print("=" * 60)
    
    profile_flood_risk_scorer()
    profile_flood_nowcaster()
    profile_anomaly_detector()
    profile_batch_processing()
    
    print("\n" + "=" * 60)
    print("✅ Memory profiling complete!")
    print("\nTo view detailed line-by-line memory usage:")
    print("  mprof run python scripts/profile_memory.py")
    print("  mprof plot")
