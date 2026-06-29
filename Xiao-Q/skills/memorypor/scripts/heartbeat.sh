#!/bin/bash
#==============================================================================
# Self-Improving Heartbeat — Executable Script
# Version: 2.1.0
# Usage: bash heartbeat.sh
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
STATE_FILE="$SELF_IMPROVING_DIR/heartbeat-state.md"
CONFIG_FILE="$SELF_IMPROVING_DIR/config.json"

#-------------------------------------------------------------------------------
# Dependency checks
#-------------------------------------------------------------------------------
check_dependencies() {
    # Check for required directory
    if [ ! -d "$SELF_IMPROVING_DIR" ]; then
        echo "❌ Error: Self-improving directory not found: $SELF_IMPROVING_DIR"
        echo "   Run 'bash scripts/setup.sh' to initialize."
        exit 1
    fi

    # Check for jq (optional)
    if ! command -v jq &>/dev/null; then
        echo "⚠️  Notice: 'jq' not found. Using fallback config values."
    fi
}

# Run dependency checks
check_dependencies

#-------------------------------------------------------------------------------
# Helper functions
#-------------------------------------------------------------------------------

log_action() {
    echo "$1" >> "$STATE_FILE.tmp"
}

get_config() {
    local key="$1"
    local default="$2"
    if [ -f "$CONFIG_FILE" ] && command -v jq &>/dev/null; then
        jq -r ".$key // $default" "$CONFIG_FILE" 2>/dev/null || echo "$default"
    else
        echo "$default"
    fi
}

#-------------------------------------------------------------------------------
# Retry mechanism with exponential backoff
#-------------------------------------------------------------------------------

retry_with_backoff() {
    local max_attempts="${1:-3}"
    local initial_delay="${2:-1}"
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if "$@"; then
            return 0
        fi

        if [ $attempt -lt $max_attempts ]; then
            local delay=$((initial_delay * 2 ** (attempt - 1)))
            echo "⚠️  Attempt $attempt failed, retrying in ${delay}s..." >&2
            sleep "$delay"
        fi

        attempt=$((attempt + 1))
    done

    echo "❌ All $max_attempts attempts failed" >&2
    return 1
}

#-------------------------------------------------------------------------------
# Execute with retry wrapper
#-------------------------------------------------------------------------------

execute_with_retry() {
    retry_with_backoff 3 1 main "$@"
}

#-------------------------------------------------------------------------------
# Main heartbeat logic
#-------------------------------------------------------------------------------

main() {
    # Read limits from config
    local CORRECTIONS_LIMIT=$(get_config "limits.corrections" 200)
    local PENDING_LIMIT=$(get_config "limits.pending" 100)
    local OBSERVATION_DAYS=$(get_config "limits.pendingObservationDays" 14)
    local TIMEOUT_DAYS=$(get_config "limits.pendingTimeoutDays" 30)

    # Create temp state file
    {
        echo "# Self-Improving Heartbeat State"
        echo ""
        echo "last_heartbeat_started_at: $(get_iso_timestamp)"
    } > "$STATE_FILE.tmp"

    # Preserve last_reviewed_change_at
    local LAST_REVIEWED="never"
    if [ -f "$STATE_FILE" ]; then
        LAST_REVIEWED=$(grep 'last_reviewed_change_at:' "$STATE_FILE" 2>/dev/null | cut -d: -f2- | tr -d ' ' || echo "never")
    fi
    echo "last_reviewed_change_at: $LAST_REVIEWED" >> "$STATE_FILE.tmp"

    # Scan for changes since last review
    local CHANGED_FILES=""
    if [ "$LAST_REVIEWED" = "never" ] || [ -z "$LAST_REVIEWED" ]; then
        # First run — scan all files
        CHANGED_FILES=$(find "$SELF_IMPROVING_DIR" -type f \( -name "*.md" -o -name "*.json" \) 2>/dev/null | grep -v "heartbeat-state.md" || true)
    else
        # Find files newer than last review
        CHANGED_FILES=$(find "$SELF_IMPROVING_DIR" -type f \( -name "*.md" -o -name "*.json" \) -newer "$STATE_FILE" 2>/dev/null | grep -v "heartbeat-state.md" || true)
    fi

    # Begin actions log
    echo "" >> "$STATE_FILE.tmp"
    echo "## Last actions" >> "$STATE_FILE.tmp"

    # Check if anything changed
    if [ -z "$CHANGED_FILES" ]; then
        echo "last_heartbeat_result: HEARTBEAT_OK" >> "$STATE_FILE.tmp"
        echo "- no material change" >> "$STATE_FILE.tmp"
        mv "$STATE_FILE.tmp" "$STATE_FILE"
        echo "HEARTBEAT_OK"
        exit 0
    fi

    # Changes found — perform conservative checks
    echo "last_heartbeat_result: HEARTBEAT_ACTION" >> "$STATE_FILE.tmp"

    # Check corrections.md size
    local CORRECTIONS_COUNT=$(grep -c "^## " "$SELF_IMPROVING_DIR/corrections.md" 2>/dev/null || echo 0)
    if [ "$CORRECTIONS_COUNT" -ge "$CORRECTIONS_LIMIT" ]; then
        log_action "- WARNING: corrections.md at $CORRECTIONS_COUNT/$CORRECTIONS_LIMIT"
        log_action "  Action: Review corrections-pending.md overflow handling"
    elif [ "$CORRECTIONS_COUNT" -ge $((CORRECTIONS_LIMIT * 80 / 100)) ]; then
        log_action "- NOTE: corrections.md approaching limit ($CORRECTIONS_COUNT/$CORRECTIONS_LIMIT)"
    fi

    # Check memory.md size
    local MEMORY_LINES=$(wc -l < "$SELF_IMPROVING_DIR/memory.md" 2>/dev/null || echo 0)
    local HOT_LIMIT=$(get_config "limits.hot" 200)
    if [ "$MEMORY_LINES" -ge "$HOT_LIMIT" ]; then
        log_action "- WARNING: memory.md at ${MEMORY_LINES}lines (limit: $HOT_LIMIT)"
        log_action "  Action: Consider compression of HOT tier"
    elif [ "$MEMORY_LINES" -ge $((HOT_LIMIT * 90 / 100)) ]; then
        log_action "- NOTE: memory.md approaching limit (${MEMORY_LINES}/$HOT_LIMIT lines)"
    fi

    # Check corrections-pending.md observation candidates
    if [ -f "$SELF_IMPROVING_DIR/corrections-pending.md" ]; then
        local PENDING_COUNT=$(grep -c "^## " "$SELF_IMPROVING_DIR/corrections-pending.md" 2>/dev/null || echo 0)
        if [ "$PENDING_COUNT" -ge "$PENDING_LIMIT" ]; then
            log_action "- WARNING: corrections-pending.md at $PENDING_COUNT/$PENDING_LIMIT"
            log_action "  Action: Review timed-out entries for archive"
        elif [ "$PENDING_COUNT" -gt 0 ]; then
            log_action "- NOTE: corrections-pending.md has $PENDING_COUNT entries"
        fi
    fi

    # Check index.md sync
    if [ -f "$SELF_IMPROVING_DIR/index.md" ]; then
        local INDEX_MEMORY_LINES=$(grep "memory.md:" "$SELF_IMPROVING_DIR/index.md" 2>/dev/null | grep -oE '[0-9]+' | head -1 || echo 0)
        if [ "$INDEX_MEMORY_LINES" != "$MEMORY_LINES" ] && [ "$MEMORY_LINES" -gt 0 ]; then
            log_action "- NOTE: index.md may be stale (shows $INDEX_MEMORY_LINES lines, actual $MEMORY_LINES)"
        fi
    fi

    # Update last_reviewed_change_at
    echo "last_reviewed_change_at: $(get_iso_timestamp)" >> "$STATE_FILE.tmp"

    # Atomic replace
    mv "$STATE_FILE.tmp" "$STATE_FILE"

    # Output result
    echo "HEARTBEAT_ACTION"
    echo "Review suggested actions in $STATE_FILE"

    exit 0
}

# Run with retry mechanism
execute_with_retry "$@"
