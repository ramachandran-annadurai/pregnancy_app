#!/usr/bin/env python3
"""
Demo script for medication folder OCR services
Shows how files are processed and converted to full_text_content format
"""

import sys
import os

def demo_medication_folder_structure():
    """Show the medication folder structure"""
    print("📁 MEDICATION FOLDER STRUCTURE")
    print("=" * 50)
    
    medication_path = os.path.join(os.path.dirname(__file__), 'medication', 'medication')
    
    if os.path.exists(medication_path):
        print(f"✅ Medication folder found: {medication_path}")
        
        # Show key files
        key_files = [
            'app/__init__.py',
            'app/services/enhanced_ocr_service.py',
            'app/services/webhook_service.py',
            'app/models/webhook_config.py'
        ]
        
        for file_path in key_files:
            full_path = os.path.join(medication_path, file_path)
            if os.path.exists(full_path):
                print(f"  ✅ {file_path}")
            else:
                print(f"  ❌ {file_path}")
    else:
        print(f"❌ Medication folder not found: {medication_path}")
        return False
    
    return True

def demo_ocr_service_capabilities():
    """Show what the OCR service can do"""
    print("\n🔍 OCR SERVICE CAPABILITIES")
    print("=" * 50)
    
    print("📄 Supported File Types:")
    print("  • PDF files (.pdf) - Native text + OCR for images")
    print("  • Text files (.txt) - Direct text extraction")
    print("  • Image files (.jpg, .png) - Full OCR processing")
    print("  • Word documents (.doc, .docx) - Text conversion")
    
    print("\n🚀 Processing Features:")
    print("  • Multi-page document support")
    print("  • Confidence scoring for each text element")
    print("  • Bounding box coordinates for text positioning")
    print("  • Automatic fallback between native text and OCR")
    
    print("\n📝 Output Format:")
    print("  • Structured results with confidence scores")
    print("  • Full text content in medication folder format")
    print("  • Metadata about processing method used")
    print("  • Ready for webhook delivery to N8N")

def demo_full_text_content_format():
    """Show the full_text_content format"""
    print("\n📝 FULL TEXT CONTENT FORMAT")
    print("=" * 50)
    
    print("The medication folder OCR service produces text in this format:")
    print()
    
    sample_format = """Text 1: PRESCRIPTION (Confidence: 95.50%)
Text 2: Patient: Sarah Johnson (Confidence: 98.20%)
Text 3: Date: 2024-01-15 (Confidence: 97.80%)
Text 4: Doctor: Dr. Michael Chen (Confidence: 96.40%)
Text 5: Medication: Prenatal Vitamins (Confidence: 94.70%)
Text 6: Dosage: 1 tablet daily (Confidence: 93.90%)
Text 7: Frequency: Once daily with breakfast (Confidence: 92.50%)
Text 8: Duration: Throughout pregnancy (Confidence: 91.80%)"""
    
    print(sample_format)
    print()
    print("This format includes:")
    print("  ✅ Sequential text numbering")
    print("  ✅ Extracted text content")
    print("  ✅ Confidence scores for each element")
    print("  ✅ Structured for easy processing")
    print("  ✅ Automatically sent to N8N webhook")

def demo_webhook_integration():
    """Show how webhook integration works"""
    print("\n🔗 WEBHOOK INTEGRATION")
    print("=" * 50)
    
    print("📤 Webhook Payload Structure:")
    print("  • timestamp: ISO format timestamp")
    print("  • source: 'paddleocr-microservice'")
    print("  • filename: Original file name")
    print("  • ocr_result: Complete OCR processing results")
    print("  • full_text_content: Formatted text content")
    print("  • metadata: Text count and configuration info")
    
    print("\n🚀 N8N Integration:")
    print("  • Automatic delivery to configured webhooks")
    print("  • Retry logic with exponential backoff")
    print("  • Success/failure reporting")
    print("  • Configurable timeout and retry settings")
    
    print("\n📋 Current N8N Configuration:")
    print("  • URL: https://n8n.srv795087.hstgr.cloud/webhook/...")
    print("  • Method: POST")
    print("  • Headers: Content-Type: application/json")
    print("  • Timeout: 30 seconds")
    print("  • Retry attempts: 3")

def demo_usage_instructions():
    """Show how to use the system"""
    print("\n📖 USAGE INSTRUCTIONS")
    print("=" * 50)
    
    print("1. 🚀 Start the Flask Backend:")
    print("   python app_simple.py")
    
    print("\n2. 🧪 Test the OCR Services:")
    print("   python test_medication_folder_ocr.py")
    
    print("\n3. 📱 Use in Flutter App:")
    print("   • Navigate to medication tracking screen")
    print("   • Click 'Upload & Process Document'")
    print("   • Select a prescription file")
    print("   • Watch the extracted text appear in the text box")
    
    print("\n4. 🔗 Check N8N Webhook:")
    print("   • Monitor N8N instance for incoming data")
    print("   • Verify payload structure is correct")
    print("   • Confirm data processing in workflow")

def main():
    """Main demonstration function"""
    print("🎯 MEDICATION FOLDER OCR SERVICES DEMO")
    print("=" * 60)
    print("This demo shows how the medication folder services work")
    print("to upload files and convert them to full_text_content format")
    print("=" * 60)
    
    # Check medication folder structure
    if not demo_medication_folder_structure():
        print("\n❌ Cannot continue without medication folder")
        return
    
    # Show capabilities
    demo_ocr_service_capabilities()
    
    # Show output format
    demo_full_text_content_format()
    
    # Show webhook integration
    demo_webhook_integration()
    
    # Show usage instructions
    demo_usage_instructions()
    
    print("\n" + "=" * 60)
    print("🎉 DEMO COMPLETE!")
    print("=" * 60)
    print("The medication folder OCR services are ready to:")
    print("  ✅ Upload prescription files")
    print("  ✅ Process with professional OCR")
    print("  ✅ Extract text in full_text_content format")
    print("  ✅ Send to N8N webhook automatically")
    print("  ✅ Display results in Flutter app text box")
    
    print("\n💡 Next steps:")
    print("  1. Start the backend: python app_simple.py")
    print("  2. Test OCR: python test_medication_folder_ocr.py")
    print("  3. Use in Flutter app for file upload")

if __name__ == "__main__":
    main()
