
import os
import sys
import re
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta, date

def get_project_root():
    """Determine the project root directory"""
    # Assuming script is in scripts/merge/
    return Path(__file__).resolve().parent.parent.parent

def check_dependencies():
    """Verify required packages"""
    try:
        import pandas
        import pyarrow
    except ImportError:
        print("[ERROR] Required packages 'pandas' or 'pyarrow' not installed.", file=sys.stderr)
        sys.exit(1)

def get_monthly_groups(data_dir, year):
    """
    Scan a year directory and group daily Parquet files by month.
    Returns: dict { 'YYYY-MM': [list of file paths] }
    """
    year_dir = data_dir / str(year)
    if not year_dir.exists():
        return {}

    groups = {}
    date_pattern = re.compile(r'^(\d{4})-(\d{2})-\d{2}$')
    
    for f in year_dir.glob('*.parquet'):
        match = date_pattern.match(f.stem)
        if match:
            month_key = f"{match.group(1)}-{match.group(2)}"
            if month_key not in groups:
                groups[month_key] = []
            groups[month_key].append(f)
            
    return groups

def is_safe_to_merge(month_str, days_wait=5):
    """
    Check if enough time has passed since the end of the month.
    month_str: 'YYYY-MM'
    """
    try:
        year, month = map(int, month_str.split('-'))
        # Calculate the first day of the NEXT month
        if month == 12:
            next_month_start = date(year + 1, 1, 1)
        else:
            next_month_start = date(year, month + 1, 1)
            
        cutoff_date = next_month_start + timedelta(days=days_wait)
        return date.today() >= cutoff_date
    except Exception as e:
        print(f"[WARN] Failed to parse date {month_str}: {e}")
        return False

def merge_and_validate(month_key, files, target_dir, sort_columns):
    """
    Merge daily files, validate data match, save monthly file, and delete daily files.
    """
    # Sort files to ensure deterministic loading order
    files = sorted(files)
    print(f"[INFO] Merging {month_key} ({len(files)} files)...")

    try:
        # Load all daily files
        dfs = [pd.read_parquet(f) for f in files]
        if not dfs:
            return False
            
        daily_combined = pd.concat(dfs, ignore_index=True)
        
        # Drop duplicates before sorting
        daily_combined = daily_combined.drop_duplicates()
        
        # Sort combined data
        if sort_columns:
            daily_combined = daily_combined.sort_values(sort_columns).reset_index(drop=True)
        else:
            daily_combined = daily_combined.reset_index(drop=True)

        # Output path: YYYY/YYYY-MM.parquet
        year = month_key.split('-')[0]
        output_dir = target_dir / year
        output_file = output_dir / f"{month_key}.parquet"
        
        # Save to monthly file
        daily_combined.to_parquet(output_file, compression='zstd', index=False)
        
        # VALIDATION
        # Read back the saved file
        saved_df = pd.read_parquet(output_file)
        
        # Sort saved data (should be already sorted, but to be sure)
        if sort_columns:
            saved_df = saved_df.sort_values(sort_columns).reset_index(drop=True)
        else:
            saved_df = saved_df.reset_index(drop=True)
            
        # Compare
        pd.testing.assert_frame_equal(daily_combined, saved_df)
        print(f"[OK] Validation passed for {output_file.name}")
        
        # Cleanup
        for f in files:
            os.remove(f)
        print(f"[CLEANUP] Deleted {len(files)} daily files")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to merge {month_key}: {e}", file=sys.stderr)
        # If created but failed validation, try to delete the potentially corrupt monthly file
        if 'output_file' in locals() and output_file.exists():
            try:
                os.remove(output_file)
                print(f"[ROLLBACK] Deleted corrupt monthly file {output_file.name}")
            except:
                pass
        return False

def read_txt_file(file_path, market_type):
    """Read text file into DataFrame based on market type"""
    try:
        if market_type == 'KR-1m':
            # KR-1m: symbol, price, volume, time
            df = pd.read_csv(file_path, sep='\t', header=None,
                           names=['symbol', 'price', 'volume', 'time'],
                           dtype={'symbol': str, 'price': int, 'volume': int, 'time': str})
            date_str = file_path.stem
            # Create datetime column (dt)
            df['dt'] = pd.to_datetime(date_str + ' ' + df['time'])
            # Sort columns
            df = df[['symbol', 'dt', 'price', 'volume']]
            
        elif market_type == 'KR-1d':
            # KR-1d: symbol, open, high, low, close, volume
            df = pd.read_csv(file_path, sep='\t', header=None,
                           names=['symbol', 'open', 'high', 'low', 'close', 'volume'],
                           dtype={'symbol': str, 'open': int, 'high': int, 'low': int, 
                                  'close': int, 'volume': int})
            date_str = file_path.stem
            df['date'] = pd.to_datetime(date_str)
            df = df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]
            
        elif market_type == 'US-5m':
            # US-5m: symbol, price, volume, time
            # Note: US volume needs float handling then round to int
            df = pd.read_csv(file_path, sep='\t', header=None,
                           names=['symbol', 'price', 'volume', 'time'],
                           dtype={'symbol': str, 'price': float, 'volume': float, 'time': str})
            
            df['volume'] = df['volume'].fillna(0).round().astype(int)
            date_str = file_path.stem
            df['dt'] = pd.to_datetime(date_str + ' ' + df['time'])
            df = df[['symbol', 'dt', 'price', 'volume']]
            
        return df
    except Exception as e:
        print(f"[ERROR] Failed to read {file_path}: {e}")
        return None

def compare_dfs(combined_txt, merged_df, market_type, label, sort_cols):
    """Internal helper to compare text data vs parquet data"""
    # Let's subset the parquet data to exactly the rows that should match the text files
    # We can do this by merging on the index columns
    merged_comparison = pd.merge(combined_txt, merged_df, on=sort_cols, how='inner', suffixes=('_txt', '_pq'))
    
    if len(merged_comparison) != len(combined_txt):
        print(f"[FAIL] Row count mismatch! Txt: {len(combined_txt)}, Matched in Parquet: {len(merged_comparison)}")
        print(f"       This means some rows in TXT are missing from Parquet.")
        return False

    # Now compare value columns
    value_cols = [c for c in combined_txt.columns if c not in sort_cols]
    mismatch_count = 0
    
    for col in value_cols:
        col_txt = f"{col}_txt"
        col_pq = f"{col}_pq"
        
        # Numeric comparison with tolerance (especially for float prices in US)
        is_float = pd.api.types.is_float_dtype(merged_comparison[col_txt])
        
        if is_float:
            matches = np.isclose(merged_comparison[col_txt], merged_comparison[col_pq], equal_nan=True)
        else:
            matches = merged_comparison[col_txt] == merged_comparison[col_pq]
            
        if not matches.all():
            n_mismatch = (~matches).sum()
            mismatch_count += n_mismatch
            print(f"[FAIL] Column '{col}' mismatch count: {n_mismatch}")
            # Show sample
            sample = merged_comparison[~matches].head(1)
            print(f"       Sample: Txt={sample[col_txt].values[0]}, Pq={sample[col_pq].values[0]}")
            
    if mismatch_count == 0:
        print(f"[OK] {label}: Perfectly matched {len(combined_txt)} rows.")
        return True
    else:
        print(f"[FAIL] {label}: Validation failed with {mismatch_count} total mismatches.")
        return False
