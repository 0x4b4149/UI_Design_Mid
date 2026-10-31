@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  = Skyline Weather - 啟動本機網站 =
echo.
if not exist ".venv\Scripts\python.exe" (
  echo 找不到 .venv，請先依照 README 建立虛擬環境。
  pause
  exit /b 1
)
".venv\Scripts\python.exe" manage.py runserver
pause
