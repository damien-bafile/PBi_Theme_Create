# Surface Brief: Theme Library

## Job and Audience

**Who:** Power BI theme designers (repeat users, teams with shared themes)  
**Context:** After editing; user saves theme or wants to load previous work  
**Task:** Organize, find, and load saved themes without file browser friction  
**Success:** User can quickly load a theme from a list; no filesystem navigation needed

**Visitor Mode:** Operate (manage theme collection as part of workflow)

---

## Outcome and Proof

**Primary action:** 
- View saved themes in a sidebar list
- Click to load theme
- Right-click to delete/export

**Success criteria:**
- User's themes are listed and searchable
- Loading a theme is 1-2 clicks (vs. File → Open → browse)
- Theme name shows; can optionally show metadata (date, color preview)

**Product-specific truth:** Designers reuse and iterate on themes; library reduces friction

---

## Selected Direction

**Placement:** Left sidebar, above editor form (new panel, stacked with other sections or tabbed)  
**Interaction:**
- Simple list of saved themes
- Double-click to load
- Right-click context menu: "Load", "Delete", "Export", "Rename"
- Search box to filter by name (optional; nice-to-have)

**Storage:** User specifies save location via Save As dialog; library shows all .json files from that folder

---

## Scope and Boundaries

**Fidelity:** Functional MVP (simple list, core operations)  
**Breadth:** Read/write operations on saved theme files  
**Interactivity:** Click to load, right-click menu  

**What remains untouched:** Current editor form, menus, preview  
**Anti-goals:**
- NOT a tag/category system (Phase 1 is flat list)
- NOT cloud sync or team collaboration (local filesystem only)
- NOT theme comparison (side-by-side view is future)
- NOT import/export of multiple themes at once

---

## States and Ranges

**Library states:**
- **No folder set:** Show message "Set a theme folder in File → Preferences" with button
- **Empty folder:** Show "No themes saved yet"
- **1-50 themes:** List all (scrollable if >15)
- **>50 themes:** Consider pagination or infinite scroll (Phase 2)

**Theme metadata shown:**
- Name (filename without .json)
- Date modified (optional; nice-to-have)
- Color swatch preview (optional; Phase 2)

---

## Interaction and Layout

**UI structure:**
```
┌─ Theme Library ─────────┐
│ [Search box]            │
│ ─────────────────────── │
│ • Corporate Blue        │
│ • Minimalist (Dark)     │
│ • High Contrast         │
│ • My Project Theme      │
│                         │
│ (Right-click for menu)  │
└─────────────────────────┘
```

**Right-click menu:**
- Load (or double-click to load)
- Rename…
- Delete
- Export… (copies to user-chosen location)

**Affordances:**
- Hover highlight on theme names
- Clear indication of which theme is currently loaded (bold, highlight, or checkmark)

**Transitions:**
- Load theme: fade out current editor content, load new theme, fade in (optional; could be instant)
- Delete theme: confirm dialog ("Delete 'Theme Name'?"), remove from list

---

## Constraints and Open Decisions

**Platform:** Desktop Qt app (PySide6)  
**File discovery:** Scan folder for .json files at startup; refresh on demand (or auto-watch folder)  
**Performance:** List render must be instant for 50+ items  
**Accessibility:** List should be keyboard-navigable; support arrow keys and Enter to load  

**Open decisions:**
- **Theme folder location:**
  - Option A: User specifies once (File → Preferences → Theme folder)
  - Option B: Always show file picker ("Choose theme folder")
  - **Recommendation:** Option A (persistent preference)
  
- **Folder watching:** Auto-refresh when themes are added/deleted on disk?
  - **Recommendation:** Refresh button in library panel header ("Refresh" icon)
  
- **Default themes:** Ship with 2-3 pre-built themes (Corporate, Minimalist, High Contrast)?
  - **Recommendation:** Phase 2 feature; Phase 1 is user-created themes only

- **Theme metadata:** Show date modified, file size, color preview?
  - **Recommendation:** Phase 1 = name only; Phase 2 = date + color swatch

---

## Implementation Consequence

- **Complexity:** Medium (file system scanning, list UI, right-click menu)
- **Dependencies:** Depends on PowerBITheme.load() (already exists)
- **Testing:** File discovery, load/delete/rename operations, error handling (missing files, permission errors)
- **Performance:** Fast list rendering for 50+ themes
- **Code impact:** New LibraryPanel widget, folder preference storage

---

## Confirmed Direction ✅

This brief is ready for implementation as **Phase 3** (after Visual Preview and Undo/Redo).

---

## Implementation Roadmap

1. **Phase 1 (Visual Preview)**: Live chart mockups showing theme
2. **Phase 2 (Undo/Redo)**: 20-edit history with keyboard shortcuts
3. **Phase 3 (Theme Library)**: Sidebar list of saved themes with load/delete

All three features improve the core value proposition: **powerful, efficient theme creation**.
