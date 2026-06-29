#!/bin/bash
#==============================================================================
# Self-Improving Skill — Automated Setup Script
# Version: 2.1.0
# Usage: curl <url> | bash OR ./setup.sh [options]
#==============================================================================

set -e

# Detect OS for portable date
detect_os() {
    case "$(uname -s)" in
        Darwin*)  echo "darwin" ;;
        Linux*)   echo "linux" ;;
        MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
        *)        echo "unknown" ;;
    esac
}

OS="$(detect_os)"

# Portable date function
get_iso_timestamp() {
    if [ "$OS" = "darwin" ]; then
        date -u +%Y-%m-%dT%H:%M:%S%z
    else
        date -Iseconds 2>/dev/null || date -u +%Y-%m-%dT%H:%M:%S%z
    fi
}

# Configuration
SELF_IMPROVING_DIR="${SELF_IMPROVING_DIR:-$HOME/self-improving}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd -P 2>/dev/null || cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="$HOME/self-improving-backup-$(date +%Y%m%d-%H%M%S)"
MODE="normal"  # low | normal | high | heavy

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tier)
            MODE="$2"
            shift 2
            ;;
        --dir)
            SELF_IMPROVING_DIR="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "  --tier low|normal|high|heavy  Set usage tier (default: normal)"
            echo "  --dir <path>                   Set self-improving directory (default: ~/self-improving)"
            echo "  --help                        Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=============================================="
echo "Self-Improving Skill Setup v2.1.0"
echo "=============================================="
echo "Directory: $SELF_IMPROVING_DIR"
echo "Tier: $MODE"
echo ""

# Tier-specific limits
case $MODE in
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
esac

# Step 1: Backup existing directory
if [ -d "$SELF_IMPROVING_DIR" ]; then
    echo "[1/10] Backing up existing directory to $BACKUP_DIR..."
    cp -r "$SELF_IMPROVING_DIR" "$BACKUP_DIR"
    echo "  Backup created: $BACKUP_DIR"
else
    echo "[1/10] Creating new directory structure..."
    mkdir -p "$SELF_IMPROVING_DIR"
fi

# Step 2: Create directory structure
echo "[2/10] Creating directory structure..."
mkdir -p "$SELF_IMPROVING_DIR"/{projects,domains,archive}
echo "  Created: projects/, domains/, archive/"

# Step 3: Create config.json
echo "[3/10] Creating configuration..."
cat > "$SELF_IMPROVING_DIR/config.json" << EOF
{
  "version": "2.1.0",
  "tier": "$MODE",
  "limits": {
    "corrections": $CORRECTIONS_LIMIT,
    "pending": $PENDING_LIMIT,
    "hot": $HOT_LIMIT,
    "pendingObservationDays": 14,
    "pendingTimeoutDays": 30
  },
  "setupAt": "$(get_iso_timestamp)"
}
EOF
echo "  Created: config.json ($MODE tier)"

# Step 4: Create memory.md
echo "[4/10] Creating core files..."
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
echo "  Created: memory.md"

# Step 5: Create corrections.md (part of core files)
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
echo "  Created: corrections.md"

# Step 6: Create supporting files
echo "[6/10] Creating supporting files..."
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

echo "  Created: index.md, heartbeat-state.md"

# Step 7: Verify installation
echo "[7/10] Verifying installation..."
EXPECTED_FILES=(
    "$SELF_IMPROVING_DIR/memory.md"
    "$SELF_IMPROVING_DIR/corrections.md"
    "$SELF_IMPROVING_DIR/index.md"
    "$SELF_IMPROVING_DIR/heartbeat-state.md"
    "$SELF_IMPROVING_DIR/config.json"
    "$SELF_IMPROVING_DIR/projects"
    "$SELF_IMPROVING_DIR/domains"
    "$SELF_IMPROVING_DIR/archive"
)

ALL_PRESENT=true
for file in "${EXPECTED_FILES[@]}"; do
    if [ ! -e "$file" ]; then
        echo "  MISSING: $file"
        ALL_PRESENT=false
    fi
done

if $ALL_PRESENT; then
    echo "  All files verified."
else
    echo "  Verification failed!"
    exit 1
fi

# Step 8: Auto-integrate with workspace if files exist
echo "[8/10] Checking workspace integration..."
INTEGRATED_ANY=false

# CLAUDE.md integration
if [ -f "./CLAUDE.md" ]; then
    if ! grep -q "Self-Improving" ./CLAUDE.md 2>/dev/null; then
        echo "  Adding self-improving steering to CLAUDE.md..."
        cat >> ./CLAUDE.md << 'CLAUDE_EOF'

## Self-Improving
Compounding execution quality is part of the job.
Before non-trivial work, load `~/self-improving/memory.md` and only the smallest relevant domain or project files.
After corrections, failed attempts, or reusable lessons, write one concise entry to the correct self-improving file immediately.
Prefer learned rules when relevant, but keep self-inferred rules revisable.
Do not skip retrieval just because the task feels familiar.
CLAUDE_EOF
        echo "  ✓ CLAUDE.md updated"
        INTEGRATED_ANY=true
    else
        echo "  ✓ CLAUDE.md already has self-improving steering"
    fi
fi

# AGENTS.md integration
if [ -f "./AGENTS.md" ]; then
    if ! grep -q "self-improving" ./AGENTS.md 2>/dev/null; then
        # Add to Memory section if it exists
        if grep -q "^## Memory$" ./AGENTS.md 2>/dev/null; then
            echo "  Adding self-improving to AGENTS.md..."
            # Find the Memory section and add after it
            sed -i.bak '/^## Memory$/a\
\
- **Self-improving:** `~/self-improving/` (via `self-improving` skill) — execution-improvement memory (preferences, workflows, style patterns, what improved/worsened outcomes)' ./AGENTS.md
            rm ./AGENTS.md.bak 2>/dev/null || true
            echo "  ✓ AGENTS.md updated"
            INTEGRATED_ANY=true
        else
            echo "  ⚠ AGENTS.md found but no '## Memory' section — appending to end"
            cat >> ./AGENTS.md << 'AGENTS_EOF'

- **Self-improving:** `~/self-improving/` (via `self-improving` skill) — execution-improvement memory (preferences, workflows, style patterns, what improved/worsened outcomes)
AGENTS_EOF
            echo "  ✓ AGENTS.md updated (appended)"
            INTEGRATED_ANY=true
        fi
    else
        echo "  ✓ AGENTS.md already has self-improving"
    fi
fi

# HEARTBEAT.md integration
if [ -f "./HEARTBEAT.md" ]; then
    if ! grep -q "Self-Improving Check" ./HEARTBEAT.md 2>/dev/null; then
        echo "  Adding self-improving to HEARTBEAT.md..."
        cat >> ./HEARTBEAT.md << HEARTBEAT_EOF

## Self-Improving Check
- Read \`$SKILL_DIR/heartbeat-rules.md\`
- Use \`~/self-improving/heartbeat-state.md\` for last-run markers and action notes
- If no file inside \`~/self-improving/\` changed since the last reviewed change, return \`HEARTBEAT_OK\`
HEARTBEAT_EOF
        echo "  ✓ HEARTBEAT.md updated"
        INTEGRATED_ANY=true
    else
        echo "  ✓ HEARTBEAT.md already has self-improving"
    fi
fi

if [ "$INTEGRATED_ANY" = false ] && [ ! -f "./CLAUDE.md" ] && [ ! -f "./AGENTS.md" ] && [ ! -f "./HEARTBEAT.md" ]; then
    echo "  No workspace files (CLAUDE.md, AGENTS.md, HEARTBEAT.md) found in current directory."
    echo "  Run setup from your workspace root, or integrate manually (see setup.md)."
fi

# Step 9: Create verification script
echo "[9/10] Creating verification script..."
cat > "$SELF_IMPROVING_DIR/verify.sh" << 'VERIFY_EOF'
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

# Check workspace integration
echo ""
echo "Workspace Integration:"
[ -f "./CLAUDE.md" ] && grep -q "Self-Improving" ./CLAUDE.md && pass "CLAUDE.md integrated" || warn "CLAUDE.md not integrated"
[ -f "./AGENTS.md" ] && grep -q "self-improving" ./AGENTS.md && pass "AGENTS.md integrated" || warn "AGENTS.md not integrated"
[ -f "./HEARTBEAT.md" ] && grep -q "Self-Improving" ./HEARTBEAT.md && pass "HEARTBEAT.md integrated" || warn "HEARTBEAT.md not integrated"

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
VERIFY_EOF
chmod +x "$SELF_IMPROVING_DIR/verify.sh"
echo "  Created: verify.sh"

# Step 10: Summary
echo "[10/10] Setup complete!"
echo ""
echo "=============================================="
echo "Summary"
echo "=============================================="
echo "Directory: $SELF_IMPROVING_DIR"
echo "Tier: $MODE"
echo ""
echo "Next steps:"
echo "  1. Verify installation: bash ~/self-improving/verify.sh"
echo "  2. Check memory stats: bash scripts/stats.sh"
echo "  3. Run heartbeat: bash scripts/heartbeat.sh"
echo ""
echo "Workspace integration:"
echo "  ✓ CLAUDE.md auto-integrated (if present)"
echo "  ✓ AGENTS.md auto-integrated (if present)"
echo "  ✓ HEARTBEAT.md auto-integrated (if present)"
echo ""
echo "Commands:"
echo "  bash ~/self-improving/verify.sh  — Verify installation"
echo "  bash scripts/stats.sh            — Show memory statistics"
echo "  bash scripts/heartbeat.sh         — Run heartbeat maintenance"
echo ""
echo "Documentation: $SKILL_DIR/setup.md"
echo "Glossary: $SKILL_DIR/glossary.md"
echo ""
echo "Backup location (if existed): $BACKUP_DIR"
echo "=============================================="
