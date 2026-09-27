#!/bin/bash
# toolforge-jobs run installar --image python3.11 --command "~/shs/update_ArWikiCats.sh" --wait
# sed -i 's/\r$//' ~/shs/*.sh && chmod +x ~/shs/*.sh

# use bash strict mode
set -euo pipefail

REPO_NAME="$1"        # e.g. cats_maker
TARGET_DIR="$2"       # e.g. bots/cats_maker

if [ -z "${1:-}" ] || [ -z "${2:-}" ]; then
    echo "Usage: $0 <repo_name> <target_dir> [branch]" >&2
    exit 1
fi

COPY_TO_TARGET="${COPY_TO_TARGET:-}"

BRANCH="${3:-main}"
SUB_DIR_COPY="${SUB_DIR_COPY:-}"
USER_NAME="${USER_NAME:-MrIbrahem}"
BASE_DIR="${BASE_DIR:-${HOME}}"

CLONE_DIR="${BASE_DIR}/${REPO_NAME}_tmp"

# Optional clean of TARGET_DIR
CLEAN_INSTALL="${CLEAN_INSTALL:-0}"

# Define the centralized archive directory in the home folder
OLD_REPOS_BASE="${HOME}/old_repos"

# Optional clean of jsons files before copy to avoid issues with old jsons files
REMOVE_SRC_JSONS_BEFORE_COPY="${REMOVE_SRC_JSONS_BEFORE_COPY:-0}"

# Ensure the Python3 binary exists before compiling
PYTHON_BIN="${PYTHON_BIN:-$HOME/local/bin/python3}"

COMPILE_PYTHON_FILES="${COMPILE_PYTHON_FILES:-0}"

REPO_URL="https://github.com/${USER_NAME}/${REPO_NAME}.git"

# Navigate to the project directory
cd "$BASE_DIR" || exit

echo ">>> Deploying ${REPO_NAME} (branch: ${BRANCH})"

# Remove any existing clone directory
rm -rf "$CLONE_DIR"

echo ">>> clone --branch ${BRANCH}"
echo "${REPO_URL}"

git clone --branch "$BRANCH" "$REPO_URL" "$CLONE_DIR"

rm -rf "$CLONE_DIR/.git"

if [ "$CLEAN_INSTALL" = "1" ] && [ -d "$TARGET_DIR" ]; then
    echo ">>> Clean install enabled"

    # Ensure the directory is writable before moving/deleting
    chmod -R u+w "$TARGET_DIR" 2>/dev/null || true

    # Ensure the archive directory exists
    mkdir -p "$OLD_REPOS_BASE"

    # Extract the directory name (e.g., cats_maker) to use in the archive name
    DIR_NAME=$(basename "$TARGET_DIR")

    # Set the destination path with a timestamp (e.g., ~/old_repos/src_backup_1715000)
    DESTINATION="${OLD_REPOS_BASE}/${REPO_NAME}_${DIR_NAME}_backup_$(date +%s%N)_$$"

    echo ">>> Archiving old version to: $DESTINATION"
    mv "$TARGET_DIR" "$DESTINATION"
fi

mkdir -p "$TARGET_DIR"

# Copy
SRC_DIR="$CLONE_DIR"

if [ -n "$SUB_DIR_COPY" ]; then
    SRC_DIR="$CLONE_DIR/$SUB_DIR_COPY"
    echo ">>> Copying sub-directory: $SRC_DIR"

    if [ ! -d "$SRC_DIR" ]; then
        echo ">>> ERROR: $SRC_DIR does not exist in repo"
        echo ">>> exit."
        exit 1
    fi
fi

if [ "$REMOVE_SRC_JSONS_BEFORE_COPY" = "1" ]; then
    echo ">>> Removing old JSON files from $SRC_DIR"
    find "$SRC_DIR" -name "*.json" -delete
fi

cp -rf "$SRC_DIR/"* "$TARGET_DIR/" -v

if [ -n "$COPY_TO_TARGET" ]; then
    echo ">>> Copying additional file: $COPY_TO_TARGET"
    cp -f "$CLONE_DIR/$COPY_TO_TARGET" "$TARGET_DIR/" -v
fi

if [ "$COMPILE_PYTHON_FILES" = "1" ]; then
    echo ">>> Compiling Python files to .pyc"

    # Compile all Python files to .pyc explicitly to avoid race conditions
    # Ensure the Python3 binary exists before compiling
    if [ -x "$PYTHON_BIN" ]; then
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

# Optional: Install dependencies
#"$PYTHON_BIN" -m pip install -r "$TARGET_DIR/requirements.in"

# Remove the "$CLONE_DIR" directory.
rm -rf "$CLONE_DIR"

echo ">>> ${REPO_NAME} deployed successfully"
