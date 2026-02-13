import unittest
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

class TestMain(unittest.TestCase):
    """Test cases for main.py"""

    def test_import(self):
        """Test if main can be imported"""
        try:
            import main
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import main: {e}")

if __name__ == '__main__':
    unittest.main()
