#!/usr/bin/env python3
"""
Startup script for the Nutrition Backend Service
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_nutrition.txt"])
        print("✅ Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False
    return True

def start_nutrition_backend():
    """Start the nutrition backend service"""
    print("🚀 Starting Nutrition Backend Service...")
    print("🍎 Service will be available at: http://localhost:8000")
    print("📱 Flutter app will connect to: http://127.0.0.1:8000")
    print("\n" + "="*50)
    
    try:
        # Start the nutrition backend
        subprocess.run([sys.executable, "nutrition_backend.py"])
    except KeyboardInterrupt:
        print("\n🛑 Nutrition Backend Service stopped by user")
    except Exception as e:
        print(f"❌ Error starting nutrition backend: {e}")

def main():
    """Main function"""
    print("🍎 Nutrition Backend Service Setup")
    print("="*40)
    
    # Check if nutrition_backend.py exists
    if not Path("nutrition_backend.py").exists():
        print("❌ nutrition_backend.py not found!")
        print("Please ensure you're in the correct directory")
        return
    
    # Check if requirements file exists
    if not Path("requirements_nutrition.txt").exists():
        print("❌ requirements_nutrition.txt not found!")
        print("Please ensure you're in the correct directory")
        return
    
    # Install requirements
    if not install_requirements():
        print("❌ Failed to install requirements. Exiting...")
        return
    
    # Start the service
    start_nutrition_backend()

if __name__ == "__main__":
    main()
