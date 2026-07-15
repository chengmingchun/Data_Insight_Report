@echo off
setlocal
cd /d "%~dp0"

set "VENV_PY=.venv\Scripts\python.exe"

if exist "%VENV_PY%" goto :check_dependencies

echo [setup] Creating Python virtual environment...
where python >nul 2>nul
if errorlevel 1 goto :use_py_launcher
python -m venv .venv
if errorlevel 1 goto :venv_failed
goto :check_dependencies

:use_py_launcher
where py >nul 2>nul
if errorlevel 1 goto :python_missing
py -3 -m venv .venv
if errorlevel 1 goto :venv_failed

:check_dependencies
"%VENV_PY%" -c "import streamlit, pandas, plotly, jinja2, pydantic, pydantic_settings, openai" >nul 2>nul
if not errorlevel 1 goto :run_app

echo [setup] Installing project dependencies...
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :install_failed

:run_app
echo [start] Opening AI Data Insight Report at http://localhost:8501
set "PYTHONUTF8=1"
set "STREAMLIT_BROWSER_GATHER_USAGE_STATS=false"
"%VENV_PY%" -m streamlit run app.py --server.headless=true --server.address=127.0.0.1 --browser.gatherUsageStats=false %*
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%

:python_missing
echo [error] Python 3.11 or newer was not found. Install Python and try again.
endlocal & exit /b 1

:venv_failed
echo [error] Failed to create the virtual environment.
endlocal & exit /b 1

:install_failed
echo [error] Dependency installation failed. Check the network and pip output above.
endlocal & exit /b 1
