# Product

<!-- impeccable:product-schema 1 -->

## Platform

desktop (PySide6 / Qt GUI — not web)

## Users

Power BI designers and developers who build reports professionally. They need to create custom themes to match company branding, and the built-in Power BI theme editor is either too limited or too laborious (manual JSON editing).

## Product Purpose

A visual, interactive desktop tool for creating Power BI themes without manually writing JSON. Lets users quickly design themes with live preview, save/load themes, and export them directly to Power BI's format. Reduces friction and speeds up iteration compared to editing JSON by hand.

## Positioning

A purpose-built visual editor specifically for Power BI themes, not a generic JSON editor. Users can see their theme applied in real-time and apply it to Power BI Desktop directly.

## Operating Context

- Designers work in Power BI Desktop alongside this tool.
- They open existing themes (.json, .pbix, .pbit) to edit or use as templates.
- They export finished themes and load them in Power BI Desktop via View → Themes.
- Currently used within a team/organization with existing branding standards.

## Capabilities and Constraints

**Capabilities:**
- Create themes from scratch or import from existing Power BI files
- Edit theme name, data colors, structural colors, text classes (typography)
- Edit visual styles for specific Power BI visual types
- Live JSON preview
- Save/open theme files
- Take screenshots of the editor

**Constraints:**
- Must remain a desktop GUI app (PySide6 / Qt)
- Must follow team/company branding and style standards
- Python 3.12+ required

## Brand Commitments

Follows existing team/company branding guidelines for UI and UX.

## Evidence on Hand

- README with feature overview and usage instructions
- Working desktop GUI with theme editor, open/save/import flows
- Model layer (`pbitheme.model`) independent of GUI, suitable for scripting
- Screenshots directory (for generated preview images)
- Demo JSON theme file

## Product Principles

1. **Visual clarity over config complexity** — Surface only the controls users need; hide Power BI's JSON complexity behind intuitive UI.
2. **Live feedback** — Show theme changes instantly; don't make users guess what JSON will do.
3. **Integration-first** — Import from existing Power BI files and export directly; minimize manual copy-paste.
4. **Separation of concerns** — Keep the theme model independent from GUI so it can power scripts and other tools later.
