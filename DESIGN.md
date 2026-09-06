---
name: Power BI Theme Creator
description: A focused desktop tool for visually designing Power BI themes
colors:
  accent-red: "#D64550"
  accent-green: "#1AAB40"
  text-primary: "#252423"
  border-subtle: "#888888"
  surface-background: "#FFFFFF"
  text-strong: "#000000"
rounded:
  sm: "4px"
typography:
  body:
    fontFamily: "Segoe UI, Arial, sans-serif"
    fontSize: "11pt"
    fontWeight: 400
    lineHeight: 1.4
  monospace:
    fontFamily: "Courier New, monospace"
    fontSize: "10pt"
    fontWeight: 400
    lineHeight: 1.2
components:
  button-primary:
    backgroundColor: "{colors.accent-green}"
    textColor: "#FFFFFF"
    padding: "6px 16px"
    rounded: "{rounded.sm}"
  button-secondary:
    backgroundColor: "{colors.surface-background}"
    textColor: "{colors.text-primary}"
    padding: "6px 16px"
    rounded: "{rounded.sm}"
  status-custom:
    textColor: "{colors.accent-green}"
  status-default:
    textColor: "{colors.accent-red}"
---

# Design System: Power BI Theme Creator

## Overview

**Creative North Star: "The Craftsperson's Workshop"**

This is a focused, utilitarian workspace where theme designers work with precision and clarity. Like a well-organized craftsperson's bench, every tool has its place and purpose. The interface prioritizes function over flourish: clean layouts, clear groupings, and immediate visual feedback so users stay immersed in their creative task. The editing experience is tactile and responsive—every color pick, every font choice registers instantly in the live preview.

**Key Characteristics:**
- **Immediate feedback** — Users see changes in real-time; no delays between edit and preview
- **Clear visual hierarchy** — Information grouped logically (General, Structural colours, Data colours, Text classes, Visual styles)
- **Functional transparency** — JSON preview always visible; users understand what their theme will export
- **Precise controls** — Color swatches, font dropdowns, size spinners are direct and purposeful
- **Status at a glance** — Visual checklist shows which elements are customized (✓) and which use defaults (✗)

## Colors

The palette is minimal and functional. Accents signal status and interactivity; neutrals provide the working surface.

### Primary
- **Accent Green** (#1AAB40): Marks a customized or active state (✓ in the visual checklist; OK/Save buttons). Used sparingly to highlight completed customization.

### Secondary
- **Accent Red** (#D64550): Marks an uncustomized or warning state (✗ in the visual checklist). Draws attention to elements that need work.

### Neutral
- **Text Primary** (#252423): Labels, form text, dialog content. Dark enough for readability on white; warm enough to feel less harsh than pure black.
- **Text Strong** (#000000): Borders, strong emphasis, rare use.
- **Border Subtle** (#888888): Form borders, divider lines. Recessive, doesn't compete with content.
- **Surface Background** (#FFFFFF): Canvas for the editor and all input fields. Clean, infinite space for the form.

### Named Rules

**The Status Rule.** Customized = green (✓), Unchecked = red (✗). No other uses of these colors. They are diagnostic, not decorative.

## Typography

Two font families serve distinct roles: UI copy uses the system font stack for clarity and familiarity; JSON preview uses monospace for technical accuracy.

**Display Font:** Segoe UI, Arial, sans-serif (fallback to system)
**Monospace Font:** Courier New, monospace

**Character:** Familiar, readable, no personality. The focus is the user's data and their theme, not the interface.

### Hierarchy
- **Body** (11pt, regular, 1.4 line-height): Labels, button text, form copy. The main voice. Sufficient size for comfortable reading; adequate spacing between lines so the form doesn't feel cramped.
- **Monospace** (10pt, regular, 1.2 line-height): JSON preview. Tight leading to fit more content; fixed-width so hex values and JSON structure remain readable.

### Named Rules

**The Clarity Rule.** No font weights beyond regular (400) and bold (700). No sizes below 10pt. Typography serves legibility, not decoration.

## Layout

The interface is a **left-right splitter**: the left pane contains the editable form (scrollable); the right pane holds a live JSON preview (read-only monospace text).

- **Left pane (editor):** Scrollable form layout with grouped sections (General, Structural colours, Data colours, Text classes, Visual styles). Sections use `QGroupBox` for visual grouping. Form fields are arranged vertically for scan-ability.
- **Right pane (preview):** Monospace text area showing the exported theme JSON. Updates on every edit (no save/refresh needed).
- **Splitter ratio:** 3:2 (editor gets 60%, preview gets 40%).
- **Window size:** 1000px × 720px baseline; resizable.
- **Spacing:** Qt default (form layout margins ~8-12px); section group boxes have internal padding.

Form elements align left; controls are grouped in horizontal rows (e.g., font dropdown + size spinner + color button on one row for TextClassEditor).

## Elevation & Depth

**No shadows.** The interface is flat. Depth is conveyed through **layering and grouping**: grouped sections (QGroupBox with borders) sit atop the form background. Color buttons use a subtle border (1px solid #888) to signal clickability. Dialogs appear as modal overlays.

Visual hierarchy relies on layout, grouping, and color accents rather than shadow depth.

## Shapes

**Minimal radius.** Color buttons use a small border-radius (4px) to soften edges without calling attention. Otherwise, inputs and controls use the Qt default (typically square corners). The focus is on content and precision, not rounded aesthetics.

Buttons are rectangular; color buttons are slightly wider (120px × 28px) to accommodate hex-value display and remain clickable.

## Components

### Color Button
**Signature component of the system.** A `QPushButton` that displays the hex value and a live color swatch as its background. Opens a native color picker on click.

- **Shape:** 120px wide × 28px tall; 4px border-radius; 1px solid #888 border
- **Appearance:** Swatch fills background; hex value (#XXXXXX) displayed as text. Text color (black or white) chosen for contrast against the swatch.
- **On click:** Opens `QColorDialog` (native system color picker)
- **Feedback:** Text updates instantly; preview re-renders on every change (no save button)

### Data Colours Editor
A list of color buttons with add/remove controls.

- **Add button:** "+ Add colour" (text button, secondary style)
- **Remove button:** "- Remove last" (text button, secondary style)
- **Rows:** Each color is numbered (1., 2., 3., ...) and shown as a ColorButton. Numbering is implicit order in the theme's data color array.

### Text Class Editor
Horizontal row of three controls: font dropdown, size spinner, color button.

- **Font dropdown:** `QFontComboBox` (system fonts)
- **Size spinner:** `QSpinBox` range 4–120pt, displays value with " pt" suffix
- **Color button:** ColorButton for the text color
- **Arrangement:** Flex layout; font stretches to fill available space, size and color buttons are right-aligned

### Visual Styles Checklist
A scrollable grid of Power BI visual types with customization status.

- **Left column (clickable label):** Visual name as a flat QPushButton (text-align left; no border)
- **Right column (status indicator):** Single character: "✓" (green, #1AAB40) if customized, or "✗" (red, #D64550) if default
- **On click:** Emits `visualRequested(visual_key)` to open the style editor dialog

### Visual Style Dialog
Modal dialog for editing per-visual overrides (background, border, title, data labels, legend, and raw JSON).

- **Structure:** Vertical sections (Background, Border, Title, Data Labels, Legend, Advanced JSON); each section is a `QGroupBox` with a checkbox to toggle the override, followed by editable fields
- **Fields:** Color buttons, spinners, font/position dropdowns, plain-text JSON area
- **Buttons:** "Clear All Overrides" (secondary button); "OK" / "Cancel" (dialog standard buttons)

## Do's and Don'ts

### Do:
- **Do** show the live JSON preview on every edit. The user never wonders what their theme will look like exported.
- **Do** use green (✓, #1AAB40) and red (✗, #D64550) *only* for status indicators. Don't use them elsewhere.
- **Do** arrange form controls horizontally when grouped (e.g., font + size + color on one row).
- **Do** group related fields in `QGroupBox` with a clear label (General, Structural colours, etc.).
- **Do** keep text size ≥10pt and line-height ≥1.2 for readability in monospace preview.
- **Do** enable/disable related controls together (e.g., if "Override" checkbox is unchecked, disable the color and transparency fields).

### Don't:
- **Don't** add shadows or blur effects. Depth comes from grouping and borders.
- **Don't** use decorative colors or accents beyond green/red status. The focus is the user's data.
- **Don't** change font weights beyond regular (400) and bold (700).
- **Don't** hide or defer the JSON preview. It's the contract with the user: "this is what you're exporting."
- **Don't** add animations or transitions. Immediate, instant feedback is more important than polish.
- **Don't** expand the UI beyond the defined sections (General, Structural, Data colours, Text, Visual styles). Avoid feature creep in the interface.
