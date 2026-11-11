#!/usr/bin/env python
"""Import OWID charts data from CSV file into the database."""

from __future__ import annotations

import csv
import logging
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

if os.getenv("APP_ENV", os.getenv("FLASK_ENV")) not in ["production", "testing"]:
    _env_file_path = str(Path(__file__).parent.parent.parent / ".env")
    load_dotenv(_env_file_path)


INSERT_SQL = text("""
    INSERT INTO owid_charts (
        slug, title, has_map_tab, max_time, min_time,
        default_tab, is_published, single_year_data, len_years, has_timeline
    ) VALUES (
        :slug, :title, :has_map_tab, :max_time, :min_time,
        :default_tab, :is_published, :single_year_data, :len_years, :has_timeline
    )
    ON DUPLICATE KEY UPDATE
        title = VALUES(title),
        has_map_tab = VALUES(has_map_tab),
        max_time = VALUES(max_time),
        min_time = VALUES(min_time),
        default_tab = VALUES(default_tab),
        is_published = VALUES(is_published),
        single_year_data = VALUES(single_year_data),
        len_years = VALUES(len_years),
        has_timeline = VALUES(has_timeline)
    """)


def get_database_uri() -> str:
    """Return the SQLAlchemy database URI from the environment."""
    sqlalchemy_database_uri: str = os.environ.get("DATABASE_URI", "")

    if not sqlalchemy_database_uri:
        raise RuntimeError("DATABASE_URI environment variable is not set")

    return sqlalchemy_database_uri


def parse_bool(value: str | int) -> bool:
    """Parse boolean value from CSV string."""
    if not value:
        return False
    if isinstance(value, int):
        value = str(value)
    return value.strip().lower() in {"yes", "true", "1", "y"}


def parse_int(value: str) -> int | None:
    """Parse integer value from CSV string."""
    if not value or value.strip() == "":
        return None
    try:
        return int(value.strip())
    except (TypeError, ValueError):
        return None


def read_csv_file(file_path: str) -> list[dict[str, Any]]:
    """Read CSV file and return list of chart data dictionaries."""
    charts: list[Any] = []

    logger.info(f"Reading CSV file: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            chart_data = {
                "slug": row.get("slug", "").strip(),
                "title": row.get("title", "").strip(),
                "has_map_tab": parse_bool(row.get("has_map_tab", "")),
                "max_time": parse_int(row.get("max_time", "")),
                "min_time": parse_int(row.get("min_time", "")),
                "default_tab": row.get("default_tab", "").strip() or None,
                "is_published": parse_bool(row.get("is_published", "")),
                "single_year_data": parse_bool(row.get("single_year_data", "")),
                "len_years": parse_int(row.get("len_years", "")),
                "has_timeline": parse_bool(row.get("has_timeline", "")),
            }

            # Validate required fields
            if not chart_data["slug"]:
                logger.warning(f"Skipping row with empty slug: {row}")
                continue

            if not chart_data["title"]:
                logger.warning(f"Skipping row {chart_data['slug']} with empty title")
                continue

            charts.append(chart_data)

    logger.info(f"Read {len(charts)} charts from CSV")
    return charts


def import_charts_to_db(charts: list[dict[str, Any]]) -> tuple[int, int, int]:
    """
    Import charts into the database using SQLAlchemy.

    Returns:
        tuple: (number of inserted charts, number of updated charts, number of failed charts)
    """
    sqlalchemy_database_uri = get_database_uri()
    db_name = make_url(sqlalchemy_database_uri).database

    logger.info(f"Connecting to database: {db_name}")

    engine = create_engine(sqlalchemy_database_uri, pool_pre_ping=True)

    inserted = 0
    updated = 0
    failed = 0

    try:
        # Load all existing slugs once instead of querying for every row
        with engine.connect() as connection:
            existing_slugs = {row[0] for row in connection.execute(text("SELECT slug FROM owid_charts"))}

        logger.info("Importing charts into database...")

        for i, chart_data in enumerate(charts, 1):
            try:
                # Each chart runs in its own transaction, so one failure doesn't affect the others
                with engine.begin() as connection:
                    connection.execute(INSERT_SQL, chart_data)

                if chart_data["slug"] in existing_slugs:
                    updated += 1
                else:
                    inserted += 1
                    existing_slugs.add(chart_data["slug"])

                if i % 100 == 0:
                    logger.info(f"Processed {i}/{len(charts)} charts...")

            except Exception as e:
                logger.error(f"Failed to import chart {chart_data['slug']}: {e}")
                failed += 1
    finally:
        engine.dispose()

    return inserted, updated, failed


def main() -> None:
    """Main import function."""
    csv_file = os.path.join(os.path.dirname(__file__), "src", "main_app", "data", "owid_charts.csv")

    # Try alternative path if running from different directory
    if not os.path.exists(csv_file):
        csv_file = os.path.join(os.getcwd(), "src", "main_app", "data", "owid_charts.csv")

    if not os.path.exists(csv_file):
        logger.error(f"CSV file not found: {csv_file}")
        sys.exit(1)

    try:
        db_url = make_url(get_database_uri())
        db_name, db_host = db_url.database, db_url.host
    except Exception:
        db_name, db_host = "Not set", "Not set"

    print("=" * 70)
    print("OWID Charts CSV Import")
    print("=" * 70)
    print(f"CSV File: {csv_file}")
    print(f"Database: {db_name}")
    print(f"Host: {db_host}")
    print("-" * 70)

    try:
        # Read CSV file
        charts = read_csv_file(csv_file)

        if not charts:
            logger.error("No valid charts found in CSV file")
            sys.exit(1)

        # Import to database
        inserted, updated, failed = import_charts_to_db(charts)

        print("\n" + "=" * 70)
        print("Import Summary:")
        print("=" * 70)
        print(f"Total charts in CSV: {len(charts)}")
        print(f"Inserted (new):     {inserted}")
        print(f"Updated (existing): {updated}")
        print(f"Failed:             {failed}")
        print("=" * 70)

        if failed > 0:
            logger.warning(f"{failed} charts failed to import. Check logs for details.")
            sys.exit(1)
        else:
            logger.info("Import completed successfully!")
            print("\n✓ All charts imported successfully!")
            print("\nView charts at:")
            print("  - Admin:  http://localhost:5000/admin_panel/owidcharts")
            print("  - Public: http://localhost:5000/owidcharts/")
            print("  - Test:   http://localhost:5000/owidcharts/all")

    except Exception as e:
        logger.exception(f"Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
