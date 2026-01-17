
import sys
import re
import pandas as pd
from pathlib import Path

# Add script directory to path to import utils
sys.path.append(str(Path(__file__).parent))
import yearly_utils as utils

MARKET_TYPE = 'KR-1d'
DATA_SUBDIR = 'KR-1d'

def validate_kr1d_yearly():
    utils.check_dependencies()
    
    project_root = utils.get_project_root()
    data_dir = project_root / "data" / DATA_SUBDIR
    
    if not data_dir.exists():
        print(f"[WARN] Data directory not found: {data_dir}")
        return

    print(f"\nScanning {MARKET_TYPE} in {data_dir} for yearly validation...")
    
    # Walk through years
    for year_dir in sorted(data_dir.glob('*')):
        if not year_dir.is_dir(): 
            continue
            
        year_key = year_dir.name
        try:
            int(year_key)
        except ValueError:
            continue

        yearly_parquet = year_dir / f"{year_key}.parquet"
        if not yearly_parquet.exists():
            continue

        print(f"[CHECK] Validating yearly {year_key} vs {yearly_parquet.name}...")
        
        # 1. Read all txt files for this year
        all_txts = sorted(year_dir.glob("*.txt"))
        # Exclude dotfiles
        all_txts = [f for f in all_txts if not f.name.startswith('.')]
        
        if not all_txts:
            print(f"[WARN] No txt files found for year {year_key} but yearly parquet exists.")
            continue

        sort_cols = ['symbol', 'date']

        # Read and deduplicate TXT data
        txt_dfs = [utils.read_txt_file(f, MARKET_TYPE) for f in all_txts]
        txt_dfs = [df for df in txt_dfs if df is not None]
        if not txt_dfs:
            continue
            
        combined_txt = pd.concat(txt_dfs, ignore_index=True).drop_duplicates().sort_values(sort_cols).reset_index(drop=True)
        
        # Read and deduplicate Parquet data
        try:
            yearly_pq = pd.read_parquet(yearly_parquet).drop_duplicates().sort_values(sort_cols).reset_index(drop=True)
            utils.compare_dfs(combined_txt, yearly_pq, MARKET_TYPE, f"Year {year_key}", sort_cols)
        except Exception as e:
            print(f"[ERROR] Failed to read or process {yearly_parquet}: {e}")

if __name__ == "__main__":
    validate_kr1d_yearly()
