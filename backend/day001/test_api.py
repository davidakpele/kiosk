#!/usr/bin/env python3
"""
Test all API endpoints
"""
import requests

BASE_URL = "http://localhost:8000"

def test_endpoint(url, description):
    try:
        response = requests.get(url)
        print(f"✅ {description}: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ {description}: {e}")
        return False

print("🧪 Testing API endpoints...")

endpoints = [
    (f"{BASE_URL}/", "Root endpoint"),
    (f"{BASE_URL}/health", "Health check"),
    (f"{BASE_URL}/doctors/", "All doctors"),
    (f"{BASE_URL}/doctors/1", "Doctor by ID"),
    (f"{BASE_URL}/doctors/specialty/Cardiologist", "Doctors by specialty"),
]

all_passed = all(test_endpoint(url, desc) for url, desc in endpoints)

if all_passed:
    print("🎉 All endpoints working correctly!")
else:
    print("💥 Some endpoints failed")