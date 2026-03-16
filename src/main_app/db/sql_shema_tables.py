from dataclasses import dataclass


@dataclass
class TablesCreatesSql:
    user_tokens: str
    tasks: str
    task_stages: str
    fix_nested_tasks: str
    templates: str
    admin_users: str
    jobs: str
    settings: str


user_tokens = """
    CREATE TABLE IF NOT EXISTS user_tokens (
        user_id VARCHAR(255) NOT NULL,
        username VARCHAR(255) NOT NULL,
        access_token varbinary(1024) NOT NULL,
        access_secret varbinary(1024) NOT NULL,
        created_at timestamp NOT NULL DEFAULT current_timestamp(),
        updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        last_used_at datetime DEFAULT NULL,
        rotated_at datetime DEFAULT NULL,
        PRIMARY KEY (user_id),
        KEY idx_user_tokens_username (username)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
"""

tasks = """
    CREATE TABLE IF NOT EXISTS tasks (
        id VARCHAR(128) PRIMARY KEY,
        username text NULL,
        title text NOT NULL,
        normalized_title VARCHAR(512) NOT NULL,
        main_file VARCHAR(512) NULL,
        status VARCHAR(64) NOT NULL,
        form_json longtext NULL,
        data_json longtext NULL,
        results_json longtext NULL,
        created_at timestamp DEFAULT current_timestamp(),
        updated_at timestamp DEFAULT current_timestamp() ON UPDATE current_timestamp()
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

task_stages = """
    CREATE TABLE IF NOT EXISTS task_stages (
        stage_id VARCHAR(255) PRIMARY KEY,
        task_id VARCHAR(128) NOT NULL,
        stage_name VARCHAR(255) NOT NULL,
        stage_number INT NOT NULL,
        stage_status VARCHAR(64) NOT NULL,
        stage_sub_name longtext NULL,
        stage_message longtext NULL,
        updated_at timestamp DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        CONSTRAINT fk_task_stage_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        CONSTRAINT uq_task_stage UNIQUE (task_id, stage_name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

fix_nested_tasks = """
    CREATE TABLE IF NOT EXISTS fix_nested_tasks (
        id VARCHAR(128) PRIMARY KEY,
        username text NULL,
        filename text NOT NULL,
        status VARCHAR(64) NOT NULL,
        nested_tags_before INT NULL,
        nested_tags_after INT NULL,
        nested_tags_fixed INT NULL,
        download_result JSON NULL,
        upload_result JSON NULL,
        error_message text NULL,
        created_at timestamp DEFAULT current_timestamp(),
        updated_at timestamp DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        INDEX idx_fix_nested_status (status),
        INDEX idx_fix_nested_username (username(255)),
        INDEX idx_fix_nested_created (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

templates = """
    CREATE TABLE IF NOT EXISTS templates (
        id int(11) NOT NULL AUTO_INCREMENT,
        title VARCHAR(255) NOT NULL,
        main_file VARCHAR(255) DEFAULT NULL,
        last_world_file VARCHAR(255) DEFAULT NULL,
        source VARCHAR(255) NOT NULL DEFAULT '',
        created_at timestamp NOT NULL DEFAULT current_timestamp(),
        updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        PRIMARY KEY (id),
        UNIQUE KEY title (title),
        KEY title_index (title),
        KEY main_file (main_file),
        KEY last_world_file (last_world_file),
        KEY source (source)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

admin_users = """
    CREATE TABLE IF NOT EXISTS admin_users (
        id int(11) NOT NULL AUTO_INCREMENT,
        username VARCHAR(255) NOT NULL,
        is_active tinyint(1) NOT NULL DEFAULT 1,
        created_at timestamp NOT NULL DEFAULT current_timestamp(),
        updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        PRIMARY KEY (id),
        UNIQUE KEY username (username)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
"""

jobs = """
    CREATE TABLE IF NOT EXISTS jobs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        job_type VARCHAR(255) NOT NULL,
        username VARCHAR(255) NULL,
        status VARCHAR(50) NOT NULL DEFAULT 'pending',
        started_at timestamp NULL,
        completed_at timestamp NULL,
        result_file VARCHAR(500) NULL,
        created_at timestamp DEFAULT current_timestamp(),
        updated_at timestamp DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        INDEX idx_status_created (status, created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

settings = """
    CREATE TABLE IF NOT EXISTS settings (
        id INT NOT NULL AUTO_INCREMENT,
        key VARCHAR(190) COLLATE utf8mb4_unicode_ci NOT NULL,
        title VARCHAR(500) COLLATE utf8mb4_unicode_ci NOT NULL,
        value text COLLATE utf8mb4_unicode_ci NULL,
        value_type enum('boolean','string','integer','json')
            COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'boolean',
        PRIMARY KEY (id),
        UNIQUE KEY unique_key (key)
    ) ENGINE=InnoDB
        DEFAULT CHARSET=utf8mb4
        COLLATE=utf8mb4_unicode_ci;
"""

# sql_tables
sql_tables = TablesCreatesSql(
    user_tokens=user_tokens,
    tasks=tasks,
    task_stages=task_stages,
    fix_nested_tasks=fix_nested_tasks,
    templates=templates,
    admin_users=admin_users,
    jobs=jobs,
    settings=settings,
)
