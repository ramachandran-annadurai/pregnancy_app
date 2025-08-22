#!/usr/bin/env python3
"""
Quick test for PaddleOCR dependencies
"""

try:
    print("🧪 Testing PaddleOCR Dependencies...")
    
    # Test 1: PaddleOCR
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR imported successfully")
    
    # Test 2: PyMuPDF
    import fitz
    print("✅ PyMuPDF imported successfully")
    
    # Test 3: PyPDF2
    import PyPDF2
    print("✅ PyPDF2 imported successfully")
    
    # Test 4: PIL
    from PIL import Image
    print("✅ PIL imported successfully")
    
    # Test 5: OpenCV
    import cv2
    print("✅ OpenCV imported successfully")
    
    # Test 6: Medication folder services
    import sys
    import os
    
    medication_path = os.path.join(os.path.dirname(__file__), 'medication', 'medication')
    sys.path.insert(0, medication_path)
    
    from app.services.enhanced_ocr_service import EnhancedOCRService
    print("✅ EnhancedOCRService imported successfully")
    
    from app.services.webhook_service import WebhookService
    print("✅ WebhookService imported successfully")
    
    print("\n🎉 ALL DEPENDENCIES ARE WORKING!")
    print("💡 You can now start the Flask backend with full OCR capabilities")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("💡 Install missing dependencies and try again")
except Exception as e:
    print(f"❌ Error: {e}")
    print("💡 Check the error message above")
