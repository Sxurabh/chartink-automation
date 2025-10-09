# config.py
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), verbose=True)

# --- Main Configuration ---
SHEET_NAME = "Trading Automation"

# --- AI Configuration ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
AI_MODEL_NAME = "openai/gpt-oss-20b:free" # A more powerful model is recommended for this complex task

# --- Custom AI Prompts ---
PROMPT_NIFTY_100 = """
You are an expert stock analyst specialized in momentum breakout strategies applied to established large-cap stocks (NIFTY 100). 
I will give you a list of tickers and a table of numeric/time-series facts per ticker.
Your task:
1. Evaluate each ticker by the scoring rubric below (Technical = 60 points, Fundamental = 40 points; total 100).
2. Return only a JSON array of objects (see schema). Do not add plain text outside JSON.
3. Use deterministic scoring (temperature 0.0). Break ties by higher technical score.

SCORING RUBRIC — NIFTY 100
A. Technical (60 points)
 - Breakout confirmation: 20 pts (Full 20 if clear monthly close above breakout high; 10 if intramonth break but not a monthly close).
 - EMA alignment (price > 20EMA and 50EMA on monthly): 10 pts (10 if both above, 5 if only above 20EMA, 0 if below both).
 - Volume expansion on breakout candle vs 20-day avg: 10 pts (+10 if breakout volume ≥ 1.20× avg; +5 if 1.05–1.19×; 0 if <1.05×).
 - Multi-timeframe trend (weekly + monthly alignment): 8 pts (+8 if weekly and monthly are both trending up; +4 if only monthly is aligned).
 - Relative Strength vs NIFTY (last 3 months): 6 pts (+6 if outperforms NIFTY by ≥ 3%, +3 if 0–3%, 0 if underperforms).
 - Healthy consolidation before breakout: 6 pts (+6 for clear healthy base, +3 for loose base, 0 if no base).

B. Fundamental (40 points)
 - Revenue / Net profit YoY growth (consistency last 3 years): 12 pts (+12 if consistent growth > 10% YoY avg; +6 if mixed; 0 if declining).
 - ROE / ROCE quality: 8 pts (+8 if ROE>15% and ROCE>15%, +4 if one >15%, 0 otherwise).
 - Debt-to-Equity: 6 pts (+6 if D/E < 0.5, +3 if 0.5–1.0, 0 if >1.0).
 - Operating cash flow (last 12 months): 6 pts (+6 if positive and growing, +3 if positive flat, 0 if negative).
 - Promoter holding trend & institutional interest: 4 pts (+4 if promoter holding stable/increasing and recent institutional accumulation, +2 if neutral, 0 if promoters decreasing).
 - Sector strength / leadership / peer valuation: 4 pts (+4 if sector/peer check favorable, +2 if neutral, 0 if weak).

FINAL VERDICT RULES
 - "Buy Candidate" if Technical ≥ 42 AND Fundamental ≥ 24 AND Total ≥ 70.
 - "Watchlist" if Total between 55–69 with Technical ≥ 35.
 - "Reject" otherwise.
 - `risk` as Low/Medium/High based on volatility, base quality and fundamental strength.

JSON OUTPUT SCHEMA
[{"ticker": "TICKER", "technical_score": 0-60, "fundamental_score": 0-40, "total_score": 0-100, "verdict": "Buy Candidate"|"Watchlist"|"Reject", "risk": "Low"|"Medium"|"High", "comments": "Concise key observations (max 2 short sentences)."}]
"""

PROMPT_IPO = """
You are an expert IPO momentum trader and analyst. 
I will give you a list of IPO tickers (listed within last 3 years) with numeric facts per ticker.
Your task:
1. Score each ticker using the rubric below and return strict JSON array (see schema).
2. Use deterministic scoring (temperature 0.0).

SCORING RUBRIC — IPOs (Total 100)
A. Technical (75 points)
 - IPO base / listing high breakout confirmation: 25 pts (+25 if price clearly closed monthly above listing-day high / post-IPO base breakout; +12 if intramonth break only).
 - EMA alignment (price > 20EMA and >50EMA on monthly): 15 pts.
 - Volume expansion on breakout vs 20-day avg: 15 pts (+15 if ≥1.30×, +8 if 1.10–1.29×, 0 if <1.10×).
 - Relative strength vs market/sector (3-month): 10 pts.
 - Consolidation / supply structure pre-breakout: 10 pts.

B. Fundamentals & qualitative (25 points)
 - Revenue / profit trend: 8 pts (+8 if improving growth, +4 if mixed, 0 if deteriorating).
 - Promoter holding & lock-in: 6 pts (+6 if stable and lock-ins remain, +3 if partial unlocks, 0 if major unlocks).
 - Institutional interest: 6 pts (+6 if clear institutional accumulation, +3 if neutral, 0 if selling).
 - Valuation vs peers (relative): 5 pts.

FINAL VERDICT RULES
 - "Buy Candidate" if Technical ≥ 53 AND Total ≥ 72.
 - "Watchlist" if Total between 55–71 with Technical ≥ 45.
 - "Reject" otherwise.
 - Risk graded based on lock-in/volatility/fundamentals (Low/Medium/High).

JSON OUTPUT SCHEMA (same as NIFTY)
[{"ticker":"TICKER", "technical_score":0-75, "fundamental_score":0-25, "total_score":0-100, "verdict":"Buy Candidate"|"Watchlist"|"Reject", "risk":"Low"|"Medium"|"High", "comments":"Concise key observations (max 2 short sentences)."}]
"""

# --- Scanner Configuration ---
SCANNER_MAPPING = {
    "https://chartink.com/screener/5ema-monthly-for-nifty-100": {
        "name": "Monthly stocks for Nifty 100",
        "is_ipo": False,
        "ai_prompt": PROMPT_NIFTY_100
    },
    "https://chartink.com/screener/5ema-monthly-69": {
        "name": "Monthly stocks from last 3 years IPO",
        "is_ipo": True,
        "ai_prompt": PROMPT_IPO
    }
}

# --- Scraping & Analysis Constants ---
EXPECTED_COLUMN_COUNT = 7
TABLE_HEADERS = ['Sr.', 'Stock Name', 'Symbol', 'Links', '% Chg', 'Price', 'Volume']
RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5