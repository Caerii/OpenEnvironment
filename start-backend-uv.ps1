# PowerShell script to start the backend with uv
Write-Host "Starting Semantic Terrain Backend (uv mode)..." -ForegroundColor Green

# Check if uv is installed
try {
    $uvVersion = uv --version
    Write-Host "Using $uvVersion" -ForegroundColor Cyan
} catch {
    Write-Host "ERROR: uv is not installed!" -ForegroundColor Red
    Write-Host "Install it with: powershell -c 'irm https://astral.sh/uv/install.ps1 | iex'" -ForegroundColor Yellow
    exit 1
}

Set-Location server

# Check if uv.lock exists
if (-not (Test-Path "uv.lock")) {
    Write-Host "No uv.lock found. Running initial sync..." -ForegroundColor Yellow
    uv sync
}

# Start server (run from repo root so Python can find the 'server' module)
Set-Location ..
$env:PYTHONPATH = (Get-Location).Path
Write-Host "Starting FastAPI server on http://localhost:8001" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""
uv run --directory server uvicorn server.main:app --host 0.0.0.0 --port 8001 --reload
