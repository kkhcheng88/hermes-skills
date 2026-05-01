---
name: report-infographic
description: Generate print-quality investment report infographics from Report Template markdown content. Uses huashu-design skill's design styles to produce HTML infographics in multiple visual styles. Triggered after Report 1 (Macro Regime) or similar data-heavy report generation.
---

# Report Infographic Generator

Convert structured investment report data into beautiful, print-quality HTML infographics.

## Prerequisites

- huashu-design skill installed at `~/.hermes/skills/huashu-design/`
- Report Template at `~/Investment/templates/report1_macro_template.md`
- Report data generated from the Report 1 workflow

## Output Directory

Save generated infographics to `~/Investment/reports/` with naming convention:
- `sample_v3_{style}.html` for samples
- `{date}_report1_{style}.html` for production reports

## Section Order (Fixed)

Follow the agreed Report Template structure:

| Section | Content |
|---------|---------|
| 01 | **CIO 判斷** — Core verdict (Risk Appetite × Monetary Environment × Regime combo) + investment advice. No length limit. |
| 02 | **Second-Level Thinking** — Howard Marks framework (1st/2nd/3rd order). Placed right after CIO as it's deeper analysis of the summary. |
| 03 | **新聞驅動分析** — Grouped by topic (e.g., 美伊地緣政治, Fed). Each topic: facts + impact analysis merged (NOT separate sections). |
| 04 | **全球資產表現** — SPY, QQQ, Russell 2000 each independently with full TA (RSI, SMA). VIX level + direction only (NO RSI/SMA). Include IV Rank. |
| 05 | **Monetary Environment** — Indicator table + Oil/inflation analysis + liquidity environment. |
| 06 | **Risk Appetite** — Indicator table + detailed judgment (elaboration, not 2 sentences). |

## Design Styles (Best for Financial Reports)

Pick 1-3 styles to generate variants for user comparison:

### Recommended Styles (from huashu-design references/design-styles.md)

| Style | Feel | Colors | Best For |
|-------|------|--------|----------|
| **01 Pentagram** | Minimal, Swiss grid, typographic | B/W + 1 accent (e.g., terracotta #C23B22) on cream #FAF9F6 | Bloomberg-style professional reports |
| **04 Fathom** | Scientific, precise, data-driven | Navy #0B1426 + gray + 1 accent (#4A90D9) | Data-heavy technical reports |
| **02 Stamen** | Warm, organic, cartographic | Terracotta + sage green + deep blue on warm cream | Approachable yet professional |
| **10 Müller-Brockmann** | Pure Swiss modernism | Strict B/W + 1 accent | Ultra-clean, zero decoration |
| **17 Takram** | Japanese speculative, soft tech | Neutral naturals (beige, soft gray, muted green) | Elegant, philosophical tone |

### Style DNA Quick Reference

**Pentagram**: Extreme typographic hierarchy, 60%+ whitespace, serif display + sans body, black + 1 accent color, Swiss grid with precise spacing.

**Fathom**: Scientific journal aesthetic, precise data viz, neutral scheme (grays, navy), clean sans-serif, information density without clutter.

**Stamen**: Cartographic approach to data, organic patterns, warm palette (terracotta, sage, deep blues), layered information, hand-crafted feel.

## HTML Structure Pattern

Each infographic follows this pattern:

```
<!doctype html>
<html lang="zh-Hant">
<head>
  - Google Fonts (style-specific)
  - CSS variables (per style)
  - Layout: max-width ~1120px, centered
</head>
<body>
  <div class="report">
    - Header (title + date + confidence)
    - Section 01: CIO Verdict (3-column grid + advice block)
    - Section 02: Second-Level Thinking (3-column grid)
    - Section 03: News (card groups, 2-col facts + impact analysis)
    - Section 04: Assets (3-column card grid × 2 rows)
    - Section 05: Monetary (table + 2-col analysis cards)
    - Section 06: Risk Appetite (table + analysis card)
    - Footer (data sources)
  </div>
</body>
</html>
```

## Key Design Decisions (from user feedback)

1. **No emoji symbols for judgment** — Use clear text, not 🟢⚖️🔴. Formal report tone.
2. **SPY, QQQ, Russell 2000 are independent** — Each has own subsection with full TA. Don't compare them against each other, but always cover all three.
3. **VIX analysis** — Level + direction movement + IV Rank only. NO RSI/SMA (VIX is not a price ticker).
4. **News + Deep Analysis merged** — One section per topic, fact → impact → asset implications, all in one flow.
5. **CIO 判斷 is the star** — Longest, most important section. Other sections are supporting evidence.
6. **Second-Level Thinking after CIO** — It's deeper thinking from the summary, so it follows immediately.

## Typography Choices

| Style | Display | Body | Mono |
|-------|---------|------|------|
| Pentagram | DM Serif Display | Instrument Sans | JetBrains Mono |
| Fathom | Newsreader | DM Sans | JetBrains Mono |
| Stamen | Playfair Display | Source Sans 3 | JetBrains Mono |

Always include Traditional Chinese (繁體) fonts via Google Fonts: Noto Serif TC / Noto Sans TC as fallbacks.

## Workflow

1. Generate report data via Report 1 workflow (or use existing report)
2. Select 1-3 styles from the recommended list
3. Create HTML infographic(s) following the section order and style DNA
4. Save to `~/Investment/reports/`
5. Present to user for comparison
6. User selects preferred style → establish as default for future reports
