# Portfolio Site Phase 1 — Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Phase 1 frontend of takatoshihirokawa.com as a new Next.js 15 project in a new GitHub repository, with dark theme, custom mouse-tracking cursor, and all home sections (Hero / About / Works / Contact).

**Architecture:** Single-page scroll layout in Next.js 15 App Router. All sections live in `app/page.tsx` and are composed from components in `components/sections/`. Framer Motion drives all animations — custom cursor via `useMotionValue` + `useSpring`, section entries via `whileInView`. Works data is static TypeScript in `lib/works.ts` for Phase 1; MDX pipeline is deferred to Phase 2.

**Tech Stack:** Next.js 15 (App Router), Tailwind CSS v4, Framer Motion, TypeScript

**Spec:** `docs/superpowers/specs/2026-10-22-portfolio-site-design.md`

## Global Constraints

- New GitHub repository: `takatoshihirokawa/portfolio`
- New project lives at `/home/user/portfolio` (outside timer-app)
- Node.js ≥ 20, next@15, framer-motion@11+, tailwindcss@4
- TypeScript strict mode
- All text: exact copy from the spec's content section (Japanese/English mixed)
- Dark background: `#0a0a0a`; accent: `#e8ff47` (electric yellow-green)
- No light mode toggle in Phase 1
- Custom cursor must be disabled on touch devices (pointer: coarse)
- All sections must be responsive: mobile-first, single column on < 768px

## Review Focus

- Custom cursor jank on fast mouse moves — `useSpring` stiffness/damping must feel smooth, not laggy or overshooting; test at Task 3
- Hero mouse-tracking background must not cause layout shift or scroll performance issues — use `transform` only, never `top`/`left`; verified at Task 4
- `whileInView` sections firing on mobile where IntersectionObserver behaves differently — use `once: true` and `margin` settings; verified at Task 5
- Work card hover tilt breaking on keyboard navigation — tilt must only activate on `onHoverStart`, not on focus; verified at Task 6
- Contact form submit must not hard-reload the page even without a backend — use `e.preventDefault()` and show a static success state; verified at Task 7

---

## File Structure

```
/home/user/portfolio/
├── app/
│   ├── layout.tsx              Root layout: fonts, CustomCursor, dark body bg
│   ├── page.tsx                Home: renders all section components in order
│   ├── globals.css             Tailwind base + CSS custom properties
│   ├── works/
│   │   └── [slug]/
│   │       └── page.tsx        Work detail template (static placeholder)
│   └── privacy-policy/
│       └── page.tsx            Privacy policy stub
├── components/
│   ├── ui/
│   │   └── CustomCursor.tsx    Mouse-following cursor (Client Component)
│   ├── layout/
│   │   ├── Header.tsx          Fixed nav with anchor links + mobile hamburger
│   │   └── Footer.tsx          Copyright + back-to-top
│   └── sections/
│       ├── Hero.tsx            Full-viewport hero + mouse-reactive gradient
│       ├── About.tsx           Profile, field tags, tools
│       ├── Works.tsx           Works grid + WorkCard
│       ├── Topics.tsx          Empty-state placeholder
│       └── Contact.tsx         Form (static) + SNS links
├── lib/
│   └── works.ts                Static works data array (type + 6 entries)
├── public/
│   └── images/                 (empty for now)
├── next.config.ts
├── tailwind.config.ts
└── package.json
```

---

## Task 1: Repository & Project Scaffold

**Files:**
- Create: `/home/user/portfolio/` (entire Next.js project)
- Create: `package.json`, `next.config.ts`, `tailwind.config.ts`, `tsconfig.json`
- Create: `app/globals.css`

**Interfaces:**
- Produces: runnable dev server at `localhost:3000`; all later tasks build on this scaffold

- [ ] **Step 1: Create new GitHub repository**

Use the `mcp__github__create_repository` tool:
- name: `portfolio`
- owner: `takatoshihirokawa`
- private: false
- description: "Portfolio site — takatoshihirokawa.com"

- [ ] **Step 2: Scaffold Next.js project**

```bash
cd /home/user
npx create-next-app@latest portfolio \
  --typescript \
  --tailwind \
  --app \
  --no-src-dir \
  --no-eslint \
  --import-alias "@/*"
cd portfolio
```

- [ ] **Step 3: Install dependencies**

```bash
npm install framer-motion
```

- [ ] **Step 4: Configure `next.config.ts`**

Set `reactStrictMode: true`. No other changes needed for Phase 1.

- [ ] **Step 5: Set up `app/globals.css` with CSS variables**

Add to globals.css after Tailwind directives:
```css
:root {
  --bg: #0a0a0a;
  --fg: #f0f0f0;
  --accent: #e8ff47;
  --muted: #555555;
}
body {
  background-color: var(--bg);
  color: var(--fg);
}
```

- [ ] **Step 6: Verify dev server starts**

```bash
npm run dev
```
Expected: dev server at localhost:3000, no errors in terminal

- [ ] **Step 7: Initialize git and push**

```bash
git init
git remote add origin https://github.com/takatoshihirokawa/portfolio.git
git add .
git commit -m "feat: scaffold Next.js 15 project with Tailwind and Framer Motion"
git push -u origin main
```

---

## Task 2: Static Works Data

**Files:**
- Create: `lib/works.ts`

**Interfaces:**
- Produces: `Work` type + `works` array, consumed by `Works.tsx` and `works/[slug]/page.tsx`

```ts
export type Work = {
  slug: string
  title: string
  year: number
  tags: string[]
  description: string
  thumbnail: string
}
export const works: Work[]
```

- [ ] **Step 1: Create `lib/works.ts` with type and 6 entries**

Exact slugs and titles from spec:
```ts
export type Work = {
  slug: string
  title: string
  year: number
  tags: string[]
  description: string
  thumbnail: string
}

export const works: Work[] = [
  {
    slug: "kamiculum-learning-platform",
    title: "カミキュラム 美容室向け教育・学習Webアプリ",
    year: 2026,
    tags: ["Direction", "Development", "Design"],
    description: "美容室スタッフ向けのオンライン教育・学習プラットフォーム。",
    thumbnail: "/images/works/kamiculum.jpg",
  },
  {
    slug: "hanashiru-1on1-web-app",
    title: "ハナシル 1on1支援Webアプリ",
    year: 2026,
    tags: ["Direction", "Development", "Design", "Project Management"],
    description: "1on1面談を支援するWebアプリケーション。",
    thumbnail: "/images/works/hanashiru.jpg",
  },
  {
    slug: "hbl-kikuchi-fuma-campaign-site",
    title: "HBL × 菊池風磨 Campaign Site",
    year: 2026,
    tags: ["Direction", "Development"],
    description: "ブランドキャンペーンサイト。",
    thumbnail: "/images/works/hbl.jpg",
  },
  {
    slug: "kilel-brand-website-movie-production",
    title: "KILEL Brand Website & Movie Production",
    year: 2026,
    tags: ["Direction", "Produce"],
    description: "ブランドサイトと動画制作。",
    thumbnail: "/images/works/kilel.jpg",
  },
  {
    slug: "salonwriter-ai-writing-app",
    title: "SalonWriter 美容師向けAI文章生成Webアプリ",
    year: 2025,
    tags: ["Direction", "Development", "Design"],
    description: "美容師向けAI文章生成ツール。",
    thumbnail: "/images/works/salonwriter.jpg",
  },
  {
    slug: "joule-works-internal-management-app",
    title: "Joule Works 社内業務管理Webアプリ",
    year: 2025,
    tags: ["Direction", "Development", "Design"],
    description: "社内業務管理Webアプリケーション。",
    thumbnail: "/images/works/joule-works.jpg",
  },
]
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add lib/works.ts
git commit -m "feat: add static works data"
```

---

## Task 3: Global Layout — CustomCursor + Header + Footer

**Files:**
- Create: `components/ui/CustomCursor.tsx`
- Create: `components/layout/Header.tsx`
- Create: `components/layout/Footer.tsx`
- Modify: `app/layout.tsx`

**Interfaces:**
- Consumes: CSS variables from `globals.css`
- Produces: `<CustomCursor>`, `<Header>`, `<Footer>` — consumed by `app/layout.tsx`

- [ ] **Step 1: Create `components/ui/CustomCursor.tsx`**

`"use client"` component. Use `useMotionValue` for x/y and `useSpring` (stiffness: 300, damping: 28) for smooth lag. Render a 12px circle div positioned fixed with `pointer-events: none`, `z-index: 9999`. Hide on touch devices via a `window.matchMedia("(pointer: coarse)")` check in `useEffect`. The outer ring (40px, border only) uses slower spring (stiffness: 150, damping: 20) for trailing effect.

Review Focus test — add this in a comment block at top of file:
```ts
// REVIEW: spring values — stiffness 300/damping 28 for dot, 150/20 for ring
// If cursor feels laggy: increase stiffness. If overshooting: increase damping.
```

- [ ] **Step 2: Create `components/layout/Header.tsx`**

`"use client"` component (needs scroll detection for background). Fixed position, full width. Logo: "Takatoshi Hirokawa" as `<a href="/">`. Nav links: About (`/#about`), Works (`/#works`), Topics (`/#topics`), Contact (`/#contact`). Add `bg-[var(--bg)]/80 backdrop-blur` when scrolled > 50px (use `useScroll` from framer-motion or plain `window.scrollY`). Mobile: hamburger icon toggles a full-screen menu overlay with the same links.

- [ ] **Step 3: Create `components/layout/Footer.tsx`**

Server Component. Content: `© 2026 Takatoshi Hirokawa` left, "Back to Top" (`<a href="#top">`) right.

- [ ] **Step 4: Update `app/layout.tsx`**

Import Google Font (Noto Sans JP + Inter via `next/font/google`). Add `<CustomCursor>`, `<Header>`, `<Footer>` wrapping `{children}`. Set `<body id="top">`.

- [ ] **Step 5: Verify layout renders**

```bash
npm run dev
```
Expected: cursor dot follows mouse, header visible, footer at bottom. Cursor absent on touch-simulated viewport.

- [ ] **Step 6: Commit**

```bash
git add components/ app/layout.tsx
git commit -m "feat: add global layout with custom cursor, header, and footer"
```

---

## Task 4: Hero Section

**Files:**
- Create: `components/sections/Hero.tsx`
- Modify: `app/page.tsx`

**Interfaces:**
- Consumes: CSS variables
- Produces: `<Hero>` — used in `app/page.tsx`

- [ ] **Step 1: Create `components/sections/Hero.tsx`**

`"use client"` component. Full viewport height (`min-h-screen`). Structure:

```
<section id="top-home">
  <MouseGradient />     ← radial gradient that follows mouse (transform only)
  <div>                 ← content, staggered reveal on mount
    <p>Planning / Direction / Development</p>
    <h1>廣川 貴理</h1>
    <p>「何を作るか」からではなく、<br/>「何を解決したいか」から考えます。</p>
  </div>
  <ScrollIndicator />   ← animated arrow/line at bottom
</section>
```

MouseGradient: `useMotionValue` + `useSpring` (stiffness: 80, damping: 20) for x/y, rendered as a `motion.div` with radial-gradient background using `accent` color at ~8% opacity. Use `style={{ x, y }}` with `transform` — never `top`/`left`.

Review Focus test — use `transform: translate()` not position for the gradient div. Add a comment asserting this.

Content reveal: `motion.div` with `initial={{ opacity: 0, y: 30 }}` and `animate={{ opacity: 1, y: 0 }}`, stagger children by 0.15s using `variants`.

- [ ] **Step 2: Add Hero to `app/page.tsx`**

```tsx
import Hero from "@/components/sections/Hero"
export default function Home() {
  return <main><Hero /></main>
}
```

- [ ] **Step 3: Verify Hero renders and mouse gradient tracks**

```bash
npm run dev
```
Expected: full-viewport hero, gradient follows mouse smoothly, text fades in on load.

- [ ] **Step 4: Commit**

```bash
git add components/sections/Hero.tsx app/page.tsx
git commit -m "feat: add Hero section with mouse-tracking gradient"
```

---

## Task 5: About Section

**Files:**
- Create: `components/sections/About.tsx`
- Modify: `app/page.tsx`

**Interfaces:**
- Consumes: CSS variables
- Produces: `<About id="about">` — used in `app/page.tsx`

- [ ] **Step 1: Create `components/sections/About.tsx`**

Server Component (no interactivity needed; wrap animated children in a `"use client"` sub-component if needed). Section label `[01] About`. Three subsections:

**Profile block:**
- Name: 廣川 貴理 (Takatoshi Hirokawa)
- Profile text: 山梨県・河口湖を拠点に、企業やサービスのWeb・デジタル課題を支援。サイト、アプリ、SNS、広告、採用コンテンツ、業務効率化、AI活用など、企画から制作・開発まで一貫して対応。

**Field tags** (pill/badge style with accent border):
- Web・デジタル企画 / Webサイト / LP制作 / Webアプリ / サービス開発 / SNS / 広告施策 / 採用コンテンツ / AI活用 / DX支援 / プロジェクトマネジメント

**Tools:**
- Design: XD / Illustrator / Photoshop
- Development: Bubble / Studio / Dify

Animation: `whileInView={{ opacity: 1, y: 0 }}` from `{ opacity: 0, y: 40 }` with `once: true`, `margin: "-100px"`.

Review Focus test — `once: true` on viewport trigger prevents re-firing on scroll back up; add this as an inline comment on the `viewport` prop.

- [ ] **Step 2: Add About to `app/page.tsx`**

Add `<About />` after `<Hero />` with `id="about"`.

- [ ] **Step 3: Verify section fades in on scroll**

```bash
npm run dev
```
Expected: About section fades up when scrolled into view, does not re-animate on scroll back.

- [ ] **Step 4: Commit**

```bash
git add components/sections/About.tsx app/page.tsx
git commit -m "feat: add About section with scroll-triggered animation"
```

---

## Task 6: Works Section

**Files:**
- Create: `components/sections/Works.tsx`
- Modify: `app/page.tsx`

**Interfaces:**
- Consumes: `Work`, `works` from `lib/works.ts`
- Produces: `<Works id="works">` — used in `app/page.tsx`

- [ ] **Step 1: Create `components/sections/Works.tsx`**

`"use client"` component. Section label `[02] Works`. Import `works` from `lib/works.ts`.

Render a CSS grid (2 cols on md+, 1 col on mobile). Each work renders as a card:

```
<motion.article
  whileHover={{ y: -6, rotateX: 2, rotateY: -2 }}
  style={{ transformStyle: "preserve-3d", perspective: 1000 }}
  onHoverStart / onHoverEnd   ← tilt only on hover, NOT on focus
>
  <div className="aspect-video bg-[var(--muted)]" />  ← thumbnail placeholder
  <h3>{work.title}</h3>
  <p>{work.year}</p>
  <ul>{work.tags.map(tag => <li key={tag}>{tag}</li>)}</ul>
</motion.article>
```

Each card wraps in `<Link href={`/works/${work.slug}`}>`. Cards animate with `whileInView` staggered (0.1s per card).

Review Focus test: `onHoverStart` sets tilt state, `onHoverEnd` resets. Keyboard focus (`:focus-visible`) does NOT trigger tilt. Add a comment on the event handlers.

- [ ] **Step 2: Add Works to `app/page.tsx`**

Add `<Works />` after `<About />`.

- [ ] **Step 3: Verify grid and card hover**

```bash
npm run dev
```
Expected: 2-column grid on desktop, cards lift on hover, no tilt on Tab-focus.

- [ ] **Step 4: Commit**

```bash
git add components/sections/Works.tsx app/page.tsx
git commit -m "feat: add Works section with animated cards"
```

---

## Task 7: Topics + Contact Sections

**Files:**
- Create: `components/sections/Topics.tsx`
- Create: `components/sections/Contact.tsx`
- Modify: `app/page.tsx`

**Interfaces:**
- Produces: `<Topics id="topics">`, `<Contact id="contact">` — used in `app/page.tsx`

- [ ] **Step 1: Create `components/sections/Topics.tsx`**

Server Component. Section label `[03] Topics`. Render empty state: `<p>No Contents</p>` in muted color. No animation needed.

- [ ] **Step 2: Create `components/sections/Contact.tsx`**

`"use client"` component. Section label `[04] Contact`.

Form fields (controlled with `useState`):
- 姓 / 名 (text inputs, side by side)
- セイ / メイ (furigana, side by side)  
- メールアドレス (email input)
- お問い合わせ種別 (select: 新規制作 / リニューアル・改善 / 運用・保守 / その他)
- お問い合わせ内容 (textarea)
- プライバシーポリシー同意チェックボックス (links to `/privacy-policy`)
- Submit button

On submit: `e.preventDefault()`, set `submitted = true`, show static thank-you message "送信しました。3営業日以内にご返信いたします。". No backend in Phase 1.

Review Focus test: `e.preventDefault()` in `handleSubmit` — add a comment that backend integration is Phase 3.

SNS block: LINE / Instagram / X の DM誘導テキスト + icon placeholders.

- [ ] **Step 3: Add both sections to `app/page.tsx`**

```tsx
<Topics />
<Contact />
```

- [ ] **Step 4: Verify form behavior**

```bash
npm run dev
```
Expected: form renders, submitting shows thank-you message without page reload, no console errors.

- [ ] **Step 5: Commit**

```bash
git add components/sections/Topics.tsx components/sections/Contact.tsx app/page.tsx
git commit -m "feat: add Topics (empty) and Contact sections"
```

---

## Task 8: Work Detail Page

**Files:**
- Create: `app/works/[slug]/page.tsx`
- Create: `app/privacy-policy/page.tsx`

**Interfaces:**
- Consumes: `works` from `lib/works.ts` (for `generateStaticParams`)
- Produces: static work detail pages + privacy policy stub

- [ ] **Step 1: Create `app/works/[slug]/page.tsx`**

Server Component. Use `generateStaticParams` returning all slugs from `works`. Find work by slug; return 404 (`notFound()`) if not found. Render:
- Back link: `← Works`
- Work title, year, tags
- Thumbnail placeholder (`aspect-video bg-[var(--muted)]`)
- Description paragraph
- Note: "詳細コンテンツはPhase 2で追加予定"

- [ ] **Step 2: Create `app/privacy-policy/page.tsx`**

Server Component. Render a stub: heading "プライバシーポリシー" and paragraph "準備中です。"

- [ ] **Step 3: Run build to verify static generation**

```bash
npm run build
```
Expected: 6 `/works/[slug]` pages pre-rendered, no TypeScript errors, no build errors.

- [ ] **Step 4: Commit**

```bash
git add app/works/ app/privacy-policy/
git commit -m "feat: add work detail pages and privacy policy stub"
```

---

## Task 9: Responsive Polish + Final Push

**Files:**
- Modify: all section components (responsive audit)
- Modify: `components/layout/Header.tsx` (mobile menu final check)

**Interfaces:**
- Consumes: all section components
- Produces: deployable build

- [ ] **Step 1: Responsive audit**

Check each section at 375px (mobile) and 768px (tablet) in browser DevTools:
- Hero: text wraps correctly, no overflow
- About: tags wrap, no horizontal scroll
- Works: 1 column on mobile, 2 on md
- Contact: form inputs full-width on mobile
- Header: hamburger visible on mobile, desktop nav visible on lg+

Fix any issues found.

- [ ] **Step 2: Run final build**

```bash
npm run build
```
Expected: clean build, no errors, no TypeScript errors.

- [ ] **Step 3: Commit and push**

```bash
git add -A
git commit -m "feat: responsive polish — Phase 1 frontend complete"
git push origin main
```

- [ ] **Step 4: Open PR on GitHub**

Create a draft pull request on `takatoshihirokawa/portfolio` from `main` (or a feature branch if used).
