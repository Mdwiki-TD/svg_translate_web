import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Optional

import requests

output_dir = Path(__file__).parent / "owid_metadata"
json_sitemap = Path(__file__).parent / "sitemap.json"

# Create the output directory if it doesn't exist
if not output_dir.exists():
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {output_dir}")


def download_owid_grapher_metadata(limit: Optional[int] = None) -> None:
    """
    Downloads grapher metadata from Our World in Data sitemap.
    :param limit: Maximum number of files to download (set to None for all)
    """
    sitemap_url = "https://ourworldindata.org/sitemap.xml"
    print(f"Fetching sitemap from {sitemap_url}...")
    try:
        response = requests.get(sitemap_url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching sitemap: {e}")
        return

    # Parse XML content
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        print(f"Error parsing XML sitemap: {e}")
        return

    # Define XML namespaces used in standard sitemaps
    namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    # Extract all <loc> tags
    loc_elements = root.findall(".//ns:loc", namespaces)
    if not loc_elements:
        # Fallback if no namespace is matched
        loc_elements = root.findall(".//loc")

    print(f"Found {len(loc_elements)} total URLs in sitemap.")

    # Filter only grapher URLs
    grapher_urls: list[Any] = []
    for loc in loc_elements:
        url = loc.text.strip() if loc.text else ""
        if "/grapher/" in url:
            grapher_urls.append(url)

    print(f"Filtered {len(grapher_urls)} 'grapher' URLs.")

    with open(json_sitemap, "w", encoding="utf-8") as f:
        json.dump(grapher_urls, f, ensure_ascii=False, indent=4)

    # Process and download metadata
    count = 0
    for url in grapher_urls:
        if limit and count >= limit:
            print(f"\nReached the specified limit of {limit} downloads. Stopping.")
            break

        # Extract the slug from URL
        # e.g., https://ourworldindata.org/grapher/road-deaths-over-the-long-term -> road-deaths-over-the-long-term
        slug = url.split("/grapher/")[-1].strip("/")

        if not slug:
            continue

        metadata_url = f"https://ourworldindata.org/grapher/{slug}.metadata.json"
        print(f"[{count + 1}] Fetching metadata for slug: {slug}")

        try:
            meta_res = requests.get(metadata_url, timeout=15)
            if meta_res.status_code == 200:
                # Construct file path using pathlib and write JSON content
                file_path = output_dir / f"{slug}.metadata.json"
                file_path.write_text(meta_res.text, encoding="utf-8")
                count += 1

                # Polite delay to prevent overwhelming the server
                time.sleep(0.5)
            elif meta_res.status_code == 404:
                print(f"  <- Metadata not found (404) for: {slug}")
            else:
                print(f"  <- Failed to fetch metadata (Status: {meta_res.status_code})")
        except requests.RequestException as e:
            print(f"  <- Connection error for {slug}: {e}")

    print(f"\nProcess completed! Successfully saved {count} files to '{output_dir}' directory.")


if __name__ == "__main__":
    # Change limit to None to download all available files without restriction
    download_owid_grapher_metadata(limit=10)
