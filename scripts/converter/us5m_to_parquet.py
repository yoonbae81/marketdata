#!/usr/bin/env python3
"""
Convert existing US 5-minute text files to Parquet format.
One-time conversion script for migrating historical data.

Required packages:
    pip install pandas pyarrow numpy

Usage:
    python us5m_to_parquet.py <directory>
    
Example:
    python us5m_to_parquet.py data/US-5m/
"""

import sys
from pathlib import Path

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

try:
    import numpy as np
except ImportError:
    print("[ERROR] Required package 'numpy' is not installed.", file=sys.stderr)
    print("Please install it with: pip install numpy", file=sys.stderr)
    sys.exit(1)


def validate_parquet(txt_file, parquet_file):
    """Validate that parquet file matches the txt file"""
    try:
        # Read both files
        txt_df = pd.read_csv(txt_file, sep='\t', header=None,
                            names=['symbol', 'price', 'volume', 'time'],
                            dtype={'symbol': str, 'price': float, 'volume': float, 'time': str})
        
        # Round volume to integer (same as conversion)
        txt_df['volume'] = txt_df['volume'].round().astype(int)
        
        # Parse date from filename
        date_str = txt_file.stem
        txt_df['dt'] = pd.to_datetime(date_str + ' ' + txt_df['time'])
        txt_df = txt_df[['symbol', 'dt', 'price', 'volume']]
        
        parquet_df = pd.read_parquet(parquet_file)
        
        # Check row count
        if len(txt_df) != len(parquet_df):
            return False
        
        # Check columns
        if txt_df.columns.tolist() != parquet_df.columns.tolist():
            return False
        
        # Compare data values
        for col in txt_df.columns:
            if pd.api.types.is_datetime64_any_dtype(txt_df[col]) or pd.api.types.is_datetime64_any_dtype(parquet_df[col]):
                # Compare datetime columns
                if not txt_df[col].equals(parquet_df[col]):
                    return False
            elif txt_df[col].dtype == 'object' or parquet_df[col].dtype == 'object':
                if not txt_df[col].equals(parquet_df[col]):
                    return False
            else:
                if not np.allclose(txt_df[col], parquet_df[col], equal_nan=True):
                    return False
        
        return True
    except Exception:
        return False


def convert_file(txt_file):
    """Convert a single text file to Parquet"""
    txt_path = Path(txt_file)
    if not txt_path.exists():
        print(f"[ERROR] File not found: {txt_file}")
        return False
    
    # Determine output path (same location, .parquet extension)
    output_file = txt_path.with_suffix('.parquet')
    
    # Check if parquet already exists and is valid
    if output_file.exists():
        if validate_parquet(txt_path, output_file):
            print(f"[SKIP] {output_file.name} already exists and is valid")
            return True
        else:
            print(f"[WARN] {output_file.name} exists but validation failed, reconverting...")
    
    # Parse date from filename
    date_str = txt_path.stem  # YYYY-MM-DD
    
    # Read text file
    try:
        df = pd.read_csv(txt_path, sep='\t', header=None,
                         names=['symbol', 'price', 'volume', 'time'],
                         dtype={'symbol': str, 'price': float, 'volume': float, 'time': str})
    except Exception as e:
        print(f"[ERROR] Failed to read {txt_file}: {e}")
        return False
    
    # Round volume to integer (handle fractional shares)
    df['volume'] = df['volume'].round().astype(int)
    
    # Create datetime column
    df['dt'] = pd.to_datetime(date_str + ' ' + df['time'])
    df = df[['symbol', 'dt', 'price', 'volume']]
    
    # Save to Parquet
    df.to_parquet(output_file, compression='snappy', index=False)
    print(f"[OK] {txt_path.name} -> {output_file.name} ({len(df)} records)")
    return True


def convert_directory(directory):
    """Convert all text files in a directory tree"""
    directory = Path(directory)
    
    txt_files = sorted(directory.rglob("*.txt"))
    if not txt_files:
        print(f"[WARN] No .txt files found in {directory}")
        return
    
    print(f"[INFO] Found {len(txt_files)} text files to convert")
    success_count = 0
    
    for txt_file in txt_files:
        if convert_file(txt_file):
            success_count += 1
    
    print(f"\n[INFO] Converted {success_count}/{len(txt_files)} files successfully")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert US 5-minute text files to Parquet')
    parser.add_argument('directory', nargs='?', default='.',
                       help='Directory containing text files to convert (default: current directory)')
    
    args = parser.parse_args()
    
    convert_directory(args.directory)

