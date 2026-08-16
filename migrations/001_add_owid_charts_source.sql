-- Persist the complete OWID Grapher citationShort value for reuse by crop_main_files.
-- Run once on existing databases before deploying the application change.
ALTER TABLE owid_charts
    ADD COLUMN IF NOT EXISTS source VARCHAR(2048) NOT NULL DEFAULT '' AFTER title;
