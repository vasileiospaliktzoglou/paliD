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
    today = datetime.now()
    if today.month == 12:
        end_of_month = datetime(today.year + 1, 1, 1)
    else:
        end_of_month = datetime(today.year, today.month + 1, 1)
    total_days = pd.date_range(start=today, end=end_of_month, freq='B')
    return max(0, len(total_days) - 4)

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
        
        today_session = hist.iloc[-1]
        daily_low = today_session['Low']
        daily_high = today_session['High']
        
        if regime == "BULL":
            target_limit = midpoint_20d - (0.5 * std_dev_20d)
        else:
            target_limit = midpoint_20d - (2.0 * std_dev_20d)
            
        z_score = (live_price - midpoint_20d) / std_dev_20d
        
        # New Feature 3: Calculate direct distance to target metrics
        dist_euro = live_price - target_limit
        dist_pct = (dist_euro / live_price) * 100
        
        # New Feature 1: Momentum Gap-Down Protection Warning
        momentum_warning = ""
        if z_score < -1.5:
            momentum_warning = ' <span class="warn-badge">⚠️ HEAVY MOMENTUM CRASH</span>'
        
        if days_left <= 0:
            action = "🟢 FORCE MARKET BUY NOW"
            color_class = "buy-now"
        elif live_price <= target_limit:
            action = "🟢 TARGET HIT: MARKET BUY"
            color_class = "buy-now"
        else:
            action = f"🎯 SET DAILY LIMIT AT €{target_limit:.2f}"
            color_class = "set-limit"
            
        results.append({
            "ETF": display_name, "Price": f"€{live_price:.2f}", "Avg": f"€{midpoint_20d:.2f}",
            "DailyLow": f"€{daily_low:.2f}", "DailyHigh": f"€{daily_high:.2f}",
            "Target": f"€{target_limit:.2f}", "Distance": f"€{dist_euro:.2f} ({dist_pct:.2f}%)",
            "ZScore": f"{z_score:.2f}", "Action": action + momentum_warning, "Class": color_class
        })
    return results

if __name__ == "__main__":
    regime, spy_live, spy_ma = calculate_macro_regime()
    days_left = get_days_to_deadline()
    metrics = generate_etf_metrics(regime, days_left)
    
    regime_text = "🟢 BULL REGIME (Normal Targets)" if regime == "BULL" else "🔴 BEAR REGIME (Panic Protections Active)"
    regime_class = "bull-banner" if regime == "BULL" else "bear-banner"
    
    table_rows = ""
    for m in metrics:
        table_rows += f"""
        <tr>
            <td><strong>{m['ETF']}</strong></td>
            <td>{m['Price']}</td>
            <td><span class="range-text-low">{m['DailyLow']}</span></td>
            <td><span class="range-text-high">{m['DailyHigh']}</span></td>
            <td>{m['Avg']}</td>
            <td><strong>{m['Target']}</strong></td>
            <td>{m['Distance']}</td>
            <td>{m['ZScore']}</td>
            <td><span class="badge {m['Class']}">{m['Action']}</span></td>
        </tr>
        """
        
    html_content = f"""<!DOCTYPE html>
    <html>
    <head>
        <title>PALI Execute Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: 'Segoe UI', system-ui, sans-serif; background-color: #f8f9fa; color: #212529; padding: 20px; }}
            .container {{ max-width: 1150px; margin: 0 auto; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            .header-flex {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 5px; }}
            h1 {{ font-size: 24px; margin: 0; color: #1e293b; }}
            .refresh-btn {{ background-color: #1a73e8; color: white; text-decoration: none; padding: 8px 16px; border-radius: 4px; font-weight: 600; font-size: 13px; }}
            .refresh-btn:hover {{ background-color: #1557b0; }}
            .meta {{ font-size: 14px; color: #64748b; margin-bottom: 20px; margin-top: 10px; }}
            .banner {{ padding: 12px 15px; border-radius: 6px; font-weight: bold; margin-bottom: 25px; }}
            .bull-banner {{ background-color: #e6f4ea; color: #137333; }}
            .bear-banner {{ background-color: #fce8e6; color: #c5221f; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
            th {{ background-color: #f1f5f9; color: #475569; font-weight: 600; }}
            .badge {{ padding: 6px 12px; border-radius: 4px; font-weight: 600; font-size: 13px; display: inline-block; }}
            .buy-now {{ background-color: #e6f4ea; color: #137333; }}
            .set-limit {{ background-color: #e8f0fe; color: #1a73e8; }}
            .warn-badge {{ background-color: #fff0f6; color: #c41d7f; border: 1px solid #ffadd2; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-left: 5px; }}
            .range-text-low {{ color: #b45309; font-weight: 500; }}
            .range-text-high {{ color: #0369a1; font-weight: 500; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-flex">
                <h1>PALI ETF Execution Dashboard v2.4</h1>
                <a href="https://github.com" target="_blank" class="refresh-btn">⚡ FORCE LIVE REFRESH</a>
            </div>
            <div class="meta">Last Updated: {datetime.now().strftime('%d %b %Y %H:%M')} CET | Monthly Deadline Status: <strong>{days_left} Trading Days Left</strong></div>
            <div class="banner {regime_class}">Macro Market Trend (SPY Filter): {regime_text}</div>
            <table>
                <thead>
                    <tr>
                        <th>ETF</th>
                        <th>Live Price</th>
                        <th>Daily Low</th>
                        <th>Daily High</th>
                        <th>20D Midpoint</th>
                        <th>Target Limit Price</th>
                        <th>Distance to Target</th>
                        <th>Z-Score</th>
                        <th>Core Execution Action</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Dashboard version 2.4 compiled successfully.")
