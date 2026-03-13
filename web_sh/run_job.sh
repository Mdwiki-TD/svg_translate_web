#!/bin/bash

# use bash strict mode
set -euo pipefail

# Activate the virtual environment and install dependencies
source $HOME/www/python/venv/bin/activate

python3 www/python/src/offline/collect_main_files.py

# toolforge-jobs run
# toolforge-jobs run offline --image python3.13 --command "~/web_sh/run_job.sh" --wait
