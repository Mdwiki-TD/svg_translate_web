"""Tests for the wikitext module."""

from __future__ import annotations
from src.main_app.jobs_workers.crop_main_files.wikitext import appendImageExtractedTemplate, update_original_file_text


class TestAddOtherVersions:
    """Tests for the add_other_versions function."""

    def testItAppendsToExistingImageExtractedTemplate(self):
        oldText1 = '''
{{Information
|description={{zh|1=北师大启功像1。}}
|other_versions={{Image extracted|HoryujiYumedono0363 edit1.jpg}}
}}

{{PD-self}}
'''

        newText1 = '''
{{Information
|description={{zh|1=北师大启功像1。}}
|other_versions={{Image extracted|HoryujiYumedono0363 edit1.jpg|2=My new file.jpg}}
}}

{{PD-self}}
'''

        oldText2 = '''
{{Information
|description={{zh|1=北师大启功像1。}}
|other_versions={{Image extracted|HoryujiYumedono0363 edit1.jpg|Crop 1.jpg}}
}}

{{PD-self}}
'''

        newText2 = '''
{{Information
|description={{zh|1=北师大启功像1。}}
|other_versions={{Image extracted|HoryujiYumedono0363 edit1.jpg|Crop 1.jpg|3=My new file.jpg}}
}}

{{PD-self}}
'''

        result1 = appendImageExtractedTemplate('My new file.jpg', oldText1)
        assert result1 == newText1

        result2 = appendImageExtractedTemplate('My new file.jpg', oldText2)
        assert result2 == newText2


class TestUpdate_original_file_text:
    """Tests for the add_other_versions function."""

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
