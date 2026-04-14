@echo off
setlocal

cd /d "%~dp0"

echo Starting valuation dashboard server...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$listener = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue; if (-not $listener) { Start-Process python -ArgumentList 'D:\code2\valuation_dashboard_server.py' -WorkingDirectory 'D:\code2' }"

powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 3"

echo Opening dashboard in browser...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process 'http://127.0.0.1:8765/?refresh=1'"

endlocal
