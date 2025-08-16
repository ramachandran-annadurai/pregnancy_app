#!/usr/bin/env python3
"""
Test Pregnancy Week Endpoint
"""

import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_USER_ID = "PAT175463472805233C"

def test_pregnancy_week_endpoint():
    """Test the pregnancy week endpoint"""
    print("🔍 Testing Pregnancy Week Endpoint")
    print("=" * 40)
    
    try:
        # Test the endpoint
        response = requests.get(
            f"{BASE_URL}/nutrition/pregnancy-info/{TEST_USER_ID}",
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📡 Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("✅ Success!")
                if data['is_pregnant']:
                    pregnancy_info = data['pregnancy_info']
                    print(f"🤰 Pregnancy Week: {pregnancy_info['current_week']}")
                    print(f"📅 Trimester: {pregnancy_info['trimester']}")
                    print(f"📅 Expected Delivery: {pregnancy_info['expected_delivery_date']}")
                else:
                    print("❌ User is not pregnant")
            else:
                print(f"❌ API Error: {data['message']}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_backend_health():
    """Test if backend is running"""
    print("\n🔍 Testing Backend Health")
    print("=" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/nutrition/health")
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Pregnancy Week Endpoint Test")
    print("=" * 50)
    
    # First check if backend is running
    if test_backend_health():
        # Test pregnancy week endpoint
        test_pregnancy_week_endpoint()
    else:
        print("\n🚨 Please start the backend first:")
        print("   python app_simple.py")
    
    print("\n" + "=" * 50)
    print("📱 Flutter app will now automatically:")
    print("   ✅ Fetch pregnancy week from backend")
    print("   ✅ Display it in a beautiful read-only field")
    print("   ✅ Update when you refresh")
    print("   ✅ Use it for food tracking")
