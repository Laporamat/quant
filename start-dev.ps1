#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start the Quant backend (FastAPI) and frontend (Vite) dev servers side-by-side.

.DESCRIPTION
    Opens two new PowerShell windows:
      - Window 1: python main.py  (FastAPI on http://localhost:8000)
      - Window 2: npm run dev     (Vite on http://localhost:5173)

    Prerequisites:
      - Python 3.11+ with all deps installed  (pip install -r requirements.txt)
      - Node.js 18+ with deps installed        (cd frontend && npm install)
      - .env file configured (copy .env.example → .env and edit)
#>

$ROOT = $PSScriptRoot

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  QuantDash Dev Launcher" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# ── Check .env ────────────────────────────────────────────────────────────────
if (-not (Test-Path "$ROOT\.env")) {
    Write-Host "[WARN] .env not found — copying from .env.example" -ForegroundColor Yellow
    Copy-Item "$ROOT\.env.example" "$ROOT\.env"
}

# ── Check frontend/node_modules ───────────────────────────────────────────────
if (-not (Test-Path "$ROOT\frontend\node_modules")) {
    Write-Host "[INFO] Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location "$ROOT\frontend"
    npm install
    Set-Location $ROOT
}

Write-Host "[INFO] Starting FastAPI backend (port 8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "Set-Location '$ROOT'; Write-Host 'Quant Backend' -ForegroundColor Cyan; python main.py"

Start-Sleep -Seconds 2

Write-Host "[INFO] Starting Vite frontend (port 5173)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "Set-Location '$ROOT\frontend'; Write-Host 'Vite Dev Server' -ForegroundColor Cyan; npm run dev"

Write-Host ""
Write-Host "[OK] Both servers launched." -ForegroundColor Green
Write-Host "  Backend  → http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Frontend → http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "  (Close the new terminal windows to stop the servers)" -ForegroundColor Gray
