# test_yfinance_monthly.py
import yfinance as yf
from datetime import datetime

def run_monthly_test():
    """
    Test script for monthly candle high/low of RELIANCE.NS (last month)
    """
    print("--- Running yfinance Monthly Candle Test for RELIANCE ---\n")
    
    try:
        # Fetch monthly data
        ticker = yf.Ticker("RELIANCE.NS")
        df = ticker.history(period="6mo", interval="1mo")  # Get 6 months for context
        
        if not df.empty:
            print(f"✅ Monthly data fetched: {len(df)} candles from {df.index[0].strftime('%b %Y')} to {df.index[-1].strftime('%b %Y')}\n")
            
            # Get the last monthly candle (September 2025)
            last_candle = df.iloc[-1]  # Last row is most recent month
            
            high = last_candle['High']
            low = last_candle['Low']
            open_price = last_candle['Open']
            close = last_candle['Close']
            month_name = last_candle.name.strftime('%B %Y')
            
            print(f"✅ Last Monthly Candle: {month_name}")
            print(f"  Open:  ₹{open_price:.2f}")
            print(f"  High:  ₹{high:.2f}")
            print(f"  Low:   ₹{low:.2f}")
            print(f"  Close: ₹{close:.2f}")
            
            # Return just high and low as tuple (for service-like usage)
            ohl_result = (high, low)
            print(f"\nService-style result: {ohl_result}")
            
            # Show recent 3 monthly candles for context
            print(f"\nRecent 3 Monthly Candles:")
            print(df[['Open', 'High', 'Low', 'Close']].tail(3))
        else:
            print("❌ No monthly data returned")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}\n")
        print("Ensure: pip install --upgrade yfinance")
        
    print("\n--- Monthly Test Finished ---")


if __name__ == "__main__":
    run_monthly_test()
