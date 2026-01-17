#!/usr/bin/env python3
"""
Parquet-based data extraction for MarketData.
Reads daily .parquet files from data/ directory structure.
Can be run standalone or imported as a module.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Check required dependencies
try:
    import pandas as pd
except ImportError:
    print("[ERROR] Required package 'pandas' is not installed.", file=sys.stderr)
    print("Please install it with: pip install pandas", file=sys.stderr)
    sys.exit(1)

try:
    import pyarrow
except ImportError:
    print("[ERROR] Required package 'pyarrow' is not installed.", file=sys.stderr)
    print("Please install it with: pip install pyarrow", file=sys.stderr)
    sys.exit(1)



def get_files_to_read(data_dir, start_dt, end_dt):
    """
    Find parquet files covering the date range [start_dt, end_dt].
    Searches for:
    1. {year}.parquet (merged yearly)
    2. {year}/{year}-{month:02d}.parquet (merged monthly)
    3. {year}/{year}-{month:02d}-{day:02d}.parquet (daily)
    """
    files = []
    
    # Iterate through each calendar year in the range
    for year in range(start_dt.year, end_dt.year + 1):
        # 1. Check for yearly merged file: data/TYPE/YYYY.parquet OR data/TYPE/YYYY/YYYY.parquet
        yearly_file = data_dir / f"{year}.parquet"
        if not yearly_file.exists():
            yearly_file = data_dir / str(year) / f"{year}.parquet"
            
        if yearly_file.exists():
            files.append(yearly_file)
            continue
            
        year_dir = data_dir / str(year)
        if not year_dir.exists():
            continue
            
        # If year not merged, check months
        # Determine month range for this year
        start_month = start_dt.month if year == start_dt.year else 1
        end_month = end_dt.month if year == end_dt.year else 12
        
        for month in range(start_month, end_month + 1):
            # 2. Check for monthly merged file: data/TYPE/YYYY/YYYY-MM.parquet
            monthly_file = year_dir / f"{year}-{month:02d}.parquet"
            if monthly_file.exists():
                files.append(monthly_file)
                continue
            
            # If month not merged, check days
            # Determine day range for this month
            # For simplicity, we can just glob and filter by date string
            month_prefix = f"{year}-{month:02d}-"
            daily_files = sorted(list(year_dir.glob(f"{month_prefix}*.parquet")))
            
            for f in daily_files:
                # Extract date from filename: YYYY-MM-DD.parquet
                try:
                    file_date_str = f.stem
                    file_dt = datetime.strptime(file_date_str, '%Y-%m-%d')
                    
                    # We only care about date part for filtering files
                    # But the provided start_dt/end_dt might have time
                    # So we compare date to date
                    if start_dt.date() <= file_dt.date() <= end_dt.date():
                        files.append(f)
                except ValueError:
                    continue
                    
    return files


def extract_kr_1min(symbol, start_date, end_date, data_dir=None):
    """Extract KR 1-minute data for a symbol within date range"""
    if data_dir is None:
        # Default to project root / data / KR-1m
        script_dir = Path(__file__).parent
        data_dir = script_dir.parent / "data" / "KR-1m"
    else:
        data_dir = Path(data_dir)
    
    start_dt = datetime.strptime(start_date.split()[0], '%Y-%m-%d')
    end_dt = datetime.strptime(end_date.split()[0] if ' ' in end_date else end_date, '%Y-%m-%d')
    
    # Handle optional time in end_date
    if ' ' in end_date or ':' in end_date:
        end_boundary = end_date
    else:
        end_boundary = f"{end_date} 23:59:59"
    
    file_paths = get_files_to_read(data_dir, start_dt, end_dt)
    
    dfs = []
    for file_path in file_paths:
        df = pd.read_parquet(file_path)
        df = df[df['symbol'] == symbol]
        # Filter by time range
        df = df[(df['dt'] >= start_date) & (df['dt'] <= end_boundary)]
        if not df.empty:
            dfs.append(df)
    
    if dfs:
        return pd.concat(dfs, ignore_index=True).sort_values('dt')
    return pd.DataFrame()


def extract_kr_day(symbol, start_date, end_date, data_dir=None):
    """Extract KR daily data for a symbol within date range"""
    if data_dir is None:
        # Default to project root / data / KR-1d
        script_dir = Path(__file__).parent
        data_dir = script_dir.parent / "data" / "KR-1d"
    else:
        data_dir = Path(data_dir)
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    file_paths = get_files_to_read(data_dir, start_dt, end_dt)
    
    dfs = []
    for file_path in file_paths:
        df = pd.read_parquet(file_path)
        df = df[df['symbol'] == symbol]
        # Filter by date range
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        if not df.empty:
            dfs.append(df)
    
    if dfs:
        return pd.concat(dfs, ignore_index=True).sort_values('date')
    return pd.DataFrame()


def extract_us_5min(symbol, start_date, end_date, data_dir=None):
    """Extract US 5-minute data for a symbol within date range"""
    if data_dir is None:
        # Default to project root / data / US-5m
        script_dir = Path(__file__).parent
        data_dir = script_dir.parent / "data" / "US-5m"
    else:
        data_dir = Path(data_dir)
    
    start_dt = datetime.strptime(start_date.split()[0], '%Y-%m-%d')
    end_dt = datetime.strptime(end_date.split()[0] if ' ' in end_date else end_date, '%Y-%m-%d')
    
    # Handle optional time in end_date
    if ' ' in end_date or ':' in end_date:
        end_boundary = end_date
    else:
        end_boundary = f"{end_date} 23:59:59"
    
    file_paths = get_files_to_read(data_dir, start_dt, end_dt)
    
    dfs = []
    for file_path in file_paths:
        df = pd.read_parquet(file_path)
        df = df[df['symbol'] == symbol]
        # Filter by time range
        df = df[(df['dt'] >= start_date) & (df['dt'] <= end_boundary)]
        if not df.empty:
            dfs.append(df)
    
    if dfs:
        return pd.concat(dfs, ignore_index=True).sort_values('dt')
    return pd.DataFrame()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="MarketData Parquet Extractor")
    parser.add_argument("type", choices=["day", "min"], help="Data type (day or min)")
    parser.add_argument("symbol", help="Ticker symbol (Numeric=KR, Alphabetical=US)")
    parser.add_argument("start_date", help="Start date (YYYY-MM-DD or 'YYYY-MM-DD HH:MM:SS')")
    parser.add_argument("end_date", nargs='?', help="End date (YYYY-MM-DD or 'YYYY-MM-DD HH:MM:SS'), defaults to start_date")
    
    args = parser.parse_args()
    if args.end_date is None:
        args.end_date = args.start_date
    
    # Automatic market detection: Numeric symbols are KR, Alphabetical are US
    is_numeric = args.symbol.replace('.', '').replace('-', '').isdigit()
    
    try:
        if args.type == "day":
            if is_numeric:
                df = extract_kr_day(args.symbol, args.start_date, args.end_date)
            else:
                print(f"[ERROR] US Day data extraction not implemented for '{args.symbol}'")
                sys.exit(1)
        else:  # min
            if is_numeric:
                df = extract_kr_1min(args.symbol, args.start_date, args.end_date)
            else:
                df = extract_us_5min(args.symbol, args.start_date, args.end_date)
                
        if df.empty:
            print("No data found.")
        else:
            print(df.to_string(index=False))
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
