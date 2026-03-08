import json, paramiko
HOST='192.168.3.120'; PORT=2222; USER='Roy'; PASSWORD='kaiyic'
latest = r'C:\Users\Roy\.openclaw\workspace-content\daily_pack_20260308_224019.json'
out_pack = r'C:\Users\Roy\.openclaw\workspace-content\daily_pack_20260308_224019_xigua_test.json'
tts_dir = r'C:\Users\Roy\.openclaw\workspace-content\tts_20260308_224019_xigua_test'
cmd = rf"""
$ErrorActionPreference = 'Stop'
py -3 C:\Users\Roy\.openclaw\workspace\matrix_pack_expander.py --input '{latest}' --output '{out_pack}' --min-score 85 | Out-Null
py -3 C:\Users\Roy\.openclaw\workspace\tts_render_windows.py --input '{out_pack}' --output-dir '{tts_dir}' | Out-Null
$pack = Get-Content '{out_pack}' -Raw | ConvertFrom-Json
$result = [ordered]@{{
  drafts = @($pack.drafts | ForEach-Object {{ $_.platform }})
  video_kits = @($pack.video_publish_kits.PSObject.Properties.Name)
  has_xigua = [bool]($pack.drafts | Where-Object {{ $_.platform -eq '西瓜视频' }})
  tts_files = @((Get-ChildItem '{tts_dir}' -Filter '*.wav' -ErrorAction SilentlyContinue) | ForEach-Object {{ [ordered]@{{ name=$_.Name; size_mb=[math]::Round($_.Length / 1MB, 2) }} }})
}}
$result | ConvertTo-Json -Depth 6
"""
client = paramiko.SSHClient(); client.set_missing_host_key_policy(paramiko.AutoAddPolicy()); client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=20)
stdin, stdout, stderr = client.exec_command('powershell -NoProfile -Command "' + cmd.replace('"','`"') + '"', timeout=1800)
out = stdout.read().decode('utf-8','replace'); err = stderr.read().decode('utf-8','replace'); rc = stdout.channel.recv_exit_status(); client.close()
print(json.dumps({'rc': rc, 'stdout': out, 'stderr': err}, ensure_ascii=False, indent=2))
