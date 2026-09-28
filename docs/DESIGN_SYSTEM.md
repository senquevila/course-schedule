# Design System

The single visual theme for Course Calendar. This document is the complete
reference: every color, font, size, and component rule needed to build or
change a screen is here, so no other design file is needed.

The look is adapted from a community e-learning UI kit: deep forest-green
panels, a pale mint canvas, white surfaces, and a lime accent. The values in
**Measured from the kit** were extracted from the kit's exported artwork (pixel
census of the full render, plus zoomed samples of each element). Values marked
**derived** were not in the kit and were chosen to fit it.

## Decisions

- **One theme.** A single light theme. No dark mode and no theme toggle.
- **The look, not the brand.** The app keeps the name "Course Calendar"; no kit
  branding, marketing copy, or stock photography.
- **Decorative shapes are rare.** The lime, sage, and teal shapes appear only in
  the home hero, never on working screens (calendar, tables, forms).
- **Class names stay.** Every component maps to a class the templates already
  use, so applying the theme changes `static/css/style.css` and the `<head>` of
  `templates/base.html` only.

## The look at a glance

```
 mint canvas ─────────────────────────────────────────────────────────────
  Course Calendar (teal, bold)      [ 🔍 Search courses      ] (white field)   Home  Courses

  ┌─ forest panel, 16px corners ──────────────────────────────────────┐
  │  C O U R S E   C A L E N D A R      (tracked caps, near-white)     │  ◖ lime
  │  Plan, teach, and track             (Inter bold, near-white)       │  ◗ sage
  │  every session                                                     │  ❧ teal
  │  One sentence of body copy in pale aqua.                           │
  │  [ 🔍 Search…            (mint)  |  Courses ⌄ (white) ]            │
  └────────────────────────────────────────────────────────────────────┘

  ┌ white card ┐ ┌ white card ┐ ┌ white card ┐     ← surfaces separate by
  └────────────┘ └────────────┘ └────────────┘       color, not shadows
```

## Color

### Measured from the kit

Share of the full artwork (frames and photos excluded) shows how the kit
balances the palette: forest dominates, mint and white carry content, lime is a
small accent.

| Token | Hex | Where the kit uses it | Share |
|---|---|---|---|
| `--forest` | `#083B3B` | Page background, hero panel, check marks | ~65% |
| `--white` | `#FFFFFF` | Cards, navbar search field, dropdown segment, headline text | ~7% |
| `--mint` | `#E7F5F2` | Navbar and page canvas, hero search field | ~7% |
| `--lime` | `#EAF140` | Check-mark circles, large semicircle shape | ~1% |
| `--sage` | `#CBDDBD` | Quarter-circle shape | <1% |
| `--teal` | `#126D61` | Leaf shape, logo wordmark (`#136354`–`#136A59`, same hue) | <1% |
| `--on-forest` | `#F8FAFC` | Headlines and the tracked caps label on forest | — |
| `--on-forest-soft` | `#D3F1F1` | Body copy on forest (pale aqua, not grey) | — |
| `--ink-soft` | `#405354` | Text on white segments ("Courses ⌄") | — |
| `--placeholder-kit` | `#737776` / `#6D7C79` | Placeholders on white / on mint | — |

### Derived

| Token | Hex | Use | Why |
|---|---|---|---|
| `--ink` | `#083B3B` | Body text on mint and white | Same as forest; the kit has no separate text color |
| `--muted` | `#5F6E6B` | Placeholders, secondary text, table headers | Kit placeholder on mint is 3.9:1 (fails AA); this keeps its hue at 4.8:1 |
| `--rule` | `#D3E6E1` | Borders, dividers | A step darker than mint, same hue |
| `--danger` | `#B3322A` | Destructive actions, errors | Kit has no red; warm enough to sit next to lime |

### Contrast (WCAG 2.x)

Every text pair used by this system passes AA (4.5:1).

| Pair | Ratio |
|---|---|
| `--on-forest` on forest | 11.8 |
| `--on-forest-soft` on forest | 10.4 |
| lime on forest / forest on lime | 10.1 |
| ink on mint | 11.0 |
| forest on sage | 8.6 |
| `--ink-soft` on white | 8.1 |
| teal on white / on mint | 6.2 / 5.5 |
| `--danger` on white | 6.2 |
| `--muted` on white / on mint | 5.3 / 4.8 |

**Lime is never text on white or mint** (it's nearly invisible there). It's a
fill, a ring, or text on forest only.

### Session status (derived)

Used by the calendar chips and legend. `LogStatus.style` in
`schedule/models.py` reads these by name (`--status-<value>-bg/-fg`).

| Status | Label | Background | Text / edge bar | Contrast |
|---|---|---|---|---|
| `none` | No log | `#E2EBE9` | `#44605D` | 5.6 |
| `ok` | As scheduled | `#D7EEE5` | `#0E5A4F` | 6.7 |
| `delayed` | Delayed | `#FBE4DF` | `#9C2F22` | 6.1 |
| `many` | Many logs | `#F6F0B8` | `#6B5500` | 6.2 |

## Typography

**Inter**, loaded from Google Fonts with weights 400, 500, 600, and 700.
Identified from the kit's glyphs (two-storey `a`, single-storey `g`, straight
`K` leg, flat-topped `t`, horizontal terminals on `e` and `s`). Fallback:
`system-ui, -apple-system, 'Segoe UI', sans-serif`.

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
```

| Role | Size / line height | Weight | Tracking | Color | Kit reference |
|---|---|---|---|---|---|
| Hero headline | 48px / 1.1 (mobile 32px) | 700 | `-0.02em` | `--on-forest` | Hero headline |
| Tracked caps label | 14px / 1.2 | 500 | `0.4em`, uppercase | `--on-forest` | Label above hero headline |
| Page title | 32px / 1.2 | 700 | `-0.02em` | `--ink` | — |
| Section heading (h2) | 24px / 1.25 | 700 | `-0.01em` | `--ink` | — |
| Card heading (h3) | 18px / 1.3 | 600 | normal | `--ink` | — |
| Logo | 20px / 1 | 700 | `-0.01em` | `--teal` | Navbar wordmark |
| Body | 16px / 1.55 | 400 | normal | `--ink`, or `--on-forest-soft` on forest | Hero body copy |
| Small / labels | 14px / 1.4 | 500 | normal | `--muted` | — |
| Placeholder | 16px | 400 | normal | `--muted` | Search fields |

Rules:
- Prose lines stay under 70 characters.
- The tracked caps label appears **once**, in the home hero. Everywhere else,
  labels are sentence case.
- Numbers in tables, stats, and the calendar use `font-variant-numeric: tabular-nums`.

## Shape, spacing, depth

Radii were measured relative to element height in the kit and scaled to this
app's sizes.

| Token | Value | Use |
|---|---|---|
| `--radius-sm` | `8px` | Inputs, buttons, search field, calendar chips, badges |
| `--radius` | `12px` | Cards, tables, calendar panel |
| `--radius-lg` | `16px` | Hero panel, modal |

- The kit's inputs are **softly rounded rectangles, not pills.**
- Spacing scale (px): 4, 8, 12, 16, 24, 32, 48, 64. Panels pad 24px (hero:
  48px desktop, 24px mobile). Sections are 48px apart.
- **No drop shadows** on cards; white on mint separates them. The modal is the
  only element with a shadow: `0 24px 48px -12px rgba(8, 59, 59, 0.35)`.

## Components

Each entry names the class(es) it styles.

### Navbar — `.navbar`, `.navbar-brand`, `.navbar-menu`

- Mint background (same as the canvas), no border, 16px vertical padding.
- Logo: "Course Calendar", Inter 700, 20px, `--teal`.
- Links: 16px, 500, `--ink-soft`; hover `--ink`. Current section (optional):
  2px lime underline, 6px below the text.
- Search field (optional, if search is added): white fill, no border,
  `--radius-sm`, 44px tall, magnifier icon and placeholder in `--muted`.

### Hero panel — new `.hero` (home page only)

- Forest fill, `--radius-lg`, 48px padding (24px on mobile).
- Content, top to bottom: tracked caps label → headline → one sentence of body
  copy → optional search field.
- Hero search: a single 56px-tall field split in two, like the kit: left part
  mint with magnifier + placeholder, right part white with a `<select>`
  ("Courses ⌄") in `--ink-soft`; outer corners `--radius-sm`.
- Decorative shapes on the right, hidden below 768px, drawn with CSS:
  - lime semicircle (flat side up), about 40% of the panel height;
  - sage quarter-circle, small, top right;
  - teal leaf (two opposite corners rounded at 100%), small, overlapping the
    semicircle's edge.

### Page header — `.page-header`, `.page-title`, `.page-subtitle`, `.breadcrumbs`

- Working screens have no panel: page title in `--ink` directly on mint,
  subtitle in `--muted`.
- Breadcrumbs: 14px, `--muted`; links `--teal`.

### Buttons — `.btn` and variants, `.action-btn`

`--radius-sm`, 44px tall (sm: 36px), 16px horizontal padding, Inter 600.

| Variant | Class | Fill | Text | Border | Hover |
|---|---|---|---|---|---|
| Primary | `.btn-primary` | forest | white | none | teal fill |
| Accent | new `.btn-accent` | lime | forest | none | lime at 85% brightness |
| Secondary | `.btn-secondary`, `.action-edit` | white | forest | `--rule` | mint fill |
| Danger | `.btn-danger` | danger | white | none | darker danger |
| Danger quiet | `.action-delete` | white | danger | `--rule` | danger border |

At most **one accent button per screen** (e.g. "Add Log" in the session modal).

### Inputs — `.form-input`, `.form-select`, `.form-textarea`, `.form-group`

- Mint fill on white surfaces, white fill on mint surfaces (the kit does both).
- No border at rest; `--radius-sm`; 44px tall; text `--ink`, placeholder `--muted`.
- Focus: 1px forest border plus a 3px lime ring (`box-shadow: 0 0 0 3px var(--lime)`).
- Labels: 14px, 500, `--ink`, 6px above the field.
- Errors: 14px `--danger` text below the field; the field gets a 1px danger border.

### Cards — `.course-card`, `.topic-card`, `.panel`, `.upload-container`, `.review-form`

- White on mint, `--radius`, no border, no shadow, 24px padding.
- Course card: name (h3) → subject code as a badge → two-column details list
  (labels `--muted`, values `--ink`) → footer actions above a `--rule` line.

### Stats — `.stats`

- One white panel, four cells divided by `--rule` lines.
- Number: 32px, 700, tabular; a 10px lime dot sits before it, echoing the kit's
  lime check circles. Label: 14px `--muted`.

### Tables — `table`, `th`, `td`, `.detail-table`

- White, `--radius`, no outer border, `overflow: hidden`.
- Header row: mint fill, 14px 600 `--muted` text.
- Rows: 12px 16px padding, divided by `--rule`; hover row fill mint.

### Badges — `.badge`, `.badge-*`, `.course-code`

- `--radius-sm`, 13px, 600, 2px 8px padding.
- Default: mint fill, teal text.
- Material types: pdf → danger text on `#FBE4DF`; url → teal on mint;
  video → forest on lime; document → forest on sage; image → `--ink-soft` on
  `#E2EBE9`.

### Alerts — `.alert-*`

- `--radius-sm`, no border, 12px 16px padding.
- success → `ok` status colors; error → `delayed`; warning → `many`;
  info → forest text on mint with a 3px teal left edge.

### Modal — `.modal`, `.modal-content`

- Overlay: `rgba(8, 59, 59, 0.6)` (forest at 60%).
- Panel: white, `--radius-lg`, 28px padding, the modal shadow above.
- Title: 20px 700 `--ink`; close button `--muted`, hover `--ink` on mint.

### Steps — `.steps` (home setup guide)

- Each number sits in a 28px lime circle with forest digits, 600, the kit's
  check-circle look carrying a number (the steps are a real sequence).
- Step title 16px 600 `--ink`; description 15px `--muted`.

### Calendar — `.calendar-grid`, `.calendar-session`, `.calendar-legend`, `.calendar-nav`

- The grid sits in a white panel with `--radius`; weekday header row mint,
  14px 600 `--muted`.
- Empty (out-of-month) days: mint fill.
- **Today:** the day number sits in a 28px lime circle with forest text. This is
  the calendar's one loud element.
- Session chips: `--radius-sm`, status colors from the table above, a 3px edge
  bar on the left in the status text color, 13px text with a tabular time.
- Legend: 14px swatches in the same status colors, labels `--muted`.
- Month navigation: month name as h2 on the left; Prev/Next secondary buttons on
  the right.
- Below 768px the grid scrolls sideways inside its panel (minimum width 680px).

## Accessibility floor

- All text pairs meet WCAG AA (table above).
- Every interactive element shows focus: the lime ring from Inputs.
- `prefers-reduced-motion: reduce` disables transitions and animations.
- Layouts work from 360px wide with no page-level horizontal scroll.
- Icon-only controls (close ×, search magnifier) carry an `aria-label`.

## CSS tokens

Paste-ready `:root` block for `static/css/style.css`:

```css
:root {
    /* Kit palette */
    --forest: #083b3b;
    --white: #ffffff;
    --mint: #e7f5f2;
    --lime: #eaf140;
    --sage: #cbddbd;
    --teal: #126d61;
    --on-forest: #f8fafc;
    --on-forest-soft: #d3f1f1;
    --ink-soft: #405354;

    /* Derived */
    --ink: #083b3b;
    --muted: #5f6e6b;
    --rule: #d3e6e1;
    --danger: #b3322a;

    /* Session status (LogStatus.style) */
    --status-none-bg: #e2ebe9;
    --status-none-fg: #44605d;
    --status-ok-bg: #d7eee5;
    --status-ok-fg: #0e5a4f;
    --status-delayed-bg: #fbe4df;
    --status-delayed-fg: #9c2f22;
    --status-many-bg: #f6f0b8;
    --status-many-fg: #6b5500;

    /* Type */
    --font: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;

    /* Shape */
    --radius-sm: 8px;
    --radius: 12px;
    --radius-lg: 16px;

    color-scheme: light;
}
```
