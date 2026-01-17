
import unittest
import tempfile
import shutil
import os
import sys
import pandas as pd
from datetime import date
from pathlib import Path

# Add src and scripts/merge-yearly to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts' / 'merge-yearly'))

import yearly_utils as utils

class TestMergeYearlyLogic(unittest.TestCase):
    """Test yearly merge logic"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.target_dir = Path(self.test_dir) / 'data' / 'KR-1d'
        self.year_dir = self.target_dir / '2020'
        self.year_dir.mkdir(parents=True, exist_ok=True)
        
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def test_past_year(self):
        """Test is_past_year logic"""
        this_year = date.today().year
        self.assertTrue(utils.is_past_year(str(this_year - 1)))
        self.assertFalse(utils.is_past_year(str(this_year)))
        self.assertFalse(utils.is_past_year(str(this_year + 1)))

    def test_merge_yearly_and_validate(self):
        """Test the yearly merge, validation, and cleanup process"""
        # Create 3 monthly files for 2020
        months = ['2020-01', '2020-02', '2020-03']
        files = []
        
        for m in months:
            f_path = self.year_dir / f"{m}.parquet"
            df = pd.DataFrame({
                'symbol': ['005930'],
                'date': pd.to_datetime([f"{m}-01"]),
                'price': [1000]
            })
            df.to_parquet(f_path)
            files.append(f_path)
            
        # Verify monthly files exist
        self.assertEqual(len(list(self.year_dir.glob('*.parquet'))), 3)
        
        # Merge
        utils.merge_yearly_and_validate('2020', files, self.target_dir, ['symbol', 'date'])
        
        # Verify cleanup (monthly files gone)
        # Search for YYYY-MM.parquet pattern
        remaining = list(self.year_dir.glob('2020-*.parquet'))
        self.assertEqual(len(remaining), 0)
        
        # Verify yearly file exists
        yearly_file = self.year_dir / '2020.parquet'
        self.assertTrue(yearly_file.exists())
        
        # Verify content
        merged_df = pd.read_parquet(yearly_file)
        self.assertEqual(len(merged_df), 3)
        self.assertEqual(str(merged_df.iloc[0]['date'].date()), '2020-01-01')
        self.assertEqual(str(merged_df.iloc[2]['date'].date()), '2020-03-01')

if __name__ == '__main__':
    unittest.main()
