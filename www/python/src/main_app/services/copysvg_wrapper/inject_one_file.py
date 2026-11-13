"""Step for injecting translations into SVG files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from CopySVGTranslation import SVGTranslationService, TranslationConfig  # type: ignore
from CopySVGTranslation.exceptions import CopySVGTranslationError  # type: ignore
from lxml import etree

from .mapping import (
    InjectorData,
    InjectorStats,
    InjectResult,
    TranslationMapping,
)

logger = logging.getLogger(__name__)


class SvgInjector:
    """SVG translation injection service."""

    def __init__(self, config: TranslationConfig | None = None) -> None:
        """Initialize with optional configuration.

        Args:
            config: Translation configuration. Uses defaults if None.
        """
        self.config = config or TranslationConfig(
            case_insensitive=True,
            overwrite_translations=False,
            pretty_print=True,
            sort_switches=True,
        )

    def write_svg_file(self, output_file, tree: etree._ElementTree) -> bool:
        """Write SVG to disk."""
        try:
            tree.write(
                str(output_file),
                encoding="utf-8",
                xml_declaration=True,
                pretty_print=True,
            )
            return True
        except (OSError, Exception):
            logger.error("Failed to write translated SVG: %s", output_file)
            return False

    def write_msg(self, stats: InjectorStats) -> str:
        """Format injection result message."""
        if stats.new_languages_count > 0:
            msg = f"{stats.new_languages_count} languages injected"

        elif stats.updated_translations > 0:
            msg = f"{stats.updated_translations} translations Updated"

        elif stats.inserted_translations > 0:
            msg = f"{stats.inserted_translations} translations inserted"

        return msg

    def _inject(
        self,
        file_name: str,
        data: InjectorData,
    ) -> InjectResult:
        """Internal injection result handler."""
        stats_obj = data.inject_stats
        result_error = (data.error.code or data.error.label) if data.error else None
        tree = data.tree

        if not tree:
            logger.debug(f"Failed to translate {file_name}")
            msg = (data.error.label if data.error else None) or "Failed to translate"

            if result_error == "nested_tspan_error":
                msg = "Nested tspan error"

            return InjectResult(result=False, msg=msg)

        if result_error:
            logger.debug(f"Failed to translate {file_name}")
            return InjectResult(result=False, msg=result_error)

        if not stats_obj.has_changes():
            return InjectResult(result=None, msg="No changes")

        return InjectResult.from_stats(
            stats=stats_obj,
            result=True,
        )

    def inject_one_file(
        self,
        file: Path,
        translations: dict[str, Any] | TranslationMapping,
        output_file: Path,
        overwrite_translations: bool = False,
    ) -> InjectResult:
        """Inject translations into a collection of SVG files and write the results."""
        if isinstance(translations, TranslationMapping):
            translations = translations.to_json()

        data: InjectorData = self.start_svg_injection(
            inject_file=file,
            mapping=translations,
            overwrite_translations=overwrite_translations,
        )

        inject_result: InjectResult = self._inject(file_name=file.name, data=data)

        if not inject_result.result:
            return inject_result

        saved = self.write_svg_file(output_file, data.tree)

        if saved:
            inject_result.msg = self.write_msg(data.inject_stats)
            return inject_result

        logger.error("Failed to write translated SVG: %s", output_file)

        inject_result.result = False
        inject_result.msg = "Failed to write file"

        return inject_result

    def start_svg_injection(
        *,
        inject_file: Path | str,
        mapping: dict[str, Any] | TranslationMapping | None = None,
        overwrite_translations: bool = False,
    ) -> InjectorData:
        """
        Function-style wrapper around SVGTranslationService.inject, kept for
        backward compatibility with existing callers.
        """
        config = TranslationConfig(
            case_insensitive=True,
            overwrite_translations=overwrite_translations,
            pretty_print=True,
            sort_switches=True,
        )

        file_name = inject_file.name if isinstance(inject_file, Path) else str(inject_file)

        service = SVGTranslationService(config=config)

        try:
            op_result = service.inject(
                svg_path=inject_file,
                mapping=mapping,
            )

            if op_result.data is not None:
                return op_result.data
            else:
                err_code = op_result.error_code or "injection_failed"
                err_exc = CopySVGTranslationError(op_result.error or "", code=err_code)
                return InjectorData.from_error(err_exc)

        except CopySVGTranslationError as exc:
            logger.error(f"CopySVGTranslationError on file:{file_name}.")
            logger.error(f"Error code: {exc.code}")
            logger.error(f"Error label: {exc.label}")
            return InjectorData.from_error(exc)

        except Exception as exc:
            logger.error(f"Error injecting translations into {file_name}: {exc}")
            return InjectorData.from_error(exc)


__all__ = [
    "SvgInjector",
]
