""" """

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
    owid_charts: str


user_tokens = """
    CREATE TABLE IF NOT EXISTS user_tokens (
        user_id int NOT NULL,
        username VARCHAR(255) NOT NULL,
        access_token varbinary(1024) NOT NULL,
        access_secret varbinary(1024) NOT NULL,
        created_at timestamp NOT NULL DEFAULT current_timestamp(),
        updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        last_used_at datetime DEFAULT NULL,
        rotated_at datetime DEFAULT NULL,
        PRIMARY KEY (user_id),
        KEY idx_user_tokens_username (username)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;
"""

tasks = """
    CREATE TABLE IF NOT EXISTS tasks (
        id VARCHAR(128) NOT NULL,
        username text DEFAULT NULL,
        title text NOT NULL,
        normalized_title VARCHAR(512) NOT NULL,
        main_file VARCHAR(512) DEFAULT NULL,
        status VARCHAR(64) NOT NULL,
        form_json longtext DEFAULT NULL,
        data_json longtext DEFAULT NULL,
        results_json longtext DEFAULT NULL,
        created_at timestamp NOT NULL DEFAULT current_timestamp(),
        updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        PRIMARY KEY (id),
        KEY idx_tasks_norm (normalized_title),
        KEY idx_tasks_status (status),
        KEY idx_tasks_created (created_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;
"""

task_stages = """
    CREATE TABLE IF NOT EXISTS task_stages (
        stage_id VARCHAR(255) NOT NULL,
        task_id VARCHAR(128) NOT NULL,
        stage_name VARCHAR(255) NOT NULL,
        stage_number INT NOT NULL,
        stage_status VARCHAR(64) NOT NULL,
        stage_sub_name longtext DEFAULT NULL,
        stage_message longtext DEFAULT NULL,
        updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        PRIMARY KEY (stage_id),
        UNIQUE KEY uq_task_stage (task_id, stage_name),
        KEY idx_task_stages_task (task_id, stage_number),
        CONSTRAINT fk_task_stage_task FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;
"""

fix_nested_tasks = """
    CREATE TABLE IF NOT EXISTS fix_nested_tasks (
        id VARCHAR(128) NOT NULL,
        username text DEFAULT NULL,
        filename text NOT NULL,
        status VARCHAR(64) NOT NULL,
        nested_tags_before INT DEFAULT NULL,
        nested_tags_after INT DEFAULT NULL,
        nested_tags_fixed INT DEFAULT NULL,
        download_result JSON NULL,
        upload_result JSON NULL,
        error_message text DEFAULT NULL,
        created_at timestamp NOT NULL DEFAULT current_timestamp(),
        updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        PRIMARY KEY (id),
        INDEX idx_fix_nested_status (status),
        INDEX idx_fix_nested_username (username (255)),
        INDEX idx_fix_nested_created (created_at)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;
"""

# pymysql.err.OperationalError: (1364, "Field 'slug' doesn't have a default value")
templates = """
    CREATE TABLE IF NOT EXISTS templates (
        id INT NOT NULL AUTO_INCREMENT,
        title VARCHAR(255) NOT NULL,
        main_file VARCHAR(255) DEFAULT NULL,
        last_world_file VARCHAR(255) DEFAULT NULL,
        slug VARCHAR(255) NOT NULL DEFAULT '',
        source VARCHAR(255) NOT NULL DEFAULT '',
        created_at timestamp NOT NULL DEFAULT current_timestamp(),
        updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        PRIMARY KEY (id),
        UNIQUE KEY title (title),
        KEY title_index (title),
        KEY main_file (main_file),
        KEY last_world_file (last_world_file),
        KEY source (source)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

"""

admin_users = """
    CREATE TABLE IF NOT EXISTS admin_users (
        id INT NOT NULL AUTO_INCREMENT,
        username VARCHAR(255) NOT NULL,
        is_active tinyint (1) NOT NULL DEFAULT 1,
        created_at timestamp NOT NULL DEFAULT current_timestamp(),
        updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        PRIMARY KEY (id),
        UNIQUE KEY username (username)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;
"""

jobs = """
    CREATE TABLE IF NOT EXISTS jobs (
    id INT NOT NULL AUTO_INCREMENT,
        job_type VARCHAR(255) NOT NULL,
        username VARCHAR(255) DEFAULT NULL,
        status VARCHAR(50) NOT NULL DEFAULT 'pending',
        started_at timestamp NULL DEFAULT NULL,
        completed_at timestamp NULL DEFAULT NULL,
        result_file VARCHAR(500) DEFAULT NULL,
        created_at timestamp NOT NULL DEFAULT current_timestamp(),
        updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        PRIMARY KEY (id),
        INDEX idx_status_created (status, created_at)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;
"""

settings = """
    CREATE TABLE IF NOT EXISTS settings (
        `id` INT NOT NULL AUTO_INCREMENT,
        `key` VARCHAR(190) NOT NULL,
        `title` VARCHAR(500) NOT NULL,
        `value` text DEFAULT NULL,
        `value_type` enum ('boolean', 'string', 'integer', 'json') NOT NULL DEFAULT 'boolean',
        PRIMARY KEY (`id`),
        UNIQUE KEY unique_key (`key`)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
"""

owid_charts = """
    CREATE TABLE IF NOT EXISTS owid_charts (
        id INT NOT NULL AUTO_INCREMENT,
        slug VARCHAR(255) NOT NULL,
        title VARCHAR(500) NOT NULL,
        has_map_tab TINYINT(1) DEFAULT 0,
        max_time INT DEFAULT NULL,
        min_time INT DEFAULT NULL,
        default_tab VARCHAR(50) DEFAULT NULL,
        is_published TINYINT(1) DEFAULT 0,
        single_year_data TINYINT(1) DEFAULT 0,
        len_years INT DEFAULT NULL,
        has_timeline TINYINT(1) DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        UNIQUE KEY unique_slug (slug),
        KEY idx_slug (slug),
        KEY idx_published (is_published)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;
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
    owid_charts=owid_charts,
)
