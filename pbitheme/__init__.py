"""Power BI theme creator package.

The :mod:`pbitheme.model` module is GUI-free and can be used on its own to
build and serialise themes; :mod:`pbitheme.gui` provides the Qt front end.
"""

from .model import (
    PowerBITheme, TextClass, VISUAL_TYPES, LEGEND_POSITIONS,
    is_valid_hex, normalise_hex,
    build_background_object, build_border_object, build_title_object,
    build_data_labels_object, build_legend_object,
    unpack_background_object, unpack_border_object, unpack_title_object,
    unpack_data_labels_object, unpack_legend_object,
    merge_visual_style_entry
)

__all__ = [
    "PowerBITheme", "TextClass", "VISUAL_TYPES", "LEGEND_POSITIONS",
    "is_valid_hex", "normalise_hex",
    "build_background_object", "build_border_object", "build_title_object",
    "build_data_labels_object", "build_legend_object",
    "unpack_background_object", "unpack_border_object", "unpack_title_object",
    "unpack_data_labels_object", "unpack_legend_object",
    "merge_visual_style_entry"
]
__version__ = "0.2.0"
