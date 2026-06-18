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
EXPORT_LINE="export PATH=\"$VENV_BIN:\$PATH\"  # experiment-notifier"

echo ""
echo "==> Adding notify-exp to PATH..."
added=0
for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$rc" ]; then
        if grep -qF "$VENV_BIN" "$rc"; then
            echo "    $rc — already set, skipping"
        else
            printf '\n%s\n' "$EXPORT_LINE" >> "$rc"
            echo "    $rc — updated"
            added=1
        fi
    fi
done

if [ "$added" -eq 0 ]; then
    # No rc file existed — create ~/.bashrc as a fallback
    if ! [ -f "$HOME/.bashrc" ] && ! [ -f "$HOME/.zshrc" ]; then
        printf '%s\n' "$EXPORT_LINE" > "$HOME/.bashrc"
        echo "    ~/.bashrc — created"
        added=1
    fi
fi

if [ "$added" -eq 1 ]; then
    echo ""
    echo "    Reload your shell to activate:"
    echo "    source ~/.bashrc   # or ~/.zshrc"
fi

echo ""
echo "==> Configure credentials (one time per machine):"
echo "    cp $REPO_DIR/.env.example ~/.notifier.env"
echo "    \$EDITOR ~/.notifier.env"
echo ""
echo "==> Verify it works (after reloading shell):"
echo "    notify-exp test"
