@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  = Skyline Weather - Build Report PDF / PPTX =
echo.
if not exist ".venv\Scripts\python.exe" (
  echo Could not find .venv. Please follow README to create virtualenv first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\build_report.py
if errorlevel 1 (
  echo Report generation failed.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\build_pptx.py
echo.
echo Output files saved in docs\report\
pause

