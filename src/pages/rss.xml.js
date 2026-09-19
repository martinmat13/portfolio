import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export async function GET(context) {
  // Pull all your stories
  const stories = await getCollection('stories');
  
  return rss({
    title: 'Martin Mathew | Field Notes',
    description: 'Engineering reflections and transit stories.',
    // This pulls the URL you set in step 1!
    site: context.site, 
    items: stories.map((story) => ({
      title: story.data.title,
      pubDate: story.data.date,
      description: story.data.summary,
      link: `/stories/${story.slug}/`,
    })),
    customData: `<language>en-us</language>`,
  });
}