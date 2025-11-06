@echo off
REM HypnoAgent Installation Script (Windows)
REM Installs all dependencies for backend and frontend

echo ========================================
echo   HypnoAgent Installation
echo ========================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

python --version
echo.

REM Check Node version
echo Checking Node.js version...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

node --version
echo.

REM Check if .env exists
if not exist "%PROJECT_ROOT%\.env" (
    echo WARNING: .env file not found.
    echo Copying .env.example to .env...
    copy "%PROJECT_ROOT%\.env.example" "%PROJECT_ROOT%\.env"
    echo Done! Please edit .env with your credentials.
    echo.
)

REM Install backend dependencies
echo Installing backend dependencies...
cd /d "%PROJECT_ROOT%\backend"

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

REM Install requirements
echo Installing Python packages...
pip install -r requirements.txt

echo Backend dependencies installed!
echo.

REM Install frontend dependencies
echo Installing frontend dependencies...
cd /d "%PROJECT_ROOT%\frontend"

echo Installing npm packages...
call npm install

echo Frontend dependencies installed!
echo.

REM Create necessary directories
echo Creating necessary directories...
if not exist "%PROJECT_ROOT%\backend\audio_files" mkdir "%PROJECT_ROOT%\backend\audio_files"
if not exist "%PROJECT_ROOT%\backend\avatars" mkdir "%PROJECT_ROOT%\backend\avatars"
if not exist "%PROJECT_ROOT%\backend\prompts" mkdir "%PROJECT_ROOT%\backend\prompts"

echo Directories created!
echo.

REM Summary
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your credentials
echo    - SUPABASE_DB_URL (required)
echo    - OPENAI_API_KEY (required)
echo    - Optional: ELEVENLABS_API_KEY, DEEPGRAM_API_KEY, LIVEKIT_*
echo.
echo 2. Start development servers:
echo    scripts\dev.bat
echo.
echo 3. Visit:
echo    - Frontend: http://localhost:3003
echo    - Backend API: http://localhost:8003/docs
echo    - Health Check: http://localhost:8003/health
echo.

pause
