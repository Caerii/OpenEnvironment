# PowerShell script to start the frontend dev server
Write-Host "Starting OpenEnvironment Frontend..." -ForegroundColor Green

Set-Location "OpenEnvironment\web"

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pnpm install
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
    Write-Host "`nWARNING: Missing texture files in OpenEnvironment/web/public/textures/:" -ForegroundColor Red
    foreach ($tex in $missing) {
        Write-Host "  - $tex" -ForegroundColor Red
    }
    Write-Host "`nSee OpenEnvironment/web/public/textures/README.md for instructions.`n" -ForegroundColor Yellow
}

# Start dev server
Write-Host "Starting Vite dev server on http://localhost:5173" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
pnpm run dev
