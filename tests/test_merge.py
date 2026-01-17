
import unittest
import tempfile
import shutil
import os
import sys
import pandas as pd
from datetime import datetime, date, timedelta
from pathlib import Path

# Add src and scripts/merge-monthly to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts' / 'merge-monthly'))

import monthly_utils as utils

class TestMergeLogic(unittest.TestCase):
    """Test monthly merge logic and safety checks"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / 'data' / 'KR-1d' / '2020'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def test_safe_to_merge(self):
        """Test the 5-day aging rule"""
        today = date.today()
        
        # safely past dates
        last_month = today.replace(day=1) - timedelta(days=1)
        safe_month_str = last_month.strftime('%Y-%m')
        
        # If today is 2026-01-17
        # previous month (2025-12) ended 2025-12-31. +5 days = 2026-01-05. Safe.
        # current month (2026-01) ends 2026-01-31. +5 days = 2026-02-05. Unsafe.
        
        current_month_str = today.strftime('%Y-%m')
        
        # This test might be tricky due to dynamic dates, so we mock logic
        # 2 months ago is always safe
        two_months_ago = (today.replace(day=1) - timedelta(days=40)).strftime('%Y-%m')
        self.assertTrue(utils.is_safe_to_merge(two_months_ago))
        
        # Future month is unsafe
        future_month = (today.replace(day=1) + timedelta(days=40)).strftime('%Y-%m')
        self.assertFalse(utils.is_safe_to_merge(future_month))
        
        # Current month is unsafe
        self.assertFalse(utils.is_safe_to_merge(current_month_str))

    def test_merge_and_validate(self):
        """Test the merge, validation, and cleanup process"""
        # Create 3 daily files for 2020-01
        days = ['2020-01-01', '2020-01-02', '2020-01-03']
        files = []
        
        for d in days:
            f_path = self.data_dir / f"{d}.parquet"
            df = pd.DataFrame({
                'symbol': ['005930'],
                'date': pd.to_datetime([d]),
                'price': [1000]
            })
            df.to_parquet(f_path)
            files.append(f_path)
            
        # Verify files exist
        self.assertEqual(len(list(self.data_dir.glob('*.parquet'))), 3)
        
        # Merge
        utils.merge_and_validate('2020-01', files, self.data_dir.parent, ['symbol', 'date'])
        
        # Verify cleanup (daily files gone)
        daily_files = list(self.data_dir.glob('2020-01-*.parquet'))
        self.assertEqual(len(daily_files), 0)
        
        # Verify monthly file exists
        monthly_file = self.data_dir / '2020-01.parquet'
        self.assertTrue(monthly_file.exists())
        
        # Verify content
        merged_df = pd.read_parquet(monthly_file)
        self.assertEqual(len(merged_df), 3)
        self.assertEqual(str(merged_df.iloc[0]['date'].date()), '2020-01-01')
        self.assertEqual(str(merged_df.iloc[2]['date'].date()), '2020-01-03')

if __name__ == '__main__':
    unittest.main()
