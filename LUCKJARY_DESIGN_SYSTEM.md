# Luckjary Haute Joaillerie — Atelier Design System Specification

> **MANDATORY DESIGN STANDARD FOR ALL FUTURE PAGES & COMPONENTS**  
> All future admin views, changelists, change forms, dashboards, and client-facing interfaces across the Luckjary platform MUST strictly adhere to these design tokens, typography rules, button recipes, and surface treatments.

---

## 1. Typography & Font Hierarchy

The typography embodies a high-contrast luxury atelier aesthetic: timeless elegance in serif headings, pristine legibility in geometric sans-serif interface elements, and precision tabular clarity in technical and financial data.

| Role | Font Family | Fallbacks | Usage | CSS / Tailwind Class |
| :--- | :--- | :--- | :--- | :--- |
| **Haute Joaillerie Display & Headings** | `Cormorant Garamond` | Georgia, Bodoni Moda, Playfair Display, serif | Page titles, screen greetings (`Welcome back, Eleanor`), modal headers, table titles, KPI numbers | `font-serif font-normal tracking-wide text-white` (`font-family: 'Cormorant Garamond', Georgia, serif;`) |
| **Interface & Data Sans** | `Plus Jakarta Sans` | Arimo, Inter, -apple-system, sans-serif | Navigation links, buttons, table headers, table cells, form labels, inputs, modal body | `font-sans font-medium` (`font-family: 'Plus Jakarta Sans', sans-serif;`) |
| **Technical & Telemetry Monospace** | `JetBrains Mono` | SF Mono, Consolas, monospace | Order Reference IDs (`#LCK-202611-304918`), SKU tags (`LUK-DEMI-RG-006`), amounts (`₹9,28,399`), timestamps, hash tokens | `font-mono tracking-tight` (`font-family: 'JetBrains Mono', monospace;`) |

### Typography Guidelines
1. **Headings (`h1`, `h2`, `h3`)**:
   - Always render in `Cormorant Garamond` serif.
   - Color must be crisp pure white (`#ffffff`) or `#f3f4f6`.
   - Never use heavy bold (`font-bold`) on serif titles; prefer regular/normal (`font-normal` or `font-medium`, weight `400`–`500`) with subtle letter-spacing (`tracking-wide` / `letter-spacing: 0.02em`).
2. **Body & Interface Text**:
   - Primary labels and titles: `#f3f4f6` (Off-white).
   - Secondary / descriptive text: `#9ca3af` (Muted gray).
   - Inactive / Section labels: `#6b7280` (Neutral muted, uppercase with `tracking-wider`).
3. **Currency & Prices**:
   - Always display Indian Rupee (`₹`) as primary currency, followed by tabular numbers in `JetBrains Mono` or `Plus Jakarta Sans` bold. Example: `₹9,28,399` (`($11,165.00)`).

---

## 2. Action Buttons & Interactive Controls (Strict Rules)

### Primary Action Buttons (`+ Create Order`, `Fulfill orders`, `+ Add Collection`, `Save`)
- **Background**: Atelier Emerald `#10b981` (hover: `#34d399` / `#059669`).
- **Text Color**: **`#07080a !important;` (Pitch-Black)**.  
  *(CRITICAL: Under no circumstances should primary button text be white, teal, or gray. Due to Django admin link inheritance, always enforce `style="color: #07080a !important;"` or `.btn-primary`)*.
- **Font**: `Plus Jakarta Sans`, weight `600` (`font-semibold`), `0.75rem` to `0.875rem` (`text-xs` / `text-sm`).
- **Border Radius**: `8px` (`0.5rem` / `rounded-lg`).
- **Glow Shadow**: `box-shadow: 0 0 20px -3px rgba(16, 185, 129, 0.35)` (`.glow-emerald`).
- **Border**: `1px solid rgba(16, 185, 129, 0.35)`.
- **Underline**: **`text-decoration: none !important;`** (Zero underlines under all states).
- **Icons**: Inline SVGs with stroke/fill matching `#07080a`.

#### HTML Reference Pattern for Primary Buttons:
```html
<a href="/admin/orders/order/add/" 
   class="btn-primary glow-emerald inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 transition-all cursor-pointer"
   style="color: #07080a !important; text-decoration: none !important;">
    <svg class="w-3.5 h-3.5" fill="none" stroke="#07080a" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"></path>
    </svg>
    <span>+ Create Order</span>
</a>
```

### Secondary Action Buttons (`Open OMS Console`, `Launch OMS`, `Reset`, `Filters`, `History`)
- **Background**: `#171920` (Obsidian surface) or `rgba(23, 25, 32, 0.8)`. Hover: `#21242d`.
- **Text Color**: `#e5e5e5` (hover: `#ffffff`).
- **Border**: `1px solid #21242d` (hover: `rgba(255, 255, 255, 0.15)`).
- **Font**: `Plus Jakarta Sans`, weight `500` (`font-medium`).
- **Border Radius**: `8px` (`rounded-lg`).

#### HTML Reference Pattern for Secondary Buttons:
```html
<button class="btn-secondary inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-[#171920] hover:bg-[#21242d] border border-[#21242d] text-neutral-200 transition-all cursor-pointer">
    <span>Open OMS Console</span>
</button>
```

### Destructive / Delete Actions (`Delete`, `Remove`)
- **Background**: Transparent or `rgba(239, 68, 68, 0.1)`. Hover: `rgba(239, 68, 68, 0.2)`.
- **Text Color**: `#f87171` (hover: `#ef4444`).
- **Border**: `1px solid rgba(239, 68, 68, 0.2)`.

---

## 3. Surface Hierarchy & Canvas Palette

| Element | Hex / RGBA | Description |
| :--- | :--- | :--- |
| **Main Canvas Base** | `#07080a` to `#0d0e10` | Deep luxury obsidian canvas backdrop |
| **Sidebar & Header Surface** | `#0c0d10` to `#121315` | Elevated backdrop with subtle `1px solid rgba(255, 255, 255, 0.06)` border |
| **Card / Container Surface (`.card-surface`)** | `linear-gradient(145deg, rgba(23, 25, 32, 0.7) 0%, rgba(17, 19, 23, 0.95) 100%)` | Semi-transparent luxury panel with `backdrop-filter: blur(12px)` and `1px solid rgba(255, 255, 255, 0.06)` |
| **Interactive Form Fields (`.glass-input`)** | `#111317` / `rgba(17, 19, 23, 0.85)` | Glassmorphism input with `background-color: #111317 !important; color: #f3f4f6 !important; border: 1px solid rgba(255, 255, 255, 0.08) !important;`. Under no circumstances should inputs be white (`#ffffff`). Focus ring: `rgba(16, 185, 129, 0.5)`. |
| **Divider & Separator Lines** | `#21242d` / `rgba(255, 255, 255, 0.06)` | Minimal separation lines |

---

## 4. Status Indicators & Badges

| Status | Background | Text Color | Border | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Optimal / Active / Paid** | `rgba(16, 185, 129, 0.12)` | `#34d399` (Emerald 400) | `1px solid rgba(16, 185, 129, 0.3)` | Verified orders, active materials, online status |
| **Needs Action / Pending / Unfulfilled** | `rgba(245, 158, 11, 0.12)` | `#fbbf24` (Amber 400) | `1px solid rgba(245, 158, 11, 0.3)` | Fulfillment alerts, pending payment reviews |
| **In Atelier QC / Processing** | `rgba(99, 102, 241, 0.12)` | `#a5b4fc` (Indigo 300) | `1px solid rgba(99, 102, 241, 0.3)` | Jeweler crafting, hallmark inspection |
| **Delivered / Archived** | `rgba(107, 114, 128, 0.15)` | `#9ca3af` (Gray 400) | `1px solid rgba(107, 114, 128, 0.25)` | Closed orders, historic records |

---

## 5. Universal Zero-Underline Rule

**Underlines are strictly forbidden throughout all dashboard pages, changelists, form controls, navigation links, and breadcrumbs.**

All CSS sheets must maintain the universal reset:
```css
a, a *, a:link, a:visited, a:hover, a:hover *, a:focus, a:active {
    text-decoration: none !important;
    text-decoration-line: none !important;
}
```

---

## 6. Checklist for Adding or Modifying Pages

When creating or modifying any view or template:
- [ ] Headings (`h1`, `h2`, `h3`, page title) use `Cormorant Garamond` serif with `#ffffff`.
- [ ] Body, buttons, and navigation use `Plus Jakarta Sans`.
- [ ] Order IDs, SKU tags, and monetary figures use `JetBrains Mono`.
- [ ] Primary buttons use `#10b981` emerald background with `#07080a` pitch-black text and `glow-emerald`.
- [ ] Secondary buttons use `#171920` surface with `#e5e5e5` text and 1px `#21242d` border.
- [ ] No links or buttons have underlines on hover or active states.
- [ ] Cards and containers use `.card-surface` with subtle borders and rounded corners.
- [ ] Mobile responsive layout handles viewports from `360px` to `480px` without horizontal overflow.
