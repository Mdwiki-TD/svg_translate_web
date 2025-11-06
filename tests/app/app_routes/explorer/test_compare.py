"""
Tests for SVG comparison functions.
"""
from pathlib import Path
import tempfile
from lxml import etree

from src.app.app_routes.explorer.compare import file_langs, analyze_file, compare_svg_files


def create_test_svg(content: str) -> Path:
    """Create a temporary SVG file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write(content)
        return Path(f.name)


def test_file_langs_empty_svg():
    """
    Tests that file_langs returns ['en'] for an empty SVG.
    """
    svg_content = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    svg_path = create_test_svg(svg_content)
    assert file_langs(svg_path) == ['en']
    svg_path.unlink()


def test_file_langs_with_languages():
    """
    Tests that file_langs extracts languages correctly.
    """
    svg_content = '''
    <svg xmlns="http://www.w3.org/2000/svg">
        <text systemLanguage="fr">Bonjour</text>
        <text systemLanguage="es">Hola</text>
    </svg>
    '''
    svg_path = create_test_svg(svg_content)
    langs = file_langs(svg_path)
    assert 'en' in langs
    assert 'fr' in langs
    assert 'es' in langs
    svg_path.unlink()


def test_file_langs_malformed_svg():
    """
    Tests that file_langs handles malformed SVGs.
    """
    svg_content = '<svg><text></svg>'
    svg_path = create_test_svg(svg_content)
    assert file_langs(svg_path) == ['en']
    svg_path.unlink()


def test_analyze_file():
    """
    Tests the analyze_file function.
    """
    svg_content = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    svg_path = create_test_svg(svg_content)
    result = analyze_file(svg_path)
    assert result['languages'] == ['en']
    svg_path.unlink()


def test_compare_svg_files():
    """
    Tests the compare_svg_files function.
    """
    svg_content1 = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    svg_path1 = create_test_svg(svg_content1)
    svg_content2 = '<svg xmlns="http://www.w3.org/2000/svg"><text systemLanguage="fr"></text></svg>'
    svg_path2 = create_test_svg(svg_content2)

    results = compare_svg_files(svg_path1, svg_path2)
    assert len(results) == 2
    assert results[0]['languages'] == ['en']
    assert 'en' in results[1]['languages']
    assert 'fr' in results[1]['languages']

    svg_path1.unlink()
    svg_path2.unlink()
