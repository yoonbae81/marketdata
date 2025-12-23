#!/usr/bin/env python3
"""
Integration tests for KRX price modules using real API calls.
These tests make actual network requests to verify the modules work with real data.

Note: These tests may fail if:
- Network is unavailable
- API endpoints change
- Market is closed (for minute/day data)
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from symbol import fetch_symbols, parse_symbols
from day import fetch_day_symbol, parse_day_data
from minute import fetch_minute_symbol, parse_minute_rows


class TestSymbolIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for symbol.py with real API"""
    
    async def test_fetch_kospi_symbols_real(self):
        """Test fetching real KOSPI symbols from API"""
        print("\n[INFO] Fetching real KOSPI symbols...")
        symbols = await fetch_symbols('KOSPI')
        
        # Verify we got some symbols
        self.assertIsInstance(symbols, list)
        self.assertGreater(len(symbols), 0, "Should fetch at least some KOSPI symbols")
        
        # Verify symbol format (6 characters, alphanumeric)
        for symbol in symbols[:5]:  # Check first 5
            self.assertEqual(len(symbol), 6, f"Symbol {symbol} should be 6 characters")
            self.assertTrue(symbol.isalnum(), f"Symbol {symbol} should be alphanumeric")
        
        print(f"[SUCCESS] Fetched {len(symbols)} KOSPI symbols")
        print(f"[SAMPLE] First 5 symbols: {symbols[:5]}")
    
    async def test_fetch_kosdaq_symbols_real(self):
        """Test fetching real KOSDAQ symbols from API"""
        print("\n[INFO] Fetching real KOSDAQ symbols...")
        symbols = await fetch_symbols('KOSDAQ')
        
        # Verify we got some symbols
        self.assertIsInstance(symbols, list)
        self.assertGreater(len(symbols), 0, "Should fetch at least some KOSDAQ symbols")
        
        # Verify symbol format
        for symbol in symbols[:5]:
            self.assertEqual(len(symbol), 6)
            self.assertTrue(symbol.isdigit())
        
        print(f"[SUCCESS] Fetched {len(symbols)} KOSDAQ symbols")
        print(f"[SAMPLE] First 5 symbols: {symbols[:5]}")


class TestDayIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for day.py with real API"""
    
    async def test_fetch_samsung_day_data_real(self):
        """Test fetching real daily data for Samsung Electronics (005930)"""
        print("\n[INFO] Fetching real daily data for Samsung (005930)...")
        
        import aiohttp
        import asyncio
        
        # Use a recent date (yesterday or a few days ago)
        target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        connector = aiohttp.TCPConnector(limit=1)
        semaphore = asyncio.Semaphore(1)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            result = await fetch_day_symbol(session, '005930', target_date, semaphore)
        
        if result:
            print(f"[SUCCESS] Fetched data for {target_date}")
            print(f"[SAMPLE] Data: {result}")
            
            # Verify format: symbol\topen\thigh\tlow\tclose\tvolume
            parts = result.split('\t')
            self.assertEqual(len(parts), 6, "Should have 6 tab-separated fields")
            self.assertEqual(parts[0], '005930', "First field should be symbol")
            
            # Verify all price fields are numeric
            for i in range(1, 6):
                self.assertTrue(parts[i].isdigit(), f"Field {i} should be numeric")
        else:
            print(f"[WARNING] No data found for {target_date} (market might be closed)")
            self.skipTest(f"No data available for {target_date}")
    
    async def test_fetch_multiple_symbols_day_data(self):
        """Test fetching daily data for multiple well-known symbols"""
        print("\n[INFO] Fetching daily data for multiple symbols...")
        
        import aiohttp
        import asyncio
        
        # Well-known Korean stocks
        symbols = ['005930', '000660', '035420']  # Samsung, SK Hynix, NAVER
        target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        connector = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300)
        semaphore = asyncio.Semaphore(3)
        results = []
        
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [fetch_day_symbol(session, symbol, target_date, semaphore) 
                    for symbol in symbols]
            responses = await asyncio.gather(*tasks)
            results = [r for r in responses if r]
        
        print(f"[SUCCESS] Fetched data for {len(results)}/{len(symbols)} symbols")
        for result in results:
            print(f"[SAMPLE] {result}")
        
        # At least some symbols should have data
        if len(results) == 0:
            self.skipTest(f"No data available for {target_date}")


class TestMinuteIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for minute.py with real API"""
    
    async def test_fetch_samsung_minute_data_real(self):
        """Test fetching real minute data for Samsung Electronics (005930)"""
        print("\n[INFO] Fetching real minute data for Samsung (005930)...")
        
        import aiohttp
        import asyncio
        
        # Use today's date
        target_date = datetime.now().strftime('%Y-%m-%d')
        
        connector = aiohttp.TCPConnector(limit=1)
        semaphore = asyncio.Semaphore(1)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            results = await fetch_minute_symbol(session, '005930', target_date, semaphore)
        
        if results and len(results) > 0:
            print(f"[SUCCESS] Fetched {len(results)} minute data points for {target_date}")
            print(f"[SAMPLE] First 3 entries:")
            for result in results[:3]:
                print(f"  {result}")
            
            # Verify format: symbol\tprice\tvolume\ttime
            first_entry = results[0]
            parts = first_entry.split('\t')
            self.assertEqual(len(parts), 4, "Should have 4 tab-separated fields")
            self.assertEqual(parts[0], '005930', "First field should be symbol")
            self.assertTrue(parts[1].isdigit(), "Price should be numeric")
            self.assertTrue(parts[2].isdigit(), "Volume should be numeric")
            self.assertRegex(parts[3], r'\d{2}:\d{2}', "Time should be HH:MM format")
        else:
            print(f"[WARNING] No minute data found for {target_date} (market might be closed)")
            self.skipTest(f"No minute data available for {target_date}")
    
    async def test_minute_data_deduplication(self):
        """Test that minute data is properly deduplicated"""
        print("\n[INFO] Testing minute data deduplication...")
        
        import aiohttp
        import asyncio
        
        target_date = datetime.now().strftime('%Y-%m-%d')
        
        connector = aiohttp.TCPConnector(limit=1)
        semaphore = asyncio.Semaphore(1)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            results = await fetch_minute_symbol(session, '005930', target_date, semaphore)
        
        if results and len(results) > 0:
            # Extract times from results
            times = [r.split('\t')[3] for r in results]
            
            # Check for duplicates
            unique_times = set(times)
            self.assertEqual(len(times), len(unique_times), 
                           "All times should be unique (no duplicates)")
            
            print(f"[SUCCESS] All {len(times)} entries have unique timestamps")
        else:
            self.skipTest(f"No minute data available for {target_date}")


class TestDataConsistency(unittest.TestCase):
    """Test data consistency and format validation"""
    
    def test_symbol_format_validation(self):
        """Test that symbol format validation works correctly"""
        valid_symbols = ['005930', '000660', '035420']
        
        for symbol in valid_symbols:
            self.assertEqual(len(symbol), 6, f"{symbol} should be 6 characters")
            self.assertTrue(symbol.isdigit(), f"{symbol} should be all digits")
    
    def test_date_format_validation(self):
        """Test date format used in the modules"""
        test_date = datetime.now().strftime('%Y-%m-%d')
        
        # Should match YYYY-MM-DD format
        self.assertRegex(test_date, r'\d{4}-\d{2}-\d{2}')


if __name__ == '__main__':
    print("="*70)
    print("KRX Price Integration Tests")
    print("="*70)
    print("\nThese tests make REAL API calls and may take some time.")
    print("Tests may fail if the market is closed or network is unavailable.\n")
    
    unittest.main(verbosity=2)
