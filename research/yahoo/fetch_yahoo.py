# -*- coding: utf-8 -*-
"""
CIO Engine — Yahoo Finance Data Fetcher
========================================
Data Source: yfinance API (primary) + Yahoo Finance web (backup)
Features: Fetch company info, analyst consensus, technical indicators
Output: JSON file to data/companies/{ticker}/

Usage:
    python engine/scripts/fetch_yahoo.py TSLA
    python engine/scripts/fetch_yahoo.py TSLA --full  # Include technical indicators
    python engine/scripts/fetch_yahoo.py TSLA --output data/companies/TSLA/raw.json
"""

import yfinance as yf
import json
import sys
import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# Fix Windows encoding issue
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# ============================================================
# 配置
# ============================================================

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
DEFAULT_OUTPUT_DIR = "data/companies"


# ============================================================
# 工具函數
# ============================================================

def safe_get(data: dict, key: str, default=None):
    """安全取值，處理 None 和空字串"""
    val = data.get(key, default)
    if val is None or val == '' or val == 'N/A':
        return default
    return val


def retry_fetch(func, *args, max_retries=MAX_RETRIES, delay=RETRY_DELAY, **kwargs):
    """帶重試機制的數據抓取"""
    last_error = None
    for attempt in range(max_retries):
        try:
            result = func(*args, **kwargs)
            if result is not None:
                return result
            last_error = "Result is None"
        except Exception as e:
            last_error = str(e)
        
        if attempt < max_retries - 1:
            print(f"  ⚠️ Attempt {attempt + 1} failed: {last_error}. Retrying in {delay}s...")
            time.sleep(delay)
    
    print(f"  ❌ All {max_retries} attempts failed: {last_error}")
    return None


# ============================================================
# 核心抓取函數
# ============================================================

def fetch_basic_info(ticker: str) -> Dict[str, Any]:
    """抓取公司基本資訊"""
    print(f"📊 Fetching basic info for {ticker}...")
    
    t = yf.Ticker(ticker)
    info = retry_fetch(lambda: t.info)
    
    if not info:
        return {"error": "Failed to fetch basic info", "ticker": ticker}
    
    result = {
        "ticker": ticker,
        "fetch_date": datetime.now().isoformat(),
        "company_name": safe_get(info, 'longName'),
        "sector": safe_get(info, 'sector'),
        "industry": safe_get(info, 'industry'),
        "description": safe_get(info, 'longBusinessSummary'),
        "employees": safe_get(info, 'fullTimeEmployees'),
        
        # 價格數據
        "price": {
            "current": safe_get(info, 'currentPrice'),
            "previous_close": safe_get(info, 'previousClose'),
            "open": safe_get(info, 'open'),
            "day_low": safe_get(info, 'dayLow'),
            "day_high": safe_get(info, 'dayHigh'),
            "52week_low": safe_get(info, 'fiftyTwoWeekLow'),
            "52week_high": safe_get(info, 'fiftyTwoWeekHigh'),
            "50day_avg": safe_get(info, 'fiftyDayAverage'),
            "200day_avg": safe_get(info, 'twoHundredDayAverage'),
        },
        
        # 估值指標
        "valuation": {
            "market_cap": safe_get(info, 'marketCap'),
            "enterprise_value": safe_get(info, 'enterpriseValue'),
            "trailing_pe": safe_get(info, 'trailingPE'),
            "forward_pe": safe_get(info, 'forwardPE'),
            "peg_ratio": safe_get(info, 'pegRatio'),
            "price_to_sales": safe_get(info, 'priceToSalesTrailing12Months'),
            "price_to_book": safe_get(info, 'priceToBook'),
            "ev_to_revenue": safe_get(info, 'enterpriseToRevenue'),
            "ev_to_ebitda": safe_get(info, 'enterpriseToEbitda'),
        },
        
        # 盈利指標
        "profitability": {
            "trailing_eps": safe_get(info, 'trailingEps'),
            "forward_eps": safe_get(info, 'forwardEps'),
            "profit_margin": safe_get(info, 'profitMargins'),
            "operating_margin": safe_get(info, 'operatingMargins'),
            "gross_margin": None,  # 需要從財報計算
            "return_on_equity": safe_get(info, 'returnOnEquity'),
            "return_on_assets": safe_get(info, 'returnOnAssets'),
        },
        
        # 財務健康
        "financials": {
            "total_cash": safe_get(info, 'totalCash'),
            "total_debt": safe_get(info, 'totalDebt'),
            "debt_to_equity": safe_get(info, 'debtToEquity'),
            "current_ratio": safe_get(info, 'currentRatio'),
            "revenue_growth": safe_get(info, 'revenueGrowth'),
            "earnings_growth": safe_get(info, 'earningsGrowth'),
            "free_cashflow": safe_get(info, 'freeCashflow'),
            "operating_cashflow": safe_get(info, 'operatingCashflow'),
        },
        
        # 分紅
        "dividend": {
            "rate": safe_get(info, 'dividendRate'),
            "yield": safe_get(info, 'dividendYield'),
            "payout_ratio": safe_get(info, 'payoutRatio'),
        },
    }
    
    # 計算毛利率（從財報中提取）
    try:
        financials = retry_fetch(lambda: t.financials)
        if financials is not None and not financials.empty:
            if 'Gross Profit' in financials.index and 'Total Revenue' in financials.index:
                gross_profit = financials.loc['Gross Profit'].iloc[0]
                total_revenue = financials.loc['Total Revenue'].iloc[0]
                if total_revenue and total_revenue != 0:
                    result["profitability"]["gross_margin"] = round(gross_profit / total_revenue, 4)
    except Exception as e:
        print(f"  ⚠️ Could not calculate gross margin: {e}")
    
    # 計算 FCF（如果沒有直接提供）
    if result["financials"]["free_cashflow"] is None:
        try:
            cf = retry_fetch(lambda: t.cashflow)
            if cf is not None and not cf.empty:
                if 'Free Cash Flow' in cf.index:
                    result["financials"]["free_cashflow"] = cf.loc['Free Cash Flow'].iloc[0]
        except Exception as e:
            print(f"  ⚠️ Could not calculate FCF: {e}")
    
    print(f"  ✅ Basic info fetched successfully")
    return result


def fetch_analyst_consensus(ticker: str) -> Dict[str, Any]:
    """抓取分析師共識"""
    print(f"📈 Fetching analyst consensus for {ticker}...")
    
    t = yf.Ticker(ticker)
    result = {
        "ticker": ticker,
        "fetch_date": datetime.now().isoformat(),
    }
    
    # 1. 推薦分佈
    print("  Fetching recommendations...")
    rec = retry_fetch(lambda: t.recommendations)
    if rec is not None and not rec.empty:
        rec_reset = rec.reset_index()
        recommendations = []
        for idx, row in rec_reset.iterrows():
            recommendations.append({
                "date": str(row.get('Date', '')) if row.get('Date') else None,
                "strongBuy": int(row.get('strongBuy', 0)),
                "buy": int(row.get('buy', 0)),
                "hold": int(row.get('hold', 0)),
                "sell": int(row.get('sell', 0)),
                "strongSell": int(row.get('strongSell', 0)),
            })
        result["recommendations"] = recommendations
        
        # 最新推薦
        if recommendations:
            latest = recommendations[-1]
            total = latest['strongBuy'] + latest['buy'] + latest['hold'] + latest['sell'] + latest['strongSell']
            result["latest_recommendation"] = latest
            result["analyst_count"] = total
            if total > 0:
                bull_pct = round((latest['strongBuy'] + latest['buy']) / total * 100, 1)
                result["bull_bear_ratio"] = {
                    "bull_pct": bull_pct,
                    "bear_pct": round(100 - bull_pct, 1),
                    "total_analysts": total,
                }
    else:
        result["recommendations"] = []
        result["recommendations_error"] = "No data returned"
    
    # 2. 目標價
    print("  Fetching price targets...")
    try:
        tp = t.analyst_price_targets
        if tp:
            result["price_targets"] = {
                "low": tp.get('low'),
                "mean": tp.get('mean'),
                "median": tp.get('median'),
                "high": tp.get('high'),
            }
    except Exception as e:
        result["price_targets_error"] = str(e)
    
    # 3. 升降級歷史
    print("  Fetching upgrades/downgrades...")
    ug = retry_fetch(lambda: t.upgrades_downgrades)
    if ug is not None and not ug.empty:
        ug_reset = ug.reset_index()
        upgrades = []
        for idx, row in ug_reset.iterrows():
            date_val = row.get('Date', '')
            # 嘗試從 index 獲取日期（如果 Date 欄位為空）
            if not date_val and hasattr(ug_reset.index[idx], 'strftime'):
                date_val = ug_reset.index[idx].strftime('%Y-%m-%d')
            
            upgrades.append({
                "date": str(date_val) if date_val else None,
                "firm": str(row.get('Firm', '')),
                "action": str(row.get('Action', '')),
                "from_grade": str(row.get('FromGrade', '')),
                "to_grade": str(row.get('ToGrade', '')),
            })
        result["upgrades_downgrades"] = upgrades
        
        # 統計升降級趨勢（最近 30 天）
        recent_upgrades = [u for u in upgrades if u['action'] == 'up']
        recent_downgrades = [u for u in upgrades if u['action'] == 'down']
        result["upgrade_downgrade_trend"] = {
            "total_upgrades": len(recent_upgrades),
            "total_downgrades": len(recent_downgrades),
            "trend": "bullish" if len(recent_upgrades) > len(recent_downgrades) 
                     else "bearish" if len(recent_downgrades) > len(recent_upgrades)
                     else "neutral",
        }
    else:
        result["upgrades_downgrades"] = []
        result["upgrades_downgrades_error"] = "No data returned"
    
    print(f"  ✅ Analyst consensus fetched")
    return result


def fetch_technical_indicators(ticker: str, period: str = "1y") -> Dict[str, Any]:
    """抓取技術指標（需要 ta 庫）"""
    print(f"📉 Fetching technical indicators for {ticker}...")
    
    try:
        import ta
    except ImportError:
        print("  ⚠️ ta library not installed. Run: pip install ta")
        return {"error": "ta library not installed"}
    
    t = yf.Ticker(ticker)
    hist = retry_fetch(lambda: t.history(period=period))
    
    if hist is None or hist.empty:
        return {"error": "No historical data"}
    
    result = {
        "ticker": ticker,
        "fetch_date": datetime.now().isoformat(),
        "period": period,
    }
    
    # SMA
    for window in [20, 50, 200]:
        sma = ta.trend.SMAIndicator(close=hist['Close'], window=window)
        result[f"sma_{window}"] = round(sma.sma_indicator().iloc[-1], 2)
    
    # EMA
    for window in [12, 26]:
        ema = ta.trend.EMAIndicator(close=hist['Close'], window=window)
        result[f"ema_{window}"] = round(ema.ema_indicator().iloc[-1], 2)
    
    # RSI
    rsi = ta.momentum.RSIIndicator(close=hist['Close'], window=14)
    result["rsi_14"] = round(rsi.rsi().iloc[-1], 2)
    
    # MACD
    macd = ta.trend.MACD(close=hist['Close'])
    result["macd"] = {
        "macd_line": round(macd.macd().iloc[-1], 2),
        "signal_line": round(macd.macd_signal().iloc[-1], 2),
        "histogram": round(macd.macd_diff().iloc[-1], 2),
    }
    
    # Bollinger Bands
    bb = ta.volatility.BollingerBands(close=hist['Close'])
    result["bollinger"] = {
        "upper": round(bb.bollinger_hband().iloc[-1], 2),
        "middle": round(bb.bollinger_mavg().iloc[-1], 2),
        "lower": round(bb.bollinger_lband().iloc[-1], 2),
    }
    
    # Volume stats
    result["volume"] = {
        "current": int(hist['Volume'].iloc[-1]),
        "avg_20d": round(hist['Volume'].tail(20).mean(), 0),
        "avg_50d": round(hist['Volume'].tail(50).mean(), 0),
    }
    
    # 價格位置
    current_price = hist['Close'].iloc[-1]
    result["price_position"] = {
        "current": round(current_price, 2),
        "vs_sma20": round((current_price / result["sma_20"] - 1) * 100, 2),
        "vs_sma50": round((current_price / result["sma_50"] - 1) * 100, 2),
        "vs_sma200": round((current_price / result["sma_200"] - 1) * 100, 2),
    }
    
    print(f"  ✅ Technical indicators fetched")
    return result


def fetch_all(ticker: str, include_technical: bool = False) -> Dict[str, Any]:
    """抓取所有數據"""
    print(f"\n🚀 Fetching all data for {ticker}...")
    print("=" * 50)
    
    result = {
        "ticker": ticker,
        "fetch_date": datetime.now().isoformat(),
        "data_source": "yfinance",
    }
    
    # 1. 基本資訊
    result["basic"] = fetch_basic_info(ticker)
    
    # 2. 分析師共識
    result["analyst"] = fetch_analyst_consensus(ticker)
    
    # 3. 技術指標（可選）
    if include_technical:
        result["technical"] = fetch_technical_indicators(ticker)
    
    print("\n" + "=" * 50)
    print(f"✅ All data fetched for {ticker}")
    
    return result


# ============================================================
# 主程式
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_yahoo.py <TICKER> [--full] [--output <path>]")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    include_technical = "--full" in sys.argv
    
    # 輸出路徑
    output_path = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_path = sys.argv[idx + 1]
    
    if not output_path:
        output_dir = os.path.join(DEFAULT_OUTPUT_DIR, ticker)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "raw.json")
    
    # 抓取數據
    data = fetch_all(ticker, include_technical=include_technical)
    
    # 寫入文件
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📁 Data saved to: {output_path}")
    
    # 打印摘要
    if data.get("basic", {}).get("price", {}).get("current"):
        price = data["basic"]["price"]["current"]
        pe = data["basic"]["valuation"].get("trailing_pe", "N/A")
        fpe = data["basic"]["valuation"].get("forward_pe", "N/A")
        print(f"\n📊 Summary: {ticker} @ ${price}")
        print(f"   P/E: {pe} | Forward P/E: {fpe}")
    
    if data.get("analyst", {}).get("price_targets", {}).get("mean"):
        target = data["analyst"]["price_targets"]["mean"]
        price = data["basic"]["price"]["current"]
        if price and target:
            upside = round((target / price - 1) * 100, 1)
            print(f"   Target: ${target} ({'+' if upside > 0 else ''}{upside}%)")
    
    if data.get("analyst", {}).get("latest_recommendation"):
        rec = data["analyst"]["latest_recommendation"]
        total = rec['strongBuy'] + rec['buy'] + rec['hold'] + rec['sell'] + rec['strongSell']
        bull = rec['strongBuy'] + rec['buy']
        bear = rec['sell'] + rec['strongSell']
        print(f"   Analysts: {bull}B / {rec['hold']}H / {bear}S ({total} total)")


if __name__ == "__main__":
    main()
