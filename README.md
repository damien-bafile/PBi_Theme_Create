# PBi_Theme_Create

A **Power BI theme creator**: a Python + Qt (PySide6) desktop app that lets you
configure a report theme visually — with a **live preview of every visual** — and
export it as a Power BI `*.json` theme file. The theme model is GUI-free, so you
can also generate themes from scripts.

## Features

- **Live visual preview** — every visual is drawn as an SVG mockup that updates
  as you edit, plus a live JSON preview of the exported theme.
- **Per-visual formatting** — axes, gridlines, legend, data labels, table
  headers / values / totals / banded rows, gauge, KPI, slicer and more, for each
  visual type.
- **Generic overrides on every visual** — title, background, border (width &
  rounded corners), drop shadow, data labels, legend, visual header, padding.
- **Named style presets** — multiple presets per visual (Power BI's Style
  dropdown), not just the default.
- **Colours & text** — data colours, structural colour classes, conditional-
  format gradient colours, and the four primary text classes.
- **Valid Power BI export** — the per-visual settings are translated into real
  Power BI theme *cards* (verified against Microsoft's published schema), and
  **imported themes reverse-translate** back into the editor (clean round-trip).
- **Advanced JSON** tab — set any property the schema supports, even ones not yet
  in the structured UI.

## Install & run

```bash
pip install -r requirements.txt
python main.py
```

Requires Python 3.8+ and PySide6.

## Using the theme in Power BI

1. Save your theme from the app (**File → Save As...**).
2. In Power BI Desktop: **View → Themes → Browse for themes** and select the
   generated `.json` file.

## Generate a theme without the GUI

```python
from pbitheme.model import PowerBITheme

theme = PowerBITheme("Corporate")
theme.data_colors = ["#118DFF", "#12239E", "#E66C37"]
theme.background = "#FFFFFF"
theme.save("corporate.json")
```

## Power BI theme coverage roadmap

**Goal: 100% structured coverage** — every Power BI formatting *card* for every
visual editable in the structured UI (with live preview), not just via the
Advanced JSON escape hatch. Coverage is tracked below at the **card** level
(property-depth within each card is an ongoing sub-goal). Today anything missing
can still be set through the **Advanced JSON** tab and exports validly.

**Legend:** ✅ done &nbsp;·&nbsp; ◐ partial &nbsp;·&nbsp; ☐ planned &nbsp;·&nbsp; — not applicable to this visual

**Current overall card coverage: ~52%** (393 / 749 themeable cards across all visuals).

### Stages

- **Stage 1 — Foundations — ✅ complete.** Data / structural / gradient colours;
  text classes; per-visual core formatting for every customizable visual (axes,
  gridlines, legend, data labels, headers / values / totals, banded rows); the
  generic overrides (title, background, border width & radius, drop shadow,
  visual header, padding); data-point default colour; gauge / KPI / slicer / card
  specifics; named style presets; bespoke SVG previews for every visual; valid
  card export **and** reverse-translate import (round-trip).
- **Stage 2 — Axis & label depth + subtitle — ✅ complete.** Axis **title
  text**, value-axis **log scale** and **fixed range** (start / end), data-label
  **display units**, **decimal precision** and **position**, **legend title**
  (show + text), and a **subtitle** generic override (all visuals). (Data-label
  *orientation* is column/bar-only in the schema, and `plotArea` offers only an
  image + transparency — no fill colour — so both are intentionally skipped.)
- **Stage 3 — Table & matrix depth — ☐.** Built-in table `stylePreset`,
  `columnFormatting` (per-column colour / alignment / data bars), `columnWidth`,
  column / row totals (matrix), blank rows, sparklines, word wrap.
- **Stage 4 — Reference lines & analytics — ☐.** X / Y reference lines, trend
  line, ratio line, error bars, markers, scatter bubbles / fill, waterfall
  sentiment colours & breakdown, ribbon bands, pie slices (start angle / inner
  radius).
- **Stage 5 — Slicer & non-chart visuals — ☐.** Slicer slider / date / date
  range / numeric input / selection / search box / dropdown; decomposition tree
  nodes; action-button fill / text / icon / outline + states; image scaling;
  shapes; map controls & category labels.
- **Stage 6 — Containers, tooltips & misc — ☐.** Report tooltip & visual-header
  tooltip styling, divider, spacing, subheader, `general` (alt text / responsive),
  small multiples, zoom slider.

### Coverage matrix

| Visual | Frame | Axes | Legend | Labels | Colors | Table | Card/KPI/Gauge | Slicer | Refs/Analytics | % |
|---|---|---|---|---|---|---|---|---|---|---|
| Bar Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ☐ | 48% |
| Column Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ☐ | 48% |
| Clustered Bar Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ☐ | 48% |
| Clustered Column Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ☐ | 48% |
| 100% Stacked Bar Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ☐ | 48% |
| 100% Stacked Column Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ☐ | 48% |
| Line Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ☐ | 46% |
| Area Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ☐ | 46% |
| Line & Clustered Column Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ☐ | 46% |
| Line & Stacked Column Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ☐ | 50% |
| Ribbon Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ☐ | 48% |
| Scatter Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ☐ | 41% |
| Waterfall Chart | ✅ | ✅ | ✅ | ✅ | ☐ | — | — | — | ☐ | 55% |
| Pie Chart | ✅ | — | ✅ | ✅ | ☐ | — | — | — | ☐ | 56% |
| Donut Chart | ✅ | — | ✅ | ✅ | ☐ | — | — | — | ☐ | 56% |
| Treemap | ✅ | — | ✅ | ◐ | ☐ | — | — | — | ☐ | 56% |
| Funnel | ✅ | ☐ | — | ✅ | ✅ | — | — | — | ☐ | 60% |
| Gauge | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | — | ☐ | 70% |
| Card | ✅ | — | — | ✅ | — | — | ☐ | — | ☐ | 60% |
| Multi-row Card | ✅ | — | — | ✅ | — | — | ☐ | — | ☐ | 56% |
| KPI | ✅ | — | — | — | — | — | ✅ | — | ☐ | 68% |
| Table | ✅ | — | — | — | — | ◐ | — | — | ☐ | 57% |
| Table (Extended) | ✅ | — | — | — | — | ◐ | — | — | ☐ | 57% |
| Matrix | ✅ | — | — | — | — | ◐ | — | — | ☐ | 54% |
| Pivot Table | ✅ | — | — | — | — | ◐ | — | — | ☐ | 54% |
| Slicer | ✅ | — | — | — | — | — | — | ◐ | ☐ | 37% |
| Map | ✅ | — | ✅ | ☐ | ☐ | — | — | — | ☐ | 50% |
| Filled Map | ✅ | — | ✅ | ◐ | ☐ | — | — | — | ☐ | 56% |
| Shape Map | ✅ | — | ✅ | — | ☐ | — | — | — | ☐ | 53% |
| Azure Maps | ✅ | — | ✅ | ◐ | ☐ | — | — | — | ☐ | 56% |
| Decomposition Tree | ✅ | — | — | ☐ | — | — | — | — | ☐ | 50% |
| Key Drivers | ✅ | — | — | — | — | — | — | — | ☐ | 58% |
| Q&A | ✅ | — | — | — | — | — | — | — | ☐ | 58% |
| Smart Narrative | ✅ | — | — | — | — | — | — | — | ☐ | 58% |
| Action Button | ✅ | — | — | — | — | — | — | — | ☐ | 58% |
| Basic Shape | ✅ | — | — | — | — | — | — | — | ☐ | 58% |
| Image | ✅ | — | — | — | — | — | — | — | ☐ | 58% |
| Text Box | ✅ | — | — | — | — | ☐ | — | — | ☐ | 53% |
| Python Visual | ✅ | — | — | — | — | — | — | — | ☐ | 58% |
| R Visual | ✅ | — | — | — | — | — | — | — | ☐ | 58% |

*Notes: **Frame** = title, background, border, drop shadow, visual header,
padding (generic overrides on every visual). The **Card/KPI/Gauge** column tracks
each visual's specialized cards — e.g. Card's value/label live under **Labels**;
its `wordWrap` card is what's still ☐. **Colors** = per-series / default data
point, sentiment, ribbon bands, pie slices. **Refs/Analytics** = reference lines,
plot area, trend, tooltips, small multiples and other container cards (Stage 6).*

## Project layout

```
main.py                          # GUI entry point
pbitheme/
    model.py                     # PowerBITheme, TextClass — the GUI-free model
    theme_export.py              # internal formatting <-> valid Power BI cards
    driver.py                    # headless driver (control + screenshot the app)
    gui/
        main_window.py           # editor form + live preview
        visual_style_dialog.py   # per-visual style editor + presets
        visual_formatter.py      # dynamic formatter panel
        visual_formatting_config.py  # per-visual field definitions
        preview_mockups.py       # SVG mockups for every visual
        preview_panel.py         # main-window visual preview
        widgets.py               # ColorButton, editors, checklist
test_all_features.py             # feature suite
test_dynamic_preview.py          # every setting updates the preview
test_theme_export.py             # export cards + round-trip invariants
```

## Architecture

- **`PowerBITheme`** owns all editable state and serialises to / from the Power
  BI theme JSON. Per-visual settings are kept internally as a flat `formatting`
  map and translated to real Power BI cards on export (`theme_export`).
- The GUI collects widget state into a fresh `PowerBITheme` on every edit and
  re-renders both the SVG preview and the JSON, keeping model and view decoupled.
