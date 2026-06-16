@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0.."

set "PYTHON_EXE="

if exist ".\.venv\Scripts\python.exe" (
  set "PYTHON_EXE=.\.venv\Scripts\python.exe"
  goto run_bridge
)

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_EXE=py"
  goto run_bridge
)

for /f "delims=" %%P in ('where python 2^>nul') do (
  echo %%P | findstr /I /C:"WindowsApps\python.exe" >nul
  if errorlevel 1 (
    set "PYTHON_EXE=%%P"
    goto run_bridge
  )
)

echo ERROR: No usable Python found.
echo Checked .venv, py launcher, and python paths excluding WindowsApps\python.exe.
pause
exit /b 1

:run_bridge
echo Project root: %cd%
echo Python: %PYTHON_EXE%
"%PYTHON_EXE%" -m harbor.bridges.wechat_bridge
if errorlevel 1 (
  echo.
  echo WeChat Bridge exited with an error.
  pause
  exit /b %errorlevel%
)

endlocal
