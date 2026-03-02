"""Tests for the wikitext module."""

from __future__ import annotations

from src.main_app.utils.wikitext import update_original_file_text


class TestUpdate_original_file_text:
    """Tests for the update_original_file_text function."""

    def testItAddsImageExtractedTemplateToOtherVersions2(self):
        oldText = """
== {{int:filedesc}} ==

{{Information
 |description = '''English:'''<br>
Algoma Steel<br>
photo taken from Wallace Terrace<br>
[[Sault Ste. Marie, Ontario|Sault Ste. Marie]], [[Ontario]], [[Canada]]<br>
30 June, 2006.
'''Français:'''<br>
l'Aciérie d'Algoma<br>
photographié à terrasse Wallace ÆØÅ<br>
Sault-S<sup>te</sup>-Marie, Ontario, Canada<br>
30 juin, 2006
 |date = {{According to EXIF data|2006-07-30}}
 |source = {{own assumed}}
 |author = {{Author assumed|[[User:Fungus Guy|Fungus Guy]]}}
 |permission =
 |other_versions =
}}

== {{int:license-header}} ==
{{Self|PD-self|author=Fungus Guy}}

[[Category:Essar Steel Algoma]]"""

        newText = """
== {{int:filedesc}} ==

{{Information
 |description = '''English:'''<br>
Algoma Steel<br>
photo taken from Wallace Terrace<br>
[[Sault Ste. Marie, Ontario|Sault Ste. Marie]], [[Ontario]], [[Canada]]<br>
30 June, 2006.
'''Français:'''<br>
l'Aciérie d'Algoma<br>
photographié à terrasse Wallace ÆØÅ<br>
Sault-S<sup>te</sup>-Marie, Ontario, Canada<br>
30 juin, 2006
 |date = {{According to EXIF data|2006-07-30}}
 |source = {{own assumed}}
 |author = {{Author assumed|[[User:Fungus Guy|Fungus Guy]]}}
 |permission =
 |other_versions ={{Image extracted|1=My new file.jpg}}
}}

== {{int:license-header}} ==
{{Self|PD-self|author=Fungus Guy}}

[[Category:Essar Steel Algoma]]"""

        result = update_original_file_text('My new file.jpg', oldText)
        assert result == newText

    def testnotduplicateinsert(self):
        oldText = """
        == {{int:filedesc}} ==

        {{Information
        |source = https://ourworldindata.org/grapher/share-with-drug-use-disorders
        |permission = "License: All of Our World in Data is completely open access and all work is licensed under the Creative Commons BY license. You have the permission to use, distribute, and reproduce in any medium, provided the source and authors are credited."
        |other versions ={{Image extracted|1=Share-with-drug-use-disorders,World,2021 (cropped).svg}}
        }}"""

        result = update_original_file_text('File:Share-with-drug-use-disorders,World,2021_(cropped).svg', oldText)
        assert result == oldText


class TestUpdate_original_file_text_extensive:
    """
    Full-coverage tests for update_original_file_text.

    The function follows this priority chain:
      1. Filename already in text        -> return unchanged (no-op)
      2. {{Image extracted|...}} exists  -> append to it
      3. {{Information}} exists          -> add/update |other_versions parameter
      4. License-header section exists   -> insert {{Image extracted}} before it
      5. [[Category:...]] exists         -> insert {{Image extracted}} before it
      6. None of the above               -> return unchanged
    Additional normalisation:
      - "File:" prefix is stripped before comparison / insertion
      - Underscores "_" are converted to spaces " "
    """

    # ------------------------------------------------------------------
    # Path 1 – filename already present in the text → no-op
    # ------------------------------------------------------------------

    def test_returns_unchanged_when_filename_already_present(self):
        """Text already contains the exact filename – must not be modified."""
        text = """{{Information
|other_versions={{Image extracted|1=My cropped file.jpg}}
}}"""
        result = update_original_file_text("My cropped file.jpg", text)
        assert result == text

    def test_returns_unchanged_when_filename_with_file_prefix_already_present(self):
        """'File:' prefix is stripped before the duplicate check."""
        text = """{{Information
|other_versions={{Image extracted|1=My cropped file.jpg}}
}}"""
        result = update_original_file_text("File:My cropped file.jpg", text)
        assert result == text

    def test_returns_unchanged_when_filename_with_underscores_already_present(self):
        """Underscores in the input are normalised to spaces for the duplicate check."""
        text = """{{Information
|other_versions={{Image extracted|1=Share-with-drug-use-disorders,World,2021 (cropped).svg}}
}}"""
        result = update_original_file_text(
            "File:Share-with-drug-use-disorders,World,2021_(cropped).svg", text
        )
        assert result == text

    def test_no_duplicate_insert_when_already_in_other_versions(self):
        """Regression: cropped filename already inside |other versions| – no duplication."""
        old_text = """
        == {{int:filedesc}} ==

        {{Information
        |source = https://ourworldindata.org/grapher/share-with-drug-use-disorders
        |permission = "License: All of Our World in Data..."
        |other versions ={{Image extracted|1=Share-with-drug-use-disorders,World,2021 (cropped).svg}}
        }}"""

        result = update_original_file_text(
            "File:Share-with-drug-use-disorders,World,2021_(cropped).svg", old_text
        )
        assert result == old_text

    # ------------------------------------------------------------------
    # Path 2 – {{Image extracted|...}} already present → append to it
    # ------------------------------------------------------------------

    def test_appends_to_existing_image_extracted_with_one_arg(self):
        """When Image extracted has one positional arg, the new file becomes |2=..."""
        old_text = """{{Information
|description=Some desc
|other_versions={{Image extracted|Existing crop.jpg}}
}}"""
        result = update_original_file_text("New crop.jpg", old_text)
        assert "{{Image extracted|Existing crop.jpg|2=New crop.jpg}}" in result

    def test_appends_to_existing_image_extracted_with_two_args(self):
        """When Image extracted already has two args, the new file becomes |3=..."""
        old_text = """{{Information
|description=Some desc
|other_versions={{Image extracted|First.jpg|Second.jpg}}
}}"""
        result = update_original_file_text("Third.jpg", old_text)
        assert "{{Image extracted|First.jpg|Second.jpg|3=Third.jpg}}" in result

    def test_appends_to_extracted_images_template_variant(self):
        """Template aliases like 'Extracted images' are also recognised."""
        old_text = """{{Information
|other_versions={{Extracted images|Foo.jpg}}
}}"""
        result = update_original_file_text("Bar.jpg", old_text)
        assert "Bar.jpg" in result
        assert old_text != result

    def test_file_prefix_stripped_when_appending_to_image_extracted(self):
        """'File:' prefix must be stripped from the filename before appending."""
        old_text = """{{Information
|other_versions={{Image extracted|Existing.jpg}}
}}"""
        result = update_original_file_text("File:New crop.jpg", old_text)
        assert "New crop.jpg" in result
        assert "File:New crop.jpg" not in result

    # ------------------------------------------------------------------
    # Path 3a – {{Information}} has an existing |other_versions| param
    #           (but no Image extracted template inside) → update param value
    # ------------------------------------------------------------------

    def test_adds_image_extracted_to_empty_other_versions_param(self):
        """Empty |other_versions = | inside {{Information}} gets the new template."""
        old_text = """
== {{int:filedesc}} ==

{{Information
 |description = Some description
 |date = 2006-07-30
 |source = {{own assumed}}
 |author = Some Author
 |permission =
 |other_versions =
}}

== {{int:license-header}} ==
{{Self|PD-self|author=Some Author}}

[[Category:Some Category]]"""

        result = update_original_file_text("My new file.jpg", old_text)
        assert "{{Image extracted|1=My new file.jpg}}" in result
        # Other parameters must remain intact
        assert "|description = Some description" in result
        assert "|author = Some Author" in result

    def test_appends_to_non_empty_other_versions_without_image_extracted(self):
        """Non-empty |other_versions| without Image extracted gets the template appended."""
        old_text = """{{Information
|description=Some desc
|other_versions=[[File:Related.jpg|thumb]]
}}"""
        result = update_original_file_text("New crop.jpg", old_text)
        assert "{{Image extracted|1=New crop.jpg}}" in result

    # ------------------------------------------------------------------
    # Path 3b – {{Information}} exists but has NO |other_versions| param
    # ------------------------------------------------------------------

    def test_creates_other_versions_param_when_information_has_none(self):
        """{{Information}} without any |other_versions| gets the param added."""
        old_text = """{{Information
|description={{en|1=Some description}}
|author=Test Author
|date=2022
|source=https://example.com
|permission=CC-BY
}}"""
        result = update_original_file_text("New crop.jpg", old_text)
        assert "{{Image extracted|1=New crop.jpg}}" in result
        assert result != old_text

    # ------------------------------------------------------------------
    # Path 4 – no {{Information}}, but license header present
    # ------------------------------------------------------------------

    def test_inserts_before_license_header_when_no_information_template(self):
        """Without {{Information}}, the template is inserted before the license header."""
        old_text = """{{PD-old-70}}

== {{int:license-header}} ==
{{PD-old-70-1923}}

[[Category:Old photos]]"""

        result = update_original_file_text("New crop.jpg", old_text)
        assert "{{Image extracted|1=New crop.jpg}}" in result
        license_pos = result.index("{{int:license-header}}")
        inserted_pos = result.index("{{Image extracted|1=New crop.jpg}}")
        assert inserted_pos < license_pos

    def test_license_header_match_is_case_insensitive(self):
        """License-header section marker is matched case-insensitively."""
        old_text = """== {{int:License-Header}} ==
{{PD-self}}"""
        result = update_original_file_text("New crop.jpg", old_text)
        assert "{{Image extracted|1=New crop.jpg}}" in result

    # ------------------------------------------------------------------
    # Path 5 – no {{Information}}, no license header, but [[Category:…]]
    # ------------------------------------------------------------------

    def test_inserts_before_category_when_no_information_and_no_license_header(self):
        """Without {{Information}} or license header, inserts before [[Category:...]]."""
        old_text = """Some plain description text.

[[Category:Photographs]]"""

        result = update_original_file_text("New crop.jpg", old_text)
        assert "{{Image extracted|1=New crop.jpg}}" in result
        cat_pos = result.index("[[Category:")
        inserted_pos = result.index("{{Image extracted|1=New crop.jpg}}")
        assert inserted_pos < cat_pos

    def test_category_match_is_case_insensitive(self):
        """Category link is matched case-insensitively."""
        old_text = """Some text.

[[category:Photographs]]"""
        result = update_original_file_text("New crop.jpg", old_text)
        assert "{{Image extracted|1=New crop.jpg}}" in result

    # ------------------------------------------------------------------
    # Path 6 – nothing matches → return unchanged
    # ------------------------------------------------------------------

    def test_returns_unchanged_when_no_anchor_found(self):
        """Text with no {{Information}}, no license header, no category → unchanged."""
        old_text = "Just a plain text without any wiki markup."
        result = update_original_file_text("New crop.jpg", old_text)
        assert result == old_text

    def test_returns_unchanged_for_empty_string(self):
        """Empty input string is returned unchanged."""
        result = update_original_file_text("New crop.jpg", "")
        assert result == ""

    # ------------------------------------------------------------------
    # Normalisation edge cases
    # ------------------------------------------------------------------

    def test_underscores_in_filename_are_converted_to_spaces(self):
        """Underscores in the input filename are replaced with spaces in the output."""
        old_text = """{{Information
|description=Some desc
|other_versions=
}}"""
        result = update_original_file_text("My_new_file.jpg", old_text)
        assert "My new file.jpg" in result
        assert "My_new_file.jpg" not in result

    def test_file_prefix_stripped_in_output(self):
        """'File:' prefix must not appear in the inserted template text."""
        old_text = """{{Information
|description=Some desc
|other_versions=
}}"""
        result = update_original_file_text("File:New crop.jpg", old_text)
        assert "{{Image extracted|1=New crop.jpg}}" in result
        assert "File:New crop.jpg" not in result

    def test_file_prefix_and_underscores_together(self):
        """Both normalisation rules apply simultaneously."""
        old_text = """{{Information
|description=Some desc
|other_versions=
}}"""
        result = update_original_file_text("File:My_new_crop.jpg", old_text)
        # Filename must appear without the File: prefix and without underscores
        assert "{{Image extracted|1=My new crop.jpg}}" in result
        assert "File:My_new_crop.jpg" not in result
        assert "My_new_crop.jpg" not in result
