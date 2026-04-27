/**
 * YouTube Transcript Extractor
 * 
 * Extracts transcripts from YouTube videos using Puppeteer.
 * Connects to Chrome debugging port 9222.
 * 
 * Usage:
 *   1. Edit the `videos` array below with your target videos
 *   2. Start Chrome: start_chrome.bat (Windows) or start_chrome.sh (Mac/Linux)
 *   3. Run: node extract_transcript.js
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

// ============================================================
// CONFIGURATION - Edit these values for your extraction
// ============================================================

const videos = [
  // Test video - Marty Whitman WealthTrack interview (previously verified working)
  { id: '9A7SNC-gFGI', name: 'whitman_wealthtrack_test', title: 'Marty Whitman WealthTrack Interview Test' },
];

// Output directory for transcript files (relative to project root)
const OUTPUT_DIR = 'transcripts/';

// Delay between videos in milliseconds (avoid rate limiting)
const DELAY_BETWEEN_VIDEOS = 5000;

// Maximum wait time for transcript panel to load (in seconds)
const MAX_TRANSCRIPT_WAIT = 25;

// ============================================================

const CHROME_DEBUG_URL = 'http://127.0.0.1:9222';

/**
 * Find and click transcript button using multiple methods
 * Returns true if successful, false otherwise
 */
async function findAndClickTranscriptButton(page) {
  console.log('Step 1: Looking for "...more" button in video description...');
  
  // Step 1: 先點擊「...更多」按鈕展開描述
  const moreButtonSelectors = [
    'button[aria-label*="更多" i]',
    'button[aria-label*="more" i]',
    'button[aria-label*="Expand" i]',
    'button[aria-label*="展開" i]',
    '#description-inline-expander button#expand',
    'ytd-text-inline-expander #expand',
    'ytd-text-inline-expander button',
    '#description-inner #expand',
  ];
  
  let moreClicked = false;
  for (const selector of moreButtonSelectors) {
    try {
      const button = await page.$(selector);
      if (button) {
        const isVisible = await page.evaluate(el => {
          const rect = el.getBoundingClientRect();
          return rect.width > 0 && rect.height > 0;
        }, button);
        if (isVisible) {
          console.log(`Found "more" button with selector: ${selector}`);
          await button.click();
          moreClicked = true;
          await page.waitForTimeout(2000); // 等待描述展開
          break;
        }
      }
    } catch (e) {
      // 繼續嘗試
    }
  }
  
  if (!moreClicked) {
    // 嘗試用文字搜尋
    const allButtons = await page.$$('button');
    for (const btn of allButtons) {
      const text = await page.evaluate(el => {
        return (el.textContent || '').trim() + ' ' + (el.getAttribute('aria-label') || '');
      }, btn);
      if (text.includes('...更多') || text.includes('更多') ||
          text.toLowerCase().includes('more') || text.toLowerCase().includes('expand')) {
        console.log(`Found "more" button by text: ${text.substring(0, 50)}`);
        await btn.click();
        moreClicked = true;
        await page.waitForTimeout(2000);
        break;
      }
    }
  }
  
  console.log(`Description expanded: ${moreClicked}`);
  
  // Step 2: 找「顯示轉錄文字」按鈕
  console.log('Step 2: Looking for "Show transcript" button...');
  
  const transcriptSelectors = [
    'button[aria-label*="轉錄文字"]',
    'button[aria-label*="轉錄稿"]',
    'button[aria-label*="transcript" i]',
    'button[aria-label*="Show transcript"]',
    'yt-button-shape[aria-label*="轉錄文字"]',
    'yt-button-shape[aria-label*="transcript" i]',
  ];
  
  for (const selector of transcriptSelectors) {
    try {
      const button = await page.$(selector);
      if (button) {
        console.log(`Found transcript button with selector: ${selector}`);
        await button.click();
        return true;
      }
    } catch (e) {
      // 繼續嘗試
    }
  }
  
  // 用文字搜尋
  const allButtons2 = await page.$$('button, yt-button-shape');
  for (const btn of allButtons2) {
    try {
      const text = await page.evaluate(el => {
        return (el.textContent || '') + ' ' + (el.getAttribute('aria-label') || '');
      }, btn);
      if (text.includes('轉錄文字') || text.includes('轉錄稿') ||
          text.toLowerCase().includes('transcript') || text.includes('顯示轉錄')) {
        console.log(`Found transcript button by text: ${text.substring(0, 50)}`);
        await btn.click();
        return true;
      }
    } catch (e) {
      // 繼續
    }
  }
  
  console.log('Could not find transcript button');
  return false;
}

/**
 * Check if transcript panel is open and ready
 */
async function isTranscriptPanelReady(page) {
  return await page.evaluate(() => {
    const panel = document.querySelector('ytd-engagement-panel-section-list-renderer[visibility="ENGAGEMENT_PANEL_VISIBILITY_EXPANDED"]');
    if (!panel) return { ready: false, reason: 'no_panel' };
    
    const segments = panel.querySelectorAll('ytd-transcript-segment-renderer, transcript-segment-view-model');
    const cueSegments = panel.querySelectorAll('ytd-transcript-body-renderer .cue');
    const spinner = panel.querySelector('tp-yt-paper-spinner[active]');
    
    if (spinner) return { ready: false, reason: 'loading' };
    if (segments.length > 0) return { ready: true, reason: 'segments_found', count: segments.length };
    if (cueSegments.length > 0) return { ready: true, reason: 'cues_found', count: cueSegments.length };
    
    // Check if panel has meaningful text content
    const panelText = panel.innerText.trim();
    if (panelText.length > 100) return { ready: true, reason: 'text_content', count: panelText.split('\n').length };
    
    return { ready: false, reason: 'empty' };
  });
}

async function extractTranscriptFromPage(page, videoId, videoName, videoTitle) {
  const url = `https://www.youtube.com/watch?v=${videoId}`;
  console.log(`\n${'='.repeat(60)}`);
  console.log(`Processing: ${videoTitle}`);
  console.log(`URL: ${url}`);
  console.log(`${'='.repeat(60)}`);

  try {
    // Navigate to video
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
    console.log('Page loaded, waiting for content...');
    
    // Wait for video info to load (indicates page is ready)
    await page.waitForSelector('ytd-video-primary-info-renderer, #top-row', { timeout: 15000 }).catch(() => {
      console.log('Warning: Video info selector timeout, continuing anyway...');
    });
    // Increased wait time for page content to fully load
    await new Promise(r => setTimeout(r, 5000));

    // First check if transcript panel is already open
    let panelStatus = await isTranscriptPanelReady(page);
    let clickAttempts = 0;
    const maxClickAttempts = 3;
    
    while (!panelStatus.ready && clickAttempts < maxClickAttempts) {
      console.log(`\nAttempt ${clickAttempts + 1} to find and click transcript button...`);
      
      const clicked = await findAndClickTranscriptButton(page);
      
      if (clicked) {
        // Wait for panel to open and load
        console.log('Waiting for transcript panel to open...');
        await new Promise(r => setTimeout(r, 3000));
        
        // Check panel status with retries
        for (let i = 0; i < 5; i++) {
          panelStatus = await isTranscriptPanelReady(page);
          console.log(`Panel check ${i + 1}: ${panelStatus.ready ? 'ready' : panelStatus.reason}`);
          if (panelStatus.ready) break;
          await new Promise(r => setTimeout(r, 1000));
        }
        
        if (panelStatus.ready) {
          console.log(`Transcript panel is ready (${panelStatus.reason}, count: ${panelStatus.count})`);
          break;
        }
      } else {
        console.log('Could not find transcript button');
      }
      
      clickAttempts++;
      
      // If not found, wait and retry (page might still be loading)
      if (clickAttempts < maxClickAttempts) {
        console.log('Retrying after delay...');
        await new Promise(r => setTimeout(r, 2000));
      }
    }
    
    if (!panelStatus.ready) {
      console.log('✗ Could not open transcript panel after all attempts');
      return { success: false, videoId, name: videoName, error: 'Could not open transcript panel' };
    }

    // Wait for transcript to load
    console.log('Waiting for transcript to load...');
    for (let i = 0; i < MAX_TRANSCRIPT_WAIT; i++) {
      await new Promise(r => setTimeout(r, 1000));
      
      const status = await page.evaluate(() => {
        const panel = document.querySelector('ytd-engagement-panel-section-list-renderer[visibility="ENGAGEMENT_PANEL_VISIBILITY_EXPANDED"]');
        if (!panel) return { state: 'no_panel' };
        
        const segments = panel.querySelectorAll('ytd-transcript-segment-renderer, transcript-segment-view-model');
        const spinner = panel.querySelector('tp-yt-paper-spinner[active]');
        const cueSegments = panel.querySelectorAll('ytd-transcript-body-renderer .cue');
        
        return { 
          state: segments.length > 0 ? 'ready' : (spinner ? 'loading' : (cueSegments.length > 0 ? 'cue_ready' : 'empty')),
          segmentCount: segments.length,
          cueCount: cueSegments.length,
          spinnerActive: !!spinner
        };
      });
      
      console.log(`Attempt ${i+1}: ${status.state} (segments: ${status.segmentCount}, cues: ${status.cueCount})`);
      
      if (status.state === 'ready' || status.state === 'cue_ready') {
        break;
      }
    }

    // Scroll to trigger lazy loading
    console.log('Scrolling transcript panel...');
    await page.evaluate(() => {
      const panel = document.querySelector('ytd-engagement-panel-section-list-renderer[visibility="ENGAGEMENT_PANEL_VISIBILITY_EXPANDED"]');
      if (!panel) return;
      const scrollContainer = panel.querySelector('#scroll-container') || panel;
      scrollContainer.scrollTop = scrollContainer.scrollHeight;
    });
    await new Promise(r => setTimeout(r, 3000));

    // Extract transcript content using multiple methods
    const transcript = await page.evaluate(() => {
      const panel = document.querySelector('ytd-engagement-panel-section-list-renderer[visibility="ENGAGEMENT_PANEL_VISIBILITY_EXPANDED"]');
      if (!panel) return { method: 'none', content: 'No panel found' };

      // Method 1: ytd-transcript-segment-renderer
      const segments1 = panel.querySelectorAll('ytd-transcript-segment-renderer');
      if (segments1.length > 0) {
        const lines = [];
        for (const seg of segments1) {
          const ts = seg.querySelector('.timestamp')?.textContent?.trim() || '';
          const text = seg.querySelector('#content, .segment-text')?.textContent?.trim() || '';
          if (text) lines.push('[' + ts + '] ' + text);
        }
        if (lines.length > 0) return { method: 'ytd-transcript-segment-renderer', content: lines.join('\n'), count: lines.length };
      }

      // Method 2: transcript-segment-view-model (new YouTube UI)
      const segments2 = panel.querySelectorAll('transcript-segment-view-model');
      if (segments2.length > 0) {
        const lines = [];
        for (const seg of segments2) {
          const ts = seg.querySelector('div.ytwTranscriptSegmentViewModelTimestamp')?.textContent?.trim() || '';
          const text = seg.querySelector('span.ytAttributedStringHost[role="text"]')?.textContent?.trim() || seg.textContent?.trim() || '';
          if (text) lines.push('[' + ts + '] ' + text);
        }
        if (lines.length > 0) return { method: 'transcript-segment-view-model', content: lines.join('\n'), count: lines.length };
      }

      // Method 3: ytd-transcript-body-renderer innerText
      const body = panel.querySelector('ytd-transcript-body-renderer');
      if (body && body.innerText.trim().length > 20) {
        return { method: 'ytd-transcript-body-renderer innerText', content: body.innerText.trim(), count: body.innerText.split('\n').length };
      }

      // Method 4: Panel innerText
      const panelText = panel.innerText.trim();
      if (panelText.length > 50) {
        const lines = panelText.split('\n').filter(l => l.trim() && !l.includes('字幕記錄') && !l.includes('Transcript'));
        return { method: 'panel innerText', content: lines.join('\n'), count: lines.length };
      }

      // Method 5: TreeWalker text nodes (last resort)
      const allText = [];
      const walker = document.createTreeWalker(panel, NodeFilter.SHOW_TEXT, null, false);
      let node;
      while (node = walker.nextNode()) {
        const text = node.textContent.trim();
        if (text && text.length > 2 && !text.includes('css-build') && !text.includes('shady')) {
          allText.push(text);
        }
      }
      if (allText.length > 5) {
        return { method: 'treeWalker text nodes', content: allText.join('\n'), count: allText.length };
      }

      return { method: 'none', content: 'Could not extract transcript' };
    });

    console.log(`Method: ${transcript.method}, Count: ${transcript.count || 'N/A'}`);

    // Save to file if we got content
    if (transcript.content && transcript.content.length > 50 && transcript.method !== 'none') {
      const outputPath = path.join(OUTPUT_DIR, `${videoName}_transcript.txt`);
      const header = `# YouTube Transcript
# Title: ${videoTitle}
# URL: ${url}
# Video ID: ${videoId}
# Extracted: ${new Date().toISOString()}
# Method: ${transcript.method}

`;
      fs.writeFileSync(outputPath, header + transcript.content);
      console.log(`✓ Saved to: ${outputPath}`);
      return { success: true, videoId, name: videoName, segmentCount: transcript.count, method: transcript.method };
    } else {
      console.log(`✗ Could not extract transcript (video may not have captions)`);
      return { success: false, videoId, name: videoName, error: 'No transcript content extracted' };
    }

  } catch (error) {
    console.log(`✗ Error: ${error.message}`);
    return { success: false, videoId, name: videoName, error: error.message };
  }
}

async function main() {
  if (videos.length === 0) {
    console.error('No videos configured. Edit the `videos` array in this script before running.');
    process.exit(1);
  }

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

  // Create output directory if it doesn't exist
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const page = await browser.newPage();
  const results = [];
  const noTranscriptVideos = [];

  for (const video of videos) {
    const result = await extractTranscriptFromPage(page, video.id, video.name, video.title);
    results.push(result);
    
    if (!result.success) {
      noTranscriptVideos.push(video.id);
    }
    
    // Delay between videos to avoid rate limiting
    console.log(`\nWaiting ${DELAY_BETWEEN_VIDEOS / 1000} seconds before next video...`);
    await new Promise(r => setTimeout(r, DELAY_BETWEEN_VIDEOS));
  }

  await page.close();
  browser.disconnect();

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('SUMMARY');
  console.log('='.repeat(60));
  const successful = results.filter(r => r.success);
  const failed = results.filter(r => !r.success);
  console.log(`\nSuccessful: ${successful.length}`);
  successful.forEach(r => console.log(`  ✓ ${r.name} (${r.segmentCount} segments, method: ${r.method})`));
  console.log(`\nFailed: ${failed.length}`);
  failed.forEach(r => console.log(`  ✗ ${r.name}: ${r.error}`));
  
  if (noTranscriptVideos.length > 0) {
    console.log(`\nVideos without transcripts (save these for manual review):`);
    noTranscriptVideos.forEach(id => console.log(`  - https://www.youtube.com/watch?v=${id}`));
    
    // Save no-transcript list
    const noTranscriptPath = path.join(OUTPUT_DIR, 'no_transcript_videos.txt');
    fs.writeFileSync(noTranscriptPath, noTranscriptVideos.map(id => `https://www.youtube.com/watch?v=${id}`).join('\n'));
    console.log(`  Saved to: ${noTranscriptPath}`);
  }
  
  console.log('\n' + JSON.stringify(results, null, 2));
}

main().catch(console.error);
