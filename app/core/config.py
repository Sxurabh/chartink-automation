# app/core/config.py
import os
from pydantic import BaseModel, Field
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class ScannerConfig(BaseModel):
    """Defines the structure for a single ChartInk scanner."""
    name: str
    url: str
    is_ipo: bool = False

class Settings(BaseModel):
    """Main application settings."""
    sheet_name: str = Field(default="Trading Automation")
    scanners: List[ScannerConfig] = [
        ScannerConfig(
            name="Monthly stocks for Nifty 100",
            url="https://chartink.com/screener/5ema-monthly-for-nifty-100",
            is_ipo=False
        ),
        ScannerConfig(
            name="Monthly stocks from last 3 years IPO",
            url="https://chartink.com/screener/5ema-monthly-69",
            is_ipo=True
        )
    ]
    # 👇 Headers remain the same with your new columns
    table_headers: List[str] = [
        'Stock Name', 'Symbol', 'Price', 'Volume',
        'Buying Price', 'Stoploss', 'Status'
    ]
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
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