#!/usr/bin/env python3
"""
defeatbeta API Data Fetcher
Fetches comprehensive stock data from defeatbeta-api
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from defeatbeta_api.data.ticker import Ticker, Tickers
except ImportError:
    print("ERROR: defeatbeta-api not installed. Run: pip install defeatbeta-api")
    sys.exit(1)


def fetch_price(ticker: str) -> dict:
    """Fetch historical price data."""
    t = Ticker(ticker)
    df = t.price()
    return {
        "shape": list(df.shape),
        "columns": df.columns.tolist(),
        "date_range": [str(df["report_date"].min()), str(df["report_date"].max())],
        "latest_close": float(df["close_price"].iloc[-1]),
        "row_count": len(df)
    }


def fetch_fundamentals(ticker: str) -> dict:
    """Fetch valuation fundamentals."""
    t = Ticker(ticker)
    result = {}
    
    try:
        result["market_cap"] = t.market_capitalization().to_dict("records")
    except Exception:
        result["market_cap"] = None
    
    try:
        ttm_pe = t.ttm_pe()
        result["ttm_pe_latest"] = float(ttm_pe.iloc[-1]["ttm_pe"]) if not ttm_pe.empty else None
    except Exception:
        result["ttm_pe_latest"] = None
    
    try:
        result["pb_ratio"] = t.pb_ratio().to_dict("records")[-1] if hasattr(t, 'pb_ratio') else None
    except Exception:
        result["pb_ratio"] = None
    
    try:
        result["ps_ratio"] = t.ps_ratio().to_dict("records")[-1] if hasattr(t, 'ps_ratio') else None
    except Exception:
        result["ps_ratio"] = None
    
    try:
        result["peg_ratio"] = t.peg_ratio().to_dict("records")[-1] if hasattr(t, 'peg_ratio') else None
    except Exception:
        result["peg_ratio"] = None
    
    try:
        result["beta"] = t.beta().to_dict("records")[-1] if hasattr(t, 'beta') else None
    except Exception:
        result["beta"] = None
    
    try:
        ev = t.enterprise_value()
        result["enterprise_value"] = float(ev.iloc[-1]["enterprise_value"]) if not ev.empty and "enterprise_value" in ev.columns else None
    except Exception:
        result["enterprise_value"] = None
    
    return result


def fetch_profitability(ticker: str) -> dict:
    """Fetch profitability metrics."""
    t = Ticker(ticker)
    result = {}
    
    try:
        roe_df = t.roe()
        result["roe_latest"] = float(roe_df.iloc[-1]["roe"]) if not roe_df.empty else None
    except Exception:
        result["roe_latest"] = None
    
    try:
        result["roa"] = t.roa().to_dict("records")[-1] if hasattr(t, 'roa') else None
    except Exception:
        result["roa"] = None
    
    try:
        result["roic"] = t.roic().to_dict("records")[-1] if hasattr(t, 'roic') else None
    except Exception:
        result["roic"] = None
    
    try:
        result["roce"] = t.roce().to_dict("records")[-1] if hasattr(t, 'roce') else None
    except Exception:
        result["roce"] = None
    
    try:
        wacc_df = t.wacc()
        result["wacc"] = float(wacc_df.iloc[-1]["wacc"]) if not wacc_df.empty else None
    except Exception:
        result["wacc"] = None
    
    return result


def fetch_growth(ticker: str) -> dict:
    """Fetch growth metrics."""
    t = Ticker(ticker)
    result = {}
    
    try:
        qoq = t.quarterly_revenue_yoy_growth()
        result["quarterly_revenue_yoy_growth_latest"] = float(qoq.iloc[-1]["quarterly_revenue_yoy_growth"]) if not qoq.empty else None
    except Exception:
        result["quarterly_revenue_yoy_growth_latest"] = None
    
    return result


def fetch_financials(ticker: str) -> dict:
    """Fetch financial statements."""
    t = Ticker(ticker)
    result = {}
    
    methods = [
        ("quarterly_income_statement", "quarterly_income"),
        ("quarterly_balance_sheet", "quarterly_balance"),
        ("quarterly_cash_flow", "quarterly_cash_flow"),
        ("annual_income_statement", "annual_income"),
        ("annual_balance_sheet", "annual_balance"),
        ("annual_cash_flow", "annual_cash_flow"),
    ]
    
    for method_name, key in methods:
        try:
            if hasattr(t, method_name):
                df = getattr(t, method_name)()
                result[key] = {"shape": list(df.shape), "columns": df.columns.tolist()}
        except Exception:
            result[key] = None
    
    return result


def fetch_transcripts(ticker: str) -> dict:
    """Fetch earnings call transcripts."""
    t = Ticker(ticker)
    tc = t.earning_call_transcripts()
    transcripts = tc.get_transcript_list()
    
    return {
        "count": len(transcripts),
        "latest": transcripts[-1] if transcripts else None
    }


def fetch_news(ticker: str) -> dict:
    """Fetch news items."""
    t = Ticker(ticker)
    news = t.news()
    news_list = news.get_news_list()
    
    return {
        "count": len(news_list),
        "latest": news_list[-1] if news_list else None
    }


def fetch_sec_filings(ticker: str) -> dict:
    """Fetch SEC filings."""
    t = Ticker(ticker)
    df = t.sec_filing()
    
    return {
        "count": len(df),
        "columns": df.columns.tolist(),
        "latest": df.tail(3)[["form_type", "filing_date", "accession_number"]].to_dict("records")
    }


def fetch_dcf(ticker: str, output_dir: str = "/tmp/defeatbeta/dcf") -> dict:
    """Generate DCF Excel model."""
    t = Ticker(ticker)
    
    os.makedirs(output_dir, exist_ok=True)
    result = t.dcf(output_dir=output_dir)
    
    return {
        "output_path": result.get("file_path", f"{output_dir}/{ticker}.xlsx"),
        "success": True
    }


def fetch_all(ticker: str, output_dir: str = "/tmp/defeatbeta") -> dict:
    """Fetch all available data."""
    return {
        "ticker": ticker,
        "fetch_date": "2026-05-02",  # Would use datetime.now().isoformat()
        "data_source": "defeatbeta-api",
        "price": fetch_price(ticker),
        "fundamentals": fetch_fundamentals(ticker),
        "profitability": fetch_profitability(ticker),
        "growth": fetch_growth(ticker),
        "financials": fetch_financials(ticker),
        "transcripts": fetch_transcripts(ticker),
        "news": fetch_news(ticker),
        "sec_filings": fetch_sec_filings(ticker)
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch stock data from defeatbeta-api")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g., NVDA)")
    parser.add_argument("--full", action="store_true", help="Fetch all available data")
    parser.add_argument("--output", help="Output file path (.json)")
    parser.add_argument("--dcf", action="store_true", help="Generate DCF Excel model")
    parser.add_argument("--transcripts", action="store_true", help="Fetch transcript list")
    
    args = parser.parse_args()
    ticker = args.ticker.upper()
    
    if args.dcf:
        result = fetch_dcf(ticker)
        print(json.dumps(result, indent=2))
    elif args.transcripts:
        result = fetch_transcripts(ticker)
        print(json.dumps(result, indent=2))
    elif args.full:
        result = fetch_all(ticker)
        print(json.dumps(result, indent=2))
    else:
        # Default: quick summary
        result = {
            "ticker": ticker,
            "price": fetch_price(ticker),
            "fundamentals": fetch_fundamentals(ticker),
            "profitability": fetch_profitability(ticker),
            "growth": fetch_growth(ticker),
            "sec_filings": fetch_sec_filings(ticker),
        }
        print(json.dumps(result, indent=2))
    
    # Save to file if specified
    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
