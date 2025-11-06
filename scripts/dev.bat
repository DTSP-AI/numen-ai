@echo off
REM HypnoAgent Development Server Startup Script (Windows)
REM Starts both backend and frontend

echo ========================================
echo   HypnoAgent Development Server
echo ========================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Check if .env exists
if not exist "%PROJECT_ROOT%\.env" (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure your credentials.
    echo.
    echo Run: copy .env.example .env
    exit /b 1
)

REM Check if backend venv exists
if not exist "%PROJECT_ROOT%\backend\venv" (
    echo WARNING: Backend virtual environment not found.
    echo Run: scripts\install.bat first
    echo.
)

REM Check if frontend node_modules exists
if not exist "%PROJECT_ROOT%\frontend\node_modules" (
    echo WARNING: Frontend node_modules not found.
    echo Run: scripts\install.bat first
    echo.
)

REM Start backend in new window
echo Starting backend on port 8003...
start "HypnoAgent Backend" cmd /k "cd /d %PROJECT_ROOT%\backend && venv\Scripts\activate && uvicorn main:app --reload --port 8003"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
echo Starting frontend on port 3003...
start "HypnoAgent Frontend" cmd /k "cd /d %PROJECT_ROOT%\frontend && npm run dev"

REM Display info
echo.
echo ========================================
echo   Services Started Successfully!
echo ========================================
echo.
echo Backend API:      http://localhost:8003
echo API Docs:         http://localhost:8003/docs
echo Health Check:     http://localhost:8003/health
echo.
echo Frontend:         http://localhost:3003
echo.
echo Two terminal windows have been opened.
echo Close them to stop the services.
echo.

pause
