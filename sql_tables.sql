-- Adminer 5.3.0 MariaDB 5.5.5-10.6.22-MariaDB-log dump
SET
    NAMES utf8;

SET
    time_zone = '+00:00';

SET
    foreign_key_checks = 0;

SET
    sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

SET
    NAMES utf8mb4;

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


CREATE TABLE IF NOT EXISTS templates (
    id INT NOT NULL AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    main_file VARCHAR(255) DEFAULT NULL,
    last_world_file VARCHAR(255) DEFAULT NULL,
    last_world_year INT DEFAULT NULL,
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

CREATE TABLE IF NOT EXISTS admin_users (
    id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(255) NOT NULL,
    is_active tinyint (1) NOT NULL DEFAULT 1,
    created_at timestamp NOT NULL DEFAULT current_timestamp(),
    updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    PRIMARY KEY (id),
    UNIQUE KEY username (username)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

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

CREATE TABLE IF NOT EXISTS settings (
    `id` INT NOT NULL AUTO_INCREMENT,
    `key` VARCHAR(190) NOT NULL,
    `title` VARCHAR(500) NOT NULL,
    `value` text DEFAULT NULL,
    `value_type` enum ('boolean', 'string', 'integer', 'json') NOT NULL DEFAULT 'boolean',
    PRIMARY KEY (`id`),
    UNIQUE KEY unique_key (`key`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS owid_charts (
    chart_id INT NOT NULL AUTO_INCREMENT,
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
    PRIMARY KEY (chart_id),
    UNIQUE KEY unique_slug (slug),
    KEY idx_slug (slug),
    KEY idx_published (is_published)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE OR REPLACE VIEW owid_charts_templates AS
SELECT
    c.chart_id,
    t.id AS template_id,
    t.title AS template_title
FROM owid_charts c
LEFT JOIN templates t
    -- ON t.source LIKE '%/grapher/%'
    -- AND SUBSTRING_INDEX(SUBSTRING_INDEX(t.source, '/grapher/', -1), '?', 1) = c.slug;
    ON t.slug = c.slug;

CREATE OR REPLACE VIEW templates_need_update AS
SELECT
    t.id AS template_id,
    t.title AS template_title,
    t.slug AS slug,
    c.max_time,
    t.last_world_year
FROM owid_charts c
JOIN templates t
    ON t.slug = c.slug
WHERE t.last_world_year != c.max_time
   AND t.last_world_year IS NOT NULL
