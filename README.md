# PBi_Theme_Create

[![Tests](https://github.com/damien-bafile/PBi_Theme_Create/actions/workflows/tests.yml/badge.svg)](https://github.com/damien-bafile/PBi_Theme_Create/actions/workflows/tests.yml)

A **Power BI theme creator**: a Python + Qt (PySide6) desktop app that lets you
configure a report theme visually — with a **live preview of every visual** — and
export it as a Power BI `*.json` theme file. The theme model is GUI-free, so you
can also generate themes from scripts.

## Features

- **Full visual coverage** — every one of the **52** visual types Power BI's
  theme schema defines is themeable (the editor lists **54** entries, exposing
  both the schema and friendly names for Table and Matrix). **50** entries have
  dedicated structured formatting; the other **2** use the generic overrides.
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
- **Light / dark mode** — toggle via **Edit → Dark Mode** (remembered between
  sessions); status cues stay legible in both. Plus per-visual **in-dialog
  undo/redo** (Ctrl+Z/Ctrl+Y) and a dismissible first-run guide.
- **Packaged & tested** — installs as a `pbitheme` command (`pip install -e .`),
  runs headless in CI on Python 3.12, and a build workflow produces a
  Windows `.exe` plus wheel/sdist on demand.

## Install & run

**Windows users** can grab the standalone `PowerBI_Theme_Creator.exe` (no Python
needed) from the [latest release](https://github.com/damien-bafile/PBi_Theme_Create/releases/latest).

From source:

```bash
pip install -e .        # installs PySide6 + jsonschema
python main.py          # or: pbitheme  /  python -m pbitheme
```

Requires Python 3.12+ and PySide6.

## Using the theme in Power BI

1. Save your theme from the app (**File → Save As...**).
2. In Power BI Desktop: **View → Themes → Browse for themes** and select the
   generated `.json` file.

## Schema validation

The exported theme can be validated against the **official Power BI report
theme JSON schema** (bundled from Microsoft's `powerbi-desktop-samples`,
currently **v2.157**) via **File → Validate** (Ctrl+L). **File → Check for
Schema Update…** checks Microsoft's repo for a newer schema version. It is also
scriptable and covered by tests:

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

## Releasing

Releases are cut by the **Build** workflow (`.github/workflows/build.yml`),
which builds the Windows `.exe` and the wheel/sdist and publishes a GitHub
Release with those files attached. There are two ways to trigger it:

- **Push a version tag** (from a machine with tag-push rights):

  ```bash
  git tag v0.1.0
  git push origin v0.1.0
  ```

- **Run it manually** — GitHub → **Actions → Build → Run workflow**, and set the
  **version** input (e.g. `v0.1.0`). This creates the tag on the chosen commit,
  builds the artifacts, and publishes the release. Leaving **version** blank
  just builds the artifacts (downloadable from the run) without releasing.

Before releasing, bump `version` in `pyproject.toml` to match the tag. Release
notes are auto-generated from merged PRs; edit them on the release afterwards if
needed. The published assets are `PowerBI_Theme_Creator.exe`,
`pbitheme-<version>-py3-none-any.whl` and `pbitheme-<version>.tar.gz`.

## Power BI theme coverage

**Every visual is covered.** The Power BI report theme schema (v2.157) defines
**52** visual types, and the editor makes all of them selectable — listing
**54** entries because it exposes both the schema and friendly names for Table
(`tableEx` / `table`) and Matrix (`pivotTable` / `matrix`). **52** of the
editor's entries have dedicated, structured formatting sections; the remaining
**2** — Python and R — are themed through the
generic overrides (title, background, border, drop shadow, padding, tooltips, …).
Everything exports to real Power BI theme *cards*, is validated against the
bundled schema, and round-trips (export → import → export is stable). Anything
not yet in a structured section can still be set through the **Advanced JSON**
tab.

Card-level depth within each visual (every property of every card) remains an
ongoing sub-goal, tracked in the stages and matrix below. The only two
generic-only visuals left, **R** and **Python**, genuinely expose nothing beyond
frame styling — the schema gives them just `provider` / `source`, so there is
nothing more to surface. (**Key Drivers**, **Q&A** and **Azure Maps** graduated
to structured sections in Stages 10–12 below.)

**Legend:** ✅ done &nbsp;·&nbsp; ◐ partial &nbsp;·&nbsp; ☐ planned &nbsp;·&nbsp; — not applicable to this visual

Most fields update the **live preview**; a few (marked *export-only* in the
stages below) are exported as valid Power BI cards but can't be meaningfully
shown in a simplified mockup (e.g. font family, word wrap, page/report cards).

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
- **Stage 8 — Complete the visual set — ✅ complete.** Added every remaining
  schema visual: **Stacked Area** & **100% Stacked Area** charts (cartesian
  config); **Page** & **Report** (wallpaper, filter pane, filter cards →
  `outspace` / `outspacePane` / `filterCard`); **Card (new)** (callout value,
  category label, accent bar); the new **Slicer / List slicer / Text slicer**
  (header + items); **Page** & **Bookmark navigators** (button fill / text /
  outline); **Scorecard** (column headers, metric name, current value, target);
  and **Filter**, **Group** & **Paginated (RDL)** (container background /
  border). Also fixed the **R-visual** mapping (`rVisual → scriptVisual`) so R
  themes actually apply. All export-only, schema-valid and round-tripping.
- **Stage 9 — Typography depth — ✅ complete.** Property-level depth *within*
  the chart cards already emitted: **bold / italic** (live previewed) and **font
  family** on the X-axis, Y-axis, legend and data labels of every cartesian chart
  (bar / column / line / area / stacked-area / combos / stacked / ribbon /
  scatter / waterfall), plus value-axis **display units** and **decimal
  precision**. Extended the same **bold / italic / font family** to the **pie /
  donut / treemap** legends & data labels and the **funnel** data labels.
  Centralised in the shared axis / legend / label renderers, so all these visuals
  gained it at once.
- **Stage 10 — Key Drivers structured section — ✅ complete.** Promoted **Key
  Drivers** from generic-only to a dedicated section covering all **8** of its
  schema `fill` colours: **primary**, **secondary**, **default** and
  **reference-line** (Analysis Colors); **font**, **primary-font** and
  **secondary-font** (Text); and **background** (canvas). Primary / secondary /
  background are **live-previewed** in the influencer mockup; the rest are valid
  export-only cards. All emit onto the visual's catch-all `*` card as flat fills
  (per the schema), validate, and round-trip.
- **Stage 11 — Q&A structured section — ✅ complete.** Promoted **Q&A** from
  generic-only to a dedicated section covering all **28** of its themeable schema
  properties across five groups — **Question** (font colour / family / size +
  bold / italic / underline), **Input Box** (background, suggestion / hover,
  submit button, and the accepted / warning / error underline colours),
  **Restatement**, **Result Card** and **Header** (each with font colour / family
  / size + emphasis). Background, question-font colour and the hover accent are
  **live-previewed**; the rest are valid export-only cards. Like Key Drivers,
  everything emits onto the visual's `*` card (per the schema), validates, and
  round-trips.
- **Stage 12 — Azure Maps structured section — ✅ complete.** Promoted **Azure
  Maps** — the last visual with real themeable depth — from generic-only to a
  colours + typography section covering all **20** of its schema `fill` colours
  plus font family / size and label emphasis (**27** fields) across seven groups:
  **Data Points**, **Bubbles**, **Clusters**, **Data Labels**, **Category
  Labels**, **Heat Map** (low / center / high gradient) and **Reference Layer**
  (bubbles / lines / polygons / unmapped objects). The bubble fill
  (`defaultColor`) is **live-previewed** on the map pins; the rest are valid
  export-only cards. Emits onto the `*` card, exported under the schema name
  `azureMap`, validates and round-trips. (Azure's ~40 map-behaviour toggles —
  traffic, boundaries, navigation, world-wrap — stay in Advanced JSON by design:
  a theme should brand the visual, not dictate analytical map behaviour.)
- **Stage 13 — Line & marker depth — ✅ complete.** With every visual now
  structured, this begins the card-level depth pass. Added a **Lines & Markers**
  section to the six **line / area / combo** charts (the Power BI `lineStyles`
  card): default **line width**, **line style** (solid / dashed / dotted),
  **interpolation** (linear / smooth / stepped), and **markers** (show / shape /
  size / colour). Export-only (the simplified mockup can't render stroke width or
  marker shape), schema-valid, round-tripping, and gated so bar / column charts
  don't emit it. Card / property names ground-truthed against Microsoft-endorsed
  theme templates (the marker toggle is `showMarker`).
- **Stage 14 — Axis-title, slicer & table/matrix depth — ✅ complete.** A batch
  of card-level additions onto cards the app already emits (so the mappings are
  proven, not inferred): **axis titles** gain **bold / italic / font family** on
  the X and Y axes of every cartesian chart (`categoryAxis` / `valueAxis`,
  siblings of the existing title colour / size); **Slicer** gains **font family /
  italic / underline** on its header and items cards; **Table / Matrix** gain a
  banded **alternate-row font colour** (`values.fontColorSecondary`) and the
  matrix **expand / collapse (+/-) icons** (show / colour / size on `rowHeaders`,
  matrix-only). All export-only, schema-valid and round-tripping. (The matrix
  expand/collapse card placement is inferred — the schema flattens card names
  away — so if Power BI Desktop reads those from a different card, only that card
  name needs adjusting.)
- **Stage 15 — Gridline & data-label detail — ✅ complete.** More card-level depth
  on cards the app already emits: cartesian **gridline transparency** (on
  `valueAxis`, sibling of the existing gridline colour / thickness) and
  **data-label background colour + transparency** (on the `labels` card, filling
  the gap where the app toggled *Show Background* but never set its colour). All
  export-only, schema-valid and round-tripping.
- **Not themeable — stays in Advanced JSON.** The per-visual navigation/link card
  (`visualLink`) is genuinely instance-specific — it targets a bookmark, report
  section or URL a theme can't know — so it has no structured field by design.

### Coverage matrix

| Visual | Frame | Axes | Legend | Labels | Colors | Table | Card/KPI/Gauge | Slicer | Other | % |
|---|---|---|---|---|---|---|---|---|---|---|
| Bar Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ✅ | 70% |
| Column Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ✅ | 70% |
| Clustered Bar Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | 70% |
| Clustered Column Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | 70% |
| 100% Stacked Bar Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ✅ | 70% |
| 100% Stacked Column Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ✅ | 70% |
| Line Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | 76% |
| Area Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | 76% |
| Stacked Area Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | 76% |
| 100% Stacked Area Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | 76% |
| Line & Clustered Column Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | 76% |
| Line & Stacked Column Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | 76% |
| Ribbon Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ✅ | 70% |
| Scatter Chart | ✅ | ✅ | ✅ | ✅ | ◐ | — | — | — | ✅ | 73% |
| Waterfall Chart | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ◐ | 75% |
| Pie Chart | ✅ | — | ✅ | ✅ | ◐ | — | — | — | ◐ | 70% |
| Donut Chart | ✅ | — | ✅ | ✅ | ◐ | — | — | — | ◐ | 70% |
| Treemap | ✅ | — | ✅ | ◐ | ☐ | — | — | — | ◐ | 65% |
| Funnel | ✅ | ☐ | — | ✅ | ✅ | — | — | — | ◐ | 67% |
| Gauge | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | — | ◐ | 74% |
| Card | ✅ | — | — | ✅ | — | — | ☐ | — | ◐ | 65% |
| Multi-row Card | ✅ | — | — | ✅ | — | — | ☐ | — | ◐ | 62% |
| KPI | ✅ | — | — | — | — | — | ✅ | — | ◐ | 72% |
| Table | ✅ | — | — | — | — | ✅ | — | — | ◐ | 73% |
| Table (Extended) | ✅ | — | — | — | — | ✅ | — | — | ◐ | 73% |
| Matrix | ✅ | — | — | — | — | ✅ | — | — | ◐ | 72% |
| Pivot Table | ✅ | — | — | — | — | ✅ | — | — | ◐ | 72% |
| Slicer | ✅ | — | — | — | — | — | — | ✅ | ◐ | 70% |
| Map | ✅ | — | ✅ | ✅ | ◐ | — | — | — | ◐ | 64% |
| Filled Map | ✅ | — | ✅ | ✅ | ✅ | — | — | — | ◐ | 68% |
| Shape Map | ✅ | — | ✅ | — | ◐ | — | — | — | ◐ | 58% |
| Azure Maps | ✅ | — | — | ◐ | ✅ | — | — | — | ◐ | 68% |
| Decomposition Tree | ✅ | — | — | ◐ | — | — | — | — | ◐ | 53% |
| Key Drivers | ✅ | — | — | ◐ | ✅ | — | — | — | ◐ | 72% |
| Q&A | ✅ | — | — | ◐ | ✅ | — | — | — | ◐ | 73% |
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
**line width / style / interpolation + markers** (line / area / combo charts),
**data & header tooltips** (all visuals), **small multiples** (cartesian charts),
and the visual-specific cards for buttons / shapes / trees / maps / images
(Stages 4-7).*

### Additional visuals (Stage 8)

These don't map onto the chart-oriented columns above; each has its own
dedicated, export-only cards (schema-valid, round-tripping):

| Visual | Dedicated cards |
|---|---|
| Card (new) — `cardVisual` | callout value, category label, accent bar |
| Slicer (new) — `advancedSlicerVisual` | header, items |
| List Slicer — `listSlicer` | header, items |
| Text Slicer — `textSlicer` | header, items |
| Page Navigator — `pageNavigator` | button fill, text, outline |
| Bookmark Navigator — `bookmarkNavigator` | button fill, text, outline |
| Scorecard (Goals) — `scorecard` | column headers, metric name, current value, target |
| Filter — `filter` | header, items |
| Group — `group` | container background, border |
| Paginated (RDL) — `rdlVisual` | container background, border |
| Page — `page` | wallpaper, filter pane, filter cards |
| Report — `report` | filter pane, filter cards |

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
