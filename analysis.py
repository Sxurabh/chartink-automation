# analysis.py

import yfinance as yf
from typing import Tuple, Dict
from openai import OpenAI
import config

def get_fundamental_analysis(ticker: str) -> Tuple[int, str]:
    """
    Analyzes a stock based on key fundamental metrics and returns a score and reasons string.
    """
    score = 0
    reasons = []
    try:
        stock = yf.Ticker(f"{ticker}.NS")
        info = stock.info

        # Metric 1: Positive Earnings Per Share (EPS)
        if info.get('trailingEps', -1) > 0:
            score += 1
            reasons.append(f"Positive EPS ({info.get('trailingEps', 0):.2f})")
        
        # Metric 2: Reasonable P/E Ratio
        if 0 < info.get('trailingPE', 100) < 40:
            score += 1
            reasons.append(f"Good P/E ({info.get('trailingPE', 0):.2f})")

        # Metric 3: Low Debt to Equity Ratio
        if info.get('debtToEquity', 101) < 100:
            score += 1
            reasons.append(f"Low Debt/Equity ({info.get('debtToEquity', 0)/100:.2f})")

        # Metric 4: High Return on Equity (ROE)
        if info.get('returnOnEquity', 0) > 0.15:
            score += 1
            reasons.append(f"High ROE ({info.get('returnOnEquity', 0):.2%})")

        return score, ", ".join(reasons) if reasons else "No strong fundamentals."

    except Exception:
        return 0, "Data Not Available"

def get_ai_analysis(ticker: str) -> Tuple[str, str]:
    """
    Calls the OpenRouter API to get an AI-generated investment thesis and risk assessment.
    """
    if not config.OPENROUTER_API_KEY:
        return "API Key Not Configured", "API Key Not Configured"
    
    try:
        stock = yf.Ticker(f"{ticker}.NS")
        info = stock.info
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=config.OPENROUTER_API_KEY)
        
        prompt_data = (
            f"Company: {info.get('longName', ticker)}\n"
            f"Sector: {info.get('sector', 'N/A')}\n"
            f"Business Summary: {info.get('longBusinessSummary', 'N/A')}"
        )
        
        completion = client.chat.completions.create(
            model=config.AI_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a sharp financial analyst. Provide a 2-sentence investment thesis, then list the top 2-3 potential risks using bullet points."},
                {"role": "user", "content": prompt_data},
            ],
            temperature=0.6, max_tokens=200
        )
        response = completion.choices[0].message.content
        parts = response.split("Risk")
        thesis = parts[0].strip()
        risks = "Risk" + parts[1].strip() if len(parts) > 1 else "No specific risks identified."
        return thesis, risks
    except Exception as e:
        return f"AI Analysis Failed: {e}", "AI Analysis Failed"