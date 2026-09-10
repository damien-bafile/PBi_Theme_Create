---
target: the app (main window + visual style dialog)
total_score: 30
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 1
target_identity: "file:/home/daimyo/Dev/PBi_Theme_Create/pbitheme/gui/main_window.py"
target_fingerprint: "sha256:3a0b4d18061b43f50b5e1e06c3d76bf97d55d41bd2aff1d3a0847345fc629778"
target_path: /home/daimyo/Dev/PBi_Theme_Create/pbitheme/gui/main_window.py
timestamp: 2026-09-09T12-09-44Z
slug: pbitheme-gui-main-window-py
---
Method: dual-agent (A: design review · B: detector + evidence)

# Critique (3rd run) — Power BI Theme Creator (PySide6/Qt desktop · Operate mode)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Status bar, `[*]` dirty title, dual live preview all present — but the headline checklist's status is clipped to "✗ Defa", so at-a-glance status breaks exactly where it matters. |
| 2 | Match System / Real World | 3 | Plain-language relabels + tooltips are strong; residual jargon survives only in Advanced JSON. |
| 3 | User Control and Freedom | 3 | Undo/redo now spans colour/name/data/text + Cancel + unsaved guard — but "Clear All Overrides" is irreversible inside the dialog. |
| 4 | Consistency and Standards | 3 | Uniform ColorButton/QGroupBox/shortcuts; named presets add an undeclared mode. |
| 5 | Error Prevention | 3 | Discard guard defaults to Cancel, Advanced JSON validated on OK; destructive Clear All has no confirm. |
| 6 | Recognition Rather Than Recall | 3 | Live preview + visible hex + filter box; the 2-row cramped visual list forces blind scrolling through 50+ types. |
| 7 | Flexibility and Efficiency | 3 | Shortcuts, filter, presets, Save vs Save As; no keyboard path to open a visual, no multi-apply. |
| 8 | Aesthetic and Minimalist | 3 | Clean overall, but collapsed override sections render as large near-empty boxes and the nested tiny scroll looks broken. |
| 9 | Error Recovery | 4 | Open/Save/Validate/Invalid-JSON dialogs are specific and actionable with next steps. |
| 10 | Help and Documentation | 2 | Tooltips + the "written as a set" note help; no onboarding, empty-state, or docs. |
| **Total** | | **30/40** | **Good** — up from 27; one self-inflicted regression is the main wound. |

## Design Specificity Verdict — **PASS (specific and intentional)**
- **A:** Reads unmistakably as a purpose-built PBI theme editor — dual live preview, ✓/✗ status system, live hex on the swatch, domain-accurate taxonomy — matching DESIGN.md's "Craftsperson's Workshop". Deliberately plain (Fusion, flat) by intent; the forced light palette is a real, verified commitment. One drift: named presets exceed DESIGN.md's "no feature creep" rule (justified but undeclared).
- **B:** `impeccable detect` → `[]` (exit 0) on both `pbitheme` and `.` — **inapplicable, not clean**: HTML/CSS/DOM scanner, 0 app-authored markup (only a stray PyInstaller `build/` xref, which it did not even flag).
- **Overlays:** none — Qt desktop, no DOM/dev server.
- **Corrected false positive:** B estimated white hex text ~3:1 on the `#118DFF`/`#1AAB40`/`#D64550` swatches — but the rendered text is **black** (WCAG picker), which passes (≈6.3 / 6.9 / 4.8:1). Not a defect.

## Overall Impression
Materially better than the last pass and now solidly "Good": trustworthy dual preview, a correct WCAG-backed status system, a real unsaved-changes safety net, and working undo/redo. The one real wound is a **regression I introduced last pass**: moving the Visual Styles checklist up left it cramped in a nested scroll with a horizontal scrollbar that truncates the status column — the headline capability looks broken. Fixing that single P1 is most of the remaining distance.

## What's Working
1. **Trustworthy dual live preview** — the dialog preview renders from the *same* `_build_overrides()` path that saves, so what you see is what exports.
2. **The status system is done right** — glyph **plus** WCAG-AA colour (not colour-only), and ✓ now honestly means the user changed something (`_existing_was_empty`/`_user_touched`).
3. **A real safety net** — unsaved guard (`[*]`, `closeEvent`, Discard-defaults-to-Cancel), Save vs Save As, and a pre-edit-baseline undo/redo that now covers colour/name/data/text.

## Priority Issues

**[P1] The headline feature is visually crippled — cramped, double-scrolled, truncated.** *(regression from last pass, verified)* The Visual Styles list shows only ~2 rows with **both** a vertical and a horizontal scrollbar, and the right-hand status is clipped to "✗ Defa". Root cause: `VisualStylesChecklist` nests its own `QScrollArea` inside the outer form scroll with no minimum height (so Qt collapses it), and the 2-column grid is wider than the ~450px left pane, forcing horizontal scroll that eats the status column. *Fix:* drop the inner scroll (or give it an 8–10 row min height) and lay the list out in **one column** in the narrow pane; give status a fixed width and never truncate it (elide the visual name instead if anything).

**[P2] "Clear All Overrides" is destructive with no confirm and no in-dialog undo.** `_clear_all()` unchecks all sections, resets the formatter and blanks the Advanced JSON in one click; undo/redo only records on dialog accept, so a mis-click is unrecoverable until OK/Cancel. *Fix:* a confirmation ("Clear all overrides for this visual?") or a session-local undo of the last clear.

**[P3] Collapsed Generic Override sections waste space / read as empty.** Each collapsed section is a large group box holding only an "Override" checkbox in whitespace — the opposite of the compact intent. *Fix:* when collapsed, render a slim single-line row (checkbox inline with the section title), expanding only on toggle.

**[P3] Presets are an undeclared mode with no explanation.** `+ New` exceeds DESIGN.md's defined sections and offers no hint that it maps to Power BI's named `styleName` entries. *Fix:* a one-line tooltip/hint on the preset row.

## Persona Red Flags
- **Alex (brand-focused):** hits the cramped/truncated visual list first and may think the visual-styles feature is broken — the very thing they came for.
- **Jordan (power user):** loves filter/presets/shortcuts/Advanced JSON; annoyed by no keyboard path to open a visual, no multi-apply, the no-confirm Clear All, and the sparse override tab.
- **Sam (accessibility):** wins — WCAG-AA glyph-backed status, explicit tab order, accessible names. Risks — the truncated status text and nested double-scroll are hostile to keyboard-only / magnifier / large-text use.

## Minor Observations
- `_update_title` always appends `[*] — Power BI Theme Creator`; verify the "Untitled" path reads well before a file exists.
- Dialog preview is fixed 250×200 while its widget min is 250×250 — a small letterbox gap.
- Focus opens on the tab bar rather than the first field (reasonable, but keyboard users must tab in).

## Questions to Consider
1. If the Visual Styles checklist is the headline capability, why does it get the *smallest* pane — should it be a first-class panel or its own tab rather than a squeezed box?
2. The dialog now exposes 14 generic sections + per-visual formatting + raw JSON + presets — has "surface only the controls users need" quietly inverted into "surface everything Power BI can do"?
3. Undo/redo spans main-window edits but stops at the dialog boundary — shouldn't editing a visual's style be one edit that Ctrl+Z can reverse?
