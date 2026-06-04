#!/bin/bash
# Secure File Sharing System - Startup Script

echo "==================================="
echo "Secure File Sharing System"
echo "==================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "Starting Secure File Sharing Server..."
echo "Web UI: http://localhost:8000"
echo "API Docs: http://localhost:8000/api/docs"
echo "Health: http://localhost:8000/health"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
