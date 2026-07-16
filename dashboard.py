import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

TARGET_ETFS = {
    "V60A": "V60A.DE",       
    "VNGA80": "VNGA80.MI",   
    "VWCE": "VWCE.DE"        
}
MACRO_FILTER = "SPY"         

def calculate_macro_regime():
    spy = yf.Ticker(MACRO_FILTER)
    hist = spy.history(period="300d")
    live_price = hist['Close'].iloc[-1]
    ma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
    regime = "BULL" if live_price >= ma_200 else "BEAR"
    return regime, live_price, ma_200

def get_days_to_deadline():
    """Calculate trading days left until TDM -4 (Ultimate Monthly Buy Window)"""
    today = datetime.now()
    # Estimate trading days remaining by excluding weekends roughly
    end_of_month = datetime(today.year, today.month, 1)
    if today.month == 12:
        end_of_month = datetime(today.year + 1, 1, 1)
    else:
        end_of_month = datetime(today.year, today.month + 1, 1)
        
    total_days = pd.date_range(start=today, end=end_of_month, freq='B')
    days_to_deadline = len(total_days) - 4
    return max(0, days_to_deadline)

def generate_etf_metrics(regime, days_left):
    results = []
    for display_name, ticker_symbol in TARGET_ETFS.items():
        etf = yf.Ticker(ticker_symbol)
        hist = etf.history(period="40d")
        if len(hist) < 20: continue
            
        rolling_window = hist.tail(20)
        live_price = rolling_window['Close'].iloc[-1]
        midpoint_20d = rolling_window['Close'].mean()
        std_dev_20d = rolling_window['Close'].std()
        
        if regime == "BULL":
            target_limit = midpoint_20d - (0.5 * std_dev_20d)
        else:
            target_limit = midpoint_20d - (2.0 * std_dev_20d)
            
        z_score = (live_price - midpoint_20d) / std_dev_20d
        
        # Hard Rule: Force execution if time limit has elapsed
        if days_left <= 0:
            action = "🟢 FORCE MARKET BUY NOW (Deadline Reached)"
        elif live_price <= target_limit:
            action = "🟢 TARGET HIT: EXECUTE MARKET BUY"
        else:
            action = f"🎯 SET DAILY LIMIT ORDER AT €{target_limit:.2f}"
            
        results.append({
            "ETF": display_name, "Live Price": f"€{live_price:.2f}", "20D Avg": f"€{midpoint_20d:.2f}",
            "Volatility": f"€{std_dev_20d:.2f}", "Target Limit": f"€{target_limit:.2f}",
            "Z-Score": f"{z_score:.2f}", "Core Action": action
        })
    return pd.DataFrame(results)

if __name__ == "__main__":
    regime, spy_live, spy_ma = calculate_macro_regime()
    days_left = get_days_to_deadline()
    
    # Structure the report string
    report = []
    report.append("=" * 80)
    report.append(f"PALI INSTITUTIONAL EXECUTION MATRICES | {datetime.now().strftime('%d %b %Y %H:%M')}")
    report.append("=" * 80)
    regime_str = "🟢 BULL REGIME (Normal Targets)" if regime == "BULL" else "🔴 BEAR REGIME (Panic Target Cushions Enabled)"
    report.append(f"Macro Trend (SPY): {regime_str}")
    report.append(f"SPY Live Price: ${spy_live:.2f} | SPY 200MA Baseline: ${spy_ma:.2f}")
    report.append(f"Trading Days Remaining to Monthly Deadline Window: {days_left} Days")
    report.append("-" * 80)
    
    df_metrics = generate_etf_metrics(regime, days_left)
    report.append(df_metrics.to_string(index=False))
    report.append("=" * 80)
    
    final_text = "\n".join(report)
    
    # 1. Print output to GitHub logs console
    print(final_text)
    
    # 2. Dump output into a temporary text report file for the email trigger
    with open("email_report.txt", "w", encoding="utf-8") as f:
        f.write(final_text)
