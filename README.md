# PBi_Theme_Create

A small **Power BI theme creator**: a Python + Qt (PySide6) desktop app that
lets you configure a report theme visually and export it as a Power BI
`*.json` theme file. Built with an object-oriented design that cleanly
separates the theme model from the GUI.

## Features

- **Live JSON preview** — the exported theme updates as you edit.
- **Data colours** — add / remove swatches, each with a colour picker.
- **Structural colours** — foreground, background, table accent, good /
  neutral / bad.
- **Text classes** — font face, size and colour for `title`, `header`,
  `callout` and `label`.
- **Visual styles** — a full `visualStyles` block like the
  [deldersveld / MattRudy theme templates](https://github.com/MattRudy/PowerBI-ThemeTemplates).
  Enable formatting cards (background, border, title, data labels, category
  labels) and target **all visuals (`*`)** or any of the **52 visuals** the
  Power BI schema defines (every chart, card, slicer, table, map, AI, script
  and navigation visual). Colours are emitted in Power BI's
  `{"solid": {"color": "#..."}}` form.
- **Open / Save** existing `.json` themes — **lossless**: any keys, text
  classes, visual selectors, cards or properties the editor doesn't model are
  preserved verbatim, so opening a hand-crafted theme and saving it keeps
  everything you didn't touch.
- **Schema validation** — validate the theme against the official Power BI
  report theme JSON schema (bundled from Microsoft's
  `powerbi-desktop-samples`, currently **v2.157**) via **File → Validate** or
  the **Validate** button. Output is verified to conform.
- The theme model (`pbitheme.model`) has **no GUI dependency**, so you can
  generate themes from scripts too.

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

# Detailed visualStyles: turn on the background card for all visuals
glob = theme.visual_styles[0]            # the "*" target
glob.enabled["background"] = True
glob.values["background"] = {"show": True, "color": "#0B3D91", "transparency": 0}

theme.save("corporate.json")
```

This produces the same nested shape as the template repo, e.g.:

```json
"visualStyles": {
  "*": { "*": { "background": [
    { "show": true, "color": { "solid": { "color": "#0B3D91" } }, "transparency": 0 }
  ] } }
}
```

## Project layout

```
main.py                     # GUI entry point
pbitheme/
    __init__.py
    model.py                # PowerBITheme, TextClass — the GUI-free model
    validate.py             # validate a theme against the bundled PBI schema
    schema/                 # official Power BI report theme JSON schema
    gui/
        __init__.py
        main_window.py       # MainWindow: editor form + live JSON preview
        widgets.py           # ColorButton, DataColorsEditor, TextClassEditor,
                             #   VisualStyleEditor, ...
requirements.txt
```

## Conformance

The generated JSON is validated against the official
[Power BI report theme JSON schema](https://github.com/microsoft/powerbi-desktop-samples/tree/main/Report%20Theme%20JSON%20Schema)
(Draft 7). A full-feature theme validates with zero errors against schema
versions 2.126, 2.143 and 2.157. Notably, `labelDisplayUnits` is emitted as an
**integer** (`0`=Auto, `1`=None, `1000`=Thousands, …) as the current API
requires — older community templates used a string here, which the current
schema rejects.

### Coverage

- **Visual targets:** all **52** visuals defined by the schema are selectable
  (guarded by a test that fails if the schema adds one we don't list).
- **Formatting cards:** most visuals expose a set of five common cards —
  background, border, title, data labels and category labels. **Table, Matrix
  and Slicer have detailed, dedicated card sets:**
  - **Table** (`tableEx`): background, border, title, grid, column headers,
    values, total, style preset.
  - **Matrix** (`pivotTable`): background, border, title, grid, column headers,
    row headers (stepped layout, +/- buttons), values (banded rows, values on
    rows), subtotals, grand total, style preset.
  - **Slicer** (`slicer`): background, border, title, general (orientation,
    outline), header, items, selection controls, slider.

  **Charts have dedicated card sets** too:
  - **Cartesian charts** (column, bar, line, area, their clustered/stacked/100%
    variants, combo, ribbon, waterfall, scatter): background, border, title,
    legend, X axis, Y axis (each with gridlines and axis title), data colours,
    data labels.
  - **Circular / part-to-whole** (pie, donut, treemap, funnel): background,
    border, title, legend, data colours, data labels (no axes).

  The model is schema-driven (`CARD_SCHEMA` / `VISUAL_CARD_SCHEMA`), so more
  visuals can be given dedicated card sets the same way.

Run the conformance tests with:

```bash
python -m unittest discover -s tests
```

You can validate from scripts too:

```python
from pbitheme.model import PowerBITheme
from pbitheme.validate import validate_theme

errors = validate_theme(PowerBITheme("Demo").to_dict())
assert errors == []
```

## Architecture

- **`PowerBITheme`** owns all editable state and knows how to serialise
  itself to / from the Power BI theme JSON structure.
- **`TextClass`** is a small value object for a single typography class.
- The GUI widgets each expose a `changed` signal; `MainWindow` collects the
  widget state into a fresh `PowerBITheme` and re-renders the preview on every
  edit, keeping the model and the view decoupled.
