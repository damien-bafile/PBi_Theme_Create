# Surface Brief: Visual Preview Panel

## Job and Audience

**Who:** Power BI theme designers (primary users from PRODUCT.md)  
**Context:** Mid-edit; users need to see how their theme looks before exporting  
**Task:** Preview theme applied to realistic Power BI visuals (charts, tables, cards)  
**Success:** User sees live visual feedback; makes color decisions with confidence

**Visitor Mode:** Operate (users complete theme-creation task with visual validation)

---

## Outcome and Proof

**Primary action:** View theme applied to 4 visual types in real-time (live preview as user edits)  
**Success criteria:**
- Chart colors match theme data colors
- Text contrast is readable
- Structural colors (background, borders, accents) are visible and appropriate
- User gains confidence before export

**Product-specific truth:** Power BI visuals are the end goal; preview validates themes in their native context

---

## Selected Direction

**Placement:** Right pane (currently JSON preview) → replace or augment  
**Approach:** 
- Show 4 chart mockups: Bar chart, Table, Line chart, Card (KPI)
- Each mockup uses live theme colors and typography from the editor
- Update in real-time as user edits (same as JSON preview)
- Allow toggle between Preview and JSON (tabs or button)

**Interaction:**
- Mockups are read-only (no interaction beyond viewing)
- Live refresh on every theme edit (connected to preview signal)
- Mockup size adapts to pane width

---

## Scope and Boundaries

**Fidelity:** Medium — simplified Power BI visual mockups (not pixel-perfect reproductions)  
**Breadth:** 4 visual types (as selected by user)  
**Interactivity:** Read-only preview; no tooltips, data exploration, or drill-down  
**Targets:** Maintain ~2:1 width ratio for current splitter  
**What remains untouched:** Editor form, menu, status bar  

**Anti-goals:**
- NOT a full Power BI embed (too complex, requires Power BI APIs)
- NOT interactive data exploration
- NOT printing/export quality visuals (mockups only)

---

## States and Ranges

**Sample data:**
- Bar chart: 5 categories, 2-3 series
- Table: 3 columns, 5 rows (text, numbers, percentage)
- Line chart: 3 lines, 12 months
- Card: Single KPI value + trend

**States:**
- **Default:** All 4 mockups visible (grid or vertical stack)
- **Empty:** Show if theme is blank (placeholder state)
- **Loading:** (probably none; rendering is instant)

---

## Interaction and Layout

**Hierarchy:**
- Mockups split vertically (or stack vertically if narrow)
- Each labeled ("Bar Chart", "Table", "Line Chart", "Card")
- Colors and typography from theme applied in real-time

**Affordances:**
- Clear distinction: preview vs JSON pane (tabs or toggle button)
- Tooltips on mockup type labels explain what's shown
- No interactions on mockups themselves

**Transitions:**
- Tab/button press switches between Preview and JSON smoothly
- Color changes update mockups instantly (signal-driven, like JSON preview)

---

## Constraints and Open Decisions

**Platform:** Desktop Qt app (PySide6)  
**Accessibility:** Mockups should be labeled accessibly; consider alt text for screen readers  
**Performance:** Rendering must be instant (no perceived lag)  
**Reusable components:** Create MockupRenderer class or functions to render each visual type  

**Open decisions:**
- How much detail in mockups? (Simple shapes vs. realistic rendering)
- Should mockups be HTML/SVG, or Qt graphics?
- Can we use mock Power BI API data, or generate our own?

---

## Implementation Consequence

- **Complexity:** Medium (4 mockup generators + live update signal)
- **Dependencies:** None (doesn't require external Power BI APIs for Phase 1)
- **Testing:** Visual regression tests for each mockup type, color accuracy
- **Future:** Could expand to more visual types, print-quality export, or Power BI embed

---

## Confirmed Direction ✅

This brief is ready for implementation as **Phase 1** (first feature to ship).

Next: `/impeccable shape` for Undo/Redo, then Theme Library.
