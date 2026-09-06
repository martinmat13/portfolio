import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

// ---------------------------------------------------------------------------
// Update `site` before deploying — Vercel/Netlify need it for the sitemap
// and for absolute OpenGraph URLs to resolve correctly.
// ---------------------------------------------------------------------------
export default defineConfig({
  site: "https://your-domain-or-vercel-subdomain.vercel.app",
  integrations: [
    tailwind({ applyBaseStyles: false }),
    mdx(),
    sitemap(),
  ],
  markdown: {
    remarkPlugins: [remarkMath],
    rehypePlugins: [rehypeKatex],
    shikiConfig: {
      theme: "github-dark-dimmed",
    },
  },
});
