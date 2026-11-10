"""
Build and update the wikitext of original and cropped files.
"""

from __future__ import annotations

import logging
import re

import wikitextparser as wtp

from .insertion import BeforeMarkerInserter
from .other_versions import OtherVersionsUpdater

logger = logging.getLogger(__name__)


class InformationAuthorUpdater:
    """Sets the Author value of the first ``{{Information}}`` template."""

    @staticmethod
    def update_information_author(text: str, author_citation: str | None) -> str:
        """Replace the Author value in the first ``{{Information}}`` template.

        Args:
            text: The original file-description wikitext.
            author_citation: The complete attribution to set. Empty values leave the text unchanged.

        Returns:
            The modified wikitext, or the original text if no Information template exists.
        """
        if not author_citation:
            return text

        parsed = wtp.parse(text)
        for template in parsed.templates:
            if template.name.strip().lower() != "information":
                continue

            for argument in template.arguments:
                if argument.name.strip().lower() == "author":
                    if argument.value.strip().lower() == "our world in data":
                        argument.value = f" {author_citation}\n"
                        return parsed.string

                    if argument.value.strip() == author_citation:
                        return text

                    argument.value = f" {author_citation}\n"
                    return parsed.string

            template.set_arg("author", f" {author_citation}\n")
            return parsed.string

        return text


class OriginalFileTextUpdater:
    """Adds the ``{{Image extracted}}`` reference to the original file page."""

    TEMPLATE_NAME = "Image extracted"
    TEMPLATE_NAME_REGEX = r"(extracted ?(images?|file|photo)?|image ?extracted|cropped version)"

    def __init__(
        self,
        inserter: BeforeMarkerInserter | None = None,
        other_versions: OtherVersionsUpdater | None = None,
    ) -> None:
        self.inserter = inserter or BeforeMarkerInserter()
        self.other_versions = other_versions or OtherVersionsUpdater()

    @staticmethod
    def append_image_extracted_template(cropped_file_name: str, text: str) -> str:
        """If the page already has an extracted-image template, append the cropped file to it."""
        if cropped_file_name.lower() in text.replace("_", " ").lower():
            return text
        cropped_file_name = cropped_file_name.removeprefix("File:")
        match = re.search(
            r"{{\s*" + OriginalFileTextUpdater.TEMPLATE_NAME_REGEX + r"\s*(\s*|\|[^\}]+)}}",
            text,
            flags=re.I | re.M,
        )
        if not match:
            return text

        start, length = match.start(), match.end() - match.start()
        tpl_text = text[start : start + length]

        # Find out how many existing arguments there are
        arg_no = tpl_text.count("|") + 1

        # Append |N=name before the }} of the template
        return text[: start + length - 2] + f"|{arg_no}={cropped_file_name}" + text[start + length - 2 :]

    def update_original_file_text(self, file_name: str, text: str) -> str:
        """Update the original file's wikitext to include the cropped file information."""
        file_name = file_name.removeprefix("File:").replace("_", " ").strip()
        if file_name.lower() in text.replace("_", " ").lower():
            return text

        text_to_add = f"{{{{{self.TEMPLATE_NAME}|1={file_name}}}}}"

        modified_text = self.append_image_extracted_template(file_name, text)

        if modified_text == text:
            modified_text = self.other_versions.add_template(text, self.TEMPLATE_NAME, file_name)

        if modified_text == text:
            modified_text = self.inserter.insert_before_methods(text, text_to_add)

        return modified_text


class CroppedFileTextBuilder:
    """Builds the wikitext of a cropped file from the original file's wikitext."""

    TEMPLATE_NAME = "Extracted from"

    def __init__(
        self,
        inserter: BeforeMarkerInserter | None = None,
        author_updater: InformationAuthorUpdater | None = None,
        other_versions: OtherVersionsUpdater | None = None,
    ) -> None:
        self.inserter = inserter or BeforeMarkerInserter()
        self.author_updater = author_updater or InformationAuthorUpdater()
        self.other_versions = other_versions or OtherVersionsUpdater()

    def create_cropped_file_text(
        self,
        file_name: str,
        text: str,
        author_citation: str | None = None,
    ) -> str:
        """
        Create cropped-file wikitext and optionally enrich its Author attribution.

        Args:
            file_name: The name of the original file.
            text: The wikitext content of the original file.
            author_citation: A canonical upstream-source citation from OWID metadata.

        Returns:
            The wikitext content for the cropped file.
        """
        file_name = file_name.removeprefix("File:").replace("_", " ").strip()
        text_to_add = f"{{{{{self.TEMPLATE_NAME}|1={file_name}}}}}"

        if not text or not text.strip():
            return text_to_add

        # Add {{Extracted from|1=...}} to the "other versions" parameter of {{Information}}
        modified_text = self.other_versions.add_template(text, self.TEMPLATE_NAME, file_name)

        if modified_text == text:
            modified_text = self.inserter.insert_before_methods(text, text_to_add)

        if author_citation:
            modified_text = self.author_updater.update_information_author(modified_text, author_citation)
        return modified_text


__all__ = [
    "CroppedFileTextBuilder",
    "InformationAuthorUpdater",
    "OriginalFileTextUpdater",
]
