@echo off
echo ================================================================================
echo          Intel Hackathon 2026 - OpsAssistant Pro (Phi-4 Mini)
echo ================================================================================
echo.
echo Please wait while the server starts...
echo (This window must stay open while using the tool)
echo.
echo When you see "Application startup complete", open your browser and go to:
echo    file:///c:/Users/srakella/ops-assistant/index.html
echo.
echo ================================================================================
echo.

cd /d c:\Users\srakella\ops-assistant
c:\Users\srakella\ops-assistant\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000

echo.
echo Server stopped. You can close this window.
pause
