# Surface Brief: Undo/Redo

## Job and Audience

**Who:** Power BI theme designers (all experience levels)  
**Context:** Mid-edit; user makes a mistake or wants to explore alternatives  
**Task:** Revert changes and replay changes without losing work  
**Success:** User confidently experiments, knowing they can undo

**Visitor Mode:** Operate (quality-of-life enhancement for theme creation workflow)

---

## Outcome and Proof

**Primary action:** Undo/Redo editing history (Ctrl+Z / Ctrl+Y)  
**Success criteria:**
- Undo reverts to previous theme state
- Redo replays changes
- History persists across 20 edits (or session end)
- No data loss; all theme state recovered exactly

**Product-specific truth:** Users confidently experiment when they know they can undo; reduces design friction

---

## Selected Direction

**Mechanism:** 
- Track theme state in a stack (20-edit history)
- Undo = pop from stack, show previous state
- Redo = replay popped states
- Triggered by Ctrl+Z (undo), Ctrl+Y or Ctrl+Shift+Z (redo)

**Interaction:**
- Menu items: Edit → Undo, Edit → Redo (with keyboard shortcuts shown)
- Status bar shows undo/redo availability ("Undo: X edits available" or greyed-out icons)
- No visual undo history panel (keep simple; just keyboard shortcuts)

---

## Scope and Boundaries

**Fidelity:** Fully functional, production-ready  
**Breadth:** All theme edits (colors, fonts, names, visual styles)  
**Interactivity:** Keyboard shortcuts + menu items  
**History depth:** Last 20 edits (LRU: oldest automatically dropped when limit hit)  

**What remains untouched:** Current theme state, JSON preview, editor form  
**Anti-goals:**
- NOT a visual undo timeline or history browser
- NOT branching undo (simple linear stack)
- NOT undo for file operations (open/save are not undoable)

---

## States and Ranges

**History states:**
- **0 edits:** No undo available (Undo menu grayed out)
- **1-20 edits:** Undo available up to current point
- **>20 edits:** Only last 20 in history (oldest dropped)
- **Redo available:** Only after undo has been called

**Clear undo history:**
- On "New" theme (File → New clears history and starts fresh)
- On "Open" theme (loading a file clears history, starts new history for edits)

---

## Interaction and Layout

**Menu structure:**
```
Edit
  ├─ Undo [Ctrl+Z]        (enabled/disabled based on history)
  ├─ Redo [Ctrl+Y]        (enabled/disabled based on redo stack)
  └─ (separator)
```

**Keyboard shortcuts:**
- `Ctrl+Z` → Undo
- `Ctrl+Y` or `Ctrl+Shift+Z` → Redo

**Visual feedback:**
- Status bar (lower left): "Ready" or "Undo available" (optional)
- Menu items grayed out when not available

**Transitions:**
- Instant state transition on Undo/Redo (no animation needed)
- JSON preview and all form fields update to match new state
- Visual Preview (if built) also updates

---

## Constraints and Open Decisions

**Platform:** Desktop Qt app (PySide6)  
**Storage:** History lives in memory only (cleared on app exit; file not touched)  
**Performance:** Undo/Redo must be instant (<50ms)  
**Testing:** Unit tests for history stack, edge cases (undo at start, redo after new edit)  

**Open decisions:**
- Stack size: 20 edits is reasonable; could be configurable in future
- What granularity = 1 edit? (Each field change, or batch on focus-out?)
  - **Recommendation:** Each significant change (e.g., color change, size change, checkbox toggle) = 1 edit
  - Batch rapid changes (e.g., dragging spinner) as single edit when focus lost
- Should undo clear the "current file" marker? (i.e., does Undo unsave the file?)
  - **Recommendation:** Yes—undo means file is modified but not matching last saved state

---

## Implementation Consequence

- **Complexity:** Low-medium (history stack + state capture)
- **Dependencies:** None (self-contained feature)
- **Testing:** History correctness, edge cases (undo at limit, redo branching)
- **Performance:** Must be sub-50ms for all undo/redo operations
- **Code impact:** Minimal; wraps existing state management (PowerBITheme)

---

## Confirmed Direction ✅

This brief is ready for implementation as **Phase 2** (after Visual Preview).

Next: `/impeccable shape` for Theme Library.
