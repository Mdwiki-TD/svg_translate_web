from typing import Any

from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField
from wtforms.validators import DataRequired, Optional


def strip_filter(value: str | None) -> str:
    if value is not None:
        return value.strip()
    return value


class CopySvgLangsForm(FlaskForm):
    # Template title field: required with a default value
    title = StringField(
        "Template Title",
        validators=[DataRequired(message="This field is required.")],
        filters=[strip_filter],
        default="Template:OWID/Death rate from obesity",
    )

    # Optional field for the oldest file title
    manual_main_title = StringField(
        "Manual Oldest File Title (optional)", validators=[Optional()], render_kw={"placeholder": "File:Example.svg"}
    )

    # Toggle switches (Default set to True to be checked by default)
    overwrite_translations = BooleanField("Overwrite Existing translations", default=True)

    upload = BooleanField("Upload Files", default=True)

    overwrite_download = BooleanField("Overwrite existing files when download", default=True)

    submit = SubmitField("Start")

def setup_svg_langs_form(all_settings: dict[str, Any] | None = None) -> CopySvgLangsForm:
    form = CopySvgLangsForm()
    # set upload default dynamically only on GET (first load)
    upload_disabled_by_default = bool(
        all_settings and all_settings.get("copy_svg_langs_upload_disabled_by_default", False)
    )
    form.upload.data = not upload_disabled_by_default
    return form



__all__ = [
    "CopySvgLangsForm",
    "setup_svg_langs_form",
]
