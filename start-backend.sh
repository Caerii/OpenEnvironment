#!/bin/bash
# Bash script to start the backend server (macOS/Linux)

echo "Starting Semantic Terrain Backend..."

cd server

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
echo "Activating virtual environment..."
source .venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start server
echo "Starting FastAPI server on http://localhost:8000"
echo "Press Ctrl+C to stop"
uvicorn main:app --reload --port 8000

