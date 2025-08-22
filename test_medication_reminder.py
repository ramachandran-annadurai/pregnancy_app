#!/usr/bin/env python3
"""
Test script for medication reminder functionality
"""

import requests
import json
import time

def test_medication_reminder_endpoints():
    """Test the medication reminder endpoints"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Testing Medication Reminder Endpoints")
    print("=" * 50)
    
    # Test 1: Send reminders to all patients
    print("\n1️⃣ Testing /medication/send-reminders endpoint...")
    try:
        response = requests.post(f"{base_url}/medication/send-reminders")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result['message']}")
            print(f"   Reminders sent: {result['reminders_sent']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Network Error: {e}")
    
    # Test 2: Test reminder for a specific patient (you'll need to replace with a real patient ID)
    print("\n2️⃣ Testing /medication/test-reminder/<patient_id> endpoint...")
    print("   Note: Replace 'PATIENT_ID_HERE' with a real patient ID from your database")
    
    patient_id = "PATIENT_ID_HERE"  # Replace with actual patient ID
    
    if patient_id != "PATIENT_ID_HERE":
        try:
            response = requests.post(f"{base_url}/medication/test-reminder/{patient_id}")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success: {result['message']}")
                print(f"   Email sent to: {result['patient_email']}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Network Error: {e}")
    else:
        print("   ⚠️ Skipped: Please update patient_id in the script")
    
    # Test 3: Check upcoming dosages for a patient
    print("\n3️⃣ Testing /medication/get-upcoming-dosages/<patient_id> endpoint...")
    if patient_id != "PATIENT_ID_HERE":
        try:
            response = requests.get(f"{base_url}/medication/get-upcoming-dosages/{patient_id}")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success: Found {result['total_upcoming']} upcoming dosages")
                print(f"   Prescription medications: {result['total_prescriptions']}")
                
                # Show upcoming dosages
                for dosage in result.get('upcoming_dosages', [])[:3]:  # Show first 3
                    print(f"   💊 {dosage['medication_name']} - {dosage['dosage']} at {dosage['time']}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Network Error: {e}")
    else:
        print("   ⚠️ Skipped: Please update patient_id in the script")
    
    print("\n" + "=" * 50)
    print("🏁 Testing completed!")

def check_backend_health():
    """Check if the backend is running"""
    try:
        response = requests.get("http://127.0.0.1:5000/")
        if response.status_code == 200:
            print("✅ Backend is running and accessible")
            return True
        else:
            print(f"❌ Backend responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend is not accessible: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Medication Reminder Test Script")
    print("=" * 50)
    
    # Check if backend is running
    if not check_backend_health():
        print("\n💡 Please start the Flask backend first:")
        print("   python app_simple.py")
        exit(1)
    
    # Run tests
    test_medication_reminder_endpoints()
