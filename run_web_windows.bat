@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Tapo Viewer Web

set "PY="
py -3 --version >nul 2>nul && set "PY=py -3"
if not defined PY (
  python --version >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo.
  echo [LOI] Chua cai Python that tren may nay.
  echo   1. Tai Python tai https://www.python.org/downloads/windows/
  echo   2. Khi cai, TICK o "Add python.exe to PATH" o man hinh dau tien.
  echo   3. Cai xong, dong cua so nay va nhap dup lai run_web_windows.bat
  echo.
  pause & exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Dang tao moi truong lan dau, vui long doi...
  if exist ".venv" rmdir /s /q ".venv"
  %PY% -m venv .venv
  if errorlevel 1 (
    echo [LOI] Khong tao duoc moi truong Python. Chup man hinh nay gui cho nguoi ho tro.
    pause & exit /b 1
  )
)

echo Dang kiem tra thu vien (lan dau mat 1-2 phut)...
".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
  echo [LOI] Cai thu vien that bai. Kiem tra ket noi Internet roi chay lai.
  pause & exit /b 1
)

start "" http://localhost:8080
echo Dang chay Tapo Viewer Web. GIU NGUYEN cua so nay. Dong cua so = dung phan mem.
".venv\Scripts\python.exe" web.py
pause
