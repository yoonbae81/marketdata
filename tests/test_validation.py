
import unittest
import tempfile
import shutil
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

import validate_merged_data as vmd

class TestValidationLogic(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / 'data' / 'KR-1d'
        self.year_dir = self.data_dir / '2020'
        self.year_dir.mkdir(parents=True, exist_ok=True)
        
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def test_validate_year_success(self):
        # 1. Create mock txt files
        df1 = pd.DataFrame({
            'symbol': ['005930'],
            'date': [pd.to_datetime('2020-01-01')],
            'open': [100], 'high': [110], 'low': [90], 'close': [105], 'volume': [1000]
        })
        df2 = pd.DataFrame({
            'symbol': ['005930'],
            'date': [pd.to_datetime('2020-02-01')],
            'open': [105], 'high': [115], 'low': [95], 'close': [110], 'volume': [1100]
        })
        
        # Save as txt (tab-separated, no header)
        df1[['symbol', 'open', 'high', 'low', 'close', 'volume']].to_csv(self.year_dir / '2020-01-01.txt', sep='\t', header=False, index=False)
        df2[['symbol', 'open', 'high', 'low', 'close', 'volume']].to_csv(self.year_dir / '2020-02-01.txt', sep='\t', header=False, index=False)
        
        # 2. Create yearly parquet
        combined = pd.concat([df1, df2], ignore_index=True)
        combined.to_parquet(self.year_dir / '2020.parquet', index=False)
        
        # 3. Validate
        # Redirect stdout to check output
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            vmd.validate_year('KR-1d', self.year_dir, '2020')
        
        output = f.getvalue()
        self.assertIn("[OK] Year 2020: Perfectly matched 2 rows.", output)

    def test_validate_year_fail(self):
        # 1. Create mock txt file
        df1 = pd.DataFrame({
            'symbol': ['005930'],
            'date': [pd.to_datetime('2020-01-01')],
            'open': [100], 'high': [110], 'low': [90], 'close': [105], 'volume': [1000]
        })
        df1[['symbol', 'open', 'high', 'low', 'close', 'volume']].to_csv(self.year_dir / '2020-01-01.txt', sep='\t', header=False, index=False)
        
        # 2. Create yearly parquet with different data
        df_wrong = df1.copy()
        df_wrong['close'] = 999
        df_wrong.to_parquet(self.year_dir / '2020.parquet', index=False)
        
        # 3. Validate
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            vmd.validate_year('KR-1d', self.year_dir, '2020')
        
        output = f.getvalue()
        self.assertIn("[FAIL] Column 'close' mismatch count: 1", output)
        self.assertIn("[FAIL] Year 2020: Validation failed with 1 total mismatches.", output)

if __name__ == '__main__':
    unittest.main()
