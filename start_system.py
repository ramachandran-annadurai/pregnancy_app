#!/usr/bin/env python3
"""
Startup script for Patient Alert System
"""

import subprocess
import time
import webbrowser
import os
import sys

def start_flask_api():
    """Start the Flask API"""
    print("🚀 Starting Flask API...")
    try:
        # Start Flask API in background
        subprocess.Popen([sys.executable, "app_simple.py"], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        print("✅ Flask API started on http://localhost:5000")
        return True
    except Exception as e:
        print(f"❌ Failed to start Flask API: {e}")
        return False

def start_frontend():
    """Start the frontend server"""
    print("🌐 Starting frontend server...")
    try:
        # Change to simple_frontend directory and start server
        os.chdir("simple_frontend")
        subprocess.Popen([sys.executable, "-m", "http.server", "8080"], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        os.chdir("..")
        print("✅ Frontend started on http://localhost:8080")
        return True
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return False

def open_browser():
    """Open browser to frontend"""
    print("📱 Opening browser...")
    try:
        webbrowser.open("http://localhost:8080")
        print("✅ Browser opened successfully")
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print("Please manually open: http://localhost:8080")

def main():
    """Main startup function"""
    print("🎉 Patient Alert System - Startup")
    print("=" * 50)
    
    # Start Flask API
    api_ok = start_flask_api()
    
    # Wait a moment for API to start
    time.sleep(2)
    
    # Start frontend
    frontend_ok = start_frontend()
    
    # Wait for frontend to start
    time.sleep(2)
    
    if api_ok and frontend_ok:
        print("\n✅ System started successfully!")
        print("\n📱 Access points:")
        print("• Frontend: http://localhost:8080")
        print("• API: http://localhost:5000")
        print("• Postman Collection: Patient_Alert_System_Flask_API.postman_collection.json")
        
        # Open browser
        open_browser()
        
        print("\n🎉 System is ready to use!")
        print("Press Ctrl+C to stop all servers")
        
        try:
            # Keep the script running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
    else:
        print("\n❌ Failed to start system")
        print("Please check:")
        print("1. Python dependencies: pip install -r requirements_flask_simple.txt")
        print("2. MongoDB connection")
        print("3. Port availability (5000, 8080)")

if __name__ == "__main__":
    main() 