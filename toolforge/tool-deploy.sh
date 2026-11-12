#!/usr/bin/env bash
set -euo pipefail

# This file can not be executed directly, it is called from toolforge/deploy.sh script

# Full path to the uploaded repository passed from GitHub Actions
FULL_PATH="${1:-}"

if [ -z "$FULL_PATH" ]; then
    echo "Error: Missing full repository path argument." >&2
    exit 1
fi

TOOL_NAME="copy-svg-langs"

# Define tool home path
TOOL_PATH="/data/project/$TOOL_NAME"

echo ">>> Updating tool repository..."
echo ">>> FULL_PATH: $FULL_PATH"

# Run sed on all .sh files in the uploaded directory to fix compatibility issues
echo ">>> Fixing Windows line endings (CRLF to LF) for all shell scripts..."
find "$FULL_PATH" -type f -name "*.sh" -exec sed -i 's/\r$//' {} +

echo ">>> Updating '$TOOL_NAME' tool core repository..."

# Run deployment steps inside $TOOL_NAME's toolforge context
cp -rf "$FULL_PATH"/toolforge/deploy_scripts $TOOL_PATH -v
cp -rf "$FULL_PATH"/toolforge/shs $TOOL_PATH -v

echo ">>> Making scripts executable..."
chmod +x $TOOL_PATH/shs/*.sh $TOOL_PATH/deploy_scripts/*.sh

echo ">>> executing file: $TOOL_PATH/shs/update_local.sh"
$TOOL_PATH/shs/update_local.sh "$FULL_PATH"

echo ">>> executing file: $TOOL_PATH/shs/pip.sh"
$TOOL_PATH/shs/pip.sh
