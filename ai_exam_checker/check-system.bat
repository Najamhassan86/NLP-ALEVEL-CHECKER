@echo off
echo ============================================
echo AI Exam Checker - System Check
echo ============================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python not found!
    echo Install Python 3.11 from: https://www.python.org/downloads/
    goto :end
) else (
    python --version
    echo [OK] Python found
)
echo.

echo Checking Python version...
python -c "import sys; v=sys.version_info; print(f'{v.major}.{v.minor}.{v.micro}'); exit(0 if v.major==3 and v.minor>=11 else 1)"
if errorlevel 1 (
    echo [WARNING] Python version might not be compatible
    echo Recommended: Python 3.11
    echo Your version is shown above
) else (
    echo [OK] Python version is compatible
)
echo.

echo Checking pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] pip not found!
    echo Install pip or reinstall Python
    goto :end
) else (
    pip --version
    echo [OK] pip found
)
echo.

echo Checking disk space...
wmic logicaldisk where "DeviceID='C:'" get FreeSpace /format:value | findstr FreeSpace
echo [INFO] You need at least 10GB free for models and packages
echo.

echo Checking internet connection...
ping -n 1 pypi.org >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Cannot reach pypi.org
    echo You may have internet or firewall issues
    echo Package installation might fail
) else (
    echo [OK] Internet connection working
)
echo.

echo Checking if Ollama is installed...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Ollama not installed yet
    echo Download from: https://ollama.com/download
) else (
    ollama --version
    echo [OK] Ollama found

    echo Checking for llama3.1:8b model...
    ollama list | findstr llama3.1 >nul 2>&1
    if errorlevel 1 (
        echo [INFO] Model not pulled yet
        echo Run: ollama pull llama3.1:8b
    ) else (
        echo [OK] llama3.1:8b model found
    )
)
echo.

echo Checking if virtual environment exists...
if exist venv (
    echo [OK] Virtual environment exists
) else (
    echo [INFO] Virtual environment not created yet
    echo Run setup.bat to create it
)
echo.

echo ============================================
echo System Check Complete
echo ============================================
echo.
echo Summary:
echo - If all checks pass, run: setup.bat
echo - If Python version is not 3.11, download it first
echo - If Ollama not installed, download it after setup
echo.

:end
pause
