---
name: youtube-transcript-extractor
description: |
  YouTube Transcript 提取工具。使用 Puppeteer 連接 Chrome debugging port 搜尋 YouTube 影片並提取 transcripts（逐字稿）。
  適用於：提取投資者訪談/演講逐字稿、搜尋特定人物 YouTube 影片並批量提取字幕、收集已故投資者歷史訪談資料。
  觸發詞：「提取 YouTube transcript」「搜尋 YouTube 影片」「提取字幕」「YouTube 逐字稿」「搜尋投資者影片」。
---

# YouTube Transcript Extractor

## 適用範圍
此 skill 適用於所有需要提取 YouTube transcripts 的 agent，不限於特定框架。

## 前置條件
- Node.js 18+
- Puppeteer 已安裝（`npm install puppeteer`）
- Chrome 瀏覽器

## 目錄結構

```
.agents/skills/youtube-transcript-extractor/
├── SKILL.md                    # 本文件
├── scripts/
│   ├── start_chrome.bat        # Windows: 啟動 Chrome debugging
│   ├── start_chrome.sh         # Mac/Linux: 啟動 Chrome debugging
│   ├── search_youtube.js       # YouTube 搜尋腳本
│   ├── extract_transcript.js   # Transcript 提取腳本
│   └── diagnose_structure.js   # 結構診斷腳本
└── templates/
    └── batch_extract_template.js  # 批量提取模板
```

## 使用方式

### Step 1: 啟動 Chrome Debugging
```bash
# Windows
.agents\skills\youtube-transcript-extractor\scripts\start_chrome.bat

# Mac/Linux
.agents/skills/youtube-transcript-extractor/scripts/start_chrome.sh
```

### Step 2: 搜尋 YouTube 影片
編輯 `search_youtube.js` 中的 `SEARCH_QUERIES`：
```javascript
const SEARCH_QUERIES = ['Warren Buffett', 'Charlie Munger'];
```
執行：
```bash
node .agents/skills/youtube-transcript-extractor/scripts/search_youtube.js
```

### Step 3: 提取 Transcripts
編輯 `extract_transcript.js` 中的 `videos` 陣列：
```javascript
const videos = [
  { id: 'VIDEO_ID_1', name: 'investor_name_topic' },
  { id: 'VIDEO_ID_2', name: 'investor_name_topic2' },
];
```
執行：
```bash
node .agents/skills/youtube-transcript-extractor/scripts/extract_transcript.js
```

## 正確的 YouTube UI 流程
1. 打開影片頁面
2. **先點擊「...更多」按鈕展開描述**
3. 在「字幕」區塊中點擊「顯示轉錄文字」按鈕
4. Transcript 面板會在右側開啟

## 最佳實踐
- 每部影片間等待 3-5 秒，避免被 YouTube 限速
- 影片無字幕時，記錄 video ID 並跳過
- 使用 `--headed` 模式 debug
- 不要使用 VPN（可能觸發機器人驗證）
- 使用 `--user-data-dir` 連接已有 Chrome profile

## 常見問題
### Transcript 按鈕找不到
- 確保先點擊「...更多」按鈕展開描述
- 按鈕在「字幕」區塊中，標記為「顯示轉錄文字」
- 英文版為 "Show transcript"，在 "Subtitles/CC" 區塊中

### Chrome 無法連接 port 9222
- 確保 Chrome 已用 `--remote-debugging-port=9222` 啟動
- 檢查 http://localhost:9222 是否可訪問

### 機器人驗證
- 關閉 VPN
- 使用已登入的 Chrome profile
- 降低請求頻率

## 不要使用的方法
- ❌ Python `yt_transcript_fetcher.py` — timedtext API 失敗率高
- ❌ 直接用 YouTube API — 需要配額且限制多
- ✅ Puppeteer + Chrome debugging — 唯一可靠的方法

## 輸出格式

### 搜尋結果 (search_results.json)
```json
[
  {
    "videoId": "abc123",
    "title": "影片標題",
    "viewCount": "1.2M views",
    "uploadDate": "2 years ago",
    "channel": "頻道名稱",
    "duration": "15:30",
    "description": "描述...",
    "url": "https://www.youtube.com/watch?v=abc123"
  }
]
```

### Transcript 檔案 (.txt)
```
=== Video: [影片標題] ===
=== URL: https://www.youtube.com/watch?v=abc123 ===
=== Duration: 15:30 ===

[00:00] First line of transcript
[00:05] Second line of transcript
...
```
