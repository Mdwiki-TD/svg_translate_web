
from dataclasses import dataclass


@dataclass
class TablesCreatesSql:
    user_tokens: str


user_tokens = """
    CREATE TABLE IF NOT EXISTS user_tokens (
        user_id INT PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        access_token VARBINARY(1024) NOT NULL,
        access_secret VARBINARY(1024) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        last_used_at DATETIME DEFAULT NULL,
        rotated_at DATETIME DEFAULT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

sql_tables = TablesCreatesSql(
    user_tokens=user_tokens
)
