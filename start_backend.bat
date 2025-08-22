@echo off
echo Starting Flask Backend Server...
echo.
echo This will start the medication reminder system and all API endpoints
echo.
cd /d "%~dp0"
python app_simple.py
pause
