@echo off
setlocal
cd /d "%~dp0"

if not defined OPENCLAW_REMOTE_HOST set OPENCLAW_REMOTE_HOST=192.168.3.120
if not defined OPENCLAW_REMOTE_PORT set OPENCLAW_REMOTE_PORT=2222
if not defined OPENCLAW_REMOTE_USER set OPENCLAW_REMOTE_USER=Roy

start "" http://127.0.0.1:8787
py -3 dashboard_app.py

endlocal
