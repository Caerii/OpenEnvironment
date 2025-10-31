#!/bin/bash
# Bash script to start the backend with uv (macOS/Linux)

echo "Starting Semantic Terrain Backend (uv mode)..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "ERROR: uv is not installed!"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "Using $(uv --version)"

cd server

# Check if uv.lock exists
if [ ! -f "uv.lock" ]; then
    echo "No uv.lock found. Running initial sync..."
    uv sync
fi

# Start server (run from repo root so Python can find the 'server' module)
cd ..
export PYTHONPATH="$(pwd)"
echo "Starting FastAPI server on http://localhost:8001"
echo "Press Ctrl+C to stop"
echo ""
uv run --directory server uvicorn server.main:app --host 0.0.0.0 --port 8001 --reload
