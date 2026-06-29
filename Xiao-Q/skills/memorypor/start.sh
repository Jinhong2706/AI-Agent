#!/bin/bash
#==============================================================================
# Self-Improving Skill — One-Line Installer
# Version: 2.1.0
# Usage: curl -sL <raw-url>/start.sh | bash
#        OR: bash start.sh [--tier low|normal|high|heavy]
#==============================================================================

set -e

# Configuration
DEFAULT_TIER="normal"
TIER="${TIER:-normal}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tier)
            TIER="$2"
            shift 2
            ;;
        --help)
            echo "Usage: curl -sL <url>/start.sh | bash"
            echo "   OR: bash start.sh [--tier low|normal|high|heavy]"
            echo ""
            echo "Options:"
            echo "  --tier low|normal|high|heavy  Set usage tier (default: normal)"
            echo "  --help                        Show this help"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# Detect OS for platform-specific behavior
detect_os() {
    case "$(uname -s)" in
        Darwin*)  echo "darwin" ;;
        Linux*)   echo "linux" ;;
        MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
        *)        echo "unknown" ;;
    esac
}

OS="$(detect_os)"

echo "=============================================="
echo "Self-Improving Skill — Quick Setup"
echo "=============================================="
echo "Detected OS: $OS"
echo "Tier: $TIER"
echo ""

# Step 1: Detect if we're running from an installed location or need to download
SELF_IMPROVING_DIR="${SELF_IMPROVING_DIR:-$HOME/self-improving}"

# Step 2: Check if already installed
if [ -d "$SELF_IMPROVING_DIR" ] && [ -f "$SELF_IMPROVING_DIR/config.json" ]; then
    echo "Self-improving is already installed at: $SELF_IMPROVING_DIR"
    echo "To reinstall, remove the directory first."
    echo ""
    echo "Next steps:"
    echo "  bash \$SELF_IMPROVING_DIR/scripts/stats.sh      — View statistics"
    echo "  bash \$SELF_IMPROVING_DIR/scripts/heartbeat.sh  — Run heartbeat"
    exit 0
fi

# Step 3: Create directory structure
echo "[1/4] Creating directory structure..."
mkdir -p "$SELF_IMPROVING_DIR"/{projects,domains,archive}

# Step 4: Create config.json
echo "[2/4] Creating configuration..."

# Tier-specific limits
case "$TIER" in
    low)
        CORRECTIONS_LIMIT=200; PENDING_LIMIT=100; HOT_LIMIT=200
        ;;
    normal)
        CORRECTIONS_LIMIT=300; PENDING_LIMIT=150; HOT_LIMIT=300
        ;;
    high)
        CORRECTIONS_LIMIT=500; PENDING_LIMIT=300; HOT_LIMIT=400
        ;;
    heavy)
        CORRECTIONS_LIMIT=1000; PENDING_LIMIT=500; HOT_LIMIT=500
        ;;
    *)
        CORRECTIONS_LIMIT=300; PENDING_LIMIT=150; HOT_LIMIT=300
        ;;
esac

# Portable date formatting
DATE_CMD="date"
if [ "$OS" = "darwin" ]; then
    # macOS date -I is available but -Iseconds is not
    CREATED_AT="$($DATE_CMD -u +%Y-%m-%dT%H:%M:%S%z)"
else
    # GNU date supports -Iseconds
    CREATED_AT="$($DATE_CMD -Iseconds 2>/dev/null || $DATE_CMD -u +%Y-%m-%dT%H:%M:%S%z)"
fi

cat > "$SELF_IMPROVING_DIR/config.json" << EOF
{
  "version": "2.0.0",
  "tier": "$TIER",
  "limits": {
    "corrections": $CORRECTIONS_LIMIT,
    "pending": $PENDING_LIMIT,
    "hot": $HOT_LIMIT,
    "pendingObservationDays": 14,
    "pendingTimeoutDays": 30
  },
  "setupAt": "$CREATED_AT"
}
EOF

# Step 5: Create core files
echo "[3/4] Creating core files..."

cat > "$SELF_IMPROVING_DIR/memory.md" << 'EOF'
# Self-Improving Memory (HOT Tier)

## Confirmed Preferences
<!-- Patterns confirmed by user, never decay -->

## Active Patterns
<!-- Patterns observed 3+ times, subject to decay -->

## Recent (last 7 days)
<!-- New corrections pending confirmation -->

## Quick Reference
- Promoted rules cite source: "Promoted from corrections.md:date"
- See glossary.md for terminology
EOF

cat > "$SELF_IMPROVING_DIR/corrections.md" << 'EOF'
# Corrections Log

<!-- Format:
## YYYY-MM-DD HH:MM — [Type]
- **Correction:** "what user said"
- **Context:** where it happened
- **Count:** N (for promotion tracking)
- **Status:** pending | confirmed | promoted | archived

Type categories: format | technical | communication | project | domain
-->

## Log

EOF

cat > "$SELF_IMPROVING_DIR/index.md" << 'EOF'
# Memory Index

## HOT (always loaded)
- memory.md: 0 lines

## WARM (load on demand)
- projects/: 0 files
- domains/: 0 files

## COLD (archived)
- archive/: 0 files

## Statistics
Last updated: never
Total entries: 0
Promotions: 0
Demotions: 0
EOF

cat > "$SELF_IMPROVING_DIR/heartbeat-state.md" << 'EOF'
# Self-Improving Heartbeat State

last_heartbeat_started_at: never
last_reviewed_change_at: never
last_heartbeat_result: never

## Last actions
- none yet
EOF

# Step 6: Create verification script
echo "[4/4] Creating verification script..."
cat > "$SELF_IMPROVING_DIR/verify.sh" << 'VERIFYEOF'
#!/bin/bash
# Self-Improving Verification Script
# Run: bash ~/self-improving/verify.sh

set -e
SELF_IMPROVING_DIR="${SELF_IMPROVING_DIR:-$HOME/self-improving}"
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; errors=$((errors+1)); }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }

errors=0
echo "=============================================="
echo "Self-Improving Verification"
echo "=============================================="

# Check directory
[ -d "$SELF_IMPROVING_DIR" ] && pass "Directory exists: $SELF_IMPROVING_DIR" || fail "Directory missing: $SELF_IMPROVING_DIR"

# Check core files
for f in memory.md corrections.md index.md heartbeat-state.md config.json; do
    [ -f "$SELF_IMPROVING_DIR/$f" ] && pass "File exists: $f" || fail "File missing: $f"
done

# Check directories
for d in projects domains archive; do
    [ -d "$SELF_IMPROVING_DIR/$d" ] && pass "Directory exists: $d" || fail "Directory missing: $d"
done

# Summary
echo ""
echo "=============================================="
if [ $errors -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}$errors check(s) failed${NC}"
    exit 1
fi
VERIFYEOF
chmod +x "$SELF_IMPROVING_DIR/verify.sh"

echo ""
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "Directory: $SELF_IMPROVING_DIR"
echo "Tier: $TIER"
echo ""
echo "Next steps:"
echo "  bash $SELF_IMPROVING_DIR/verify.sh         — Verify installation"
echo "  bash $SELF_IMPROVING_DIR/scripts/stats.sh — View statistics (if scripts available)"
echo ""
echo "For full setup with scripts, clone the skill to your skills directory."
echo "=============================================="
