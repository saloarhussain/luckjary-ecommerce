---
description: Enforce Luckjary Haute Atelier typography, colors, and button styles across all views
trigger: always_on
---

# Luxury Atelier Design System Rules

Whenever editing or generating HTML templates, CSS, or UI components for the Luckjary dashboard or admin:

1. **Typography**:
   - Headers (`h1`, `h2`, `h3`, page titles): Use `Cormorant Garamond` serif with `#ffffff` text.
   - Body & Controls (buttons, labels, table data, links): Use `Plus Jakarta Sans`.
   - Technical & Data (Order IDs `#LCK-...`, SKUs, prices `₹`, counters): Use `JetBrains Mono`.

2. **Buttons**:
   - Primary Buttons: Must have background `#10b981` (Emerald 500) and text color `#07080a !important;` (pitch-black). Never white text on emerald buttons. Box shadow `.glow-emerald`.
   - Secondary Buttons: Background `#171920`, text `#e5e5e5`, border `1px solid #21242d`.
   - Zero underlines on any button or link state (`text-decoration: none !important;`).

3. **Surfaces**:
   - Deep canvas base: `#07080a` to `#0d0e10`.
   - Card surfaces: `.card-surface` with `linear-gradient(145deg, rgba(23, 25, 32, 0.7) 0%, rgba(17, 19, 23, 0.95) 100%)` and `1px solid rgba(255, 255, 255, 0.06)`.
