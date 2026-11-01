@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  = Skyline Weather - Start Local Server =
echo.
if not exist ".venv\Scripts\python.exe" (
  echo Could not find .venv. Please follow README to create virtualenv first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" manage.py runserver
pause

