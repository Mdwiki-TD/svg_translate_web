#!/bin/bash

# Periodic job-queue recovery.
#
# Releases active slots left behind by disappeared executions and dispatches
# the oldest pending job of every job type. Safe to run repeatedly: claiming a
# job is an atomic database update guarded by the unique idx_unique_active_job
# constraint, so concurrent runs never start the same job twice.
#
# Manual run:
# toolforge-jobs run queue-dispatcher --image python3.13 --command "~/shs/dispatch_jobs.sh" --wait

set -euo pipefail

# Activate the virtual environment
source "$HOME/www/python/venv/bin/activate"

flask --app "$HOME/www/python/src/app.py" dispatch-jobs
