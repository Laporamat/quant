# ============================================================
# Quant Backend — Quick Launch Script
# วิธีใช้: คลิกขวาที่ไฟล์นี้ แล้วเลือก "Run with PowerShell"
# หรือพิมพ์ใน Terminal: .\run.ps1
# ============================================================

$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot"

Write-Host ""
Write-Host "🚀  Quant Backend Launcher" -ForegroundColor Cyan
Write-Host "    Working Dir: $PSScriptRoot"
Write-Host ""

# 1. Check python exists
try {
    $pyVer = & python --version 2>&1
    Write-Host "[OK]   $pyVer" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Python ไม่พบ! ต้องติดตั้ง Python 3.11+" -ForegroundColor Red
    Read-Host "กด Enter เพื่อออก"
    exit 1
}

# 2. Check venv / requirements
$venvPath = Join-Path $PSScriptRoot ".venv"
if (Test-Path $venvPath) {
    Write-Host "[INFO] พบ virtual environment ที่ .venv — กำลัง activate" -ForegroundColor DarkGray
    & (Join-Path $venvPath "Scripts\Activate.ps1")
}

# 3. Ensure deps installed (สแกนครั้งเดียว)
$needInstall = $false
try {
    python -c "import fastapi, uvicorn, pandas, yfinance" 2>$null | Out-Null
} catch { $needInstall = $true }

if ($needInstall) {
    Write-Host "[DO ]  ติดตั้ง dependencies (pip install -r requirements.txt)" -ForegroundColor Yellow
    & python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] ติดตั้ง dependencies ไม่สำเร็จ" -ForegroundColor Red
        Read-Host "กด Enter เพื่อออก"
        exit 1
    }
} else {
    Write-Host "[OK]   Dependencies พร้อมใช้งาน" -ForegroundColor Green
}

# 4. Ensure .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[DO ]  สร้างไฟล์ .env จาก .env.example" -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "[OK]   สร้าง .env แล้ว (ถ้าจะแก้ DB/Redis ให้แก้ใน .env แล้วรันใหม่)" -ForegroundColor Green
}

# 5. Create data directories
@("data\raw", "data\cache", "reports", "logs") | ForEach-Object {
    if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
}

# 6. Run the server
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "   Quant Backend is starting..." -ForegroundColor White
Write-Host "   Swagger UI  : http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   ReDoc       : http://localhost:8000/redoc" -ForegroundColor Cyan
Write-Host "   Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "   (กด Ctrl+C เพื่อหยุดเซิร์ฟเวอร์)" -ForegroundColor DarkGray
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

& python main.py --reload --host 0.0.0.0 --port 8000

# ถ้าถูกจบโดย Ctrl+C หรือ error ก็ให้รอ
Write-Host ""
Write-Host "Server stopped." -ForegroundColor Yellow
Read-Host "กด Enter เพื่อปิดหน้าต่าง"
