---
name: Jinder
description: Design system for Jinder (Job + Tinder), a skills-based job-matching platform. Based on June (june.so) colors and components, with Clay typography (Plain Black / Inter). Warm sand page with white cards, navy ink, pastel tint chips, flat and professional.
colors:
  primary: "#151531"
  ink: "#151531"
  ink-deep: "#0d131b"
  ink-soft: "#2a2a63"
  body: "#343a40"
  muted: "#868e96"
  muted-soft: "#adb5bd"
  disabled: "#ced4da"
  on-primary: "#ffffff"
  canvas: "#ffffff"
  surface-soft: "#fafafa"
  sand: "#fdfbf8"
  sand-strong: "#f8f4ed"
  sand-line: "#f2ece3"
  surface-subtle: "#f8f9fa"
  surface-muted: "#f6f8f9"
  surface-strong: "#edf0f2"
  surface-dark: "#151531"
  hairline: "#e9ecef"
  hairline-alpha: "rgba(13, 19, 27, 0.10)"
  separator: "#e6ecf0"
  accent: "#6868f7"
  accent-tint: "#f0f0fe"
  orange: "#ffa340"
  orange-strong: "#f27c0d"
  orange-tint: "#ffe9c8"
  gold: "#ffa340"
  gold-tint: "#fff5c7"
  gold-ink: "#7a651e"
  series-1: "#6868f7"
  series-2: "#c66714"
  series-3: "#003d5a"
  series-4: "#298040"
  series-5: "#560059"
  tint-pink: "#f9e2fb"
  tint-pink-ink: "#560059"
  tint-blue: "#c9f0ff"
  tint-blue-ink: "#003d5a"
  tint-green: "#daf9d4"
  tint-green-ink: "#005900"
  tint-yellow: "#fff5c7"
  tint-yellow-ink: "#a68716"
  tint-rose: "#ffd2e1"
  tint-rose-ink: "#800000"
  success: "#32ae47"
  success-tint: "rgba(50, 174, 71, 0.10)"
  error: "#f53d3d"
  selection: "rgba(29, 161, 242, 0.08)"
typography:
  display-font: '"Plain Black", Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
  body-font: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
  display-xl: { size: 72px, weight: 500, lineHeight: 1.0, letterSpacing: -2.5px }
  display-lg: { size: 56px, weight: 500, lineHeight: 1.05, letterSpacing: -2px }
  display-md: { size: 40px, weight: 500, lineHeight: 1.1, letterSpacing: -1px }
  display-sm: { size: 32px, weight: 500, lineHeight: 1.15, letterSpacing: -0.5px }
  title-lg: { size: 24px, weight: 600, lineHeight: 1.3, letterSpacing: -0.3px }
  title-md: { size: 18px, weight: 600, lineHeight: 1.4, letterSpacing: 0 }
  title-sm: { size: 16px, weight: 600, lineHeight: 1.4, letterSpacing: 0 }
  lead: { size: 18px, weight: 400, lineHeight: 1.55, letterSpacing: 0 }
  body-md: { size: 16px, weight: 400, lineHeight: 1.55, letterSpacing: 0 }
  body-sm: { size: 14px, weight: 400, lineHeight: 1.55, letterSpacing: 0 }
  label: { size: 13px, weight: 500, lineHeight: 1.4, letterSpacing: 0 }
  caption: { size: 13px, weight: 500, lineHeight: 1.4, letterSpacing: 0 }
  caption-uppercase: { size: 12px, weight: 600, lineHeight: 1.4, letterSpacing: 1.5px }
  nav-link: { size: 14px, weight: 500, lineHeight: 1.4, letterSpacing: 0 }
  button: { size: 14px, weight: 600, lineHeight: 1.0, letterSpacing: 0 }
spacing:
  xxs: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
  xxxl: 64px
  section: 96px
rounded:
  xs: 6px
  sm: 8px
  md: 10px
  lg: 12px
  xl: 20px
  xxl: 24px
  pill: 9999px
shadows:
  xs: "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
  sm: "0 1px 3px 0 rgba(0, 0, 0, 0.10), 0 1px 2px 0 rgba(0, 0, 0, 0.06)"
  md: "0 4px 6px -1px rgba(0, 0, 0, 0.10), 0 2px 4px -2px rgba(0, 0, 0, 0.10)"
  popover: "0 2px 10px 0 rgba(13, 19, 27, 0.10), 0 0 2px 0 rgba(13, 19, 27, 0.20)"
  key: "0 0 1px 0 rgba(13, 19, 27, 0.25), 0 2px 1px 0 rgba(13, 19, 27, 0.05)"
  inset-ring: "inset 0 0 0 1px rgba(13, 19, 27, 0.05)"
---

## Overview

### About this document
This document is the design system for **Jinder**. Jinder translates overseas and cross-industry experience into skills that Australian employers recognise. It has two user groups: international talent and employers.

The system has three sources:
- **Colors, spacing, radius, shadows and components:** June (june.so).
- **Typography:** Clay (see `DESIGN_Clay.md`).
- **Brand, logo and product components:** Jinder (see [Brand & Logo](#brand--logo) and [Jinder Components](#jinder-components)).

The reference build is in `../app/`. Use this document and the build together. If they do not agree, this document is correct.

This document is one of three portable files. With `prompt.md` (build steps and the API contract) and `AI_Rule.md` (rules), it is enough to build the same frontend on a different computer. This document describes how the frontend looks. `prompt.md` describes how it works.

The visual direction is **flat, minimal and trustworthy**. This is the recommended style for recruitment products. The product shows people's careers. Thus, the UI must look calm, honest and professional, not playful.

### Origin: June
June (june.so) is the friendliest-looking product analytics tool in the B2B SaaS category. Where Amplitude and Mixpanel feel like instrument panels, June set out to be "warm and welcoming in a space that's often cold and intimidating" — and the design system says so at every level. The base atmosphere is a **clean white canvas** (`{colors.canvas}` — #ffffff) carrying **deep navy ink** (`{colors.ink}` — #151531) instead of pure black, set in **Plain Black** (substituted with Inter at weight 500) at very large sizes with negative letter-spacing — confident and warm without needing heavy weight.

Color voltage comes in small, controlled doses: a **periwinkle accent** (`{colors.accent}` — #6868f7), a **warm orange** (`{colors.orange}` — #ffa340), and a family of **pastel tinted chips** — pink, blue, green, yellow, rose — each paired with its own deep ink color of the same hue. These tints label report categories, plans and features. They are never used as large full-bleed blocks; the canvas stays white and calm, and the tints act like colored sticky notes on it.

**Key Characteristics:**
- A warm sand page (`{colors.sand}` — #fdfbf8) with white cards and panels on top. It is easier on the eyes than pure white in long sessions, and it matches the orange in the logo. The landing page has one white band ("How it works") and one darker sand band (`{colors.sand-strong}`).
- Navy ink (`{colors.ink}` — #151531) for headlines, nav and the primary button — never #000.
- Plain Black (or Inter 500 substitute) is the display voice at weight 500 with -0.5 to -2.5px letter-spacing. Inter handles body, navigation, buttons and UI.
- Pastel tint + same-hue deep ink pairs (`{colors.tint-blue}` / `{colors.tint-blue-ink}`, etc.) for category labels and plan headers.
- Compact, rounded controls: primary button 36px tall, `{rounded.md}` (10px). Cards `{rounded.xl}` (20px).
- Almost flat: shadows are tiny (1–3px blur) and used on buttons, popovers and floating cards only.
- Inline links are **bold periwinkle text with no underline** (`{component.text-link}`).
- A dark navy band (`{colors.surface-dark}`) appears sparingly for announcement / closing CTAs with white 40px/500 headlines.

## Colors

### Brand & Accent
- **Primary** (`{colors.primary}` — #151531): Primary CTA background, headlines, nav links, logo mark. Navy with a slight violet cast.
- **Accent** (`{colors.accent}` — #6868f7): Periwinkle. Link text, focus/active states, highlighted UI, chart series 1.
- **Accent Tint** (`{colors.accent-tint}` — #f0f0fe): Very light periwinkle surface for callout cards (e.g. the founder letter card).
- **Orange** (`{colors.orange}` — #ffa340): Warm accent for badges, highlights and illustrations. Strong variant `{colors.orange-strong}` (#f27c0d); tint `{colors.orange-tint}` (#ffe9c8).
  The CSS custom property `--orange-strong` (#f27c0d) is defined in `app/styles-core.css`, with the other tokens that `styles.css` does not have. Use it as the base of chart series 2. Do not use it for text.

### Pastel Tint Pairs
Always used as a pair — tint as background, same-hue ink as text. Never put body gray on a tint.

| Pair | Background | Ink | Typical use |
|---|---|---|---|
| Pink | `{colors.tint-pink}` #f9e2fb | `{colors.tint-pink-ink}` #560059 | Engagement / feature reports |
| Blue | `{colors.tint-blue}` #c9f0ff | `{colors.tint-blue-ink}` #003d5a | "All-in-one" plan header, company reports |
| Green | `{colors.tint-green}` #daf9d4 | `{colors.tint-green-ink}` #005900 | Retention, success, "included" labels |
| Yellow | `{colors.tint-yellow}` #fff5c7 | `{colors.tint-yellow-ink}` #a68716 | Activation, highlights |
| Rose | `{colors.tint-rose}` #ffd2e1 | `{colors.tint-rose-ink}` #800000 | Churn / at-risk signals |

### Surface
- **Canvas** (`{colors.canvas}` — #ffffff): Default page floor.
- **Sand** (`{colors.sand}` — #fdfbf8): The page background of the whole app: landing, sign in / create account (form side), legal pages and every signed-in screen.
- **Sand Strong** (`{colors.sand-strong}` — #f8f4ed): A darker sand band on the landing page (audience cards).
- **Sand Line** (`{colors.sand-line}` — #f2ece3): Hairlines on sand (top nav, market block, footer).
- **Surface Soft** (`{colors.surface-soft}` — #fafafa): Not a page background any more. Kept for small fills inside white cards (for example compare tables).
- **Surface Subtle** (`{colors.surface-subtle}` — #f8f9fa): Table headers, FAQ rows, inputs on soft bands.
- **Surface Muted** (`{colors.surface-muted}` — #f6f8f9) / **Surface Strong** (`{colors.surface-strong}` — #edf0f2): Pressed states, skeletons, inactive tracks.
- **Surface Dark** (`{colors.surface-dark}` — #151531): Announcement and closing CTA bands.
- **Hairline** (`{colors.hairline}` — #e9ecef): 1px borders on cards, nav, tables. `{colors.hairline-alpha}` for borders over tinted surfaces.

### Text
- **Ink** (`{colors.ink}` — #151531): Headlines, nav, emphasized labels.
- **Ink Deep** (`{colors.ink-deep}` — #0d131b): Largest hero h1 on product pages.
- **Ink Soft** (`{colors.ink-soft}` — #2a2a63): Inline links and secondary headings in letter-style content.
- **Body** (`{colors.body}` — #343a40): Default running text.
- **Muted** (`{colors.muted}` — #868e96): Captions, meta, footer links.
- **Muted Soft** (`{colors.muted-soft}` — #adb5bd) / **Disabled** (`{colors.disabled}` — #ced4da): Placeholders, disabled text, footer fine print.
- **On Primary** (`{colors.on-primary}` — #ffffff): Text on primary buttons and dark bands.

### Semantic
- **Success** (`{colors.success}` — #32ae47) with `{colors.success-tint}` background.
- **Error** (`{colors.error}` — #f53d3d).
- **Selection** (`{colors.selection}`): Table-row / text selection highlight.

### Premium (gold)
Premium has its own colour set. It is the **orange** family. It marks Premium parts. The skill tables also use the gold pair for the state "Below" (the talent has the skill below the asked level). Only `styles-core.css` defines the set.
- **Gold** (`{colors.gold}` — #ffa340, the same as `{colors.orange}`): the crown fill, the ring round the avatar, the borders of Premium parts (the plan card, the `locked-badge`).
- **Gold tint** (`{colors.gold-tint}` — #fff5c7, the same as `{colors.tint-yellow}`): the background of the gold chip.
- **Gold ink** (`{colors.gold-ink}` — #7a651e): the text of the gold chip and the outline of the crown. It is `{colors.tint-yellow-ink}` mixed 70% with `{colors.ink}`. Contrast on gold tint: **5.2 : 1**. The plain `{colors.tint-yellow-ink}` has only 3.1 : 1 on its tint, so a gold chip must not use it.
- The colours are made with `color-mix()` inside `@supports`. A browser without `color-mix` uses the plain tokens.

### Chart series colours and contrast
A line on white needs a contrast of 3 : 1 or more. The plain tokens `{colors.orange}` (2.0 : 1) and `{colors.success}` (2.9 : 1) are too light, so series 2 and 4 use darker mixes with `{colors.ink}`.

| Series | Token | Colour | Contrast on white |
|---|---|---|---|
| 1 | `{colors.series-1}` = `{colors.accent}` | #6868f7 | 4.3 : 1 |
| 2 | `{colors.series-2}` = `{colors.orange-strong}` mixed 80% with `{colors.ink}` | #c66714 | 3.9 : 1 |
| 3 | `{colors.series-3}` = `{colors.tint-blue-ink}` | #003d5a | 11.6 : 1 |
| 4 | `{colors.series-4}` = `{colors.success}` mixed 70% with `{colors.ink}` | #298040 | 4.9 : 1 |
| 5 | `{colors.series-5}` = `{colors.tint-pink-ink}` | #560059 | 13.6 : 1 |

Colour is never the only signal. Each series also has its own line style and marker (see `radar-chart`).

### Known design debt (low contrast, not changed)
Two styles that exist from the first version are **below 4.5 : 1**. They are open design debt. Replace them when you can. Do not use them for new text.
- `.chip-yellow` (`{colors.tint-yellow-ink}` on `{colors.tint-yellow}`): **3.1 : 1**. The gold chip (`chip-gold`) and the "Below" cells of the skill tables use the darker gold ink instead.
  The old yellow chip is still in use for the skill gaps on the job card, and for the gap count and the "Below level" chip of "Your path to this job".
- `{colors.muted}` text (the `.hint` class) on white: **3.3 : 1**. The small hints that Version 2 added use `{colors.body}` instead. The old hints are not changed.

## Typography

> Font system adopted from `DESIGN_Clay.md` (Plain Black + Inter). Colors, spacing, radius and components remain June.

### Font Family
**Plain Black** (a custom rounded display face) carries headlines; **Inter** handles body, navigation, buttons and UI. Plain Black at weight 500 with negative letter-spacing handles every display headline; Inter handles the rest. The fallback stack walks `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` for both.

### Hierarchy

| Token | Size | Weight | Line Height | Letter Spacing | Use |
|---|---|---|---|---|---|
| `{typography.display-xl}` | 72px | 500 | 1.0 | -2.5px | Hero h1 — Plain Black |
| `{typography.display-lg}` | 56px | 500 | 1.05 | -2px | Section heads — Plain Black |
| `{typography.display-md}` | 40px | 500 | 1.1 | -1px | Sub-section heads, dark-band headlines |
| `{typography.display-sm}` | 32px | 500 | 1.15 | -0.5px | CTA-band heads, auth-card titles, metric numbers |
| `{typography.title-lg}` | 24px | 600 | 1.3 | -0.3px | Plan names, FAQ head, feature-card titles |
| `{typography.title-md}` | 18px | 600 | 1.4 | 0 | Card titles, intro paragraphs |
| `{typography.title-sm}` | 16px | 600 | 1.4 | 0 | Small card titles, list labels, FAQ questions |
| `{typography.lead}` | 18px | 400 | 1.55 | 0 | Hero sub-headline |
| `{typography.body-md}` | 16px | 400 | 1.55 | 0 | Default running text |
| `{typography.body-sm}` | 14px | 400 | 1.55 | 0 | Pricing feature lists, FAQ answers, footer |
| `{typography.label}` | 13px | 500 | 1.4 | 0 | Tint chips, tab labels, table headers |
| `{typography.caption}` | 13px | 500 | 1.4 | 0 | Badge labels, captions, meta |
| `{typography.caption-uppercase}` | 12px | 600 | 1.4 | 1.5px | Section eyebrow labels, "FEATURED" badges |
| `{typography.nav-link}` | 14px | 500 | 1.4 | 0 | Top navigation items (Inter) |
| `{typography.button}` | 14px | 600 | 1.0 | 0 | Button labels (Inter) |

### Principles
Plain Black at weight 500 + negative letter-spacing IS the display voice. Going to weight 700 reads as bombastic; the rounded character of the typeface adds warmth that bolder weight would flatten.

The body-vs-display split is functional: Plain Black for headlines, Inter for everything else (running text, UI, buttons, nav). Mixing them is a system violation.

### Note on Font Substitutes
If Plain Black is unavailable, **Inter** at weight 500 with -0.05em letter-spacing is a usable approximation. **Söhne Breit** at weight Buch is an alternative if licensed. **Recoleta** at weight 500 carries similar rounded-display warmth.

## Layout

### Spacing System
- **Base unit:** 4px.
- **Tokens:** `{spacing.xxs}` 4px · `{spacing.xs}` 8px · `{spacing.sm}` 12px · `{spacing.md}` 16px · `{spacing.lg}` 24px · `{spacing.xl}` 32px · `{spacing.xxl}` 48px · `{spacing.xxxl}` 64px · `{spacing.section}` 96px.
- **Hero:** h1 followed by `{spacing.xxxl}` (64px) before the next block.
- **Card internal padding:** `{spacing.xl}` (32px) on desktop, `{spacing.lg}` (24px) on mobile.

### Grid & Container
- **Max content width:** ~1200px for marketing grids; ~640px for letter / long-form reading columns.
- **Hero:** centered single column — h1, lead, button row, then a product screenshot.
- **Feature grids:** 3-up desktop, 2-up tablet, 1-up mobile.
- **Pricing:** plan cards side by side with a comparison table below.

### Whitespace Philosophy
Lots of white, centered compositions, short lines. The page should feel like a calm, friendly document, not a dense dashboard. Color is added through small tinted chips and product screenshots, not big colored backgrounds.

## Elevation & Depth

| Level | Treatment | Use |
|---|---|---|
| Flat | No shadow, no border | Page sections, nav, hero |
| Hairline | 1px `{colors.hairline}` | Cards, tables, inputs |
| Tinted | Pastel tint fill, no shadow | Chips, plan headers, callout cards |
| Raised XS | `{shadows.xs}` | Primary / secondary buttons |
| Raised SM | `{shadows.sm}` | Floating product screenshots, cards on hover-free lists |
| Popover | `{shadows.popover}` | Dropdown menus (Product, Content), tooltips |
| Key | `{shadows.key}` | Keyboard-key style buttons and toggles |

No heavy shadows anywhere. Depth comes from white-on-soft-gray contrast and tiny, crisp shadows.

## Shapes

### Border Radius Scale

| Token | Value | Use |
|---|---|---|
| `{rounded.xs}` | 6px | Chips, small tags, menu items |
| `{rounded.sm}` | 8px | Inputs, small cards, table containers |
| `{rounded.md}` | 10px | Buttons |
| `{rounded.lg}` | 12px | Screenshot frames, tab corners |
| `{rounded.xl}` | 20px | Feature cards, letter / callout cards, plan cards |
| `{rounded.xxl}` | 24px | Large dark CTA bands |
| `{rounded.pill}` | 9999px | Badges, toggles, avatars |

The logo mark is a rounded square (`{rounded.md}` at 40px). Use the same softness on all interactive items. Do not use 0px corners.

## Brand & Logo

### Name
**Jinder** = **J**ob + T**inder**. Talent and jobs "match", as on a swipe app. The tone stays professional: the match is based on skills, and every match is explained.

- Write the name as one word with a capital J: **Jinder**. Do not write "JINDER", "jinder" or "Jin-der" in UI text.
- Some internal keys (for example, `sb_users` in `localStorage`) still use the legacy prefix `sb_`. Users do not see them.

### Logo mark
The mark is two swiped cards on a rounded square, with a check badge where the cards overlap:
- **Left card, `{colors.accent}`, turned -12°:** the talent profile.
- **Right card, `{colors.orange}`, turned +12°:** the job.
- **Check badge, white circle with a navy check:** the match.

| Part | Specification |
|---|---|
| Canvas | 40 × 40 viewBox, `rx="10"` |
| Background | `{colors.primary}` |
| Left card | `rect x=8.5 y=9 w=13 h=18 rx=3`, `rotate(-12 15 18)`, `{colors.accent}` |
| Right card | `rect x=18.5 y=9 w=13 h=18 rx=3`, `rotate(12 25 18)`, `{colors.orange}` |
| Badge | `circle cx=20 cy=27 r=6`, white fill, 1.5 stroke in the background color |
| Check | `M17.4 27.1 l1.8 1.8 3.4-3.6`, stroke 1.8, round caps and joins, background color |

Files: `app/logo.svg` (favicon) and the `#logo` symbol in `app/icons.svg` (UI). The two files must look the same.

### Wordmark
- Text: **Jinder**, one word.
- Font: `{typography.display-font}`, 18px, weight 600, letter-spacing -0.4px.
- "J" is `{colors.accent}` (the "Job" in the name). "inder" is `{colors.ink}`.
- Markup: `<span class="logo-word"><span>J</span>inder</span>`.
- Gap between mark and wordmark: 10px. Mark size in the nav: 32px.

### Logo on dark surfaces
On `{colors.surface-dark}`, invert the mark:
- Background becomes white.
- The badge becomes `{colors.primary}` and the check becomes white.
- The cards keep their colors.
- "inder" becomes white. "J" becomes `#b7b7fb` (light accent).

In the build, add the class `on-dark` to the parent. The mark reads its colors from the CSS custom properties `--lm-bg` (background, badge stroke and check) and `--lm-line` (badge fill).

> **Caution:** Page CSS does not apply inside an external sprite (`icons.svg#logo`). Put the logo colors in inline `style` attributes in the symbol, with fallbacks (for example, `fill: var(--lm-bg, #151531)`). If you use classes, the mark shows incorrectly.

### Slogan
**Where skills meet their match.**

- The slogan connects the name (a match) with the product promise (skills first).
- Use the slogan with the logo, in the footer, on the auth pages and in the home page title.
- Write it in English, with the final period.
- Do not change the words or translate them.
- Font: `{typography.display-font}`, 18px, weight 500, letter-spacing -0.3px, `{colors.ink}`.
- On dark surfaces: 15px, white at 70% opacity.

### Logo rules
- Keep clear space of 8px or more around the mark.
- Do not show the mark smaller than 16px.
- Do not change the card colors. They show the two sides of a match.
- Do not add shadows, gradients or outlines to the mark.
- Do not use a heart or other dating symbols. Jinder is a hiring product.

## Components

### Top Navigation

**`top-nav`** — Sand bar (`{colors.sand}`) at 92% opacity with a light blur, 64px tall, sticky, 1px `{colors.sand-line}` bottom border. Logo at left. Menu links in `{typography.nav-link}`: "How it works", "For talent", "For employers". Each link has 8px × 12px padding and `{rounded.sm}`. The active link (`aria-current="page"`) has a `{colors.surface-muted}` background. At right: a "Sign in" text link and a `{component.button-primary}` "Get started".

### Buttons

**`button-primary`** — Background `{colors.primary}` (#151531), text `{colors.on-primary}`, type `{typography.button}` (Inter 14px / 600), padding 8px × 12px, height 36px, rounded `{rounded.md}` (10px), shadow `{shadows.xs}`. Large hero variant: height 44px, padding 12px × 20px, 16px label.

**`button-secondary`** — Background `{colors.canvas}`, text `{colors.ink}`, 1px `{colors.hairline}` border plus `{shadows.xs}`. Same size as primary.

**`button-on-dark`** — White background, `{colors.ink}` text, used on `{colors.surface-dark}` bands.

**`text-link`** — All inline links (for example, "Forgot password?", "Create one", "Sign in", "Edit"). Text is `{colors.accent}` at weight 600, with no underline. On hover, the color changes to `{colors.ink-soft}`. Do not use underlines for links. Use the same style for all inline links in the app.

**`legal-link`** — Links to Terms of Use and Privacy Policy. Same style as `text-link`. On the sign-in and sign-up pages, these links open in a new tab (`target="_blank" rel="noopener"`). Thus, the user does not lose the data in the form. Add the screen-reader text "(opens in a new tab)".

### Cards & Containers

**`hero-band`** — Centered on `{colors.canvas}`. h1 in `{typography.display-xl}` `{colors.ink-deep}`, lead in `{typography.lead}` `{colors.body}`, button row, then a product screenshot in `{component.screenshot-frame}`.

**`screenshot-frame`** — Product UI image on white, 1px `{colors.hairline}`, `{rounded.lg}`, `{shadows.sm}`.

**`feature-card`** — White, 1px `{colors.hairline}`, `{rounded.xl}`, padding `{spacing.xl}`. Top: `{component.tint-chip}`; then title in `{typography.title-lg}`; body in `{typography.body-md}`; optional small report screenshot.

**`letter-card`** — Long-form callout on `{colors.accent-tint}`, 1px `{colors.hairline}`, `{rounded.xl}`, padding 40px. Date in `{typography.title-sm}`, body in `{typography.body-md}` `{colors.ink-soft}`, max-width ~640px.

**`plan-card`** — White, 1px `{colors.hairline-alpha}`, `{rounded.xl}`, padding `{spacing.xl}`. Plan name in `{typography.title-lg}` colored with a tint ink (e.g. `{colors.tint-blue-ink}`), price, `{component.button-primary}` full-width, then feature list in `{typography.body-sm}` (Inter) with green check icons.

**`logo-wall`** — "Trusted by next-gen B2B SaaS" in `{typography.display-sm}` + a row of grayscale customer logos.

**`faq-item`** — Row with question in `{typography.title-sm}` `{colors.ink}`, answer in `{typography.body-sm}` `{colors.body}`; rows separated by `{colors.separator}` hairlines.

### Chips, Badges & Tabs

**`tint-chip`** — Pastel background + same-hue ink (see Pastel Tint Pairs), `{typography.label}`, padding 4px × 8px, `{rounded.xs}`.

**`badge-pill`** — `{colors.orange}` or `{colors.accent}` background with white text, `{typography.caption}`, `{rounded.pill}`. For "New" and announcement labels.

**`segmented-tab`** + **`segmented-tab-active`** — Container `{colors.surface-muted}` `{rounded.sm}`; active segment white with `{shadows.key}` and `{colors.ink}` label; inactive `{colors.muted}`.

### Inputs & Forms

**`text-input`** — White, 1px `{colors.hairline}`, `{rounded.sm}`, height 36–40px, padding 8px × 12px, `{typography.body-md}`, placeholder `{colors.muted-soft}`.

**`text-input-focused`** — Border `{colors.accent}` + 3px `{colors.accent-tint}` ring.

### Data Display (product UI)

**`report-card`** — White card, `{rounded.lg}`, hairline, title row with tint chip + metric name, large number in `{typography.display-sm}` (Plain Black 32px / 500), chart below.

**`chart-palette`** — Series order: `{colors.series-1}` (accent) → `{colors.series-2}` (strong orange, darker) → `{colors.series-3}` (blue ink) → `{colors.series-4}` (green, darker) → `{colors.series-5}` (pink ink). Use the darker series colours for lines and for text on white (see [Chart series colours and contrast](#chart-series-colours-and-contrast)). Gridlines `{colors.separator}`, axis labels `{typography.caption}` `{colors.muted}`.

### CTA / Footer

**`cta-band-dark`** — `{colors.surface-dark}` background, `{rounded.xxl}`, padding 64px. h2 in `{typography.display-md}` white, sub-line in `{typography.lead}` at 80% white, `{component.button-on-dark}`.

**`footer`** — `{colors.sand}` with a `{colors.sand-line}` top line; 4–5 link columns in 14px `{colors.muted}`, column heads `{typography.title-sm}` `{colors.ink}`.

## Jinder Components

These components are not part of June. They are specific to Jinder.

### Icons
- Use SVG line icons only (Lucide style): 24px grid, stroke 2, round caps and joins, `stroke: currentColor`, no fill.
- Default size: 20px. In buttons: 16px. In icon tiles: 22px.
- Keep all icons as `<symbol>` items in `app/icons.svg`. Show an icon with `<svg class="icon"><use href="icons.svg#id"/></svg>`.
- Add `aria-hidden="true"` to decorative icons.
- Do not use emoji as icons.

**`icon-tile`** — 44px square, `{rounded.lg}`, tint background with the same-hue ink icon (pink, yellow, blue, green). An `accent` variant uses `{colors.accent-tint}` with an `{colors.accent}` icon.

### Tint meaning in Jinder
Use the tint pairs with these meanings:

| Tint | Meaning |
|---|---|
| Pink | Translation, talent, cross-border experience |
| Yellow | Skill gaps, items to improve |
| Blue | Employers, companies, roles |
| Green | Matches, success, completed items |
| Rose | Errors, risk |
| Gold (orange family) | Premium: the crown, the gold ring, the "Premium" chip, the lock badge. Also the "Below" state (a skill below the asked level) in skill tables |

### Shared components of version 2 (lists, Premium, compare)
These components are used by many screens. The talent screens, the employer screens and the Compare page all call the same code (`js/components/`).

**`pager`** (`components/pagination.js`) — Under every list of jobs or talent. A row that wraps: at the left the **"Rows per page"** select (10, 20 or 50; the first is the default), then "Showing 11–20 of 134" (`aria-live="polite"`, tabular figures), then the page buttons.
- The buttons are in a `nav` (`aria-label="Pagination"`). **Previous** and **Next** are step buttons. A page is a button with its number; the current page has the `is-current` class (navy background, white text) and `aria-current="page"`. Gaps show as "…". The row has at most 7 items.
- Each button is 36px tall, `{rounded.sm}`, hairline border. A disabled step button has 50% opacity.
- The pager is **hidden** when there are no items, when the list has one page and 10 items or fewer, and for a Basic employer (the list is cut to 5, no pager). A list with one page and more than 10 items still shows the size select.
- The page size is **remembered** in the browser for each list and each user (key `jinder.pagesize.<list>.<userId>`).
- On screens of 768px or less, the buttons and the select are 44px tall and the "Showing" text moves to the top.
- After a page change, the focus goes to the heading of the list and a live message says "Page 2 of 7". After a size change, the focus stays on the size select.

**`sort-select`** (`components/sort-select.js`) — A visible label "Sort by" (13px / 500 `{colors.ink}`) and a native `select` (36px tall; 44px on touch screens). The first option is the default. Job lists: "Best match" and "Newest posted". Bookmarks also have "Recently saved" (the default). Applications: "Recently updated", "Best skill match", "Newest application". Employer talent list: "Best fit for this job" and "Recently updated". The lists of employer jobs and of applicants have one sort only, so they show the text "Newest first." and no select.
- A change of the sort, or of the page size, goes back to page 1. A live message says "Sorted by Newest posted. Page 1 of 7".
- **`list-toolbar`** — The row above a list that holds the sort select (and, for the talent list, the tabs and the job select).

**`jd-view`** (`components/jd-view.js`) — The job description in a box. It is a `section` with `role="region"`, an `aria-label` ("Job description"), `tabindex="0"`, a maximum height of 32rem and `overflow-y: auto`, so that a long text scrolls inside the box and the box does not push the page.
- The text uses a small markup: a line `## Heading` is a heading (`h3`, 15px / 600 `{colors.ink}`), a line `- text` is a bullet, a blank line ends a paragraph. All text is escaped. A text with no heading shows as paragraphs. No text shows "There is no description for this job."
- The box has a hairline border, `{rounded.lg}`, padding 16px × 24px, 15px text with a line height of 1.65.
- **Scroll shadow:** a soft shadow at the top and the bottom edge tells that there is more text. It is made with CSS background layers only (`background-attachment: local`). This is the one place where a gradient is allowed, because it is a scroll cue and not a decoration.
- **Keyboard:** the box takes the focus (Tab). The arrow keys scroll it. A 2px `{colors.accent}` focus ring shows.
- The JD editor in the employer job form uses the same look for its preview.

**`crown`, `premium-chip`, `locked-badge`** (`components/premium.js`) — The Premium markers.
- **`crown`** — A 16px crown icon (`i-crown`), filled with `{colors.gold}`, outlined with `{colors.gold-ink}`. It has `role="img"` and the label "Premium", or it is `aria-hidden` when the text next to it says Premium.
- **`chip-gold` / `premium-chip`** — A chip with `{colors.gold-tint}` background, `{colors.gold-ink}` text, a 1px inset ring of `{colors.gold}` and weight 600.
- **`locked-badge`** — A gold chip with a lock icon (`i-lock`) and the text "Premium". It is a button by default (`data-premium-lock="<feature>"`): a click opens the "Premium feature" dialog ("{feature} is part of Premium. In this demo you can switch your plan in Settings." and a "Go to Settings" button). Inside another button or link, use the static variant (a plain `span`). Screen readers hear "Premium feature: {feature}".
- Rule: a **Basic** user sees the lock badge on a Premium feature. A **Premium** user sees the feature as normal. The crown is for the account area only (the user block and Settings).

**`compare-tray`** (`components/compare-tray.js`, `core/compare-store.js`) — The basket bar for Compare. It is fixed at the bottom of the main area, with a white background, a hairline top border and `{shadows.popover}`. Its left edge follows the menu (248px, 72px when the menu is hidden, 0 on small screens). The page gets bottom padding of the bar height, so the bar covers no content.
- The bar shows only when the basket has 1 or more items. It has the title **"Compare (n/5)"**, a `compare-chip` for each item (the title and a remove button, `aria-label="Remove {title} from compare"`), a primary **"Open compare"** link (when there are 2 or more items; with 1 item, a disabled button and the text "Add 1 more job to compare." or "Add 1 more talent to compare.") and **"Clear"**.
- The basket holds at most 5 items. It is stored in the browser (`jinder.compare.<userId>.<kind>`; kind is `job` for a talent and `talent` for an employer) and it stays while the user browses. The 6th item is refused with the text "You can compare up to 5 jobs." (or "profiles").
- The app shell shows the bar on every signed-in page, except the Compare page. A list page must not add a second bar.
- **`compare-pick`** — The small "Compare" check box on a job card or talent card, and the "Compare" toggle button on a detail page (`aria-pressed`, a check mark when the item is in the basket).

**`plan-card` (Settings)** — The card in "Your plan" that lists the benefits of the plan. White, 1px hairline, `{rounded.xl}`, padding 24px. A **Premium** user has a 2px `{colors.gold}` border.
- Head: a 44px `icon-tile` (gold with the crown for Premium; accent with a lock for Basic), the title "Your current plan: Premium" (or "Basic") and a muted line.
- **`benefit-list`:** one row for each benefit (a 24px icon, the label in 14px / 600, a 13px description and the status at the right). Basic: a lock icon and a gold "Premium" chip. Premium: a green check and a green chip **"Used"** with "N times", or a neutral chip **"Not used yet"**. A benefit that a Basic user already has shows a check and a neutral "Included". On small screens the status moves under the text.
- A Basic plan has the primary button "Try Premium (demo)". Under the card, the demo switch (two radio cards) stays, with the text "Demo only: switch the plan to try the Premium features. There is no payment."

### Landing page
**`eyebrow`** — Section label above a heading. `{typography.caption-uppercase}` in `{colors.accent}`.

**`hero-eyebrow`** — The hero label "Skills-based hiring for **Australia**" is a white pill (1px `{colors.hairline}`, `{rounded.pill}`, `{shadows.xs}`, padding 4px 4px 4px 14px). The word "Australia" is highlighted in an **`au-chip`**: a pill with `{colors.orange-tint}` background, a 14px map-pin icon in `{colors.orange}`, and `{colors.ink}` text at weight 700. Use the orange highlight only for the Australian market, so it keeps its meaning.

**`screenshot-frame` (product preview)** — Browser-style frame. It has a top bar on `{colors.surface-subtle}` with three gray dots and a URL. The body shows two panels:
- **Translation table:** rows of "source experience → Australian skill". Source text is `{colors.muted}`. Target text is `{colors.ink}` at weight 500. Rows have `{colors.separator}` lines between them.
- **Match card:** role title, tint chip, score in `{typography.display-md}`, an 8px `{colors.accent}` meter, then reasons. A reason with a check icon is green. A gap with an alert icon is `{colors.tint-yellow-ink}`.

The frame is decorative. Give it `role="img"` and an `aria-label` that tells what it shows.

**`market-block`** (Australian job market) — Centred, with a bottom hairline. An `eyebrow` with a map-pin icon ("The Australian job market"), a 32px display heading ("Skilled talent is here. Employers can't find it."), then **two highlight cards** side by side (max 420px each; one column on small screens). Each card: a tint background (pink for talent, blue for employers), `{rounded.xl}`, padding `{spacing.lg}`, a white `icon-tile` at the left (graduation / briefcase), the number in 48px display, the label in 15px / 500 ink, and the source in 12px. Show only the two Australian market numbers. Always show the source of a statistic. Do not add a "black-box" or a made-up statistic.

**`feature-card` (step)** — A `feature-card` with an `icon-tile`, a step number ("01", "02", "03") at top right in `{typography.caption-uppercase}` `{colors.muted}`, and a 20px / 600 Inter title.

**`audience-card`** — One card for each user group, two in a row. White, hairline, `{rounded.xl}`, 40px padding. It has an `icon-tile`, a `{typography.display-sm}` title, a `check-list`, and a button at the bottom.

**`check-list`** — List with a green 18px check icon before each item. On dark surfaces, the icon is `{colors.orange}`.

### System screens
**`placeholder`** — For a section that a later phase builds. Inside the app shell: the section title in `{typography.display-md}`, a sub-line, and a `panel` with an empty state (clock `icon-tile`, "This section is coming soon.", a secondary "Back to Home" button).

**`no-access`** — Inside the app shell. Title "You don't have access to this page", sub-line "This page is for a different account type.", a shield `icon-tile` and a primary "Go to Home" button.

**`not-found`** — `top-nav` with the logo, then the `legal-page` column: eyebrow "Error 404", title "We can't find this page", text "The link may be old, or the page may have moved." and a primary button to Home.

**`empty-state`** (in any panel) — Centred column: an `icon-tile`, one line of `{colors.muted}` text that tells what to do, and one button. Always tell the user the next action. Never show an empty panel.

**Loading and error states** — While data loads, show "Loading …" text with `role="status"` in the place of the content. If the API returns an error, show a short message with `role="alert"` in the same place. Do not show a blank area.

### Authentication pages
**`auth-split`** — Full-height page with two columns (5 : 7):
- **Left, `auth-aside`:** `{colors.surface-dark}`, logo (dark version), a `{typography.display-md}` white headline, a `check-list`, and a short quote above a thin white line.
- **Right, `auth-main`:** white. A top row with a "Sign in" or "Create account" link button. The form sits in the center, max-width 400px. A legal line is at the bottom.
- Below 1024px, the left column is hidden and the logo moves to the top row.

**`role-picker`** — Two selectable cards in a `radiogroup`: "I'm looking for work" (globe icon) and "I'm hiring" (briefcase icon). Each card has a title and a one-line description. The selected card (`aria-checked="true"`) has an `{colors.accent}` border, a 3px `{colors.accent-tint}` ring and an accent icon. When "I'm hiring" is selected, show the Company field.

**`password-field`** — `text-input` with an icon button inside at the right. The button shows or hides the password. Change its `aria-label` between "Show password" and "Hide password".

**`field-hint`** — 12px `{colors.muted}` text below an input. Connect it to the input with `aria-describedby`.

**`field-error`** — 12px `{colors.error}` text directly below the input. When there is an error:
1. Add a `{colors.error}` border to the input.
2. Set `aria-invalid="true"` on the input.
3. Connect the message with `aria-describedby`.
4. Move focus to the first field that has an error.

**`form-alert`** — Message above the form for errors that are not about one field, and for success messages. Error: rose tint. Success: green tint. Use `role="alert"`.

### App structure
The app is one page (`index.html`). Each screen is a view. The address bar shows the screen after `#`, for example `#/home`.

| Screen group | Layout |
|---|---|
| Landing, Terms, Privacy, Page not found | `top-nav` + content + footer, on `{colors.canvas}` |
| Sign in, Create account | `auth-split` |
| All signed-in screens | `app-shell` with the screen in the main area, on `{colors.sand}` (the left pane and the cards stay white) |

**`skip-link`** — The first item on the page: "Skip to content". It is above the page and not visible until it gets keyboard focus. Then it shows at the top left as a navy pill with white 14px / 600 text.

**Focus after a screen change** — The page heading (`h1`) gets focus, so that screen readers read the new screen. This focus has no visible ring. Keyboard focus on other items keeps the normal ring.

### App shell (signed-in screens)
**`app-shell`** — Two columns: a left navigation pane and the main area. The main area has the screen content, max width 1200px, centred.

**`sidebar`** (left navigation pane) — White, 1px `{colors.hairline}` right border. It stays fixed when the page scrolls. Width 248px.
- **Top:** the logo (link to Home) and a "hide navigation" icon button (panel icon) at the right.
- **Navigation:** a list of `nav-item` links for the role of the user.
  - Talent: Home, Jobs, Bookmarks, Applications, **Compare**, Notifications.
  - Employer: Home, Talent, My jobs, **Compare**, Notifications. A Basic employer sees a small gold lock chip ("Premium") at the right of Compare. The item still opens the Compare page, which explains the feature. When the menu is hidden, the chip is a small lock at the top right of the icon.
  - There is **no "Settings" item**. The user block at the bottom opens Settings (see below). The Compare item (`columns` icon) is the current item on `#/compare`.
  - **`nav-badge`** — The Notifications item shows the number of unread notifications at its right: `{colors.error}` pill, white 11px / 700 text, minimum 20px. When the pane is collapsed, a 16px badge sits at the top right of the icon. The link label says the count ("Notifications, 3 unread"). No badge when the count is 0.
- **Bottom** (1px hairline line above): the **user block** and a "Sign out" `nav-item`.
  - **`sidebar-user-link`** — The user block is **one link** to `#/settings`. It has the initials `avatar`, the name, the role chip and, for talent, the `sidebar-alias` line. The link name for screen readers is "Account settings, {name}". It has a hover background `{colors.surface-muted}`. On the Settings page it is the current page (`aria-current="page"`, `{colors.accent-tint}` background). It is one stop for the keyboard.
  - **Premium user:** the link has the class `is-premium`. A `crown` sits at the top right of the avatar (18px, `{colors.gold}` with `{colors.gold-ink}` outline), the avatar has a **gold ring** (a 2px gap and a 2px `{colors.gold}` ring) and a small gold chip "Premium" shows after the role chip. A hidden text "Premium plan" describes the link. The crown also shows when the menu is hidden. The crown and the lock update at once when the plan changes (event `jinder:plan-change`).
  - On small screens the same block is in the opened menu.

**`nav-item`** — Icon 20px + label, 14px / 500 `{colors.body}`, padding 10px × 12px, `{rounded.md}`. The icon is `{colors.muted}`.
- Hover: `{colors.surface-muted}` background.
- Current screen (`aria-current="page"`): `{colors.accent-tint}` background, `{colors.ink}` text at weight 600, `{colors.accent}` icon.

**`sidebar-collapsed`** — When the user hides the navigation, the pane becomes 72px wide. It shows icons only. The labels and the wordmark are hidden. Each item has a tooltip (`title`) with its label. The app remembers this choice on the device.

**`sidebar` on small screens (768px or less)** — The pane is hidden at the left. A white top bar (56px, hairline bottom) shows a menu button, the logo and, at the right, a bell icon link to Notifications with a small `nav-badge`. The menu button opens the pane over the content with a dark scrim (`rgba(13, 19, 27, 0.45)`). Click the scrim, choose an item or press Esc to close it.

**`avatar`** — 32px circle, `{colors.accent-tint}` background, initials in `{colors.accent}` 13px / 600.

### Home (signed-in)
All signed-in screens use `{colors.sand}` as the background, so white cards stand out.

**`dash-head`** — Greeting in `{typography.display-md}`, a sub-line in `{colors.muted}`, and the primary action button at right.

**`report-card` (stat)** — Label at top left, a 18px `{colors.muted-soft}` icon at top right, a number in `{typography.display-sm}`, and a 13px meta line. When there is no data, the meta line tells the user what to do next.

**`panel`** — White, hairline, `{rounded.xl}`, padding `{spacing.xl}`. Title in Inter 18px / 600.

**`steps`** — Ordered setup checklist. Each row has a 28px numbered circle, a title, a description, and a "Start" button. A completed row has a green circle with a white check and no button. On the Talent Home, hide the checklist when all steps are done.

**Talent Home layout** — No KPI or stat cards. From top to bottom: `dash-head` → **"Your activity"** panel → `search-bar` → "Recommended for you" → "Skill insights" (Premium charts or the `upgrade` box) → "Get set up" (only while a step is open).

**`activity-grid`** ("Your activity") — Two bordered boxes (hairline, `{rounded.lg}`, padding `{spacing.lg}`), side by side; they stack at 1024px or less. Each box has a 14px / 600 title with an accent icon.
- **Active applications:** the number in display 32px + a yellow chip "{n} needs your action", a `bar-chart` by status (active applications only), and a "See all applications" `text-link`.
- **What employers see:** the `alias-badge`, the roles with ANZSCO codes, a line "Level: Senior · 7.5 years", up to 8 green skill chips with the level as text ("Python · Advanced") + "+N more", a line for the certifications and a line for the awards (the first 3 names and "+N more"; names and years only), a hint about what is never shown, and a small secondary "Edit profile" button. It replaces the empty "anonymous profile" chart.
- The active applications count reads **all** the applications (not one page), so the count is right.

**"Recommended for you" (talent Home)** — The best 5 jobs as `job-card`s, **no pager**, with the line "Showing the 5 best of {N} recommended jobs. See all jobs" (a `text-link` to the Jobs screen) when there are more. Each card has the "Compare" check box.

**Employer Home** keeps its three `report-card`s (Open jobs, Jobs at target, Waiting for you). The job titles in "My jobs" open the **job overview** page. The chart "Applicants per job" shows the newest 10 jobs and says "Shows the newest 10 of {N} jobs." when there are more. The talent list on Home shows the top 3.

### Onboarding (talent accounts)
The onboarding dialog collects data to recommend jobs. It opens automatically on the first visit of a talent account.

**`modal`** — Native `<dialog>`, opened with `showModal()`. Width `min(600px, 100% - 32px)`, `{rounded.xl}`, `{shadows.popover}`, backdrop `rgba(13, 19, 27, 0.45)`. It has three parts:
- **Head:** "Step X of N" in `{typography.caption-uppercase}` `{colors.muted}`, a 4px `{colors.accent}` progress meter, and a close button (X icon).
- **Body:** scrolls if necessary. Step title in `{typography.display-sm}`, sub-line in `{colors.muted}`.
- **Foot:** `{colors.surface-subtle}` with a top hairline. "Back" (ghost) at left. Actions at right.

**`dropzone`** — CV upload area. A `<label>` for a hidden file input. 1.5px dashed `{colors.disabled}` border, `{rounded.lg}`, `{colors.surface-subtle}` background. When a file is dragged over it, the border becomes `{colors.accent}` and the background `{colors.accent-tint}`. Accepted files: PDF and DOCX, 10 MB or less. Inside the zone, put the icon tile, the main line and the size hint on separate lines, centred.

> **Caution:** The drop zone is a `<label>` inside `.field`. The rule `.field label` (display block) is stronger than `.dropzone`. Use the selector `.field .dropzone`, or the icon and the text run together on one line.

**`file-chip`** — Selected file: file icon, name (ellipsis if long), size, and a remove button. Hairline border, `{rounded.lg}`.

**`privacy-note`** — Short notice on `{colors.accent-tint}` with a shield icon, 13px `{colors.ink-soft}`. Tell the user what employers can and cannot see. Text on the CV step: "Employers never see your CV or your personal details. They see only your translated skills and experience, under an alias — not your name, contact details, photo or nationality." Do not use the word "Prototype" in the UI.

**`combobox` (searchable dropdown)** — Use it for answers that have a list of common values: qualification, field of study, country, job title, domain, years of experience, skills, target role, certification name (a free name is allowed).
- The user types to filter the list. The matched text is bold.
- The user can type a value that is not in the list. The last row shows `+ Use "{text}"` in `{colors.accent}`. Allow this for all fields except fixed ranges (years of experience).
- Keyboard: ArrowDown and ArrowUp move. Enter selects. Esc closes the list only, not the dialog.
- Style: `text-input` with a chevron button at right. The list is white, 1px `{colors.hairline}`, `{rounded.sm}`, `{shadows.popover}`, max height 240px. An option is 14px with `{rounded.xs}`. The active option has a `{colors.accent-tint}` background.
- Accessibility: follow the WAI-ARIA 1.2 combobox pattern. Announce the number of results in a `role="status"` region.

**`list-field` (multi-value field)** — Use it when a person can have more than one answer: qualifications, fields of study, countries, roles, industries, skills, target roles.
- It has a `combobox`, an "Add" button and a list of `skill-chip` values.
- A counter "N of MAX" is at the right of the label.
- The user can pick options from the list and add their own values.
- Duplicates are not added. A typed value that matches an option uses the spelling of the option.
- When the list is full, the input and the "Add" button are disabled.
- If the user types a value and does not press Enter, the value is added when they continue.
- Use a single `combobox` (not a list) only for fixed ranges, for example years of experience.

**`choice`** — Toggle chip for multi-select answers (locations, work types, industries). A `<button aria-pressed>`, `{rounded.pill}`, hairline border, 13px / 500. Pressed: `{colors.accent-tint}` background and `{colors.accent}` border. Put the chips in a `role="group"` with a label.

**`skill-chip`** — Removable skill: pink tint pair, `{rounded.xs}`, with an X button. The button has `aria-label="Remove {skill}"`.

**`review-list`** — Summary before save, and "Your profile" in edit mode. Bordered list with rows: label (`{colors.muted}`) with a marker under it ("From your CV" AI chip, or a yellow "Missing" chip when a required answer is empty — then the value is yellow ink), value (`{colors.ink}`) and an "Edit" `legal-link` button ("Change" for the CV). The save stops with an alert while a required answer is missing.

### Skill translation (talent)
This is the core of Jinder (Feature 2). The talent sees how their experience is translated, and decides what employers see.

**Onboarding flow** — With a CV: Add your CV → Reading your CV → Education → Experience → Skills → **Certifications and awards** → Your translated profile → Goals → Check your answers (9 steps). Without a CV, the Reading step is not there (8 steps).
The word for a field of work is **"Domain"** on every step ("Domains", "Target domains"). The list has the 3 domains only, with no custom value ("Choose a domain from the list.").

**Edit mode (a done profile)** — Do not send the person through the whole flow again. Every edit starts and ends on **"Your profile"** (the `review-list` with "Edit" on each row). The head says "Edit profile" or "Edit profile · Step X of N".
- "Edit answers" / "Edit profile" → "Your profile". "Edit" on a row opens only that step (education, experience or skills also show the translation again, so the shared skills stay correct), then returns.
- "Edit" on the Certifications or Awards row → Certifications and awards → Your profile.
- "Update CV" → Update your CV → Reading → Your translated profile → Your profile (4 steps, no "Skip for now"). A field that the new CV does not show keeps the old answer.
- "Review translated skills" → Your translated profile → Your profile.
- The first step of an edit has "Back to profile". The save button is "Save changes".

**`progress-indeterminate`** — 240 × 6px track (`{colors.surface-strong}`, pill) with an accent segment that moves from left to right. Use it while the API reads a CV or translates. With reduced motion, the segment does not move. Put a status line under it ("Reading your CV…").

**`field-marker`** — Small chip at the right of a field label:
- **"AI-detected":** `{colors.accent-tint}` background, `{colors.ink-soft}` text, a small accent check. The value came from the CV. It goes away when the talent changes the field.
- **"Missing":** yellow tint pair. The CV did not show this field and the field is empty.

**`cv-found`** ("What we found in your CV") — A summary at the top of the Education step, only after a CV scan with the real backend. `{colors.surface-subtle}` background, hairline border, `{rounded.lg}`, padding 16px. A 14px / 600 title and a list of 6 rows: Current role, Desired role, Level, Years of experience, Certifications, Awards.
- A found field has a green check icon and its value in bold. A field that is not found has a yellow alert icon and the text "Not found. You can add it in the next steps." The meaning is an icon and a word, not only colour.

**`cv-hint`** — A 12px `{colors.body}` line under a field that the CV filled: "From your CV. Check it. Change it if it is wrong." (with a small accent check). When the CV did not show the field and it is empty, the line says what is missing, for example "We could not find your desired role in your CV. You can add it." The line goes away when the talent adds a value. The new fields (current role, desired role, level, exact years, certifications, awards) also get the "AI-detected" `field-marker`.

**`level-field`** — On the Experience step: **"Your level"** is a `select` ("Not sure" and the 6 levels, the first option is the default). **"Exact years of experience"** is an optional number field (0 to 40, step 0.5). A valid number sets the band of "Total years of work experience" (same rule as the server) and locks the band select. A number outside the range shows "Enter a number from 0 to 40."

**`cred-editor`** (Certifications and awards step) — Two lists, each a `fieldset` with a `legend` and a hint. Under each list the text: "Employers see these names. Do not write your own name, your employer's name or contact details here."
- A row (`cred-row`: hairline, `{rounded.lg}`, padding 12px 16px; a grid of the main fields and an 8rem year field; one column on 768px or less) with a "Remove" button. At most 20 rows in each list ("Maximum 20 reached"). An "Add a certification" or "Add an award" secondary button. An empty list shows "No certifications added." or "No awards added."
- **Certification row:** Name (a `combobox` with the 38 known certifications, free text allowed), Year (optional) and Issuer (optional). A known name fills the issuer and locks it ("From the list of known certifications.").
- **Award row:** Name, Kind (a `select` of the 12 kinds; required: "Choose a kind.") and Year (optional).
- A year must be from 1990 to next year. A row with nothing in it is dropped. An error is under its field (`aria-invalid`, `aria-describedby`) and the first error takes the focus. Removing a row announces it and moves the focus to the next row or the Add button.

**`skill-level-select`** (`tr-level`) — On a translation card of a skill (not on a role or a qualification card): a `select` with the label "Level". The first option says "From the evidence (Advanced)" (the server uses the evidence level) and the others are "1 · Beginner" to "5 · Expert". A level that came from the CV starts selected, with the tag "From your CV" until the talent changes it. The select is 36px tall (44px on touch screens).

**`demo-banner`** — Yellow tint pair, radius 8, alert icon, 13px. Only in mock mode: "Demo mode: the mock API filled these fields from a sample CV (…), not from your file." Never show it with a real backend.

**`translation-card`** — One translated skill. White, hairline, `{rounded.lg}`, padding `{spacing.md}`.
- Tags row: kind chip (pink "Cross-border", blue "Cross-industry", neutral "Direct"), evidence chip ("Evidence: Strong" green, "Moderate" yellow, "Limited" neutral), and "Edited by you" when the talent changed the name.
- Map row: the original words in `{colors.muted}` → arrow → the Australian skill in `{colors.ink}` 600, and a blue ANZSCO chip when there is a code.
- The reason in 13px. If the CV shows the skill: a quote box on `{colors.surface-subtle}`: "From your CV: “…”".
- Actions: small "Accept" (pressed = green tint "Accepted"), "Edit" (opens an inline field with a searchable dropdown, "Save" and "Cancel"), "Remove".
- **Accepted:** green border and a 3px green bar at the left.
- Removed skills go to a "Removed (not shared)" row of chips. A chip puts the skill back.

**`gap-box`** — "Things Australian employers may ask about": `{colors.surface-subtle}`, `{rounded.lg}`, a list with yellow alert icons (for example, "Infrastructure as code (for example Terraform)"). It helps the talent prepare. It is not a score.

**`shared-preview`** — "What employers see": 1px dashed `{colors.accent}` border, `{colors.accent-tint}` background, `{rounded.lg}`. It shows the `alias-badge`, the roles with ANZSCO codes, the level, the exact years, the accepted skills as green chips with their level as text ("Python · Advanced"), the certifications and awards (names and years only) and the AQF levels. A hint says what is never shown: name, contact details, photo, nationality, employer names and the CV. The same box is in Settings, with the data from the API (it shows the same facts as the Home panel and this preview).

> **Caution:** Do not show a score for the person. The evidence level is about one skill, not about the talent. Do not use nationality, ethnicity, gender, age or visa status in a translation.

### Jobs (talent)
All job data is internal Jinder data. Every job link opens a Jinder screen. Do not link to other job sites. Do not show the name of a data provider.

**`search-bar`** — White card, 1px `{colors.hairline}`, `{rounded.xl}`, padding `{spacing.md}`. Three parts in a row:
- A 44px search input with a search icon inside at the left. Placeholder: "Search jobs by title, skill or company".
- A 44px location select: "All locations" and the cities.
- A large primary "Search" button.

It shows on the talent Home (under the greeting) and at the top of the Jobs screen. On small screens, the three parts stack.

**`job-card`** — One job. Hairline, `{rounded.lg}`, padding `{spacing.lg}`, two columns (content : 140px):
- **Content:**
  - Title in Inter 17px / 600. The title is a link to the job detail screen (no underline, `{colors.accent}` on hover).
  - Meta line in 13px `{colors.muted}`: company · map-pin area · work type · salary.
  - **Summary:** about 200 characters of the job description, 14px `{colors.body}`.
  - **`job-facts`** (under the meta line): chips for the **Level** (pink, for example "Senior"), the **Experience** (neutral: "5–9 years", "5+ years", "Up to 6 years" or "2 years") and the **Work mode** (blue: Onsite, Hybrid or Remote). A fact that the job does not have has no chip. Each chip has a hidden word for screen readers ("Level: Senior") and a `title`. A long chip wraps, so the card never runs out of the page at 390px.
  - Tags row: a green chip link "Applied · Track" when the talent applied, a blue `tint-chip` "ANZSCO {code} · {occupation}", "Posted {date}" and "Closes {date}". A closed job shows a rose "Closed" chip.
  - **Skill gaps row:** the label "SKILL GAPS" in `{typography.caption-uppercase}` `{colors.muted}`, then up to 4 yellow chips (12px) and "+N more". If there is no gap, show a green chip "No skill gaps found". A related skill is not a gap.
  - Reasons with green check icons. Notes in `{colors.muted}` with a gray alert icon, for a work type or a location that the talent did not choose.
  - **`card-actions`:** small ghost buttons in `{colors.muted}`: "Not for me" (eye-off icon) and "Report" (flag icon). Next to them, the `compare-pick` check box "Compare" (the screen reader name is "Compare {job title}"). It is on every card, also on the compact cards, with the real backend only.
- **Coverage column (right aligned):** the `bookmark-button` at the top, the coverage "{c}%" in `{typography.display-sm}`, "skills covered", an accent meter and the line "{m} of {n} skills + {p} related". Coverage is about the skills of this job. It is not a score on the person.
- **`card-foot`** (across both columns, hairline top): the `card-actions` at the left and a small secondary **"Job detail →"** button at the **bottom right** (also on compact cards).

**`job-card-hidden`** — After "Not for me": a dashed hairline row with "{title} is hidden. We show fewer jobs like this." and an "Undo" `text-link` button.

**`job-card` (compact)** — For "Similar jobs". No summary and no reasons. Padding `{spacing.md}` × `{spacing.lg}`.

**`bookmark-button`** — Saves a job to Bookmarks.
- On a card: a ghost icon button with the bookmark icon.
- On the job detail screen: a secondary button with the icon and the text "Save" or "Saved".
- Saved: `{colors.accent}` color, and the icon is filled with `{colors.accent}`.
- Use `aria-pressed`. The label tells the action: "Save {title} to bookmarks" or "Remove {title} from bookmarks".
- After a change, a polite live region says "{title} saved to bookmarks." or "{title} removed from bookmarks."

**`source-chip`** — Neutral chip in the panel head: "{N} open jobs · updated {date}". While the data loads: "Loading jobs…". If the data is not available: "Jobs unavailable".

**`back-link`** — A text button (or link) with a chevron-left icon, `{colors.accent}` 14px / 600, no underline. "Back" goes to the previous screen. On screens with a fixed parent, the text is the parent name ("Applications", "My jobs", the job title, "Talent").

**Jobs screen** — Title "Jobs", the `search-bar`, and a `panel` "Results" with a count line ("{N} open jobs for “{word}” in {city}. Best fit first." or "Newest first."), a `list-toolbar` with the `sort-select` ("Best match", "Newest posted"), the `job-card` list and the `pager` under it. The page, the page size and the sort are in the address (`?page=2&pageSize=20&sort=newest`), so the Back button and a shared link work.

**Job detail screen**
- `back-link`, then the head: category chip (with the specialisation: "Data · Data analytics") and ANZSCO chip, the job title in `{typography.display-md}`, the meta line and the dates.
- **Actions row, at the left under the dates:** a large primary "Apply" (send icon) that opens the apply screen; after applying, "Applied · Track status"; for a closed job, a disabled "Apply" with the hint "This job is closed. You can't apply now.". Then the `bookmark-button` (with text), a secondary **"Compare"** toggle (`compare-pick`, with `aria-pressed`; real backend only), a ghost "Not for me" and a ghost "Report".
- Two columns (2 : 1; one column on screens of 1024px or less):
  - Left, two `panel`s one above the other:
    - **"Job facts"**: a `fact-grid` (a `dl` of label and value pairs): Level, Experience, Work mode, Place, Type, Salary, Education. A fact that the job does not have is left out. Under it, for a job that has version 2 data: an h3 **"Certifications"** with the groups "Required" and "Preferred" (neutral chips, each group has a 13px / 600 label) and an h3 **"Awards"** with the group "Preferred" (the label of the award kind, for example "Hackathon"). An empty list says "This job does not ask for a certification." or "This job does not ask for an award."
    - **"About the role"**: the full job description in the `jd-view` box. The text is **never cut**. It has the headings of the job description and scrolls inside the box (maximum height `min(32rem, 70vh)`).
  - `panel` "Your skills for this job": the coverage in 40px, the meter, the coverage line, the `fit-score`, "Skill by skill" (`skill-match` list) and "Why it fits". If the talent has no profile, show an `empty-state` that asks them to complete it.
- Then the `fit-panel` and the `path-panel` (see below).
- `panel` "Similar jobs": up to 3 compact job cards. The head has a small secondary button **"Compare with these jobs"** (columns icon, real backend only): it puts this job and the similar jobs into the basket (at most 5) and opens the Compare page.

**`radar-chart`** — A spider chart in SVG (viewBox 560 × 470, plot radius 140) for **1 to 5 series** on 3 to 10 axes, each 0 to 100. Four hairline rings (25, 50, 75, 100) with 10px muted numbers on the top axis, hairline spokes, and axis labels in 12px / 600 `{colors.body}` outside the outer ring. A long axis label wraps to at most 3 lines of 14 characters and the full text is in a `title`.
Each series is a polygon with a 2.5px line and a fill of 12% opacity (6% when there are more than 3 series), and a marker on each value. **Colour is not the only signal.** Each series has its own colour (see `chart-palette`), line style and marker:

| Series | Colour | Line | Marker |
|---|---|---|---|
| 1 | `{colors.series-1}` | solid | circle |
| 2 | `{colors.series-2}` | dashed | square |
| 3 | `{colors.series-3}` | dotted | diamond |
| 4 | `{colors.series-4}` | dash-dot | triangle |
| 5 | `{colors.series-5}` | long dash | cross |

A legend lists the series with a small swatch that has the same colour, line and fill. The SVG has `role="img"` and an `aria-label` with all the values. A `data-table` with the same numbers (one decimal, tabular figures; "—" for no value) is always next to it. A radar never shows a total.
- **Two-layer mode** (`radar-layers`, used by "Your path to this job"): series 1 "You have" is a **filled** shape (28% opacity) and series 2 "Job requires" is an **outline** only with a thicker line (3.5px). Where the filled shape is smaller than the outline, the talent sees the gap.

**`path-panel` ("Your path to this job")** — A `panel` under the `fit-panel`, only for a talent with a profile. Head: h2 and a muted line ("What you already have for this job, and what is still missing. This is a guide for you. Employers never see it."). It replaces the version 1 panel with the 12-month line chart.
- **Summary chips** (`path-summary`): a green chip "7 fit" (check icon), a yellow chip "3 gaps" (alert icon; "1 gap"), a neutral chip "about 5.5 months to close the gaps" (only when there is a gap) and a blue chip with the readiness tier (a hidden word "Readiness:" before it).
- **Two columns** (`path-grid`; one column on 1024px or less):
  - **Left (`path-chart`):** the two-layer `radar-chart` over the skill groups of the job (Languages, Frameworks & libraries, Cloud & DevOps, Data & storage, ML & AI, Engineering practices, Collaboration, and the axes Experience, Level and Certifications when the job has them), and a `data-table` "Skill group (0 to 100)" with the columns **Job requires**, **You have** and **Status**. The status is an icon and a word: **Fit** (check, green), **Above** (star), **Gap** (alert, yellow). A chart with fewer than 3 axes is not drawn; the table stays.
  - **Right (`path-lists`):** two lists. **"Where you fit"** and **"Gaps to close"** (`path-list`, `path-item`).
    - A **fit item:** a green check, the label in bold, a small neutral chip for the kind when it is not a skill (Experience, Level, Certification, Award), "You: Advanced · Needs: Proficient" and an optional note.
    - A **gap item:** a yellow alert icon, a kind chip (**Missing** rose, **Below level** yellow, **Experience** blue, **Level** blue, **Certification** pink), the label in bold, a **"Required"** chip when the job marks the skill as a must, "You: None · Needs: Proficient", the months with a clock icon ("about 3.5 months", "less than 1 month") and an optional note.
    - An empty fit list says "Nothing in your profile meets a requirement of this job yet." An empty gap list says "No gaps: you meet every requirement."
- Last line: "These are estimates from the type of each gap. They are not a promise and not a decision about you."
- Without data (the mock, an old job): the panel has only the head and "A detailed path is not available for this job." Nothing breaks.
- The 12-month **line chart is removed**. There is no projection.

**`fit-panel` ("How this job fits you")** — A `panel` above "Your path to this job". It is not changed in version 2. Head: h2, a muted line, and a blue chip "Fit score {n}". Body in two columns (1.1 : 1; one column on 1024px or less): the `radar-chart` and the numbers table with the formula (F1, F2 or F5) as a hint after each axis name.

**`fit-score`** — A line under the coverage on a job card and on the job detail panel: "Fit score" in 12px `{colors.muted}` and the number in 14px / 600 `{colors.ink}` with one decimal.

**`similar-chip`** — A neutral chip on a similar job card: "{tier} · {n}% alike" (Formula 3).

**Bookmarks screen** — Title "Bookmarks", a secondary "Browse jobs" button at the right, and a `panel` "Saved jobs" with a count, the `sort-select` ("Recently saved" is the default, "Best match", "Newest posted"), the job cards and the `pager`. When the talent removes a bookmark here, its card goes away at once and the page loads again quietly, so that the next job moves up and the count is right. The old "Compare jobs (n/3)" button is gone: each card has the `compare-pick` check box and the `compare-tray` shows the basket. Empty: "No saved jobs yet. Save a job to compare it later." and a primary "Browse jobs" button.

> **Caution:** A match must use only skills, levels, years, certifications, awards, roles, domains, locations and work modes and types. Do not use nationality, ethnicity, gender, age, visa status or country of study.

> **Caution:** Do not link to other job sites (for example "View on …"). Job titles and "Job detail" open the Jinder job detail screen.

### Compare page (both roles)
The Compare page (`#/compare`) is a full page in the app shell. The menu item "Compare" is the current item. The page decides what to show by the role of the user. It works with the real backend only. In mock mode the error panel shows the message "… needs the real Jinder backend …".
There is **no total score and no ranking of people** anywhere on the page. Every chart has a table with the same numbers. All class names start with `cmp-`.

| Role | What it compares | Plan |
|---|---|---|
| Talent | 2 to 5 jobs, against the talent's own skills | Free |
| Employer | 2 to 5 anonymous talent profiles, for **one chosen job** of the employer | Premium |

**Items and address** — The items come from `?ids=a,b,c` in the address, else from the basket (`compare-tray`). The page and the basket stay in step (the address is changed with `history.replaceState`, so no history entry is added). More than 5 ids: the page uses the first 5 and says so ("You chose 7 jobs. You can compare up to 5, so this page uses the first 5.").

**Header** — h1 "Compare jobs" (talent) or "Compare talent" (employer), the sub-line, a count text ("3 of 5 chosen"; at 5: "5 of 5 chosen. That is the most you can compare."), a ghost "Clear all" and a primary **"Add to compare"** (disabled at 5). The employer page has a select **"For which job?"** under it. It lists the own jobs that are not closed. The default is `?jobId=`, else the last used job, else the first open job.

**Cards** (`cmp-cards`, one for each item) — A swatch (the line style and colour of this item in the chart), the title or alias (a link), a "Remove" button (`aria-label="Remove {title} from compare"`) and facts.
- Job card: company and place, a rose "Closed" chip, Level, Experience, Work mode, Salary (middle) and "View job". An empty value shows a dash and the hidden text "Not listed".
- Talent card: Level, Experience, Roles (first 2), "Skills for this job" ("5 of 6 skills + 1 related") and "View profile for this job".

**Panels, talent page:**
1. **"How each job fits you"** — ONE `radar-chart` with one series for each job on the axes that all jobs have, and a table (rows are the axes, with the formula tag F1, F2 or F5; one decimal). The best value of a row has the text "Highest" (no mark when all values are equal).
2. **"Skills side by side"** — Rows are the skills of all jobs. The first column has the skill and "You: Advanced (4)" or "You: —". Each cell has an icon and a word (**Meets**, **Below**, **Missing**) and "Needs Proficient (3) · Must have" or "Nice to have". A job that does not ask for the skill says "Not asked". The last row is "Skills you meet" ("2 of 5 skills").
3. **"Details"** — Level, Specialisation, Experience, Work mode, Job type, Salary, Education, Certifications required and preferred, Preferred awards. A row that no job has is hidden.
4. **"How close the jobs are to each other"** — A matrix of jobs by jobs with the Formula 3 number (one decimal) and the tier word. The diagonal says "Same job". Under it, one `details` for each pair: the parts, the advice and the salary change.

**Panels, employer page:**
1. **"Profiles on the same axes"** — ONE `radar-chart` with one series for each profile (named by the aliases) and a table. After each axis name a small note: "merit model", "fit to the job" or "from the skills table". No "Highest" mark and no sort.
2. **"Skills side by side"** — Rows are the skills of the job. The first column has the skill and "Job needs: Proficient (3) · Must have". Each cell has an icon and a word (**Meets**, **Below**, **Related**, **Missing**) and "Level: Advanced (4)", "Related via {skill}" or "No level". A row "Other skills" and a footer "Skills that meet the job".
3. **"Qualifications and recognition"** — Rows Qualifications, Certifications and Awards. Names and years only ("Name (2023)"), no issuer, no person name. "None listed" when empty.
4. **"Where the profiles differ"** (`compare-areas`) — Rows are the areas (up to 8). A cell says "1st", "2nd", … (the position inside that one area). Profiles with the same position also say "Equal". If all profiles have the same position in an area, every cell says "Equal". The muted line says: "Jinder does not add the areas up and does not rank people. You decide."

**The picker** — The "Add to compare" button opens a dialog (`cmp-picker-dialog`) "Choose jobs to compare" or "Choose talent to compare". It works on a copy of the choice: **"Done"** puts it into the basket and the address and loads the page again; "Cancel", the X and Esc close it without a change. Parts: tabs, a search box, a count line (`aria-live="polite"`: "3 of 5 chosen. You can choose more."), the list "Chosen now" (chips with a remove button) and a list with check boxes ("Show more"). At 5 chosen, the other check boxes are disabled. A row has a check box, the title, short facts and a "Chosen" chip.
- Talent tabs: "Saved jobs" and "Recommended"; the search box searches all jobs (after 300 ms, at least 2 characters).
- Employer tabs: "Talent for this job" and "Saved talent"; the search box filters the loaded rows by alias. A row has no score.

**States** — Loading ("Comparing jobs…"; employer: "Comparing profiles…"; `role="status"`); updating (the old result stays, dimmed, with `aria-busy`); results; **fewer than 2 items** (`cmp-empty`: "Choose at least 2 jobs to compare", the chosen item, a button "Choose jobs"; no request is sent); **error** (`cmp-error`, `role="alert"`: the API message, and a "Remove" button for each chosen item when an item is not found, or "Try again"); **no open job** (employer: "You have no open job" and a button "Post a job").

**Locked page (a Basic employer)** — The page makes **no** compare, job or talent request. It shows the h1 "Compare talent", a gold lock badge, the headline "Compare 2 to 5 talent profiles side by side" with a list of what Compare does, the `upgrade` box ("Compare is part of Premium. In this demo you can switch your plan in Settings.") and a **sample picture** (`cmp-example`): a small table of "Profile A/B/C" and "Skill A/B/C" with the chip "Example" and the text "This picture is a sample. It does not show real people." The picture is `aria-hidden`. A 403 `PREMIUM_REQUIRED` during use shows the same page with the line "Your plan does not include Compare now."

**Accessibility and small screens** — Every table has a hidden `caption`, `scope="col"` and `scope="row"`, and sits in a scroll region (`role="region"`, `tabindex="0"`, `aria-label` "{name}. This table scrolls sideways on a small screen."). On narrow screens the tables scroll inside this region and the **first column is sticky**; the page itself does not scroll sideways. Skill states always have an icon and a word. The state colour pairs are: Meets green, Below gold, Missing rose, Related blue (all 4.5 : 1 or more). Secondary text uses `--cmp-muted` (a darker grey, 6.4 : 1). After a remove, the focus goes to the Remove button of the next card (or the Add button) and a live message says "{title} removed from compare. N jobs left."
- Lesson: a text with the class `sr-only` is `position: absolute`. In a scroll box that is not a positioned box it escapes the clip and widens the whole page. Give every `overflow-x: auto` box that holds `sr-only` text `position: relative`.

### Alias and Settings
**`alias-field`** (Create account, talent only) — Label "Alias (optional)" with a "Suggest one" `text-link` button at the right. Hint: "Employers see this name, not your real name. Leave it empty and we choose one for you." If the alias is taken, the error line shows the message and a `text-link` button "Use “{suggestion}”".

**Alias rules** — An alias is a neutral name, 3 to 30 letters. It must not contain the real name, a country, a nationality or a city of origin. The system alias is "Colour Animal" (for example "Teal Heron"). Do not use personality words or colours that describe skin or hair.

**`your-data` (Settings section, real backend only)** — A `panel` with the intro "Download a copy of the data that Jinder keeps about you, or delete your account and all of its data. You can't undo a delete." A secondary button "Download my data" and a danger button "Delete my account". The delete button opens a small dialog that asks for the password.

**`alias-badge`** — Pill with the pink tint pair, display font 16px / 600. It shows the current alias after "Employers see you as".

**`sidebar-alias`** — In the user block of the `sidebar` (the link to Settings), for talent only: "Alias: {alias}" in 12px `{colors.muted}`, with the alias in `{colors.tint-pink-ink}` at weight 600.

**Settings screen** — Title "Settings". It opens from the **user block** at the bottom of the menu (there is no Settings item). Each section is a `panel` with two columns: an intro (280px: h2 in Inter 18px / 600 and a muted line) and the form (max 480px). On screens of 1024px or less, the columns stack. `#/settings?section=plan` scrolls to the plan.
- **Your plan** (the **first** section): the `plan-card` with the benefits of the plan and, under it, the demo switch (see `plan-card (Settings)`). Without the list of benefits (the mock backend), only the old two radio cards show, in the same place.
- **Profile details:** full name, company (employers), email (read-only, `{colors.surface-subtle}` background).
- **Alias** (talent): `alias-badge`, the new-alias field with "Suggest another".
- **Career profile** (talent): a two-column review list (CV, target roles, skills, shared skills, locations, work type), the buttons "Update CV", "Review translated skills" and "Edit answers", and the `shared-preview` box with the data from the API.
- **Password:** current, new and confirm fields.
- **The demo plan switch** (in "Your plan", under the card): two `plan-option` radio cards side by side (one column on small screens): "Basic" and "Premium" (with a gold "Premium" chip), each with a one-line hint of what it includes. The checked card has a `{colors.accent}` border and `{colors.accent-tint}` background. It is a demo toggle: there is no payment. A failed change (the switch is off on this server) shows the message and puts the switch back to the real plan.
- **Session:** a secondary "Sign out" button.
- **Demo data** (mock mode only): a `btn-danger` "Reset demo data" with a confirm dialog.
- Each form has its own alert. The save button is at the right. After a save, show a green alert.

**`demo-box`** (Sign in, mock mode only) — Under the form: dashed `{colors.accent}` border, `{colors.accent-tint}` background, `{rounded.lg}`, padding `{spacing.md}`. Title "Try the demo" (14px / 600), a hint, and one small secondary button per demo account.

### Status, matching and dialogs (shared components)
**`dialog-small`** — A small native `<dialog>` for report, invite and confirm actions. Width `min(520px, 100% - 32px)`, `{rounded.xl}`, `{shadows.popover}`. Close X at the top right. Title 24px. Foot on `{colors.surface-subtle}` with "Cancel" (ghost) and the submit button. A destructive submit uses `btn-danger`.

**`btn-danger`** — Like `btn-primary`, with `{colors.error}` background and white text. Use it only to confirm an action that can't be undone (decline, not selected, reset).

**`radio-group`** — A list of radio rows, 14px, accent radio. Used for report reasons and interview times.

**`ribbon` (status)** — Pill, padding 6px × 12px, 13px / 600. The text always says the status. Tones: Applied and Declined = `{colors.surface-strong}` with ink; Contacted and In review = blue tint pair; Interview = yellow; Accepted, Offer and Confirmed = green; Not selected = rose. Screen readers hear "Status: …".

**`stepper`** — Six steps in a row: Applied (or Contacted) · In review · Interview · Accepted · Offer · Confirmed. Each step: a 28px circle and a 13px label; a 2px line joins the circles. Done = `{colors.success}` circle with a white check. Current = `{colors.accent}` circle with a 4px `{colors.accent-tint}` ring and an ink 600 label. To do = `{colors.surface-strong}` circle with a muted number. An ended application adds a rose step "Not selected" or "Declined" with an X.

**`history`** — A list, newest first. Each row: date and time in 13px `{colors.muted}` (170px) and "**Who** — what happened" (You / Employer / Talent).

**`action-panel`** — A `panel` with a 2px border in a tint colour (blue, yellow or green) that shows the next step for this user. It has one short title, one short text and the actions at the right. Only the actions that are allowed now are shown.

**`skill-match`** — One row per required skill: icon, skill name (ink 500), state text at the right (12px / 600). Match = green tint pair "You have it" (employers: "Has it"); Related = blue tint pair "Related" + "via {skill}"; a skill that the talent has below the asked level (`fitStatus` "below") = the same blue pair "Below level" + "You: {level} · Needs: {level}" (employers: "Has: {level} · Needs: {level}"); Gap = yellow tint pair "Gap". The text gives the meaning, the colour only helps.

**`coverage`** — "{c}%" in the display font + "skills covered" + accent meter + "{m} of {n} skills + {p} related". Small version (`cov-mini`) in lists: 20px number, 4px meter, 12px line, right aligned.

**`profile-card`** (shared profile) — The alias with a 28px pink initials `avatar`, then a list of rows (130px muted label : neutral chips): Roles, **Level**, **Experience** (the exact years first, else the range), Skills (green chips with the level as text: "Python · Advanced"), **Certifications**, **Awards** (names and years only, no issuer, no kind), Qualifications, Domains, Target roles, Locations, Work types. A row for a version 2 key shows only when the key is in the data (the copy of an old application has none). It shows only what employers may see.

**`identity-box`** — On the employer review screen. Anonymous: `{colors.surface-subtle}` box with an eye-off icon, "Anonymous" and a hint. Shared: green tint pair box with a user-check icon, the name and the email, and "The talent agreed to share this for the interview."

**`note-text`** — A quote for notes, messages and offers: `{colors.surface-subtle}`, 3px `{colors.accent}` bar at the left, 14px, keeps line breaks.

**`tabs`** — Segmented tabs on `{colors.surface-muted}` (padding 4px, `{rounded.md}`). The selected tab is white with `{shadows.xs}` and ink 600 text. A count in 12px muted can follow the label.

### Applications (talent)
**Apply screen** — "Apply for {job}". A small steps line ("1. Review your profile · 2. Send · 3. Track"). Two columns: a `panel` "What the employer sees" with the `profile-card` and an "Edit profile" button, and a side `panel` "Your skills for this job" (`coverage` + `skill-match`). Then a `panel` "Send your application" with an optional note (500 characters, live counter) and the warning "Do not add your name, email or phone number…". Primary large "Send application".

**Applications screen** — `tabs` Active / Past (the tab links keep the sort), the `sort-select` ("Recently updated", "Best skill match", "Newest application") and the `pager`. The API has no filter for Active and Past, so the browser reads all the pages, filters the tab and cuts the page. Each row (`app-row`, hairline, `{rounded.lg}`): job title link, company and city, dates; at the right the `ribbon`, a yellow "Action needed" chip when the talent must act, and the coverage text. Rejected and finished applications are in Past.

**Tracking screen** — A success alert after sending. The job title, the `ribbon`, the `stepper` in a panel, then the `action-panel` for the current step: change the note (only while Applied), choose an interview time (radio cards with a calendar icon; the chosen card has an accent border) with the consent box "Share my name and email with this employer for the interview." (not ticked by default), the offer with "Accept offer" and "Decline offer", or the feedback form when the application is finished. Below: "What you sent" (the note and the `profile-card` copy) and "Your skills for this job", then the `history`.

> **Caution:** The talent stays anonymous until they tick the consent box. Never tick it for them.

### Employer screens
**Employer Home** — Greeting and "Post a job". Three `report-card`s: Open jobs, Jobs at target, Waiting for you. Two equal panels: "My jobs" (rows with a close badge) and "Top talent" (alias, roles, `cov-mini`). A panel "Hiring activity" with charts.

**`close-badge`** — Green "Open"; yellow "Closes in {n} days" when fewer than 7 days are left; rose "Closed".

**My jobs** — In the head: a secondary "Post from a PDF" button and the primary "Post a job". A panel "Your jobs" with the line "Newest first." (one sort only, so no `sort-select`), the rows and the `pager`. Rows with the job title link (it opens the **job overview**), category · city · type, dates, the `close-badge`, a yellow "{n} waiting for you" chip, a target meter "{applicants} / {target}", a secondary small "Applicants" button and an "Edit" button.

**Job form** — Title, a 3-column grid (**Domain**, **Specialisation** (it changes with the domain), **Level**, **Minimum years** and **Maximum years** (an empty maximum means "or more"), **Work mode**, **Education**, location, work type, salary, close date, target applicants), the description and the lists below. When the employer edits a job, a yellow note says that applicants get a notification. Ask only for job information: never for age, gender, nationality or visa status.
- **`jd-editor`** (the description): a text area (`maxlength` 10,000, with the counter "n of 10,000 characters"). A **new** job starts with a template of 8 headings ("## About the role", "## What you will do", "## What you bring", "## Nice to have", "## Tech stack", "## What we offer", "## About the company", "## How we hire"), each with one empty bullet. A hint says what "## " and "- " do. When the form is sent, empty bullets, headings without text and extra blank lines are removed.
  The **"Preview"** button (`aria-expanded`; "Hide preview") shows the text in a `jd-view` box and follows the text while it is open.
- **`skill-req`** (**required skills**, 1 to 12): a row for each skill with its name, a **level** select ("1 - Beginner" to "5 - Expert") and a **"Must have"** check box, and a remove button. The input "Add a skill" is a `combobox`. "Suggest skills" adds the suggestions at level 3 and Must have. A job from older data starts at level 3 and Must have.
- **`cert-editor`**: two `combobox` lists, "Required certifications" and "Preferred certifications" (pick from the 38 known names or type text; chips with a remove button; at most 10 in each list; a name is in one list only).
- **`award-editor`**: 12 check boxes, one for each kind of award ("Preferred awards", at most 10).
- Errors from the API are written next to the field (`aria-invalid`, `aria-describedby`). The first error takes the focus. In mock mode the fields that the mock does not keep are not drawn.

**Job overview** (`#/my-jobs/:id/overview`) — The page of one job for the employer, with the full job description. After "Post job" and "Save changes" the app opens it.
- Head: h1 with the title, a muted line (company · place · salary), chips (`jo-chips`: status "Open", "Closing soon" or "Closed", the level and the work mode) and the actions: a primary **"Edit job"** (not for a closed job), a secondary "See talent" and a secondary "See applicants", and a back link "My jobs". A closed job has a banner (`jo-banner`, `role="note"`) and the page is read-only.
- Small stats (`jo-stats`, `report-card`s): Applicants (with the target meter), Waiting for you, Invited, and "Interest in this job" (Premium: Shown, Opened, Saved, Applied; Basic: a gold lock badge).
- A panel **"About the role"** with the full description in the `jd-view` box (scroll box, keyboard focus).
- A panel **"Job facts"** (`jo-facts`, a `dl`): Domain, Specialisation, Level, Experience ("5 to 9 years", "6 years or more", "Up to 9 years"), Type, Work mode, Education, Posted and Closes. A fact that the job does not have is left out. A `null` shows "Not given".
- A panel **"Skills"**: a table with Skill, Level needed and Must or nice (Must first). A job without levels shows chips.
- A panel **"Certifications and awards"** (required, preferred, preferred awards). It is left out when the job has none.

**`job-import`** (new jobs only, above the form) — A `panel` "Start from a job description file" with a `dropzone` (PDF or DOCX, up to 10 MB), a `file-chip`, and a primary "Read file and fill the form" button. While the file is read: `progress-indeterminate` + "Reading your file…". After: the form is filled; each filled field has a "From your file" AI chip after its label, and a field the file does not show has a yellow "Missing" chip. A change to a field removes its chip. A green alert tells the employer to check each field and add the close date and the target. In mock mode, show the `demo-banner`. Between the panel and the form: a thin divider with "or fill in the form yourself".

**Applications for a job** — Three cards (applicants vs target, waiting, required skills), a "Show" filter and rows: alias link, dates, `ribbon`, "Waiting for you" chip, `cov-mini`, "Review" button. The list has the line "Newest first." and the `pager`. A status filter reads all the pages and cuts the pages in the browser.

**Review screen** — The alias as the title, the `stepper`, the `action-panel` (start review; offer 1 to 3 interview times with date-time fields; confirm the time; accept; send an offer; not selected; feedback), then "Talent profile" (`identity-box`, the note, the `profile-card` with the level, years, certifications and awards when the snapshot has them) and "Skills for this job" (`coverage` + the `skill-table` when the snapshot has skill levels, else `skill-match`; + "This shows skills only. Use your own judgement for the decision."), and the `history`.

**Talent screen** — A toolbar (`list-toolbar`): the job select, a link "Job overview", `tabs` All / Saved and the `sort-select` ("Best fit for this job" is the default, "Recently updated"). Under it, the required skills as chips, then `cand-card`s, the `pager` and the notes.
- **`cand-card`**: the alias link and an "In your pipeline" chip; a **facts row** (`cand-facts`): the level chip (blue, only when known), the years (the exact `yearsExperience` when known, else the band) and "Updated N days ago" (`cand-updated`; "Updated today"); roles and cities; up to 6 skill chips with the level as text ("Python · Advanced"; green when the job asks for the skill, with a hidden "(the job asks for this skill)"); then up to 3 **`cred-chip`**s for certifications and awards together (a graduation icon is a certification, a star icon is an award, a hidden word "Certification:" or "Award:", names and years only, for example "AWS Certified Cloud Practitioner (2024)") and "+N more"; then the actions (Save, Not for this job, Report, Invite, the `compare-pick` check box). At the right: `cov-mini`. **No score on the card.**
- **Basic employer:** 5 cards and **no pager**, and under the list a gold `upgrade` box: "You see the top 5 of {N} talent profiles. Premium shows all of them." with a lock badge. Invite and the Compare check box are replaced by a `locked-badge` (static, inside a ghost button) that opens the "Premium feature" dialog.
- **Premium employer:** the "Compare" check box on each card (`compare-pick`, label "Compare" and the alias for screen readers). A 6th tick is refused: the check box is cleared and the note "You can compare up to 5 profiles." shows (and a live message says it). The check boxes follow the basket.
- The page size is remembered for each list: Talent (All) and Talent (Saved) have their own. A change of the page, the size or the sort loads the list in place, without a screen flash.

**Talent detail** — The alias, "Anonymous profile · matched to {job}", "Updated N days ago"; Save, Invite or "Review application", a Compare toggle ("Add to compare" / "In compare list", Premium) or a lock badge (Basic), Report. Two columns:
- A `panel` "Profile" (the version 2 `profile-card`: Level, Experience, Roles, Skills with level text and, when the job lists a level, "needs Proficient" (`chip-need`), Certifications, Awards, Qualifications, Domains, Target roles, Locations, Work types; a shield hint about what is never shown). A row is left out when the answer has no such key. A `null` shows "Not given".
- A side `panel` "Skills for {job}": the coverage and the **`skill-table`**.

**`skill-table`** (`skills-wide`) — A `data-table` with four columns: **Skill**, **Job needs** ("Advanced · Must have" or "Nice to have"), **Talent** (the level as text, or "—") and **Result**. The result is an icon and a word, and the cell has a tint: **Meets** (check, green pair), **Below** (alert, gold pair; contrast 4.5 : 1 or more), **Missing** (x, rose pair), **Related** (target, blue pair, "via {skill}") or **Has it** (when the talent has the skill but the level is not known). A text count sits in the side box ("1 meets", "1 missing"). The table shows only when the job has levels and the talent has skill levels; otherwise the old `skill-match` list stays. The browser derives the result from three API values (the skill status, the talent's levels and the job's levels). It makes no number and no score.

> **Caution:** Employer screens never show a name, email, photo, nationality, country of study, employer names or the CV, unless the talent agreed to share the name and email for an interview.

### Notifications and insights
**Notifications screen** — A list of rows (`notif`): an icon tile, the title (a link to the screen it is about), the body, and a 12px line with the date, "Email sent (demo)" for email events, and "Unread". Unread rows have a `{colors.accent}` border and `{colors.accent-tint}` background. "Mark all as read" at the top right.

**`bar-chart`** — A simple chart in HTML: rows of label (max 160px, ellipsis) · 10px pill track with an accent fill · the number as text. Charts are in a 2-column grid (1 column on 1024px or less), each with a 14px / 600 caption.
- Talent Home "Your activity": active applications by status and "What employers see". The "Skill insights" panel (Premium): "Skills to learn next" and "Demand for your skills".
- Employer Home "Hiring activity": applicants per job. Premium: pipeline by stage and an "Interest per job" table (shown, opened, saved, applied — totals per job only).

**`upgrade`** — Yellow tint pair box with a 1px dashed yellow-ink border, `{rounded.lg}`: a gold `locked-badge` ("Premium" with a lock; on the employer screens it is a button that opens the "Premium feature" dialog), one line of text and a secondary "See plans" button (to Settings › Plan).

**`data-table`** — 14px, 10px × 12px cells, hairline row lines, uppercase 12px muted column heads, row heads in ink 600. It scrolls inside its container on small screens.

> **Caution:** Charts show counts about jobs, skills and the process. Never show a chart that ranks or scores a person, and never show what one talent did.

### Interaction and accessibility
- Transitions: 150ms with `cubic-bezier(0.2, 0, 0, 1)` on color, border and shadow only.
- Buttons move down 1px when pressed.
- Focus: 2px `{colors.accent}` outline with 2px offset on `:focus-visible`.
- Respect `prefers-reduced-motion`: remove transitions.
- Text contrast must be 4.5 : 1 or more.
- On touch screens, buttons and inputs must be 44px tall or more. This includes the pager buttons, the sort and page size selects, the "Compare" check box and the level selects.
- **Lists:** every list has a heading that takes the focus after a page change, and a polite live message ("Page 2 of 7", "Sorted by Newest posted. Page 1 of 7", "20 rows per page. Page 1 of 3"). While a page loads, the list has `aria-busy="true"` and is half transparent. A late answer is dropped.
- **Scroll boxes** (`jd-view`, tables): a `role="region"` with `tabindex="0"` and a visible focus ring, so that the keyboard can scroll them.
- **Premium:** a lock or a crown always comes with the word "Premium" (a hidden text for the screen reader). The state of a benefit is a word ("Used", "Not used yet", "Included").
- A status, a skill result or a chart value is never only a colour. It has an icon and a word, or a table.

## Do's and Don'ts

### Do
- Keep the page calm: warm sand behind white cards; add color through tint chips, accents and product screenshots.
- Use navy `{colors.ink}` for all headings and the primary button.
- Set display headlines in Plain Black (or Inter 500 substitute) with negative letter-spacing.
- Always pair a pastel tint with its own deep ink color.
- Use bold periwinkle text with no underline for all inline links.
- Keep controls compact (36px buttons) and rounded (10px).
- Show real product UI — reports, charts, company profiles — as the main visual.
- Use SVG line icons from `icons.svg`.
- Show the source of every statistic.
- Explain every match score with reasons in plain language.

### Don't
- Don't use pure black (#000) for text or buttons.
- Don't use pastel tints as full-section backgrounds or mix a tint with gray body text.
- Don't bold display weight beyond 500 — it reads as bombastic.
- Don't add large, soft, blurry shadows or glassmorphism.
- Don't use sharp 0px corners on cards or buttons.
- Don't use more than 2 tint colors inside one card.
- Don't use emoji as icons or decoration.
- Don't show a score without the reasons for it.
- Don't show one combined score or a ranking of a person. Show coverage per job, skill by skill. In Compare, never add the axes or the areas up.
- Don't use a line chart for a projection of the future. Version 2 removed the 12-month chart.
- Don't use colour as the only signal: statuses, skill states and chart values always have text.
- Don't show made-up quotes or numbers as real data in a public demo.

## Responsive Behavior

### Breakpoints

| Name | Width | Key Changes |
|---|---|---|
| Mobile | < 768px | Hamburger nav; h1 72→36px (500, -1px); display-lg 56→36px; grids 1-up; plan cards stack |
| Tablet | 768–1024px | Nav tightens; feature grids 2-up |
| Desktop | 1024–1440px | Full nav; 3-up feature grids |
| Wide | > 1440px | Same as desktop, max content ~1200px |

### Touch Targets
- Desktop button height is 36px; on touch devices raise `{component.button-primary}` and `{component.text-input}` to at least 44px.

### Collapsing Strategy
- Nav dropdowns turn into an accordion inside the mobile menu.
- Hero stays centered; screenshot scales to full width with `{rounded.lg}` kept.
- Comparison tables scroll horizontally inside their container on mobile.

## Iteration Guide

1. Work on ONE component at a time and reference its key (`{component.plan-card}`, `{component.tint-chip}`).
2. Choose a tint pair by meaning. See [Tint meaning in Jinder](#tint-meaning-in-jinder).
3. Variants (`-active`, `-disabled`, `-focused`) live as separate entries.
4. Use `{token.refs}` everywhere — never inline hex.
5. Never document hover.
6. Display = Plain Black 500 with negative letter-spacing; UI, nav, buttons = Inter 500–600; body = Inter 400.

## Known Gaps

- Tokens were extracted from the live june.so marketing pages (homepage and /pricing) in October 2026, after June announced it was joining Amplitude; parts of the original site may already be removed.
- Spacing scale, container widths, breakpoints, mobile type sizes, input styles, segmented tabs, report-card and chart palette are inferred conventions, not measured values.
- Plain Black is licensed and not a public web font; Inter 500 with negative letter-spacing is the substitute.
- Illustrations are out of scope. Jinder uses product previews, not illustrations.
- The quotes on the auth pages and the sample data in the product preview are placeholders. Replace them with real content before a public demo.
- The old rules `lc-*` of the removed 12-month chart are removed from `styles.css`. The low-contrast styles are open design debt (see Colors): `--muted` (3.3:1), `.chip-yellow` (3.1:1), accent text (4.3:1) and white text on the accent colour (3.7:1). QA measured 55 kinds of text below 4.5:1 (`jinder_platform/docs/changes/QA.md`, finding A11Y-1).
- The new parts were checked in Chrome only, with the keyboard and the DOM. No screen reader (NVDA, VoiceOver) was tested. `color-mix()` has a fallback to the plain tokens, and the fallback colours were not looked at.
- The frontend is complete only on the client side. In `mock` mode, a mock API in the browser stores accounts in `localStorage`. This is for demos only. The mock has its own smaller ICT data (24 jobs, 10 sample talent, 5 CV samples, 4 job file samples; no word of another field of work), and the features of version 2 that need the formula engine or the real backend (Compare, the plan card with benefits, "Your path to this job") are not in the mock. The real backend follows the API contract in `prompt.md`.
- In mock mode, the CV upload does not read the file: the mock returns one of 5 ICT sample results (data analyst, software developer, machine learning researcher, business analyst, systems administrator; the file name chooses it), with the level, the exact years, certifications, awards and skill levels, and the screen shows the `demo-banner`. The translation library has 33 role pairs and 37 skill pairs (mock), all ICT. Jobs are the 24 ICT jobs that are embedded in the app (a copy of 24 of the 50 synthetic jobs; a job has the full description, its level, years, skill levels, certifications and awards). Skills are found with the word patterns of the taxonomy; employers choose the skills of the jobs they post. Premium is a demo toggle in Settings (no payment). Emails are not sent: notifications show "Email sent (demo)". "Post from a PDF" does not read the file in mock mode: the mock returns one of 4 ICT sample job descriptions (the file name chooses it) and shows the `demo-banner`. The demo data (2 demo accounts, 10 anonymous sample talent, the 4 jobs of the demo employer, 7 applications) is written once into the browser store (key `jinder.mock.db.v2`) and can be reset in Settings. The employer screens of the mock keep the old fields (no level, years, certifications or awards on a talent card).
