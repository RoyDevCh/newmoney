Set-Location $PSScriptRoot

if (-not $env:OPENCLAW_REMOTE_HOST) { $env:OPENCLAW_REMOTE_HOST = "192.168.3.120" }
if (-not $env:OPENCLAW_REMOTE_PORT) { $env:OPENCLAW_REMOTE_PORT = "2222" }
if (-not $env:OPENCLAW_REMOTE_USER) { $env:OPENCLAW_REMOTE_USER = "Roy" }

Start-Process "http://127.0.0.1:8787"
py -3 "$PSScriptRoot\dashboard_app.py"
