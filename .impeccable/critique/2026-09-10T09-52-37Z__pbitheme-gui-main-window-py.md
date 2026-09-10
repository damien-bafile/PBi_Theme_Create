---
target: the app (main window + visual style dialog, light + dark)
total_score: 32
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 2
target_identity: "file:/home/daimyo/Dev/PBi_Theme_Create/pbitheme/gui/main_window.py"
target_fingerprint: "sha256:d2793f4d96ab54200e51ad91422d16dad2f8dd64d12ddd744c629dd02ec78c80"
target_path: /home/daimyo/Dev/PBi_Theme_Create/pbitheme/gui/main_window.py
timestamp: 2026-09-10T09-52-37Z
slug: pbitheme-gui-main-window-py
---
Method: dual-agent (A: design review · B: detector + evidence)

# Critique (4th run) — Power BI Theme Creator (PySide6/Qt desktop · Operate mode)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 4 | Dual live preview, `[*]` dirty marker, save/open status — but in-dialog undo state is invisible. |
| 2 | Match System / Real World | 3 | Structural jargon has tooltips now; "Generic Overrides" + export-only cards stay Power-BI-internal. |
| 3 | User Control and Freedom | 3 | App + in-dialog undo, confirm-discard, confirmed Clear All — but the Clear All copy misstates reversibility. |
| 4 | Consistency and Standards | 3 | Mostly clean; the welcome banner doesn't re-theme when Dark Mode is toggled at runtime. |
| 5 | Error Prevention | 4 | Confirm on close/new/open + Clear All, invalid-JSON blocked, schema validation. Solid. |
| 6 | Recognition Rather Than Recall | 3 | Live previews, tooltips, search, empty-state hint — but the colour palette is pushed below the fold under a 260px checklist. |
| 7 | Flexibility and Efficiency | 3 | Filter, presets, shortcuts, pbix import, undo/redo — dialog Ctrl+Z/Y are shortcut-only (no button/menu). |
| 8 | Aesthetic and Minimalist | 3 | Clean/flat, but dark-mode visual names read as disabled and 50+ red "✗ Default" rows form a noisy wall. |
| 9 | Error Recovery | 3 | Open/Save remediation copy is genuinely good; invalid-JSON warning names no line/field. |
| 10 | Help and Documentation | 3 | Banner + tooltips + inline notes + empty-state; no persistent help once the banner is gone. |
| **Total** | | **32/40** | **Competent → Strong (low end)** — an earned +2, held back by two new/remaining defects. |

## Design Specificity Verdict — **PASS (specific, built to its own DESIGN.md)**
- **A:** The "Craftsperson's Workshop" is real in the artifact — forced Fusion palette, status green/red used only for ✓/✗, WCAG hex-on-swatch, dual live preview, and a genuine dark second surface with re-tuned AA status colours (not a CSS invert). Where it frays: the *primary click targets* (visual-name buttons) have no explicit colour token, so on dark they collapse to near-disabled grey; and the new in-dialog undo has no visual presence.
- **B:** `impeccable detect` → `[]` (exit 0) on both targets — **inapplicable, not clean** (HTML/CSS/DOM scanner, 0 app markup among 151 Python files). **Swatch WCAG picker confirmed working** (white hex on the dark `#252423` swatches ≈ 15:1) — correcting last pass's false positive.
- **Overlays:** none (Qt desktop, no DOM/dev server).

## Overall Impression
Capable and trustworthy, punctured twice. The preview-truth architecture (`_update_preview` and `_on_ok` build the saved object the same way) is a real integrity guarantee, dark mode is a proper second surface, and the safety scaffolding is thorough. But two defects that **my own recent features introduced** hold the score down: the Clear-All dialog now *lies* about reversibility, and the dark-mode primary targets are the least legible text on screen.

## What's Working
1. **Preview-truth architecture** — the live SVG can't drift from what exports (same build path).
2. **Destructive-action discipline** — confirm-discard, confirmed + atomic-undoable Clear All, hard-blocked invalid JSON.
3. **Honest, actionable error copy** — Open/Save failures say what to do next; schema validation lists up to 20 issues.

## Priority Issues

**[P1] The Clear All confirmation actively misinforms.** *(verified)* The dialog says *"This can't be undone from inside the dialog"* — but this pass made Clear All exactly one `Ctrl+Z` step. The copy now contradicts a shipped feature, discouraging the very safety net that exists and eroding trust in every other confirm. *Fix:* change to *"You can undo this with Ctrl+Z."* (and consider dropping the modal since it's now reversible).

**[P1] Dark-mode visual names read as disabled.** *(verified — A + B)* `widgets.py` `_NAME_STYLE` sets no explicit colour, so under a QSS rule the flat buttons drop palette text colour and render dim grey on the dark chrome (~2–3:1, below AA) while the red "✗ Default" column stays bright — inverting the hierarchy (targets should dominate, status should support). Same root cause dims the right-pane section headings. *Fix:* give `_NAME_STYLE` (and the preview headings) an explicit `color: palette(...)` so text follows the mode; verify flat + hover clear AA on `DARK_BASE`.

**[P2] The colour palette fell off the fold.** Moving Visual Styles above the colour sections last pass, plus the checklist's 260px min height, pushed structural / gradient / data / text colours below the fold — so the banner's "set your palette" points at content the user can't see on open. *Fix:* shrink the checklist min-height (~150–170px), and/or keep General + Structural colours on the first screen alongside a shorter Visual-styles list.

**[P2] In-dialog undo/redo is invisible.** Ctrl+Z/Ctrl+Y are `QShortcut`-only — no button, no menu in the modal — so most users won't know it exists (compounded by the P1 copy saying it doesn't). *Fix:* small Undo/Redo buttons next to "Clear All Overrides," enabled-state driven by the stacks.

**[P3] Welcome banner ignores the runtime theme toggle.** It reads `theme.dark_mode` once at build; toggling Dark Mode with the banner still up leaves a light banner on dark chrome. *Fix:* restyle it inside `_on_toggle_dark`, or use palette roles instead of hardcoded hex.

**[P3] The red "✗ Default" wall.** With 50+ visuals, the *default* state is the loudest thing on screen, inverting the Status Rule's intent. *Fix:* mute default rows to a still-legible grey ✗ so the green ✓ Custom rows are what pop.

## Persona Red Flags
- **Alex (new designer, follows the banner):** told to "set your palette," lands on a list of visual names with colour controls off-screen, then a Clear All dialog that claims irreversibility. Two early trust dents.
- **Jordan (power user, dark mode):** the clickable visual names are the dimmest text on screen; uses Ctrl+Z reflexively but has no on-screen confirmation and was told it wouldn't work.
- **Sam (low-vision):** dark-mode target legibility is a direct barrier; the misleading destructive-action copy scares a cautious user off.

## Minor Observations
- Dialog undo records per-*keystroke* (textChanged) on line edits, vs the main window's deliberate `editingFinished` batching — inconsistent granularity.
- Switching presets silently commits current fields into the old preset with no "unsaved" signal.
- Data-colour ✕ delete has no confirm/undo hint inside the widget.
- JSON preview font `"monospace"` is a family alias, not the Courier New DESIGN.md names.

## Questions to Consider
1. If the live preview *is* the contract, why is the palette that drives it hidden below the fold on launch?
2. You shipped in-dialog undo *and* a warning that says it doesn't exist — are the confirm dialogs being written from memory rather than the current code?
3. In dark mode the loudest thing is the *default* state and the quietest is the *action* — should "done" be what glows instead of "not done"?
