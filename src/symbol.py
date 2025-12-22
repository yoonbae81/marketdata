#!/usr/bin/env python3
"""
Symbol collection module for KRX market data.
Fetches stock symbols from KOSPI and KOSDAQ markets.
"""

import argparse
import asyncio
import aiohttp
import json
import sys
from datetime import datetime


SYMBOL_URLS = [
    'https://finance.daum.net/api/quotes/stocks?market=KOSPI',
    'https://finance.daum.net/api/quotes/stocks?market=KOSDAQ'
]

SYMBOL_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    'referer': 'https://finance.daum.net/domestic/all_quotes',
}


def parse_symbols(res_text):
    """Parse symbol data from API response"""
    data = json.loads(res_text)['data']
    symbols = []
    for item in data:
        symbol = item['code'][3:9]
        symbols.append(symbol)
    return symbols


async def fetch_symbols():
    """Fetch all symbols from KOSPI and KOSDAQ"""
    print('[INFO] Fetching symbols...', file=sys.stderr)
    all_symbols = []
    
    async with aiohttp.ClientSession() as session:
        for url in SYMBOL_URLS:
            try:
                async with session.get(url, headers=SYMBOL_HEADERS, timeout=10) as response:
                    if response.status != 200:
                        print(f'[ERROR] HTTP Status Code {response.status}', file=sys.stderr)
                        continue
                    
                    text = await response.text()
                    symbols = parse_symbols(text)
                    all_symbols.extend(symbols)
            except Exception as e:
                print(f'[ERROR] Failed to fetch symbols from {url}: {e}', file=sys.stderr)
    
    print(f'[INFO] Found {len(all_symbols)} symbols', file=sys.stderr)
    return all_symbols


async def main_async():
    """Main async entry point"""
    symbols = await fetch_symbols()
    if not symbols:
        print('[ERROR] No symbols found', file=sys.stderr)
        return 1
    
    # Output symbols to stdout (one per line)
    for symbol in symbols:
        print(symbol)
    
    return 0


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Fetch KRX stock symbols')
    args = parser.parse_args()
    
    try:
        exit_code = asyncio.run(main_async())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print('\n[INFO] Interrupted by user', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'[ERROR] Unexpected error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
