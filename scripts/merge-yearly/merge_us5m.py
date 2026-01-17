
import sys
from pathlib import Path

# Add script directory to path to import utils
sys.path.append(str(Path(__file__).parent))
import yearly_utils as utils

def main():
    utils.check_dependencies()
    
    project_root = utils.get_project_root()
    data_dir = project_root / "data" / "US-5m"
    
    if not data_dir.exists():
        print(f"[WARN] Data directory not found: {data_dir}")
        return

    print("==========================================")
    print("MarketData Yearly Merge: US-5m")
    print(f"Target: {data_dir}")
    print("==========================================")

    groups = utils.get_yearly_groups(data_dir)
    
    for year_key, files in sorted(groups.items()):
        # Only merge if it's a past year
        if not utils.is_past_year(year_key):
            print(f"[SKIP] {year_key}: Not a past year yet")
            continue
            
        if not files:
            continue

        # Merge
        # US-5m sort key: symbol, dt
        utils.merge_yearly_and_validate(year_key, files, data_dir, ['symbol', 'dt'])

if __name__ == "__main__":
    main()
