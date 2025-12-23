@echo off
REM Setup development environment on Windows

echo ======================================================================
echo KRX Price Development Environment Setup
echo ======================================================================
echo.

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo [OK] Dependencies installed

REM Run tests to verify setup
echo.
echo Running tests to verify setup...
python -m unittest tests.test_symbol.TestParseSymbols -v

echo.
echo ======================================================================
echo Development environment setup complete!
echo ======================================================================
echo.
echo To activate the virtual environment, run:
echo   .venv\Scripts\activate.bat
echo.
echo To run tests:
echo   python -m unittest discover tests -v              # All tests
echo   python -m unittest tests.test_symbol tests.test_day tests.test_minute -v  # Unit tests only
echo   python -m unittest tests.test_integration -v      # Integration tests only
