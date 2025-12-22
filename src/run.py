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

# Import the collection modules
from symbol import fetch_symbols
from day import collect_day_data
from minute import collect_minute_data


async def main_async(date, output_dir, concurrency):
    """Main orchestration: symbols -> (day || minute)"""
    print(f'[INFO] Starting market data collection for {date}', file=sys.stderr)
    
    # Step 1: Fetch symbols sequentially
    symbols = await fetch_symbols()
    if not symbols:
        print('[ERROR] No symbols found, exiting', file=sys.stderr)
        return 1
    
    # Step 2: Collect day and minute data in parallel
    day_task = collect_day_data(date, symbols, concurrency)
    minute_task = collect_minute_data(date, symbols, concurrency)
    
    day_results, minute_results = await asyncio.gather(day_task, minute_task)
    
    # Step 3: Save results
    output_path = Path(output_dir)
    
    # Save day data
    day_dir = output_path / 'day'
    day_dir.mkdir(parents=True, exist_ok=True)
    day_file = day_dir / f'{date}.txt'
    with open(day_file, 'w') as f:
        for line in sorted(day_results):
            f.write(line + '\n')
    print(f'[INFO] Day data saved to {day_file}', file=sys.stderr)
    
    # Save minute data (sorted by time - 4th column)
    minute_dir = output_path / 'minute'
    minute_dir.mkdir(parents=True, exist_ok=True)
    minute_file = minute_dir / f'{date}.txt'
    with open(minute_file, 'w') as f:
        # Sort by 4th column (time)
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
