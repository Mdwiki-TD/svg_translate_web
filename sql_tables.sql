    -- Adminer 5.3.0 MariaDB 5.5.5-10.6.22-MariaDB-log dump

    SET NAMES utf8;
    SET time_zone = '+00:00';
    SET foreign_key_checks = 0;
    SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

    SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS admin_users (
    id int(11) NOT NULL AUTO_INCREMENT,
    username varchar(255) NOT NULL,
    is_active tinyint(1) NOT NULL DEFAULT 1,
    created_at timestamp NOT NULL DEFAULT current_timestamp(),
    updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    PRIMARY KEY (id),
    UNIQUE KEY username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE IF NOT EXISTS fix_nested_tasks (
    id varchar(128) NOT NULL,
    username text DEFAULT NULL,
    filename text NOT NULL,
    status varchar(64) NOT NULL,
    nested_tags_before int(11) DEFAULT NULL,
    nested_tags_after int(11) DEFAULT NULL,
    nested_tags_fixed int(11) DEFAULT NULL,
    download_result longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(download_result)),
    upload_result longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(upload_result)),
    error_message text DEFAULT NULL,
    created_at timestamp NOT NULL DEFAULT current_timestamp(),
    updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    PRIMARY KEY (id),
    KEY idx_fix_nested_status (status),
    KEY idx_fix_nested_username (username(255)),
    KEY idx_fix_nested_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE IF NOT EXISTS jobs (
    id int(11) NOT NULL AUTO_INCREMENT,
    job_type varchar(255) NOT NULL,
    username varchar(255) DEFAULT NULL,
    status varchar(50) NOT NULL DEFAULT 'pending',
    started_at timestamp NULL DEFAULT NULL,
    completed_at timestamp NULL DEFAULT NULL,
    result_file varchar(500) DEFAULT NULL,
    created_at timestamp NOT NULL DEFAULT current_timestamp(),
    updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    PRIMARY KEY (id),
    KEY idx_status_created (status,created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE IF NOT EXISTS settings (
    id int(11) NOT NULL AUTO_INCREMENT,
    key varchar(190) NOT NULL,
    title varchar(500) NOT NULL,
    value text DEFAULT NULL,
    value_type enum('boolean','string','integer','json') NOT NULL DEFAULT 'boolean',
    PRIMARY KEY (id),
    UNIQUE KEY unique_key (key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS tasks (
    id varchar(128) NOT NULL,
    username text DEFAULT NULL,
    title text NOT NULL,
    normalized_title varchar(512) NOT NULL,
    main_file varchar(512) DEFAULT NULL,
    status varchar(64) NOT NULL,
    form_json longtext DEFAULT NULL,
    data_json longtext DEFAULT NULL,
    results_json longtext DEFAULT NULL,
    created_at timestamp NOT NULL DEFAULT current_timestamp(),
    updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    PRIMARY KEY (id),
    KEY idx_tasks_norm (normalized_title),
    KEY idx_tasks_status (status),
    KEY idx_tasks_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE IF NOT EXISTS task_stages (
    stage_id varchar(255) NOT NULL,
    task_id varchar(128) NOT NULL,
    stage_name varchar(255) NOT NULL,
    stage_number int(11) NOT NULL,
    stage_status varchar(64) NOT NULL,
    stage_sub_name longtext DEFAULT NULL,
    stage_message longtext DEFAULT NULL,
    updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    PRIMARY KEY (stage_id),
    UNIQUE KEY uq_task_stage (task_id,stage_name),
    KEY idx_task_stages_task (task_id,stage_number),
    CONSTRAINT fk_task_stage_task FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE IF NOT EXISTS templates (
    id int(11) NOT NULL AUTO_INCREMENT,
    title varchar(255) NOT NULL,
    main_file varchar(255) DEFAULT NULL,
    last_world_file varchar(255) DEFAULT NULL,
    source varchar(255) NOT NULL DEFAULT '',
    created_at timestamp NOT NULL DEFAULT current_timestamp(),
    updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    PRIMARY KEY (id),
    UNIQUE KEY title (title),
    KEY title_index (title),
    KEY main_file (main_file),
    KEY last_world_file (last_world_file),
    KEY source (source)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


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
