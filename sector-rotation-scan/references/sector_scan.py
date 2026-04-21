"""
Sector Rotation Scan — yfinance data collection template
Returns a DataFrame with sector temperature metrics
"""
import yfinance as yf
import pandas as pd

# Define sectors to scan (customize per user's focus areas)
DEFAULT_SECTORS = {
    # Benchmarks
    "SPY": "S&P 500", "QQQ": "Nasdaq 100", "IWM": "Russell 2000",
    # AI / Semi
    "SMH": "Semi ETF", "NVDA": "NVIDIA", "AVGO": "Broadcom", "AMD": "AMD",
    "MRVL": "Marvell", "TSM": "TSMC", "ASML": "ASML",
    "MU": "Micron (Memory)", "AMAT": "Applied Mat", "LRCX": "Lam Research",
    # Optical
    "AAOI": "AAOI", "LITE": "Lumentum", "COHR": "Coherent",
    # Cloud
    "MSFT": "Microsoft", "GOOG": "Alphabet", "AMZN": "Amazon", "META": "Meta",
    # Energy
    "XLE": "Energy ETF", "XOM": "Exxon", "CVX": "Chevron",
    # Metals
    "GLD": "Gold ETF", "SLV": "Silver ETF",
    # Financials
    "XLF": "Financials ETF", "JPM": "JPMorgan",
}

def scan_sectors(sectors=None):
    if sectors is None:
        sectors = DEFAULT_SECTORS
    
    results = []
    for ticker, name in sectors.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="6mo")
            if len(hist) < 10:
                continue
            
            current = hist['Close'].iloc[-1]
            w1 = hist['Close'].iloc[-5] if len(hist) >= 5 else current
            m1 = hist['Close'].iloc[-22] if len(hist) >= 22 else current
            m3 = hist['Close'].iloc[-66] if len(hist) >= 66 else hist['Close'].iloc[0]
            
            y1 = t.history(period="1y")
            h52 = y1['High'].max()
            l52 = y1['Low'].min()
            
            vol_5d = hist['Volume'].iloc[-5:].mean()
            vol_20d = hist['Volume'].iloc[-20:].mean()
            vol_ratio = vol_5d / vol_20d if vol_20d > 0 else 1
            
            # Get fundamentals
            info = t.info
            fwd_pe = info.get('forwardPE', None)
            peg = info.get('pegRatio', None)
            rev_growth = info.get('revenueGrowth', None)
            margin = info.get('profitMargins', None)
            
            results.append({
                "Ticker": ticker, "Name": name, "Price": round(current, 2),
                "1W%": round((current/w1-1)*100, 1),
                "1M%": round((current/m1-1)*100, 1),
                "3M%": round((current/m3-1)*100, 1),
                "%From52H": round((current/h52-1)*100, 1),
                "%From52L": round((current/l52-1)*100, 1),
                "VolRatio": round(vol_ratio, 2),
                "FwdPE": round(fwd_pe, 1) if fwd_pe else None,
                "PEG": round(peg, 2) if peg else None,
                "RevGrowth": round(rev_growth*100, 1) if rev_growth else None,
                "Margin": round(margin*100, 1) if margin else None,
            })
        except Exception:
            pass
    
    return pd.DataFrame(results)

def classify_temperature(pct_from_52h):
    if pct_from_52h > -5: return "HOT"
    elif pct_from_52h > -15: return "WARM"
    elif pct_from_52h > -25: return "COOL"
    else: return "COLD"

if __name__ == "__main__":
    df = scan_sectors()
    df['Temp'] = df['%From52H'].apply(classify_temperature)
    print(df.sort_values('%From52H', ascending=False).to_string(index=False))
