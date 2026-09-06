@echo off
cd /d "%~dp0frontend"
echo Installing dependencies (first run only)...
npm install
echo.
echo Starting Bond Analytics React app...
echo Open http://localhost:5173 in your browser
echo.
npm run dev
pause
