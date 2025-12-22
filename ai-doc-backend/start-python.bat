@echo off
REM ============================================
REM Document Reader - Pure Python Backend
REM ============================================
REM Starts only the Python Flask application
REM No Node.js backend

echo.
echo =============================================
echo Document Reader Backend - Python Only
echo =============================================
echo.

REM Change to parsers_python directory
cd /d "%~dp0\parsers_python"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your system PATH
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking Python dependencies...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check for Tesseract (required for OCR)
echo Checking for Tesseract OCR...
where tesseract >nul 2>&1
if errorlevel 1 (
    echo WARNING: Tesseract OCR not found in PATH
    echo OCR functionality will not work
    echo Install from: https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo Continuing with native PDF text extraction...
    timeout /t 3 >nul
)

REM Start Python Flask server
echo.
echo Starting Document Reader Flask Server on http://localhost:5001
echo.
echo Press CTRL+C to stop the server
echo.

python app.py

if errorlevel 1 (
    echo.
    echo ERROR: Flask server failed to start
    pause
)
