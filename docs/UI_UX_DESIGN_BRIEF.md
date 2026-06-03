# UI/UX Design Brief
## Project Name: Fender - Automobile Garage Management System

---

## 1. Design Philosophy
The Fender user interface is designed with a **Flat, Minimalist, Dark Mode First** aesthetic. It focuses on functional information density, high contrast readability, and a professional administrative tool feel. 

To maintain an academic focus and ensure code maintainability:
- **No Gradients**: All color fills are flat, solid values to look professional and avoid a cluttered appearance.
- **No Glassmorphism**: Cards and overlays use flat solid backdrops with fine dark border dividers to clearly separate components.
- **Responsive Layout**: Designed utilizing the standard 12-column grid of Bootstrap 5.
- **High Typography Contrast**: Bright grey text set against deep dark backgrounds, with clear font weight distinctions for hierarchy.

---

## 2. Color Palette
Fender uses a global dark color scheme. Below are the precise hex values to be implemented in `static/css/style.css`:

```css
:root {
    /* Backgrounds */
    --bg-global: #121212;      /* Deep dark grey base */
    --bg-card: #1e1e1e;        /* Slightly raised card background */
    --bg-sidebar: #181818;     /* Intermediate dark grey for navigation sidebar */
    --bg-input: #2a2a2a;       /* Dark form input fields background */

    /* Borders & Lines */
    --border-color: #2d2d2d;   /* Fine dividers between elements */
    --border-focus: #3b82f6;   /* Input focus boundary color */

    /* Typography */
    --text-primary: #e0e0e0;   /* Readable light grey for body and headings */
    --text-secondary: #8a8a8a; /* Muted grey for metadata, labels, and timestamps */
    --text-muted: #555555;     /* Darker grey for disabled elements */

    /* Status Accents (Flat, Solid) */
    --color-primary: #3b82f6;  /* Cobalt Blue (Brand, Edit actions) */
    --color-success: #10b981;  /* Emerald Green (Completed status, Paid invoices) */
    --color-warning: #f59e0b;  /* Amber Yellow (Pending status, Partially Paid) */
    --color-danger: #ef4444;   /* Crimson Red (Cancelled status, Unpaid invoices, Low Stock warnings) */
    --color-info: #06b6d4;     /* Cyan (In Progress status) */
}
```

---

## 3. Typography & Hierarchy
- **Primary Body and Headings Font**: **Inter** or **Outfit** (imported via Google Fonts).
- **Monospace Font (SQL/DBMS Showcases)**: **SFMono-Regular**, **Consolas**, or **Courier New** for readability of code blocks and log outputs.
- **Font Scale Hierarchy**:
  - `h1` (Dashboard Title): `1.75rem` / Semibold (`font-weight: 600`)
  - `h2` (Section Headers): `1.25rem` / Medium (`font-weight: 500`)
  - `h3` (Card Titles): `1.0rem` / Semibold (`font-weight: 600`)
  - Body Text: `0.875rem` / Regular (`font-weight: 400`)
  - Small / Badges: `0.75rem` / Bold (`font-weight: 700`)

---

## 4. UI Layout Architecture
The overall application viewport is structured with a split layout:

```text
┌─────────────────────────────────────────────────────────────┐
│                       TOP NAVBAR                            │
├─────────┬───────────────────────────────────────────────────┤
│         │                                                   │
│  LEFT   │                 MAIN VIEWPORT                     │
│  SIDE-  │                                                   │
│  BAR    │  ┌──────────────┐ ┌──────────────┐ ┌───────────┐  │
│         │  │  Stat Card   │ │  Stat Card   │ │ Stat Card │  │
│  (Fixed)│  └──────────────┘ └──────────────┘ └───────────┘  │
│         │                                                   │
│         │  ┌─────────────────────────────────────────────┐  │
│         │  │             Data Table                      │  │
│         │  └─────────────────────────────────────────────┘  │
│         │                                                   │
└─────────┴───────────────────────────────────────────────────┘
```

- **Sidebar (Fixed Left)**:
  - Width: `260px` on desktop.
  - Collapses into a toggleable overlay on mobile viewports.
  - Contains: Garage Branding Logo (`Fender`), active staff user badge (Full Name + role indicator badge), and vertical navigation list with Bootstrap Icons (`bi-*`).
- **Top Navbar**:
  - Dynamic breadcrumb displaying active path (e.g. `Dashboard / Service Jobs`).
  - Action buttons (e.g. "New Service Job" shortcut).
  - Quick User controls: dropdown with logout.
- **Main Viewport (Right)**:
  - Fluid scrolling content area with a max-width container to prevent layout stretching on ultra-wide screens.

---

## 5. UI Components

### 5.1 Metrics Cards (KPIs)
- Borderless flat boxes with a subtle border divider.
- Right-aligned icons colored with the corresponding status accent (e.g. Danger red for Low Stock).
- Big numerical indicators for quick dashboard overview.

### 5.2 Responsive Tables
- Standard Bootstrap `.table-dark`, `.table-hover`, and `.align-middle` classes.
- Borderless cell walls; solid row divider lines.
- Left-aligned text columns; right-aligned currency/total columns.
- Actions column with small, flat, icon-only buttons (`btn-sm`).

### 5.3 Forms and Modals
- Forms should use floating labels (`.form-floating`) for input fields.
- Form inputs styled with a dark background (`var(--bg-input)`), light text, and outline focus glow (`var(--border-focus)`).
- Dropdowns (`select` tags) mapped to match DB enum constraints.
- Modals configured with `.modal-content` background overriding standard white to card background (`var(--bg-card)`).

### 5.4 Badge Indicators
Statuses are rendered using custom-colored solid pills:
- **Pending / Partially Paid**: `bg-warning` (Amber Yellow) with dark text.
- **In Progress**: `bg-info` (Cyan) with dark text.
- **Completed / Paid**: `bg-success` (Emerald Green) with white text.
- **Cancelled / Unpaid / Low Stock**: `bg-danger` (Crimson Red) with white text.

---

## 6. Chart.js Configurations (Client-Side Analytics)
All charts are rendered dynamically in `<canvas>` tags using Chart.js, pulling data from JSON API endpoints. The charts match the global color palette:

- **Revenue Trend (Line / Bar Chart)**:
  - Fill Color: `#3b82f6` (Primary Blue) with `0.4` opacity.
  - Border Color: `#3b82f6`.
  - Gridlines: `#2d2d2d`.
- **Job Status Distribution (Doughnut Chart)**:
  - Segment Colors: `['#10b981', '#f59e0b', '#06b6d4', '#ef4444']` representing Completed, Pending, In Progress, and Cancelled.
- **Inventory breakdown (Pie Chart)**:
  - Palette cycles through Primary Blue, Cyan, Green, and Purple to separate categories clearly.
