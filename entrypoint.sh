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
if not src_path.exists():
    src_path = Path('/app/src')
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
    
    # Step 2 & 3: Prepare and execute tasks
    # We now pass output files directly to the collectors
    day_file = output_path / 'day' / f'{date}.txt'
    minute_file = output_path / 'minute' / f'{date}.txt'
    
    # Use temporary files for each market to allow parallel writing without lock contention
    # and then merge them.
    temp_files = {
        'KOSPI_DAY': output_path / f'kospi_day_{date}.tmp',
        'KOSPI_MINUTE': output_path / f'kospi_minute_{date}.tmp',
        'KOSDAQ_DAY': output_path / f'kosdaq_day_{date}.tmp',
        'KOSDAQ_MINUTE': output_path / f'kosdaq_minute_{date}.tmp'
    }

    task_defs = []
    if kospi_symbols:
        task_defs.append(('KOSPI_DAY', collect_day_data(date, kospi_symbols, concurrency, str(temp_files['KOSPI_DAY']))))
        task_defs.append(('KOSPI_MINUTE', collect_minute_data(date, kospi_symbols, concurrency, str(temp_files['KOSPI_MINUTE']))))
    
    if kosdaq_symbols:
        task_defs.append(('KOSDAQ_DAY', collect_day_data(date, kosdaq_symbols, concurrency, str(temp_files['KOSDAQ_DAY']))))
        task_defs.append(('KOSDAQ_MINUTE', collect_minute_data(date, kosdaq_symbols, concurrency, str(temp_files['KOSDAQ_MINUTE']))))
    
    print(f'[INFO] Dispatching {len(task_defs)} collection tasks...', file=sys.stderr)
    await asyncio.gather(*[t[1] for t in task_defs])
    
    # Step 4: Merge files
    print('[INFO] Merging results...', file=sys.stderr)
    
    # Combine Day files
    day_file.parent.mkdir(parents=True, exist_ok=True)
    with open(day_file, 'w', encoding='utf-8') as outfile:
        for key in ['KOSPI_DAY', 'KOSDAQ_DAY']:
            tmp = temp_files[key]
            if tmp.exists():
                with open(tmp, 'r', encoding='utf-8') as infile:
                    for line in infile:
                        outfile.write(line)
                tmp.unlink()

    # Combine Minute files
    minute_file.parent.mkdir(parents=True, exist_ok=True)
    with open(minute_file, 'w', encoding='utf-8') as outfile:
        for key in ['KOSPI_MINUTE', 'KOSDAQ_MINUTE']:
            tmp = temp_files[key]
            if tmp.exists():
                with open(tmp, 'r', encoding='utf-8') as infile:
                    for line in infile:
                        outfile.write(line)
                tmp.unlink()
    
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
