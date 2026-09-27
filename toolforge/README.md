# test

```bash
rm -rf svg_tr_repo_tmp

git clone https://github.com/Mdwiki-TD/svg_translate_web.git svg_tr_repo_tmp -b z

# Execute updater script
chmod +x "/home/ibrahemqasim/svg_tr_repo_tmp/toolforge/deploy.sh"

bash "/home/ibrahemqasim/svg_tr_repo_tmp/toolforge/deploy.sh" "/home/ibrahemqasim/svg_tr_repo_tmp"

```

# steps

1.  Github action [`deploy.yaml`](../.github/workflows/deploy.yaml) execute [`deploy.sh`](deploy.sh) script
2.  `deploy.sh` will:
    -   Execute [`tool-deploy.sh`](tool-deploy.sh):
        -   `tool-deploy.sh` will execute [`update_local.sh`](update_local.sh)
    -   Execute `toolforge-webservice` commands (status/stop/start)
