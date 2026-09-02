@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo   Quant Trading System - Push to GitHub
echo ============================================================
echo.

cd /d "c:\appAI\quant"

where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] git not found! Please install Git first: https://git-scm.com/
    pause
    exit /b 1
)

if not exist ".git" (
    echo [1/5] Initializing Git repository...
    git init
    if !errorlevel! neq 0 ( echo [FAIL] git init failed & pause & exit /b 1 )
    echo [OK] Git initialized.
    echo.
) else (
    echo [1/5] Git already initialized - skip.
    echo.
)

echo [2/5] Adding all files...
git add -A
echo [OK] Files staged.
echo.

git rev-parse --verify HEAD >nul 2>nul
if !errorlevel! neq 0 (
    echo [3/5] Creating initial commit...
    git commit -m "Initial commit: Quant Trading System - Backtester, Strategies, Indicators, REST API, and Statistics modules"
    if !errorlevel! neq 0 ( echo [FAIL] commit failed & pause & exit /b 1 )
) else (
    echo [3/5] Creating commit with latest changes...
    git commit -m "Update: Sync latest changes to repository" --allow-empty
)
echo [OK] Commit done.
echo.

git remote get-url origin >nul 2>nul
if !errorlevel! neq 0 (
    echo [4/5] Adding remote origin: https://github.com/Laporamat/quant.git
    git remote add origin https://github.com/Laporamat/quant.git
) else (
    echo [4/5] Remote origin already exists - updating URL...
    git remote set-url origin https://github.com/Laporamat/quant.git
)
echo [OK] Remote configured.
echo.

for /f "delims=" %%i in ('git branch --show-current') do set CUR_BRANCH=%%i
if "!CUR_BRANCH!"=="" set CUR_BRANCH=main
git branch -M main

echo [5/5] Pushing to GitHub (branch: main)...
echo.
git push -u origin main

if !errorlevel! equ 0 (
    echo.
    echo ============================================================
    echo   SUCCESS! Code pushed to GitHub successfully.
    echo   URL: https://github.com/Laporamat/quant
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo   PUSH FAILED.
    echo.
    echo   Possible reasons:
    echo   1. GitHub authentication required (username + token/password)
    echo   2. Repository is private and you don't have access
    echo   3. Repository already has commits that conflict
    echo.
    echo   If repo has existing commits, run:  git pull --rebase origin main
    echo   Then run this script again.
    echo ============================================================
)

echo.
pause
