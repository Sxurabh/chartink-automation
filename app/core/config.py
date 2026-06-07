# app/core/config.py
import json
import os
from pydantic import BaseModel, Field
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

TABLE_WIDTH = 6
TABLE_GAP = 2
TABLE_STRIDE = TABLE_WIDTH + TABLE_GAP

def col_letter(n):
    n += 1
    result = ""
    while n > 0:
        n -= 1
        result = chr(ord('A') + n % 26) + result
        n //= 26
    return result

class ScannerConfig(BaseModel):
    """Defines the structure for a single ChartInk scanner."""
    name: str
    url: str
    is_ipo: bool = False

def _load_scanners() -> List[ScannerConfig]:
    scanners_file = 'scanners.json'
    if os.path.exists(scanners_file):
        with open(scanners_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [ScannerConfig(**item) for item in data]
    return [
        ScannerConfig(
            name="Monthly stocks for Nifty 100",
            url="https://chartink.com/screener/5ema-monthly-for-nifty-100",
            is_ipo=False
        ),
        ScannerConfig(
            name="Monthly stocks from last 5 years IPO",
            url="https://chartink.com/screener/5ema-monthly-69",
            is_ipo=True
        )
    ]

class Settings(BaseModel):
    """Main application settings."""
    sheet_name: str = Field(default="5 EMA Tracker")
    worksheet_name: str = "Scanned Stocks"
    scanners: List[ScannerConfig] = Field(default_factory=_load_scanners)
    table_headers: List[str] = [
        'Stock Name', 'Symbol', 'Price', 'Volume',
        'Buying Price', 'Stoploss'
    ]
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    max_concurrent_scanners: int = Field(default=4, description="Max scanners to run in parallel")
    proxy_validate_timeout: int = Field(default=3, description="TCP connect timeout in seconds for proxy validation")
    proxy_validate_max: int = Field(default=0, description="Max proxies to validate (0 = all)")
    browser_types: List[str] = Field(default=["firefox", "chromium"], description="Browser engines to randomize across")
    gcp_credentials: Dict = Field(default_factory=dict)

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

def get_settings() -> Settings:
    """
    Initializes and returns the application settings.
    Reads GCP credentials from environment if available.
    """
    gcp_creds_str = os.getenv('GCP_CREDENTIALS')
    gcp_creds_dict = {}
    if gcp_creds_str:
        import json
        gcp_creds_dict = json.loads(gcp_creds_str)

    return Settings(gcp_credentials=gcp_creds_dict)

settings = get_settings()