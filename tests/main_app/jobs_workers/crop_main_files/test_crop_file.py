"""Unit tests for crop_main_files.crop_file module."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from unittest.mock import patch

from src.main_app.jobs_workers.crop_main_files import crop_file


def create_test_svg(include_footer: bool = True) -> str:
    """Create a test SVG string with optional footer."""
    svg_content = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">',
        '  <rect x="10" y="10" width="100" height="100" fill="red" />',
        '  <circle cx="200" cy="150" r="50" fill="blue" />',
    ]
    if include_footer:
        svg_content.append('  <g id="footer">')
        svg_content.append('    <rect x="0" y="500" width="800" height="100" fill="gray" />')
        svg_content.append('    <text x="400" y="550">Footer Text</text>')
        svg_content.append("  </g>")
    svg_content.append("</svg>")
    return "\n".join(svg_content)


def test_get_max_y_of_element_with_rect():
    """Test getting max y value from a rect element."""
    svg = '<rect x="10" y="20" width="50" height="30" />'
    element = ET.fromstring(svg)

    max_y = crop_file.get_max_y_of_element(element)

    assert max_y == 50.0  # y(20) + height(30)


def test_get_max_y_of_element_with_circle():
    """Test getting max y value from a circle element."""
    svg = '<circle cx="100" cy="150" r="25" />'
    element = ET.fromstring(svg)

    max_y = crop_file.get_max_y_of_element(element)

    assert max_y == 150.0  # cy value


def test_get_max_y_of_element_with_no_y_attrs():
    """Test getting max y value from element with no y attributes."""
    svg = '<rect x="10" width="50" height="30" />'
    element = ET.fromstring(svg)

    max_y = crop_file.get_max_y_of_element(element)

    assert max_y == 0.0


def test_get_max_y_of_element_with_units():
    """Test getting max y value from element with units like 'px'."""
    svg = '<rect x="10" y="20px" width="50" height="30px" />'
    element = ET.fromstring(svg)

    max_y = crop_file.get_max_y_of_element(element)

    assert max_y == 50.0  # Should strip 'px' and calculate correctly


def test_get_max_y_of_element_with_invalid_values():
    """Test getting max y value from element with invalid attribute values."""
    svg = '<rect x="10" y="invalid" width="50" height="abc" />'
    element = ET.fromstring(svg)

    max_y = crop_file.get_max_y_of_element(element)

    assert max_y == 0.0  # Should handle invalid values gracefully


def test_get_max_y_of_element_with_negative_values():
    """Test getting max y value with negative coordinates."""
    svg = '<rect x="10" y="-20" width="50" height="30" />'
    element = ET.fromstring(svg)

    max_y = crop_file.get_max_y_of_element(element)

    assert max_y == 10.0  # y(-20) + height(30)


def test_remove_footer_and_adjust_height_success(tmp_path):
    """Test successfully removing footer and adjusting height."""
    input_path = tmp_path / "input.svg"
    output_path = tmp_path / "output.svg"
    input_path.write_text(create_test_svg(include_footer=True))

    result = crop_file.remove_footer_and_adjust_height(str(input_path), str(output_path))

    assert result is True
    assert output_path.exists()

    # Parse output and verify footer is gone
    tree = ET.parse(output_path)
    root = tree.getroot()

    # Check that footer is removed
    footer_elements = [elem for elem in root.iter() if elem.get("id") == "footer"]
    assert len(footer_elements) == 0


def test_remove_footer_and_adjust_height_updates_viewbox(tmp_path):
    """Test that viewBox is updated correctly."""
    input_path = tmp_path / "input.svg"
    output_path = tmp_path / "output.svg"
    input_path.write_text(create_test_svg(include_footer=True))

    crop_file.remove_footer_and_adjust_height(str(input_path), str(output_path), padding=20.0)

    tree = ET.parse(output_path)
    root = tree.getroot()

    # Check that viewBox height was updated
    viewbox = root.get("viewBox", "")
    parts = viewbox.split()
    assert len(parts) == 4

    # New height should be less than original 600
    new_height = float(parts[3])
    assert new_height < 600
    assert new_height > 0


def test_remove_footer_and_adjust_height_no_footer(tmp_path):
    """Test behavior when footer element is not found."""
    input_path = tmp_path / "input.svg"
    output_path = tmp_path / "output.svg"
    input_path.write_text(create_test_svg(include_footer=False))

    result = crop_file.remove_footer_and_adjust_height(str(input_path), str(output_path))

    assert result is False
    # Output file should still not exist when footer not found
    assert not output_path.exists()


def test_remove_footer_and_adjust_height_custom_footer_id(tmp_path):
    """Test removing footer with custom ID."""
    input_path = tmp_path / "input.svg"
    output_path = tmp_path / "output.svg"

    svg_content = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">',
        '  <rect x="10" y="10" width="100" height="100" fill="red" />',
        '  <g id="custom_footer">',
        '    <rect x="0" y="500" width="800" height="100" fill="gray" />',
        "  </g>",
        "</svg>",
    ]
    input_path.write_text("\n".join(svg_content))

    result = crop_file.remove_footer_and_adjust_height(str(input_path), str(output_path), footer_id="custom_footer")

    assert result is True
    assert output_path.exists()


def test_remove_footer_and_adjust_height_custom_padding(tmp_path):
    """Test removing footer with custom padding."""
    input_path = tmp_path / "input.svg"
    output_path = tmp_path / "output.svg"
    input_path.write_text(create_test_svg(include_footer=True))

    crop_file.remove_footer_and_adjust_height(str(input_path), str(output_path), padding=50.0)

    tree = ET.parse(output_path)
    root = tree.getroot()

    height_str = root.get("height", "")
    height = float(height_str)

    # Height should account for padding
    assert height > 0


def test_remove_footer_removes_siblings_after_footer(tmp_path):
    """Test that elements after footer are also removed."""
    input_path = tmp_path / "input.svg"
    output_path = tmp_path / "output.svg"

    svg_content = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">',
        '  <rect x="10" y="10" width="100" height="100" fill="red" />',
        '  <g id="footer">',
        '    <rect x="0" y="500" width="800" height="100" fill="gray" />',
        "  </g>",
        '  <g id="after_footer">',
        '    <rect x="0" y="600" width="800" height="100" fill="black" />',
        "  </g>",
        "</svg>",
    ]
    input_path.write_text("\n".join(svg_content))

    crop_file.remove_footer_and_adjust_height(str(input_path), str(output_path))

    tree = ET.parse(output_path)
    root = tree.getroot()

    # Check that after_footer is also removed
    after_footer_elements = [elem for elem in root.iter() if elem.get("id") == "after_footer"]
    assert len(after_footer_elements) == 0


def test_crop_svg_file_success(tmp_path):
    """Test successful SVG cropping."""
    file_path = tmp_path / "test.svg"
    cropped_output_path = tmp_path / "test_cropped.svg"
    file_path.write_text(create_test_svg(include_footer=True))

    result = crop_file.crop_svg_file(file_path, cropped_output_path)

    assert result["success"] is True
    assert result["error"] is None
    assert cropped_output_path.exists()


def test_crop_svg_file_no_footer(tmp_path):
    """Test cropping SVG with no footer."""
    file_path = tmp_path / "test.svg"
    cropped_output_path = tmp_path / "test_cropped.svg"
    file_path.write_text(create_test_svg(include_footer=False))

    result = crop_file.crop_svg_file(file_path, cropped_output_path)

    assert result["success"] is False
    assert result["error"] == "No footer element found in SVG"


def test_crop_svg_file_invalid_input(tmp_path):
    """Test cropping with invalid SVG file."""
    file_path = tmp_path / "test.svg"
    cropped_output_path = tmp_path / "test_cropped.svg"
    file_path.write_text("This is not valid XML")

    result = crop_file.crop_svg_file(file_path, cropped_output_path)

    assert result["success"] is False
    assert result["error"] is not None


def test_crop_svg_file_file_not_found(tmp_path):
    """Test cropping with non-existent file."""
    file_path = tmp_path / "nonexistent.svg"
    cropped_output_path = tmp_path / "test_cropped.svg"

    result = crop_file.crop_svg_file(file_path, cropped_output_path)

    assert result["success"] is False
    assert result["error"] is not None


def test_crop_svg_file_exception_handling(tmp_path):
    """Test that exceptions are properly caught and returned."""
    file_path = tmp_path / "test.svg"
    cropped_output_path = tmp_path / "test_cropped.svg"
    file_path.write_text(create_test_svg(include_footer=True))

    # Mock remove_footer_and_adjust_height to raise an exception
    with patch("src.main_app.jobs_workers.crop_main_files.crop_file.remove_footer_and_adjust_height") as mock_remove:
        mock_remove.side_effect = Exception("Test exception")

        result = crop_file.crop_svg_file(file_path, cropped_output_path)

        assert result["success"] is False
        assert "Test exception" in result["error"]


def test_crop_svg_file_permission_error(tmp_path):
    """Test cropping when output path is not writable."""
    file_path = tmp_path / "test.svg"
    file_path.write_text(create_test_svg(include_footer=True))

    # Try to write to a directory as if it were a file
    cropped_output_path = tmp_path

    result = crop_file.crop_svg_file(file_path, cropped_output_path)

    assert result["success"] is False
    assert result["error"] is not None


def test_remove_footer_preserves_namespaces(tmp_path):
    """Test that XML namespaces are preserved during cropping."""
    input_path = tmp_path / "input.svg"
    output_path = tmp_path / "output.svg"

    svg_content = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="800" height="600" viewBox="0 0 800 600">',
        '  <rect x="10" y="10" width="100" height="100" fill="red" />',
        '  <g id="footer">',
        '    <rect x="0" y="500" width="800" height="100" fill="gray" />',
        "  </g>",
        "</svg>",
    ]
    input_path.write_text("\n".join(svg_content))

    crop_file.remove_footer_and_adjust_height(str(input_path), str(output_path))

    # Read output and verify namespaces are present
    output_content = output_path.read_text()
    assert 'xmlns="http://www.w3.org/2000/svg"' in output_content
    # Note: xlink namespace may only be preserved if it's actually used in the remaining content


def test_crop_svg_with_complex_nested_elements(tmp_path):
    """Test cropping SVG with deeply nested elements."""
    input_path = tmp_path / "input.svg"
    output_path = tmp_path / "output.svg"

    svg_content = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">',
        '  <g id="content">',
        "    <g>",
        '      <rect x="10" y="10" width="100" height="100" fill="red" />',
        "      <g>",
        '        <circle cx="200" cy="150" r="50" fill="blue" />',
        "      </g>",
        "    </g>",
        "  </g>",
        '  <g id="footer">',
        '    <rect x="0" y="500" width="800" height="100" fill="gray" />',
        "  </g>",
        "</svg>",
    ]
    input_path.write_text("\n".join(svg_content))

    result = crop_file.remove_footer_and_adjust_height(str(input_path), str(output_path))

    assert result is True

    tree = ET.parse(output_path)
    root = tree.getroot()

    # Verify content group still exists
    content_elements = [elem for elem in root.iter() if elem.get("id") == "content"]
    assert len(content_elements) == 1


def test_get_max_y_with_line_elements():
    """Test getting max y from line elements."""
    svg = '<line x1="10" y1="20" x2="100" y2="150" />'
    element = ET.fromstring(svg)

    max_y = crop_file.get_max_y_of_element(element)

    # Should get y2 value
    assert max_y == 150.0


def test_crop_svg_file_output_is_valid_xml(tmp_path):
    """Test that cropped output is valid XML."""
    file_path = tmp_path / "test.svg"
    cropped_output_path = tmp_path / "test_cropped.svg"
    file_path.write_text(create_test_svg(include_footer=True))

    crop_file.crop_svg_file(file_path, cropped_output_path)

    # Should be able to parse the output without errors
    tree = ET.parse(cropped_output_path)
    assert tree is not None
