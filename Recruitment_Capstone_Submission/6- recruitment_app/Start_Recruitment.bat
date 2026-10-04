@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Setting up the recruitment app environment...
    python -m venv .venv
    if errorlevel 1 goto failed
)
if not exist ".venv\recruitment_ready" (
    echo Installing application packages. This is needed on the first launch only...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto failed
    type nul > ".venv\recruitment_ready"
)
echo Opening the recruitment workspace in your browser...
echo Keep this window open while using the app. Close it to stop the app.
".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.headless false --browser.gatherUsageStats false
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo The app could not start. Keep the error above and share it for troubleshooting.
pause
exit /b 1
