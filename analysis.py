# analysis.py

import yfinance as yf
import json
from typing import Dict, Any
from openai import OpenAI
import config

def gather_data_for_ai(ticker: str) -> Dict[str, Any]:
    """
    Gathers all the raw technical and fundamental data points required by the AI prompts.
    """
    try:
        stock = yf.Ticker(f"{ticker}.NS")
        info = stock.info
        
        hist_monthly = stock.history(period="3y", interval="1mo")
        hist_daily = stock.history(period="3mo", interval="1d")
        
        if len(hist_monthly) < 2:
            return {"ticker": ticker, "error": "Not enough monthly data."}

        last_month = hist_monthly.iloc[-2]
        breakout_candle = hist_monthly.iloc[-1]
        
        hist_monthly['20EMA'] = hist_monthly['Close'].ewm(span=20, adjust=False).mean()
        hist_monthly['50EMA'] = hist_monthly['Close'].ewm(span=50, adjust=False).mean()
        
        avg_volume_20d = hist_daily['Volume'][-20:].mean()
        breakout_volume_ratio = breakout_candle['Volume'] / avg_volume_20d if avg_volume_20d > 0 else 1
        
        data = {
            "ticker": ticker,
            "breakout_confirmation": "intramonth" if breakout_candle['High'] > last_month['High'] else "no",
            "price_vs_20EMA": "above" if breakout_candle['Close'] > hist_monthly['20EMA'].iloc[-1] else "below",
            "price_vs_50EMA": "above" if breakout_candle['Close'] > hist_monthly['50EMA'].iloc[-1] else "below",
            "breakout_volume_ratio": f"{breakout_volume_ratio:.2f}x",
            "revenue_growth_yoy": f"{info.get('revenueGrowth', 0) * 100:.2f}%",
            "roe": f"{info.get('returnOnEquity', 0) * 100:.2f}%",
            "debt_to_equity": info.get('debtToEquity', 'N/A'),
            "operating_cash_flow": info.get('operatingCashflow', 'N/A'),
        }
        if breakout_candle['Close'] > last_month['High']:
            data["breakout_confirmation"] = "monthly_close"
            
        return data

    except Exception:
        return {"ticker": ticker, "error": "Failed to fetch complete data."}


def get_ai_scanned_analysis(ticker_data: Dict[str, Any], api_key: str, custom_prompt: str) -> Dict[str, Any]:
    """
    Calls the OpenRouter API with a custom prompt and data, expecting a JSON response.
    """
    if not api_key:
        return {"error": "API Key Not Provided"}
    
    try:
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        user_message = "\n".join([f"{key}: {value}" for key, value in ticker_data.items()])
        
        completion = client.chat.completions.create(
            model=config.AI_MODEL_NAME,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": custom_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.0,
        )
        response_content = completion.choices[0].message.content
        response_data = json.loads(response_content)

        # --- FIX: Handle both list and dictionary responses from the AI ---
        if isinstance(response_data, list):
            # If AI returns a list as requested, take the first item.
            return response_data[0]
        elif isinstance(response_data, dict):
            # If AI returns a single object, use it directly.
            return response_data
        else:
            return {"ticker": ticker_data.get('ticker'), "error": "Unexpected AI response format."}

    except Exception as e:
        return {"ticker": ticker_data.get('ticker'), "error": f"AI Analysis Failed: {e}"}