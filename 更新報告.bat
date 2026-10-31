@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  = 重新產生期中報告 PDF / PPTX =
echo  請先編輯 docs\report\report_meta.json（組別、組員、連結）
echo.
if not exist ".venv\Scripts\python.exe" (
  echo 找不到 .venv，請先依照 README 建立虛擬環境。
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\build_report.py
if errorlevel 1 (
  echo 報告產生失敗，請確認 Chrome 已安裝。
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\build_pptx.py
echo.
echo 完成：docs\report\Skyline_Weather_期中專題報告.pdf / .pptx
pause
