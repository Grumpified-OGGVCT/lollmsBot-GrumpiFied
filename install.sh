#!/usr/bin/env bash
set -euo pipefail

# lollmsBot automated installer
# Supports Linux/macOS/Windows (WSL/Git Bash/Cygwin)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== lollmsBot Installer ==="
echo "Target directory: $SCRIPT_DIR"

# === 1. Detect platform ===
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    PLATFORM="windows"
    PY_VERSION="3.11"  # Windows: prefer 3.11 for stability
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
    PY_VERSION="3.12"
else
    PLATFORM="linux"
    PY_VERSION="3.11"
fi

echo "Detected platform: $PLATFORM (Python >= $PY_VERSION)"

# === 2. Python detection ===
echo "Checking Python installation..."

if command -v python3 >/dev/null 2>&1; then
    PY3_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    echo "Found Python $PY3_VERSION"
    
    if [[ "$(python3 -c "import sys; print(sys.version_info >= ($PY_VERSION.split('.') | head -1 | head -1, $(echo $PY_VERSION | cut -d. -f2), 0))")" == "True" ]]; then
        PYTHON="python3"
    fi
fi

# Fallback: python/python.exe
if [[ -z "${PYTHON:-}" ]]; then
    if command -v python >/dev/null 2>&1; then
        PYTHON="python"
    elif [[ "$PLATFORM" == "windows" ]] && command -v python.exe >/dev/null 2>&1; then
        PYTHON="python.exe"
    fi
fi

if [[ -n "${PYTHON:-}" ]]; then
    PY_INSTALLED_VERSION=$($PYTHON -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    echo "Using $PYTHON $PY_INSTALLED_VERSION"
else
    echo "Python $PY_VERSION not found. Installing..."
    
    case $PLATFORM in
        linux)
            # Ubuntu/Debian
            if [[ -f /etc/os-release ]] && grep -qi ubuntu /etc/os-release; then
                sudo apt update
                sudo apt install -y python3.11 python3.11-venv python3-pip
                PYTHON="python3.11"
            # RHEL/CentOS/Fedora
            elif [[ -f /etc/os-release ]] && grep -qi fedora /etc/os-release; then
                sudo dnf install -y python3.11 python3.11-pip
                PYTHON="python3.11"
            # Arch
            elif [[ -f /etc/os-release ]] && grep -qi arch /etc/os-release; then
                sudo pacman -S --noconfirm python
            # Raspberry Pi OS (Debian-based)
            elif grep -qi "raspbian\|raspberry" /etc/os-release 2>/dev/null; then
                sudo apt update
                sudo apt install -y python3.11 python3.11-venv python3-pip
                PYTHON="python3.11"
            else
                echo "Unsupported Linux distro. Please install Python $PY_VERSION manually."
                exit 1
            fi
            ;;
        macos)
            # Use Homebrew
            if ! command -v brew >/dev/null 2>&1; then
                echo "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install python@3.12
            PYTHON="python3.12"
            ;;
        windows)
            echo "Windows: Please install Python $PY_VERSION from https://python.org or Microsoft Store first."
            echo "Then rerun install.sh"
            exit 1
            ;;
    esac
fi

# === 3. Venv setup ===
VENV_DIR=".venv"
echo "Creating virtual environment at $VENV_DIR..."

if [[ -d "$VENV_DIR" ]]; then
    echo "Removing existing venv..."
    rm -rf "$VENV_DIR"
fi

"$PYTHON" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"  # Linux/macOS

if [[ "$PLATFORM" == "windows" ]]; then
    . "$VENV_DIR/Scripts/activate"
fi

# Upgrade pip first
pip install --upgrade pip setuptools wheel

# === 4. Install lollmsBot ===
echo "Installing lollmsBot..."
pip install -e .

# === 5. Test installation ===
echo "Testing installation..."
lollmsbot --help >/dev/null 2>&1 && echo "✓ CLI works" || echo "✗ CLI failed"

echo ""
echo "=== Installation complete! ==="
echo "To run:"
echo "  source .venv/bin/activate"
echo "  lollmsbot gateway"
echo ""
echo "Create .env with your LoLLMS settings to start:"
echo "LOLLMS_HOST_ADDRESS=http://localhost:9600"
echo "LOLLMSBOT_PORT=8800"
