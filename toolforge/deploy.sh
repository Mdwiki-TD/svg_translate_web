#!/usr/bin/env bash
set -euo pipefail
# This file should run from the main toolforge user. not from tool.

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

# Run deployment steps inside $TOOL_NAME's toolforge context
become $TOOL_NAME sh -c "
cp -rf \"$FULL_PATH/toolforge/deploy_scripts\" $TOOL_PATH -v;
cp -rf \"$FULL_PATH/toolforge/shs\" $TOOL_PATH -v;
cp -rf \"$FULL_PATH/toolforge/tool-deploy.sh\" $TOOL_PATH -v;
chmod +x $TOOL_PATH/tool-deploy.sh -v;
$TOOL_PATH/tool-deploy.sh \"$FULL_PATH\"
"

# Run toolforge-webservice commands
become $TOOL_NAME sh -c "
echo \">>> Checking webservice status...\";
toolforge-webservice python3.13 status;

echo \">>> Stopping webservice...\";
toolforge-webservice python3.13 stop;

echo \">>> Starting webservice...\";
toolforge-webservice python3.13 start;
"
echo ">>> '$TOOL_NAME' repository update completed successfully."
