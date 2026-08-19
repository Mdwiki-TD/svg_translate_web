from __future__ import annotations

from src.main_app.api_services.files_service.exceptions import SharedFileExistsError


class TestSharedFileExistsError:
    def test_existing_file_name(self):
        error = SharedFileExistsError(
            "A file with this name already exists in the shared file repository. If you still want to upload your file, please go back and use a new name. [[File:Share_of_deaths_obesity,_AFG.svg|thumb|center|Share_of_deaths_obesity,_AFG.svg]]",
        )
        assert error.existing_file_name == "File:Share_of_deaths_obesity,_AFG.svg"
