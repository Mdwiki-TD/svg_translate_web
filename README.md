# SVG Translate Web

A Flask-based web application for copying SVG translations between different language versions on Wikimedia Commons. This tool runs on [Wikimedia Toolforge](https://wikitech.wikimedia.org/wiki/Portal:Toolforge) and helps users efficiently manage multilingual SVG files.

## Features

-   **SVG Translation Management**: Copy translations from SVG files to other language versions
-   **Template Processing**: Process MediaWiki templates containing SVG files
-   **OAuth Integration**: Secure authentication via MediaWiki OAuth for file uploads
-   **Task Management**: Track translation tasks with detailed progress monitoring
-   **Admin Dashboard**: Administrative interface for managing templates and tasks
-   **Fix Nested Tags**: Tools to handle and fix nested tag structures in SVG files
-   **Explorer Interface**: Browse and manage SVG files and translations
-   **Rate Limiting**: Built-in rate limiting for API protection

## Prerequisites

-   Python 3.11 or higher (Python 3.13 recommended)
-   MySQL/MariaDB database
-   MediaWiki OAuth consumer credentials (for production use)

## Installation

### Local Development Setup

1. **Clone the repository**

    ```bash
    git clone https://github.com/Mdwiki-TD/svg_translate_web.git
    cd svg_translate_web
    ```

2. **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3. **Set up environment variables**

    Copy the example environment file and configure it:

    ```bash
    cp src/example.env src/.env
    ```

    Edit `src/.env` with your configuration (see [Configuration](#configuration) section below).

4. **Run the application**

    ```bash
    python -m flask --app src.app run
    ```

    Or for debug mode:

    ```bash
    python src/app.py debug
    ```

    The application will be available at `http://localhost:5000`

## Configuration

### Required Environment Variables

Create a `.env` file in the `src/` directory with the following variables:

#### Flask Configuration

```bash
# Generate with: python -c "import secrets; print(secrets.token_hex(16))"
FLASK_SECRET_KEY=your_secret_key_here
```

#### Storage Paths

```bash
MAIN_DIR=/path/to/svg/storage
```

#### Database Configuration

```bash
DB_NAME=svg_langs
DB_HOST=127.0.0.1
TOOL_REPLICA_USER=your_db_user
TOOL_REPLICA_PASSWORD=your_db_password
```

#### OAuth Configuration

```bash
OAUTH_MWURI=https://commons.wikimedia.org/w/index.php
OAUTH_CONSUMER_KEY=your_consumer_key
OAUTH_CONSUMER_SECRET=your_consumer_secret

# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
OAUTH_ENCRYPTION_KEY=your_fernet_key_here
```

#### Authentication & Security

```bash
AUTH_COOKIE_NAME=uid_enc
AUTH_COOKIE_MAX_AGE=2592000  # 30 days
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

#### Other Settings

```bash
DISABLE_UPLOADS=0
UPLOAD_END_POINT=commons.wikimedia.org
# Replace with your actual contact email
USER_AGENT="Copy SVG Translations/1.0 (https://copy-svg-langs.toolforge.org; your-contact-email@example.org)"
ADMINS=user1,user2,user3
```

For detailed OAuth setup instructions, see [docs/oauth.md](docs/oauth.md).

## Usage

### Basic Workflow

1. **Login**: Navigate to the application and login using your Wikimedia account (OAuth)
2. **Start Translation Task**:
    - Enter a template title (e.g., `Template:OWID/death rate from obesity`)
    - Optionally specify a manual main file title
    - Choose options for overwriting and uploading
    - Click "Start" to begin the translation task
3. **Monitor Progress**: Track task progress through the web interface
4. **Review Results**: Check completed translations in the explorer

### Admin Features

Administrators (configured via `ADMINS` environment variable) have access to:

-   Template management interface
-   Task overview and management
-   System configuration

## Development

### Code Style

The project uses:

-   **Black** for code formatting (line length: 120)
-   **isort** for import sorting
-   **flake8** for linting
-   **mypy** for type checking
-   **pylint** for additional linting

Configuration files:

-   `pyproject.toml` - Black and isort configuration
-   `.flake8` - Flake8 configuration
-   `.pylintrc` - Pylint configuration
-   `mypy.ini` - MyPy configuration

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_task_routes.py

# Run with coverage
pytest --cov=src
```

### Project Structure

```
svg_translate_web/
├── src/
│   ├── app/                    # Flask application
│   │   ├── app_routes/         # Route blueprints
│   │   │   ├── admin/          # Admin routes
│   │   │   ├── auth/           # Authentication routes
│   │   │   ├── tasks/          # Task management routes
│   │   │   ├── explorer/       # File explorer routes
│   │   │   └── ...
│   │   ├── db/                 # Database models and stores
│   │   ├── users/              # User management
│   │   └── threads/            # Background task threads
│   ├── templates/              # Jinja2 templates
│   ├── static/                 # Static assets (CSS, JS)
│   └── app.py                  # WSGI entry point
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── tests/                      # Test suite
├── docs/                       # Documentation
└── web_sh/                     # Deployment scripts
```

## Deployment

### Toolforge Deployment

The application is designed to run on Wikimedia Toolforge. Configuration is provided in `service.template`:

```yaml
backend: kubernetes
cpu: 3
mem: 6Gi
replicas: 2
type: python3.13
```

Deployment is automated via GitHub Actions when pushing to the `main` branch.

### Manual Deployment Steps

1. Ensure all environment variables are configured on Toolforge
2. Upload the code to Toolforge
3. Install dependencies: `pip install -r requirements.txt`
4. Start the webservice: `toolforge-webservice python3.13 start`

## Dependencies

Key dependencies include:

-   **Flask** - Web framework
-   **flask-limiter** - Rate limiting
-   **mwclient** - MediaWiki API client
-   **mwoauth** - MediaWiki OAuth
-   **lxml** - XML processing
-   **pymysql** - MySQL database connector
-   **CopySVGTranslation** - Core SVG translation library
-   **cryptography** - Encryption support

See `requirements.txt` for complete list.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes following the code style guidelines
4. Run tests and linting
5. Commit your changes (`git commit -am 'Add your feature'`)
6. Push to the branch (`git push origin feature/your-feature`)
7. Create a Pull Request

## License

This project is maintained by the Mdwiki-TD organization. Please refer to the repository for license information.

## Support

For issues, questions, or contributions, please:

-   Open an issue on [GitHub](https://github.com/Mdwiki-TD/svg_translate_web/issues)
-   Visit the tool at [copy-svg-langs.toolforge.org](https://copy-svg-langs.toolforge.org)

## Acknowledgments

This tool is built to support the Wikimedia community in managing multilingual SVG content on Wikimedia Commons.
