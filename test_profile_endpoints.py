#!/usr/bin/env python3
"""
Test Patient Profile Endpoints
"""

import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_EMAIL = "malaravan.mainmaran.lm@gmail.com"
TEST_PATIENT_ID = "PAT175463472805233C"

def test_get_patient_profile_by_email():
    """Test getting patient profile by email"""
    print("🔍 Testing Get Patient Profile by Email")
    print("=" * 50)
    
    try:
        response = requests.get(
            f"{BASE_URL}/get-patient-profile-by-email/{TEST_EMAIL}",
            headers={'Content-Type': 'application/json'}
        )
        
        print(f" Response Status: {response.status_code}")
        print(f" Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("✅ Patient Profile retrieved successfully!")
                
                profile = data['profile']
                print(f"\n🔑 Key Information:")
                print(f"   🆔 Patient ID: {profile.get('patient_id', 'N/A')}")
                print(f"   Email ID: {profile.get('email', 'N/A')}")
                print(f"   📱 Mobile Number: {profile.get('mobile', 'N/A')}")
                print(f"   📅 Pregnancy Week: {profile.get('pregnancy_week', 'N/A')}")
                
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

def test_get_patient_profile_by_id():
    """Test getting patient profile by patient ID"""
    print("\n🔍 Testing Get Patient Profile by Patient ID")
    print("=" * 50)
    
    try:
        response = requests.get(
            f"{BASE_URL}/get-patient-profile/{TEST_PATIENT_ID}",
            headers={'Content-Type': 'application/json'}
        )
        
        print(f" Response Status: {response.status_code}")
        print(f" Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("✅ Patient Profile retrieved successfully!")
                
                profile = data['profile']
                print(f"\n🔑 Key Information:")
                print(f"   🆔 Patient ID: {profile.get('patient_id', 'N/A')}")
                print(f"   Email ID: {profile.get('email', 'N/A')}")
                print(f"   📱 Mobile Number: {profile.get('mobile', 'N/A')}")
                print(f"   📅 Pregnancy Week: {profile.get('pregnancy_week', 'N/A')}")
                
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
    print(" Patient Profile Endpoints Test")
    print("=" * 60)
    
    test_get_patient_profile_by_email()
    test_get_patient_profile_by_id()
    
    print("\n" + "=" * 60)
    print("📱 Flutter app will now show profile with key information!")

if __name__ == "__main__":
    main()
