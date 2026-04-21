---
name: content-to-notebooklm
description: 多源內容快速 distill：將網頁、YouTube、Discord 投資內容、PDF 等上傳到 Google NotebookLM，用 AI 做摘要、分析、播客、PPT、Quiz 等多種格式輸出。支援付費牆繞過
version: 1.0.0
author: joeseesun (adapted for Hermes by Kars)
homepage: https://github.com/joeseesun/qiaomu-anything-to-notebooklm
metadata:
  hermes:
    tags: [notebooklm, content-conversion, podcast, youtube, web, paywall, distill]
---

# 多源內容 → NotebookLM 智能 Distill

將網頁、YouTube、Discord 投資心得、PDF 等上傳到 Google NotebookLM，用 AI 快速做摘要、深度分析、播客、PPT 等多種格式。

## 支援的內容源

| 類型 | 處理方式 |
|------|---------|
| 網頁 URL | 直接 `notebooklm source add <URL>` 或用 `fetch_url.sh` 繞付費牆 |
| YouTube | 直接傳 URL，NotebookLM 自動提取字幕 |
| Discord 訊息 | 複製文字內容 → 儲存 TXT → `notebooklm source add` |
| 微信公眾號 | MCP tool `read_feishu_doc` 抓取 |
| PDF / EPUB / DOCX | `markitdown` 轉換 → 上傳 |
| 本地文字 / Markdown | 直接上傳 |

## 工作目錄

```
~/.hermes/skills/content-to-notebooklm/
├── SKILL.md                          # 本文件
├── scripts/
│   └── fetch_url.sh                  # 付費牆繞過（自動偵測）
├── feishu-read-mcp/                  # 微信公眾號 MCP server
│   └── src/server.py
└── main.py                           # 深度分析模式
```

## 前置條件

所有依賴已安裝，但 NotebookLM 需要首次認證：

```bash
notebooklm login    # 首次使用前必須（開啟瀏覽器登入 Google）
notebooklm list     # 驗證認證成功
```

## 核心使用方式

### 1. 網頁文章 → Distill

```
用戶：幫我 distill 這篇文章 https://example.com/article
```

執行：
```bash
notebooklm create "文章標題"
notebooklm source add "https://example.com/article" --title "文章標題"
notebooklm generate report    # 或 audio / slide-deck / mind-map / quiz 等
notebooklm download report ./report.md
```

**付費牆網頁**（NYT / WSJ / FT / Bloomberg 等 300+ 網站）：
```bash
bash ~/.hermes/skills/content-to-notebooklm/scripts/fetch_url.sh "https://paywall-site.com/article"
# 自動 6 層級聯繞過：代理 → Googlebot UA → Referer → AMP → archive.today → agent-fetch
```

### 2. YouTube → Distill

```
用戶：這個 YouTube 幫我做摘要 https://youtube.com/watch?v=xxx
```

執行：直接傳 URL 給 NotebookLM（自動提取字幕）
```bash
notebooklm create "YouTube 影片標題"
notebooklm source add "https://youtube.com/watch?v=xxx"
notebooklm generate report
```

### 3. Discord 訊息 → Distill

Discord 訊息唔可以直接傳 URL，需要複製內容：

```
用戶：呢段 Discord 訊息幫我 distill：
（貼上內容）
```

執行：
```bash
# 儲存為 TXT
echo "用戶貼上的內容" > /tmp/discord_content_$(date +%s).txt
notebooklm create "Discord 投資心得"
notebooklm source add /tmp/discord_content_xxx.txt
notebooklm generate report
```

### 4. 微信公眾號 → Distill

```
用戶：呢篇微信文章幫我摘要 https://mp.weixin.qq.com/s/xxx
```

執行：用 MCP tool `read_feishu_doc` 抓取 → 儲存 TXT → 上傳

### 5. 本地檔案 → Distill

```
用戶：呢個 PDF 幫我做分析 /path/to/file.pdf
```

執行：
```bash
markitdown /path/to/file.pdf -o /tmp/converted.md
notebooklm create "PDF 文件"
notebooklm source add /tmp/converted.md
```

## NotebookLM 輸出格式

| 用戶指令 | 意圖 | notebooklm 命令 |
|---------|------|----------------|
| 摘要 / 總結 / 報告 | report | `generate report` |
| 播客 / 音頻 / 做成語音 | audio | `generate audio` |
| PPT / 幻燈片 | slide-deck | `generate slide-deck` |
| 思維導圖 / 腦圖 | mind-map | `generate mind-map` |
| Quiz / 出題 | quiz | `generate quiz` |
| 視頻 | video | `generate video` |
| 閃卡 / flashcards | flashcards | `generate flashcards` |

如果用戶冇指定格式，預設做 **report**（文字摘要）。

## 長線 Notebook 架構（推薦模式）

唔係每次都開新 notebook，而係用三個長線 notebook 攒 knowledge：

| Notebook | 內容範圍 | 對應投資憲章 |
|----------|---------|-------------|
| **投資哲學 & 策略** | 心態、框架、回測方法論、倉位管理 | WHY |
| **產業鏈 & 價值鏈** | 半導體 supply chain、AI infra、能源轉型 | WHAT to own |
| **市場情緒 & 宏觀** | Fed、VIX regime、資金流向、地緣政治 | WHEN |

**工作模式：**
- **每日**：收到 YouTube/Discord/文章 → 即時摘要返俾用戶 + source add 到對應 notebook（唔 generate，只加 source）
- **每週**：觸發 refresh → 對三個 notebook 分別 generate report → 提取 insights → 存入 memory → 送「本週投資知識更新」俾用戶

## 完整工作流程（以投資文章為例）

```
用戶：幫我 distill 呢篇 https://some-finance-site.com/article

1. 偵測 URL 類型 → 一般網頁
2. notebooklm create "文章標題"
3. notebooklm source add "https://some-finance-site.com/article"
4. notebooklm generate report
5. 等待生成完成
6. notebooklm download report ./report.md
7. 讀取報告內容，回傳給用戶摘要

如遇付費牆：
2b. bash fetch_url.sh "https://..." → 取得 Markdown
2c. echo "$content" > /tmp/paywall_xxx.txt
2d. notebooklm source add /tmp/paywall_xxx.txt
```

## 深度分析模式

用戶指定「深度分析」「遞歸提問」時：
```bash
python3 ~/.hermes/skills/content-to-notebooklm/main.py /path/to/file --deep-analysis
```
自動生成 10 個深度問題並向 NotebookLM 提問，返回結構化 JSON。

## 常見問題

- **NotebookLM 未認證**：執行 `notebooklm login`
- **付費牆繞過失敗**：部分網站有額外反爬蟲，成功率約 80%
- **YouTube 字幕提取**：需要影片有字幕（自動字幕或手動字幕均可）
- **生成時間**：報告 ~1-2 分鐘，播客 ~2-5 分鐘，PPT ~1-3 分鐘
