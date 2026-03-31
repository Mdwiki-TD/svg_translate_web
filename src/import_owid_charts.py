#!/usr/bin/env python
"""Import OWID charts data from CSV file into the database."""

from __future__ import annotations

import csv
import logging
import os
import sys
from typing import Any, Dict, List

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()


def parse_bool(value: str) -> bool:
    """Parse boolean value from CSV string."""
    if not value:
        return False
    return value.strip().lower() in {"yes", "true", "1", "y"}


def parse_int(value: str) -> int | None:
    """Parse integer value from CSV string."""
    if not value or value.strip() == "":
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None


def read_csv_file(file_path: str) -> List[Dict[str, Any]]:
    """Read CSV file and return list of chart data dictionaries."""
    charts = []

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


def import_charts_to_db(charts: List[Dict[str, Any]]) -> tuple[int, int, int]:
    """
    Import charts into the database.

    Returns:
        tuple: (number of inserted charts, number of updated charts, number of failed charts)
    """
    db_name = os.getenv("DB_NAME", "")

    if not db_name:
        raise RuntimeError("DB_NAME environment variable is not set")

    try:
        import pymysql
    except ImportError:
        raise RuntimeError("PyMySQL is not installed. Run: pip install pymysql")

    logger.info(f"Connecting to database: {db_name}")

    connection = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=db_name,
        user=os.getenv("TOOL_REPLICA_USER", None),
        password=os.getenv("TOOL_REPLICA_PASSWORD", None),
        charset="utf8mb4",
        autocommit=True,
    )

    cursor = connection.cursor()

    insert_sql = """
    INSERT INTO owid_charts (
        slug, title, has_map_tab, max_time, min_time,
        default_tab, is_published, single_year_data, len_years, has_timeline
    ) VALUES (
        %(slug)s, %(title)s, %(has_map_tab)s, %(max_time)s, %(min_time)s,
        %(default_tab)s, %(is_published)s, %(single_year_data)s, %(len_years)s, %(has_timeline)s
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
    """

    inserted = 0
    updated = 0
    failed = 0

    logger.info("Importing charts into database...")

    for i, chart_data in enumerate(charts, 1):
        try:
            # Check if chart exists
            cursor.execute("SELECT chart_id FROM owid_charts WHERE slug = %s", (chart_data["slug"],))
            exists = cursor.fetchone()

            if exists:
                # Update existing chart
                cursor.execute(insert_sql, chart_data)
                if cursor.rowcount > 0:
                    updated += 1
            else:
                # Insert new chart
                cursor.execute(insert_sql, chart_data)
                if cursor.rowcount > 0:
                    inserted += 1

            if i % 100 == 0:
                logger.info(f"Processed {i}/{len(charts)} charts...")

        except Exception as e:
            logger.error(f"Failed to import chart {chart_data['slug']}: {e}")
            failed += 1

    cursor.close()
    connection.close()

    return inserted, updated, failed


def main():
    """Main import function."""
    csv_file = os.path.join(os.path.dirname(__file__), "src", "main_app", "data", "owid_charts.csv")

    # Try alternative path if running from different directory
    if not os.path.exists(csv_file):
        csv_file = os.path.join(os.getcwd(), "src", "main_app", "data", "owid_charts.csv")

    if not os.path.exists(csv_file):
        logger.error(f"CSV file not found: {csv_file}")
        sys.exit(1)

    print("=" * 70)
    print("OWID Charts CSV Import")
    print("=" * 70)
    print(f"CSV File: {csv_file}")
    print(f"Database: {os.getenv('DB_NAME', 'Not set')}")
    print(f"Host: {os.getenv('DB_HOST', 'localhost')}")
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
            print(f"\nView charts at:")
            print(f"  - Admin:  http://localhost:5000/admin/owid-charts")
            print(f"  - Public: http://localhost:5000/owid-charts/")
            print(f"  - Test:   http://localhost:5000/owid-charts/all")

    except Exception as e:
        logger.exception(f"Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
