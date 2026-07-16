@echo off
setlocal
set "BRIDGE_DIR=%~dp0"

:: Prefer .venv if it exists
if exist "%BRIDGE_DIR%.venv\Scripts\python.exe" (
  " %BRIDGE_DIR%.venv\Scripts\python.exe" "%BRIDGE_DIR%server.py"
  exit /b %errorlevel%
)

:: Fall back to config.json
set "CONFIG=%BRIDGE_DIR%config.json"
if not exist "%CONFIG%" (
  echo config.json not found. Run setup.ps1 first. 1>&2
  exit /b 1
)

for /f "tokens=2 delims=:," %%a in ('findstr /i "python_env" "%CONFIG%"') do set "AGENT_PYTHON=%%~a"
set "AGENT_PYTHON=%AGENT_PYTHON: =%"
set "AGENT_PYTHON=%AGENT_PYTHON:"=%"
set "AGENT_PYTHON=%AGENT_PYTHON:\\=\%"

if not exist "%AGENT_PYTHON%" (
  echo Python not found. Run setup.ps1 first. 1>&2
  exit /b 1
)
"%AGENT_PYTHON%" "%BRIDGE_DIR%server.py"
