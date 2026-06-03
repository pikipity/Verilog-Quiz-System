#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="verilog-quiz-system"

mkdir -p ~/.local/share/applications
mkdir -p ~/.local/share/icons/hicolor/512x512/apps

cp "$SCRIPT_DIR/$APP_NAME.desktop" ~/.local/share/applications/
cp "$SCRIPT_DIR/$APP_NAME.png" ~/.local/share/icons/hicolor/512x512/apps/
chmod +x ~/.local/share/applications/$APP_NAME.desktop

sed -i "s|Exec=.*|Exec=$SCRIPT_DIR/$APP_NAME|" ~/.local/share/applications/$APP_NAME.desktop

update-desktop-database ~/.local/share/applications/ 2>/dev/null || true

echo "========================================"
echo "Verilog Quiz System installed!"
echo "You can now find it in your applications menu."
echo "========================================"
