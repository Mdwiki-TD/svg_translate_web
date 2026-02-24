""" """

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

logger = logging.getLogger("svg_translate")


def get_max_y_of_element(element) -> float:
    """
    Get the maximum y+height value from an SVG element and all its descendants.
    Used to calculate the actual bottom edge of the remaining content.
    """
    max_y = 0.0

    y_attrs = [element.get("y"), element.get("y1"), element.get("y2"), element.get("cy")]
    for y_val in y_attrs:
        if y_val:
            # Extract only numbers in case there are strings like "px" attached
            y_match = re.search(r"[\d.-]+", y_val)
            if y_match is None:
                continue
            try:
                y_val = float(y_match.group())
            except (ValueError, TypeError):
                continue

            # If the element has a height (like rect), add it to Y
            height_val = element.get("height")
            h_num = 0.0
            if height_val:
                h_match = re.search(r"[\d.]+", height_val)
                if h_match is not None:
                    try:
                        h_num = float(h_match.group())
                    except (ValueError, TypeError):
                        h_num = 0.0

            # Update the maximum Y-axis value
            max_y = max(max_y, y_val + h_num)
    return max_y


def remove_footer_and_adjust_height(
    input_path: Path, output_path: Path, footer_id: str = "footer", padding: float = 10.0
) -> bool:
    # 1. Register the SVG namespace to avoid modifying/corrupting the tags
    namespace = "http://www.w3.org/2000/svg"
    ET.register_namespace("", namespace)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

    # Parse the SVG file
    tree = ET.parse(input_path)
    root = tree.getroot()

    old_height = root.get("height", "?")

    # 2. Find and remove the footer element
    footer_removed = False
    for svg_element in root.iter():
        if footer_removed:
            break

        children = list(svg_element)
        for index, child in enumerate(children):
            if child.get("id", "") == footer_id:
                # Found the footer!
                # Now remove the footer and ALL sibling elements that come after it
                elements_to_remove = children[index:]
                for svg_child_element in elements_to_remove:
                    svg_element.remove(svg_child_element)

                footer_removed = True
                break

    if not footer_removed:
        logger.info(f"No <g id='{footer_id}'> found in the file.")
        return False

    # 3. Calculate the new height based on the REMAINING elements
    content_max_y = 0.0

    # Search all remaining elements for attributes that define their vertical position
    for child in root.iter():
        y = get_max_y_of_element(child)
        # Update the maximum Y-axis value
        content_max_y = max(content_max_y, y)

    logger.info(f"📐 Max y in remaining content: {content_max_y:.2f}")

    # New height = max y of content + padding
    # Alternatively, use the footer's top position directly: new_height = footer_min_y
    # Add a bottom margin (padding) to keep it visually appealing
    # new_height = math.ceil(content_max_y + padding)
    new_height = content_max_y + padding

    if content_max_y == 0.0:
        logger.warning("No vertical extent found in remaining content; falling back to original height.")
        # Optionally fall back to the original height or skip modification
        return False

    logger.info(f"📏 New height: {new_height:.2f} (padding={padding})")

    # 4. Update the viewBox and height attributes in the root <svg> tag
    root.set("height", f"{new_height:.2f}")
    old_viewbox = root.get("viewBox", "")
    if old_viewbox:
        parts = old_viewbox.split()
        if len(parts) == 4:
            # Update the height value in the viewBox
            parts[3] = f"{new_height:.2f}"
            root.set("viewBox", " ".join(parts))

    logger.info(f"🔄 height: {old_height} → {new_height:.2f}")

    # Save the new file
    tree.write(output_path, encoding="unicode", xml_declaration=False)

    logger.info(f"💾 Saved to: {output_path}")
    return True


def crop_svg_file(
    file_path: Path,
    cropped_output_path: Path,
) -> dict[str, Any]:
    """
    Crop SVG using viewBox manipulation.

    PLACEHOLDER: This is a placeholder implementation. Full implementation will:
    1. Parse SVG to get current dimensions
    2. Modify viewBox attribute to crop (or add crop transform)
    3. Save cropped version to output path

    Args:
        file_path: Path to the SVG file to crop
        cropped_output_path: Path where the cropped SVG should be saved

    Returns:
        dict with keys: success (bool), error (str|None)
    """
    try:
        cropped = remove_footer_and_adjust_height(file_path, cropped_output_path)

    except Exception as e:
        logger.exception(f"Error cropping SVG: {e}")
        return {"success": False, "error": str(e)}

    return {"success": cropped, "error": None if cropped else "No footer element found in SVG"}


__all__ = [
    "crop_svg_file",
]
