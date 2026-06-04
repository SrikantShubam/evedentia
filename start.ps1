# Evidentia — start backend + frontend
# Usage: .\start.ps1
# Backend: http://localhost:8000
# Frontend: http://localhost:3000

Set-Location $PSScriptRoot

Write-Host "Starting backend (http://localhost:8000) ..."
$backend = Start-Process -FilePath "python" -ArgumentList "scripts/start_api.py" -PassThru -NoNewWindow

Start-Sleep -Seconds 3

Write-Host "Starting frontend (http://localhost:3000) ..."
$frontend = Start-Process -FilePath "cmd" -ArgumentList "/c npx next dev" -WorkingDirectory "docs/frontend" -PassThru -NoNewWindow

Write-Host ""
Write-Host "Backend:  http://localhost:8000"
Write-Host "Frontend: http://localhost:3000"
Write-Host "Press Ctrl+C to stop both."
Write-Host ""

try {
    while (-not $backend.HasExited -and -not $frontend.HasExited) {
        Start-Sleep -Seconds 2
    }
} finally {
    if (-not $backend.HasExited) { Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue }
    if (-not $frontend.HasExited) { Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue }
    Write-Host "Servers stopped."
}
