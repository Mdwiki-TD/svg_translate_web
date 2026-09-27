#!/usr/bin/env bash
set -euo pipefail

# called via: become "$TOOL_NAME" bash -lc "deploy.sh <FULL_PATH>"
FULL_PATH="$1"
TOOL_NAME="copy-svg-langs"

# Define tool home path
TOOL_PATH="/data/project/$TOOL_NAME"

# echo ">>> Fixing Windows line endings (CRLF to LF)..."
# find "$FULL_PATH" -type f -name "*.sh" -exec sed -i 's/\r$//' {} +

echo ">>> Updating '$TOOL_NAME' tool core repository..."
cp -r "$FULL_PATH"/toolforge/shs/* "$TOOL_PATH"/shs -v
cp -r "$FULL_PATH"/toolforge/deploy_scripts/* "$TOOL_PATH"/deploy_scripts -v

chmod +x "$TOOL_PATH"/shs/*.sh "$TOOL_PATH"/deploy_scripts/*.sh

toolforge-jobs run update-repo --image python3.13 --command "$TOOL_PATH"/shs/update.sh --wait

toolforge-jobs run pipup --image python3.13 --command "$TOOL_PATH"/shs/pip.sh --wait

toolforge-webservice python3.13 status
toolforge-webservice python3.13 stop
toolforge-webservice python3.13 start
