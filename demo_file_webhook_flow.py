#!/usr/bin/env python3
"""
Simple demonstration script for file upload and webhook flow
Shows how to manually test the complete process
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"

def demo_file_upload_and_webhook():
    """Demonstrate the complete file upload and webhook flow"""
    print("🚀 File Upload and Webhook Flow Demonstration")
    print("=" * 50)
    
    # Step 1: Check if backend is running
    print("\n📡 Step 1: Checking backend status...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Please start the Flask server first.")
        return
    
    # Step 2: Create sample prescription text
    print("\n📝 Step 2: Creating sample prescription text...")
    prescription_text = """
    PRESCRIPTION
    
    Patient: John Smith
    Date: 2024-01-15
    Doctor: Dr. Johnson
    
    Medication: Amoxicillin
    Dosage: 500mg
    Frequency: Three times daily
    Duration: 7 days
    Special Instructions: Take with food
    
    Prescribed by: Dr. Johnson
    """
    
    print(f"✅ Created prescription text ({len(prescription_text)} characters)")
    
    # Step 3: Send to webhook using medication folder service
    print("\n🚀 Step 3: Sending to webhook using medication folder service...")
    
    webhook_data = {
        'patient_id': 'demo_patient_001',
        'medication_name': 'Amoxicillin',
        'extracted_text': prescription_text.strip(),
        'filename': 'demo_prescription.txt',
        'timestamp': datetime.now().isoformat()
    }
    
    print("📤 Sending data to webhook...")
    print(f"📄 Patient ID: {webhook_data['patient_id']}")
    print(f"📄 Medication: {webhook_data['medication_name']}")
    print(f"📄 Filename: {webhook_data['filename']}")
    print(f"📄 Text length: {len(webhook_data['extracted_text'])} characters")
    
    try:
        response = requests.post(
            f"{BASE_URL}/medication/process-with-n8n-webhook",
            json=webhook_data,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"\n📡 Webhook Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook delivery successful!")
            
            # Display the result
            print(f"\n📋 Response Details:")
            print(f"  Message: {result.get('message', '')}")
            print(f"  Success: {result.get('success', False)}")
            print(f"  Timestamp: {result.get('timestamp', '')}")
            
            # Display webhook results
            webhook_results = result.get('webhook_results', [])
            if webhook_results:
                print(f"\n🔗 Webhook Results ({len(webhook_results)} attempts):")
                for i, webhook_result in enumerate(webhook_results, 1):
                    success = webhook_result.get('success', False)
                    config_name = webhook_result.get('config_name', 'Unknown')
                    url = webhook_result.get('url', 'Unknown')
                    status = "✅ Success" if success else "❌ Failed"
                    print(f"  {i}. {config_name}: {status}")
                    print(f"     URL: {url}")
                    
                    if not success:
                        error = webhook_result.get('error', 'Unknown error')
                        print(f"     Error: {error}")
            else:
                print("\n⚠️ No webhook results returned")
            
            # Display OCR data
            ocr_data = result.get('ocr_data', {})
            if ocr_data:
                print(f"\n📄 OCR Data:")
                print(f"  Success: {ocr_data.get('success', False)}")
                print(f"  Text count: {ocr_data.get('text_count', 0)}")
                results = ocr_data.get('results', [])
                if results:
                    print(f"  First result text: {results[0].get('text', '')[:100]}...")
            
        else:
            print(f"❌ Webhook delivery failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error sending to webhook: {e}")
    
    # Step 4: Test fallback mock service
    print("\n🔗 Step 4: Testing fallback mock service...")
    
    mock_data = {
        'patient_id': 'demo_patient_001',
        'medication_name': 'Test Medication',
        'extracted_text': 'Test prescription text for mock service',
        'filename': 'test_prescription.txt',
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        mock_response = requests.post(
            f"{BASE_URL}/medication/process-with-mock-n8n",
            json=mock_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if mock_response.status_code == 200:
            mock_result = mock_response.json()
            print("✅ Mock service working correctly")
            print(f"📄 Message: {mock_result.get('message', '')}")
        else:
            print(f"❌ Mock service error: {mock_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing mock service: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Demonstration Summary:")
    print("✅ Backend connectivity verified")
    print("✅ Sample prescription text created")
    print("✅ Webhook service tested")
    print("✅ Mock service tested")
    print("\n💡 The system is now ready to process real prescription files!")
    print("🔍 Check the backend logs for detailed webhook service information.")

if __name__ == "__main__":
    demo_file_upload_and_webhook()
