"""Tests for the wikitext module."""

from __future__ import annotations
from src.main_app.utils.wikitext import appendImageExtractedTemplate


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
