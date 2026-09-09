---
target: the app (main window + visual style dialog)
total_score: 25
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 2
target_identity: "file:/home/daimyo/Dev/PBi_Theme_Create/pbitheme/gui/main_window.py"
target_fingerprint: "sha256:19e16ab10c504276ac654a9bf418f7975927a8d76311c1c6d8f86fd75cd94dd3"
target_path: /home/daimyo/Dev/PBi_Theme_Create/pbitheme/gui/main_window.py
timestamp: 2026-09-09T10-16-48Z
slug: pbitheme-gui-main-window-py
---
Method: dual-agent (A: design review · B: detector + evidence)

# Critique — Power BI Theme Creator (PySide6/Qt desktop · Operate mode)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Live preview + JSON + status bar are strong; title bar never shows the current filename or an unsaved-changes marker. |
| 2 | Match System / Real World | 3 | Fluent Power BI vocabulary, but menus say "Open"/"Save As…" though the product's mental model is import/export to Power BI. |
| 3 | User Control and Freedom | 2 | Undo/redo and Cancel exist, but New / Open / Quit discard the whole theme with no confirmation. |
| 4 | Consistency and Standards | 2 | Visual Formatting has no per-field opt-in while Generic Overrides gates every section behind a checkbox — two opposite "what's an override" models. |
| 5 | Error Prevention | 2 | No unsaved-changes guard on destructive actions; unchecking a Generic-Override section does not actually remove it (the JSON base retains it), so checkbox state and reality diverge. |
| 6 | Recognition Rather Than Recall | 3 | Swatches show hex, checklist shows ✓/✗ — but the status colours are tuned "for white" and wash out on the dark chrome the app actually renders in. |
| 7 | Flexibility and Efficiency | 3 | Shortcuts, style presets, .pbix/.pbit import, schema-validate = real power; no toolbar, save/export is menu-only, no fast re-save. |
| 8 | Aesthetic and Minimalist | 3 | Generally clean; Generic Overrides stacks 14 sections and the right preview overflows horizontally (Table + Card/KPI clipped). |
| 9 | Error Recovery | 3 | Schema validation lists issues in detail; load/save failures show dialogs but offer no remediation. |
| 10 | Help and Documentation | 1 | No in-app help, tooltips, or first-run hint anywhere. |
| **Total** | | **25/40** | **Acceptable (~62%)** — solid domain core, undesigned shell + destructive-path gaps. |

All ten heuristics apply to a desktop tool; none scored n/a.

## Design Specificity Verdict

**Authored for Power BI theming in substance; generic-Qt in chrome.**

**LLM assessment (A):** The *content* is unmistakably domain-built — structural-colour names lifted from the PBI schema (Foreground, Dimmed/category, Table accent, Good/Neutral/Bad), a conditional-formatting gradient row, a per-visual checklist of real PBI visual types, live SVG mockups, schema validation, and .pbix/.pbit import. `ColorButton` (hex-in-swatch, luminance-picked text, native picker) is a genuine signature component. But the *shell* is undesigned: both screenshots render in the OS **dark** Qt theme while DESIGN.md specifies a white "Craftsperson's Workshop" surface (`#FFFFFF`), and the status colours in `theme.py` are tuned (per their own code comment) "for white." The design system on paper is not the one on screen.

**Deterministic scan (B):** `impeccable detect --json pbitheme` and `… .` both returned `[]`, exit 0 — but this is **inapplicable, not clean**: the bundled detector is an HTML/CSS/DOM slop scanner and the repo has **zero** scannable markup/style files (25 .py, no .html/.css/.jsx/…). Nothing for a rule to match. No false positives possible.

**Visual overlays:** none — no web page, DOM, or dev server exists (Qt desktop), so the `detect.js` overlay and browser inspection were correctly not run. Objective evidence came from two real app screenshots instead.

## Overall Impression

The engine is excellent and the shell is unfinished. The dual live preview (main-window mockups + the dialog's `_update_preview`, both rendering from the same path that OK saves) is a genuinely strong product thesis executed correctly — WYSIWYG for exported theme JSON. What lets it down is everything around that core: it inherits the OS dark palette that contradicts its own DESIGN.md and washes out its one diagnostic signal, it clips content on first paint, and its destructive paths (New/Open/Quit) have no guard. Biggest single opportunity: **own the app's palette** so the design system is real and the ✓/✗ status is legible.

## What's Working

1. **Dual live preview with save-path fidelity.** Both the main Visual Preview tab and the dialog preview render from the same `_build_overrides()` that OK persists — "what you see is what exports." That is the whole product thesis, and it holds.
2. **`ColorButton` as a real component.** Fixed 120×28, native `QColorDialog`, hex shown as monospace, text colour auto-picked by luminance. The one place DESIGN.md is fully realized, and it feels tactile.
3. **Integration-first plumbing surfaced in the UI.** One dialog imports .pbix/.pbit/.json; "Validate against Power BI schema" (Ctrl+L) with a detailed issue list is exactly what a pro PBI dev wants and can't get in Power BI's own editor.

## Priority Issues

**[P1] The app renders on OS dark chrome, contradicting its own DESIGN.md and hiding its status signal.** `theme.py` sets status colours "for white," DESIGN.md describes a white surface, yet the app ships on dark chrome (both screenshots). The ✓Custom / ✗Default badges — the checklist's entire purpose — nearly vanish, and B measured widespread white-on-saturated-swatch contrast failures that the dark ground worsens. *Why it matters:* the design system isn't real, and the one diagnostic cue is illegible. *Fix:* force the app's own light palette per DESIGN.md via `QApplication.setPalette(...)`, or compute status/label colours against the actual background. *Command:* `/impeccable audit` (contrast), then `/impeccable polish`.

**[P1] No unsaved-changes protection.** Verified: `main_window.py` has no `closeEvent`, no dirty flag, and the title is the static "Power BI Theme Creator" (set once, never updated). New / Open / Quit discard a hand-built theme with no prompt. *Why it matters:* one Ctrl+N silently destroys work. *Fix:* track a dirty flag on edit, guard New/Open/close with a "Discard changes?" dialog, and show `"Corporate Blue* — Power BI Theme Creator"`. *Command:* `/impeccable harden`.

**[P2] Hex labels fail AA on saturated swatches.** The `0.299R+0.587G+0.114B > 140` heuristic in `ColorButton._refresh` picks white text where white only reaches ~3:1 (B measured: white on `#118DFF` ≈ 3.1–3.4:1, on `#1AAB40` ≈ 2.6–3.0:1, on `#F2C811` yellow ≈ 1.5:1 — essentially illegible). *Why it matters:* reading the exact hex is the swatch's whole job. *Fix:* replace the heuristic with a true WCAG relative-luminance comparison (pick black vs white by higher ratio); optionally a 1px text halo. *Command:* `/impeccable audit`.

**[P2] Truncation and overflow read as "broken" on first paint.** B confirmed: the dialog tab bar clips "Advanced JSON" → "Advanced J" with scroll chevrons; the main-window Visual Preview overflows horizontally so Table and Card/KPI are cut off behind a scrollbar (Card/KPI looks empty in-viewport). *Why it matters:* the first impression is "cut off," not "at a glance" — and the clipped panes hide the core payoff. *Fix:* `tabs.setUsesScrollButtons(False)` + wider min width / elide; make the preview grid scale or wrap to the pane width. (Partly a fixed-capture-size artifact — verify at a maximized window.) *Command:* `/impeccable layout` (or `/impeccable adapt` for resize behavior).

**[P2] "Customized" (✓) doesn't mean the user changed anything.** The Visual Formatting tab has no per-field opt-in, so opening a visual and clicking OK writes a full formatting object of *defaults* and flips the checklist to ✓Custom even with zero changes — while Generic Overrides demands a checkbox per section. Two contradictory override models, and the ✓ badge can't distinguish "changed" from "a value exists." *Why it matters:* the checklist's core signal is untrustworthy. *Fix:* only write fields the user actually changed (diff against defaults), and unify the opt-in model across both tabs. *Command:* `/impeccable clarify` + `/impeccable harden`.

**[P3] Axis section interleaves label and title properties.** Reading order is Title Text → Label Color → Font Size → Bold/Italic → Font Family → Title Color → Title Size — title and label attributes shuffled together, with "Font Family" of ambiguous scope. *Fix:* split "Axis title" and "Axis labels" sub-groups, consistent Font/Size/Color/Style order in each. *Command:* `/impeccable layout`.

> **Correction to Assessment A:** A raised a P1 that generic overrides are *silently dropped* on re-open+OK. I verified this against the code and it is **false** — `_on_ok` merges onto an Advanced-JSON base seeded from the existing object, so an untouched OK **retains** the override (test: `result keeps background: True`). The real, milder issue is the inverse (folded into P1/P2 above): the Override checkbox doesn't reflect existing state, and unchecking it doesn't remove the override. No silent data loss on re-edit.

## Persona Red Flags

**Alex (power user)** — mostly served (shortcuts, presets, pbix import, Ctrl+L validate), but: no toolbar / no plain Save (every export is a full "Save As" prompt, no fast re-save to the current file); no rename/delete for a "+ New" style preset (a typo'd name is permanent); no dirty indicator, so a heavily-edited theme looks identical to a saved one.

**Jordan (first-timer)** — fails at orientation: opens to a wall of colour swatches with no primary Save/Export affordance and the Visual-styles checklist below the fold; zero tooltips/help to explain "Dimmed/category" or "Table accent"; the checklist rows are flat borderless text buttons that don't look clickable, so the per-visual dialog may never be discovered; Ctrl+N wipes everything with no warning.

**Sam (accessibility / keyboard)** — partial credit: `AccessibleName`/`Description` are set on swatches, spinners and override checkboxes, and a main-window tab order is wired. But the customized/default state leans on colour that's unreadable on dark chrome; the hex-on-swatch contrast failures hit low-vision users directly; tab order inside the data-colour editor and across the dialog's 14 group boxes is undefined.

## Minor Observations

- Default chart font size is **8 pt** in the dialog (below DESIGN.md's ≥10pt clarity intent for exported text).
- Data-colour controls only remove the **last** swatch — no per-row delete or reorder.
- Redo is Ctrl+Y only; add Ctrl+Shift+Z (Linux convention).
- Conditional-formatting swatches don't share a left/right edge with the structural swatches — broken column rhythm between the two groups (B).
- Open/Save error dialogs surface the raw exception with no suggested action.

## Questions to Consider

1. **Which design is real** — the white "workshop" in DESIGN.md, or the dark OS chrome the app actually ships in that hides its status colours?
2. **What does the ✓ actually mean** — "the user changed it" or "a value exists"? Can the checklist honestly tell those apart today?
3. **Where did the export promise go** — the product sells "export to Power BI," but the moment is an unlabeled "Save As… .json" dialog. Is hiding import/export behind generic file ops costing the integration-first positioning?
