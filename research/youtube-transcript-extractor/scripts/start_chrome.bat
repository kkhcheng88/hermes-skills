@echo off
REM YouTube Transcript Extractor - Chrome Debug Launcher (Windows)
REM This script starts Chrome with remote debugging enabled on port 9222

echo Starting Chrome with debugging port 9222...

REM Kill any existing Chrome instances (optional - remove if you want to keep existing windows)
taskkill /F /IM chrome.exe 2>nul

REM Wait for Chrome to close
timeout /t 2 /nobreak >nul

REM Start Chrome with debugging port
REM --user-data-dir: Use a separate profile for debugging (avoids conflicts with your main Chrome)
REM --remote-debugging-port: Enable remote debugging on port 9222
REM --no-first-run: Skip first-run wizard
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir=C:\temp\chrome-debug --remote-debugging-port=9222 --no-first-run

REM Wait for Chrome to start
timeout /t 5 /nobreak >nul

echo.
echo Chrome started successfully!
echo Debugging port: 9222
echo Debug URL: http://127.0.0.1:9222
echo.
echo You can now run the YouTube transcript extraction scripts.
echo.
pause
