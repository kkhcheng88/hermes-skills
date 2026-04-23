---
name: report2-chain-sector
description: 生成 Report 2（Layer 2）— Value Chain + Sector 分析。Chain 優先，Sector 監控為主。觸發詞：report 2, layer 2, sector report, chain report, 產業鏈報告, 板塊報告。
---

# Report 2 — Value Chain + Sector（Layer 2）

Report 2 喺 Report 1（Macro Regime）嘅前提下揀戰場。核心邏輯：**Chain 優先，Sector 退後**。

## Template

**Markdown**：直接生成，結構跟隨 Section 順序。存檔路徑：`~/Investment/reports/daily_report2_chain_sector.md`

**HTML**：Fathom 深海軍藍風格（同 Report 1），template 存檔：`~/Investment/reports/daily_report2_chain_sector.html`。HTML 版唔用 emoji，用色點/圖標代替。Discord 用 `MEDIA:` 語法發送 HTML attachment。

## 核心設計決策

### Chain vs Sector 優先級

| | Chain（產業鏈） | Sector（板塊） |
|--|---------------|---------------|
| **粒度** | 窄、聚焦 | 大、泛 |
| **爆發力** | 高，容易出機會 | 低，平時少見大動 |
| **角色** | 核心分析對象 | 監控為主，異常先展開 |
| **Template 位置** | Section 3-4（優先） | Section 6（靠後） |

### Sector 深度分析觸發條件（三選一）

未觸發 → 只有表格 + 一句話（等同持續監控）。
觸發 → 展開 Section 6.3 深入分析。

| 觸發條件 | 閾值 | 邏輯 |
|---------|------|------|
| **偏差過大** | vs SPY 偏差 > ±5%（1W 或 1M） | 資金大規模流入/流出 |
| **連續異動** | 連續 3 日以上同方向偏離 SPY | 持續性異動而非 noise |
| **板塊級催化劑** | 政策/法規/宏觀事件直接影響成個板塊 | Structural change，唔係單一公司新聞 |

### Chain 冷熱判定

三個信號，任何一個觸發 → 升溫/降溫：
1. 新聞突變
2. 股價 vs SPY 短期偏差
3. 技術指標信號

狀態：🔥 熱 / 🌡️ 升溫 / ❄️ 冷

## Section 順序（固定，唔好改）

1. **Macro Context 連結** — 從 Report 1 提取 Regime 組合，一句話講前提
2. **CIO 判斷** — 核心結論 + 本週注意力分配（CIO Filter：睇啲乜 + 信號 + 行動 trigger） + 操作指引
3. **Value Chain 溫度計 + 輪動概覽** — 10 條 Chain 冷熱狀態 + 輪動變化
4. **熱門 Chain 深度分析** — 只展開 🔥/🌡️，含敘事分析 + cycle positioning + 風險 + IC 結論
5. **行業新聞驅動（過去一週）** — 新聞為 Chain 分析服務，含 chain 內部分化
6. **Sector ETF 監控** — GICS 11 + 主題 12，表格為主，觸發條件先展開 6.3
7. **資金流向 + 時間窗口** — 資金流向 + 風險/催化劑時間窗口
8. **持續監測** — 3-5 個觸發條件

## 10 條 Value Chain

1. AI / 半導體
2. 光通訊
3. Memory
4. 能源
5. 貴金屬
6. Nuclear / Uranium
7. Cybersecurity
8. GLP-1 / Obesity
9. Reshoring / Industrial
10. Quantum Computing

## 23 ETF 清單

**GICS 11**：XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLB, XLRE, XLU, XLC

**主題 12**：DRAM, NASA, MEME, CHAT, IGV, GRID, QTUM, CIBR, NLR, URA, DFEN, PAVE

## 格式規則

- **Discord 文字版可用 emoji 增強可讀性**（🔥 熱 / 🌡️ 升溫 / ❄️ 冷 / 🔴🟡⚪ 風險等級），HTML 版唔用 emoji
- Agent 思想蒸馏成分析視角，唔拋書包列 Agent 名
- IC 式一句話結論（每個深度分析都要有）
- 繁體中文（廣東話口語風格）

## Agent Framework（按情境自動選擇）

| 情境 | 視角 | 分析重點 |
|------|------|---------|
| 過熱 | Marks + Miller + Eveillard | 係頂？定仲有空間？ |
| 過冷 | Klarman + Munger + Graham | 真撈底？定 value trap？ |
| 升溫 | Lynch + Greenblatt + Marks | 真催化定 noise？ |
| 內部分化 | Lynch + Buffett + Greenblatt | 邊類受益？邊類受壓？ |
| 通用 | Marks + Munger + Lynch | 基礎三件套 |

## 與 Report 1 關係

- Report 1 提供 Macro Regime 前提（Risk Appetite × Monetary Environment × Regime 組合）
- Report 2 喺此前提下揀戰場（Chain + Sector）
- Report 2 的 Section 1 直接從 Report 1 提取結論，唔重複

## Data Sources

| 工具 | 用途 |
|------|------|
| yfinance | ETF 價格、技術指標（RSI/SMA） |
| TradingKey Stock Score API | 板塊/個股評分、輿情 |
| WallStreetCN | 行業新聞（過去一週） |
| News API | 英文行業新聞（過去一週） |

**新聞時效性原則**：以最新新聞為主（過去 7 日）。Report 2 跟隨 Report 1 嘅 macro 結論，唔重複 macro data。

## Deliver to Discord

如果將來做 Markdown 版本（文字分段），分 4-5 段 send 到 #investment channel（Discord 有字數限制）：

```
send_message(target="discord:1495805538003583006", message="...")
```

**分段策略**（經驗值）：
1. **Macro Context + CIO 判斷 + 注意力分配表**（含操作指引）
2. **Chain 溫度計 + 輪動概覽**（溫度表 + 一段文字）
3. **熱門 Chain 深度**（2-3 條 chain 深度分析）
4. **行業新聞驅動 + Sector ETF 異常**（新聞 + 異常 sector）
5. **風險時間窗口 + 持續監測 + 操作指引總結**（含存檔路徑）

**HTML 版本（推薦，同 Report 1 Fathom 風格）**：
```
send_message(target="discord:1495805538003583006", message="Report 2 — Value Chain + Sector（{date}）\\nMEDIA:~/Investment/reports/daily_report2_chain_sector.html")
```
