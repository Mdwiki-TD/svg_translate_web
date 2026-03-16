
from dataclasses import dataclass


@dataclass
class TablesCreatesSql:
    user_tokens: str
    tasks: str
    task_stages: str


user_tokens = """
    CREATE TABLE IF NOT EXISTS user_tokens (
        user_id varchar(255) NOT NULL,
        username varchar(255) NOT NULL,
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
        username TEXT NULL,
        title TEXT NOT NULL,
        normalized_title VARCHAR(512) NOT NULL,
        main_file VARCHAR(512) NULL,
        status VARCHAR(64) NOT NULL,
        form_json LONGTEXT NULL,
        data_json LONGTEXT NULL,
        results_json LONGTEXT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

task_stages = """
    CREATE TABLE IF NOT EXISTS task_stages (
        stage_id VARCHAR(255) PRIMARY KEY,
        task_id VARCHAR(128) NOT NULL,
        stage_name VARCHAR(255) NOT NULL,
        stage_number INT NOT NULL,
        stage_status VARCHAR(64) NOT NULL,
        stage_sub_name LONGTEXT NULL,
        stage_message LONGTEXT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT fk_task_stage_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        CONSTRAINT uq_task_stage UNIQUE (task_id, stage_name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


sql_tables = TablesCreatesSql(
    user_tokens=user_tokens,
    tasks=tasks,
    task_stages=task_stages,
)
