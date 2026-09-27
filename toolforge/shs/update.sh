#!/bin/bash
# toolforge-jobs run update-repo --image python3.11 --command "~/shs/update.sh" --wait

export USER_NAME="Mdwiki-TD"
export SUB_DIR_COPY="src"
export CLEAN_INSTALL=1

# Optional clean of jsons files before copy to avoid issues with old jsons files
export REMOVE_SRC_JSONS_BEFORE_COPY=0

# Ensure the Python3 binary exists before compiling
export PYTHON_BIN="$HOME/www/python/venv/bin/python3"
export COMPILE_PYTHON_FILES=1

# additional file to copy to TARGET_DIR
export COPY_TO_TARGET="requirements.txt"

REPO_NAME="svg_translate_web"
TARGET_DIR="$HOME/www/python/src"
BRANCH="${1:-main}"

$HOME/shs/deploy_repo.sh "$REPO_NAME" "$TARGET_DIR" "$BRANCH"
