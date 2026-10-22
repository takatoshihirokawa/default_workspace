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

## Admin Panel (CMS)

Path: `/admin`

### Authentication
- Supabase Auth + Google OAuth
- Only the owner's Google account can access
- Middleware redirects unauthenticated users to `/admin/login`

### Features
1. **Dashboard** — list of works, quick stats
2. **Works CRUD** — add / edit / delete works via form UI
3. **Claude Chat** — chat interface powered by Claude API; natural language commands execute Supabase operations (e.g. "新しいワークを追加して" → form pre-filled or directly inserted)
4. **Profile editor** — edit About section content

### Claude API Role (admin panel)
- Endpoint: `POST /api/admin/chat` (Next.js Route Handler, server-side, API key in env)
- Model: `claude-sonnet-4-6`
- System prompt: gives Claude access to available tools (create_work, update_work, delete_work, list_works)
- Tool use: Claude calls tools that execute Supabase mutations
- Response streamed to chat UI

---

## Supabase Schema

### `works` table
```sql
id          uuid primary key default gen_random_uuid()
slug        text unique not null
title       text not null
year        int not null
tags        text[] not null
description text not null
thumbnail   text
sort_order  int default 0
created_at  timestamptz default now()
updated_at  timestamptz default now()
```

### `contact_submissions` table
```sql
id            uuid primary key default gen_random_uuid()
last_name     text not null
first_name    text not null
last_kana     text
first_kana    text
email         text not null
inquiry_type  text not null
message       text not null
created_at    timestamptz default now()
```

---

## Implementation Phases

### Phase 1 — Frontend
- Project scaffold (Next.js 15 + Tailwind + Framer Motion)
- Global layout, custom cursor, dark theme
- Hero section with mouse-tracking animation
- About, Works (static data from Supabase or seed), Contact sections
- Work detail page template
- Responsive layout

### Phase 2 — Supabase Integration
- Supabase client setup
- Works data from `works` table
- Migrate 6 seed works into Supabase

### Phase 3 — Admin Panel
- Supabase Auth + Google OAuth
- `/admin` dashboard, works CRUD UI
- Claude API chat interface with tool use
- Profile editor

### Phase 4 — Contact & Deploy
- Contact form → Supabase `contact_submissions`
- Vercel deployment + custom domain `takatoshihirokawa.com`
- Performance / accessibility pass

---

## Out of Scope (v1)

- Light mode toggle
- Topics section content (section exists but shows empty state)
- Analytics
