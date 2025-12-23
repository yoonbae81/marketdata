#!/usr/bin/env python3
"""
Unit tests for symbol.py module using unittest and unittest.mock
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio
import json
import sys
import os
from io import StringIO

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from symbol import (
    parse_symbols,
    fetch_symbols,
    main_async,
    SYMBOL_URLS,
    SYMBOL_HEADERS
)


class TestParseSymbols(unittest.TestCase):
    """Test cases for parse_symbols function"""
    
    def test_parse_symbols_success(self):
        """Test successful parsing of symbol data"""
        mock_response = json.dumps({
            'data': [
                {'code': 'KR7005930003', 'name': '삼성전자'},
                {'code': 'KR7000660001', 'name': 'SK하이닉스'},
                {'code': 'KR7035420009', 'name': 'NAVER'}
            ]
        })
        
        result = parse_symbols(mock_response)
        
        self.assertEqual(len(result), 3)
        self.assertIn('005930', result)
        self.assertIn('000660', result)
        self.assertIn('035420', result)
    
    def test_parse_symbols_empty_data(self):
        """Test parsing with empty data"""
        mock_response = json.dumps({'data': []})
        
        result = parse_symbols(mock_response)
        
        self.assertEqual(len(result), 0)
        self.assertEqual(result, [])
    
    def test_parse_symbols_single_item(self):
        """Test parsing with single symbol"""
        mock_response = json.dumps({
            'data': [
                {'code': 'KR7005930003', 'name': '삼성전자'}
            ]
        })
        
        result = parse_symbols(mock_response)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], '005930')


class TestFetchSymbols(unittest.IsolatedAsyncioTestCase):
    """Test cases for fetch_symbols async function"""
    
    async def test_fetch_symbols_kospi_success(self):
        """Test successful KOSPI symbol fetch"""
        mock_response_text = json.dumps({
            'data': [
                {'code': 'KR7005930003', 'name': '삼성전자'},
                {'code': 'KR7000660001', 'name': 'SK하이닉스'}
            ]
        })
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=mock_response_text)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('symbol.aiohttp.ClientSession', return_value=mock_session):
            result = await fetch_symbols('KOSPI')
        
        self.assertEqual(len(result), 2)
        self.assertIn('005930', result)
        self.assertIn('000660', result)
    
    async def test_fetch_symbols_kosdaq_success(self):
        """Test successful KOSDAQ symbol fetch"""
        mock_response_text = json.dumps({
            'data': [
                {'code': 'KR7035420009', 'name': 'NAVER'}
            ]
        })
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=mock_response_text)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('symbol.aiohttp.ClientSession', return_value=mock_session):
            result = await fetch_symbols('KOSDAQ')
        
        self.assertEqual(len(result), 1)
        self.assertIn('035420', result)
    
    async def test_fetch_symbols_http_error(self):
        """Test handling of HTTP error response"""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('symbol.aiohttp.ClientSession', return_value=mock_session):
            result = await fetch_symbols('KOSPI')
        
        self.assertEqual(result, [])
    
    async def test_fetch_symbols_unknown_market(self):
        """Test handling of unknown market"""
        result = await fetch_symbols('UNKNOWN')
        
        self.assertEqual(result, [])
    
    async def test_fetch_symbols_network_exception(self):
        """Test handling of network exception"""
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=Exception("Network error"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('symbol.aiohttp.ClientSession', return_value=mock_session):
            result = await fetch_symbols('KOSPI')
        
        self.assertEqual(result, [])


class TestMainAsync(unittest.IsolatedAsyncioTestCase):
    """Test cases for main_async function"""
    
    async def test_main_async_specific_market(self):
        """Test main_async with specific market"""
        with patch('symbol.fetch_symbols', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = ['005930', '000660']
            
            # Capture stdout
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                result = await main_async('KOSPI')
            
            self.assertEqual(result, 0)
            mock_fetch.assert_called_once_with('KOSPI')
            
            output = captured_output.getvalue()
            self.assertIn('005930', output)
            self.assertIn('000660', output)
    
    async def test_main_async_all_markets(self):
        """Test main_async with all markets"""
        with patch('symbol.fetch_symbols', new_callable=AsyncMock) as mock_fetch:
            # Mock different returns for KOSPI and KOSDAQ
            mock_fetch.side_effect = [
                ['005930', '000660'],  # KOSPI
                ['035420']  # KOSDAQ
            ]
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                result = await main_async(None)
            
            self.assertEqual(result, 0)
            self.assertEqual(mock_fetch.call_count, 2)
            
            output = captured_output.getvalue()
            self.assertIn('005930', output)
            self.assertIn('000660', output)
            self.assertIn('035420', output)
    
    async def test_main_async_no_symbols_found(self):
        """Test main_async when no symbols are found"""
        with patch('symbol.fetch_symbols', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            
            result = await main_async('KOSPI')
            
            self.assertEqual(result, 1)
    
    async def test_main_async_all_markets_no_symbols(self):
        """Test main_async with all markets returning no symbols"""
        with patch('symbol.fetch_symbols', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [[], []]  # Both markets return empty
            
            result = await main_async(None)
            
            self.assertEqual(result, 1)


class TestConstants(unittest.TestCase):
    """Test cases for module constants"""
    
    def test_symbol_urls_defined(self):
        """Test that SYMBOL_URLS contains required markets"""
        self.assertIn('KOSPI', SYMBOL_URLS)
        self.assertIn('KOSDAQ', SYMBOL_URLS)
        self.assertTrue(SYMBOL_URLS['KOSPI'].startswith('https://'))
        self.assertTrue(SYMBOL_URLS['KOSDAQ'].startswith('https://'))
    
    def test_symbol_headers_defined(self):
        """Test that SYMBOL_HEADERS contains required headers"""
        self.assertIn('user-agent', SYMBOL_HEADERS)
        self.assertIn('referer', SYMBOL_HEADERS)


if __name__ == '__main__':
    unittest.main()
