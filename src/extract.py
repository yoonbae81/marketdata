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


def _extract_generator(symbol, start_date, end_date, data_dir, time_col='dt', end_suffix=' 23:59:59'):
    """Generic generator for extracting data month by month / file by file."""
    symbol = symbol.upper()
    data_dir = Path(data_dir)
    
    start_dt = datetime.strptime(start_date.split()[0], '%Y-%m-%d')
    # If end_date has no time, use the end of that day for filtering
    if ' ' in end_date or ':' in end_date:
        end_dt_str = end_date.split()[0]
        end_boundary = end_date
    else:
        end_dt_str = end_date
        end_boundary = f"{end_date}{end_suffix}"
    
    end_dt = datetime.strptime(end_dt_str, '%Y-%m-%d')
    
    file_paths = get_files_to_read(data_dir, start_dt, end_dt)
    
    for file_path in file_paths:
        try:
            df = pd.read_parquet(file_path)
            if df.empty:
                continue
                
            df = df[df['symbol'] == symbol]
            if df.empty:
                continue
                
            # Filter by date/time range
            df = df[(df[time_col] >= start_date) & (df[time_col] <= end_boundary)]
            if not df.empty:
                yield df.sort_values(time_col)
        except Exception as e:
            print(f"[WARN] Failed to read {file_path}: {e}", file=sys.stderr)
            continue


def extract_kr_1min(symbol, start_date, end_date, data_dir=None):
    """Extract KR 1-minute data for a symbol within date range"""
    if data_dir is None:
        script_dir = Path(__file__).parent
        data_dir = script_dir.parent / "data" / "KR-1m"
    
    dfs = list(_extract_generator(symbol, start_date, end_date, data_dir, time_col='dt'))
    if dfs:
        return pd.concat(dfs, ignore_index=True).sort_values('dt')
    return pd.DataFrame()


def extract_kr_day(symbol, start_date, end_date, data_dir=None):
    """Extract KR daily data for a symbol within date range"""
    if data_dir is None:
        script_dir = Path(__file__).parent
        data_dir = script_dir.parent / "data" / "KR-1d"
    
    # Daily data uses 'date' column and usually no time suffix needed for boundary
    dfs = list(_extract_generator(symbol, start_date, end_date, data_dir, time_col='date', end_suffix=''))
    if dfs:
        return pd.concat(dfs, ignore_index=True).sort_values('date')
    return pd.DataFrame()


def extract_us_5min(symbol, start_date, end_date, data_dir=None):
    """Extract US 5-minute data for a symbol within date range"""
    if data_dir is None:
        script_dir = Path(__file__).parent
        data_dir = script_dir.parent / "data" / "US-5m"
    
    dfs = list(_extract_generator(symbol, start_date, end_date, data_dir, time_col='dt'))
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
    
    args.symbol = args.symbol.upper()
    
    # Automatic market detection: Numeric symbols are KR, Alphabetical are US
    is_numeric = args.symbol.replace('.', '').replace('-', '').isdigit()
    
    # Determine the generator and column names
    script_dir = Path(__file__).parent
    if args.type == "day":
        if is_numeric:
            data_dir = script_dir.parent / "data" / "KR-1d"
            gen = _extract_generator(args.symbol, args.start_date, args.end_date, data_dir, time_col='date', end_suffix='')
        else:
            print(f"[ERROR] US Day data extraction not implemented for '{args.symbol}'", file=sys.stderr)
            sys.exit(1)
    else:  # min
        if is_numeric:
            data_dir = script_dir.parent / "data" / "KR-1m"
        else:
            data_dir = script_dir.parent / "data" / "US-5m"
        gen = _extract_generator(args.symbol, args.start_date, args.end_date, data_dir, time_col='dt')
    
    # Stream the output
    try:
        header_printed = False
        data_found = False
        
        for df_chunk in gen:
            data_found = True
            # Print without index, and only show header for the first chunk
            print(df_chunk.to_string(index=False, header=not header_printed))
            header_printed = True
            # Flush stdout to ensure immediate visibility
            sys.stdout.flush()
            
        if not data_found:
            print("No data found.")
            
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
