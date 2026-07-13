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

REM Stop if scraper failed
if %errorlevel% neq 0 (
    echo.
    echo Scraper failed. Exiting...
    pause
    exit /b
)

echo.
echo Getting today's date...

for /f %%i in ('powershell -command "Get-Date -Format yyyy-MM-dd"') do set TODAY=%%i

echo.
echo Staging updated Excel file...

git add amazon_products.xlsx

REM Check if anything actually changed
git diff --cached --quiet
if %errorlevel%==0 (
    echo.
    echo No price changes detected.
    pause
    exit /b
)

echo.
echo Creating Git commit...

git commit -m "Daily Amazon price update - %TODAY%"

echo.
echo Pulling latest changes...

git pull --rebase origin main

echo.
echo Pushing to GitHub...

git push origin main

echo.
echo ==========================================
echo Automation completed successfully!
echo ==========================================

pause