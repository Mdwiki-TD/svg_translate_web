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
