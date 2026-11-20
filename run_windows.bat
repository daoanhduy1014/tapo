@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul || (
  echo Chua cai Python. Tai tai https://www.python.org/downloads/ va tick "Add Python to PATH".
  pause & exit /b 1
)
if not exist .venv (
  echo Dang tao moi truong lan dau, vui long doi...
  python -m venv .venv
  .venv\Scripts\python -m pip install --upgrade pip
  .venv\Scripts\python -m pip install -r requirements.txt
)
start "" .venv\Scripts\pythonw main.py
