import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime

# ==========================================
# ⚙️ CONFIGURATION ZONE
# ==========================================
TARGET_ETFS = {
    "V60A": "V60A.DE",       # Vanguard LifeStrategy 60% (XETR)
    "VNGA80": "VNGA80.MI",   # Vanguard LifeStrategy 80% (Borsa Italiana)
    "VWCE": "VWCE.DE"        # Vanguard FTSE All-World (XETR)
}
MACRO_FILTER = "SPY"         # S&P 500 ETF for global regime checks

# Set your strict day of the month to force deployment (e.g., 24th)
MONTHLY_DEADLINE_DAY = 24  
# ==========================================

def calculate_macro_regime():
    """Tier 1: Verify macro health against the 200-day Simple Moving Average"""
    spy = yf.Ticker(MACRO_FILTER)
    hist = spy.history(period="300d")
    live_price = hist['Close'].iloc[-1]
    ma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
    regime = "BULL" if live_price >= ma_200 else "BEAR"
    return regime, live_price, ma_200

def generate_etf_metrics(regime):
    """Tier 2: Run volatility bounds and apply the time-deadline override"""
    results = []
    today = datetime.now()
    
    # Check if deadline rule is active
    is_deadline_passed = today.day >= MONTHLY_DEADLINE_DAY

    for display_name, ticker_symbol in TARGET_ETFS.items():
        etf = yf.Ticker(ticker_symbol)
        hist = etf.history(period="40d")
        if len(hist) < 20:
            continue
            
        rolling_window = hist.tail(20)
        live_price = rolling_window['Close'].iloc[-1]
        midpoint_20d = rolling_window['Close'].mean()
        std_dev_20d = rolling_window['Close'].std()
        
        # Volatility boundary settings
        if regime == "BULL":
            target_limit = midpoint_20d - (0.5 * std_dev_20d)
        else:
            target_limit = midpoint_20d - (2.0 * std_dev_20d) # Bear panic boundary
            
        z_score = (live_price - midpoint_20d) / std_dev_20d
        
        # Operational Action Engine + Time Catch Override
        if is_deadline_passed:
            action = "🟢 FORCE MARKET BUY NOW (Deadline Reached)"
        elif live_price <= target_limit:
            action = "🟢 TARGET HIT: EXECUTE MARKET BUY NOW"
        else:
            action = f"🎯 SET DAILY LIMIT ORDER AT €{target_limit:.2f}"
            
        results.append({
            "Date": today.strftime('%Y-%m-%d'),
            "ETF": display_name,
            "Live Price": round(live_price, 2),
            "20D Avg": round(midpoint_20d, 2),
            "Volatility": round(std_dev_20d, 2),
            "Target Limit": round(target_limit, 2),
            "Z-Score": round(z_score, 2),
            "Core Action": action
        })
        
    return pd.DataFrame(results), is_deadline_passed

def log_results_to_csv(df_metrics):
    """Maintain a historical CSV database log inside the GitHub Repo"""
    log_file = "execution_log.csv"
    
    # Isolate relevant columns to build an institutional database log
    log_df = df_metrics[["Date", "ETF", "Live Price", "Target Limit", "Z-Score", "Core Action"]]
    
    if not os.path.exists(log_file):
        log_df.to_csv(log_file, index=False)
    else:
        log_df.to_csv(log_file, mode='a', header=False, index=False)
    print(f"✅ Success: Daily records saved and logged to {log_file}")

if __name__ == "__main__":
    print("=" * 75)
    print(f"PALI INSTITUTIONAL EXECUTION ENGINE v2.1 | {datetime.now().strftime('%d %b %Y %H:%M')}")
    print("=" * 75)
    
    regime, spy_live, spy_ma = calculate_macro_regime()
    regime_str = "🟢 BULL REGIME (Normal Targets)" if regime == "BULL" else "🔴 BEAR REGIME (Panic Protection Active)"
    print(f"Macro Trend (SPY): {regime_str}")
    print(f"SPY Live: ${spy_live:.2f} | SPY 200MA: ${spy_ma:.2f}")
    print("-" * 75)
    
    df_dashboard, deadline_flag = generate_etf_metrics(regime)
    print(df_dashboard[["ETF", "Live Price", "20D Avg", "Volatility", "Target Limit", "Z-Score", "Core Action"]].to_string(index=False))
    print("=" * 75)
    
    # Save results to tracking file
    log_results_to_csv(df_dashboard)
    print("=" * 75)
