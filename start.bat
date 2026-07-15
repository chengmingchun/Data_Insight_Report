@echo off
setlocal

cd /d "%~dp0"
set "VENV_PY=.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [setup] Creating Python virtual environment...
    where python >nul 2>&1
    if not errorlevel 1 (
        python -m venv .venv
    ) else (
        where py >nul 2>&1
        if errorlevel 1 goto :python_missing
        py -3 -m venv .venv
    )
    if errorlevel 1 goto :venv_failed
)

"%VENV_PY%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 goto :python_version

"%VENV_PY%" -c "import streamlit, pandas, plotly, jinja2, pydantic, pydantic_settings, openai" >nul 2>&1
if errorlevel 1 (
    echo [setup] Installing project dependencies...
    "%VENV_PY%" -m pip install -r requirements.txt
    if errorlevel 1 goto :install_failed
)

echo [start] Opening AI Data Insight Report at http://localhost:8501
set "PYTHONUTF8=1"
"%VENV_PY%" -m streamlit run app.py %*
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%

:python_missing
echo [error] Python 3.11 or newer was not found. Install Python and try again.
endlocal & exit /b 1

:venv_failed
echo [error] Failed to create the virtual environment.
endlocal & exit /b 1

:python_version
echo [error] This project requires Python 3.11 or newer.
endlocal & exit /b 1

:install_failed
echo [error] Dependency installation failed. Check the network and pip output above.
endlocal & exit /b 1
