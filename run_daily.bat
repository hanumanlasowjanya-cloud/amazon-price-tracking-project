@echo off
title Amazon Price Tracker - Daily Automation

echo ==========================================
echo Amazon Price Tracker Daily Automation
echo ==========================================

REM Go to project folder
cd /d D:\PROJECTS\amazon-price-tracking-project

REM Activate virtual environment
call .venv\Scripts\activate.bat

echo.
echo Running scraper...
python extract_Data.py

if errorlevel 1 (
    echo.
    echo Scraper failed.
    pause
    exit /b 1
)

echo.
echo Getting today's date...
for /f %%i in ('powershell -command "Get-Date -Format yyyy-MM-dd"') do set TODAY=%%i

echo.
echo Checking Git status...

git status

echo.
echo Staging all changed files...

git add .

if errorlevel 1 (
    echo.
    echo Git Add Failed.
    pause
    exit /b 1
)

git diff --cached --quiet

if %errorlevel%==0 (
    echo.
    echo No changes detected.
    pause
    exit /b 0
)

echo.
echo Creating commit...

git commit -m "Daily Amazon price update - %TODAY%"

if errorlevel 1 (
    echo.
    echo Git Commit Failed.
    pause
    exit /b 1
)

echo.
echo Pulling latest changes...

git pull --rebase origin main

if errorlevel 1 (
    echo.
    echo Git Pull Failed.
    pause
    exit /b 1
)

echo.
echo Pushing to GitHub...

git push origin main

if errorlevel 1 (
    echo.
    echo Git Push Failed.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Daily Automation Completed Successfully!
echo ==========================================

pause