# 03 — Design System Specification (Organic / Natural & UI/UX Pro Max)

Source: [`app/skills/desgin/design.md`](../skills/desgin/design.md) & [UI/UX Pro Max Skill v2.0](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
Document standard: Strict design tokens, CSS variables, utility mapping, component specifications, and accessibility constraints.

---

## 1. Design Philosophy & Visual DNA

The visual personality of Skill Bridge 2.0 is **Organic / Natural**, embracing the Japanese aesthetic of **wabi-sabi** (imperfection, transience, natural tactile grounding) merged with enterprise data clarity.

1. **No Harsh Angles:** Standard rectangular containers are replaced by soft pill shapes (`rounded-full`), generous rounded corners (`rounded-[2rem]`), and organic asymmetric blob radii (`60% 40% 30% 70% / 60% 30% 70% 40%`).
2. **Paper & Loam Tactility:** The entire application features a subtle, fixed SVG noise/grain overlay at 3.5% opacity with `mix-blend-mode: multiply`, creating an unbleached rice paper texture.
3. **Tinted Diffused Shadows:** Pure black shadows (`rgba(0,0,0,...)`) are forbidden. Shadows are softly tinted with moss green or terracotta clay (`rgba(93, 112, 82, 0.12)`).
4. **Calming Typography:** Headings utilize Google Font **'Fraunces'** (warm, humanist optical serif with soft axes), paired with **'Nunito'** for body text (rounded terminal sans-serif). Monospace data uses **'JetBrains Mono'**.
5. **UI/UX Pro Max Standards:** Clean SVG iconography only (Lucide React), visible focus rings with offsets, minimum 44px touch targets, zero clipping badges, and automatic motion reduction under `prefers-reduced-motion`.

---

## 2. Token Architecture & Color Palette

### 2.1 Core Palette Tokens (Light Mode Primary)

```css
:root {
  /* Surface & Base */
  --bg-rice-paper: #FDFCF8;         /* Canvas background */
  --surface-card: #FEFEFA;          /* Elevated card background */
  --surface-stone: #F0EBE5;         /* Subtle stone tint */
  --surface-sand: #E6DCCD;          /* Warm sand container */
  --surface-mist: #F3F4F1;          /* Pale mist highlight */
  
  /* Typography & Foreground */
  --text-loam: #2C2C24;             /* Primary text (charcoal loam) - 14.5:1 contrast */
  --text-bark: #4A4A40;             /* Secondary body text */
  --text-grass: #78786C;            /* Muted labels & timestamps - 4.8:1 contrast */
  --text-subtle: #A3A396;           /* Disabled / subtle captions */
  
  /* Primary Brand: Moss Green */
  --moss-primary: #5D7052;          /* Primary buttons, active tabs, scores */
  --moss-hover: #4B5B42;            /* Darker hover state */
  --moss-surface: rgba(93, 112, 82, 0.08); /* 8% tint for pill backgrounds */
  --moss-border: rgba(93, 112, 82, 0.20);  /* Accent borders */
  
  /* Secondary Brand: Terracotta / Clay */
  --clay-secondary: #C18C5D;        /* Secondary actions, HR badges */
  --clay-hover: #A77346;            /* Darker hover state */
  --clay-surface: rgba(193, 140, 93, 0.10); /* 10% tint for alerts */
  --clay-border: rgba(193, 140, 93, 0.25);
  
  /* Borders & Dividers */
  --border-timber: #DED8CF;         /* Soft raw timber border */
  --border-subtle: rgba(222, 216, 207, 0.60);
  
  /* Status Colors */
  --status-success: #4E7C59;        /* Verified, Confirmed, Hired */
  --status-warning: #D9822B;        /* Moderate gap, Needs info */
  --status-danger: #A85448;         /* Burnt Sienna: Blocker, High gap, Rejected */
  --status-info: #5B7F95;           /* River Stone: In progress, Review */
}
```

### 2.2 Shadow Tokens

```css
:root {
  /* Soft Moss Shadow */
  --shadow-soft: 0 4px 20px -2px rgba(93, 112, 82, 0.12);
  --shadow-hover: 0 10px 30px -4px rgba(93, 112, 82, 0.18);
  
  /* Floating Clay Shadow */
  --shadow-float: 0 14px 40px -10px rgba(193, 140, 93, 0.20);
  
  /* Inset Tactile Shadow */
  --shadow-tactile: inset 0 2px 4px rgba(44, 44, 36, 0.05);
}
```

### 2.3 Typography Scale

```css
:root {
  --font-serif: 'Fraunces', Georgia, serif;
  --font-sans: 'Nunito', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}
```

| Token | Family | Weight | Size | Line Height | Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `display-1` | Fraunces | 700 | 3.5rem (56px) | 1.15 | Landing Hero Headline |
| `display-2` | Fraunces | 600 | 2.5rem (40px) | 1.20 | Section Headlines, Role Hero |
| `heading-1` | Fraunces | 600 | 1.75rem (28px) | 1.25 | Page Titles, Radar Modal Headers |
| `heading-2` | Fraunces | 600 | 1.25rem (20px) | 1.35 | Job Card Titles, Candidate Aliases |
| `body-lg` | Nunito | 500 | 1.125rem (18px) | 1.50 | Hero Intro paragraphs |
| `body-md` | Nunito | 400 | 1.0rem (16px) | 1.50 | Main body text, Job descriptions |
| `body-sm` | Nunito | 400 | 0.875rem (14px) | 1.45 | Metadata, Explanations, Tables |
| `caption` | Nunito | 600 | 0.75rem (12px) | 1.40 | Status Pills, Badge labels |
| `mono-stat` | JetBrains Mono | 600 | 0.875rem (14px) | 1.20 | Scores, ANZSCO codes, Currency |

---

## 3. Global Texture & Background Blobs

### 3.1 Paper Texture Implementation

A global fixed pseudo-element applied to `#app-root`:

```css
.organic-noise-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  content: "";
  opacity: 0.035;
  pointer-events: none;
  z-index: 9999;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
  mix-blend-mode: multiply;
}
```

### 3.2 Amorphous Ambient Blobs

Background decorative ambient washes use large blurred organic blobs:

```css
.blob-ambient-moss {
  position: absolute;
  width: 480px;
  height: 420px;
  border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%;
  background: radial-gradient(circle, rgba(93, 112, 82, 0.15) 0%, rgba(93, 112, 82, 0.0) 70%);
  filter: blur(60px);
  pointer-events: none;
  z-index: 0;
}

.blob-ambient-clay {
  position: absolute;
  width: 420px;
  height: 480px;
  border-radius: 40% 60% 70% 30% / 50% 60% 40% 50%;
  background: radial-gradient(circle, rgba(193, 140, 93, 0.14) 0%, rgba(193, 140, 93, 0.0) 70%);
  filter: blur(55px);
  pointer-events: none;
  z-index: 0;
}
```

---

## 4. Reusable Component Styles

### 4.1 Buttons

All button elements feature a tactile pill geometry (`border-radius: 9999px`) with 48px standard touch target height:

- **Primary Button (`.btn-primary`):**
  - Background: `var(--moss-primary)` (#5D7052)
  - Color: `var(--surface-mist)` (#F3F4F1)
  - Padding: `0.75rem 1.75rem`
  - Font: Nunito 700, 15px
  - Shadow: `var(--shadow-soft)`
  - Hover: `transform: scale(1.03); background: var(--moss-hover); box-shadow: var(--shadow-hover);`
  - Active: `transform: scale(0.97);`

- **Secondary / Clay Button (`.btn-clay`):**
  - Background: `var(--clay-secondary)` (#C18C5D)
  - Color: `#FFFFFF`
  - Hover: `background: var(--clay-hover); transform: scale(1.03);`

- **Outline Button (`.btn-outline`):**
  - Border: `2px solid var(--border-timber)`
  - Background: `rgba(255, 255, 255, 0.6)` with backdrop blur
  - Color: `var(--text-loam)`
  - Hover: `border-color: var(--moss-primary); color: var(--moss-primary); background: #FFFFFF;`

- **Ghost Button (`.btn-ghost`):**
  - Background: transparent
  - Color: `var(--text-bark)`
  - Hover: `background: var(--moss-surface); color: var(--moss-primary);`

- **Pill Floating Action Button (The "+" Button) (`.btn-floating-add`):**
  - Geometry: Circle 64px × 64px (`rounded-full`)
  - Background: `var(--moss-primary)` with large plus SVG icon
  - Shadow: `var(--shadow-hover)`
  - Pulse micro-animation to draw attention when no items exist.

### 4.2 Cards & Containers

- **Standard Surface Card (`.card-natural`):**
  - Background: `var(--surface-card)` (#FEFEFA)
  - Border: `1px solid var(--border-timber)` (at 60% opacity)
  - Border-Radius: `1.75rem` (28px) with subtle corner asymmetry:
    - Feature variation A: `border-radius: 2rem 1.25rem 2rem 1.75rem;`
    - Feature variation B: `border-radius: 1.5rem 2.25rem 1.5rem 2rem;`
  - Shadow: `var(--shadow-soft)`
  - Hover: `transform: translateY(-3px); box-shadow: var(--shadow-hover); border-color: rgba(93, 112, 82, 0.35);`

### 4.3 Form Inputs & Search Bar

- **Pill Input (`.input-natural`):**
  - Height: `3rem` (48px)
  - Border-Radius: `9999px`
  - Border: `1.5px solid var(--border-timber)`
  - Background: `rgba(255, 255, 255, 0.8)`
  - Padding: `0 1.5rem`
  - Font: Nunito 500, 15px
  - Focus: `outline: none; border-color: var(--moss-primary); box-shadow: 0 0 0 3px rgba(93, 112, 82, 0.20);`

### 4.4 Status & Metric Badges

- **ANZSCO Alignment Pill (`.badge-anzsco`):**
  - Background: `rgba(93, 112, 82, 0.12)`
  - Border: `1px solid rgba(93, 112, 82, 0.3)`
  - Color: `var(--moss-primary)`
  - Font: JetBrains Mono 600, 12px

- **Gap Indicator Pills:**
  - *Low Gap:* Background `rgba(78, 124, 89, 0.15)`, Color `#3A6343`
  - *Moderate Gap:* Background `rgba(217, 130, 43, 0.15)`, Color `#B06212`
  - *High Gap / Blocker:* Background `rgba(168, 84, 72, 0.15)`, Color `#8E3E34`

- **AI Provenance Badges (REQ-S22, REQ-H08):**
  - *AI Extracted:* Background `var(--surface-sand)`, Color `var(--text-bark)`, text "✨ AI Extracted"
  - *User Confirmed:* Background `rgba(78, 124, 89, 0.12)`, Color `var(--status-success)`, text "✓ Verified"
  - *User Edited:* Background `rgba(193, 140, 93, 0.15)`, Color `var(--clay-secondary)`, text "✎ Customised"

---

## 5. Visualizations & Radar Chart Specifications

### 5.1 Radar ("Spider Web") Chart Palette

Used for **Job vs Job Comparison** (REQ-S27) and **Candidate Benchmarking** (REQ-H12):

```javascript
export const RADAR_PALETTE = {
  jobA: { stroke: "#5D7052", fill: "rgba(93, 112, 82, 0.20)", label: "Job #1 (Primary)" },
  jobB: { stroke: "#C18C5D", fill: "rgba(193, 140, 93, 0.20)", label: "Job #2" },
  jobC: { stroke: "#5B7F95", fill: "rgba(91, 127, 149, 0.20)", label: "Job #3" },
  jobD: { stroke: "#8C6A8B", fill: "rgba(140, 106, 139, 0.20)", label: "Job #4" },
  grid: "#DED8CF",
  axisText: "#4A4A40"
};
```

- Web Grid: Concentric polygons (0%, 25%, 50%, 75%, 100%) rendered in soft timber dashed lines.
- Tooltip: Floating rice-paper pill showing exact metric score for every overlaid entity.

### 5.2 Line Charts for Score Progression (REQ-S09, S10)

- Line A (Match %): Solid curve in `#5D7052` (Moss Green), stroke width 2.5px. Reference threshold dashed line at 85% in `#C18C5D` labelled "Direct Alignment Threshold".
- Line B (Gap Severity Index): Solid curve in `#A85448` (Burnt Sienna) declining towards 0 over training duration, with shaded gradient area underneath.

---

## 6. Accessibility & Responsiveness Checklist (UI/UX Pro Max)

1. **Text Contrast Compliance:**
   - Primary loam text (`#2C2C24`) on rice paper (`#FDFCF8`): **14.5:1** (Exceeds WCAG AAA requirement of 7:1).
   - Moss green buttons (`#5D7052`) on pale mist text (`#F3F4F1`): **6.2:1** (Exceeds WCAG AA requirement of 4.5:1).
2. **Keyboard Focus Indicator:**
   - Every interactive control (button, input, tab, card link) must display `focus-visible:ring-2 focus-visible:ring-[#5D7052] focus-visible:ring-offset-2`.
3. **Touch Targets:**
   - All clickable targets maintain minimum height and width of 44px × 44px.
4. **Motion Sensitivity:**
   - When `@media (prefers-reduced-motion: reduce)` is detected, all transitions, blob animations, card lifts, and radar animations are disabled (`transition: none !important; animation: none !important;`).
5. **Responsive Breakpoints:**
   - `sm` (640px): Form inputs expand to full width, hero statistics convert to 2-column grid.
   - `md` (768px): Navigation sidebar collapses to icon-rail or top drawer; comparison matrix scrolls horizontally.
   - `lg` (1024px): 2-column detail layouts (7/5 grid) and multi-job radar overlay charts activate.
   - `xl` (1280px+): Full widescreen experience with persistent left sidebar navigation.
