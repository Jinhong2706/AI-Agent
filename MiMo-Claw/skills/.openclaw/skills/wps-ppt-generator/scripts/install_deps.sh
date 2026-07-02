#!/bin/bash
# Install dependencies for HTML PPT Generator skill

set -e

echo "Checking and installing dependencies..."

# Check python-pptx
python3 -c "import pptx" 2>/dev/null || {
    echo "Installing python-pptx..."
    pip install "python-pptx>=0.6.21"
}

# Check playwright
python3 -c "import playwright" 2>/dev/null || {
    echo "Installing playwright..."
    pip install "playwright>=1.40.0"
}

# Check if chromium browser is installed for playwright
if ! python3 -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(); p.stop()" 2>/dev/null; then
    echo "Installing Playwright Chromium browser..."
    playwright install chromium
fi

echo "All dependencies ready."
