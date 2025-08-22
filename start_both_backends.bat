@echo off
echo ========================================
echo Starting Both Backend Services
echo ========================================
echo.
echo This will start:
echo 1. Main Flask Backend on Port 5000
echo 2. Nutrition Backend on Port 8002
echo.
echo Keep both windows open while testing!
echo.

echo Starting Main Backend (Port 5000)...
start "Main Backend - Port 5000" cmd /k "cd /d %~dp0 && python app_simple.py"

echo Waiting 5 seconds for main backend to start...
timeout /t 5 /nobreak > nul

echo Starting Nutrition Backend (Port 8002)...
start "Nutrition Backend - Port 8002" cmd /k "cd /d %~dp0 && python nutrition_backend_new.py"

echo.
echo ========================================
echo Both services are starting...
echo ========================================
echo.
echo Main Backend: http://127.0.0.1:5000
echo Nutrition Backend: http://127.0.0.1:8002
echo.
echo Keep both command windows open!
echo.
pause
