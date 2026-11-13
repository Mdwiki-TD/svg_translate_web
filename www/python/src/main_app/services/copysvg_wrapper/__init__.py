from .extract_translations import SvgTranslationExtractor
from .inject_one_file import (
    SvgInjector,
)
from .mapping import (
    ExtractResult,
    InjectorData,
    InjectorStats,
    InjectResult,
    TranslationMapping,
)
from .nested_fixer import NestedStructureService

__all__ = [
    "NestedStructureService",
    "SvgTranslationExtractor",
    "SvgInjector",
    "InjectResult",
    "InjectorStats",
    "InjectorData",
    "TranslationMapping",
    "ExtractResult",
]
