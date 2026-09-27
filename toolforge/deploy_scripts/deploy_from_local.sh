#!/bin/bash
# sed -i 's/\r$//' ~/deploy_scripts/*.sh && chmod +x ~/deploy_scripts/*.sh

# use bash strict mode
set -euo pipefail

REPO_TMP_DIR="$1"     # Path to uploaded tmp folder, e.g., /home/username/arwiki_repo_tmp
TARGET_DIR="$2"       # Target tool folder, e.g., ARWIKI_ONE_REPO

if [ -z "${1:-}" ] || [ -z "${2:-}" ]; then
    echo "Usage: $0 <repo_tmp_dir> <target_dir>" >&2
    exit 1
fi

COPY_TO_TARGET="${COPY_TO_TARGET:-}"

SUB_DIR_COPY="${SUB_DIR_COPY:-}"
BASE_DIR="${BASE_DIR:-${HOME}}"

# Optional clean of TARGET_DIR
CLEAN_INSTALL="${CLEAN_INSTALL:-0}"

# Define the centralized archive directory in the home folder
OLD_REPOS_BASE="${HOME}/old_repos"

# Optional clean of jsons files before copy to avoid issues with old jsons files
REMOVE_SRC_JSONS_BEFORE_COPY="${REMOVE_SRC_JSONS_BEFORE_COPY:-0}"

# Ensure the Python3 binary exists before compiling
PYTHON_BIN="${PYTHON_BIN:-$HOME/local/bin/python3}"

COMPILE_PYTHON_FILES="${COMPILE_PYTHON_FILES:-0}"

echo ">>> Deploying from local uploaded temporary directory..."

# 1. Clean install / Archive if requested
if [ "$CLEAN_INSTALL" = "1" ] && [ -d "$TARGET_DIR" ]; then
    echo ">>> Clean install enabled"

    # Ensure the directory is writable before moving/deleting
    chmod -R u+w "$TARGET_DIR" 2>/dev/null || true

    # Ensure the archive directory exists
    mkdir -p "$OLD_REPOS_BASE"

    # Extract the directory name (e.g., cats_maker) to use in the archive name
    DIR_NAME=$(basename "$TARGET_DIR")

    # Set the destination path with a timestamp (e.g., ~/old_repos/src_backup_1715000)
    DESTINATION="${OLD_REPOS_BASE}/${DIR_NAME}_backup_$(date +%s%N)_$$"

    echo ">>> Archiving old version to: $DESTINATION"
    mv "$TARGET_DIR" "$DESTINATION"
fi

mkdir -p "$TARGET_DIR"

# 2. Determine Source Directory (Handle sub-folder like 'src')
SRC_DIR="$REPO_TMP_DIR"

if [ -n "$SUB_DIR_COPY" ]; then
    SRC_DIR="$REPO_TMP_DIR/$SUB_DIR_COPY"
    echo ">>> Copying sub-directory: $SRC_DIR"

    if [ ! -d "$SRC_DIR" ]; then
        echo ">>> ERROR: $SRC_DIR does not exist in local directory"
        echo ">>> exit."
        exit 1
    fi
fi

# 3. Clean JSONs if requested
if [ "$REMOVE_SRC_JSONS_BEFORE_COPY" = "1" ]; then
    echo ">>> Removing old JSON files from $SRC_DIR"
    find "$SRC_DIR" -name "*.json" -delete
fi

# 4. Copy from local temporary folder
echo ">>> Copying files from $SRC_DIR to $TARGET_DIR"
cp -rf "$SRC_DIR/"* "$TARGET_DIR/" -v

if [ -n "$COPY_TO_TARGET" ]; then
    echo ">>> Copying additional file: $COPY_TO_TARGET"
    cp -f "$REPO_TMP_DIR/$COPY_TO_TARGET" "$TARGET_DIR/" -v
fi

# 5. Compile Python Files if requested
if [ "$COMPILE_PYTHON_FILES" = "1" ]; then
    echo ">>> Compiling Python files to .pyc"

    # Compile all Python files to .pyc explicitly to avoid race conditions
    # Ensure the Python3 binary exists before compiling
    if command -v "$PYTHON_BIN" >/dev/null 2>&1; then
        export PYTHONDONTWRITEBYTECODE=1

        # Compile all Python files in the TARGET_DIR
        "$PYTHON_BIN" -m compileall -q -f "$TARGET_DIR"
        unset PYTHONDONTWRITEBYTECODE
    else
        echo ">>> Warning: Python binary not found at $PYTHON_BIN, skipping bytecode compilation"
    fi

    # Optional: Set permissions
    # chmod -R 770 "$TARGET_DIR"

    find "$TARGET_DIR" -type f ! -name "*.pyc" -exec chmod 770 {} \;
fi

echo ">>> Deployed successfully."
