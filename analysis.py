# analysis.py

import yfinance as yf
from typing import List, Dict, Any
import config

def get_fundamental_score(ticker: str) -> (int, List[str]):
    """
    Analyzes a stock based on key fundamental metrics and returns a score and reasons.
    """
    score = 0
    reasons = []
    try:
        stock = yf.Ticker(f"{ticker}.NS")
        info = stock.info

        # --- Metric 1: Positive Earnings Per Share (EPS) ---
        trailing_eps = info.get('trailingEps')
        if trailing_eps is not None and trailing_eps > 0:
            score += 1
            reasons.append(f"Positive EPS ({trailing_eps:.2f})")
        
        # --- Metric 2: Reasonable P/E Ratio ---
        pe_ratio = info.get('trailingPE')
        if pe_ratio is not None and 0 < pe_ratio < 40:
            score += 1
            reasons.append(f"Good P/E Ratio ({pe_ratio:.2f})")

        # --- Metric 3: Low Debt to Equity Ratio ---
        debt_to_equity = info.get('debtToEquity')
        if debt_to_equity is not None and debt_to_equity < 100: # d/e is often in percent
            score += 1
            reasons.append(f"Low Debt/Equity ({debt_to_equity/100:.2f})")

        # --- Metric 4: High Return on Equity (ROE) ---
        roe = info.get('returnOnEquity')
        if roe is not None and roe > 0.15:
            score += 1
            reasons.append(f"High ROE ({roe:.2%})")

        return score, reasons

    except Exception:
        # Happens if data is not available for a ticker
        return 0, ["Data Not Available"]

def analyze_and_rank_stocks(scraped_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes a list of stocks, scores them, and returns them ranked.
    """
    scanner_name = config.SCANNER_MAPPING.get(scraped_data['url'], scraped_data['url'])
    print(f"\n🔬 Performing fundamental analysis on {len(scraped_data['data'])} stocks from '{scanner_name}'...")
    
    analyzed_stocks = []
    
    # Add new columns for the analysis results
    headers = scraped_data['headers'] + ["Fundamental Score", "Reasons"]

    for row in scraped_data['data']:
        symbol_index = 2 
        if len(row) > symbol_index:
            symbol = row[symbol_index]
            score, reasons = get_fundamental_score(symbol)
            
            if reasons:
                # Add score and reasons to the row
                row_with_analysis = row + [score, ", ".join(reasons)]
                analyzed_stocks.append(row_with_analysis)
                print(f"  - Analyzed {symbol}: Score {score}")

    # Sort the stocks by score in descending order
    analyzed_stocks.sort(key=lambda x: x[len(headers)-2], reverse=True)

    print(f"  ✅ Analysis complete for '{scanner_name}'.")
    return {"url": scraped_data['url'], "headers": headers, "data": analyzed_stocks}