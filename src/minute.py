#!/usr/bin/env python3
"""
Minute-level data collection module for KRX market data.
Fetches intraday minute-by-minute price data for given symbols.
"""

import argparse
import asyncio
import aiohttp
import re
import sys
from datetime import datetime
from bs4 import BeautifulSoup


MINUTE_URL = 'https://finance.naver.com/item/sise_time.nhn'
MINUTE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4501.0 Safari/537.36'
}


def parse_minute_rows(symbol, bs):
    """Parse minute data rows from HTML"""
    values = [span.text.strip().replace(',', '') for span in bs.find_all('span', class_='tah')]
    if not values:
        return []
    
    result = []
    # 7 values per row: Time, Price, Chg, Open, High, Low, Vol
    for i in range(0, len(values), 7):
        row = values[i:i+7]
        if len(row) == 7:
            # Result format: [symbol, price, volume, time]
            result.append([symbol, row[1], row[6], row[0]])
    
    return result


async def fetch_minute_page(session, symbol, date_str, page, semaphore):
    """Fetch a single page of minute data"""
    async with semaphore:
        params = {
            'page': page,
            'code': symbol,
            'thistime': date_str.replace('-', '') + '235959'
        }
        try:
            async with session.get(MINUTE_URL, params=params, headers=MINUTE_HEADERS, timeout=10) as response:
                if response.status != 200:
                    return []
                text = await response.read()
                bs = BeautifulSoup(text, 'lxml')
                return parse_minute_rows(symbol, bs)
        except Exception:
            return []


async def fetch_minute_symbol(session, symbol, date_str, semaphore):
    """Fetch all minute data for a single symbol"""
    params = {
        'page': 1,
        'code': symbol,
        'thistime': date_str.replace('-', '') + '235959'
    }
    try:
        async with session.get(MINUTE_URL, params=params, headers=MINUTE_HEADERS, timeout=10) as response:
            if response.status != 200:
                return []
            text = await response.read()
            bs = BeautifulSoup(text, 'lxml')
            
            # Parse page 1 immediately
            all_results = parse_minute_rows(symbol, bs)
            if not all_results:
                return []

            # Determine last page
            pg_rr = bs.find('td', class_='pgRR')
            if pg_rr is None:
                last_page = 1
            else:
                match = re.search(r'page=([0-9]+)', pg_rr.a['href'])
                last_page = int(match.group(1)) if match else 1

            # Fetch remaining pages concurrently
            if last_page > 1:
                tasks = [fetch_minute_page(session, symbol, date_str, pg, semaphore) 
                        for pg in range(2, last_page + 1)]
                other_pages = await asyncio.gather(*tasks)
                for page_results in other_pages:
                    all_results.extend(page_results)

            # Dedup and sort
            unique_data = {}
            for res in all_results:
                key = res[3]  # time
                if key not in unique_data:
                    unique_data[key] = res
            
            # Return sorted results
            return ['\t'.join(unique_data[key]) for key in sorted(unique_data.keys())]
                    
    except Exception as e:
        print(f'[ERROR] Exception for {symbol}: {e}', file=sys.stderr)
        return []


async def collect_minute_data(date_str, symbols, concurrency, output_file=None):
    """Collect minute data for all symbols and optionally save to file"""
    print(f'[INFO] Collecting minute data for {date_str}...', file=sys.stderr)
    
    connector = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300)
    semaphore = asyncio.Semaphore(concurrency)
    results = []
    
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_minute_symbol(session, symbol, date_str, semaphore) for symbol in symbols]
        responses = await asyncio.gather(*tasks)
        
        for symbol_results in responses:
            results.extend(symbol_results)
    
    print(f'[INFO] Minute data collected: {len(results)} lines', file=sys.stderr)
    
    # Save to file if output_file is provided
    if output_file:
        from pathlib import Path
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            # Sort by 4th column (time)
            sorted_lines = sorted(results, key=lambda x: x.split('\t')[3] if len(x.split('\t')) > 3 else '')
            for line in sorted_lines:
                f.write(line + '\n')
        print(f'[INFO] Minute data saved to {output_path}', file=sys.stderr)
    
    return results


async def main_async(date, symbols, concurrency):
    """Main async entry point"""
    results = await collect_minute_data(date, symbols, concurrency)
    
    # Output results to stdout (sorted by time - 4th column)
    sorted_lines = sorted(results, key=lambda x: x.split('\t')[3] if len(x.split('\t')) > 3 else '')
    for line in sorted_lines:
        print(line)
    
    return 0


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Collect minute-level data for KRX stocks')
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
