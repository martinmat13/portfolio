import { defineCollection, z } from "astro:content";

// -----------------------------------------------------------------------
// CFD / RESEARCH PROJECTS
// Drop a new .mdx file into src/content/projects/ and it appears
// automatically in the grid + gets its own page via [slug].astro.
// No component code needs to change.
// -----------------------------------------------------------------------
const projects = defineCollection({
  type: "content",
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      summary: z.string().max(220),
      // Shown as monospace pills, e.g. ["OpenFOAM", "C++", "Python", "Bash"]
      stack: z.array(z.string()),
      // Free-form tags for filtering, e.g. ["turbulence", "LES", "y+"]
      tags: z.array(z.string()).default([]),
      solver: z.string().optional(), // e.g. "simpleFoam", "LIGGGHTS-DEM"
      status: z.enum(["ongoing", "complete", "archived"]).default("complete"),
      date: z.coerce.date(),
      // Small numeric readouts shown in the HUD strip on the project page
      // e.g. [{ label: "Re", value: "4.2e5" }, { label: "Cells", value: "2.1M" }]
      metrics: z
        .array(z.object({ label: z.string(), value: z.string() }))
        .default([]),
      coverImage: image().optional(),
      gallery: z.array(image()).default([]),
      repoUrl: z.string().url().optional(),
      paperUrl: z.string().url().optional(),
      featured: z.boolean().default(false),
      order: z.number().default(99),
    }),
});

// -----------------------------------------------------------------------
// COLLABORATIONS — academic / professional work outside core CFD focus
// -----------------------------------------------------------------------
const collaborations = defineCollection({
  type: "content",
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      partner: z.string(), // institution / company / collaborator name
      role: z.string(), // your role in the collaboration
      summary: z.string().max(240),
      period: z.string(), // e.g. "2024 – present"
      date: z.coerce.date(),
      tags: z.array(z.string()).default([]),
      logo: image().optional(),
      coverImage: image().optional(),
      link: z.string().url().optional(),
      order: z.number().default(99),
    }),
});

// -----------------------------------------------------------------------
// STORIES — blog / vlog: trainspotting, humour, photography, narrative
// -----------------------------------------------------------------------
const stories = defineCollection({
  type: "content",
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      kind: z.enum([
                    "writing", 
                    "video", 
                    "photo", 
                    "gallery", 
                    "tutorial", 
                    "guide", 
                    "presentation", 
                    "travelogue", 
                    "journal", 
                    "reflection"
                  ]),
      summary: z.string().max(220),
      date: z.coerce.date(),
      youtubeId: z.string().optional(), // required when kind === "video"
      coverImage: image().optional(),
      gallery: z.array(image()).default([]),
      tags: z.array(z.string()).default([]),
    }),
});

export const collections = { projects, collaborations, stories };
