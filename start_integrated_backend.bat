@echo off
echo ========================================
echo Starting Integrated Backend Server
echo ========================================
echo.
echo This backend now includes:
echo ✅ User authentication & patient profiles
echo ✅ Medication tracking & reminders
echo ✅ Mental health tracking
echo ✅ Voice transcription (Whisper AI)
echo ✅ Food analysis (GPT-4)
echo ✅ All services on PORT 5000
echo.
echo Starting server...
echo.
cd /d "%~dp0"
python app_simple.py
pause
