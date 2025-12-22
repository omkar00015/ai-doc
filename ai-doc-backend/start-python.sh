#!/bin/bash

# ============================================
# Document Reader - Pure Python Backend
# ============================================
# Starts only the Python Flask application
# No Node.js backend

echo ""
echo "============================================"
echo "Document Reader Backend - Python Only"
echo "============================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to parsers_python directory
cd "$SCRIPT_DIR/parsers_python"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed"
    echo "Please install Python 3.8+ using:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "  macOS: brew install python3"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Found Python $PYTHON_VERSION"

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update requirements
echo "Checking Python dependencies..."
pip install -q -r requirements.txt

# Check for Tesseract
if ! command -v tesseract &> /dev/null; then
    echo "WARNING: Tesseract OCR not found"
    echo "Install with:"
    echo "  Ubuntu: sudo apt-get install tesseract-ocr"
    echo "  macOS: brew install tesseract"
    echo ""
    echo "Continuing with native PDF text extraction..."
fi

# Start Python Flask server
echo ""
echo "Starting Document Reader Flask Server on http://localhost:5001"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

python app.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Flask server failed to start"
    exit 1
fi
