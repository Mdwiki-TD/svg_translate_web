#!/bin/bash
# This file can not be executed directly, it is called from the toolforge/tool-deploy.sh script

# Target local temporary path passed from the deploy steps
REPO_TMP_DIR=$1

if [ -z "$REPO_TMP_DIR" ]; then
    echo "Error: Missing temporary repository path argument."
    exit 1
fi

export SUB_DIR_COPY="src"
export CLEAN_INSTALL=1

# Optional clean of jsons files before copy to avoid issues with old jsons files
export REMOVE_SRC_JSONS_BEFORE_COPY=0

# Ensure the Python3 binary exists before compiling
export PYTHON_BIN="$HOME/www/python/venv/bin/python3"
export COMPILE_PYTHON_FILES=1

# additional file to copy to TARGET_DIR
export COPY_TO_TARGET="requirements.txt"

TARGET_DIR="$HOME/www/python/src"

# Execute the local deployment script directly without cloning from GitHub
# We copy the script to ~/deploy_scripts/ first from the github action workflow, then call it
$HOME/deploy_scripts/deploy_from_local.sh "$REPO_TMP_DIR" "$TARGET_DIR"
