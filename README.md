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
- **Open / Save** existing `.json` themes (round-trips cleanly).
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
theme.save("corporate.json")
```

## Project layout

```
main.py                     # GUI entry point
pbitheme/
    __init__.py
    model.py                # PowerBITheme, TextClass — the GUI-free model
    gui/
        __init__.py
        main_window.py       # MainWindow: editor form + live JSON preview
        widgets.py           # ColorButton, DataColorsEditor, TextClassEditor
requirements.txt
```

## Architecture

- **`PowerBITheme`** owns all editable state and knows how to serialise
  itself to / from the Power BI theme JSON structure.
- **`TextClass`** is a small value object for a single typography class.
- The GUI widgets each expose a `changed` signal; `MainWindow` collects the
  widget state into a fresh `PowerBITheme` and re-renders the preview on every
  edit, keeping the model and the view decoupled.
