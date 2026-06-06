#!/bin/bash

# use bash strict mode
set -euo pipefail

# Activate the virtual environment and install dependencies
source $HOME/www/python/venv/bin/activate

flask --app www/python/src/app.py run-collect-templates-data
# python3 www/python/src/offline/collect_templates_data.py

# toolforge-jobs run
# toolforge-jobs run offline --image python3.13 --command "~/web_sh/run_job.sh" --wait
