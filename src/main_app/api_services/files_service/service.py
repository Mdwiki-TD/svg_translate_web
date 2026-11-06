import logging
from pathlib import Path
from urllib.parse import quote

import requests

from ..clients.http_client import HttpClient
from .objects import (
    DownloadAndSaveData,
    FileInfo,
    FileLanguagesMap,
)


from ..clients import CommonsSession, GetWithRetryData
from .save_file import write_bytes_to_file

logger = logging.getLogger(__name__)

BASE_COMMONS_URL = "https://commons.wikimedia.org/wiki/Special:FilePath/"


ALL_II_PROPS = [
    "timestamp",
    "user",
    "metadata",
    "mediatype",
    "userid",
    "url",
    "uploadwarning",
    "thumburls",
    "thumbmime",
    "size",
    "sha1",
    "parsedcomment",
    "mime",
    "extmetadata",
    "commonmetadata",
    "dimensions",
    "comment",
    "canonicaltitle",
    "bitdepth",
    "archivename",
    "badfile",
]


class FilesService:
    def __init__(
        self,
        http_client: HttpClient | None = None,
    ) -> None:
        self.http_client = http_client or HttpClient(use_session=True)
        self.downloader = CommonsSession(
            http_client=self.http_client,
            timeout=30,
        )

    def get_file_info(
        self,
        prefixed_file_name: str,
        *,
        iiprops: list[str] | None = None,
    ) -> FileInfo:
        """
        Get file info from Commons API.
        """
        if iiprops:
            iiprops = [p for p in iiprops if p in ALL_II_PROPS]
        else:
            iiprops = ["metadata"]

        if not prefixed_file_name:
            return FileInfo(error="No file name provided")

        # Define API endpoint and parameters
        url = "https://commons.wikimedia.org/w/api.php"

        params = {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "titles": prefixed_file_name,
            "formatversion": "2",
            "iiprop": "|".join(iiprops),
        }

        try:
            response = self.http_client.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as err:
            logger.exception("Commons API request failed for %s", prefixed_file_name)
            return FileInfo(error=f"API error: {err}")

        # { "batchcomplete": true, "query": { "pages": [ { "ns": 6, "title": "File:34", "missing": true, "imagerepository": "" } ] } }

        pages = data.get("query", {}).get("pages", [])
        if not pages:
            return FileInfo(error="Unexpected API response")

        page = pages[0]

        # Check if file exists
        if page.get("missing") and not page.get("known"):
            return FileInfo(error=f"File {page.get('title', prefixed_file_name)} does not exist.", exists=False)

        # Extract imageinfo array
        imageinfo = page.get("imageinfo", [])
        if not imageinfo:
            return FileInfo(error=f"imageinfo not found for {page.get('title')}", exists=True)

        return FileInfo(error=None, imageinfo=imageinfo, exists=True)

    def get_file_languages(self, file_name: str) -> FileLanguagesMap:
        """
        Extract available SVG translation languages for a given Commons file.

        Args:
            file_name: Name of the file on Wikimedia Commons.

        Returns:
            A `FileLanguagesMap` instance with `error` (if any) and `langs` list.
        To mirror:
            https://svgtranslate.toolforge.org/api/languages/File:Parkinsons_disease_prevalence_ihme,_Africa,_2021.svg
        """
        if not file_name:
            return FileLanguagesMap(error="Empty fileName")

        # Normalize file name by stripping leading "File:" prefix
        file_name = file_name.strip()
        normalized_name = file_name[5:] if file_name.lower().startswith("file:") else file_name
        prefixed_file_name = f"File:{normalized_name}"

        file_info = self.get_file_info(prefixed_file_name)
        # check if image exists
        if file_info.exists is False:
            return FileLanguagesMap(error="File does not exist")

        # Extract metadata array
        imageinfo = file_info.imageinfo
        if not imageinfo:
            return FileLanguagesMap(
                error=f"Metadata not found for {prefixed_file_name}. Error: {file_info.error}",
            )

        # metadata shema: [ { "name": "version", "value": 2 }, ... , { "name": "translations", "value": []} ]
        metadata = imageinfo[0].get("metadata", [])
        if not metadata:
            return FileLanguagesMap(error=f"Metadata array empty for {prefixed_file_name}")

        translations: list[object] = []
        for entry in metadata:
            if isinstance(entry, dict) and entry.get("name") == "translations":
                value = entry.get("value")
                translations = value if isinstance(value, list) else []
                break

        # translations shema: [ { "name": "abr", "value": 2 }, { "name": "ar", "value": 2 }, ... ]
        if isinstance(translations, list) and len(translations) > 0:
            # Extract language codes from translation entries
            langs_keys = [t["name"] for t in translations if isinstance(t, dict) and "name" in t]
            if "en" not in langs_keys:
                langs_keys.append("en")
            return FileLanguagesMap(langs=langs_keys)

        return FileLanguagesMap(langs=["en"])

    # ----------------------
    #  download methods
    # ----------------------

    def download_and_save(
        self,
        *,
        title: str,
        out_dir: Path,
        overwrite_download: bool = True,
    ) -> DownloadAndSaveData:
        """
        Download a single Commons file, skipping already-downloaded copies.

        Parameters:
            title (str): Title of the file page on Wikimedia Commons.
            out_dir (Path): Directory where the file should be stored.
            overwrite_download (bool): Whether to overwrite existing files.
        """

        if not title:
            return DownloadAndSaveData(result="failed", error="Empty title provided")

        clean_title = title.removeprefix("File:")
        out_path = out_dir / clean_title

        if out_path.exists() and not overwrite_download:
            logger.debug(f"Skipped existing: {title}")
            return DownloadAndSaveData(
                result="existing",
                error="Skip existing file, no overwrite",
                path=str(out_path),
            )

        # Use the core download function with shorter timeout
        try:
            normalized_name = title.replace(" ", "_")
            url = f"{BASE_COMMONS_URL}{quote(normalized_name)}"

            download_result: GetWithRetryData = self.downloader.get_with_retry_obj(url=url, max_attempts=5)

        except Exception as e:
            logger.error(f"Failed: {title} -> {e}")
            return DownloadAndSaveData(result="failed")

        if download_result.status_code != 200:
            logger.error(f"Failed: {title} -> {download_result.status_code}")
            return DownloadAndSaveData(result="failed", error=download_result.msg)

        content = download_result.content
        if content is None:
            logger.error(f"Failed: {title} -> No content")
            return DownloadAndSaveData(result="failed", error=download_result.msg)

        size_bytes = len(content)

        # save part
        saved = write_bytes_to_file(content=content, filename=title, output_dir=out_dir)
        if saved.success:
            return DownloadAndSaveData(result="success", path=str(saved.path), size_bytes=size_bytes)
        else:
            msg = f"Failed to save file: {saved.error}"
            return DownloadAndSaveData(result="failed", error=msg, size_bytes=size_bytes)


__all__ = [
    "FilesService",
]
