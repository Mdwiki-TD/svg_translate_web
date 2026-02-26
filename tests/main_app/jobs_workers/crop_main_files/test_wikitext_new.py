"""Tests for the wikitext module."""

from __future__ import annotations
from src.main_app.jobs_workers.crop_main_files.wikitext_new import appendImageExtractedTemplate
from src.main_app.utils.wikitext.wiki_text import WikiText


class TestAddOtherVersions:
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

        result = appendImageExtractedTemplate('My new file.jpg', oldText)
        assert result == newText

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

    def testItAddsTheImageExtractedTemplateToOtherVersions(self):
        oldText = '''
=={{int:filedesc}}==
{{Information
|description={{zh|1=北师大启功像1。}}
|date=2016-05-24 12:54:22
|source={{own}}
|author=[[User:三猎|三猎]]
|permission=
|other versions=
}}

=={{int:license-header}}==
{{self|cc-by-sa-4.0}}

[[Category:Beijing Normal University]]
[[Category:Qi Gong artist]]
[[Category:Busts in Beijing]]
[[Category:Bronze busts]]
[[Category:Uploaded with UploadWizard]]'''

        newText = '''
=={{int:filedesc}}==
{{Information
|description={{zh|1=北师大启功像1。}}
|date=2016-05-24 12:54:22
|source={{own}}
|author=[[User:三猎|三猎]]
|permission=
|other versions={{Image extracted|1=My new file.jpg}}
}}

=={{int:license-header}}==
{{self|cc-by-sa-4.0}}

[[Category:Beijing Normal University]]
[[Category:Qi Gong artist]]
[[Category:Busts in Beijing]]
[[Category:Bronze busts]]
[[Category:Uploaded with UploadWizard]]'''

        result = appendImageExtractedTemplate('My new file.jpg', oldText)
        assert result == newText

    def testItPreservesNewLines(self):
        oldText = '''
=={{int:filedesc}}==
{{Information
|Source={{own}}
|Date={{According to EXIF data|2009-02-09}}
|Permission={{OTRS|2010080710005378}}
|other_versions=
}}

[[Category:A]]
[[Category:Images with borders]]
[[Category:B]]
'''
        newText = '''
=={{int:filedesc}}==
{{Information
|Source={{own}}
|Date={{According to EXIF data|2009-02-09}}
|Permission=
|other_versions={{Image extracted|1=My new file.jpg}}
}}

[[Category:A]]
[[Category:B]]
'''

        result = WikiText.make(oldText) \
            .withoutTemplatesNotToBeCopied() \
            .appendImageExtractedTemplate('My new file.jpg') \
            .withoutBorderTemplate()

        assert result == newText

        # $wikitext = $wikitext->withoutBorderTemplate();
        # $wikitext = $wikitext->withoutTrimmingTemplate();
        # $wikitext = $wikitext->withoutWatermarkTemplate();

        # // Remove templates before appending {{Extracted from}}
        # $wikitext = $wikitext->withoutTemplatesNotToBeCopied();

        # $wikitext = $wikitext->withoutCropForWikidataTemplate();
