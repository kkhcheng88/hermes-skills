/**
 * YouTube Search Script
 * 
 * Searches YouTube for videos and returns results sorted by view count.
 * Uses Puppeteer to connect to Chrome debugging port 9222.
 * 
 * Usage:
 *   1. Edit SEARCH_QUERIES and OUTPUT_FILE below
 *   2. Start Chrome: start_chrome.bat (Windows) or start_chrome.sh (Mac/Linux)
 *   3. Run: node search_youtube.js
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

// ============================================================
// CONFIGURATION - Edit these values for your search
// ============================================================

const SEARCH_QUERIES = [
  // Test: Search for Warren Buffett (sorted by view count)
  { url: 'https://www.youtube.com/results?search_query=Warren+Buffett&sp=CAM%253D', label: 'Warren Buffett (by view count)' },
];

// Output file path (relative to project root)
const OUTPUT_FILE = 'search_results.json';

// Maximum number of results per search query
const MAX_RESULTS = 30;

// Number of times to scroll down to load more results
const SCROLL_ITERATIONS = 8;

// ============================================================

const CHROME_DEBUG_URL = 'http://127.0.0.1:9222';

async function extractSearchResults(page) {
  // Wait for results to load
  await new Promise(r => setTimeout(r, 4000));

  // Scroll down to load more results
  for (let i = 0; i < SCROLL_ITERATIONS; i++) {
    await page.evaluate(() => window.scrollBy(0, 800));
    await new Promise(r => setTimeout(r, 1200));
  }

  // Scroll back to top then down again for lazy-loaded content
  await page.evaluate(() => window.scrollTo(0, 0));
  await new Promise(r => setTimeout(r, 1000));
  for (let i = 0; i < 3; i++) {
    await page.evaluate(() => window.scrollBy(0, 1500));
    await new Promise(r => setTimeout(r, 1000));
  }

  // Extract video information
  const results = await page.evaluate(() => {
    const videos = [];
    const seen = new Set();
    
    const videoElements = document.querySelectorAll('ytd-video-renderer');

    for (const el of videoElements) {
      try {
        // Get video ID and title from the title link
        const titleLink = el.querySelector('a#video-title');
        if (!titleLink) continue;
        
        const href = titleLink.getAttribute('href') || '';
        const videoIdMatch = href.match(/[?&]v=([a-zA-Z0-9_-]{11})/);
        const videoId = videoIdMatch ? videoIdMatch[1] : null;
        if (!videoId || seen.has(videoId)) continue;
        seen.add(videoId);

        // Use the title attribute which is cleaner than textContent
        const title = titleLink.getAttribute('title') || titleLink.textContent?.trim() || '';

        // Get metadata from the metadata line
        const metaSpans = el.querySelectorAll('#metadata-line span');
        let viewCount = '';
        let uploadDate = '';
        
        for (const span of metaSpans) {
          const text = span.textContent.trim();
          if (text.match(/\d.*view/i) || text.match(/\d.*次觀看/) || text.match(/\d.*觀看/)) {
            viewCount = text;
          } else if (text.match(/ago|前|year|month|week|day|hour/i)) {
            uploadDate = text;
          }
        }

        // Get channel name
        const channelLink = el.querySelector('ytd-channel-name a');
        const channel = channelLink?.textContent?.trim() || '';

        // Get duration
        const durationEl = el.querySelector('#time-status span, .ytd-thumbnail-overlay-time-status-renderer span, span.style-scope.ytd-thumbnail-overlay-time-status-renderer');
        const duration = durationEl?.textContent?.trim() || '';

        // Get description snippet
        const descEl = el.querySelector('#description-text');
        const description = descEl?.textContent?.trim() || '';

        videos.push({
          videoId,
          title,
          viewCount,
          uploadDate,
          channel,
          duration,
          description,
          url: `https://www.youtube.com/watch?v=${videoId}`
        });
      } catch (e) {
        // Skip elements that fail to parse
      }
    }

    return videos;
  });

  return results.slice(0, MAX_RESULTS);
}

async function main() {
  console.log('Connecting to Chrome on port 9222...');
  
  let browser;
  try {
    browser = await puppeteer.connect({
      browserURL: CHROME_DEBUG_URL,
      defaultViewport: null
    });
  } catch (err) {
    console.error('Failed to connect to Chrome. Make sure Chrome is running with debugging port 9222.');
    console.error('Run start_chrome.bat (Windows) or start_chrome.sh (Mac/Linux) first.');
    console.error('Error:', err.message);
    process.exit(1);
  }

  const page = await browser.newPage();
  const allResults = [];
  const seenIds = new Set();

  for (const query of SEARCH_QUERIES) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`Searching: ${query.label}`);
    console.log(`URL: ${query.url}`);
    console.log(`${'='.repeat(60)}`);

    try {
      await page.goto(query.url, { waitUntil: 'networkidle2', timeout: 30000 });
      const results = await extractSearchResults(page);
      
      console.log(`Found ${results.length} videos`);
      
      // Deduplicate across queries
      for (const video of results) {
        if (!seenIds.has(video.videoId)) {
          seenIds.add(video.videoId);
          allResults.push({ ...video, searchQuery: query.label });
        }
      }
    } catch (err) {
      console.error(`Error searching "${query.label}": ${err.message}`);
    }

    // Delay between searches
    console.log('Waiting 3 seconds before next search...');
    await new Promise(r => setTimeout(r, 3000));
  }

  await page.close();
  browser.disconnect();

  // Save results
  const outputDir = path.dirname(OUTPUT_FILE);
  if (outputDir && !fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(allResults, null, 2));
  console.log(`\n${'='.repeat(60)}`);
  console.log(`RESULTS SUMMARY`);
  console.log(`${'='.repeat(60)}`);
  console.log(`Total unique videos found: ${allResults.length}`);
  console.log(`Saved to: ${OUTPUT_FILE}`);
  
  // Print top results
  console.log('\nTop 10 results:');
  allResults.slice(0, 10).forEach((v, i) => {
    console.log(`  ${i + 1}. [${v.videoId}] ${v.title} (${v.viewCount})`);
  });
}

main().catch(console.error);
