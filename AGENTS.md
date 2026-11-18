# AGENTS.md — Developer & AI Instructions for Luckjary

This file defines mandatory project rules for human developers and AI pair programmers working on the Luckjary platform.

## 1. Design System Enforcement (NON-NEGOTIABLE)

All views, templates, components, and styling changes must strictly adhere to the **Luckjary Haute Atelier Design System** documented in [LUCKJARY_DESIGN_SYSTEM.md](file:///c:/Users/Asusr/.gemini/antigravity/scratch/cad-management-app/luckjary/LUCKJARY_DESIGN_SYSTEM.md).

### Typography
- **Headings & Page Titles (`h1`, `h2`, `h3`, page headers)**: MUST use `Cormorant Garamond` (fallback: `Georgia`, `Bodoni Moda`, `Playfair Display`, serif) in `#ffffff` or `#f3f4f6` with `font-normal tracking-wide`.
- **UI & Interface (buttons, table text, nav links, form labels, body)**: MUST use `Plus Jakarta Sans` (fallback: `Arimo`, `Inter`, sans-serif).
- **Monospace & Data (`#LCK-...`, SKUs, prices `₹`, counts, timestamps)**: MUST use `JetBrains Mono` (monospace). Default currency is Indian Rupee (`₹`).

### Button Styling Rules
- **Primary Buttons (`+ Create Order`, `Fulfill orders`, `+ ADD ...`, `Save`)**:
  - Background: Emerald `#10b981` (hover `#34d399`).
  - Text Color: **STRICTLY `#07080a` (Pitch Black)**. NEVER white or teal.
  - Due to Django CSS inheritance, always ensure `style="color: #07080a !important;"` or `.btn-primary`.
  - Border radius: `8px` (`rounded-lg`).
  - Shadow: `.glow-emerald` (`box-shadow: 0 0 20px -3px rgba(16, 185, 129, 0.35)`).
- **Secondary Buttons (`Open OMS Console`, `Launch OMS`, `Reset Changes`, `Filters`)**:
  - Background: Obsidian `#171920` (hover `#21242d`).
  - Text: `#e5e5e5` with 1px border `#21242d`.
- **Destructive Buttons**:
  - Text: `#f87171` (hover `#ef4444`).

### Underline Policy
- **Zero Underlines**: Underlines are strictly prohibited on all links, buttons, headers, and navigation items (`text-decoration: none !important;`).

### Surfaces & Containers
- Canvas background: Deep Obsidian `#07080a` to `#0d0e10`.
- Cards: `.card-surface` (`linear-gradient(145deg, rgba(23, 25, 32, 0.7) 0%, rgba(17, 19, 23, 0.95) 100%)`, border `1px solid rgba(255, 255, 255, 0.06)`, backdrop blur `12px`).
- Form inputs: `.glass-input` (`rgba(17, 19, 23, 0.85)`).

## 2. Testing & Verification Before Committing
- Run `python manage.py check` to verify Django configuration.
- Check template syntax to avoid escaped characters in URL tags (e.g. `{% url '...' %}`).
- Ensure mobile responsiveness for screen widths between `360px` and `480px`.
