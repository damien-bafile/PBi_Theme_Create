"""UI theme colors and constants for the Power BI Theme Creator."""

# Status indicator colours. These are mutated by apply_*_palette so they stay
# WCAG-AA against the active surface (dark greens/reds on white, brighter ones
# on the dark palette). Read them at refresh time, not import time.
STATUS_CUSTOM_COLOR = "#005620"   # customized elements (the notable state — glows)
STATUS_DEFAULT_COLOR = "#8b0000"  # default / uncustomized elements
STATUS_MUTED_COLOR = "#605E5C"    # muted, still-AA grey for the "default" majority
_STATUS_LIGHT = ("#005620", "#8b0000", "#605E5C")
_STATUS_DARK = ("#3FB950", "#F85149", "#9E9E9E")  # green / red / grey, AA on dark

# UI text and structural colors
TEXT_PRIMARY = "#252423"
TEXT_STRONG = "#000000"
BORDER_SUBTLE = "#888888"
SURFACE_BACKGROUND = "#FFFFFF"

# Light "workshop" surface tokens (DESIGN.md) used by the forced app palette.
SURFACE_ALT = "#F3F2F1"      # panels / alternate rows
BORDER_HAIRLINE = "#E1DFDD"

# Dark surface tokens.
DARK_WINDOW = "#2B2B2B"
DARK_BASE = "#1E1E1E"
DARK_BUTTON = "#3C3C3C"
DARK_TEXT = "#E6E6E6"
DARK_DISABLED = "#6E6E6E"
DARK_BORDER = "#3C3C3C"

#: True while the dark palette is active (read by anything that needs the mode).
dark_mode = False

# Monospace resolution. "monospace" is a generic alias Qt may resolve
# inconsistently; DESIGN.md prefers Courier New. Prefer it, then guarantee a
# real fixed-width fallback via the style hint / a CSS fallback stack.
MONOSPACE_STACK = '"Courier New", "DejaVu Sans Mono", "Consolas", monospace'


def monospace_font(size: int = 10):
    """A fixed-pitch QFont (Courier New where present, a monospace fallback else)."""
    from PySide6.QtGui import QFont

    f = QFont("Courier New", size)
    f.setStyleHint(QFont.StyleHint.Monospace)
    f.setFixedPitch(True)
    return f


def _set_status_for(dark: bool) -> None:
    global STATUS_CUSTOM_COLOR, STATUS_DEFAULT_COLOR, STATUS_MUTED_COLOR, dark_mode
    STATUS_CUSTOM_COLOR, STATUS_DEFAULT_COLOR, STATUS_MUTED_COLOR = (
        _STATUS_DARK if dark else _STATUS_LIGHT
    )
    dark_mode = dark


def apply_light_palette(app) -> None:
    """Force the app's own light palette so the design system is real everywhere.

    Without this the app inherits whatever OS theme it lands in (e.g. a dark
    desktop), which washes out the ✓/✗ status cues. Uses the Fusion style so the
    palette applies uniformly across platforms.
    """
    from PySide6.QtGui import QColor, QPalette

    _set_status_for(False)
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


def apply_dark_palette(app) -> None:
    """Apply a dark Fusion palette (menu-toggleable, persisted by the caller)."""
    from PySide6.QtGui import QColor, QPalette

    _set_status_for(True)
    app.setStyle("Fusion")
    p = QPalette()
    window = QColor(DARK_WINDOW)
    base = QColor(DARK_BASE)
    text = QColor(DARK_TEXT)
    disabled = QColor(DARK_DISABLED)
    p.setColor(QPalette.Window, window)
    p.setColor(QPalette.WindowText, text)
    p.setColor(QPalette.Base, base)
    p.setColor(QPalette.AlternateBase, QColor(DARK_BUTTON))
    p.setColor(QPalette.Text, text)
    p.setColor(QPalette.Button, QColor(DARK_BUTTON))
    p.setColor(QPalette.ButtonText, text)
    p.setColor(QPalette.ToolTipBase, window)
    p.setColor(QPalette.ToolTipText, text)
    p.setColor(QPalette.Highlight, QColor("#118DFF"))
    p.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    p.setColor(QPalette.PlaceholderText, disabled)
    p.setColor(QPalette.BrightText, QColor("#FF6B6B"))
    for group in (QPalette.Disabled,):
        p.setColor(group, QPalette.WindowText, disabled)
        p.setColor(group, QPalette.Text, disabled)
        p.setColor(group, QPalette.ButtonText, disabled)
    app.setPalette(p)


def apply_palette(app, dark: bool) -> None:
    """Apply the dark or light palette by flag."""
    if dark:
        apply_dark_palette(app)
    else:
        apply_light_palette(app)
