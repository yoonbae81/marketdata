#!/usr/bin/env python3
"""
Daily OHLCV data collection module for KRX market data.
Fetches daily price data for given symbols.
"""

import argparse
import asyncio
import aiohttp
import re
import sys
from datetime import datetime
from bs4 import BeautifulSoup


DAY_URL = 'https://finance.naver.com/item/sise_day.nhn'
DAY_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4501.0 Safari/537.36'
}


def parse_day_data(bs):
    """Parse daily OHLCV data from HTML"""
    table = bs.find('table', class_='type2')
    if not table:
        return
        
    for tr in table.find_all('tr'):
        tds = tr.find_all('td', recursive=False)
        if len(tds) < 7:
            continue
            
        date_span = tds[0].find('span')
        if not date_span:
            continue
            
        date_text = date_span.text.strip().replace('.', '-')
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_text):
            continue
            
        # 7 fields: date, close, delta, open, high, low, volume
        # row[0]: date
        # row[1]: close
        # row[3]: open
        # row[4]: high
        # row[5]: low
        # row[6]: volume
        
        yield {
            'date': date_text,
            'close': tds[1].text.strip().replace(',', ''),
            'open': tds[3].text.strip().replace(',', ''),
            'high': tds[4].text.strip().replace(',', ''),
            'low': tds[5].text.strip().replace(',', ''),
            'volume': tds[6].text.strip().replace(',', '')
        }


async def fetch_day_symbol(session, symbol, date, semaphore):
    """Fetch daily data for a single symbol"""
    async with semaphore:
        try:
            params = {'code': symbol, 'page': 1}
            async with session.get(DAY_URL, params=params, headers=DAY_HEADERS, timeout=15) as response:
                if response.status != 200:
                    return None
                content = await response.read()
                try:
                    text = content.decode('euc-kr')
                except:
                    text = content.decode('utf-8', errors='ignore')
                bs = BeautifulSoup(text, 'lxml')

                for row in parse_day_data(bs):
                    if row['date'] == date and row['open'] != '0':
                        return '\t'.join([symbol, row['open'], row['high'], row['low'], row['close'], row['volume']])
                
                return None
        except Exception:
            return None


async def day_worker(queue, session, date, semaphore, results_file, lock):
    """Worker to process symbols and append to file immediately"""
    while True:
        symbol = await queue.get()
        try:
            res = await fetch_day_symbol(session, symbol, date, semaphore)
            if res and results_file:
                async with lock:
                    with open(results_file, 'a', encoding='utf-8') as f:
                        f.write(res + '\n')
        except Exception as e:
            print(f"[ERROR] Day worker error for {symbol}: {e}", file=sys.stderr)
        finally:
            queue.task_done()


async def collect_day_data(date, symbols, concurrency, output_file):
    """Memory-safe collection of daily data"""
    print(f'[INFO] Collecting day data for {date} (output: {output_file})...', file=sys.stderr)
    
    # Init file
    from pathlib import Path
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        pass

    queue = asyncio.Queue()
    for s in symbols:
        queue.put_nowait(s)

    connector = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300)
    semaphore = asyncio.Semaphore(concurrency)
    lock = asyncio.Lock()
    
    async with aiohttp.ClientSession(connector=connector) as session:
        workers = [asyncio.create_task(day_worker(queue, session, date, semaphore, output_file, lock))
                   for _ in range(concurrency)]
        
        await queue.join()
        for w in workers:
            w.cancel()
            
    print(f'[INFO] Day data collection finished for {date}', file=sys.stderr)
    return None


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
