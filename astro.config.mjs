import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import vercel from "@astrojs/vercel/serverless";

// ---------------------------------------------------------------------------
// Update `site` before deploying — Vercel/Netlify need it for the sitemap
// and for absolute OpenGraph URLs to resolve correctly.
// ---------------------------------------------------------------------------
export default defineConfig({
  site: "https://portfolio-martin-mathew.vercel.app",
  output: "server",
  adapter: vercel({
    webAnalytics: { enabled: true },
  }),
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
