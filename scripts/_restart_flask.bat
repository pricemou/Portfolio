@echo off
cd /d "%~dp0.."
python -c "import database; print('database ok')"
if errorlevel 1 exit /b 1

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000 .*LISTENING"') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5001 .*LISTENING"') do taskkill /F /PID %%a >nul 2>&1

if exist "venv\Scripts\python.exe" (
  start "Flask Portfolio" /MIN cmd /c "cd /d "%~dp0.." && venv\Scripts\python.exe app.py"
) else (
  start "Flask Portfolio" /MIN cmd /c "cd /d "%~dp0.." && python app.py"
)
timeout /t 2 /nobreak >nul
echo Flask restarted
