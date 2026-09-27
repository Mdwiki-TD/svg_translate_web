# test

```bash
rm -rf svg_tr_repo_tmp

git clone https://github.com/Mdwiki-TD/svg_translate_web.git svg_tr_repo_tmp -b z

# Execute updater script
chmod +x "/home/ibrahemqasim/svg_tr_repo_tmp/toolforge/deploy.sh"

bash "/home/ibrahemqasim/svg_tr_repo_tmp/toolforge/deploy.sh" "/home/ibrahemqasim/svg_tr_repo_tmp"

```

# Deployment Steps

1. On every push to `main`, the GitHub Action [`deploy.yaml`](../.github/workflows/deploy.yaml) runs [`deploy.sh`](deploy.sh) on the server.
2. `deploy.sh` performs the following, in order:
    - Runs [`tool-deploy.sh`](tool-deploy.sh), which in turn runs [`shs/update_local.sh`](shs/update_local.sh) to update the tool's local copy (copying files, updating dependencies, etc.).
    - Once the update finishes, it runs `toolforge-webservice` (`status`, then `stop`, then `start`) to restart the service with the new version.
