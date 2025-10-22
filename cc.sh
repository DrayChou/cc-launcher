#!/bin/bash
# Claude Code Multi-Platform Launcher - Demo Shell Script
# This is a demonstration script showing how to integrate cc-launcher
# Copy this to your preferred location and modify the PROJECT_PATH below

# ========= CONFIGURATION =========
# Default user config directory (as recommended in README)
DEFAULT_PROJECT_PATH="$HOME/.claude/scripts/cc-launcher"

# Function to find launcher.py in user config directory
find_launcher_in_user_config() {
    local user_config_path="$1"
    local launcher="$user_config_path/launcher.py"
    if [ -f "$launcher" ]; then
        echo "$launcher"
    fi
}

# Try to find launcher.py in order of preference:
LAUNCHER=""

# 1. Check if script is in the same directory as launcher.py (for development/testing)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_LAUNCHER="$SCRIPT_DIR/launcher.py"
if [ -f "$SCRIPT_LAUNCHER" ]; then
    LAUNCHER="$SCRIPT_LAUNCHER"
    # Only show development message when not in standard location
    if [ "$SCRIPT_LAUNCHER" != "$DEFAULT_PROJECT_PATH/launcher.py" ]; then
        print_color "cyan" "Found launcher in script directory: $SCRIPT_LAUNCHER"
    fi
fi

# 2. Check user config directory (recommended location)
if [ -z "$LAUNCHER" ]; then
    USER_CONFIG_LAUNCHER=$(find_launcher_in_user_config "$DEFAULT_PROJECT_PATH")
    if [ -n "$USER_CONFIG_LAUNCHER" ]; then
        LAUNCHER="$USER_CONFIG_LAUNCHER"
        print_color "cyan" "Found launcher in user config directory: $USER_CONFIG_LAUNCHER"
    fi
fi

# 3. Check environment variable override
if [ -z "$LAUNCHER" ] && [ -n "$CC_LAUNCHER_PROJECT_PATH" ]; then
    ENV_LAUNCHER=$(find_launcher_in_user_config "$CC_LAUNCHER_PROJECT_PATH")
    if [ -n "$ENV_LAUNCHER" ]; then
        LAUNCHER="$ENV_LAUNCHER"
        print_color "cyan" "Found launcher via environment variable: $ENV_LAUNCHER"
    fi
fi

# 4. If still not found, show error and usage instructions
if [ -z "$LAUNCHER" ]; then
    print_color "red" "❌ launcher.py not found!"
    print_color "yellow" "Please ensure cc-launcher is properly installed:"
    print_color "yellow" "  1. Recommended: Copy to $DEFAULT_PROJECT_PATH"
    print_color "yellow" "  2. Or set CC_LAUNCHER_PROJECT_PATH environment variable"
    print_color "yellow" "  3. Or place cc.sh in the same directory as launcher.py"
    exit 1
fi
# ===============================

# Color output functions
print_color() {
    local color=$1
    local message=$2

    case $color in
        "red") echo -e "\033[31m$message\033[0m" ;;
        "green") echo -e "\033[32m$message\033[0m" ;;
        "yellow") echo -e "\033[33m$message\033[0m" ;;
        "cyan") echo -e "\033[36m$message\033[0m" ;;
        "magenta") echo -e "\033[35m$message\033[0m" ;;
        "gray") echo -e "\033[90m$message\033[0m" ;;
        *) echo "$message" ;;
    esac
}

# Check Python availability
find_python() {
    local python_commands=("python3" "python" "python3.11" "python3.10" "python3.9")

    for cmd in "${python_commands[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            local version=$($cmd --version 2>&1)
            if [[ $version == Python* ]]; then
                local major_version=$(echo $version | cut -d' ' -f2 | cut -d'.' -f1)
                if [[ $major_version -ge 3 ]]; then
                    print_color "green" "✓ Using Python: $cmd ($version)"
                    echo "$cmd"
                    return 0
                fi
            fi
        fi
    done

    return 1
}

PYTHON_CMD=$(find_python)

if [ -z "$PYTHON_CMD" ]; then
    print_color "red" "❌ Python 3+ not found. Please install Python 3.7 or higher."
    print_color "yellow" "   • Ubuntu/Debian: sudo apt install python3 python3-pip"
    print_color "yellow" "   • CentOS/RHEL: sudo yum install python3 python3-pip"
    print_color "yellow" "   • macOS: brew install python3"
    print_color "yellow" "   • Download from: https://www.python.org/downloads/"
    exit 1
fi

# Check if launcher exists
if [ ! -f "$LAUNCHER" ]; then
    print_color "red" "❌ Launcher not found: $LAUNCHER"
    print_color "yellow" "   Please ensure cc-launcher is installed at: $PROJECT_PATH"
    print_color "yellow" "   Or set CC_LAUNCHER_PROJECT_PATH environment variable"
    exit 1
fi

# Check launcher is executable
if [ ! -x "$LAUNCHER" ]; then
    print_color "cyan" "Making launcher executable..."
    chmod +x "$LAUNCHER"
fi

# Execute launcher
print_color "magenta" "🚀 Launching cc-launcher..."
if [ $# -gt 0 ]; then
    $PYTHON_CMD "$LAUNCHER" "$@"
    exit_code=$?
else
    $PYTHON_CMD "$LAUNCHER"
    exit_code=$?
fi

# Handle exit codes
case $exit_code in
    0) print_color "green" "✅ Launcher completed successfully" ;;
    1) print_color "red" "❌ Launcher failed with error code 1" ;;
    130) print_color "yellow" "⚠️  Launcher interrupted by user (Ctrl+C)" ;;
    *) print_color "cyan" "ℹ️  Launcher exited with code: $exit_code" ;;
esac

exit $exit_code