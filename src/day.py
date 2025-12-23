#!/usr/bin/env python3
"""
Daily OHLCV data collection module for KRX market data.
Fetches daily price data for given symbols.
"""

import argparse
import asyncio
import aiohttp
import sys
from datetime import datetime
from bs4 import BeautifulSoup


DAY_URL = 'https://finance.naver.com/item/sise_day.nhn'
DAY_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4501.0 Safari/537.36'
}


def parse_day_data(bs):
    """Parse daily OHLCV data from HTML"""
    values = [span.text.strip().replace(',', '').replace('.', '-') 
              for span in bs.find_all('span', class_='tah')]
    
    # 7 fields: date, close, delta, open, high, low, volume
    for i in range(0, len(values), 7):
        row = values[i:i+7]
        if len(row) == 7:
            yield {
                'date': row[0],
                'close': row[1],
                'delta': row[2],
                'open': row[3],
                'high': row[4],
                'low': row[5],
                'volume': row[6]
            }


async def fetch_day_symbol(session, symbol, date, semaphore):
    """Fetch daily data for a single symbol"""
    async with semaphore:
        try:
            params = {'code': symbol, 'page': 1}
            async with session.get(DAY_URL, params=params, headers=DAY_HEADERS, timeout=10) as response:
                if response.status != 200:
                    return None
                content = await response.read()
                bs = BeautifulSoup(content, 'lxml')

                for row in parse_day_data(bs):
                    if row['date'] == date and row['open'] != '0':
                        return '\t'.join([symbol, row['open'], row['high'], row['low'], row['close'], row['volume']])
                
                return None
        except Exception:
            return None


async def collect_day_data(date, symbols, concurrency, output_file=None):
    """Collect daily data for all symbols and optionally save to file"""
    print(f'[INFO] Collecting day data for {date}...', file=sys.stderr)
    
    connector = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300)
    semaphore = asyncio.Semaphore(concurrency)
    results = []
    
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_day_symbol(session, symbol, date, semaphore) for symbol in symbols]
        responses = await asyncio.gather(*tasks)
        
        for res in responses:
            if res:
                results.append(res)
    
    print(f'[INFO] Day data collected: {len(results)} lines', file=sys.stderr)
    
    # Save to file if output_file is provided
    if output_file:
        from pathlib import Path
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            for line in sorted(results):
                f.write(line + '\n')
        print(f'[INFO] Day data saved to {output_path}', file=sys.stderr)
    
    return results


async def main_async(date, symbols, concurrency):
    """Main async entry point"""
    results = await collect_day_data(date, symbols, concurrency)
    
    # Output results to stdout (sorted)
    for line in sorted(results):
        print(line)
    
    return 0


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Collect daily OHLCV data for KRX stocks')
    parser.add_argument('-d', '--date', 
                       default=datetime.now().strftime('%Y-%m-%d'),
                       help='Date to collect data for (format: YYYY-MM-DD)')
    parser.add_argument('-s', '--symbols',
                       required=True,
                       help='Comma-separated list of symbols or path to file with symbols')
    parser.add_argument('-c', '--concurrency',
                       type=int,
                       default=20,
                       help='Max concurrent requests')
    
    args = parser.parse_args()
    
    # Parse symbols
    if ',' in args.symbols:
        symbols = args.symbols.split(',')
    else:
        # Assume it's a file path
        try:
            with open(args.symbols, 'r') as f:
                symbols = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f'[ERROR] Symbols file not found: {args.symbols}', file=sys.stderr)
            sys.exit(1)
    
    try:
        exit_code = asyncio.run(main_async(args.date, symbols, args.concurrency))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print('\n[INFO] Interrupted by user', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'[ERROR] Unexpected error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
