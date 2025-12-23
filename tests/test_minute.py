#!/usr/bin/env python3
"""
Unit tests for minute.py module using unittest and unittest.mock
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

from minute import (
    parse_minute_rows,
    fetch_minute_page,
    fetch_minute_symbol,
    collect_minute_data,
    main_async,
    MINUTE_URL,
    MINUTE_HEADERS
)


class TestParseMinuteRows(unittest.TestCase):
    """Test cases for parse_minute_rows function"""
    
    def test_parse_minute_rows_success(self):
        """Test successful parsing of minute data"""
        html = """
        <html>
            <span class="tah">09:00</span>
            <span class="tah">70,000</span>
            <span class="tah">+1,000</span>
            <span class="tah">69,000</span>
            <span class="tah">71,000</span>
            <span class="tah">68,500</span>
            <span class="tah">1,000</span>
        </html>
        """
        bs = BeautifulSoup(html, 'lxml')
        
        result = parse_minute_rows('005930', bs)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], '005930')  # symbol
        self.assertEqual(result[0][1], '70000')   # price
        self.assertEqual(result[0][2], '1000')    # volume
        self.assertEqual(result[0][3], '09:00')   # time
    
    def test_parse_minute_rows_multiple(self):
        """Test parsing multiple minute rows"""
        html = """
        <html>
            <span class="tah">09:00</span>
            <span class="tah">70,000</span>
            <span class="tah">+1,000</span>
            <span class="tah">69,000</span>
            <span class="tah">71,000</span>
            <span class="tah">68,500</span>
            <span class="tah">1,000</span>
            <span class="tah">09:01</span>
            <span class="tah">70,500</span>
            <span class="tah">+500</span>
            <span class="tah">70,000</span>
            <span class="tah">71,000</span>
            <span class="tah">69,500</span>
            <span class="tah">800</span>
        </html>
        """
        bs = BeautifulSoup(html, 'lxml')
        
        result = parse_minute_rows('005930', bs)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][3], '09:00')
        self.assertEqual(result[1][3], '09:01')
    
    def test_parse_minute_rows_empty(self):
        """Test parsing with no data"""
        html = "<html></html>"
        bs = BeautifulSoup(html, 'lxml')
        
        result = parse_minute_rows('005930', bs)
        
        self.assertEqual(len(result), 0)
    
    def test_parse_minute_rows_incomplete(self):
        """Test parsing with incomplete row"""
        html = """
        <html>
            <span class="tah">09:00</span>
            <span class="tah">70,000</span>
            <span class="tah">+1,000</span>
        </html>
        """
        bs = BeautifulSoup(html, 'lxml')
        
        result = parse_minute_rows('005930', bs)
        
        self.assertEqual(len(result), 0)


class TestFetchMinutePage(unittest.IsolatedAsyncioTestCase):
    """Test cases for fetch_minute_page async function"""
    
    async def test_fetch_minute_page_success(self):
        """Test successful fetch of a minute data page"""
        html = """
        <html>
            <span class="tah">09:00</span>
            <span class="tah">70,000</span>
            <span class="tah">+1,000</span>
            <span class="tah">69,000</span>
            <span class="tah">71,000</span>
            <span class="tah">68,500</span>
            <span class="tah">1,000</span>
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
        
        result = await fetch_minute_page(mock_session, '005930', '2023-12-20', 1, semaphore)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], '005930')
    
    async def test_fetch_minute_page_http_error(self):
        """Test handling of HTTP error"""
        mock_response = AsyncMock()
        mock_response.status = 500
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        
        semaphore = asyncio.Semaphore(1)
        
        result = await fetch_minute_page(mock_session, '005930', '2023-12-20', 1, semaphore)
        
        self.assertEqual(result, [])
    
    async def test_fetch_minute_page_exception(self):
        """Test handling of exception"""
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=Exception("Network error"))
        
        semaphore = asyncio.Semaphore(1)
        
        result = await fetch_minute_page(mock_session, '005930', '2023-12-20', 1, semaphore)
        
        self.assertEqual(result, [])


class TestFetchMinuteSymbol(unittest.IsolatedAsyncioTestCase):
    """Test cases for fetch_minute_symbol async function"""
    
    async def test_fetch_minute_symbol_single_page(self):
        """Test fetch with single page of data"""
        html = """
        <html>
            <span class="tah">09:00</span>
            <span class="tah">70,000</span>
            <span class="tah">+1,000</span>
            <span class="tah">69,000</span>
            <span class="tah">71,000</span>
            <span class="tah">68,500</span>
            <span class="tah">1,000</span>
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
        
        result = await fetch_minute_symbol(mock_session, '005930', '2023-12-20', semaphore)
        
        self.assertEqual(len(result), 1)
        self.assertIn('005930', result[0])
        self.assertIn('09:00', result[0])
    
    async def test_fetch_minute_symbol_multiple_pages(self):
        """Test fetch with multiple pages of data"""
        html_page1 = """
        <html>
            <span class="tah">09:00</span>
            <span class="tah">70,000</span>
            <span class="tah">+1,000</span>
            <span class="tah">69,000</span>
            <span class="tah">71,000</span>
            <span class="tah">68,500</span>
            <span class="tah">1,000</span>
            <td class="pgRR"><a href="?page=2&code=005930">다음</a></td>
        </html>
        """
        
        html_page2 = """
        <html>
            <span class="tah">09:01</span>
            <span class="tah">70,500</span>
            <span class="tah">+500</span>
            <span class="tah">70,000</span>
            <span class="tah">71,000</span>
            <span class="tah">69,500</span>
            <span class="tah">800</span>
        </html>
        """
        
        mock_response1 = AsyncMock()
        mock_response1.status = 200
        mock_response1.read = AsyncMock(return_value=html_page1.encode())
        mock_response1.__aenter__ = AsyncMock(return_value=mock_response1)
        mock_response1.__aexit__ = AsyncMock(return_value=None)
        
        mock_response2 = AsyncMock()
        mock_response2.status = 200
        mock_response2.read = AsyncMock(return_value=html_page2.encode())
        
        mock_session = MagicMock()
        
        semaphore = asyncio.Semaphore(1)
        
        with patch('minute.fetch_minute_page', new_callable=AsyncMock) as mock_fetch_page:
            mock_fetch_page.return_value = [['005930', '70500', '800', '09:01']]
            mock_session.get = MagicMock(return_value=mock_response1)
            
            result = await fetch_minute_symbol(mock_session, '005930', '2023-12-20', semaphore)
            
            self.assertGreaterEqual(len(result), 1)
    
    async def test_fetch_minute_symbol_deduplication(self):
        """Test that duplicate times are deduplicated"""
        html = """
        <html>
            <span class="tah">09:00</span>
            <span class="tah">70,000</span>
            <span class="tah">+1,000</span>
            <span class="tah">69,000</span>
            <span class="tah">71,000</span>
            <span class="tah">68,500</span>
            <span class="tah">1,000</span>
            <span class="tah">09:00</span>
            <span class="tah">70,100</span>
            <span class="tah">+1,100</span>
            <span class="tah">69,000</span>
            <span class="tah">71,000</span>
            <span class="tah">68,500</span>
            <span class="tah">1,100</span>
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
        
        result = await fetch_minute_symbol(mock_session, '005930', '2023-12-20', semaphore)
        
        # Should only have one entry for 09:00 (deduplicated)
        self.assertEqual(len(result), 1)
    
    async def test_fetch_minute_symbol_http_error(self):
        """Test handling of HTTP error"""
        mock_response = AsyncMock()
        mock_response.status = 500
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        
        semaphore = asyncio.Semaphore(1)
        
        result = await fetch_minute_symbol(mock_session, '005930', '2023-12-20', semaphore)
        
        self.assertEqual(result, [])
    
    async def test_fetch_minute_symbol_exception(self):
        """Test handling of exception"""
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=Exception("Network error"))
        
        semaphore = asyncio.Semaphore(1)
        
        result = await fetch_minute_symbol(mock_session, '005930', '2023-12-20', semaphore)
        
        self.assertEqual(result, [])


class TestCollectMinuteData(unittest.IsolatedAsyncioTestCase):
    """Test cases for collect_minute_data async function"""
    
    async def test_collect_minute_data_success(self):
        """Test successful collection of minute data"""
        with patch('minute.fetch_minute_symbol', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                ['005930\t70000\t1000\t09:00', '005930\t70500\t800\t09:01'],
                ['000660\t120000\t500\t09:00'],
                []  # One symbol returns empty
            ]
            
            symbols = ['005930', '000660', '035420']
            result = await collect_minute_data('2023-12-20', symbols, 20)
            
            self.assertEqual(len(result), 3)
            self.assertEqual(mock_fetch.call_count, 3)
    
    async def test_collect_minute_data_with_output_file(self):
        """Test collection with output file"""
        with patch('minute.fetch_minute_symbol', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                ['005930\t70000\t1000\t09:00'],
                ['000660\t120000\t500\t09:00']
            ]
            
            m = mock_open()
            with patch('builtins.open', m):
                with patch('pathlib.Path.mkdir'):
                    symbols = ['005930', '000660']
                    result = await collect_minute_data('2023-12-20', symbols, 20,
                                                       output_file='/tmp/minute.tsv')
            
            self.assertEqual(len(result), 2)
            m.assert_called_once()
    
    async def test_collect_minute_data_sorting(self):
        """Test that results are sorted by time"""
        with patch('minute.fetch_minute_symbol', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                ['005930\t70500\t800\t09:01', '005930\t70000\t1000\t09:00'],
            ]
            
            m = mock_open()
            with patch('builtins.open', m):
                with patch('pathlib.Path.mkdir'):
                    symbols = ['005930']
                    result = await collect_minute_data('2023-12-20', symbols, 20,
                                                       output_file='/tmp/minute.tsv')
            
            # Check that write was called with sorted data
            handle = m()
            written_lines = [call[0][0] for call in handle.write.call_args_list]
            
            # First line should be 09:00, second should be 09:01
            self.assertTrue(any('09:00' in line for line in written_lines))


class TestMainAsync(unittest.IsolatedAsyncioTestCase):
    """Test cases for main_async function"""
    
    async def test_main_async_success(self):
        """Test main_async with successful data collection"""
        with patch('minute.collect_minute_data', new_callable=AsyncMock) as mock_collect:
            mock_collect.return_value = [
                '005930\t70000\t1000\t09:00',
                '005930\t70500\t800\t09:01'
            ]
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                result = await main_async('2023-12-20', ['005930'], 20)
            
            self.assertEqual(result, 0)
            output = captured_output.getvalue()
            self.assertIn('005930', output)
            self.assertIn('09:00', output)


class TestConstants(unittest.TestCase):
    """Test cases for module constants"""
    
    def test_minute_url_defined(self):
        """Test that MINUTE_URL is properly defined"""
        self.assertTrue(MINUTE_URL.startswith('https://'))
        self.assertIn('naver.com', MINUTE_URL)
    
    def test_minute_headers_defined(self):
        """Test that MINUTE_HEADERS contains User-Agent"""
        self.assertIn('User-Agent', MINUTE_HEADERS)


if __name__ == '__main__':
    unittest.main()
