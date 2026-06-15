@echo off
setlocal
chcp 65001 >nul

if "%~1"=="" (
  echo 用法：scripts\apply_update_dry_run.bat 更新包.zip
  echo 这只会预览，不会修改文件。
  exit /b 2
)

python "%~dp0update_tool\apply_update.py" "%~1" --project-root "%cd%" --dry-run
exit /b %errorlevel%
