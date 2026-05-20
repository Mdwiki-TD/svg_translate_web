#!/usr/bin/env python
"""Offline tool to capitalize the first letter of OWID subpages on Wikimedia Commons.

Lists every page whose title starts with ``Template:OWID/`` or ``OWID/`` and
renames it so that the character immediately after ``OWID/`` is uppercase.

Examples
--------
    Template:OWID/daily_meat_consumption_per_person
        -> Template:OWID/Daily_meat_consumption_per_person

    OWID/daily_meat_consumption_per_person
        -> OWID/Daily_meat_consumption_per_person

Usage
-----
    # List candidates only (safe, no changes):
    python _works_files/rename_owid_pages.py

    # Actually perform the renames:
    python _works_files/rename_owid_pages.py --apply

    # Don't leave a redirect at the old title (needs suppressredirect right):
    python _works_files/rename_owid_pages.py --apply --no-redirect

Credentials
-----------
Reads ``WIKI_USERNAME`` and ``WIKI_PASSWORD`` from ``.env`` at the repo root.
For Wikimedia projects you should generate a Bot Password at
https://commons.wikimedia.org/wiki/Special:BotPasswords and use the
``User@Botname`` form for ``WIKI_USERNAME``.

This script is intentionally NOT wired into the Flask app; run it as a
standalone command-line tool.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Iterable

import mwclient
import mwclient.errors
from dotenv import load_dotenv

logger = logging.getLogger("rename_owid_pages")

# (namespace_id, prefix_without_namespace, full_prefix_label_for_display)
PREFIXES: tuple[tuple[int, str, str], ...] = (
    (10, "OWID/", "Template:OWID/"),  # Template namespace
    (0, "OWID/", "OWID/"),  # Main namespace
)


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def load_credentials() -> tuple[str, str]:
    """Load ``WIKI_USERNAME`` and ``WIKI_PASSWORD`` from ``.env``."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.debug("Loaded environment from %s", env_path)
    else:
        logger.warning("No .env file at %s; relying on process environment", env_path)

    username = (os.getenv("WIKI_USERNAME") or "").strip()
    password = (os.getenv("WIKI_PASSWORD") or "").strip()

    if not username or not password:
        logger.error("WIKI_USERNAME and WIKI_PASSWORD must be set in .env or environment")
        sys.exit(2)
    return username, password


def build_site(host: str, user_agent: str, username: str, password: str) -> mwclient.Site:
    """Create an authenticated mwclient.Site using BotPassword/login."""
    logger.info("Connecting to %s as %s", host, username)
    site = mwclient.Site(host, scheme="https", clients_useragent=user_agent)
    site.login(username, password)
    logger.info("Logged in successfully")
    return site


def needs_rename(title: str, full_prefix: str) -> tuple[bool, str]:
    """Decide whether *title* needs a rename.

    Returns ``(needs_rename, new_title)``. Only the first character after
    ``full_prefix`` is changed; all other characters (including spaces /
    underscores and the rest of the path) are preserved as-is.
    """
    if not title.startswith(full_prefix):
        return False, title
    rest = title[len(full_prefix):]
    if not rest:
        return False, title
    first = rest[0]
    if first.isalpha() and first.islower():
        return True, full_prefix + first.upper() + rest[1:]
    return False, title


def iter_owid_pages(site: mwclient.Site, namespace: int, prefix: str) -> Iterable:
    """Yield non-redirect pages with the given prefix in *namespace*."""
    # filterredir='nonredirects' avoids picking up redirects that previous
    # runs of this script may have left behind.
    return site.allpages(prefix=prefix, namespace=namespace, filterredir="nonredirects")


def process(
    site: mwclient.Site,
    apply: bool,
    reason: str,
    move_talk: bool,
    no_redirect: bool,
) -> dict[str, int]:
    stats = {
        "checked": 0,
        "to_rename": 0,
        "renamed": 0,
        "skipped_exists": 0,
        "failed": 0,
    }

    for namespace, prefix, full_prefix in PREFIXES:
        logger.info("Listing pages with prefix %r (namespace %d)", full_prefix, namespace)
        ns_count = 0
        for page in iter_owid_pages(site, namespace, prefix):
            stats["checked"] += 1
            ns_count += 1
            title = page.name
            yes, new_title = needs_rename(title, full_prefix)
            if not yes:
                logger.debug("  ok: %s", title)
                continue

            stats["to_rename"] += 1
            logger.info("  RENAME: %s -> %s", title, new_title)
            if not apply:
                continue

            target = site.pages[new_title]
            if target.exists:
                logger.warning("  SKIP (target already exists): %s", new_title)
                stats["skipped_exists"] += 1
                continue

            try:
                page.move(
                    new_title,
                    reason=reason,
                    move_talk=move_talk,
                    no_redirect=no_redirect,
                )
                stats["renamed"] += 1
                logger.info("  MOVED: %s -> %s", title, new_title)
            except mwclient.errors.APIError as exc:
                stats["failed"] += 1
                logger.error(
                    "  FAILED (%s): %s -> %s : %s",
                    getattr(exc, "code", "?"),
                    title,
                    new_title,
                    getattr(exc, "info", exc),
                )
            except Exception as exc:  # pragma: no cover - safety net
                stats["failed"] += 1
                logger.exception("  FAILED: %s -> %s : %s", title, new_title, exc)

        logger.info("  scanned %d page(s) under %s", ns_count, full_prefix)

    return stats


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually perform the renames. Without this flag the script only lists candidates (dry-run).",
    )
    parser.add_argument(
        "--host",
        default="commons.wikimedia.org",
        help="MediaWiki host (default: commons.wikimedia.org)",
    )
    parser.add_argument(
        "--user-agent",
        default="OWID-Rename-Bot/1.0 (https://github.com/Mdwiki-TD/svg_translate_web)",
        help="User-Agent header (set per Wikimedia user-agent policy).",
    )
    parser.add_argument(
        "--reason",
        default="Capitalize first letter of OWID subpage name",
        help="Move reason / log summary on the wiki.",
    )
    parser.add_argument(
        "--no-redirect",
        action="store_true",
        help="Do not leave a redirect at the old title (needs the suppressredirect right).",
    )
    parser.add_argument(
        "--no-move-talk",
        action="store_true",
        help="Do not move the associated talk page.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose (debug) logging.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging(args.verbose)

    username, password = load_credentials()
    site = build_site(args.host, args.user_agent, username, password)

    if args.apply:
        logger.info("=== APPLY MODE: pages will be renamed on %s ===", args.host)
    else:
        logger.info("=== DRY-RUN MODE: no changes will be made (use --apply to rename) ===")

    stats = process(
        site,
        apply=args.apply,
        reason=args.reason,
        move_talk=not args.no_move_talk,
        no_redirect=args.no_redirect,
    )

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Pages checked      : {stats['checked']}")
    print(f"  Need rename        : {stats['to_rename']}")
    if args.apply:
        print(f"  Renamed            : {stats['renamed']}")
        print(f"  Skipped (exists)   : {stats['skipped_exists']}")
        print(f"  Failed             : {stats['failed']}")
    else:
        print("  (dry-run; rerun with --apply to perform the renames)")
    print("=" * 60)

    return 0 if stats.get("failed", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
