#!/bin/bash
#==============================================================================
# Self-Improving — Import Memory
# Version: 2.1.0
# Usage: bash import.sh <export-file> [options]
# Options:
#   --merge      Merge with existing memory (default: backup and replace)
#   --dry-run    Show what would be imported without applying
#==============================================================================

SELF_IMPROVING_DIR="${SELF_IMPROVING_DIR:-$HOME/self-improving}"
MODE="replace"  # replace | merge | dry-run

#-------------------------------------------------------------------------------
# Dependency checks
#-------------------------------------------------------------------------------
check_dependencies() {
    # Check for unzip command
    if ! command -v unzip &>/dev/null; then
        echo "❌ Error: 'unzip' command not found."
        echo "   Install it with: brew install unzip (macOS) or apt install unzip (Linux)"
        exit 1
    fi
}

#-------------------------------------------------------------------------------
# Helper functions
#-------------------------------------------------------------------------------
log() {
    echo "[$(date '+%H:%M:%S')] $1"
}

merge_entries() {
    local source_file="$1"
    local target_file="$2"
    local merged_file="$3"

    if [ ! -f "$source_file" ]; then
        log "Source file not found: $source_file"
        return 1
    fi

    # Create backup of target
    if [ -f "$target_file" ]; then
        cp "$target_file" "${target_file}.backup"
    fi

    # Simple merge: append new entries from source to target
    # Skip headers in source file
    local source_has_header=false
    if grep -q "^# " "$source_file" 2>/dev/null; then
        source_has_header=true
    fi

    # Copy target to merged
    if [ -f "$target_file" ]; then
        cp "$target_file" "$merged_file"
    else
        touch "$merged_file"
    fi

    # Append non-header entries from source
    if [ "$source_has_header" = true ]; then
        # Find last header line and append after it
        local last_header_line=$(grep -n "^## " "$source_file" 2>/dev/null | tail -1 | cut -d: -f1)
        if [ -n "$last_header_line" ]; then
            tail -n +$((last_header_line + 1)) "$source_file" >> "$merged_file"
        else
            tail -n +2 "$source_file" >> "$merged_file" 2>/dev/null || true
        fi
    else
        cat "$source_file" >> "$merged_file"
    fi

    log "Merged: $source_file -> $target_file"
}

#-------------------------------------------------------------------------------
# Parse arguments
#-------------------------------------------------------------------------------
IMPORT_FILE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --merge)
            MODE="merge"
            shift
            ;;
        --dry-run)
            MODE="dry-run"
            shift
            ;;
        *.zip)
            IMPORT_FILE="$1"
            shift
            ;;
        --help)
            echo "Usage: $0 <export-file> [options]"
            echo "  --merge     Merge with existing memory"
            echo "  --dry-run   Show what would be imported"
            echo "  --help      Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ -z "$IMPORT_FILE" ]; then
    echo "❌ Error: Import file required"
    echo "Usage: $0 <export-file> [options]"
    echo "   Run 'bash scripts/export.sh' first to create an export file."
    exit 1
fi

check_dependencies

echo "Self-Improving Import"
echo "===================="
echo "Mode: $MODE"
echo "Import file: $IMPORT_FILE"
echo "Target: $SELF_IMPROVING_DIR"
echo ""

# Check if import file exists
if [ ! -f "$IMPORT_FILE" ]; then
    echo "❌ Error: $IMPORT_FILE does not exist"
    exit 1
fi

# Create temp directory for extraction
IMPORT_DIR=$(mktemp -d)
trap "rm -rf $IMPORT_DIR" EXIT

# Extract archive
echo "Extracting..."
if ! unzip -q "$IMPORT_FILE" -d "$IMPORT_DIR" 2>/dev/null; then
    echo "❌ Error: Failed to extract archive. File may be corrupted."
    exit 1
fi

# Check manifest
if [ ! -f "$IMPORT_DIR/manifest.json" ]; then
    echo "❌ Error: Invalid export file (no manifest.json)"
    echo "   The file may be corrupted or not a valid self-improving export."
    exit 1
fi

# Show import info
echo ""
echo "Import summary:"
if command -v jq &>/dev/null; then
    jq '.stats' "$IMPORT_DIR/manifest.json" 2>/dev/null || cat "$IMPORT_DIR/manifest.json"
else
    cat "$IMPORT_DIR/manifest.json"
fi
echo ""

if [ "$MODE" = "dry-run" ]; then
    echo "Dry run — no changes made"
    echo ""
    echo "Would import:"
    find "$IMPORT_DIR/self-improving" -type f \( -name "*.md" -o -name "*.json" \) 2>/dev/null | while read -r f; do
        echo "  $(basename "$f"): $(wc -l < "$f" 2>/dev/null || echo 0) lines"
    done
    echo ""
    echo "Merge strategy for $MODE mode:"
    echo "  - memory.md: Would add new entries to existing"
    echo "  - corrections.md: Would add new entries to existing"
    echo "  - Other files: Would be copied/merged"
    exit 0
fi

# Backup existing directory
if [ -d "$SELF_IMPROVING_DIR" ]; then
    BACKUP_DIR="$HOME/self-improving-backup-$(date +%Y%m%d-%H%M%S)"
    echo "Backing up existing to $BACKUP_DIR..."
    if ! cp -r "$SELF_IMPROVING_DIR" "$BACKUP_DIR"; then
        echo "❌ Error: Failed to create backup"
        exit 1
    fi
    echo "Backup created: $BACKUP_DIR"
    echo ""
fi

# Perform import based on mode
if [ "$MODE" = "merge" ]; then
    echo "Merging memory..."
    echo ""

    # Create temp merged directory
    MERGED_DIR=$(mktemp -d)
    trap "rm -rf $MERGED_DIR" EXIT

    # Copy existing structure
    cp -r "$SELF_IMPROVING_DIR" "$MERGED_DIR/merged"

    # Merge core files
    log "Merging memory.md..."
    merge_entries \
        "$IMPORT_DIR/self-improving/memory.md" \
        "$SELF_IMPROVING_DIR/memory.md" \
        "$MERGED_DIR/merged/memory.md"

    log "Merging corrections.md..."
    merge_entries \
        "$IMPORT_DIR/self-improving/corrections.md" \
        "$SELF_IMPROVING_DIR/corrections.md" \
        "$MERGED_DIR/merged/corrections.md"

    # For other files, just copy from import (newer wins)
    for subdir in projects domains archive; do
        if [ -d "$IMPORT_DIR/self-improving/$subdir" ]; then
            log "Merging $subdir/..."
            for f in "$IMPORT_DIR/self-improving/$subdir"/*; do
                if [ -f "$f" ]; then
                    fname=$(basename "$f")
                    if [ -f "$SELF_IMPROVING_DIR/$subdir/$fname" ]; then
                        # Both exist - create merged version
                        merge_entries "$f" "$SELF_IMPROVING_DIR/$subdir/$fname" "$MERGED_DIR/merged/$subdir/$fname"
                    else
                        # Only in import - copy
                        cp "$f" "$MERGED_DIR/merged/$subdir/$fname"
                    fi
                fi
            done
        fi
    done

    # Replace with merged
    rm -rf "$SELF_IMPROVING_DIR"
    mv "$MERGED_DIR/merged" "$SELF_IMPROVING_DIR"
    echo ""
    echo "Merge complete!"

elif [ "$MODE" = "replace" ]; then
    echo "Replacing memory..."
    rm -rf "$SELF_IMPROVING_DIR"
    mkdir -p "$SELF_IMPROVING_DIR"
    if ! cp -r "$IMPORT_DIR/self-improving/"* "$SELF_IMPROVING_DIR/"; then
        echo "❌ Error: Failed to import files"
        if [ -d "$BACKUP_DIR" ]; then
            echo "   Restoring from backup: $BACKUP_DIR"
            cp -r "$BACKUP_DIR/"* "$SELF_IMPROVING_DIR/"
        fi
        exit 1
    fi
    echo "Memory replaced successfully"
fi

echo ""
echo "Import complete!"
echo ""
echo "Next steps:"
echo "  1. Run 'bash scripts/stats.sh' to verify"
echo "  2. Review imported entries"
echo "  3. Delete backup when satisfied: rm -rf $BACKUP_DIR"
