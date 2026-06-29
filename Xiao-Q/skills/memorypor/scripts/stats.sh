#!/bin/bash
#==============================================================================
# Self-Improving — Memory Statistics
# Version: 2.1.0
# Usage: bash stats.sh [--json]
#==============================================================================

SELF_IMPROVING_DIR="${SELF_IMPROVING_DIR:-$HOME/self-improving}"
CONFIG_FILE="$SELF_IMPROVING_DIR/config.json"
OUTPUT_JSON=false

#-------------------------------------------------------------------------------
# Dependency checks
#-------------------------------------------------------------------------------
check_dependencies() {
    local missing_deps=()

    # Check for jq (optional - will use fallback)
    if ! command -v jq &>/dev/null; then
        echo "⚠️  Notice: 'jq' not found. Using fallback values for config."
        echo "   Install jq for better performance: brew install jq (macOS) or apt install jq (Linux)"
    fi

    # Check for required files
    if [ ! -d "$SELF_IMPROVING_DIR" ]; then
        echo "❌ Error: Self-improving directory not found: $SELF_IMPROVING_DIR"
        echo "   Run 'bash scripts/setup.sh' to initialize."
        exit 1
    fi

    if [ ! -f "$SELF_IMPROVING_DIR/memory.md" ]; then
        echo "❌ Error: memory.md not found. Memory not initialized."
        echo "   Run 'bash scripts/setup.sh' to initialize."
        exit 1
    fi
}

# Run dependency checks
check_dependencies

if [ "$1" = "--json" ]; then
    OUTPUT_JSON=true
fi

# Helper functions
get_config() {
    local key="$1"
    local default="$2"
    if [ -f "$CONFIG_FILE" ] && command -v jq &>/dev/null; then
        jq -r ".$key // $default" "$CONFIG_FILE" 2>/dev/null || echo "$default"
    else
        echo "$default"
    fi
}

# Gather statistics
TIER=$(get_config "tier" "normal")
CORRECTIONS_LIMIT=$(get_config "limits.corrections" 200)
PENDING_LIMIT=$(get_config "limits.pending" 100)
HOT_LIMIT=$(get_config "limits.hot" 200)
OBSERVATION_DAYS=$(get_config "limits.pendingObservationDays" 14)
TIMEOUT_DAYS=$(get_config "limits.pendingTimeoutDays" 30)

# Count entries
MEMORY_LINES=$(wc -l < "$SELF_IMPROVING_DIR/memory.md" 2>/dev/null || echo 0)
CORRECTIONS_COUNT=$(grep -c "^## " "$SELF_IMPROVING_DIR/corrections.md" 2>/dev/null || echo 0)
PENDING_COUNT=$(grep -c "^## " "$SELF_IMPROVING_DIR/corrections-pending.md" 2>/dev/null || echo 0)
PROJECTS_COUNT=$(find "$SELF_IMPROVING_DIR/projects" -type f 2>/dev/null | wc -l || echo 0)
DOMAINS_COUNT=$(find "$SELF_IMPROVING_DIR/domains" -type f 2>/dev/null | wc -l || echo 0)
ARCHIVE_COUNT=$(find "$SELF_IMPROVING_DIR/archive" -type f 2>/dev/null | wc -l || echo 0)

# Calculate percentages
CORRECTIONS_PCT=$((CORRECTIONS_COUNT * 100 / CORRECTIONS_LIMIT))
PENDING_PCT=$((PENDING_COUNT * 100 / PENDING_LIMIT))
HOT_PCT=$((MEMORY_LINES * 100 / HOT_LIMIT))

# Health status
HEALTH="healthy"
if [ "$CORRECTIONS_PCT" -ge 100 ] || [ "$PENDING_PCT" -ge 100 ] || [ "$HOT_PCT" -ge 100 ]; then
    HEALTH="critical"
elif [ "$CORRECTIONS_PCT" -ge 80 ] || [ "$PENDING_PCT" -ge 80 ] || [ "$HOT_PCT" -ge 90 ]; then
    HEALTH="warning"
fi

# Recent activity (last 7 days)
RECENT_CORRECTIONS=$(grep -c "^## 202" "$SELF_IMPROVING_DIR/corrections.md" 2>/dev/null | tail -7 | head -1 || echo 0)

if [ "$OUTPUT_JSON" = true ]; then
    cat << EOF
{
  "tier": "$TIER",
  "stats": {
    "memory": {
      "lines": $MEMORY_LINES,
      "limit": $HOT_LIMIT,
      "percent": $HOT_PCT
    },
    "corrections": {
      "count": $CORRECTIONS_COUNT,
      "limit": $CORRECTIONS_LIMIT,
      "percent": $CORRECTIONS_PCT
    },
    "pending": {
      "count": $PENDING_COUNT,
      "limit": $PENDING_LIMIT,
      "percent": $PENDING_PCT
    }
  },
  "namespaces": {
    "projects": $PROJECTS_COUNT,
    "domains": $DOMAINS_COUNT,
    "archive": $ARCHIVE_COUNT
  },
  "health": "$HEALTH",
  "config": {
    "observationDays": $OBSERVATION_DAYS,
    "timeoutDays": $TIMEOUT_DAYS
  }
}
EOF
else
    # Progress bar function (fully portable - bash built-in only)
    progress_bar() {
        local percent=$1
        local width=20
        local filled=$((percent * width / 100))
        if [ "$percent" -ge 100 ]; then
            filled=$width
        fi
        printf "["
        local i=1
        while [ "$i" -le "$width" ]; do
            if [ "$i" -le "$filled" ]; then
                printf "#"
            else
                printf "-"
            fi
            i=$((i + 1))
        done
        printf "] %d%%" "$percent"
    }

    echo ""
    echo "=============================================="
    echo "         Self-Improving Memory Stats"
    echo "=============================================="
    echo ""
    echo "Tier: $TIER"
    echo ""
    echo "HOT (memory.md)"
    echo "  $(progress_bar $HOT_PCT) ($MEMORY_LINES/$HOT_LIMIT lines)"
    echo ""
    echo "WARM (corrections + pending)"
    echo "  Corrections: $(progress_bar $CORRECTIONS_PCT) ($CORRECTIONS_COUNT/$CORRECTIONS_LIMIT)"
    echo "  Pending:     $(progress_bar $PENDING_PCT) ($PENDING_COUNT/$PENDING_LIMIT)"
    echo ""
    echo "Namespaces"
    echo "  Projects: $PROJECTS_COUNT"
    echo "  Domains:  $DOMAINS_COUNT"
    echo "  Archive:   $ARCHIVE_COUNT"
    echo ""
    echo "Health: $HEALTH"
    echo ""
    echo "=============================================="
    echo ""

    # Warnings
    if [ "$HEALTH" = "critical" ]; then
        echo "⚠️  WARNING: Memory at critical levels!"
        [ "$CORRECTIONS_PCT" -ge 100 ] && echo "  - corrections.md is full"
        [ "$PENDING_PCT" -ge 100 ] && echo "  - corrections-pending.md is full"
        [ "$HOT_PCT" -ge 100 ] && echo "  - memory.md is full"
        echo ""
        echo "Actions:"
        echo "  1. Review corrections-pending.md for timed-out entries"
        echo "  2. Promote or archive stale entries"
        echo "  3. Consider running memory compression"
        echo ""
    elif [ "$HEALTH" = "warning" ]; then
        echo "⚡ NOTICE: Memory approaching limits"
        [ "$CORRECTIONS_PCT" -ge 80 ] && echo "  - corrections.md at ${CORRECTIONS_PCT}%"
        [ "$PENDING_PCT" -ge 80 ] && echo "  - corrections-pending.md at ${PENDING_PCT}%"
        [ "$HOT_PCT" -ge 90 ] && echo "  - memory.md at ${HOT_PCT}%"
        echo ""
    fi
fi
