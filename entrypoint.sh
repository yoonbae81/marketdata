#!/usr/bin/env python3
"""
Orchestration script for KRX market data collection.
Coordinates symbol, day, and minute data collection modules.
"""

import sys
import asyncio
import tempfile
from datetime import datetime
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Import the collection modules
from symbol import fetch_symbols
from day import collect_day_data
from minute import collect_minute_data


async def main_async(date, output_dir, concurrency):
    """Main orchestration: symbols -> (day || minute) for each market"""
    print(f'[INFO] Starting market data collection for {date}', file=sys.stderr)
    
    output_path = Path(output_dir)
    
    # Step 1: Fetch symbols
    print('[INFO] Fetching symbols for KOSPI and KOSDAQ...', file=sys.stderr)
    kospi_symbols, kosdaq_symbols = await asyncio.gather(
        fetch_symbols('KOSPI'),
        fetch_symbols('KOSDAQ')
    )
    
    # Step 2 & 3: Execute tasks and collect results
    tasks = []
    if kospi_symbols:
        tasks.append(collect_day_data(date, kospi_symbols, concurrency))
        tasks.append(collect_minute_data(date, kospi_symbols, concurrency))
    
    if kosdaq_symbols:
        tasks.append(collect_day_data(date, kosdaq_symbols, concurrency))
        tasks.append(collect_minute_data(date, kosdaq_symbols, concurrency))
    
    print(f'[INFO] Dispatching {len(tasks)} collection tasks...', file=sys.stderr)
    all_results = await asyncio.gather(*tasks)
    
    # Map results (order: [KOSPI_DAY, KOSPI_MINUTE, KOSDAQ_DAY, KOSDAQ_MINUTE])
    # The order depends on how many markets were present
    idx = 0
    day_results = []
    minute_results = []
    
    if kospi_symbols:
        day_results.extend(all_results[idx])
        minute_results.extend(all_results[idx+1])
        idx += 2
    
    if kosdaq_symbols:
        day_results.extend(all_results[idx])
        minute_results.extend(all_results[idx+1])
    
    # Step 4: Final sorting and saving
    print('[INFO] Sorting and saving results...', file=sys.stderr)
    
    # Day data sorting: Symbol only
    day_results.sort()
    
    # Minute data sorting: 1st Time, 2nd Ticker (Symbol)
    # result format: [symbol, price, volume, clean_time] joined by \t
    # so index for time is 3, index for symbol is 0
    minute_results.sort(key=lambda x: (x.split('\t')[3], x.split('\t')[0]) if len(x.split('\t')) > 3 else x)

    # Save Day files
    day_file = output_path / 'day' / f'{date}.txt'
    day_file.parent.mkdir(parents=True, exist_ok=True)
    with open(day_file, 'w', encoding='utf-8') as outfile:
        for line in day_results:
            outfile.write(line + '\n')

    # Save Minute files
    minute_file = output_path / 'minute' / f'{date}.txt'
    minute_file.parent.mkdir(parents=True, exist_ok=True)
    with open(minute_file, 'w', encoding='utf-8') as outfile:
        for line in minute_results:
            outfile.write(line + '\n')
    
    print(f'[INFO] Data saved to {day_file} and {minute_file}', file=sys.stderr)
    return 0
    
    return 0


def main():
    """Entry point for orchestration"""
    # Use environment variables or defaults
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')
    
    # Use fixed internal paths (Docker paths)
    output_dir = Path('/data')
    concurrency = 20
    
    try:
        exit_code = asyncio.run(main_async(date, str(output_dir), concurrency))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print('\n[INFO] Interrupted by user', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'[ERROR] Unexpected error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
