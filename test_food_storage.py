#!/usr/bin/env python3
"""
Test Food Storage System - Now stores within patient documents like sleep and kick logs
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

def test_save_detailed_food_entry():
    """Test saving detailed food entry (now stored within patient document)"""
    print("\n🔍 Testing Save Detailed Food Entry")
    print("=" * 40)
    
    food_data = {
        "userId": TEST_USER_ID,
        "userRole": "patient",
        "username": "Test User",
        "email": "test@example.com",
        "food_details": "Grilled chicken with steamed vegetables and brown rice",
        "meal_type": "lunch",
        "pregnancy_week": 12,
        "dietary_preference": "non-vegetarian",
        "allergies": ["nuts", "shellfish"],
        "medical_conditions": ["diabetes", "hypertension"],
        "notes": "Felt good after this meal, good energy levels"
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
                print("✅ Detailed Food Entry saved successfully!")
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

def test_save_basic_food_entry():
    """Test saving basic food entry (now stored within patient document)"""
    print("\n🔍 Testing Save Basic Food Entry")
    print("=" * 40)
    
    food_data = {
        "userId": TEST_USER_ID,
        "userRole": "patient",
        "username": "Test User",
        "email": "test@example.com",
        "food_details": "Apple and yogurt for breakfast",
        "meal_type": "breakfast",
        "pregnancy_week": 12,
        "notes": "Light breakfast, felt good"
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
                print("✅ Basic Food Entry saved successfully!")
                print(f"📊 Food Logs Count: {data['foodLogsCount']}")
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

def test_get_food_entries():
    """Test getting food entries from patient document"""
    print("\n🔍 Testing Get Food Entries")
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
                
                # Show first few entries
                for i, entry in enumerate(data['entries'][:3]):
                    print(f"\n🍽️ Entry {i+1}:")
                    print(f"   Food: {entry.get('food_details', 'N/A')}")
                    print(f"   Meal: {entry.get('meal_type', 'N/A')}")
                    print(f"   Week: {entry.get('pregnancy_week', 'N/A')}")
                    print(f"   Type: {entry.get('entry_type', 'N/A')}")
                    print(f"   Time: {entry.get('createdAt', 'N/A')}")
                
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

def test_get_food_history():
    """Test getting food history using new endpoint"""
    print("\n🔍 Testing Get Food History")
    print("=" * 40)
    
    try:
        response = requests.get(
            f"{BASE_URL}/get-food-history/{TEST_USER_ID}",
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("✅ Food History retrieved successfully!")
                print(f"📊 Total Entries: {data['totalEntries']}")
                print(f"🆔 Patient ID: {data['patientId']}")
                
                # Show first few entries
                for i, entry in enumerate(data['food_logs'][:3]):
                    print(f"\n🍽️ Entry {i+1}:")
                    print(f"   Food: {entry.get('food_details', 'N/A')}")
                    print(f"   Meal: {entry.get('meal_type', 'N/A')}")
                    print(f"   Week: {entry.get('pregnancy_week', 'N/A')}")
                    print(f"   Type: {entry.get('entry_type', 'N/A')}")
                    print(f"   Time: {entry.get('createdAt', 'N/A')}")
                
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

def test_daily_calorie_summary():
    """Test daily calorie summary with new food logs structure"""
    print("\n🔍 Testing Daily Calorie Summary")
    print("=" * 40)
    
    try:
        response = requests.get(
            f"{BASE_URL}/nutrition/daily-calorie-summary/{TEST_USER_ID}",
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("✅ Daily Calorie Summary retrieved successfully!")
                daily_summary = data['daily_summary']
                print(f"📊 Meals Eaten Today: {daily_summary['meals_eaten_today']}")
                print(f"🔥 Total Calories: {daily_summary['total_calories_today']}")
                print(f"🥩 Total Protein: {daily_summary['total_protein_today']}g")
                print(f"🍞 Total Carbs: {daily_summary['total_carbs_today']}g")
                print(f"🧈 Total Fat: {daily_summary['total_fat_today']}g")
                
                calorie_recs = data['calorie_recommendations']
                print(f"📅 Recommended Calories: {calorie_recs['recommended_daily_calories']}")
                print(f"⚖️ Calories Remaining: {calorie_recs['calories_remaining']}")
                print(f"🍽️ Meals Remaining: {calorie_recs['meals_remaining']}")
                
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
    print("🍎 Food Storage System Test - Now Stored Within Patient Documents")
    print("=" * 70)
    
    # Wait a moment for the backend to be ready
    print("⏳ Waiting for backend to be ready...")
    time.sleep(2)
    
    tests = [
        ("Backend Health", test_backend_health),
        ("Save Detailed Food Entry", test_save_detailed_food_entry),
        ("Save Basic Food Entry", test_save_basic_food_entry),
        ("Get Food Entries", test_get_food_entries),
        ("Get Food History", test_get_food_history),
        ("Daily Calorie Summary", test_daily_calorie_summary),
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
    print(f"\n{'='*70}")
    print("📊 Test Results Summary")
    print("="*70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Food storage system is working correctly.")
        print("\n🔍 What Changed:")
        print("   ✅ Food entries now stored within patient documents (like sleep/kick logs)")
        print("   ✅ No separate food_entries collection needed")
        print("   ✅ Uses $push to add entries to food_logs array")
        print("   ✅ Consistent with existing sleep and kick log patterns")
        print("   ✅ Better data organization and patient linking")
    else:
        print("⚠️ Some tests failed. Check the backend logs for issues.")
    
    print(f"\n🌐 Backend URL: {BASE_URL}")
    print("📱 Flutter app now stores food details in backend like sleep and kick logs!")

if __name__ == "__main__":
    main()
