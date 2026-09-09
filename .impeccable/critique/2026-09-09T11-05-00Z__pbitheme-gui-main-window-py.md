---
target: the app (main window + visual style dialog)
total_score: 27
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 2
target_identity: "file:/home/daimyo/Dev/PBi_Theme_Create/pbitheme/gui/main_window.py"
target_fingerprint: "sha256:8b48a9a1416db0caa6eaef25cdee32892de5d168601b47bdd9aa93aec49e2a07"
target_path: /home/daimyo/Dev/PBi_Theme_Create/pbitheme/gui/main_window.py
timestamp: 2026-09-09T11-05-00Z
slug: pbitheme-gui-main-window-py
---
Method: dual-agent (A: design review · B: detector + evidence)

# Critique (re-run) — Power BI Theme Creator (PySide6/Qt desktop · Operate mode)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Live preview + dirty title marker + status bar are strong; the Visual Formatting tab gives no signal of which fields are active overrides vs shown defaults. |
| 2 | Match System / Real World | 3 | "Foreground"/"Dimmed / category"/"Table accent" mirror Power BI terms but are unexplained jargon to a newcomer; no tooltips. |
| 3 | User Control and Freedom | 2 | Undo/Redo exists but history is pushed only on visual-style edits — colour, name, data-colour and text-class changes are unrecorded, so the most frequent edits can't be undone. |
| 4 | Consistency and Standards | 2 | Two override models across the dialog tabs; and "Clear All Overrides" does not clear the Visual Formatting panel — "all" is a false promise. |
| 5 | Error Prevention | 3 | Discard guard, Advanced-JSON + hex validation, save-failure dialogs all solid; per-row colour delete has no confirm and (see #3) no undo. |
| 6 | Recognition Rather Than Recall | 3 | Hex-on-swatch, live preview and named sections keep memory load low. |
| 7 | Flexibility and Efficiency | 3 | Shortcuts, presets, responsive 1↔2 column reflow; no search/filter on the visual checklist, no per-field "reset to default." |
| 8 | Aesthetic and Minimalist | 3 | Main form is clean; the Generic Overrides tab expands 14 sections at once with no progressive disclosure. |
| 9 | Error Recovery | 3 | Schema validation with detailed text and specific open/save/JSON error copy are genuinely good. |
| 10 | Help and Documentation | 2 | No tooltips on structural labels, no onboarding, no "what does customized mean" hint. |
| **Total** | | **27/40** | **Acceptable, top of band (~68%)** — visual system is now solid; held back by two integrity bugs. |

All ten apply; none n/a.

## Design Specificity Verdict
**PASS — a real, specific system, not a generic Qt dump.**

- **Design review (A):** DESIGN.md's white "workshop" is now legibly executed — flat surfaces, `QGroupBox` chunking, monospace hex on every swatch, dual live preview, personality-free system font. `apply_light_palette` is the key specificity move: it stops the app inheriting a dark desktop and guarantees the white-surface assumptions the whole system is tuned around. Status colours are WCAG-safe and now carry text ("✓ Custom"/"✗ Default"), not a bare glyph. Where it frays: the per-visual dialog runs **two override paradigms** — Generic Overrides gates each section behind a checkbox, Visual Formatting shows always-live pre-filled fields with no enable affordance. That's a system fork.
- **Deterministic scan (B):** `impeccable detect` returned `[]` (exit 0) on the app — **inapplicable, not clean**: the bundled detector is an HTML/CSS/DOM scanner and the app is pure Python/Qt with zero app-authored markup. (Pointed at a stray PyInstaller `build/` xref HTML it emitted two colour advisories — a build artifact, not UI. Irrelevant.)
- **Overlays:** none — no web page/DOM/dev server (Qt desktop). Evidence came from the two current screenshots.

## Overall Impression
The systemic fixes landed and the app now reads as an intentional, professional tool: light palette, WCAG-true swatch text (B measured every swatch ≥4.5:1; `#D64550` Bad is the tightest at ~4.8:1 and correctly uses black text), the dialog tab bar fully visible, the preview reflowing to one column so nothing clips, and a real unsaved-changes guard. The score is held back not by the visual system — which is specific and honest — but by **two integrity bugs where the UI's promise and its behavior diverge.** Close those and this is comfortably "polished."

## What's Working
1. **The forced light Fusion palette** converts DESIGN.md from aspiration to guarantee — it's why the status cues, swatch-text contrast and hairlines read correctly regardless of host OS theme.
2. **Accessibility is genuinely handled** — WCAG-true swatch text (`_readable_text_color`), status shown as text+glyph+colour (not colour alone), accessible names on buttons/spinboxes/checkboxes, explicit tab order, per-row delete with an accessible label. Sam is the best-served persona.
3. **Error/edge handling is above the bar** — discard guard via `closeEvent`, Save vs Save As, `[*]` modified marker, Advanced-JSON parse guard, and specific, actionable failure copy.

## Priority Issues

**[P1] "Clear All Overrides" doesn't clear the Visual Formatting tab.** *Verified:* `_clear_all()` unchecks the 14 generic checkboxes and resets Advanced JSON to `{}`, but never touches `self._formatter_panel`. Clicking it with axis/label formatting set leaves a partially-cleared visual and an Advanced-JSON box that no longer reflects the real state — a direct violation of DESIGN.md's "JSON preview is the contract." *Fix:* in `_clear_all`, also `self._formatter_panel.set_values({})` (when present) and `_update_preview()`; add a test that `_build_overrides()` is empty afterward.

**[P1] Undo/Redo silently doesn't cover the most common edits.** *Verified:* `_record_history()` is called only from `_on_edit_visual_style`; structural/gradient/data colours, text classes and the name all reach `_refresh_preview` (lines 135/144/154/163/172) with no history push, so Ctrl+Z can't reverse them and the menu item sits disabled after a colour change. Combined with per-row data-colour delete having no confirm, a destructive edit is effectively irreversible. *Fix:* push history on committed edits (debounced, gated by `_loading`/`_skip_history_record`) or at minimum on `colorChanged` and data-colour delete — or remove the affordance for what it can't reach.

**[P2] Two override paradigms inside one dialog.** Generic Overrides gates each section behind a checkbox; Visual Formatting shows always-live pre-filled fields with no toggle, so the user can't tell which values will actually be written vs which are defaults on display. *Fix:* give Visual Formatting the same per-field/per-section enable affordance, or a visible "overridden" indicator per field.

**[P2] Core task is below the fold; 14-section wall in the dialog.** The Visual Styles checklist — the product's headline capability — is the last left-form section, under Data colours and Text classes, off the initial fold; Generic Overrides expands all 14 sections at once. *Fix:* a section jump-list or collapsible groups in the form; collapsible (collapsed-unless-active) Generic Override sections.

**[P3] Unexplained structural-colour jargon.** "Foreground", "Dimmed / category", "Table accent", "Secondary background" have no tooltips; a first-timer can't map them to effect. *Fix:* a `setToolTip` per structural row.

## Persona Red Flags
- **Alex (power user):** undo is inert for the edits he makes most (colours) — kills iterate-and-revert; no filter/search on the visual checklist.
- **Jordan (first-timer):** highest risk — jargon with no help, the two-paradigm dialog, the 14-section wall, and "Clear All" not clearing everything compound; nothing tells him what makes a visual "customized" until it's already ✓/✗.
- **Sam (accessibility):** fewest flags — text+glyph+colour status, WCAG swatch text, accessible names, tab order, forced light palette. Residual: focus-ring rides on Fusion defaults (unverified), the 28px ✕ delete is on the small side, dialog internal tab order is unset.

## Minor Observations
- `LUMINANCE_THRESHOLD = 140` in theme.py is now **dead code** (replaced by `_readable_text_color`) — delete it to avoid a future inconsistency.
- Preview/dialog borders hardcode `#ddd` instead of `theme.BORDER_HAIRLINE` — a small drift from the token system.
- Data-colour delete has no confirm and no history push (ties to P1 undo).
- Two unrelated "responsive" magic numbers (preview `>=500`, dialog `>=700`) — centralize or document.

## Questions to Consider
1. If "Clear All Overrides" leaves Visual Formatting populated, what does *all* mean — and does the Advanced JSON box still tell the truth after the click?
2. Why keep an Undo item that can't undo a colour change — the single most frequent action in a *theme* editor?
3. In Visual Formatting, a pre-filled `#12239E` axis-label colour and a genuine user override look identical. How is anyone supposed to know which fields the exported theme will actually pin?
