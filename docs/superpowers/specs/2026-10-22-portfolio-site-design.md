# Portfolio Site — Design Spec

**Author:** Takatoshi Hirokawa  
**Date:** 2026-10-22  
**Status:** Approved

---

## Overview

Migrate the portfolio site at takatoshihirokawa.com from Studio to a self-built Next.js environment. The new site is a redesign — not a replica — with a creative, interactive aesthetic, dark mode, and mouse-following animations. Content is managed as MDX files edited directly by Claude Code and deployed via Vercel.

---

## Goals

- Own the codebase and design, free from Studio's constraints
- Deliver a visually striking, animation-rich portfolio that reflects the owner's craft
- Make content updates effortless: Claude Code edits MDX files, commits, and Vercel auto-deploys
- Fast, performant, mobile-responsive

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | Next.js 15 (App Router) |
| Styling | Tailwind CSS v4 + CSS Variables |
| Animation | Framer Motion |
| Content | MDX files (`/content/`) |
| Fonts | Google Fonts (選定は実装時) |
| Deploy | Vercel |
| Repo | New GitHub repository (`takatoshihirokawa/portfolio`) |

---

## Site Structure

### Pages

| Page | Path | Type |
|---|---|---|
| Home | `/` | Single-scroll page |
| Work detail | `/works/[slug]` | Dynamic MDX page |
| Privacy Policy | `/privacy-policy` | Static MDX page |

### Home Sections (in order)

1. **Hero** — Full-viewport. Name, tagline, role tags. Custom cursor + mouse-tracking background effect.
2. **About [01]** — Profile text, field tags, tools used.
3. **Works [02]** — Card grid of projects. Scroll-triggered fade-in per card.
4. **Topics [03]** — Reserved section (empty for now, shows placeholder).
5. **Contact [04]** — Inquiry form + SNS DM links.

### Navigation

- Fixed header with logo + anchor links (About / Works / Topics / Contact)
- Smooth scroll to section anchors
- Mobile: hamburger menu

---

## Design Language

### Theme

- **Mode:** Dark primary (light mode toggle optional, v2)
- **Background:** Near-black (`#0a0a0a` or similar)
- **Text:** Off-white
- **Accent:** Single accent color (warm or electric — finalized during implementation)
- **Aesthetic:** Minimal, high-contrast, typographic

### Typography

- Display / heading: geometric sans or editorial serif (finalized during implementation)
- Body: clean readable sans
- Mixed Japanese / English — both must render beautifully

### Animations

| Element | Effect |
|---|---|
| Custom cursor | Circular element that follows mouse with slight lag (`useMotionValue` + `useSpring`) |
| Hero background | Subtle mouse-reactive particle or gradient shift |
| Section entry | Fade-up on scroll (Framer Motion `whileInView`) |
| Work cards | Hover: subtle tilt + lift (perspective transform) |
| Page load | Staggered reveal of hero elements |
| Nav links | Underline slide-in on hover |

---

## Content Structure (MDX)

```
/content
  /works
    kamiculum-learning-platform.mdx
    hanashiru-1on1-web-app.mdx
    hbl-kikuchi-fuma-campaign-site.mdx
    kilel-brand-website-movie-production.mdx
    salonwriter-ai-writing-app.mdx
    joule-works-internal-management-app.mdx
  profile.mdx
  privacy-policy.mdx
```

### Work MDX Frontmatter Schema

```yaml
---
title: string
year: number
tags: string[]        # Direction, Development, Design, etc.
thumbnail: string     # /images/works/<slug>/thumb.jpg
description: string   # Short description for card
---
```

---

## Contact Form

- Fields: 姓・名・セイ・メイ、メールアドレス、お問い合わせ種別（dropdown）、内容、プライバシー同意チェックボックス
- Submission: Supabase (`hirokawa.dev` project) — insert into `contact_submissions` table via Supabase client (Phase 3)
- Phase 1: static `e.preventDefault()` + thank-you message only
- SNS links: LINE / Instagram / X(Twitter)

---

## Implementation Phases

### Phase 1 — Frontend (this sprint)
- Project scaffold (Next.js 15 + Tailwind + Framer Motion)
- Global layout, custom cursor, dark theme
- Hero section with mouse-tracking animation
- About, Works (static data), Contact sections
- Work detail page template
- Responsive layout

### Phase 2 — Content & Data
- MDX pipeline (`next-mdx-remote` or `@next/mdx`)
- Migrate all 6 works to MDX with real content
- Profile MDX
- Privacy policy page

### Phase 3 — Contact & Deploy
- Contact form with Resend or Formspree
- Vercel deployment setup + custom domain
- Performance / accessibility pass

---

## Out of Scope (v1)

- Light mode toggle
- Topics section content (section exists but shows empty state)
- CMS admin UI
- Analytics
