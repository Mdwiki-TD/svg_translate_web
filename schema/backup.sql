-- Adminer 4.8.1 MySQL 10.6.22-MariaDB-log dump
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

CREATE TABLE
  `admin_users` (
    `id` int (11) NOT NULL AUTO_INCREMENT,
    `username` varchar(255) NOT NULL,
    `is_active` tinyint (1) NOT NULL DEFAULT 1,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    PRIMARY KEY (`id`),
    UNIQUE KEY `username` (`username`)
  ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE
  `error_logs` (
    `id` bigint (20) NOT NULL AUTO_INCREMENT,
    `created_at` datetime NOT NULL DEFAULT current_timestamp(),
    `status_code` smallint (6) NOT NULL,
    `method` varchar(10) NOT NULL DEFAULT '',
    `path` varchar(500) NOT NULL,
    `query_str` text DEFAULT NULL,
    `ip` varchar(45) NOT NULL DEFAULT '',
    `access_route` varchar(255) DEFAULT NULL,
    `has_cookie` tinyint (1) NOT NULL DEFAULT 0,
    `suspected_bot` tinyint (1) NOT NULL DEFAULT 0,
    `username` varchar(120) DEFAULT NULL,
    `user_agent` varchar(500) DEFAULT NULL,
    `accept` varchar(500) DEFAULT NULL,
    `accept_language` varchar(255) DEFAULT NULL,
    `accept_encoding` varchar(255) DEFAULT NULL,
    `referer` varchar(500) DEFAULT NULL,
    `sec_fetch_mode` varchar(30) DEFAULT NULL,
    `sec_fetch_dest` varchar(30) DEFAULT NULL,
    `sec_ch_ua` varchar(255) DEFAULT NULL,
    `request_id` varchar(64) DEFAULT NULL,
    `error` varchar(500) DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_error_logs_request_id` (`request_id`),
    KEY `idx_status_path` (`status_code`, `path` (191)),
    KEY `ix_error_logs_created_at` (`created_at`)
  ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE
  `jobs` (
    `id` int (11) NOT NULL AUTO_INCREMENT,
    `job_type` varchar(255) NOT NULL,
    `username` varchar(255) DEFAULT NULL,
    `status` varchar(50) NOT NULL DEFAULT 'pending',
    `started_at` timestamp NULL DEFAULT NULL,
    `completed_at` timestamp NULL DEFAULT NULL,
    `result_file` varchar(500) DEFAULT NULL,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    `is_running` tinyint (4) DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `idx_unique_active_job` (`job_type`, `is_running`),
    KEY `idx_status_created` (`status`, `created_at`)
  ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE
  `owid_charts` (
    `chart_id` int (11) NOT NULL AUTO_INCREMENT,
    `slug` varchar(255) NOT NULL,
    `title` varchar(500) NOT NULL,
    `source` varchar(2048) NOT NULL DEFAULT '',
    `has_map_tab` tinyint (1) DEFAULT 0,
    `max_time` int (11) DEFAULT NULL,
    `min_time` int (11) DEFAULT NULL,
    `default_tab` varchar(50) DEFAULT NULL,
    `is_published` tinyint (1) DEFAULT 0,
    `single_year_data` tinyint (1) DEFAULT 0,
    `len_years` int (11) DEFAULT NULL,
    `has_timeline` tinyint (1) DEFAULT 0,
    `status_404` int (11) DEFAULT NULL,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    `owid_variable_id` int (11) DEFAULT NULL,
    PRIMARY KEY (`chart_id`),
    UNIQUE KEY `unique_slug` (`slug`),
    KEY `idx_slug` (`slug`),
    KEY `idx_published` (`is_published`)
  ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE
  `owid_charts_templates` (
    `chart_id` int (11),
    `template_id` int (11),
    `template_title` varchar(255)
  );

CREATE TABLE
  `owid_slug_redirects` (
    `id` int (11) NOT NULL AUTO_INCREMENT,
    `slug` varchar(255) NOT NULL,
    `redirect_to` varchar(255) NOT NULL,
    `should_be_replaced` tinyint (1) DEFAULT 0,
    `created_at` datetime NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (`id`),
    UNIQUE KEY `slug` (`slug`)
  ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE
  `settings` (
    `id` int (11) NOT NULL AUTO_INCREMENT,
    `key` varchar(190) NOT NULL,
    `title` varchar(500) NOT NULL,
    `value` text DEFAULT NULL,
    `value_type` enum ('boolean', 'string', 'integer', 'json') NOT NULL DEFAULT 'boolean',
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_key` (`key`)
  ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE
  `templates` (
    `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    `id` int (11) NOT NULL AUTO_INCREMENT,
    `title` varchar(255) NOT NULL,
    `main_file` varchar(255) DEFAULT NULL,
    `last_world_file` varchar(255) DEFAULT NULL,
    `last_world_year` int (11) DEFAULT NULL,
    `slug` varchar(255) NOT NULL DEFAULT '',
    `source` varchar(255) NOT NULL DEFAULT '',
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `files` int (11) DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `title` (`title`),
    KEY `title_index` (`title`),
    KEY `main_file` (`main_file`),
    KEY `last_world_file` (`last_world_file`),
    KEY `source` (`source`),
    KEY `last_world_year` (`last_world_year`)
  ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE
  `templates_need_update` (
    `template_id` int (11),
    `template_title` varchar(255),
    `slug` varchar(255),
    `owid_variable_id` int (11),
    `max_time` int (11),
    `last_world_year` int (11)
  );

CREATE TABLE
  `users` (
    `user_id` int (11) NOT NULL AUTO_INCREMENT,
    `username` varchar(255) NOT NULL,
    `can_run_jobs` tinyint (1) NOT NULL DEFAULT 0,
    `can_run_bg_jobs` tinyint (1) NOT NULL,
    `created_at` datetime NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (`user_id`),
    UNIQUE KEY `username` (`username`)
  ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE
  `user_tokens` (
    `user_id` int (11) NOT NULL,
    `access_token` blob NOT NULL,
    `access_secret` blob NOT NULL,
    `created_at` datetime NOT NULL DEFAULT current_timestamp(),
    `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
    `last_used_at` datetime DEFAULT current_timestamp(),
    `rotated_at` datetime DEFAULT NULL,
    PRIMARY KEY (`user_id`),
    CONSTRAINT `user_tokens_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
  ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `owid_charts_templates`;

CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `owid_charts_templates` AS
select
  `c`.`chart_id` AS `chart_id`,
  `t`.`id` AS `template_id`,
  `t`.`title` AS `template_title`
from
  (
    `owid_charts` `c`
    left join `templates` `t` on (`t`.`slug` = `c`.`slug`)
  );

DROP TABLE IF EXISTS `templates_need_update`;

CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `templates_need_update` AS
select
  `t`.`id` AS `template_id`,
  `t`.`title` AS `template_title`,
  `t`.`slug` AS `slug`,
  `c`.`owid_variable_id` AS `owid_variable_id`,
  `c`.`max_time` AS `max_time`,
  `t`.`last_world_year` AS `last_world_year`
from
  (
    `owid_charts` `c`
    join `templates` `t` on (
      `t`.`slug` collate utf8mb4_unicode_ci = `c`.`slug` collate utf8mb4_unicode_ci
    )
  )
where
  `t`.`last_world_year` < `c`.`max_time`
  and `c`.`max_time` <= year (current_timestamp())
  and `t`.`last_world_year` is not null
  and `c`.`status_404` is null;

-- 2026-11-16 02:06:27
