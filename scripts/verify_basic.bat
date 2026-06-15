@echo off
setlocal
chcp 65001 >nul
python "%~dp0update_tool\verify_basic.py" --project-root "%cd%"
exit /b %errorlevel%
