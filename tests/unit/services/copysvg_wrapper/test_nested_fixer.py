from __future__ import annotations

import tempfile
from pathlib import Path

from src.main_app.services.copysvg_wrapper.nested_fixer import NestedStructureService


def test_nested_structure_service_analyze_and_repair(tmp_path: Path):
    svg_file = tmp_path / "test_nested.svg"
    svg_file.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><text><tspan>A<tspan>B</tspan></tspan></text></svg>'
    )

    nested_service = NestedStructureService(strategy="flatten")

    findings = nested_service.analyze_file(svg_file)
    assert len(findings) > 0

    repair_result = nested_service.repair_file(svg_file)
    assert repair_result.success is True
    assert repair_result.len_tags_fixed == 1
    assert repair_result.len_tags_after_fix == 0

    findings_after = nested_service.analyze_file(svg_file)
    assert len(findings_after) == 0


def test_nested_structure_service_no_nested_tags(tmp_path: Path):
    svg_file = tmp_path / "test_clean.svg"
    svg_file.write_text('<svg xmlns="http://www.w3.org/2000/svg"><text><tspan>A</tspan></text></svg>')

    nested_service = NestedStructureService(strategy="flatten")

    findings = nested_service.analyze_file(svg_file)
    assert len(findings) == 0

    repair_result = nested_service.repair_file(svg_file)
    assert repair_result.success is True
    assert repair_result.len_tags_fixed == 0


def test_nested_structure_service_ignores_valid_link_wrapping_text(tmp_path: Path):
    """A normal clickable SVG title must not be reported as a nested-tag error."""
    svg_file = tmp_path / "linked_title.svg"
    svg_file.write_text(
        "<svg xmlns=\"http://www.w3.org/2000/svg\">"
        "<a href=\"https://example.org/chart\" id=\"title\">"
        "<text><tspan id=\"trsvg1\">Chart title</tspan></text>"
        "</a></svg>"
    )

    nested_service = NestedStructureService(strategy="flatten")

    assert nested_service.analyze_file(svg_file) == []


def test_nested_structure_service_detects_repairable_nesting_inside_link(tmp_path: Path):
    """A link wrapper does not hide a genuinely nested tspan from repair."""
    svg_file = tmp_path / "linked_nested_tspan.svg"
    svg_file.write_text(
        "<svg xmlns=\"http://www.w3.org/2000/svg\">"
        "<a href=\"https://example.org/chart\" id=\"title\">"
        "<text><tspan id=\"outer\">Before <tspan id=\"inner\">nested</tspan></tspan></text>"
        "</a></svg>"
    )

    nested_service = NestedStructureService(strategy="flatten")
    findings = nested_service.analyze_file(svg_file)

    assert len(findings) == 1
    assert 'id=\"outer\"' in findings[0]

    repair_result = nested_service.repair_file(svg_file)

    assert repair_result.success is True
    # The third-party service also counts the valid outer <a> internally.
    # The wrapper's filtered analysis is the authoritative check for this job.
    assert repair_result.len_tags_before_fix == 2
    assert repair_result.len_tags_fixed == 1
    assert repair_result.len_tags_after_fix == 1
    assert nested_service.analyze_file(svg_file) == []
