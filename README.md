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
- **Generic overrides on every visual** — title, subtitle, background, border
  (width & rounded corners), drop shadow, data labels, legend, visual header,
  padding, divider, spacing, alt text, and data / header tooltip styling.
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
pip install -e .        # installs PySide6 + jsonschema
python main.py
```

Requires Python 3.8+ and PySide6.

## Using the theme in Power BI

1. Save your theme from the app (**File → Save As...**).
2. In Power BI Desktop: **View → Themes → Browse for themes** and select the
   generated `.json` file.

## Schema validation

The exported theme can be validated against the **official Power BI report
theme JSON schema** (bundled from Microsoft's `powerbi-desktop-samples`,
currently **v2.157**) via **File → Validate** (Ctrl+L). It is also scriptable
and covered by tests:

```python
from pbitheme.model import PowerBITheme
from pbitheme.validate import validate_theme

assert validate_theme(PowerBITheme("Demo").to_dict()) == []
```

Run the conformance tests (they validate the real export pipeline against the
bundled schema):

```bash
python -m unittest discover -s tests
```

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

**Current overall card coverage: ~70%** (539 / 770 themeable cards across all visuals).

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
- **Stage 3 — Table & matrix depth — ✅ complete.** Previewed: grid **outer
  outline** + **overall text size**, matrix **row-header alignment** + **stepped
  layout**, **bold / italic / underline** and **font size** across column
  headers / values / row headers / totals / subtotals, full **subtotal font
  styling** (colour / size / italic / underline), and **data bars** (positive
  colour). Export-only (valid, no live preview): **font family** everywhere,
  **word wrap** (headers & values), matrix **column subtotals**. The remaining
  Advanced-JSON items were finished in the **Advanced cards** stage below (data
  bars, `columnWidth`, total label / apply-to-headers, `blankRows`, sparklines,
  built-in `stylePreset`).
- **Stage 4 — Reference lines & analytics — ✅ complete.** Done: **Y-axis
  reference line** (show / value / colour), **trend line** (show / colour) on
  every chart that supports it, **pie / donut slices** (start angle + inner
  radius), **scatter bubble size + marker border**, waterfall sentiment colours
  (Stage 3), a scatter **ratio line** (show / colour — live previewed) and
  **plot-area transparency** on every cartesian chart. (Error bars and ribbon
  bands need per-measure field binding a theme can't supply, so they stay out;
  small multiples shipped in Stage 6.)
- **Stage 5 — Slicer & non-chart visuals — ✅ complete.** Made customizable:
  **Action Button** (fill / text / outline, icon, glow & shadow, and a **hover
  state**), **Basic Shape** (fill / outline), **Decomposition Tree** (level-header
  + data-label colours), **Map** & **Filled Map** (data-point / region colour,
  category labels, region **borders**, map **style** & **controls**), **Shape
  Map** (default + border colours), **Image** (scaling), **Text Box** and **Smart
  Narrative** (text colour / size / font), plus the slicer **selection**,
  **slider**, **search box**, **date slicer**, **numeric slicer** and **dropdown**
  styling. (Button hover exports as a `$id` state array; date / numeric / search /
  dropdown and font families are valid export-only cards — no live preview.)
- **Stage 6 — Containers, tooltips & misc — ✅ complete.** Added as generic
  overrides on **every** visual: a **divider** (colour / width / style — live
  previewed under the title), **spacing** (space below title + between
  components), **general** (**alt text** + responsive layer order), a **data
  tooltip** (background + title / value colours) and a **visual-header tooltip**
  (background + title colour). Cartesian charts also gain a **small-multiples
  layout** card (columns / rows / gridline & background colour). (Spacing,
  general, tooltips and small multiples are valid export-only cards — no live
  preview; there is no `zoomSlider` card in the schema, and the per-visual
  `visualLink`/navigation tooltip stays in the Advanced-JSON backlog.)
- **Stage 7 — Advanced cards — ✅ complete.** The former backlog, tackled by
  setting each card's **theme-level defaults** (no per-column identity needed):
  table/matrix **data bars** (`columnFormatting.dataBars` — positive / negative /
  axis colour, reverse, hide-text; positive colour live-previewed as bars in the
  value cells), **column sizing** (auto-size + default width), grand-total
  **label** (table) / **apply-to-headers** (matrix), matrix **blank rows**
  (fill + border), **sparklines** (type / line / marker colour), and the built-in
  **`stylePreset`** (a dropdown of the documented preset names); plus chart
  **plot-area transparency** and the scatter **ratio line**. All export-only
  except data bars and the ratio line, all schema-valid, all round-trip.
- **Not themeable — stays in Advanced JSON.** The per-visual navigation/link card
  (`visualLink`) is genuinely instance-specific — it targets a bookmark, report
  section or URL a theme can't know — so it has no structured field by design.

### Coverage matrix

| Visual | Frame | Axes | Legend | Labels | Colors | Table | Card/KPI/Gauge | Slicer | Other | % |
|---|---|---|---|---|---|---|---|---|---|---|
| Bar Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ✅ | 67% |
| Column Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ✅ | 67% |
| Clustered Bar Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | 67% |
| Clustered Column Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | 67% |
| 100% Stacked Bar Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ✅ | 67% |
| 100% Stacked Column Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ✅ | 67% |
| Line Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | 69% |
| Area Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | 69% |
| Line & Clustered Column Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | 69% |
| Line & Stacked Column Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | 69% |
| Ribbon Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ✅ | 67% |
| Scatter Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ✅ | 70% |
| Waterfall Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ◐ | 72% |
| Pie Chart | ✅ | — | ✅ | ✅ | ◐ | — | — | — | ◐ | 67% |
| Donut Chart | ✅ | — | ✅ | ✅ | ◐ | — | — | — | ◐ | 67% |
| Treemap | ✅ | — | ✅ | ◐ | ☐ | — | — | — | ◐ | 62% |
| Funnel | ✅ | ☐ | — | ✅ | ✅ | — | — | — | ◐ | 65% |
| Gauge | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | — | ◐ | 74% |
| Card | ✅ | — | — | ✅ | — | — | ☐ | — | ◐ | 65% |
| Multi-row Card | ✅ | — | — | ✅ | — | — | ☐ | — | ◐ | 62% |
| KPI | ✅ | — | — | — | — | — | ✅ | — | ◐ | 72% |
| Table | ✅ | — | — | — | — | ✅ | — | — | ◐ | 71% |
| Table (Extended) | ✅ | — | — | — | — | ✅ | — | — | ◐ | 71% |
| Matrix | ✅ | — | — | — | — | ✅ | — | — | ◐ | 69% |
| Pivot Table | ✅ | — | — | — | — | ✅ | — | — | ◐ | 69% |
| Slicer | ✅ | — | — | — | — | — | — | ✅ | ◐ | 67% |
| Map | ✅ | — | ✅ | ✅ | ◐ | — | — | — | ◐ | 64% |
| Filled Map | ✅ | — | ✅ | ✅ | ✅ | — | — | — | ◐ | 68% |
| Shape Map | ✅ | — | ✅ | — | ◐ | — | — | — | ◐ | 58% |
| Azure Maps | ✅ | — | ✅ | ◐ | ☐ | — | — | — | ◐ | 58% |
| Decomposition Tree | ✅ | — | — | ◐ | — | — | — | — | ◐ | 53% |
| Key Drivers | ✅ | — | — | — | — | — | — | — | ◐ | 63% |
| Q&A | ✅ | — | — | — | — | — | — | — | ◐ | 63% |
| Smart Narrative | ✅ | — | — | ◐ | — | — | — | — | ◐ | 58% |
| Action Button | ✅ | — | — | — | ✅ | — | — | — | ✅ | 68% |
| Basic Shape | ✅ | — | — | — | ✅ | — | — | — | ◐ | 56% |
| Image | ✅ | — | — | — | — | — | — | — | ◐ | 66% |
| Text Box | ✅ | — | — | ◐ | — | — | — | — | ◐ | 63% |
| Python Visual | ✅ | — | — | — | — | — | — | — | ◐ | 63% |
| R Visual | ✅ | — | — | — | — | — | — | — | ◐ | 63% |

*Notes: **Frame** = title, background, border, drop shadow, visual header,
padding, **divider**, **spacing** and **general** (alt text / responsive) —
generic overrides on every visual. The **Card/KPI/Gauge** column tracks each
visual's specialized cards — e.g. Card's value/label live under **Labels**; its
`wordWrap` card is what's still ☐. **Table** = gridlines, headers, values,
totals / subtotals, banded rows, **data bars**, sparklines, column sizing and the
built-in **style preset**. **Colors** = per-series / default data point,
sentiment, ribbon bands, pie slices, shape fills, map data points. **Other** =
reference lines, trend, **ratio line** (scatter), **plot-area transparency**,
**data & header tooltips** (all visuals), **small multiples** (cartesian charts),
and the visual-specific cards for buttons / shapes / trees / maps / images
(Stages 4-7).*

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
