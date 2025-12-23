@echo off
setlocal
REM Setup development environment on Windows
REM Sets up local development environment for KRX Price Collector

echo [INFO] Setting up KRX Price Collector development environment...
echo.

REM Check for Python (Required)
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed
    echo    Please install Python 3.11 or later
    exit /b 1
)
echo [OK] Python is installed

REM Check if Docker is installed (Optional)
set DOCKER_FOUND=0
where docker >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] Docker is installed
    set DOCKER_FOUND=1
) else (
    echo [WARN] Docker is not installed
    echo    Docker is used for containerized execution.
    echo    Please install Docker Desktop: https://www.docker.com/products/docker-desktop
)

REM Check if Docker Compose is available (Optional)
set COMPOSE_FOUND=0
if %DOCKER_FOUND% equ 1 (
    docker compose version >nul 2>nul
    if %errorlevel% equ 0 (
        echo [OK] Docker Compose is available
        set COMPOSE_FOUND=1
    ) else (
        echo [WARN] Docker Compose is not available
    )
)
echo.

REM Create .venv if it doesn't exist
if not exist ".venv" (
    echo [INFO] Creating Python virtual environment (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
    
    echo [INFO] Installing dependencies...
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies.
        exit /b 1
    )
    echo [OK] Dependencies installed
    echo.
) else (
    echo [OK] Python virtual environment already exists
    echo.
)

REM Build Docker images
if %COMPOSE_FOUND% equ 1 (
    echo [INFO] Building Docker images...
    docker compose build
    if %errorlevel% equ 0 (
        echo [OK] Docker images built
    ) else (
        echo [WARN] Docker build failed.
    )
    echo.
)

REM Run tests to verify setup
echo [INFO] Running initial tests to verify setup...
if not defined VIRTUAL_ENV (
    call .venv\Scripts\activate.bat
)
python -m unittest tests.test_symbol.TestParseSymbols -v
if %errorlevel% neq 0 (
    echo [WARN] Initial tests failed. Please check your environment.
)
echo.

echo ============================================================
echo [DONE] Development environment setup complete!
echo ============================================================
echo.
echo Next steps:
echo.
echo 1. Activate virtual environment (for local development/tests):
echo    .venv\Scripts\activate.bat
echo.
echo 2. Run unit tests:
echo    python -m unittest tests.test_symbol tests.test_day tests.test_minute -v
echo.
echo 3. Run integration tests (real API calls):
echo    python -m unittest tests.test_integration -v
echo.
echo 4. Run using Docker Compose (immediate execution):
echo    docker compose run --rm app
echo.
echo Note: For production deployment with automatic scheduling,
echo    use setup-systemd.sh on a Linux server
echo.

endlocal
exit /b 0
