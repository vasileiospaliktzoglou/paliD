import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# 1. Configuration & Tickers
TARGET_ETFS = {
    "V60A": "V60A.DE",       # Vanguard LifeStrategy 60% (XETR)
    "VNGA80": "VNGA80.MI",   # Vanguard LifeStrategy 80% (Borsa Italiana)
    "VWCE": "VWCE.DE"        # Vanguard FTSE All-World (XETR)
}
MACRO_FILTER = "SPY"         # S&P 500 ETF for broad market trend

def calculate_macro_regime():
    """Tier 1: Check if market is above or below its 200-day Moving Average"""
    spy = yf.Ticker(MACRO_FILTER)
    # Fetch 300 days of data to safely calculate a 200-day MA
    hist = spy.history(period="300d")
    
    live_price = hist['Close'].iloc[-1]
    ma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
    
    regime = "BULL" if live_price >= ma_200 else "BEAR"
    return regime, live_price, ma_200

def generate_etf_metrics(regime):
    """Tier 2: Calculate rolling 20-day volatility and targets"""
    results = []
    
    for display_name, ticker_symbol in TARGET_ETFS.items():
        etf = yf.Ticker(ticker_symbol)
        # Fetch 40 days to isolate a clean rolling 20-trading-day window
        hist = etf.history(period="40d")
        
        if len(hist) < 20:
            continue
            
        rolling_window = hist.tail(20)
        live_price = rolling_window['Close'].iloc[-1]
        midpoint_20d = rolling_window['Close'].mean()
        std_dev_20d = rolling_window['Close'].std()
        
        # Calculate dynamic volatility-adjusted targets based on Macro Regime
        if regime == "BULL":
            target_limit = midpoint_20d - (0.5 * std_dev_20d)
        else:
            # Bear Market Panic Mode: Target the Lower Bollinger Band
            target_limit = midpoint_20d - (2.0 * std_dev_20d)
            
        z_score = (live_price - midpoint_20d) / std_dev_20d
        
        # Binary Action Engine
        if live_price <= target_limit:
            action = "🟢 EXECUTE MARKET BUY NOW"
        else:
            action = f"🎯 SET DAILY LIMIT ORDER AT €{target_limit:.2f}"
            
        results.append({
            "ETF": display_name,
            "Live Price": f"€{live_price:.2f}",
            "20D Avg": f"€{midpoint_20d:.2f}",
            "Volatility": f"€{std_dev_20d:.2f}",
            "Target Limit": f"€{target_limit:.2f}",
            "Z-Score": f"{z_score:.2f}",
            "Core Action": action
        })
        
    return pd.DataFrame(results)

if __name__ == "__main__":
    print("=" * 70)
    print(f"PALI INSTITUTIONAL EXECUTION ENGINE v2.0 | {datetime.now().strftime('%d %b %Y %H:%M')}")
    print("=" * 70)
    
    # Run Macro Filter
    regime, spy_live, spy_ma = calculate_macro_regime()
    regime_str = "🟢 BULL REGIME (Normal Targets)" if regime == "BULL" else "🔴 BEAR REGIME (Panic Protection Active)"
    print(f"Macro Trend (SPY): {regime_str}")
    print(f"SPY Live: ${spy_live:.2f} | SPY 200MA: ${spy_ma:.2f}")
    print("-" * 70)
    
    # Run Dashboard Metrics
    df_dashboard = generate_etf_metrics(regime)
    print(df_dashboard.to_string(index=False))
    print("=" * 70)
