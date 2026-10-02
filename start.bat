@echo off
cd /d "%~dp0"
echo ============================================
echo  Bond Analytics - Starting all services
echo ============================================
echo.

:: Start FastAPI backend in a new window
echo [1/3] Starting FastAPI backend on port 8000...
start "Bond Analytics - API" cmd /k "uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

:: Wait for the API to be ready (poll port 8000)
echo [2/3] Waiting for API to be ready...
:wait_loop
timeout /t 2 /nobreak >nul
curl -s http://localhost:8000/docs >nul 2>&1
if %errorlevel% neq 0 goto wait_loop
echo     API is up!

:: Start React frontend in a new window
echo [3/3] Starting React frontend on port 5175...
start "Bond Analytics - React" cmd /k "cd /d "%~dp0frontend" && npm run dev"

:: Wait a moment then open the browser
timeout /t 3 /nobreak >nul
echo.
echo Opening http://localhost:5175 in your browser...
start "" "http://localhost:5175"

echo.
echo ============================================
echo  Both services running. Close this window.
echo  API:      http://localhost:8000
echo  API docs: http://localhost:8000/docs
echo  App:      http://localhost:5175
echo ============================================
