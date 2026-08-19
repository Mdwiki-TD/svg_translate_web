import re
from typing import Any

# Matches the [[File:Name.svg|...]] (or [[Image:Name.svg|...]]) link embedded in
# the `info` string of a `fileexists-shared-forbidden` API error.
_SHARED_FILE_LINK_RE = re.compile(r"\[\[\s*(?:File|Image)\s*:\s*([^\]|]+)")


class SharedFileExistsError(Exception):
    """Raised when an upload is rejected because the file name already exists
    in the shared file repository (``fileexists-shared-forbidden``).

    The MediaWiki API embeds the conflicting file name inside a wikilink in the
    error ``info`` text, e.g.::

        A file with this name already exists in the shared file repository.
        If you still want to upload your file, please go back and use a new name.
        [[File:Share_of_deaths_obesity,_AFG.svg|thumb|center|Share_of_deaths_obesity,_AFG.svg]]

    This exception parses that link to expose the conflicting file name so callers
    can suggest or generate a new name.

    API result:
    {
        "code": "fileexists-shared-forbidden",
        "info": "A file with this name already exists in the shared file repository. If you still want to upload your file, please go back and use a new name. [[File:Share_of_deaths_obesity,_AFG.svg|thumb|center|Share_of_deaths_obesity,_AFG.svg]]",
    }
    """

    def __init__(self, code: str, info: str) -> None:
        super().__init__(info)
        self.code = code
        self.info = info
        self.existing_file_name: str | None = self._extract_file_name(info)

    @staticmethod
    def _extract_file_name(info: str) -> str | None:
        match = _SHARED_FILE_LINK_RE.search(info)
        if not match:
            return None
        # Strip the leading "File:"/"Image:" prefix and surrounding whitespace.
        name = match.group(1).strip()
        if name.lower().startswith(("file:", "image:")):
            name = name.split(":", 1)[1].strip()
        return name or None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "info": self.info,
            "existing_file_name": self.existing_file_name,
        }


__all__ = [
    "SharedFileExistsError",
]
