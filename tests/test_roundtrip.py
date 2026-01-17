import unittest
import tempfile
import shutil
import os
import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestKRDayRoundtrip(unittest.TestCase):
    """Test KR day data fetch-extract round-trip with Parquet"""
    
    def setUp(self):
        """Create temporary directories for test data"""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, 'data', 'KR-1d', '2026')
        os.makedirs(self.data_dir, exist_ok=True)
        
    def tearDown(self):
        """Clean up temporary directories"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def test_kr_day_roundtrip(self):
        """Test that KR day data survives save-load cycle"""
        import extract
        
        # Create sample Parquet file directly
        test_date = '2026-01-15'
        parquet_file = os.path.join(self.data_dir, f'{test_date}.parquet')
        
        # Sample data
        df = pd.DataFrame({
            'symbol': ['005930', '000660', '035720'],
            'date': pd.to_datetime(test_date),
            'open': [120000, 50000, 80000],
            'high': [125000, 52000, 82000],
            'low': [119000, 49000, 79000],
            'close': [124000, 51000, 81000],
            'volume': [10000000, 5000000, 3000000]
        })
        
        # Save to Parquet
        df.to_parquet(parquet_file, compression='snappy', index=False)
        
        # Extract the data
        result_df = extract.extract_kr_day('005930', test_date, test_date, 
                                           data_dir=os.path.join(self.test_dir, 'data', 'KR-1d'))
        
        # Verify data integrity
        self.assertEqual(len(result_df), 1)
        self.assertEqual(result_df.iloc[0]['symbol'], '005930')
        self.assertEqual(int(result_df.iloc[0]['open']), 120000)
        self.assertEqual(int(result_df.iloc[0]['high']), 125000)
        self.assertEqual(int(result_df.iloc[0]['low']), 119000)
        self.assertEqual(int(result_df.iloc[0]['close']), 124000)
        self.assertEqual(int(result_df.iloc[0]['volume']), 10000000)


class TestKR1minRoundtrip(unittest.TestCase):
    """Test KR 1min data fetch-extract round-trip with Parquet"""
    
    def setUp(self):
        """Create temporary directories for test data"""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, 'data', 'KR-1m', '2026')
        os.makedirs(self.data_dir, exist_ok=True)
        
    def tearDown(self):
        """Clean up temporary directories"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def test_kr_1min_roundtrip(self):
        """Test that KR 1min data survives save-load cycle"""
        import extract
        
        # Create sample Parquet file directly
        test_date = '2026-01-15'
        parquet_file = os.path.join(self.data_dir, f'{test_date}.parquet')
        
        # Sample data
        df = pd.DataFrame({
            'symbol': ['005930', '005930', '005930', '000660', '000660'],
            'dt': pd.to_datetime([
                '2026-01-15 09:00:00',
                '2026-01-15 09:01:00',
                '2026-01-15 09:02:00',
                '2026-01-15 09:00:00',
                '2026-01-15 09:01:00'
            ]),
            'price': [124000, 124500, 124200, 51000, 51200],
            'volume': [100000, 150000, 120000, 50000, 60000]
        })
        
        # Save to Parquet
        df.to_parquet(parquet_file, compression='snappy', index=False)
        
        # Extract the data
        result_df = extract.extract_kr_1min('005930', '2026-01-15 09:00:00', '2026-01-15 09:02:00',
                                            data_dir=os.path.join(self.test_dir, 'data', 'KR-1m'))
        
        # Verify data integrity
        self.assertEqual(len(result_df), 3)
        self.assertEqual(result_df.iloc[0]['symbol'], '005930')
        self.assertEqual(int(result_df.iloc[0]['price']), 124000)
        self.assertEqual(int(result_df.iloc[0]['volume']), 100000)
        
        # Verify chronological order
        self.assertTrue(result_df.iloc[0]['dt'] < result_df.iloc[1]['dt'])
        self.assertTrue(result_df.iloc[1]['dt'] < result_df.iloc[2]['dt'])


class TestUS5minRoundtrip(unittest.TestCase):
    """Test US 5min data fetch-extract round-trip with Parquet"""
    
    def setUp(self):
        """Create temporary directories for test data"""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, 'data', 'US-5m', '2025')
        os.makedirs(self.data_dir, exist_ok=True)
        
    def tearDown(self):
        """Clean up temporary directories"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def test_us_5min_roundtrip(self):
        """Test that US 5min data survives save-load cycle"""
        import extract
        
        # Create sample Parquet file directly
        test_date = '2025-12-15'
        parquet_file = os.path.join(self.data_dir, f'{test_date}.parquet')
        
        # Sample data
        df = pd.DataFrame({
            'symbol': ['AAPL', 'AAPL', 'AAPL', 'TSLA', 'TSLA'],
            'dt': pd.to_datetime([
                '2025-12-15 09:30:00',
                '2025-12-15 09:35:00',
                '2025-12-15 09:40:00',
                '2025-12-15 09:30:00',
                '2025-12-15 09:35:00'
            ]),
            'price': [180.50, 180.75, 180.60, 250.00, 251.50],
            'volume': [1000000, 1200000, 1100000, 800000, 900000]
        })
        
        # Save to Parquet
        df.to_parquet(parquet_file, compression='snappy', index=False)
        
        # Extract the data
        result_df = extract.extract_us_5min('AAPL', '2025-12-15 09:30:00', '2025-12-15 09:40:00',
                                            data_dir=os.path.join(self.test_dir, 'data', 'US-5m'))
        
        # Verify data integrity
        self.assertEqual(len(result_df), 3)
        self.assertEqual(result_df.iloc[0]['symbol'], 'AAPL')
        self.assertAlmostEqual(float(result_df.iloc[0]['price']), 180.50, places=2)
        self.assertEqual(int(result_df.iloc[0]['volume']), 1000000)
        
        # Verify chronological order
        self.assertTrue(result_df.iloc[0]['dt'] < result_df.iloc[1]['dt'])
        self.assertTrue(result_df.iloc[1]['dt'] < result_df.iloc[2]['dt'])


if __name__ == '__main__':
    unittest.main()
