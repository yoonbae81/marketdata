
import sys
from pathlib import Path

# Add script directory to path to import utils
sys.path.append(str(Path(__file__).parent))
import monthly_utils as utils

def main():
    utils.check_dependencies()
    
    project_root = utils.get_project_root()
    data_dir = project_root / "data" / "KR-1m"
    
    if not data_dir.exists():
        print(f"[WARN] Data directory not found: {data_dir}")
        return

    print("==========================================")
    print("MarketData Monthly Merge: KR-1m")
    print(f"Target: {data_dir}")
    print("==========================================")

    # Scan years
    for year_dir in sorted(data_dir.glob('*')):
        if not year_dir.is_dir():
            continue
            
        try:
            year = int(year_dir.name)
        except ValueError:
            continue
            
        groups = utils.get_monthly_groups(data_dir, year)
        
        for month_key, files in sorted(groups.items()):
            # Check if it's safe to merge (5 days past month end)
            if not utils.is_safe_to_merge(month_key):
                print(f"[SKIP] {month_key}: Not 5 days past month end yet")
                continue
                
            if not files:
                continue

            # Merge
            # KR-1m sort key: symbol, dt
            utils.merge_and_validate(month_key, files, data_dir, ['symbol', 'dt'])

if __name__ == "__main__":
    main()
