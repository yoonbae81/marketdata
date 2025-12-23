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
    table = bs.find('table', class_='type2')
    if not table:
        return []
    
    result = []
    for tr in table.find_all('tr'):
        tds = tr.find_all('td', recursive=False)
        if len(tds) < 7:
            continue
            
        # Check if first cell has time (format HH:MM)
        time_span = tds[0].find('span')
        if not time_span:
            continue
            
        time_text = time_span.text.strip()
        # Relaxed regex to handle potential invisible characters or non-breaking spaces
        if not re.search(r'\d{2}:\d{2}', time_text):
            continue
            
        # Extra care for time format - extract just HH:MM
        time_match = re.search(r'(\d{2}:\d{2})', time_text)
        if not time_match:
            continue
        clean_time = time_match.group(1)
            
        price = tds[1].text.strip().replace(',', '')
        volume = tds[5].text.strip().replace(',', '')
        
        # Result format: [symbol, price, volume, time]
        result.append([symbol, price, volume, clean_time])
    
    return result


async def fetch_minute_page(session, symbol, date_str, page, semaphore):
    """Fetch a single page of minute data"""
    params = {
        'page': page,
        'code': symbol,
        'thistime': date_str.replace('-', '') + '235959'
    }
    
    async with semaphore:
        try:
            async with session.get(MINUTE_URL, params=params, headers=MINUTE_HEADERS, timeout=15) as response:
                if response.status != 200:
                    return []
                content = await response.read()
                # Naver Finance uses EUC-KR
                try:
                    text = content.decode('euc-kr')
                except:
                    text = content.decode('utf-8', errors='ignore')
                
                bs = BeautifulSoup(text, 'lxml')
                return parse_minute_rows(symbol, bs)
        except Exception as e:
            print(f"[DEBUG] Error fetching {symbol} page {page}: {e}", file=sys.stderr)
            return []


async def fetch_minute_symbol(session, symbol, date_str, semaphore):
    """Fetch all minute data for a single symbol"""
    # Fetch page 1 first to determine last page
    all_results = await fetch_minute_page(session, symbol, date_str, 1, semaphore)
    if not all_results:
        return []

    # To find last page, we need page 1's BS again or just fetch it inside here
    # Optimization: fetch_minute_page could return (results, last_page) but for simplicity:
    params = { 'page': 1, 'code': symbol, 'thistime': date_str.replace('-', '') + '235959' }
    
    try:
        # We need the BS to find pgRR
        async with semaphore:
            async with session.get(MINUTE_URL, params=params, headers=MINUTE_HEADERS, timeout=15) as response:
                if response.status != 200:
                    return ['\t'.join(r) for r in all_results]
                content = await response.read()
                try:
                    text = content.decode('euc-kr')
                except:
                    text = content.decode('utf-8', errors='ignore')
                bs = BeautifulSoup(text, 'lxml')

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

        # Dedup and sort by time
        unique_data = {}
        for res in all_results:
            key = res[3]  # time string (HH:MM)
            if key not in unique_data:
                unique_data[key] = res
        
        # Return sorted results as tab-separated strings
        return ['\t'.join(unique_data[key]) for key in sorted(unique_data.keys())]
                    
    except Exception as e:
        print(f'[ERROR] Exception for {symbol}: {e}', file=sys.stderr)
        return ['\t'.join(r) for r in all_results]


async def minute_worker(queue, session, date_str, semaphore, results_file, lock):
    """Worker to process symbols from a queue and write to file immediately"""
    while True:
        symbol = await queue.get()
        try:
            # Fetch all minute data for the symbol
            symbol_results = await fetch_minute_symbol(session, symbol, date_str, semaphore)
            if symbol_results and results_file:
                async with lock:
                    with open(results_file, 'a', encoding='utf-8') as f:
                        for line in symbol_results:
                            f.write(line + '\n')
        except Exception as e:
            print(f"[ERROR] Worker error for {symbol}: {e}", file=sys.stderr)
        finally:
            queue.task_done()


async def collect_minute_data(date_str, symbols, concurrency, output_file):
    """Memory-safe collection of minute data using worker-queue pattern"""
    print(f'[INFO] Collecting minute data for {date_str} (output: {output_file})...', file=sys.stderr)
    
    # Ensure output directory exists and file is empty
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
        # Use a fixed number of workers (equal to concurrency is usually good)
        workers = [asyncio.create_task(minute_worker(queue, session, date_str, semaphore, output_file, lock))
                   for _ in range(concurrency)]
        
        await queue.join()
        
        for w in workers:
            w.cancel()
    
    print(f'[INFO] Minute data collection finished for {date_str}', file=sys.stderr)
    return None  # No longer returning a massive list


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
