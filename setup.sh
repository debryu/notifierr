#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Install uv if not present
if ! command -v uv &>/dev/null; then
    echo "==> uv not found — installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "==> Installing experiment-notifier..."
cd "$REPO_DIR"
uv sync

VENV_BIN="$REPO_DIR/.venv/bin"

echo ""
echo "==> Done! Add the following to your ~/.bashrc or ~/.zshrc:"
echo ""
echo "    export PATH=\"$VENV_BIN:\$PATH\""
echo ""
echo "Then reload your shell:"
echo "    source ~/.bashrc   # or ~/.zshrc"
echo ""
echo "==> Configure credentials (one time per machine):"
echo "    cp $REPO_DIR/.env.example ~/.notifier.env"
echo "    \$EDITOR ~/.notifier.env"
echo ""
echo "==> Verify it works:"
echo "    notify-exp test"
