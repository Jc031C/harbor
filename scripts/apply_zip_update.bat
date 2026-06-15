@echo off
REM 兼容旧名字：以后也可以继续使用 apply_zip_update.bat
call "%~dp0apply_update.bat" %*
exit /b %errorlevel%
