@echo off
REM Development Environment Setup Script for Windows
REM Sets up local development environment for MarketData

echo Setting up MarketData development environment...
echo.

REM Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed
    echo Please install Python 3.11 or later
    exit /b 1
)
echo [OK] Python is installed
echo.

REM Create .venv if it doesn't exist
if not exist ".venv" (
    echo [INFO] Creating Python virtual environment (.venv)...
    python -m venv .venv
    echo [OK] Virtual environment created
    echo.
    
    echo [INFO] Installing dependencies...
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo [OK] Dependencies installed
    echo.
) else (
    echo [OK] Python virtual environment already exists
    echo.
)

REM Create necessary directories
echo [INFO] Creating data directories...
if not exist "data\KR-1m" mkdir data\KR-1m
if not exist "data\KR-1d" mkdir data\KR-1d
if not exist "data\US-5m" mkdir data\US-5m
echo [OK] Directories created
echo.

REM Run tests to verify setup
echo [INFO] Running initial tests to verify setup...
if not defined VIRTUAL_ENV (
    call .venv\Scripts\activate.bat
)
python -m unittest discover tests -v
if %errorlevel% neq 0 (
    echo [WARN] Some tests failed. Please check your environment.
)
echo.

echo ============================================================
echo [DONE] MarketData local environment setup complete!
echo ============================================================
echo.
echo Next steps:
echo.
echo 1. Activate virtual environment:
echo    .venv\Scripts\activate.bat
echo.
echo 2. Run the fetch script:
echo    python src\fetch_kr1m.py -d 2026-01-17
echo.
echo 3. Extract data:
echo    python src\extract.py min 005930 2026-01-17 2026-01-17
echo.

endlocal
exit /b 0
