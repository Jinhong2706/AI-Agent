#!/bin/bash
# agent-browser setup script
# Installs agent-browser globally and downloads Chromium

set -e

echo "🌐 Installing agent-browser..."

# Check if already installed
if command -v agent-browser &>/dev/null; then
    VERSION=$(agent-browser --version 2>/dev/null || echo "unknown")
    echo "✓ agent-browser already installed: $VERSION"
else
    npm install -g agent-browser
    echo "✓ agent-browser installed"
fi

# Install Chromium（已通过 AGENT_BROWSER_EXECUTABLE_PATH 指定现成 chromium 时复用，不再重复下载）
if [[ -n "$AGENT_BROWSER_EXECUTABLE_PATH" && -x "$AGENT_BROWSER_EXECUTABLE_PATH" ]]; then
    echo "✓ 复用已有 Chromium: $AGENT_BROWSER_EXECUTABLE_PATH，跳过下载"
else
    echo "📦 Installing Chromium browser..."
    if [[ "$(uname)" == "Linux" ]]; then
        agent-browser install --with-deps 2>/dev/null || agent-browser install
    else
        agent-browser install
    fi
    echo "✓ Chromium ready"
fi

# Verify
echo ""
echo "🧪 Verifying..."
agent-browser open https://example.com >/dev/null 2>&1
TITLE=$(agent-browser get title 2>/dev/null || echo "")
agent-browser close >/dev/null 2>&1

if [[ "$TITLE" == *"Example"* ]]; then
    echo "✅ agent-browser is working!"
else
    echo "⚠️  Installation complete but verification unclear. Try: agent-browser open https://example.com"
fi

agent-browser --version
