#!/usr/bin/env python3
"""Deploy the dashboard to the remote Windows OpenClaw host and configure autostart."""

from __future__ import annotations

import os
import secrets
from datetime import datetime
from pathlib import Path

import paramiko


HOST = "192.168.3.120"
PORT = 2222
USERNAME = "Roy"
PASSWORD = "kaiyic"

LOCAL_ROOT = Path(__file__).resolve().parent
REMOTE_ROOT = Path(r"C:\Users\Roy\.openclaw\workspace")
REMOTE_PYTHON = r"C:\Users\Roy\AppData\Local\Programs\Python\Python312\python.exe"

FILES = [
    "dashboard_app.py",
    "dashboard_service.py",
    "metrics_adapter.py",
    "start_dashboard.cmd",
    "start_dashboard.ps1",
]

DIRS = {
    "templates": ["base.html", "dashboard.html", "content_board.html", "metrics_board.html", "monitor_board.html", "login.html"],
    "static": ["dashboard.css"],
    "metrics_templates": [
        "zhihu_template.csv",
        "xiaohongshu_template.csv",
        "douyin_template.csv",
        "xigua_template.csv",
        "bilibili_template.csv",
        "weibo_template.csv",
        "wechat_template.csv",
        "toutiao_template.csv",
    ],
}


REMOTE_STARTUP_PS1 = REMOTE_ROOT / "start_dashboard_server.ps1"
REMOTE_PIPELINE_PS1 = REMOTE_ROOT / "run_daily_pipeline.ps1"
REMOTE_INSTALL_PS1 = REMOTE_ROOT / "install_dashboard_autostart.ps1"
REMOTE_ENV_PS1 = REMOTE_ROOT / "dashboard_runtime_env.ps1"
REMOTE_PASSWORD_FILE = REMOTE_ROOT / "reports" / "dashboard_password.txt"
LOCAL_ACCESS_NOTE = LOCAL_ROOT / "reports" / "dashboard_access_latest.txt"


def upload_file(sftp: paramiko.SFTPClient, local: Path, remote: Path) -> None:
    remote_parent = str(remote.parent)
    ensure_dir(sftp, remote_parent)
    remote_str = str(remote)
    backup = remote_str + ".bak_codex"
    try:
        sftp.remove(backup)
    except IOError:
        pass
    try:
        sftp.rename(remote_str, backup)
    except IOError:
        pass
    sftp.put(str(local), remote_str)


def ensure_dir(sftp: paramiko.SFTPClient, path: str) -> None:
    parts = []
    current = path
    while current and current not in ("\\", "/"):
        parts.append(current)
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    for directory in reversed(parts):
        try:
            sftp.stat(directory)
        except IOError:
            sftp.mkdir(directory)


def main() -> None:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=20)
    sftp = client.open_sftp()
    try:
        for name in FILES:
            upload_file(sftp, LOCAL_ROOT / name, REMOTE_ROOT / name)
        for folder, names in DIRS.items():
            for name in names:
                upload_file(sftp, LOCAL_ROOT / folder / name, REMOTE_ROOT / folder / name)

        dashboard_password = None
        try:
            with sftp.open(str(REMOTE_PASSWORD_FILE), "r") as f:
                dashboard_password = f.read()
                if isinstance(dashboard_password, bytes):
                    dashboard_password = dashboard_password.decode("utf-8", errors="replace")
                dashboard_password = dashboard_password.strip()
        except IOError:
            dashboard_password = None
        if not dashboard_password:
            dashboard_password = secrets.token_urlsafe(12)
            ensure_dir(sftp, str(REMOTE_PASSWORD_FILE.parent))
            with sftp.open(str(REMOTE_PASSWORD_FILE), "w") as f:
                f.write(dashboard_password)

        dashboard_secret = secrets.token_urlsafe(24)
        env_ps1 = rf"""
$env:OPENCLAW_BACKEND = "local"
$env:OPENCLAW_REMOTE_WORKSPACE = "C:\Users\Roy\.openclaw\workspace"
$env:OPENCLAW_REMOTE_CONTENT = "C:\Users\Roy\.openclaw\workspace-content"
$env:OPENCLAW_REMOTE_COMFY = "C:\Users\Roy\ComfyUI\output"
$env:OPENCLAW_DASHBOARD_BIND_HOST = "0.0.0.0"
$env:OPENCLAW_DASHBOARD_PORT = "8787"
$env:OPENCLAW_DASHBOARD_PASSWORD_FILE = "C:\Users\Roy\.openclaw\workspace\reports\dashboard_password.txt"
$env:OPENCLAW_DASHBOARD_SECRET = "{dashboard_secret}"
$env:USERPROFILE = "C:\Users\Roy"
$env:HOME = "C:\Users\Roy"
$env:APPDATA = "C:\Users\Roy\AppData\Roaming"
$env:LOCALAPPDATA = "C:\Users\Roy\AppData\Local"
"""

        startup_ps1 = rf"""
. "{REMOTE_ENV_PS1}"
Set-Location "C:\Users\Roy\.openclaw\workspace"
& "{REMOTE_PYTHON}" -m waitress --host=0.0.0.0 --port=8787 dashboard_app:app *>> "C:\Users\Roy\.openclaw\workspace\reports\dashboard_server.log"
"""
        pipeline_ps1 = rf"""
. "{REMOTE_ENV_PS1}"
Set-Location "C:\Users\Roy\.openclaw\workspace"
& "{REMOTE_PYTHON}" "C:\Users\Roy\.openclaw\workspace\autopipeline_brain_content_publisher.py" --skip-publisher *>> "C:\Users\Roy\.openclaw\workspace\reports\daily_pipeline.log"
"""
        install_ps1 = rf"""
$dashboardTask = "OpenClawDashboardServer"
$pipelineTask = "OpenClawDailyPipeline"
$dashboardScript = "C:\Users\Roy\.openclaw\workspace\start_dashboard_server.ps1"
$pipelineScript = "C:\Users\Roy\.openclaw\workspace\run_daily_pipeline.ps1"

if (-not (Get-NetFirewallRule -DisplayName "OpenClaw Dashboard 8787" -ErrorAction SilentlyContinue)) {{
  New-NetFirewallRule -DisplayName "OpenClaw Dashboard 8787" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8787 -Profile Private | Out-Null
}}

try {{
  Unregister-ScheduledTask -TaskName $dashboardTask -Confirm:$false -ErrorAction SilentlyContinue
}} catch {{}}
try {{
  Unregister-ScheduledTask -TaskName $pipelineTask -Confirm:$false -ErrorAction SilentlyContinue
}} catch {{}}

$dashboardAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$dashboardScript`""
$dashboardTrigger = New-ScheduledTaskTrigger -AtStartup
$dashboardSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName $dashboardTask -Action $dashboardAction -Trigger $dashboardTrigger -Settings $dashboardSettings -User "SYSTEM" -RunLevel Highest -Force | Out-Null

$pipelineAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$pipelineScript`""
$pipelineTrigger = New-ScheduledTaskTrigger -Daily -At 08:30
$pipelineSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName $pipelineTask -Action $pipelineAction -Trigger $pipelineTrigger -Settings $pipelineSettings -User "SYSTEM" -RunLevel Highest -Force | Out-Null

Start-ScheduledTask -TaskName $dashboardTask
"""
        for remote_path, content in [
            (str(REMOTE_ENV_PS1), env_ps1),
            (str(REMOTE_STARTUP_PS1), startup_ps1),
            (str(REMOTE_PIPELINE_PS1), pipeline_ps1),
            (str(REMOTE_INSTALL_PS1), install_ps1),
        ]:
            with sftp.open(remote_path, "w") as f:
                f.write(content)
    finally:
        sftp.close()

    pip_cmd = f'"{REMOTE_PYTHON}" -m pip install flask paramiko waitress'
    stdin, stdout, stderr = client.exec_command(pip_cmd, timeout=1800)
    stdout.read()
    stderr.read()
    stdout.channel.recv_exit_status()

    cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File "{REMOTE_INSTALL_PS1}"'
    stdin, stdout, stderr = client.exec_command(cmd, timeout=300)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    rc = stdout.channel.recv_exit_status()
    client.close()
    if rc != 0:
        raise SystemExit(f"install failed\nSTDOUT:\n{out}\nSTDERR:\n{err}")
    LOCAL_ACCESS_NOTE.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_ACCESS_NOTE.write_text(
        "\n".join(
            [
                f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Dashboard URL: http://{HOST}:8787",
                f"Dashboard Password: {dashboard_password}",
                "Auth: password-only login",
                "Tasks: OpenClawDashboardServer, OpenClawDailyPipeline",
            ]
        ),
        encoding="utf-8",
    )
    print(f"deployment ok\nDashboard URL: http://{HOST}:8787\nDashboard Password: {dashboard_password}")


if __name__ == "__main__":
    main()
