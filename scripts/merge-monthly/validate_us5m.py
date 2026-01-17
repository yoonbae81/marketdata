
import sys
import re
import pandas as pd
from pathlib import Path

# Add script directory to path to import utils
sys.path.append(str(Path(__file__).parent))
import monthly_utils as utils

MARKET_TYPE = 'US-5m'
DATA_SUBDIR = 'US-5m'

def validate_us5m_monthly():
    utils.check_dependencies()
    
    project_root = utils.get_project_root()
    data_dir = project_root / "data" / DATA_SUBDIR
    
    if not data_dir.exists():
        print(f"[WARN] Data directory not found: {data_dir}")
        return

    print(f"\nScanning {MARKET_TYPE} in {data_dir} for monthly validation...")
    
    # Walk through years
    for year_dir in sorted(data_dir.glob('*')):
        if not year_dir.is_dir(): 
            continue
            
        year_name = year_dir.name
        try:
            int(year_name)
        except ValueError:
            continue

        # Group txt files by month
        txt_by_month = {}
        date_pattern = re.compile(r'^(\d{4})-(\d{2})-\d{2}$')
        
        all_txts = sorted(year_dir.glob("*.txt"))
        # Exclude dotfiles
        all_txts = [f for f in all_txts if not f.name.startswith('.')]
        
        for f in all_txts:
            match = date_pattern.match(f.stem)
            if match:
                month_key = f"{match.group(1)}-{match.group(2)}"
                if month_key not in txt_by_month:
                    txt_by_month[month_key] = []
                txt_by_month[month_key].append(f)
        
        sort_cols = ['symbol', 'dt']

        for month_key, files in sorted(txt_by_month.items()):
            monthly_parquet = year_dir / f"{month_key}.parquet"
            
            if not monthly_parquet.exists():
                print(f"[SKIP] {month_key}: Monthly parquet not found")
                continue
            
            print(f"[CHECK] Validating {month_key} ({len(files)} txt files) vs {monthly_parquet.name}...")
            
            # Read and deduplicate TXT data
            txt_dfs = [utils.read_txt_file(f, MARKET_TYPE) for f in files]
            txt_dfs = [df for df in txt_dfs if df is not None]
            if not txt_dfs:
                continue
                
            combined_txt = pd.concat(txt_dfs, ignore_index=True).drop_duplicates().sort_values(sort_cols).reset_index(drop=True)
            
            # Read and deduplicate Parquet data
            try:
                monthly_pq = pd.read_parquet(monthly_parquet).drop_duplicates().sort_values(sort_cols).reset_index(drop=True)
                utils.compare_dfs(combined_txt, monthly_pq, MARKET_TYPE, month_key, sort_cols)
            except Exception as e:
                print(f"[ERROR] Failed to read or process {monthly_parquet}: {e}")

if __name__ == "__main__":
    validate_us5m_monthly()
