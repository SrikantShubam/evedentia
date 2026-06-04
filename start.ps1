# Evidentia — start backend + frontend
# Usage: .\start.ps1
# Backend: http://localhost:8000
# Frontend: http://localhost:3000

$backend = Start-Process -FilePath "python" -ArgumentList "scripts/start_api.py" -PassThru -WindowStyle Minimized
Write-Host "Backend starting on http://localhost:8000 ..."

Start-Sleep -Seconds 3

$frontend = Start-Process -FilePath "npx" -ArgumentList "next", "dev" -WorkingDirectory "docs/frontend" -PassThru -WindowStyle Minimized
Write-Host "Frontend starting on http://localhost:3000 ..."

Write-Host ""
Write-Host "Both servers starting. Open http://localhost:3000 in your browser."
Write-Host "Press Ctrl+C to stop both."
Write-Host ""

try {
    Wait-Process -Id $backend.Id, $frontend.Id
} finally {
    Stop-Process -Id $backend.Id, $frontend.Id -Force -ErrorAction SilentlyContinue
    Write-Host "Servers stopped."
}
