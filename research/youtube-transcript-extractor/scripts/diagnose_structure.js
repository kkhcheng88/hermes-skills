/**
 * Diagnostic script to inspect YouTube page structure for transcript button
 */
const puppeteer = require('puppeteer-core');

const CHROME_DEBUG_URL = 'http://127.0.0.1:9222';
const TEST_URL = 'https://www.youtube.com/watch?v=gE-6jGfXvQ0';

(async () => {
  const browser = await puppeteer.connect({ browserURL: CHROME_DEBUG_URL });
  const page = await browser.newPage();
  
  try {
    console.log('Navigating to test video...');
    await page.goto(TEST_URL, { waitUntil: 'networkidle2', timeout: 30000 });
    console.log('Page loaded, waiting 5s for full render...');
    await new Promise(r => setTimeout(r, 5000));
    
    // 1. Find all sections with aria-label containing 字幕/Subtitles/Caption
    console.log('\n=== Sections with 字幕/Subtitles/Caption aria-label ===');
    const captionSections = await page.evaluate(() => {
      const results = [];
      const allElements = document.querySelectorAll('[aria-label]');
      for (const el of allElements) {
        const label = el.getAttribute('aria-label');
        if (label && (label.includes('字幕') || label.toLowerCase().includes('subtitle') || label.toLowerCase().includes('caption'))) {
          results.push({
            tag: el.tagName,
            ariaLabel: label,
            id: el.id,
            className: el.className.substring(0, 100),
            childCount: el.children.length
          });
        }
      }
      return results;
    });
    console.log(JSON.stringify(captionSections, null, 2));
    
    // 2. Find all buttons with transcript-related text
    console.log('\n=== Buttons with transcript/轉錄 text ===');
    const transcriptButtons = await page.evaluate(() => {
      const results = [];
      const buttons = document.querySelectorAll('button');
      for (const btn of buttons) {
        const text = btn.textContent.trim();
        const ariaLabel = btn.getAttribute('aria-label') || '';
        if (text.toLowerCase().includes('transcript') || text.includes('轉錄') || text.includes('字幕記錄') ||
            ariaLabel.toLowerCase().includes('transcript') || ariaLabel.includes('轉錄') || ariaLabel.includes('字幕記錄')) {
          results.push({
            text: text.substring(0, 100),
            ariaLabel: ariaLabel,
            id: btn.id,
            className: btn.className.substring(0, 100),
            parentTag: btn.parentElement?.tagName,
            parentAriaLabel: btn.parentElement?.getAttribute('aria-label') || '',
            parentClass: btn.parentElement?.className?.substring(0, 100) || ''
          });
        }
      }
      return results;
    });
    console.log(JSON.stringify(transcriptButtons, null, 2));
    
    // 3. Look for ytd-watch-metadata structure
    console.log('\n=== ytd-watch-metadata structure ===');
    const watchMetadata = await page.evaluate(() => {
      const metadata = document.querySelector('ytd-watch-metadata');
      if (!metadata) return 'NOT FOUND';
      const buttons = metadata.querySelectorAll('button');
      const buttonInfo = [];
      for (const btn of buttons) {
        buttonInfo.push({
          text: btn.textContent.trim().substring(0, 80),
          ariaLabel: btn.getAttribute('aria-label') || '',
          id: btn.id,
          className: btn.className.substring(0, 80)
        });
      }
      return {
        childCount: metadata.children.length,
        buttons: buttonInfo
      };
    });
    console.log(JSON.stringify(watchMetadata, null, 2));
    
    // 4. Look for the description/action area structure
    console.log('\n=== Action area structure (#top-row, #actions) ===');
    const actionArea = await page.evaluate(() => {
      const results = {};
      const topRow = document.querySelector('#top-row');
      if (topRow) {
        const buttons = topRow.querySelectorAll('button');
        results.topRowButtons = Array.from(buttons).map(btn => ({
          text: btn.textContent.trim().substring(0, 80),
          ariaLabel: btn.getAttribute('aria-label') || '',
          className: btn.className.substring(0, 80)
        }));
      }
      const actions = document.querySelector('#actions');
      if (actions) {
        const buttons = actions.querySelectorAll('button');
        results.actionsButtons = Array.from(buttons).map(btn => ({
          text: btn.textContent.trim().substring(0, 80),
          ariaLabel: btn.getAttribute('aria-label') || '',
          className: btn.className.substring(0, 80)
        }));
      }
      return results;
    });
    console.log(JSON.stringify(actionArea, null, 2));
    
    // 5. Check for any element containing "轉錄" or "transcript" text
    console.log('\n=== All elements containing transcript/轉錄 text ===');
    const allTranscriptElements = await page.evaluate(() => {
      const results = [];
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
      while (walker.nextNode()) {
        const node = walker.currentNode;
        const text = node.textContent?.trim() || '';
        const ariaLabel = node.getAttribute('aria-label') || '';
        const tagName = node.tagName.toLowerCase();
        if ((text.toLowerCase().includes('transcript') || text.includes('轉錄') || text.includes('字幕記錄') ||
             ariaLabel.toLowerCase().includes('transcript') || ariaLabel.includes('轉錄') || ariaLabel.includes('字幕記錄')) &&
            text.length < 200) {
          results.push({
            tag: tagName,
            text: text.substring(0, 100),
            ariaLabel: ariaLabel,
            id: node.id,
            className: node.className?.substring?.(0, 80) || ''
          });
        }
      }
      return results.slice(0, 30); // limit output
    });
    console.log(JSON.stringify(allTranscriptElements, null, 2));
    
    // 6. Specifically look for the "..." menu button and its structure
    console.log('\n=== More/... button structure ===');
    const moreButtons = await page.evaluate(() => {
      const results = [];
      const buttons = document.querySelectorAll('button');
      for (const btn of buttons) {
        const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
        const text = btn.textContent.trim().toLowerCase();
        if (ariaLabel.includes('more') || ariaLabel.includes('更多') || text === '...' || text === '···') {
          results.push({
            text: btn.textContent.trim().substring(0, 80),
            ariaLabel: btn.getAttribute('aria-label') || '',
            id: btn.id,
            className: btn.className.substring(0, 80),
            parentTag: btn.parentElement?.tagName,
            parentClass: btn.parentElement?.className?.substring(0, 80) || ''
          });
        }
      }
      return results;
    });
    console.log(JSON.stringify(moreButtons, null, 2));
    
  } catch (err) {
    console.error('Error:', err.message);
  } finally {
    await page.close();
    browser.disconnect();
  }
})();
