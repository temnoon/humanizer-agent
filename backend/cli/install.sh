#!/bin/bash
# Madhyamaka CLI Installation Script

echo "🧘 Installing Madhyamaka CLI..."

# Check Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Error: Python 3.11 is required"
    echo "   Install with: brew install python@3.11"
    exit 1
fi

echo "✅ Found Python 3.11: $(python3.11 --version)"

# Get install directory
INSTALL_DIR="${1:-$HOME/.local/bin}"

# Create install directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Copy CLI to install directory
cp "$SCRIPT_DIR/madhyamaka_cli.py" "$INSTALL_DIR/madhyamaka"
chmod +x "$INSTALL_DIR/madhyamaka"

echo "✅ Installed to: $INSTALL_DIR/madhyamaka"

# Check if install directory is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo "⚠️  Warning: $INSTALL_DIR is not in your PATH"
    echo ""
    echo "Add this line to your ~/.zshrc or ~/.bashrc:"
    echo "   export PATH=\"\$PATH:$INSTALL_DIR\""
    echo ""
    echo "Then reload your shell:"
    echo "   source ~/.zshrc  # or source ~/.bashrc"
else
    echo "✅ $INSTALL_DIR is in PATH"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Test with:"
echo "   madhyamaka health"
echo "   madhyamaka detect eternalism \"Everything must be perfect\""
echo ""
echo "Get help:"
echo "   madhyamaka --help"
echo "   madhyamaka detect --help"
echo "   madhyamaka transform --help"
echo "   madhyamaka contemplate --help"
echo "   madhyamaka teach --help"
