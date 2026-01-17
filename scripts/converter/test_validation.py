#!/usr/bin/env python3
"""
Test the validation functionality of the converter scripts.
Creates test files and demonstrates the validation routine.
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Import the converter modules
sys.path.insert(0, str(Path(__file__).parent))
import kr1m_to_parquet
import kr1d_to_parquet
import us5m_to_parquet


def test_kr1m_validation():
    """Test KR 1-minute validation"""
    print("=" * 80)
    print("Testing KR-1m Validation")
    print("=" * 80)
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create a test txt file
        txt_file = tmpdir / "2024-01-01.txt"
        txt_file.write_text("000020\t6260\t1716\t10:00\n000040\t456\t4465\t10:01\n")
        
        print(f"\n[INFO] Created test file: {txt_file.name}")
        
        # First conversion
        print("\n[TEST 1] First conversion (should create parquet)")
        result = kr1m_to_parquet.convert_file(txt_file)
        print(f"Result: {'SUCCESS' if result else 'FAILED'}")
        
        # Second conversion (should skip)
        print("\n[TEST 2] Second conversion (should skip - valid parquet exists)")
        result = kr1m_to_parquet.convert_file(txt_file)
        print(f"Result: {'SUCCESS' if result else 'FAILED'}")
        
        # Corrupt the parquet file
        parquet_file = tmpdir / "2024-01-01.parquet"
        print(f"\n[TEST 3] Corrupting parquet file...")
        parquet_file.write_bytes(b"corrupted data")
        
        # Third conversion (should detect corruption and reconvert)
        print("\n[TEST 4] Third conversion (should detect corruption and reconvert)")
        txt_file.write_text("000020\t6260\t1716\t10:00\n000040\t456\t4465\t10:01\n")
        result = kr1m_to_parquet.convert_file(txt_file)
        print(f"Result: {'SUCCESS' if result else 'FAILED'}")
        
        print("\n" + "=" * 80)
        print("KR-1m Validation Test Complete")
        print("=" * 80)


def test_kr1d_validation():
    """Test KR daily validation"""
    print("\n" + "=" * 80)
    print("Testing KR-1d Validation")
    print("=" * 80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        txt_file = tmpdir / "2024-01-01.txt"
        txt_file.write_text("000020\t6250\t6300\t6190\t6210\t73005\n")
        
        print(f"\n[INFO] Created test file: {txt_file.name}")
        
        print("\n[TEST 1] First conversion")
        result = kr1d_to_parquet.convert_file(txt_file)
        print(f"Result: {'SUCCESS' if result else 'FAILED'}")
        
        print("\n[TEST 2] Second conversion (should skip)")
        result = kr1d_to_parquet.convert_file(txt_file)
        print(f"Result: {'SUCCESS' if result else 'FAILED'}")
        
        print("\n" + "=" * 80)
        print("KR-1d Validation Test Complete")
        print("=" * 80)


def test_us5m_validation():
    """Test US 5-minute validation"""
    print("\n" + "=" * 80)
    print("Testing US-5m Validation")
    print("=" * 80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        txt_file = tmpdir / "2024-01-01.txt"
        txt_file.write_text("AAPB\t32.29\t319\t09:30\n")
        
        print(f"\n[INFO] Created test file: {txt_file.name}")
        
        print("\n[TEST 1] First conversion")
        result = us5m_to_parquet.convert_file(txt_file)
        print(f"Result: {'SUCCESS' if result else 'FAILED'}")
        
        print("\n[TEST 2] Second conversion (should skip)")
        result = us5m_to_parquet.convert_file(txt_file)
        print(f"Result: {'SUCCESS' if result else 'FAILED'}")
        
        print("\n" + "=" * 80)
        print("US-5m Validation Test Complete")
        print("=" * 80)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Converter Validation Test Suite")
    print("=" * 80)
    
    try:
        test_kr1m_validation()
        test_kr1d_validation()
        test_us5m_validation()
        
        print("\n" + "=" * 80)
        print("✓ All validation tests completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
