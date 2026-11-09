""" """

from pathlib import Path
from typing import Any

from .crop_file import crop_svg_file
from .crop_utils import generate_cropped_filename
from .download import download_file_for_cropping
from .upload import upload_cropped_file


class CropMainFilesSteps:
    @staticmethod
    def upload_cropped_file(
        cropped_filename: str,
        cropped_path: Path,
        site: Any | None,
        wikitext: str | None = None,
    ) -> dict[str, Any]:
        return upload_cropped_file(
            cropped_filename=cropped_filename,
            cropped_path=cropped_path,
            site=site,
            wikitext=wikitext,
        )

    @staticmethod
    def download_file_for_cropping(
        filename: str,
        output_dir: Path,
        files_service: Any | None = None,
    ) -> dict[str, Any]:
        return download_file_for_cropping(
            filename=filename,
            output_dir=output_dir,
            files_service=files_service,
        )

    # @cached_property
    @staticmethod
    def generate_cropped_filename(filename: str) -> str:
        """
        Transform filename to cropped version.

        Examples:
            "File:Death rate from obesity, World, 2021.svg"
            → "File:Death rate from obesity, World, 2021 (cropped).svg"
        """
        if filename.startswith("File:"):
            base_name = filename[5:]
        else:
            base_name = filename

        path = Path(base_name)
        new_stem = f"{path.stem} (cropped)"
        new_filename = new_stem + path.suffix
        return f"File:{new_filename}"

    @staticmethod
    def crop_svg_file(
        file_path: Path,
        cropped_output_path: Path,
    ) -> dict[str, Any]:
        return crop_svg_file(
            file_path=file_path,
            cropped_output_path=cropped_output_path,
        )


__all__ = [
    "CropMainFilesSteps",
    "generate_cropped_filename",
    "download_file_for_cropping",
    "upload_cropped_file",
    "crop_svg_file",
]
