# PowerShell script to start the frontend dev server
Write-Host "Starting Semantic Terrain Frontend..." -ForegroundColor Green

Set-Location web

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
}

# Check if textures exist
$textures = @("grass.jpg", "rock.jpg", "sand.jpg", "snow.jpg")
$missing = @()
foreach ($tex in $textures) {
    if (-not (Test-Path "public\textures\$tex")) {
        $missing += $tex
    }
}

if ($missing.Count -gt 0) {
    Write-Host "`nWARNING: Missing texture files in web/public/textures/:" -ForegroundColor Red
    foreach ($tex in $missing) {
        Write-Host "  - $tex" -ForegroundColor Red
    }
    Write-Host "`nSee web/public/textures/README.md for instructions.`n" -ForegroundColor Yellow
}

# Start dev server
Write-Host "Starting Vite dev server on http://localhost:5173" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
npm run dev

