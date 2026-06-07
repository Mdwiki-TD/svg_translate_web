---
name: flask-cli
description: >
    Expert guidance for Flask CLI usage, configuration, and custom command development.
    Use this skill whenever the user is working with Flask's command line interface —
    including running the dev server, setting up dotenv, writing custom Click commands,
    registering blueprint CLI commands, using FlaskGroup for custom scripts, or
    debugging CLI discovery issues. Trigger on any mention of `flask run`, `flask shell`,
    `--app`, `.flaskenv`, `@app.cli.command`, `AppGroup`, `FlaskGroup`, CLI plugins, or
    PyCharm Flask run configurations.
---

# Flask CLI Skill

## Application Discovery (`--app`)

Flask needs to know where your app lives. The `--app` flag accepts three parts:
`[path/]<import>[:instance_or_factory]`

| Usage                    | Example                           |
| ------------------------ | --------------------------------- |
| Auto-detect `app`/`wsgi` | _(omit `--app`)_                  |
| Named module             | `--app hello`                     |
| Sub-module               | `--app hello.web`                 |
| Specific instance        | `--app hello:app2`                |
| Factory with args        | `--app 'hello:create_app("dev")'` |
| Set working dir first    | `--app src/hello`                 |

**Auto-detection order:** looks for `app` or `application` instance → any Flask instance → `create_app()` or `make_app()` factory.

> ⚠️ Factory args in parentheses are parsed as Python literals — strings must be quoted inside.

---

## Running the Dev Server

```bash
flask --app hello run              # basic
flask --app hello run --debug      # with interactive debugger + reloader
flask --app hello --debug run      # equivalent (--debug at top level)
flask run --port 8000              # custom port
flask run --extra-files file1:dirA/file2   # watch extra files (: separator, ; on Windows)
flask run --exclude-patterns '*.log:tmp/*' # ignore patterns (fnmatch)
```

> ⚠️ **Never use `flask run` in production.** Use a WSGI server (gunicorn, uwsgi).

Port already in use? See `OSError: [Errno 98]` / `OSError: [WinError 10013]` → kill the process on that port or use `--port`.

---

## Environment Variables & dotenv

**Naming pattern:** `FLASK_<OPTION>` or `FLASK_<COMMAND>_<OPTION>`

```
FLASK_APP=hello
FLASK_RUN_PORT=8000
FLASK_RUN_HOST=0.0.0.0
```

### dotenv files (requires `pip install python-dotenv`)

| File        | Purpose                                       | Commit? |
| ----------- | --------------------------------------------- | ------- |
| `.flaskenv` | Public config (`FLASK_APP`, `FLASK_RUN_PORT`) | ✅ Yes  |
| `.env`      | Private secrets, credentials                  | ❌ No   |

Command-line > `.env` > `.flaskenv` (precedence).

Flask scans upward from the directory where `flask` is called to find these files.

To skip dotenv loading:

```bash
FLASK_SKIP_DOTENV=1 flask run
```

---

## Custom Commands

### Simple command

```python
import click
from flask import Flask

app = Flask(__name__)

@app.cli.command("create-user")
@click.argument("name")
def create_user(name):
    # app context is automatically available here
    ...
```

```bash
flask create-user admin
```

### Command groups (`AppGroup`)

```python
from flask.cli import AppGroup

user_cli = AppGroup('user')

@user_cli.command('create')
@click.argument('name')
def create_user(name):
    ...

app.cli.add_command(user_cli)
```

```bash
flask user create demo
```

### Application context

Commands registered via `app.cli` get an app context automatically. For standalone Click commands that need one:

```python
from flask.cli import with_appcontext

@click.command()
@with_appcontext
def do_work():
    # access current_app, db, etc.
    ...

app.cli.add_command(do_work)
```

---

## Blueprint CLI Commands

```python
from flask import Blueprint

bp = Blueprint('students', __name__)

@bp.cli.command('create')
@click.argument('name')
def create(name):
    ...

app.register_blueprint(bp)
```

```bash
flask students create alice   # nested under blueprint name by default
```

**Override the group name:**

```python
bp = Blueprint('students', __name__, cli_group='school')
# or at registration:
app.register_blueprint(bp, cli_group='school')
```

```bash
flask school create alice
```

**Flatten to top-level:**

```python
bp = Blueprint('students', __name__, cli_group=None)
# or:
app.register_blueprint(bp, cli_group=None)
```

```bash
flask create alice
```

---

## Custom Scripts (App Factory Pattern)

Use `FlaskGroup` to create a standalone CLI entry point — avoids needing `--app`.

```python
# wiki.py
import click
from flask import Flask
from flask.cli import FlaskGroup

def create_app():
    app = Flask('wiki')
    # configure, register blueprints, etc.
    return app

@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """Management script for the Wiki application."""
```

```toml
# pyproject.toml
[project.scripts]
wiki = "wiki:cli"
```

```bash
pip install -e .
wiki run
wiki shell
wiki create-user admin
```

> ⚠️ Module-level errors will break the reloader when using custom scripts. Prefer the standard `flask` command for development.

---

## CLI Plugins (Extensions)

Extensions can register commands automatically via entry points:

```toml
# pyproject.toml
[project.entry-points."flask.commands"]
my-command = "my_extension.commands:cli"
```

```python
# my_extension/commands.py
import click

@click.command()
def cli():
    ...
```

Once installed in the same virtualenv: `flask my-command`

---

## Flask Shell

```bash
flask shell
```

Opens a Python REPL with app context active and `app` pre-imported.

Add objects to the shell context:

```python
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}
```

---

## PyCharm Configuration

**Professional**: use the built-in Flask run configuration.

**Community / custom commands:**

1. Run → Edit Configurations → + → Python
2. Change "Script path" to **Module name** → enter `flask`
3. Parameters: `--app hello run --debug`
4. Copy the config to create variants for other commands (`shell`, `create-user`, etc.)

---

## Common Patterns & Troubleshooting

| Problem                         | Solution                                                     |
| ------------------------------- | ------------------------------------------------------------ |
| `Could not import module "app"` | Set `--app` or `FLASK_APP`, or name your file `app.py`       |
| Port in use                     | `--port 5001` or kill the process                            |
| dotenv not loading              | `pip install python-dotenv`                                  |
| Custom script reloader broken   | Module-level error in your code; use `flask --app` instead   |
| Blueprint commands not showing  | Ensure `app.register_blueprint(bp)` is called before running |
| Need app context in a task      | Add `@with_appcontext` decorator                             |
