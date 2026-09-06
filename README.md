# martin.sim — portfolio

A CFD / numerical-simulation focused portfolio with a storytelling section
for everything else. Built with **Astro + Tailwind CSS**, content-driven
via **Markdown/MDX collections** so new work ships without touching any UI
code.

## Stack

- **Astro** (static output) — fast, ships zero JS by default
- **Tailwind CSS** — utility styling, custom CFD-themed design tokens in `tailwind.config.mjs`
- **MDX** — project/story bodies, with `remark-math` + `rehype-katex` for LaTeX equations
- **Content Collections** (`astro:content`) — schema-validated frontmatter for projects, collaborations, and stories

## Local development

```bash
npm install
npm run dev       # http://localhost:4321
npm run build     # outputs to dist/
npm run preview   # preview the production build locally
```

## Project structure

```
src/
  components/         # reusable UI: Header, Footer, Hero, ProjectRow,
                       # TechBadge, EquationBlock, Gallery, YouTubeEmbed, HUDPanel
  content/
    config.ts          # schemas for projects / collaborations / stories
    projects/*.mdx      # ← add a new CFD project here
    collaborations/*.mdx
    stories/*.mdx
  layouts/
    BaseLayout.astro    # head, nav, footer — wraps every page
    ProjectLayout.astro # the reusable CFD project template
  pages/
    index.astro
    projects/index.astro
    projects/[slug].astro   # auto-generates a page per project file
    collaborations/index.astro
    stories/index.astro
    about.astro
  styles/global.css
public/
  cv/martin-cv.pdf     # ← replace with your real CV, same filename
  images/
```

## Adding a new CFD project (no code changes needed)

Create a new file in `src/content/projects/`, e.g. `my-new-study.mdx`:

```mdx
---
title: "My New Study"
summary: "One or two sentences — shows up in the project list."
stack: ["OpenFOAM", "Python"]
tags: ["turbulence", "y+"]
solver: "simpleFoam"
status: "ongoing"        # ongoing | complete | archived
date: 2026-06-01
metrics:
  - { label: "Re", value: "1.0 × 10⁶" }
featured: true            # shows on the homepage
order: 4                  # lower sorts first
# coverImage: "./images/cover.png"   # relative to this file
# gallery:
#   - "./images/1.png"
---

## Methodology

Write your methodology, using `$$ ... $$` for LaTeX display equations
and `$...$` for inline math, exactly as in the existing sample projects.
```

That's it — `/projects` and `/projects/my-new-study` both update
automatically, using the shared `ProjectLayout.astro` template (title, tech
stack pills, metrics/HUD strip, cover image, prose body with equations,
gallery, and tags are all handled for you).

The same pattern applies to `src/content/collaborations/` and
`src/content/stories/` — check the existing sample files for the exact
frontmatter shape (also enforced by Zod in `src/content/config.ts`, so a
typo'd field will fail the build with a clear error rather than silently
breaking the page).

## Images

Put images next to their MDX file (or in `public/images/`) and reference
them as `coverImage` / `gallery` in frontmatter — Astro's `image()` schema
helper handles optimisation and responsive `srcset` generation
automatically via the `<Image />` component already wired into
`ProjectLayout.astro` and `Gallery.astro`.

## Before you deploy

- [ ] Replace social links in `src/components/Footer.astro` and `src/pages/about.astro`
- [ ] Replace `public/cv/PLACEHOLDER.txt` with your real `martin-cv.pdf`
- [ ] Update `site:` in `astro.config.mjs` to your real domain/subdomain
- [ ] Swap the placeholder YouTube ID in the sample story for a real video
- [ ] Update the bio text in `src/pages/about.astro`

## Deploying (GitHub → Vercel/Netlify)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial portfolio scaffold"
   gh repo create your-username/portfolio --public --source=. --push
   # or: create the repo on github.com, then
   # git remote add origin https://github.com/your-username/portfolio.git
   # git push -u origin main
   ```

2. **Connect to Vercel** (or Netlify)
   - Go to vercel.com → **Add New Project** → import the GitHub repo
   - Framework preset: **Astro** (auto-detected)
   - Build command: `npm run build` · Output directory: `dist`
   - Deploy — you'll get a free `your-project.vercel.app` URL immediately

3. **Every future push to `main` auto-deploys.** Adding a new project is
   then just: drop an `.mdx` file → `git add` → `git commit` → `git push`.

4. **Custom domain later**: Vercel/Netlify project settings → Domains →
   add your domain and update the DNS records they give you. No code
   changes needed.
