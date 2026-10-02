@echo off
cd /d "%~dp0"
echo Installing API dependencies...
pip install -r requirements-api.txt
if %errorlevel% neq 0 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)
echo.
echo Starting FastAPI backend on http://localhost:8000
echo API docs: http://localhost:8000/docs
echo.
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
pause
