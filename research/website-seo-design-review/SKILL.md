---
name: website-seo-design-review
description: Review a website's SEO health and design quality — extract metadata, structured data, sitemap, and analyze visual design.
triggers:
  - review website
  - check SEO
  - website audit
  - analyze website design
  - SEO analysis
---

# Website SEO & Design Review

Comprehensive review combining technical SEO audit + design analysis. For business websites, professional services sites, or any web property.

## Step 1: Technical SEO Audit

### Extract metadata via browser console
```javascript
JSON.stringify({
  title: document.title,
  metaDesc: document.querySelector('meta[name="description"]')?.content,
  metaKeywords: document.querySelector('meta[name="keywords"]')?.content,
  canonicalUrl: document.querySelector('link[rel="canonical"]')?.href,
  ogTitle: document.querySelector('meta[property="og:title"]')?.content,
  ogDesc: document.querySelector('meta[property="og:description"]')?.content,
  ogImage: document.querySelector('meta[property="og:image"]')?.content,
  lang: document.documentElement.lang,
  hreflang: [...document.querySelectorAll('link[hreflang]')].map(e => ({lang: e.hreflang, href: e.href})),
  h1: [...document.querySelectorAll('h1')].map(e => e.textContent.trim()),
  h2: [...document.querySelectorAll('h2')].map(e => e.textContent.trim()),
  links: document.querySelectorAll('a').length,
  images: document.querySelectorAll('img').length,
  imagesWithoutAlt: [...document.querySelectorAll('img')].filter(i => !i.alt).length,
  structuredData: [...document.querySelectorAll('script[type="application/ld+json"]')].map(s => JSON.parse(s.textContent))
})
```

### Check technical files via curl
```bash
curl -s "https://DOMAIN/robots.txt" -H "User-Agent: Mozilla/5.0" | head -30
curl -s "https://DOMAIN/sitemap.xml" -H "User-Agent: Mozilla/5.0" | head -50
```

### Extract CSS design properties
```javascript
JSON.stringify({
  fontFamily: getComputedStyle(document.body).fontFamily,
  bodyColor: getComputedStyle(document.body).color,
  bodyBg: getComputedStyle(document.body).backgroundColor,
  links: getComputedStyle(document.querySelector('a') || document.body).color
})
```

## Step 2: Design Analysis

### Pitfalls
- Google search may CAPTCHA — use curl with Bing or alternative search engines instead
- Vision analysis may 404 — fall back to browser console CSS extraction + code-based analysis
- Wix/static sites — robots.txt and sitemap.xml usually exist but may be auto-generated

### Check each language version
If multilingual (hreflang tags present), navigate to each version and compare:
- Are titles/descriptions different per language?
- Is structured data correct per locale?
- Are there content differences?

## Step 3: Google Maps / Local SEO

Check Google Business Profile for:
- Rating and review count
- Category accuracy
- NAP consistency (Name, Address, Phone match website)
- Photos, hours, services listed

## Step 4: Report Structure

Organize findings as:
1. Critical (P0) — Broken structured data, missing H1, wrong hreflang
2. Major (P1) — No trust signals, thin content, missing meta descriptions
3. Minor (P2) — Font choice, color palette, image alt text
4. Competitor comparison — What do top sites in this industry have?

## Pitfalls and Lessons Learned

- Structured data on Wix can have wrong addresses (auto-filled from template, not user data) — always verify
- ZH/EN sites on Wix may share the same page title despite having hreflang — check both versions
- Wix pages-sitemap.xml may have stale lastmod dates — does not mean content is stale, but Google may crawl less frequently
- browser_vision tool intermittently returns 404 — have CSS extraction fallback ready
- Single-page Wix sites typically have no separate service pages — flag as major SEO gap for local businesses
