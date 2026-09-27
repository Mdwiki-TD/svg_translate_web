#!/bin/bash

# use bash strict mode
set -euo pipefail

# Activate the virtual environment and install dependencies
source $HOME/www/python/venv/bin/activate

flask --app "$HOME/www/python/src/app.py" run-job collect_templates_data --update-all
# python3 www/python/src/offline/collect_templates_data.py

# toolforge-jobs run
# toolforge-jobs run offline --image python3.13 --command "~/shs/run_job.sh" --wait
