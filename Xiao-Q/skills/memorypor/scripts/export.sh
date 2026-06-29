#!/bin/bash
#==============================================================================
# Self-Improving — Export Memory
# Version: 2.1.0
# Usage: bash export.sh [output-path]
#==============================================================================

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

SELF_IMPROVING_DIR="${SELF_IMPROVING_DIR:-$HOME/self-improving}"
OUTPUT_PATH="${1:-$HOME/self-improving-export-$(date +%Y%m%d-%H%M%S).zip}"

#-------------------------------------------------------------------------------
# Dependency checks
#-------------------------------------------------------------------------------
check_dependencies() {
    local missing_deps=()

    # Check for required directory
    if [ ! -d "$SELF_IMPROVING_DIR" ]; then
        echo "❌ Error: Self-improving directory not found: $SELF_IMPROVING_DIR"
        echo "   Run 'bash scripts/setup.sh' to initialize."
        exit 1
    fi

    # Check for zip command
    if ! command -v zip &>/dev/null; then
        echo "❌ Error: 'zip' command not found."
        echo "   Install it with: brew install zip (macOS) or apt install zip (Linux)"
        exit 1
    fi

    # Check for jq (optional)
    if ! command -v jq &>/dev/null; then
        echo "⚠️  Notice: 'jq' not found. Stats display will be limited."
    fi
}

check_dependencies

echo "Self-Improving Export"
echo "===================="
echo "Source: $SELF_IMPROVING_DIR"
echo "Output: $OUTPUT_PATH"
echo ""

# Create temp directory for export
EXPORT_DIR=$(mktemp -d)
trap "rm -rf $EXPORT_DIR" EXIT

# Copy all files preserving structure
cp -r "$SELF_IMPROVING_DIR" "$EXPORT_DIR/self-improving"

# Create manifest
TIMESTAMP="$(get_iso_timestamp)"
cat > "$EXPORT_DIR/manifest.json" << EOF
{
  "version": "2.1.0",
  "exportedAt": "$TIMESTAMP",
  "sourceDir": "$SELF_IMPROVING_DIR",
  "stats": {
    "memoryLines": $(wc -l < "$SELF_IMPROVING_DIR/memory.md" 2>/dev/null || echo 0),
    "correctionsCount": $(grep -c "^## " "$SELF_IMPROVING_DIR/corrections.md" 2>/dev/null || echo 0),
    "pendingCount": $(grep -c "^## " "$SELF_IMPROVING_DIR/corrections-pending.md" 2>/dev/null || echo 0),
    "projectsCount": $(find "$SELF_IMPROVING_DIR/projects" -type f 2>/dev/null | wc -l || echo 0),
    "domainsCount": $(find "$SELF_IMPROVING_DIR/domains" -type f 2>/dev/null | wc -l || echo 0),
    "archiveCount": $(find "$SELF_IMPROVING_DIR/archive" -type f 2>/dev/null | wc -l || echo 0)
  }
}
EOF

# Create export archive
cd "$EXPORT_DIR"
if zip -r "$OUTPUT_PATH" self-improving manifest.json 2>/dev/null; then
    echo ""
    echo "Export complete!"
    echo ""
    echo "Contents:"
    echo "  - self-improving/ (all memory files)"
    echo "  - manifest.json (export metadata)"
    echo ""
    echo "Stats:"
    if command -v jq &>/dev/null; then
        jq '.stats' "$EXPORT_DIR/manifest.json"
    else
        cat "$EXPORT_DIR/manifest.json"
    fi
else
    echo "❌ Error: Failed to create zip archive."
    exit 1
fi
