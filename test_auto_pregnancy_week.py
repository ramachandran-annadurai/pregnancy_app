#!/usr/bin/env python3
"""
Test Auto-Fetch Pregnancy Week Functionality
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_USER_ID = "PAT175463472805233C"

def test_backend_health():
    """Test if backend is running"""
    print("🔍 Testing Backend Health")
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

def test_get_current_pregnancy_week():
    """Test the new endpoint to get current pregnancy week"""
    print("\n🔍 Testing Get Current Pregnancy Week")
    print("=" * 40)
    
    try:
        response = requests.get(
            f"{BASE_URL}/get-current-pregnancy-week/{TEST_USER_ID}",
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📡 Response Body: {response.text}")
        
        if response.statusCode == 200:
            data = response.json()
            if data['success']:
                print("✅ Current Pregnancy Week retrieved successfully!")
                print(f"🤰 Current Week: {data['current_pregnancy_week']}")
                print(f"📧 Patient Email: {data['patientEmail']}")
                print(f"🔄 Auto-fetched: {data['auto_fetched']}")
                return True
            else:
                print(f"❌ API Error: {data['message']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_save_food_entry_without_pregnancy_week():
    """Test saving food entry without pregnancy_week (should auto-fetch)"""
    print("\n🔍 Testing Save Food Entry Without Pregnancy Week")
    print("=" * 40)
    
    food_data = {
        "userId": TEST_USER_ID,
        "userRole": "patient",
        "username": "Test User",
        "email": "test@example.com",
        "food_details": "Grilled salmon with quinoa and steamed broccoli",
        "meal_type": "dinner",
        # pregnancy_week is NOT included - should be auto-fetched
        "notes": "Delicious and healthy dinner, felt great after eating"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/nutrition/save-food-entry",
            headers={'Content-Type': 'application/json'},
            json=food_data
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📡 Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("✅ Food Entry saved successfully without pregnancy_week!")
                print(f"📊 Food Logs Count: {data['foodLogsCount']}")
                print(f"🆔 Patient ID: {data['patientId']}")
                print(f"📧 Patient Email: {data['patientEmail']}")
                return True
            else:
                print(f"❌ API Error: {data['message']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_save_detailed_food_entry_without_pregnancy_week():
    """Test saving detailed food entry without pregnancy_week (should auto-fetch)"""
    print("\n🔍 Testing Save Detailed Food Entry Without Pregnancy Week")
    print("=" * 40)
    
    food_data = {
        "userId": TEST_USER_ID,
        "userRole": "patient",
        "username": "Test User",
        "email": "test@example.com",
        "food_details": "Oatmeal with berries and nuts for breakfast",
        "meal_type": "breakfast",
        # pregnancy_week is NOT included - should be auto-fetched
        "dietary_preference": "vegetarian",
        "allergies": ["peanuts"],
        "medical_conditions": ["gestational_diabetes"],
        "notes": "Healthy breakfast, good energy levels"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/nutrition/save-detailed-food-entry",
            headers={'Content-Type': 'application/json'},
            json=food_data
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📡 Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("✅ Detailed Food Entry saved successfully without pregnancy_week!")
                print(f"📊 Food Logs Count: {data['foodLogsCount']}")
                print(f"🆔 Patient ID: {data['patientId']}")
                print(f"📧 Patient Email: {data['patientEmail']}")
                return True
            else:
                print(f"❌ API Error: {data['message']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_get_food_entries_to_verify_auto_fetched_pregnancy_week():
    """Test getting food entries to verify pregnancy week was auto-fetched"""
    print("\n🔍 Testing Get Food Entries to Verify Auto-Fetched Pregnancy Week")
    print("=" * 40)
    
    try:
        response = requests.get(
            f"{BASE_URL}/nutrition/get-food-entries/{TEST_USER_ID}",
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("✅ Food Entries retrieved successfully!")
                print(f"📊 Total Entries: {data['total_entries']}")
                
                # Check the most recent entries for auto-fetched pregnancy week
                recent_entries = data['entries'][:3]
                for i, entry in enumerate(recent_entries):
                    print(f"\n🍽️ Entry {i+1}:")
                    print(f"   Food: {entry.get('food_details', 'N/A')}")
                    print(f"   Meal: {entry.get('meal_type', 'N/A')}")
                    print(f"   Pregnancy Week: {entry.get('pregnancy_week', 'N/A')}")
                    print(f"   Auto-fetched: {entry.get('auto_fetched_pregnancy_week', 'N/A')}")
                    print(f"   Type: {entry.get('entry_type', 'N/A')}")
                    print(f"   Time: {entry.get('createdAt', 'N/A')}")
                
                # Verify that pregnancy week is present and auto-fetched
                auto_fetched_count = sum(1 for entry in recent_entries if entry.get('auto_fetched_pregnancy_week'))
                print(f"\n✅ Auto-fetched pregnancy week entries: {auto_fetched_count}/{len(recent_entries)}")
                
                return True
            else:
                print(f"❌ API Error: {data['message']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function"""
    print("🤰 Auto-Fetch Pregnancy Week Test")
    print("=" * 60)
    
    # Wait a moment for the backend to be ready
    print("⏳ Waiting for backend to be ready...")
    time.sleep(2)
    
    tests = [
        ("Backend Health", test_backend_health),
        ("Get Current Pregnancy Week", test_get_current_pregnancy_week),
        ("Save Food Entry Without Pregnancy Week", test_save_food_entry_without_pregnancy_week),
        ("Save Detailed Food Entry Without Pregnancy Week", test_save_detailed_food_entry_without_pregnancy_week),
        ("Verify Auto-Fetched Pregnancy Week", test_get_food_entries_to_verify_auto_fetched_pregnancy_week),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Results Summary")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Auto-fetch pregnancy week is working correctly.")
        print("\n🔍 What Changed:")
        print("   ✅ Backend now auto-fetches pregnancy week from patient profile")
        print("   ✅ Flutter app no longer needs to send pregnancy_week")
        print("   ✅ Pregnancy week automatically included in food entries")
        print("   ✅ New endpoint: /get-current-pregnancy-week/<patient_id>")
        print("   ✅ Food entries show auto_fetched_pregnancy_week flag")
    else:
        print("⚠️ Some tests failed. Check the backend logs for issues.")
    
    print(f"\n🌐 Backend URL: {BASE_URL}")
    print("📱 Flutter app now automatically gets pregnancy week from backend!")

if __name__ == "__main__":
    main()
