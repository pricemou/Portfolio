@echo off
set ROOT=%~dp0..
set PY=%ROOT%\venv\Scripts\python.exe
set PORT=5002

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5001 " ^| findstr LISTENING') do taskkill /F /T /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5002 " ^| findstr LISTENING') do taskkill /F /T /PID %%a >nul 2>&1
ping -n 2 127.0.0.1 >nul

cd /d "%ROOT%"
"%PY%" app.py
