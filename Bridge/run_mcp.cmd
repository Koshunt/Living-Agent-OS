@echo off
setlocal
set "BRIDGE_DIR=%~dp0"
set "CONFIG=%BRIDGE_DIR%config.json"

if not exist "%CONFIG%" (
  echo config.json not found: %CONFIG% 1>&2
  exit /b 1
)

for /f "tokens=2 delims=:," %%a in ('findstr /i "python_env" "%CONFIG%"') do set "AGENT_PYTHON=%%~a"
set "AGENT_PYTHON=%AGENT_PYTHON: =%"
set "AGENT_PYTHON=%AGENT_PYTHON:"=%"
set "AGENT_PYTHON=%AGENT_PYTHON:\\=\%"

if not exist "%AGENT_PYTHON%" (
  echo Python was not found: %AGENT_PYTHON% 1>&2
  echo Run setup.ps1 first to set up the environment. 1>&2
  exit /b 1
)
"%AGENT_PYTHON%" "%BRIDGE_DIR%server.py"
