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

Most fields update the **live preview**; a few (marked *export-only* in the
stages below) are exported as valid Power BI cards but can't be meaningfully
shown in a simplified mockup (e.g. font family, word wrap).

**Current overall card coverage: ~57%** (440 / 770 themeable cards across all visuals).

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
- **Stage 3 — Table & matrix depth — ◐ mostly done.** Previewed: grid **outer
  outline** + **overall text size**, matrix **row-header alignment** + **stepped
  layout**, **bold / italic / underline** and **font size** across column
  headers / values / row headers / totals / subtotals, full **subtotal font
  styling** (colour / size / italic / underline). Export-only (valid, no live
  preview): **font family** everywhere, **word wrap** (headers & values), matrix
  **column subtotals**. Still in Advanced JSON only: built-in table
  `stylePreset` (enum names not in the schema), per-column `columnFormatting`
  (data bars — needs per-column ids), `columnWidth`, `columnTotal`/`rowTotal`,
  `blankRows`, sparklines.
- **Stage 4 — Reference lines & analytics — ◐ mostly done.** Done: **Y-axis
  reference line** (show / value / colour), **trend line** (show / colour) on
  every chart that supports it, **pie / donut slices** (start angle + inner
  radius), **scatter bubble size + marker border**, and waterfall sentiment
  colours (Stage 3). Still to do: ratio line, error bars, `plotArea` shading,
  ribbon bands, small multiples.
- **Stage 5 — Slicer & non-chart visuals — ◐ mostly done.** Made customizable:
  **Action Button** (fill / text / outline), **Basic Shape** (fill / outline),
  **Decomposition Tree** (level-header + data-label colours), **Map** & **Filled
  Map** (data-point colour + category labels), **Shape Map** (default + border
  colours), **Image** (scaling, export-only), plus a slicer **slider** colour.
  Still to do: slicer date/numeric/search/dropdown, action-button icon + hover
  states, map controls/styles, textbox & smart-narrative text.
- **Stage 6 — Containers, tooltips & misc — ☐.** Report tooltip & visual-header
  tooltip styling, divider, spacing, subheader, `general` (alt text / responsive),
  small multiples, zoom slider.
- **Backlog — Advanced-JSON-only (no structured field yet).** Items that need
  per-column identity, in-cell chart rendering, or enum values Microsoft doesn't
  publish, so they stay in the Advanced JSON tab: table/matrix
  `columnFormatting` (per-column colour / **data bars**), `columnWidth`,
  `columnTotal` / `rowTotal`, `blankRows`, **sparklines**, and the built-in table
  **`stylePreset`**; chart `plotArea` (image / transparency only); `ratioLine`;
  and the per-visual tooltip family (`visualTooltip`, `visualHeaderTooltip`,
  `visualLink`).

### Coverage matrix

| Visual | Frame | Axes | Legend | Labels | Colors | Table | Card/KPI/Gauge | Slicer | Other | % |
|---|---|---|---|---|---|---|---|---|---|---|
| Bar Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ◐ | 58% |
| Column Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ◐ | 58% |
| Clustered Bar Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ◐ | 58% |
| Clustered Column Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ◐ | 58% |
| 100% Stacked Bar Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ◐ | 58% |
| 100% Stacked Column Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ◐ | 58% |
| Line Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ◐ | 60% |
| Area Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ◐ | 60% |
| Line & Clustered Column Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ◐ | 60% |
| Line & Stacked Column Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ◐ | 60% |
| Ribbon Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ◐ | 58% |
| Scatter Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ◐ | 57% |
| Waterfall Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ◐ | 65% |
| Pie Chart | ✅ | — | ✅ | ✅ | ◐ | — | — | — | ☐ | 62% |
| Donut Chart | ✅ | — | ✅ | ✅ | ◐ | — | — | — | ☐ | 62% |
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
| Slicer | ✅ | — | — | — | — | — | — | ◐ | ☐ | 41% |
| Map | ✅ | — | ✅ | ✅ | ◐ | — | — | — | ☐ | 52% |
| Filled Map | ✅ | — | ✅ | ✅ | ✅ | — | — | — | ☐ | 57% |
| Shape Map | ✅ | — | ✅ | — | ◐ | — | — | — | ☐ | 52% |
| Azure Maps | ✅ | — | ✅ | ◐ | ☐ | — | — | — | ☐ | 52% |
| Decomposition Tree | ✅ | — | — | ◐ | — | — | — | — | ◐ | 47% |
| Key Drivers | ✅ | — | — | — | — | — | — | — | ☐ | 58% |
| Q&A | ✅ | — | — | — | — | — | — | — | ☐ | 58% |
| Smart Narrative | ✅ | — | — | — | — | — | — | — | ☐ | 43% |
| Action Button | ✅ | — | — | — | ✅ | — | — | — | ◐ | 52% |
| Basic Shape | ✅ | — | — | — | ✅ | — | — | — | ◐ | 50% |
| Image | ✅ | — | — | — | — | — | — | — | ◐ | 61% |
| Text Box | ✅ | — | — | — | — | ☐ | — | — | ☐ | 50% |
| Python Visual | ✅ | — | — | — | — | — | — | — | ☐ | 58% |
| R Visual | ✅ | — | — | — | — | — | — | — | ☐ | 58% |

*Notes: **Frame** = title, background, border, drop shadow, visual header,
padding (generic overrides on every visual). The **Card/KPI/Gauge** column tracks
each visual's specialized cards — e.g. Card's value/label live under **Labels**;
its `wordWrap` card is what's still ☐. **Colors** = per-series / default data
point, sentiment, ribbon bands, pie slices, shape fills, map data points.
**Other** = reference lines, trend, plot area, tooltips, small multiples, and the
visual-specific cards for buttons / shapes / trees / maps / images (Stages 4-6).*

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
