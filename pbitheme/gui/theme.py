"""UI theme colors and constants for the Power BI Theme Creator."""

# Status indicator colors (WCAG AA compliant: 4.5:1+ contrast on white)
STATUS_CUSTOM_COLOR = "#005620"  # Dark green for customized elements
STATUS_DEFAULT_COLOR = "#8b0000"  # Dark red for default/uncustomized elements

# UI text and structural colors
TEXT_PRIMARY = "#252423"
TEXT_STRONG = "#000000"
BORDER_SUBTLE = "#888888"
SURFACE_BACKGROUND = "#FFFFFF"

# Luminance threshold for auto-selecting text color (light/dark) on colored backgrounds
# Colors with luminance > threshold get dark text (#000000), otherwise light text (#FFFFFF)
LUMINANCE_THRESHOLD = 140
