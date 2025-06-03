@echo off
cd /d "%~dp0"

:: Try python3 first
where python3 >nul 2>&1
if %errorlevel%==0 (
    python vtoes_tattoo_merger.py
    :: python3 extract_png.py
    goto end
)

:: Fallback to python
where python >nul 2>&1
if %errorlevel%==0 (
    python vtoes_tattoo_merger.py
    :: python extract_png.py
    goto end
)

echo ❌ Python is not installed or not in PATH.
pause

:end
pause
