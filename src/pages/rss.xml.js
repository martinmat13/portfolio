import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export async function GET(context) {
  // 1. Get all your stories
  const stories = await getCollection('stories');
  
  // 2. Sort them from newest to oldest
  const sortedStories = stories.sort(
    (a, b) => b.data.date.valueOf() - a.data.date.valueOf()
  );

  // 3. Generate the XML feed
  return rss({
    title: 'Martin Mathew | Field Notes',
    description: 'Travelogues, engineering reflections, and adventures beyond the computational mesh.',
    // context.site automatically pulls the URL you set in Step 1
    site: context.site, 
    // Map your stories to the RSS format
    items: sortedStories.map((story) => ({
      title: story.data.title,
      pubDate: story.data.date,
      description: story.data.summary,
      link: `/stories/${story.slug}/`,
    })),
    // Standard RSS language tag
    customData: `<language>en-us</language>`,
  });
}