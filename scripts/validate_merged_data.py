#!/usr/bin/env python3
"""
Validation wrapper module for testing.
Provides a unified interface to validation functions used by tests.
"""

import sys
import pandas as pd
from pathlib import Path

# Add merge-yearly to path
sys.path.insert(0, str(Path(__file__).parent / 'merge-yearly'))
import yearly_utils as utils


def validate_year(market_type, year_dir, year_key):
    """
    Validate yearly parquet file against source txt files.
    
    Args:
        market_type: Market type (e.g., 'KR-1d', 'KR-1m', 'US-5m')
        year_dir: Path to year directory containing txt files and yearly parquet
        year_key: Year string (e.g., '2020')
    """
    year_dir = Path(year_dir)
    yearly_parquet = year_dir / f"{year_key}.parquet"
    
    if not yearly_parquet.exists():
        print(f"[WARN] Yearly parquet not found: {yearly_parquet}")
        return False
    
    # Read all txt files for this year
    all_txts = sorted(year_dir.glob("*.txt"))
    # Exclude dotfiles
    all_txts = [f for f in all_txts if not f.name.startswith('.')]
    
    if not all_txts:
        print(f"[WARN] No txt files found for year {year_key}")
        return False
    
    # Determine sort columns based on market type
    if market_type in ['KR-1m', 'US-5m']:
        sort_cols = ['symbol', 'dt']
    elif market_type == 'KR-1d':
        sort_cols = ['symbol', 'date']
    else:
        sort_cols = ['symbol']
    
    # Read and combine TXT data
    txt_dfs = [utils.read_txt_file(f, market_type) for f in all_txts]
    txt_dfs = [df for df in txt_dfs if df is not None]
    
    if not txt_dfs:
        print(f"[ERROR] Failed to read any txt files for year {year_key}")
        return False
    
    combined_txt = pd.concat(txt_dfs, ignore_index=True).drop_duplicates().sort_values(sort_cols).reset_index(drop=True)
    
    # Read and process Parquet data
    try:
        yearly_pq = pd.read_parquet(yearly_parquet).drop_duplicates().sort_values(sort_cols).reset_index(drop=True)
        return utils.compare_dfs(combined_txt, yearly_pq, market_type, f"Year {year_key}", sort_cols)
    except Exception as e:
        print(f"[ERROR] Failed to read or process {yearly_parquet}: {e}")
        return False


if __name__ == "__main__":
    print("This module is intended to be imported by tests.")
