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
import os

SYMBOL_URLS = {
    'KOSPI': 'https://finance.daum.net/api/quotes/stocks?market=KOSPI',
    'KOSDAQ': 'https://finance.daum.net/api/quotes/stocks?market=KOSDAQ'
}

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


async def fetch_symbols(market='KOSPI'):
    """Fetch symbols from specific market (KOSPI or KOSDAQ)"""
    print(f'[INFO] Fetching {market} symbols...', file=sys.stderr)
    
    url = SYMBOL_URLS.get(market)
    if not url:
        print(f'[ERROR] Unknown market: {market}', file=sys.stderr)
        return []
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=SYMBOL_HEADERS, timeout=10) as response:
                if response.status != 200:
                    print(f'[ERROR] HTTP Status Code {response.status}', file=sys.stderr)
                    return []
                
                text = await response.text()
                symbols = parse_symbols(text)
                print(f'[INFO] Found {len(symbols)} {market} symbols', file=sys.stderr)
                return symbols
        except Exception as e:
            print(f'[ERROR] Failed to fetch {market} symbols: {e}', file=sys.stderr)
            return []


async def get_all_symbols(market=None):
    """Fetch symbols from KOSPI, KOSDAQ or both"""
    if market:
        return await fetch_symbols(market)
    
    kospi_symbols, kosdaq_symbols = await asyncio.gather(
        fetch_symbols('KOSPI'),
        fetch_symbols('KOSDAQ')
    )
    # Return as a unique sorted list
    return sorted(list(set(kospi_symbols + kosdaq_symbols)))


async def main_async(market=None, output_file=None):
    """Main async entry point"""
    symbols = await get_all_symbols(market)
    
    if not symbols:
        return 1
    
    if output_file:
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            for symbol in symbols:
                f.write(f"{symbol}\n")
        print(f'[INFO] Saved {len(symbols)} symbols to {output_file}', file=sys.stderr)
    else:
        # Output symbols to stdout
        for symbol in symbols:
            print(symbol)
    
    return 0


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Fetch KRX stock symbols')
    parser.add_argument('-m', '--market',
                       choices=['KOSPI', 'KOSDAQ'],
                       default=None,
                       help='Market to fetch symbols from (default: both KOSPI and KOSDAQ)')
    parser.add_argument('-o', '--output',
                       help='Output file path')
    args = parser.parse_args()
    
    try:
        # Use asyncio.run for cleaner entry
        exit_code = asyncio.run(main_async(args.market, args.output))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print('\n[INFO] Interrupted by user', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'[ERROR] Unexpected error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
