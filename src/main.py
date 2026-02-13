#!/usr/bin/env python3
"""
MarketData - Main Entry Point
"""

import os
import sys
import argparse
import asyncio
import traceback
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from script_reporter import ScriptReporter

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(str(Path(__file__).resolve().parent))

from symbol_kr import get_all_symbols
from fetch_kr1d import collect_day_data as fetch_kr1d_data
from fetch_kr1m import collect_minute_data as fetch_kr1m_data

def run(sr: ScriptReporter, args):
    """Business logic for the script"""
    date = args.date
    concurrency = args.concurrency
    
    sr.stage("FETCHING_SYMBOLS")
    # Use existing event loop if available, else run new one
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    symbols = loop.run_until_complete(get_all_symbols())
    sr.log(f"Fetched {len(symbols)} symbols")
    
    year = date.split('-')[0]
    project_root = Path(__file__).resolve().parent.parent
    
    sr.stage("FETCHING_KR_1D")
    output_1d = project_root / "data" / "KR-1d" / year / f"{date}.parquet"
    loop.run_until_complete(fetch_kr1d_data(date, symbols, concurrency, str(output_1d)))
    sr.log(f"Daily data saved to {output_1d}")
    
    sr.stage("FETCHING_KR_1M")
    output_1m = project_root / "data" / "KR-1m" / year / f"{date}.parquet"
    loop.run_until_complete(fetch_kr1m_data(date, symbols, concurrency, str(output_1m)))
    sr.log(f"Minute data saved to {output_1m}")
    
    return {"status": "completed", "date": date, "symbols_count": len(symbols)}

def main():
    """Main entry point with reporting"""
    parser = argparse.ArgumentParser(description='MarketData Collection Entry Point')
    parser.add_argument('-d', '--date', 
                       default=datetime.now().strftime('%Y-%m-%d'),
                       help='Date to collect data for (format: YYYY-MM-DD)')
    parser.add_argument('-c', '--concurrency',
                       type=int,
                       default=20,
                       help='Max concurrent requests')
    args = parser.parse_args()

    # Use "MarketData Collection" as the task name for the reporter
    sr = ScriptReporter("MarketData Collection")
    
    try:
        result = run(sr, args)
        sr.success(result)
    except Exception:
        sr.fail(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
