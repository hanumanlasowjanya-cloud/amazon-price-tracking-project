@echo off
title Amazon Price Tracker - Daily Automation

echo ==========================================
echo Amazon Price Tracker - Daily Automation
echo ==========================================

REM ======================================================
REM Project Folder
REM ======================================================

cd /d D:\PROJECTS\amazon-price-tracking-project

REM ======================================================
REM Activate Virtual Environment
REM ======================================================

call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo Failed to activate virtual environment.
    exit /b 1
)

REM ======================================================
REM Log File
REM ======================================================

set LOGFILE=automation_log.txt

echo. >> %LOGFILE%
echo ========================================== >> %LOGFILE%
echo %DATE% %TIME% >> %LOGFILE%
echo ========================================== >> %LOGFILE%

REM ======================================================
REM Run Scraper
REM ======================================================

echo.
echo Running Amazon Scraper...

python extract_Data.py >> %LOGFILE% 2>&1

if errorlevel 1 (
    echo Scraper failed.
    exit /b 1
)

REM ======================================================
REM Get Today's Date
REM ======================================================

for /f %%i in ('powershell -command "Get-Date -Format yyyy-MM-dd"') do set TODAY=%%i

REM ======================================================
REM Git Status
REM ======================================================

echo.
echo Checking Git Status...

git status

REM ======================================================
REM Stage Files
REM ======================================================

echo.
echo Staging Files...

git add .

if errorlevel 1 (
    echo Git Add Failed.
    exit /b 1
)

REM ======================================================
REM Check for Changes
REM ======================================================

git diff --cached --quiet

if %errorlevel%==0 (
    echo.
    echo No changes detected.
    exit /b 0
)

REM ======================================================
REM Commit
REM ======================================================

echo.
echo Creating Commit...

git commit -m "Daily Amazon price update - %TODAY%"

if errorlevel 1 (
    echo Git Commit Failed.
    exit /b 1
)

REM ======================================================
REM Pull Latest Changes
REM ======================================================

echo.
echo Pulling Latest Changes...

git pull --rebase origin main

if errorlevel 1 (
    echo Git Pull Failed.
    exit /b 1
)

REM ======================================================
REM Push
REM ======================================================

echo.
echo Pushing to GitHub...

git push origin main

if errorlevel 1 (
    echo Git Push Failed.
    exit /b 1
)

echo.
echo ==========================================
echo Daily Automation Completed Successfully!
echo ==========================================

exit /b 0