#!/usr/bin/env python3
"""
Unit tests for day.py module using unittest and unittest.mock
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock, MagicMock, mock_open
import asyncio
import sys
import os
from io import StringIO
from bs4 import BeautifulSoup

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from day import (
    parse_day_data,
    fetch_day_symbol,
    collect_day_data,
    main_async,
    DAY_URL,
    DAY_HEADERS
)


class TestParseDayData(unittest.TestCase):
    """Test cases for parse_day_data function"""
    
    def test_parse_day_data_success(self):
        """Test successful parsing of daily data"""
        html = """
        <html>
            <span class="tah">2023-12-20</span>
            <span class="tah">70,000</span>
            <span class="tah">+1,000</span>
            <span class="tah">69,000</span>
            <span class="tah">71,000</span>
            <span class="tah">68,500</span>
            <span class="tah">1,000,000</span>
        </html>
        """
        bs = BeautifulSoup(html, 'lxml')
        
        result = list(parse_day_data(bs))
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['date'], '2023-12-20')
        self.assertEqual(result[0]['close'], '70000')
        self.assertEqual(result[0]['open'], '69000')
        self.assertEqual(result[0]['high'], '71000')
        self.assertEqual(result[0]['low'], '68500')
        self.assertEqual(result[0]['volume'], '1000000')
    
    def test_parse_day_data_multiple_rows(self):
        """Test parsing multiple rows of data"""
        html = """
        <html>
            <span class="tah">2023-12-20</span>
            <span class="tah">70,000</span>
            <span class="tah">+1,000</span>
            <span class="tah">69,000</span>
            <span class="tah">71,000</span>
            <span class="tah">68,500</span>
            <span class="tah">1,000,000</span>
            <span class="tah">2023-12-19</span>
            <span class="tah">69,000</span>
            <span class="tah">-500</span>
            <span class="tah">68,500</span>
            <span class="tah">69,500</span>
            <span class="tah">68,000</span>
            <span class="tah">900,000</span>
        </html>
        """
        bs = BeautifulSoup(html, 'lxml')
        
        result = list(parse_day_data(bs))
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['date'], '2023-12-20')
        self.assertEqual(result[1]['date'], '2023-12-19')
    
    def test_parse_day_data_empty(self):
        """Test parsing with no data"""
        html = "<html></html>"
        bs = BeautifulSoup(html, 'lxml')
        
        result = list(parse_day_data(bs))
        
        self.assertEqual(len(result), 0)
    
    def test_parse_day_data_incomplete_row(self):
        """Test parsing with incomplete row (less than 7 fields)"""
        html = """
        <html>
            <span class="tah">2023-12-20</span>
            <span class="tah">70,000</span>
            <span class="tah">+1,000</span>
        </html>
        """
        bs = BeautifulSoup(html, 'lxml')
        
        result = list(parse_day_data(bs))
        
        self.assertEqual(len(result), 0)


class TestFetchDaySymbol(unittest.IsolatedAsyncioTestCase):
    """Test cases for fetch_day_symbol async function"""
    
    async def test_fetch_day_symbol_success(self):
        """Test successful fetch of daily data for a symbol"""
        html = """
        <html>
            <span class="tah">2023-12-20</span>
            <span class="tah">70,000</span>
            <span class="tah">+1,000</span>
            <span class="tah">69,000</span>
            <span class="tah">71,000</span>
            <span class="tah">68,500</span>
            <span class="tah">1,000,000</span>
        </html>
        """
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=html.encode())
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        
        semaphore = asyncio.Semaphore(1)
        
        result = await fetch_day_symbol(mock_session, '005930', '2023-12-20', semaphore)
        
        self.assertIsNotNone(result)
        self.assertIn('005930', result)
        self.assertIn('69000', result)  # open
        self.assertIn('71000', result)  # high
        self.assertIn('68500', result)  # low
        self.assertIn('70000', result)  # close
        self.assertIn('1000000', result)  # volume
    
    async def test_fetch_day_symbol_date_not_found(self):
        """Test when requested date is not in the data"""
        html = """
        <html>
            <span class="tah">2023-12-19</span>
            <span class="tah">70,000</span>
            <span class="tah">+1,000</span>
            <span class="tah">69,000</span>
            <span class="tah">71,000</span>
            <span class="tah">68,500</span>
            <span class="tah">1,000,000</span>
        </html>
        """
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=html.encode())
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        
        semaphore = asyncio.Semaphore(1)
        
        result = await fetch_day_symbol(mock_session, '005930', '2023-12-20', semaphore)
        
        self.assertIsNone(result)
    
    async def test_fetch_day_symbol_open_is_zero(self):
        """Test when open price is 0 (should be filtered out)"""
        html = """
        <html>
            <span class="tah">2023-12-20</span>
            <span class="tah">70,000</span>
            <span class="tah">+1,000</span>
            <span class="tah">0</span>
            <span class="tah">71,000</span>
            <span class="tah">68,500</span>
            <span class="tah">1,000,000</span>
        </html>
        """
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=html.encode())
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        
        semaphore = asyncio.Semaphore(1)
        
        result = await fetch_day_symbol(mock_session, '005930', '2023-12-20', semaphore)
        
        self.assertIsNone(result)
    
    async def test_fetch_day_symbol_http_error(self):
        """Test handling of HTTP error"""
        mock_response = AsyncMock()
        mock_response.status = 500
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        
        semaphore = asyncio.Semaphore(1)
        
        result = await fetch_day_symbol(mock_session, '005930', '2023-12-20', semaphore)
        
        self.assertIsNone(result)
    
    async def test_fetch_day_symbol_exception(self):
        """Test handling of exception during fetch"""
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=Exception("Network error"))
        
        semaphore = asyncio.Semaphore(1)
        
        result = await fetch_day_symbol(mock_session, '005930', '2023-12-20', semaphore)
        
        self.assertIsNone(result)


class TestCollectDayData(unittest.IsolatedAsyncioTestCase):
    """Test cases for collect_day_data async function"""
    
    async def test_collect_day_data_success(self):
        """Test successful collection of day data"""
        with patch('day.fetch_day_symbol', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                '005930\t69000\t71000\t68500\t70000\t1000000',
                '000660\t120000\t125000\t119000\t123000\t500000',
                None  # One symbol returns None
            ]
            
            symbols = ['005930', '000660', '035420']
            result = await collect_day_data('2023-12-20', symbols, 20)
            
            self.assertEqual(len(result), 2)
            self.assertEqual(mock_fetch.call_count, 3)
    
    async def test_collect_day_data_with_output_file(self):
        """Test collection with output file"""
        with patch('day.fetch_day_symbol', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                '005930\t69000\t71000\t68500\t70000\t1000000',
                '000660\t120000\t125000\t119000\t123000\t500000'
            ]
            
            m = mock_open()
            with patch('builtins.open', m):
                with patch('pathlib.Path.mkdir'):
                    symbols = ['005930', '000660']
                    result = await collect_day_data('2023-12-20', symbols, 20, 
                                                    output_file='/tmp/day.tsv')
            
            self.assertEqual(len(result), 2)
            m.assert_called_once()
    
    async def test_collect_day_data_empty_results(self):
        """Test when all symbols return None"""
        with patch('day.fetch_day_symbol', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            
            symbols = ['005930', '000660']
            result = await collect_day_data('2023-12-20', symbols, 20)
            
            self.assertEqual(len(result), 0)


class TestMainAsync(unittest.IsolatedAsyncioTestCase):
    """Test cases for main_async function"""
    
    async def test_main_async_success(self):
        """Test main_async with successful data collection"""
        with patch('day.collect_day_data', new_callable=AsyncMock) as mock_collect:
            mock_collect.return_value = [
                '005930\t69000\t71000\t68500\t70000\t1000000',
                '000660\t120000\t125000\t119000\t123000\t500000'
            ]
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                result = await main_async('2023-12-20', ['005930', '000660'], 20)
            
            self.assertEqual(result, 0)
            output = captured_output.getvalue()
            self.assertIn('005930', output)
            self.assertIn('000660', output)


class TestConstants(unittest.TestCase):
    """Test cases for module constants"""
    
    def test_day_url_defined(self):
        """Test that DAY_URL is properly defined"""
        self.assertTrue(DAY_URL.startswith('https://'))
        self.assertIn('naver.com', DAY_URL)
    
    def test_day_headers_defined(self):
        """Test that DAY_HEADERS contains User-Agent"""
        self.assertIn('User-Agent', DAY_HEADERS)


if __name__ == '__main__':
    unittest.main()
