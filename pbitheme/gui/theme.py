"""UI theme colors and constants for the Power BI Theme Creator."""

# Status indicator colors (WCAG AA compliant: 4.5:1+ contrast on white)
STATUS_CUSTOM_COLOR = "#005620"  # Dark green for customized elements
STATUS_DEFAULT_COLOR = "#8b0000"  # Dark red for default/uncustomized elements

# UI text and structural colors
TEXT_PRIMARY = "#252423"
TEXT_STRONG = "#000000"
BORDER_SUBTLE = "#888888"
SURFACE_BACKGROUND = "#FFFFFF"

# Light "workshop" surface tokens (DESIGN.md) used by the forced app palette.
SURFACE_ALT = "#F3F2F1"      # panels / alternate rows
BORDER_HAIRLINE = "#E1DFDD"


def apply_light_palette(app) -> None:
    """Force the app's own light palette so the design system is real everywhere.

    The status colours (STATUS_*), the swatch text picker, and DESIGN.md are all
    tuned for a white surface; without this the app inherits whatever OS theme it
    lands in (e.g. a dark desktop), which washes out the ✓/✗ status cues. Uses the
    Fusion style so the palette applies uniformly across platforms.
    """
    from PySide6.QtGui import QColor, QPalette

    app.setStyle("Fusion")
    p = QPalette()
    window = QColor(SURFACE_ALT)
    base = QColor(SURFACE_BACKGROUND)
    text = QColor(TEXT_PRIMARY)
    disabled = QColor("#A19F9D")
    p.setColor(QPalette.Window, window)
    p.setColor(QPalette.WindowText, text)
    p.setColor(QPalette.Base, base)
    p.setColor(QPalette.AlternateBase, window)
    p.setColor(QPalette.Text, text)
    p.setColor(QPalette.Button, window)
    p.setColor(QPalette.ButtonText, text)
    p.setColor(QPalette.ToolTipBase, base)
    p.setColor(QPalette.ToolTipText, text)
    p.setColor(QPalette.Highlight, QColor("#118DFF"))
    p.setColor(QPalette.HighlightedText, base)
    p.setColor(QPalette.PlaceholderText, disabled)
    for group in (QPalette.Disabled,):
        p.setColor(group, QPalette.WindowText, disabled)
        p.setColor(group, QPalette.Text, disabled)
        p.setColor(group, QPalette.ButtonText, disabled)
    app.setPalette(p)
