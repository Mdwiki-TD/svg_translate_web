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

    @staticmethod
    def generate_cropped_filename(filename: str) -> str:
        return generate_cropped_filename(filename)

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
