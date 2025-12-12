"""
Test evacuation zone generation endpoint.

This script demonstrates how to generate evacuation zones based on flood risk predictions.
Requires a running FastAPI server at http://localhost:8000
"""

import requests
import json


BASE_URL = "http://localhost:8000/api/v1"


def test_evacuation_zones_basic():
    """Test basic evacuation zone generation."""
    print("\n" + "="*70)
    print("TEST 1: Basic Evacuation Zones (Default 3 Zones)")
    print("="*70)
    
    request_data = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "flood_probability": 0.75,
        "risk_level": "high",
        "location_name": "New Delhi",
        "population_density": 11320,
        "include_shelters": True
    }
    
    print("\nRequest:")
    print(f"  Location: {request_data['location_name']}")
    print(f"  Coordinates: ({request_data['latitude']}, {request_data['longitude']})")
    print(f"  Risk Level: {request_data['risk_level']}")
    print(f"  Flood Probability: {request_data['flood_probability']:.1%}")
    print(f"  Population Density: {request_data['population_density']:,} per km²")
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict/evacuation-zones",
            json=request_data
        )
        response.raise_for_status()
        
        result = response.json()
        
        print("\n" + "-"*70)
        print("RESPONSE:")
        print("-"*70)
        print(f"\nLocation: {result['location']}")
        print(f"Center Point: {result['center_point']}")
        print(f"Risk Level: {result['risk_level']}")
        print(f"Flood Probability: {result['flood_probability']:.1%}")
        
        print(f"\n📍 EVACUATION ZONES: {len(result['zones'])} zones")
        print("-"*70)
        for zone in result['zones']:
            print(f"\n🔴 Zone: {zone['zone_id']}")
            print(f"   Radius: {zone['radius_meters']}m")
            print(f"   Priority: {zone['priority'].upper()}")
            print(f"   Estimated Affected: {zone['estimated_affected']:,} people" if zone['estimated_affected'] else "   Estimated Affected: N/A")
            print(f"   Evacuation Time: {zone['evacuation_time_minutes']} minutes")
            print(f"   Routes: {', '.join(zone['recommended_routes'])}")
        
        if result.get('shelters'):
            print(f"\n🏠 EVACUATION SHELTERS: {len(result['shelters'])} shelters")
            print("-"*70)
            for shelter in result['shelters']:
                print(f"\n📌 {shelter['name']}")
                print(f"   Location: ({shelter['latitude']:.4f}, {shelter['longitude']:.4f})")
                print(f"   Capacity: {shelter['capacity']:,} people")
                print(f"   Distance: {shelter['distance_meters']:,.0f}m")
                print(f"   Resources: {', '.join(shelter['available_resources'])}")
                print(f"   Contact: {shelter['contact']}")
        
        print(f"\n🗺️  GeoJSON DATA:")
        print("-"*70)
        geojson = result['geojson']
        print(f"   Type: {geojson['type']}")
        print(f"   Features: {len(geojson['features'])}")
        
        # Count feature types
        zone_features = sum(1 for f in geojson['features'] if f['geometry']['type'] == 'Polygon')
        point_features = sum(1 for f in geojson['features'] if f['geometry']['type'] == 'Point')
        print(f"   - Zone Polygons: {zone_features}")
        print(f"   - Point Markers: {point_features}")
        
        print(f"\n✅ Evacuation zones generated successfully!")
        
        # Save GeoJSON to file for visualization
        with open('evacuation_zones.geojson', 'w') as f:
            json.dump(geojson, f, indent=2)
        print(f"\n💾 GeoJSON saved to: evacuation_zones.geojson")
        print("   (Can be visualized at: https://geojson.io)")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")


def test_evacuation_zones_extreme():
    """Test evacuation zones for extreme risk."""
    print("\n" + "="*70)
    print("TEST 2: Extreme Risk Evacuation Zones")
    print("="*70)
    
    request_data = {
        "latitude": 19.0760,
        "longitude": 72.8777,
        "flood_probability": 0.92,
        "risk_level": "extreme",
        "location_name": "Mumbai (Coastal Area)",
        "population_density": 27000,
        "include_shelters": True,
        "zone_radii": [300, 750, 1500, 3000]  # Custom radii
    }
    
    print(f"\nLocation: {request_data['location_name']}")
    print(f"Risk Level: {request_data['risk_level'].upper()}")
    print(f"Flood Probability: {request_data['flood_probability']:.1%}")
    print(f"Custom Zone Radii: {request_data['zone_radii']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict/evacuation-zones",
            json=request_data
        )
        response.raise_for_status()
        
        result = response.json()
        
        print(f"\n📍 EVACUATION ZONES: {len(result['zones'])} zones")
        for zone in result['zones']:
            print(f"   {zone['zone_id']:12s} | {zone['priority']:10s} | {zone['estimated_affected']:7,} people | {zone['evacuation_time_minutes']:3d} min")
        
        print(f"\n✅ Extreme risk zones generated!")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")


def test_evacuation_zones_no_shelters():
    """Test evacuation zones without shelter information."""
    print("\n" + "="*70)
    print("TEST 3: Evacuation Zones Without Shelters")
    print("="*70)
    
    request_data = {
        "latitude": 22.5726,
        "longitude": 88.3639,
        "flood_probability": 0.55,
        "risk_level": "moderate",
        "location_name": "Kolkata",
        "include_shelters": False,
        "zone_radii": [1000, 2000]
    }
    
    print(f"\nLocation: {request_data['location_name']}")
    print(f"Include Shelters: {request_data['include_shelters']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict/evacuation-zones",
            json=request_data
        )
        response.raise_for_status()
        
        result = response.json()
        
        print(f"\nZones Generated: {len(result['zones'])}")
        print(f"Shelters Included: {result['shelters'] is not None}")
        print(f"GeoJSON Features: {len(result['geojson']['features'])}")
        
        print(f"\n✅ Zones generated without shelter data!")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")


def test_evacuation_zones_low_density():
    """Test evacuation zones for low population density area."""
    print("\n" + "="*70)
    print("TEST 4: Low Density Area (Rural)")
    print("="*70)
    
    request_data = {
        "latitude": 26.9124,
        "longitude": 75.7873,
        "flood_probability": 0.65,
        "risk_level": "high",
        "location_name": "Jaipur (Rural Area)",
        "population_density": 500,  # Low density
        "include_shelters": True
    }
    
    print(f"\nLocation: {request_data['location_name']}")
    print(f"Population Density: {request_data['population_density']} per km² (Rural)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict/evacuation-zones",
            json=request_data
        )
        response.raise_for_status()
        
        result = response.json()
        
        print(f"\n📍 Zone Analysis:")
        for zone in result['zones']:
            print(f"   {zone['radius_meters']}m zone: {zone['estimated_affected'] or 'N/A'} people affected")
        
        print(f"\n✅ Rural area zones generated!")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")


def main():
    """Run all evacuation zone tests."""
    print("\n" + "="*70)
    print("GUARDY AI - EVACUATION ZONE GENERATION TESTS")
    print("="*70)
    print(f"\nBase URL: {BASE_URL}")
    print("Make sure the API server is running: uvicorn app.main:app --reload")
    
    # Run all tests
    test_evacuation_zones_basic()
    test_evacuation_zones_extreme()
    test_evacuation_zones_no_shelters()
    test_evacuation_zones_low_density()
    
    print("\n" + "="*70)
    print("ALL EVACUATION ZONE TESTS COMPLETED")
    print("="*70)
    print("\n💡 TIP: Open evacuation_zones.geojson at https://geojson.io")
    print("   to visualize the generated zones on a map!\n")


if __name__ == "__main__":
    main()
