@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Tapo Viewer Web
where python >nul 2>nul || (
  echo Chua cai Python. Tai tai https://www.python.org/downloads/ va tick "Add Python to PATH".
  pause & exit /b 1
)
if not exist .venv (
  echo Dang tao moi truong lan dau, vui long doi...
  python -m venv .venv
  .venv\Scripts\python -m pip install --upgrade pip
)
.venv\Scripts\python -m pip install -q -r requirements.txt
start "" http://localhost:8080
.venv\Scripts\python web.py
pause
