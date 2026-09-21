"""Temporary helper: dump the app URL map to a file for before/after comparison."""

from __future__ import annotations


def test_dump_url_map(mock_app):
    rows = sorted(
        f"{r.rule}\t{','.join(sorted(r.methods - {'OPTIONS', 'HEAD'}))}\t{r.endpoint}"
        for r in mock_app.url_map.iter_rules()
    )
    with open("urlmap_dump.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(rows))
