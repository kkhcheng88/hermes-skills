/**
 * Batch YouTube Transcript Extractor Template
 * 
 * This template demonstrates how to extract transcripts for multiple investors
 * or search queries in a single run. Customize the INVESTORS config below.
 * 
 * Usage:
 *   1. Edit INVESTORS array with your target investors/people
 *   2. Start Chrome: start_chrome.bat (Windows) or start_chrome.sh (Mac/Linux)
 *   3. Run: node batch_extract_template.js
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

// ============================================================
// CONFIGURATION - Customize for your batch extraction
// ============================================================

const INVESTORS = [
  {
    name: 'Howard Marks',
    searchQueries: [
      'Howard Marks interview',
      'Howard Marks Oaktree',
      'Howard Marks memo',
    ],
    // Known high-quality videos (optional - will be prioritized)
    knownVideos: [
      // { id: 'VIDEO_ID', name: 'output_filename', title: 'Video Title', category: 'primary' },
    ],
    outputDir: 'transcripts/howard-marks/',
  },
  // Add more investors as needed
  // {
  //   name: 'Seth Klarman',
  //   searchQueries: ['Seth Klarman interview', 'Seth Klarman Baupost'],
  //   knownVideos: [],
  //   outputDir: 'transcripts/seth-klarman/',
  // },
];

// Global settings
const CHROME_DEBUG_URL = 'http://127.0.0.1:9222';
const DELAY_BETWEEN_VIDEOS = 5000;
const MAX_TRANSCRIPT_WAIT = 25;
const MAX_SEARCH_RESULTS = 10; // Max videos to extract per investor

// ============================================================

// Helper: Build YouTube search URL (sorted by view count)
function buildSearchUrl(query) {
  const encoded = encodeURIComponent(query);
  return `https://www.youtube.com/results?search_query=${encoded}&sp=CAM%253D`;
}

// Helper: Extract search results from page
async function extractSearchResults(page, maxResults = 20) {
  await new Promise(r => setTimeout(r, 4000));

  for (let i = 0; i < 6; i++) {
    await page.evaluate(() => window.scrollBy(0, 800));
    await new Promise(r => setTimeout(r, 1000));
  }

  const results = await page.evaluate(() => {
    const videos = [];
    const seen = new Set();
    const videoElements = document.querySelectorAll('ytd-video-renderer');

    for (const el of videoElements) {
      try {
        const titleLink = el.querySelector('a#video-title');
        if (!titleLink) continue;
        
        const href = titleLink.getAttribute('href') || '';
        const videoIdMatch = href.match(/[?&]v=([a-zA-Z0-9_-]{11})/);
        const videoId = videoIdMatch ? videoIdMatch[1] : null;
        if (!videoId || seen.has(videoId)) continue;
        seen.add(videoId);

        const title = titleLink.getAttribute('title') || titleLink.textContent?.trim() || '';
        const durationEl = el.querySelector('#time-status span, .ytd-thumbnail-overlay-time-status-renderer span');
        const duration = durationEl?.textContent?.trim() || '';

        videos.push({ videoId, title, duration });
      } catch (e) {}
    }

    return videos;
  });

  return results.slice(0, maxResults);
}

// Helper: Extract transcript from video page
async function extractTranscriptFromPage(page, videoId, videoName, videoTitle) {
  const url = `https://www.youtube.com/watch?v=${videoId}`;
  console.log(`  Processing: ${videoTitle}`);

  try {
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
    await new Promise(r => setTimeout(r, 5000));

    // Click transcript button
    await page.evaluate(() => {
      const buttons = document.querySelectorAll('button');
      for (const btn of buttons) {
        const text = btn.textContent.trim();
        if (text.includes('顯示轉錄稿') || text.includes('Show transcript') || text.includes('Transcript')) {
          btn.click();
          break;
        }
      }
    });

    // Wait for transcript
    for (let i = 0; i < MAX_TRANSCRIPT_WAIT; i++) {
      await new Promise(r => setTimeout(r, 1000));
      const ready = await page.evaluate(() => {
        const panel = document.querySelector('ytd-engagement-panel-section-list-renderer[visibility="ENGAGEMENT_PANEL_VISIBILITY_EXPANDED"]');
        if (!panel) return false;
        const segments = panel.querySelectorAll('ytd-transcript-segment-renderer, transcript-segment-view-model');
        return segments.length > 0;
      });
      if (ready) break;
    }

    // Scroll to load all
    await page.evaluate(() => {
      const panel = document.querySelector('ytd-engagement-panel-section-list-renderer[visibility="ENGAGEMENT_PANEL_VISIBILITY_EXPANDED"]');
      if (panel) {
        const scroller = panel.querySelector('#scroll-container') || panel;
        scroller.scrollTop = scroller.scrollHeight;
      }
    });
    await new Promise(r => setTimeout(r, 2000));

    // Extract content
    const transcript = await page.evaluate(() => {
      const panel = document.querySelector('ytd-engagement-panel-section-list-renderer[visibility="ENGAGEMENT_PANEL_VISIBILITY_EXPANDED"]');
      if (!panel) return { method: 'none', content: '' };

      // Try multiple methods
      const segments1 = panel.querySelectorAll('ytd-transcript-segment-renderer');
      if (segments1.length > 0) {
        const lines = [];
        for (const seg of segments1) {
          const ts = seg.querySelector('.timestamp')?.textContent?.trim() || '';
          const text = seg.querySelector('#content, .segment-text')?.textContent?.trim() || '';
          if (text) lines.push('[' + ts + '] ' + text);
        }
        if (lines.length > 0) return { method: 'segments', content: lines.join('\n'), count: lines.length };
      }

      const segments2 = panel.querySelectorAll('transcript-segment-view-model');
      if (segments2.length > 0) {
        const lines = [];
        for (const seg of segments2) {
          const text = seg.textContent?.trim() || '';
          if (text) lines.push(text);
        }
        if (lines.length > 0) return { method: 'view-model', content: lines.join('\n'), count: lines.length };
      }

      const body = panel.querySelector('ytd-transcript-body-renderer');
      if (body && body.innerText.trim().length > 20) {
        return { method: 'body', content: body.innerText.trim(), count: body.innerText.split('\n').length };
      }

      return { method: 'none', content: '' };
    });

    if (transcript.content && transcript.content.length > 50) {
      return { success: true, content: transcript.content, method: transcript.method, count: transcript.count };
    }
    return { success: false, error: 'No transcript' };

  } catch (error) {
    return { success: false, error: error.message };
  }
}

// Helper: Sanitize filename
function sanitizeFilename(name) {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
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
    console.error('Failed to connect to Chrome. Run start_chrome.bat or start_chrome.sh first.');
    process.exit(1);
  }

  const page = await browser.newPage();
  const allResults = {};

  for (const investor of INVESTORS) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`Processing: ${investor.name}`);
    console.log(`${'='.repeat(60)}`);

    // Create output directory
    if (!fs.existsSync(investor.outputDir)) {
      fs.mkdirSync(investor.outputDir, { recursive: true });
    }

    const videosToProcess = [...investor.knownVideos];
    const processedIds = new Set(videosToProcess.map(v => v.id));

    // Search for additional videos
    for (const query of investor.searchQueries) {
      console.log(`\nSearching: "${query}"`);
      const searchUrl = buildSearchUrl(query);
      
      try {
        await page.goto(searchUrl, { waitUntil: 'networkidle2', timeout: 30000 });
        const results = await extractSearchResults(page, MAX_SEARCH_RESULTS);
        
        for (const v of results) {
          if (!processedIds.has(v.videoId)) {
            processedIds.add(v.videoId);
            videosToProcess.push({
              id: v.videoId,
              name: sanitizeFilename(v.title),
              title: v.title,
              category: 'search'
            });
          }
        }
        console.log(`  Found ${results.length} videos`);
      } catch (err) {
        console.error(`  Search error: ${err.message}`);
      }
      
      await new Promise(r => setTimeout(r, 3000));
    }

    // Extract transcripts
    console.log(`\nExtracting transcripts for ${videosToProcess.length} videos...`);
    const investorResults = [];

    for (const video of videosToProcess) {
      const result = await extractTranscriptFromPage(page, video.id, video.name, video.title);
      
      if (result.success) {
        const outputPath = path.join(investor.outputDir, `${video.name}_transcript.txt`);
        const header = `# YouTube Transcript\n# Title: ${video.title}\n# URL: https://www.youtube.com/watch?v=${video.id}\n# Extracted: ${new Date().toISOString()}\n\n`;
        fs.writeFileSync(outputPath, header + result.content);
        console.log(`    ✓ Saved: ${video.name} (${result.count} segments)`);
      } else {
        console.log(`    ✗ No transcript: ${video.name}`);
      }
      
      investorResults.push({ ...video, ...result });
      await new Promise(r => setTimeout(r, DELAY_BETWEEN_VIDEOS));
    }

    allResults[investor.name] = investorResults;
  }

  await page.close();
  browser.disconnect();

  // Final summary
  console.log(`\n${'='.repeat(60)}`);
  console.log('BATCH EXTRACTION COMPLETE');
  console.log('='.repeat(60));
  
  for (const [name, results] of Object.entries(allResults)) {
    const successful = results.filter(r => r.success).length;
    console.log(`${name}: ${successful}/${results.length} transcripts extracted`);
  }
}

main().catch(console.error);
