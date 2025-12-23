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
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import the collection modules
from symbol import fetch_symbols
from day import collect_day_data
from minute import collect_minute_data


async def main_async(date, output_dir, concurrency):
    """Main orchestration: symbols -> (day || minute) for each market"""
    print(f'[INFO] Starting market data collection for {date}', file=sys.stderr)
    
    output_path = Path(output_dir)
    
    # Step 1: Fetch symbols for both markets
    print('[INFO] Fetching symbols for KOSPI and KOSDAQ...', file=sys.stderr)
    kospi_symbols, kosdaq_symbols = await asyncio.gather(
        fetch_symbols('KOSPI'),
        fetch_symbols('KOSDAQ')
    )
    
    if not kospi_symbols and not kosdaq_symbols:
        print('[ERROR] No symbols found for either market, exiting', file=sys.stderr)
        return 1
    
    # Step 2: Prepare output file paths (single file for all markets)
    day_file = output_path / 'day' / f'{date}.txt'
    minute_file = output_path / 'minute' / f'{date}.txt'
    
    # Step 3: Collect data for all markets in parallel
    kospi_day_task = None
    kospi_minute_task = None
    kosdaq_day_task = None
    kosdaq_minute_task = None
    
    if kospi_symbols:
        kospi_day_task = collect_day_data(date, kospi_symbols, concurrency)
        kospi_minute_task = collect_minute_data(date, kospi_symbols, concurrency)
    
    if kosdaq_symbols:
        kosdaq_day_task = collect_day_data(date, kosdaq_symbols, concurrency)
        kosdaq_minute_task = collect_minute_data(date, kosdaq_symbols, concurrency)
    
    # Gather all non-None tasks
    tasks = [t for t in [kospi_day_task, kospi_minute_task, kosdaq_day_task, kosdaq_minute_task] if t is not None]
    results = await asyncio.gather(*tasks)
    
    # Step 4: Combine and save results
    day_results = []
    minute_results = []
    
    result_idx = 0
    if kospi_day_task:
        day_results.extend(results[result_idx])
        result_idx += 1
    if kospi_minute_task:
        minute_results.extend(results[result_idx])
        result_idx += 1
    if kosdaq_day_task:
        day_results.extend(results[result_idx])
        result_idx += 1
    if kosdaq_minute_task:
        minute_results.extend(results[result_idx])
        result_idx += 1
    
    # Save day data
    day_file.parent.mkdir(parents=True, exist_ok=True)
    with open(day_file, 'w') as f:
        for line in sorted(day_results):
            f.write(line + '\n')
    print(f'[INFO] Day data saved to {day_file}', file=sys.stderr)
    
    # Save minute data (sorted by time - 4th column)
    minute_file.parent.mkdir(parents=True, exist_ok=True)
    with open(minute_file, 'w') as f:
        sorted_lines = sorted(minute_results, key=lambda x: x.split('\t')[3] if len(x.split('\t')) > 3 else '')
        for line in sorted_lines:
            f.write(line + '\n')
    print(f'[INFO] Minute data saved to {minute_file}', file=sys.stderr)
    
    print(f'[INFO] Market data collection finished for {date}', file=sys.stderr)
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
