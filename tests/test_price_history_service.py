# tests/test_price_history_service.py

import unittest
from unittest.mock import patch
import pandas as pd

# We assume tests are run from the project's root directory.
from app.services.price_history_service import PriceHistoryService

class TestPriceHistoryService(unittest.TestCase):

    def setUp(self):
        """Set up a fresh instance of the service for each test."""
        self.service = PriceHistoryService()

    @patch('yfinance.Ticker')
    def test_get_last_month_ohl_success(self, mock_ticker):
        """Test successful retrieval of OHLC data."""
        mock_instance = mock_ticker.return_value
        mock_df = pd.DataFrame({
            'High': [110, 115, 112],
            'Low': [100, 105, 98]
        })
        mock_instance.history.return_value = mock_df

        result = self.service.get_last_month_ohl("RELIANCE")
        
        self.assertIsNotNone(result)
        self.assertEqual(result, (115.0, 98.0))
        mock_ticker.assert_called_with("RELIANCE.NS", session=self.service.session)
        mock_instance.history.assert_called_once()

    @patch('yfinance.Ticker')
    def test_get_last_month_ohl_empty_dataframe(self, mock_ticker):
        """Test the case where yfinance returns an empty DataFrame."""
        mock_instance = mock_ticker.return_value
        mock_instance.history.return_value = pd.DataFrame()

        result = self.service.get_last_month_ohl("FAKESYMBOL")

        self.assertIsNone(result)
        self.assertEqual(mock_instance.history.call_count, 2)

    @patch('yfinance.Ticker')
    def test_get_last_month_ohl_exception(self, mock_ticker):
        """Test the case where yfinance throws an exception."""
        mock_instance = mock_ticker.return_value
        mock_instance.history.side_effect = Exception("Yahoo Finance is down")

        result = self.service.get_last_month_ohl("ERRORSYMBOL")

        self.assertIsNone(result)
        self.assertEqual(mock_instance.history.call_count, 2)

    @patch('yfinance.Ticker')
    def test_symbol_cleaning(self, mock_ticker):
        """Test if the symbol is cleaned correctly."""
        self.service.get_last_month_ohl("M&M")
        mock_ticker.assert_called_with("M-M.NS", session=self.service.session)

if __name__ == '__main__':
    unittest.main()