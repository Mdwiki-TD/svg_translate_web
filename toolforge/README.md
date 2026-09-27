# test

```bash
rm -rf svg_tr_repo_tmp

git clone https://github.com/Mdwiki-TD/svg_translate_web.git svg_tr_repo_tmp -b z

# Execute updater script
chmod +x "/home/ibrahemqasim/svg_tr_repo_tmp/toolforge/deploy.sh"

# Step 1: Execute the deploy script with the correct path
bash "/home/ibrahemqasim/svg_tr_repo_tmp/toolforge/deploy.sh" "/home/ibrahemqasim/svg_tr_repo_tmp"

# Step 2: `deploy.sh` will Execute `tool-deploy.sh`
# Step 3: `tool-deploy.sh` will Execute `update_local.sh`
# Step 4: `deploy.sh` will Run toolforge-webservice commands (status/stop/start)

```
