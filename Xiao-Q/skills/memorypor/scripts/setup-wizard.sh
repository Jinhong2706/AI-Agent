#!/bin/bash
#==============================================================================
# Self-Improving Skill — Interactive Setup Wizard
# Version: 2.1.0
# Usage: bash setup-wizard.sh
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

SELF_IMPROVING_DIR="${SELF_IMPROVING_DIR:-$HOME/self-improving}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd -P 2>/dev/null || cd "$(dirname "$0")/.." && pwd)"

# Colors (if terminal supports)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

#-------------------------------------------------------------------------------
# Helper functions
#-------------------------------------------------------------------------------
ask() {
    local prompt="$1"
    local default="$2"
    local result=""

    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " result
        result="${result:-$default}"
    else
        read -p "$prompt: " result
    fi

    echo "$result"
}

ask_yn() {
    local prompt="$1"
    local default="${2:-n}"
    local result=""

    while true; do
        read -p "$prompt [y/N]: " result
        result="${result:-$default}"
        case "$result" in
            [Yy]|[Yy][Ee][Ss]) return 0 ;;
            [Nn]|[Nn][Oo]) return 1 ;;
            *) echo "Please answer yes or no." ;;
        esac
    done
}

select_option() {
    local prompt="$1"
    shift
    local options=("$@")
    local selected=0

    echo ""
    echo "$prompt"
    echo ""
    for i in "${!options[@]}"; do
        echo "  $((i+1))) ${options[$i]}"
    done
    echo ""

    while true; do
        read -p "Select option (1-${#options[@]}): " selection
        if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#options[@]}" ]; then
            selected=$((selection-1))
            break
        fi
        echo "Invalid selection. Please enter a number."
    done

    echo "${options[$selected]}"
}

echo_banner() {
    echo ""
    echo -e "${BLUE}==============================================${NC}"
    echo -e "${BLUE}     Self-Improving Skill — Setup Wizard     ${NC}"
    echo -e "${BLUE}==============================================${NC}"
    echo ""
}

#-------------------------------------------------------------------------------
# Main wizard
#-------------------------------------------------------------------------------
main() {
    echo_banner

    echo "This wizard will guide you through setting up the Self-Improving skill."
    echo ""

    # Step 1: Welcome and check
    if [ -d "$SELF_IMPROVING_DIR" ]; then
        echo -e "${YELLOW}Warning: Self-improving directory already exists.${NC}"
        if ask_yn "Do you want to reinitialize it?" "n"; then
            BACKUP_DIR="$HOME/self-improving-backup-$(date +%Y%m%d-%H%M%S)"
            echo "Backing up to: $BACKUP_DIR"
            cp -r "$SELF_IMPROVING_DIR" "$BACKUP_DIR"
        else
            echo "Setup cancelled."
            exit 0
        fi
    fi

    # Step 2: Select tier
    echo -e "${GREEN}Step 1: Select Usage Tier${NC}"
    echo ""
    echo "How intensely will you use this skill?"
    echo ""

    local tier=$(select_option "Choose a tier:" \
        "Low (<5h/day) - Conservative limits" \
        "Normal (5-10h/day) - Default limits" \
        "High (10-15h/day) - Extended limits" \
        "Heavy (>15h/day) - Maximum limits")

    case "$tier" in
        *Low*) SELECTED_TIER="low" ;;
        *Normal*) SELECTED_TIER="normal" ;;
        *High*) SELECTED_TIER="high" ;;
        *Heavy*) SELECTED_TIER="heavy" ;;
    esac

    echo ""
    echo "Selected tier: $SELECTED_TIER"

    # Step 3: Choose components
    echo ""
    echo -e "${GREEN}Step 2: Choose Components to Install${NC}"
    echo ""

    local install_memory=true
    local install_heartbeat=true
    local install_examples=false

    if ask_yn "Install memory structure (HOT/WARM/COLD)?" "Y"; then
        install_memory=true
    else
        install_memory=false
    fi

    if ask_yn "Install heartbeat maintenance?" "Y"; then
        install_heartbeat=true
    else
        install_heartbeat=false
    fi

    if ask_yn "Install example entries?" "N"; then
        install_examples=true
    else
        install_examples=false
    fi

    # Step 4: Integration options
    echo ""
    echo -e "${GREEN}Step 3: Integration Options${NC}"
    echo ""

    local integrate_claude=false
    local integrate_agents=false
    local integrate_heartbeat=false

    if [ -f "./CLAUDE.md" ]; then
        if ask_yn "Add self-improving steering to CLAUDE.md?" "Y"; then
            integrate_claude=true
        fi
    fi

    if [ -f "./AGENTS.md" ]; then
        if ask_yn "Add memory section to AGENTS.md?" "Y"; then
            integrate_agents=true
        fi
    fi

    if [ -f "./HEARTBEAT.md" ]; then
        if ask_yn "Add heartbeat snippet to HEARTBEAT.md?" "Y"; then
            integrate_heartbeat=true
        fi
    fi

    # Step 5: Confirm
    echo ""
    echo -e "${GREEN}Step 4: Review and Confirm${NC}"
    echo ""
    echo "Configuration summary:"
    echo "  Tier: $SELECTED_TIER"
    echo "  Install memory: $install_memory"
    echo "  Install heartbeat: $install_heartbeat"
    echo "  Install examples: $install_examples"
    echo "  Integrate CLAUDE.md: $integrate_claude"
    echo "  Integrate AGENTS.md: $integrate_agents"
    echo "  Integrate HEARTBEAT.md: $integrate_heartbeat"
    echo ""

    if ! ask_yn "Proceed with installation?" "Y"; then
        echo "Setup cancelled."
        exit 0
    fi

    # Step 6: Install
    echo ""
    echo -e "${GREEN}Step 5: Installing...${NC}"
    echo ""

    # Run main setup script with selected tier
    echo "Running setup with tier: $SELECTED_TIER"
    if bash "$SKILL_DIR/scripts/setup.sh" --tier "$SELECTED_TIER"; then
        echo ""
        echo -e "${GREEN}✓ Base installation complete${NC}"
    else
        echo ""
        echo -e "${RED}✗ Base installation failed${NC}"
        exit 1
    fi

    # Integration steps
    if [ "$integrate_claude" = true ]; then
        echo ""
        echo "Adding steering to CLAUDE.md..."
        # This would modify CLAUDE.md - simplified for safety
        echo "  (Manual step required - see setup.md section 4)"
    fi

    if [ "$integrate_agents" = true ]; then
        echo ""
        echo "Adding memory section to AGENTS.md..."
        echo "  (Manual step required - see setup.md section 5)"
    fi

    if [ "$integrate_heartbeat" = true ]; then
        echo ""
        echo "Adding heartbeat snippet..."
        echo "  (Manual step required - see setup.md section 6)"
    fi

    # Final summary
    echo ""
    echo -e "${BLUE}==============================================${NC}"
    echo -e "${GREEN}Setup Complete!${NC}"
    echo -e "${BLUE}==============================================${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run 'bash scripts/stats.sh' to verify installation"
    echo "  2. Add integration snippets to CLAUDE.md/AGENTS.md/HEARTBEAT.md"
    echo "  3. Start using the skill!"
    echo ""
    echo "Documentation: $SKILL_DIR"
    echo ""
}

main "$@"
