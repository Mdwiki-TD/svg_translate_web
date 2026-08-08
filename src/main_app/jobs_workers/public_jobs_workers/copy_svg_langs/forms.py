from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField
from wtforms.validators import DataRequired, Optional


def strip_filter(value):
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
