#!/bin/bash
# YouTube Transcript Extractor - Chrome Debug Launcher (Mac/Linux)
# This script starts Chrome with remote debugging enabled on port 9222

echo "Starting Chrome with debugging port 9222..."

# Determine Chrome executable based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
else
    # Linux - try common paths
    if [ -x "$(command -v google-chrome)" ]; then
        CHROME_PATH="google-chrome"
    elif [ -x "$(command -v google-chrome-stable)" ]; then
        CHROME_PATH="google-chrome-stable"
    elif [ -x "$(command -v chromium)" ]; then
        CHROME_PATH="chromium"
    elif [ -x "$(command -v chromium-browser)" ]; then
        CHROME_PATH="chromium-browser"
    else
        echo "Error: Could not find Chrome or Chromium executable"
        exit 1
    fi
fi

# Create temp directory for Chrome debug profile
DEBUG_DIR="/tmp/chrome-debug"
mkdir -p "$DEBUG_DIR"

# Kill any existing Chrome instances using the debug port
pkill -f "chrome.*remote-debugging-port=9222" 2>/dev/null
sleep 2

# Start Chrome with debugging port
# --user-data-dir: Use a separate profile for debugging
# --remote-debugging-port: Enable remote debugging on port 9222
# --no-first-run: Skip first-run wizard
"$CHROME_PATH" --user-data-dir="$DEBUG_DIR" --remote-debugging-port=9222 --no-first-run &

# Wait for Chrome to start
sleep 5

echo ""
echo "Chrome started successfully!"
echo "Debugging port: 9222"
echo "Debug URL: http://127.0.0.1:9222"
echo ""
echo "You can now run the YouTube transcript extraction scripts."
echo ""
