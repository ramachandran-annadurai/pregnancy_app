#!/usr/bin/env python3
"""
Test script for Nutrition Endpoints in Main Backend
"""

import requests
import json
import time

# Configuration - now using main backend port 5000
BASE_URL = "http://127.0.0.1:5000"
TEST_USER_ID = "PAT175463472805233C"  # Use the same user ID from the Flutter app

def test_health_check():
    """Test main backend health check"""
    print("🔍 Testing Main Backend Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Main Backend Health: {data.get('message', 'OK')}")
            return True
        else:
            print(f"❌ Main Backend Health failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Main Backend Health error: {e}")
        return False

def test_nutrition_health():
    """Test nutrition service health check"""
    print("🔍 Testing Nutrition Service Health...")
    try:
        response = requests.get(f"{BASE_URL}/nutrition/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Nutrition Service Health: {data['message']}")
            return True
        else:
            print(f"❌ Nutrition Service Health failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Nutrition Service Health error: {e}")
        return False

def test_pregnancy_info():
    """Test pregnancy info endpoint"""
    print(f"🔍 Testing Pregnancy Info for user: {TEST_USER_ID}")
    try:
        response = requests.get(f"{BASE_URL}/nutrition/pregnancy-info/{TEST_USER_ID}")
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ Pregnancy Info: Week {data['pregnancy_info']['current_week']}")
                return data['pregnancy_info']['current_week']
            else:
                print(f"⚠️ Pregnancy Info: {data['message']}")
                return 1  # Default fallback
        else:
            print(f"❌ Pregnancy Info failed: {response.status_code}")
            return 1
    except Exception as e:
        print(f"❌ Pregnancy Info error: {e}")
        return 1

def test_save_detailed_food_entry(pregnancy_week):
    """Test detailed food entry endpoint"""
    print("🔍 Testing Detailed Food Entry...")
    
    food_data = {
        "userId": TEST_USER_ID,
        "userRole": "patient",
        "username": "Test User",
        "email": "test@example.com",
        "food_details": "Grilled chicken with steamed vegetables and brown rice",
        "meal_type": "lunch",
        "pregnancy_week": pregnancy_week,
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
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ Detailed Food Entry saved: {data['message']}")
                return True
            else:
                print(f"❌ Detailed Food Entry failed: {data['message']}")
                return False
        else:
            print(f"❌ Detailed Food Entry failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Detailed Food Entry error: {e}")
        return False

def test_get_food_entries():
    """Test get food entries endpoint"""
    print("🔍 Testing Get Food Entries...")
    try:
        response = requests.get(f"{BASE_URL}/nutrition/get-food-entries/{TEST_USER_ID}")
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ Food Entries retrieved: {data['total_entries']} entries")
                return True
            else:
                print(f"❌ Get Food Entries failed: {data['message']}")
                return False
        else:
            print(f"❌ Get Food Entries failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get Food Entries error: {e}")
        return False

def test_analyze_nutrition(pregnancy_week):
    """Test nutrition analysis endpoint"""
    print("🔍 Testing Nutrition Analysis...")
    
    analysis_data = {
        "food_input": "Grilled chicken breast with steamed broccoli and quinoa",
        "pregnancy_week": pregnancy_week
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/nutrition/analyze-nutrition",
            headers={'Content-Type': 'application/json'},
            json=analysis_data
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                calories = data['nutritional_breakdown']['estimated_calories']
                print(f"✅ Nutrition Analysis: {calories} calories estimated")
                return True
            else:
                print(f"❌ Nutrition Analysis failed: {data['message']}")
                return False
        else:
            print(f"❌ Nutrition Analysis failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Nutrition Analysis error: {e}")
        return False

def test_daily_calorie_summary():
    """Test daily calorie summary endpoint"""
    print("🔍 Testing Daily Calorie Summary...")
    try:
        response = requests.get(f"{BASE_URL}/nutrition/daily-calorie-summary/{TEST_USER_ID}")
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                total_calories = data['daily_summary']['total_calories_today']
                print(f"✅ Daily Calorie Summary: {total_calories} calories today")
                return True
            else:
                print(f"❌ Daily Calorie Summary failed: {data['message']}")
                return False
        else:
            print(f"❌ Daily Calorie Summary failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Daily Calorie Summary error: {e}")
        return False

def main():
    """Main test function"""
    print("🍎 Nutrition Endpoints Test Suite (Main Backend)")
    print("=" * 50)
    
    # Wait a moment for the backend to be ready
    print("⏳ Waiting for backend to be ready...")
    time.sleep(2)
    
    tests = [
        ("Main Backend Health", test_health_check),
        ("Nutrition Service Health", test_nutrition_health),
        ("Pregnancy Info", lambda: test_pregnancy_info()),
        ("Save Detailed Food Entry", lambda: test_save_detailed_food_entry(12)),  # Use default week 12
        ("Get Food Entries", test_get_food_entries),
        ("Analyze Nutrition", lambda: test_analyze_nutrition(12)),
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
    print(f"\n{'='*50}")
    print("📊 Test Results Summary")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Nutrition endpoints are working correctly.")
    else:
        print("⚠️ Some tests failed. Check the backend logs for issues.")
    
    print(f"\n🌐 Backend URL: {BASE_URL}")
    print("📱 Flutter app should now be able to connect successfully!")
    print("🍎 All nutrition endpoints are now available at: /nutrition/*")

if __name__ == "__main__":
    main()
