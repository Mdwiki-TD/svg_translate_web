#!/bin/bash
# Wrapper script for running Flask CLI commands inside Toolforge job pods.
#
# Usage:
#   bash ~/scripts/flask_cmd.sh run-job-id 123
#   bash ~/scripts/flask_cmd.sh reconcile-jobs
#
# IMPORTANT: `exec` is used so that Python receives SIGTERM directly
# when Toolforge sends it (via delete_job), enabling graceful cancellation.
set -euo pipefail

export MDWIKI_CLI=1

source "$HOME/www/python/venv/bin/activate"
exec flask --app "$HOME/www/python/src/app.py" "$@"
