# Compass Meta-Skill

> **Compass 投資框架的單一進入點。**
> Version: 0.7 | Last updated: 2026-05-01

---

## 身份定位

當用戶提到「Compass」或任何與股票分析相關的 ticker 時，載入此 skill。

Compass 是一套**判斷約束系統**（Judgement Constraint System），不是預測系統，也不是明牌平台。

核心信念：
> **錯誤暴露得越早，長期結果越好。**

---

## Compass Home Directory

```
~/compass/           ← 所有路徑以此為根目錄
├── skills/          ← 7個執行技能（00-06 + workflow）
├── charter/         ← 投資憲章（最高指導原則）
├── cases/           ← 實戰案例庫
├── lenses/          ← 蒸餾投資者鏡片（Lynch/Marks/Munger）
└── reference/       ← 知識參考

所有 skills 路徑：~/compass/skills/*.md
所有 cases 路徑：~/compass/cases/*.md
```

---

## 五類 Setup 分類

每次分析從 Setup Classifier 開始：

| Setup | 特徵 | 主要工具 |
|-------|------|---------|
| **A 類** | 成熟業務 + 過熱/過冷定價 | Story-First + Snowflake + Tree |
| **B 類** | Pre-revenue / Binary option | Snowflake + Tree + EV Layer |
| **C 類** | 強週期 / 商品 | Cycle-First + Scenario Planning |
| **D 類** | 穩定現金流 / 防禦 | DCF + Charter 紀律 |
| **E 類** | Identity Transition | 雙 Snowflake + EV Layer |

---

## 觸發條件（何時跑完整 Compass Workflow）

### ✅ 適合跑完整 workflow：
- 用戶認真考慮一個 **new ticker** 的持倉
- 已持有但出現 **thesis-changing event**（earnings、新催化劑）
- 季度 **portfolio review**

### ❌ 不適合：
- 5分鐘快速檢查（用 Skill 00 + brief Skill 03）
- 純粹 research 學習（不需要 Charter Check）
- 用戶已決定方向，只想要 confirmation（會 confirm bias）

---

## 完整 Workflow 順序

```
Step 1: Skill 00 — Setup Classifier（入口分類）
Step 2: Skill 01 — Snowflake Builder（結構理解）
Step 3: Skill 02 — Tree Builder（命題定義）
Step 4: Skill 03 — Story-First（市場敘事偵測）
Step 5: Skill 04 — EV Calculator（期望值計算）
Step 6: Skill 05 — Charter Check（最終 Gate）
Step 7: Skill 06 — Social Post Generator（社交內容）
Step 8: NotebookLM Infographic（如需要）
```

**CRITICAL Rules：**
- **必須按順序跑 Skills 01 → 06，唔准跳任何一個**
- **即使係 D-class（穩定現金流）都係完整版，唔准簡化任何一個 Skill**
- **所有 Skills 01-06 全部要用完整版分析，冇簡易版**
- **每個 Skill 完成後，必須等用戶 Layer 0 input 之後才進下一步**
- **不能 skip Charter Check（Skill 05）**
- **不能 skip cases archive**
- **⚠️ 數據完整性硬性規定：每個分析必須先完整拎數據，再開始 Skills 01-06 分析**
  - **禁止用 `web_search` 代替相應 skill 工具（edgar-sec-filing-workaround、fool-transcript-scraper、tradingkey、yahoo 等）**
  - **所有 data sources 必須喺 analysis 開始前口頭確認已去過邊個 source**
  - **數據不足就停手，唔准靠估**
  - **Headed browser 只係其中一個 extraction 工具，唔係必要條件**

### ⚠️ 數據完整性硬性規定

> **投資分析必須基於充足、可靠嘅數據，唔准靠估。呢個係鐵律，冇得商量。**

**分析前必須確認以下核心數據都攞到：**
1. Yahoo Finance 基本數據（price, market cap, PE, div yield, beta, revenue growth）
2. Yahoo Finance 財務報表（income statement, balance sheet, cash flow statement）
3. Earnings Transcript（最優先 Motley Fool，其次 EDGAR）
4. TradingKey 評分 + 新聞（如有）
5. 52W High/Low、近期支撐/阻力位
### ✅ 公司 IR Website（最高優先！所有 qualitative data 都喺呢度）

> **⚠️ IR Website First 規則（2026-05-01 ONDS 教訓）：**
> - 第三方的數據源（Yahoo Finance、TradingKey、SEC XBRL）經常完全 miss 併購消息、政府合約、戰略合作、的重大催化劑
> - 公司的 IR website（`https://ir.{company_domain}/press-releases`）才是最完整、最即時的 source
> - **每個分析都必須首先檢查公司 IR website**，然後先至用其他數據源
> - SEC.gov 會 block 自動化 access，但公司 IR website 通常可以直接 fetch
> - 備用方案：公司 website + 新聞稿 cloudfront CDN（如 `d1io3yog0oux5.cloudfront.net`）

**IR Website fetch 失敗時的 fallback 順序：**
1. IR website 直接 fetch（通常成功）
2. IR website → 提取 PR 連結 → 逐個 fetch PR 頁面
3. 公司主網 + investor relations section
4. 第三方新聞（TradingKey、Google News RSS、stocknews.com）
5. SEC XBRL API（只係 financial data，miss曬 qualitative）
6. **停，告知用戶數據不足**

**⚠️ ONDS 案例教訓（牢記）：**
- 第三數據源（Yahoo Finance、SEC XBRL、TradingKey）可以完全miss：**併購消息、政府合規單、策略合作、產品發布**
- 8-K items 1.01 = 併購協議 entry；2.01 = 併購完成
- 如見到多個1.01/2.01 filings + 大量集資 → 幾乎肯定有大型M&A activity，必須去IR網站確認
- Quarterly revenue突然爆發（OND Q4 $30M vs Q3 $10M）可能係併購後財務合併結果，唔係organic growth
- **IR website 先，永遠都係IR website 先**

**Web Search / Browser 的限制：**
- Web search API（`web_search` tool）**可能被block**（403/AUTH_ERROR）
- 瀏覽器工具可能遭遇 Google/SEC 的 bot detection
- JavaScript-rendered pages（如 IR website）`web_extract` 只係取到 HTML shell

**解決方案：Headed Browser（唔係VPN！）**
- WSL Chrome Beta + Xvfb + Playwright **Headed Mode**
- Headed mode 模仿真實用戶瀏覽器指紋，可以bypass大部分anti-bot
- 指令：`browser_navigate` + `browser_snapshot` + `browser_vision` 組合
- 安裝路徑：`/usr/bin/google-chrome-beta`
- **公司 IR website 通常係最可靠嘅 qualitative data 來源**，優先確保呢個得

**口頭禪：「數據不足，先停一停，唔好靠估」**

**如果關鍵數據缺失，點做？**

| 情況 | 行動 |
|------|------|
| 某項數據攞唔到 | 嘗試替代數據源（SEC filings、Morningstar、QuestMobile） |
| 替代都冇 | 明確標示邊項數據缺失，並說明邊個 conclusion 係靠估、風險幾高 |
| 超過 2 項核心數據缺失 | **停。唔好繼續分析。** 如實告知用戶：「數據不足，無法得出可靠結論，請補充資料。」 |

**口頭禪：「數據不足，先停一停，唔好靠估」**

---

## 讀取建議

分析開始前，先讀取以下文件建立上下文：

1. `~/compass/ARCHITECTURE.md` — 五層架構（如果未讀過）
2. `~/compass/charter/CHARTER.md` — 投資憲章（每次都要對照）
3. `~/compass/skills/workflow_full_run.md` — 完整流程說明
4. `~/compass/cases/` — 現有案例，了解風格與格式

---

## Skill 06 + NotebookLM Infographic Workflow

Skill 06（Social Post Generator）是用於將內部分析轉化為社交媒體內容的轉化器。

**觸發時機：**
- Case 分析完成後（verdict 為 GO/WAIT/NO-GO 都可以）
- 用戶明確要求生成 social post

**用途：** 散戶內容創作（Substack / IG / Twitter / LinkedIn）

### NotebookLM Infographic 生成流程（Option B）

當用戶要求將 Skill 06 輸出轉化為 infographic 時，執行以下流程：

```bash
# Step 1: 確認 VPN 已開啟（必須！NotebookLM 需要 VPN）
# 詢問用戶：「請打開 VPN，完成後通知我」

# Step 2: Skill 06 完成 → 保存 case file
# Step 3: 確認 / 切換到現有 notebook（如 Compass Engine）
notebooklm use e79728dc

# Step 4: 上傳 case file，捕獲返回的 source ID
# 重要：返回的 UUID（0d0d189a-xxxx）必須保存並在下一步使用
notebooklm source add ~/compass/cases/{date}_{ticker}_case.md
# 輸出範例: "Added source: 0d0d189a-07a4-4fd5-9539-600684e99a14"
#                    ↑ 這個 ID 必須用在 --source 參數

# Step 5: 生成 infographic — 必須用 -s 指定 source ID，否則會用整個 notebook
notebooklm generate infographic \
  -s 0d0d189a-07a4-4fd5-9539-600684e99a14 \
  --style bento-grid \
  --orientation landscape \
  --detail detailed \
  --wait "Compass {ticker} analysis: {verdict}. {key findings summary}."

# Step 6: 下載（狀態 completed 但 url 為 null，用 download 指令）
notebooklm download infographic ~/compass/cases/{date}_{ticker}_infographic.png --force
```

**⚠️ VPN 要求（重要！）：**
- NotebookLM 需要 VPN（Surfshark）先可以訪問
- 用戶需要手動打開 VPN
- **每次用 NotebookLM 前必須先問用戶確認 VPN 已開**
- VPN 確認後才能執行 `notebooklm` 命令

**⚠️ CRITICAL — 必須指定 source ID：**
- 唔指定 `-s` → NotebookLM 會用成個 notebook 所有資料，生出嚟嘅 infographic 唔係你想要嘅內容
- 上傳 case file 後，CLI 會返回一個 UUID，呢個就係 source ID
- 每次生成 infographic 都必須用 `-s {source_id}` 指定係邊份 doc

**重要發現（Trial & Error 得出的真相）：**
- `--json` 返回 `{"status": "completed", "url": null}` = 成功，URL 不在 JSON 回應中
- 下載靠 `notebooklm download infographic` 指令，不是靠 JSON 的 URL
- `notebooklm create` 創建空 notebook，應該用現有 notebook + `source add`
- Artifact 名稱可能不是 "{ticker}"，下載 latest 即可

**Output 保存位置：**
```
~/compass/cases/{date}_{ticker}_infographic.png
```

**Infographic 風格指令：**
```
Create a sophisticated, comprehensive technical analysis infographic with a "High-Tech Command Center" 
or "Advanced Data Dashboard" aesthetic. Use a very dark, matte navy-blue or deep charcoal background, 
overlaid with a subtle, glowing technological grid pattern and interconnected geometric network lines. 
Information should be organized into a dense, multi-grid panel structure (like a bento grid) where 
each module is clearly demarcated by thin, precise, cyan-blue or teal-blue glowing borders, making 
them look like holographic data screens from a sci-fi interface. Contrast with a clean, un-glowing 
top banner area (e.g., gold text) for the main title and logo.
```

---

## 與其他工具的整合

| 工具 | 用途 |
|------|------|
| GLM-5.1（glm-5） | 分析 + 報告撰寫（max_tokens=32000） |
| MiniMax-M2.7 | 數據下載 / 提取 |
| yfinance | 股價、財務數據 |
| TradingKey | 股票評分（必含在每個股票分析中） |

**LLM 選擇規則：**
- Charter Check（Skill 05）**不能用 Minimax**（見 `_PROMPT_GUIDE.md`）
- Skill 04 EV Calculator 建議用 GLM-5

---

## 數據來源完整地圖

每個分析都必須從以下來源獲取數據，缺一不可。

### 股價 / 財務數據
| 來源 | 用途 | Skill |
|------|------|-------|
| Yahoo Finance（yfinance API） | 股價、52W range、技術指標、EPS、revenue、P/E、FCF | `yahoo` |
| TradingKey API | 專有評分、6維分析、操作建議、分析師評級 | `tradingkey` |

### Earnings Call Transcript（最關鍵）
| 來源 | 覆蓋 | Skill |
|------|------|-------|
| **The Motley Fool**（免費全文） | 50k+ chars，CEO/CFO prepared remarks + Q&A + 32 takeaways | `fool-transcript-scraper` |
| Yahoo Finance（需付費） | 僅 2,447 chars preview | 不建議使用 |

> ⚠️ **Earnings transcript 優先用 Fool**。Yahoo Finance transcript 需要 Silver/Gold subscription，只有預覽。

### SEC Filings
| 來源 | 用途 | Skill |
|------|------|-------|
| EDGAR EFTS API（繞過 bot detection） | 8-K、10-Q、10-K 文件元數據 | `edgar-sec-filing-workaround` |

### 新聞 / KOL 觀點
| 來源 | 用途 | Skill |
|------|------|-------|
| TradingKey（SSR HTML） | 股票相關新聞（6篇，附描述） | `tradingkey` |
| Google News RSS + Xvfb | 備援新聞發現，適合小型股 | `stock-news-gathering` |
| Discord KOL channels | KOL 分析觀點（需 Discord token） | `discord-kol` |

### 宏觀數據
| 來源 | 用途 | Skill |
|------|------|-------|
| 華爾街見聞 | 實時金融新聞（中文） | `wallstreetcn` |
| NewsAPI | 突發新聞 | 直接調用 |

---

## 標準數據獲取流程

每個 ticker 分析前，必須執行：

```bash
# 1. Yahoo Finance — 基本面 + 技術指標
python fetch_yahoo.py {TICKER} --full

# 2. TradingKey — 評分 + 新聞
python tradingkey_fetcher.py {TICKER} --save data/

# 3. Motley Fool — Earnings Transcript（全套）
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" \
  python3 scrap_fool.py {TICKER}

# 4. EDGAR — 最新 SEC filings（如需要）
# 使用 edgar-sec-filing-workaround skill
```

---

### 數據覆蓋限制

| 限制 | 解決方案 |
|------|---------|
| HK/中國股票 | TradingKey 只支援美股（NASDAQ/NYSE），港股需其他來源 |
| 小型股 news 稀疏 | 用 `stock-news-gathering` 備援管道 |
| Discord KOL | 需要你自己的 Discord token + channel ID |
| KO (NYSE) | TradingKey API route 只支持 `nasdaq-{symbol}` lowercase，KO 作為 NYSE stock 無法直接用 | 用 yfinance 代替，TradingKey 只用於 news scraping |
| 實時股價 | Yahoo Finance 有 15 分鐘延遲，無真正實時 |

---

## Update 紀錄

| 日期 | 更新 |
|------|------|
| 2026-05-01 | v0.1 — 初版 meta-skill，建立單一進入點 |
| 2026-05-01 | v0.2 — 加入完整數據來源地圖 |
| 2026-05-01 | v0.5 — 加入「全部Skills必須用完整版，冇簡易版」規則 |
| 2026-05-01 | v0.6 — 加入 Charter Check 不能用 Minimax、EV Calculator 建議用 GLM-5 |
| 2026-05-01 | v0.7 — 加入「IR Website First」規則（ONDS 分析教訓：IR website reveal 併購+政府合約，第三方數據全部 miss） |

---

## 相關 Skills（個人技能，非 Compass 框架）

| Skill | 用途 |
|-------|------|
| `yitter` | X/Twitter 操作 |
| `content-to-notebooklm` | 內容上傳到 NotebookLM |
| `report-infographic` | 生成投資報告 infographic |
| `macro-regime-report` | 宏觀 Regime Report（HTML） |
