#!/bin/bash
# toolforge-jobs run installar --image python3.11 --command "~/shs/update_ArWikiCats.sh" --wait
# sed -i 's/\r$//' ~/deploy_scripts/*.sh && chmod +x ~/deploy_scripts/*.sh

# use bash strict mode
set -euo pipefail

REPO_NAME="${1:-}"    # e.g. cats_maker
TARGET_DIR="${2:-}"   # Target tool folder, e.g., ARWIKI_ONE_REPO

if [ -z "$REPO_NAME" ] || [ -z "$TARGET_DIR" ]; then
    echo "Usage: $0 <repo_name> <target_dir> [branch]" >&2
    exit 1
fi

COPY_TO_TARGET="${COPY_TO_TARGET:-}"
SUB_DIR_COPY="${SUB_DIR_COPY:-}"

BRANCH="${3:-main}"
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

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

cleanup_old_backups() {
    local prefix="$1"
    local keep="${2:-5}"
    local -a old_backups

    mapfile -t old_backups < <(ls -1dt "${prefix}"* 2>/dev/null | tail -n +"$((keep + 1))" || true)

    echo ">>> Old backups to delete: ${#old_backups[@]}"

    if [ "${#old_backups[@]}" -gt 0 ]; then
        rm -rf -- "${old_backups[@]}"
    fi
}

clone_repo() {
    local repo_url="$1"
    local branch="$2"
    local clone_dir="$3"
    local repo_name="$4"

    echo ">>> Deploying ${repo_name} (branch: ${branch})"

    # Remove any existing clone directory
    rm -rf "$clone_dir"

    echo ">>> clone --branch ${branch}"
    echo "${repo_url}"

    git clone --branch "$branch" "$repo_url" "$clone_dir"

    rm -rf "$clone_dir/.git"
}

# Move the existing target dir into the archive, then prune old backups
archive_old_version() {
    local target_dir="$1"
    local repo_name="$2"
    local old_repos_base="$3"
    local keep="${4:-5}"

    echo ">>> Clean install enabled"

    # Ensure the directory is writable before moving/deleting
    chmod -R u+w "$target_dir" 2>/dev/null || true

    # Ensure the archive directory exists
    mkdir -p "$old_repos_base"

    local dir_name backup_path destination

    # Extract the directory name (e.g., cats_maker) to use in the archive name
    dir_name=$(basename "$target_dir")

    backup_path="${repo_name}_${dir_name}_backup"

    # Set the destination path with a timestamp (e.g., ~/old_repos/src_backup_1715000)
    destination="${old_repos_base}/${backup_path}_$(date +%s%N)_$$"

    echo ">>> Archiving old version to: $destination"
    mv "$target_dir" "$destination"

    cleanup_old_backups "${old_repos_base}/${backup_path}_" "$keep"
}

# Prints the source dir to stdout (logs go to stderr so they are not captured)
resolve_src_dir() {
    local base_dir="$1"
    local sub_dir="${2:-}"
    local src_dir="$base_dir"

    if [ -n "$sub_dir" ]; then
        src_dir="$base_dir/$sub_dir"
        echo ">>> Copying sub-directory: $src_dir" >&2

        if [ ! -d "$src_dir" ]; then
            echo ">>> ERROR: $src_dir does not exist in repo" >&2
            echo ">>> exit." >&2
            return 1
        fi
    fi

    echo "$src_dir"
}

remove_json_files() {
    local src_dir="$1"
    echo ">>> Removing old JSON files from $src_dir"
    find "$src_dir" -name "*.json" -delete
}

copy_files() {
    local src_dir="$1"
    local target_dir="$2"
    local clone_dir="$3"
    local extra_file="${4:-}"

    echo ">>> Copying files from $src_dir to $target_dir"
    cp -rf "$src_dir/"* "$target_dir/" -v

    if [ -n "$extra_file" ]; then
        echo ">>> Copying additional file: $extra_file"
        cp -f "$clone_dir/$extra_file" "$target_dir/" -v
    fi
}

compile_python_files() {
    local target_dir="$1"
    local python_bin="$2"

    echo ">>> Compiling Python files to .pyc"

    # Compile all Python files to .pyc explicitly to avoid race conditions
    # Ensure the Python3 binary exists before compiling
    if command -v "$python_bin" >/dev/null 2>&1; then
        export PYTHONDONTWRITEBYTECODE=1

        # Compile all Python files in the target_dir
        "$python_bin" -m compileall -q -f "$target_dir"
        unset PYTHONDONTWRITEBYTECODE
    else
        echo ">>> Warning: Python binary not found at $python_bin, skipping bytecode compilation"
    fi

    # Optional: Set permissions
    # chmod -R 770 "$TARGET_DIR"

    find "$target_dir" -type f ! -name "*.pyc" -exec chmod 770 {} \;
}

# Optional: Install dependencies
install_requirements() {
    local python_bin="$1"
    local target_dir="$2"
    "$python_bin" -m pip install -r "$target_dir/requirements.in"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

main() {
    local src_dir

    # Navigate to the project directory
    cd "$BASE_DIR" || exit 1

    # Clone
    clone_repo "$REPO_URL" "$BRANCH" "$CLONE_DIR" "$REPO_NAME"

    # 1. Clean install / archive if requested
    if [ "$CLEAN_INSTALL" = "1" ] && [ -d "$TARGET_DIR" ]; then
        archive_old_version "$TARGET_DIR" "$REPO_NAME" "$OLD_REPOS_BASE" 5
    fi

    mkdir -p "$TARGET_DIR"

    # 2. Determine Source Directory (Handle sub-folder like 'src')
    src_dir=$(resolve_src_dir "$CLONE_DIR" "$SUB_DIR_COPY")

    # 3. Clean JSONs if requested
    if [ "$REMOVE_SRC_JSONS_BEFORE_COPY" = "1" ]; then
        remove_json_files "$src_dir"
    fi

    # 4. Copy files
    copy_files "$src_dir" "$TARGET_DIR" "$CLONE_DIR" "$COPY_TO_TARGET"

    # 5. Compile Python files if requested
    if [ "$COMPILE_PYTHON_FILES" = "1" ]; then
        compile_python_files "$TARGET_DIR" "$PYTHON_BIN"
    fi

    # Cleanup
    rm -rf "$CLONE_DIR"

    echo ">>> ${REPO_NAME} Deployed successfully"
}

main
