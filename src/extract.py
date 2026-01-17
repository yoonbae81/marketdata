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
    
    dfs = []
    current = start_dt
    
    while current <= end_dt:
        date_str = current.strftime('%Y-%m-%d')
        year = current.strftime('%Y')
        
        file_path = data_dir / year / f"{date_str}.parquet"
        if file_path.exists():
            df = pd.read_parquet(file_path)
            df = df[df['symbol'] == symbol]
            # Filter by time range
            df = df[(df['dt'] >= start_date) & (df['dt'] <= end_boundary)]
            if not df.empty:
                dfs.append(df)
        
        current += timedelta(days=1)
    
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
    
    dfs = []
    current = start_dt
    
    while current <= end_dt:
        date_str = current.strftime('%Y-%m-%d')
        year = current.strftime('%Y')
        
        file_path = data_dir / year / f"{date_str}.parquet"
        if file_path.exists():
            df = pd.read_parquet(file_path)
            df = df[df['symbol'] == symbol]
            if not df.empty:
                dfs.append(df)
        
        current += timedelta(days=1)
    
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
    
    dfs = []
    current = start_dt
    
    while current <= end_dt:
        date_str = current.strftime('%Y-%m-%d')
        year = current.strftime('%Y')
        
        file_path = data_dir / year / f"{date_str}.parquet"
        if file_path.exists():
            df = pd.read_parquet(file_path)
            df = df[df['symbol'] == symbol]
            # Filter by time range
            df = df[(df['dt'] >= start_date) & (df['dt'] <= end_boundary)]
            if not df.empty:
                dfs.append(df)
        
        current += timedelta(days=1)
    
    if dfs:
        return pd.concat(dfs, ignore_index=True).sort_values('dt')
    return pd.DataFrame()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="MarketData Parquet Extractor")
    parser.add_argument("type", choices=["day", "min"], help="Data type (day or min)")
    parser.add_argument("symbol", help="Ticker symbol (Numeric=KR, Alphabetical=US)")
    parser.add_argument("start_date", help="Start date (YYYY-MM-DD or 'YYYY-MM-DD HH:MM:SS')")
    parser.add_argument("end_date", help="End date (YYYY-MM-DD or 'YYYY-MM-DD HH:MM:SS')")
    
    args = parser.parse_args()
    
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
