import json, paramiko
HOST='192.168.3.120'; PORT=2222; USER='Roy'; PASSWORD='kaiyic'
cmd = r'''$ErrorActionPreference = 'Stop'
$files = @(
  'C:\Users\Roy\.openclaw\workspace\autopipeline_brain_content_publisher.py',
  'C:\Users\Roy\.openclaw\workspace\production_strategy_config.py',
  'C:\Users\Roy\.openclaw\workspace\platform_visual_templates.py',
  'C:\Users\Roy\.openclaw\workspace\platform_monetization_mapper.py',
  'C:\Users\Roy\.openclaw\workspace\video_publish_pack_builder.py',
  'C:\Users\Roy\.openclaw\workspace\tts_render_windows.py',
  'C:\Users\Roy\.openclaw\workspace\publish_appendix_builder.py',
  'C:\Users\Roy\.openclaw\workspace\manual_publish_queue_builder.py',
  'C:\Users\Roy\.openclaw\workspace\matrix_pack_expander.py',
  'C:\Users\Roy\.openclaw\workspace-content\content_quality_gate.py'
)
foreach ($f in $files) { py -3 -m py_compile $f }
$latest = Get-ChildItem 'C:\Users\Roy\.openclaw\workspace-content' -Filter 'daily_pack_*.json' | Where-Object { $_.Name -notlike '*_raw_*' -and $_.Name -notlike '*_boosted.json' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
[pscustomobject]@{ok=$true; latest_pack=$latest.FullName} | ConvertTo-Json -Compress
'''
client = paramiko.SSHClient(); client.set_missing_host_key_policy(paramiko.AutoAddPolicy()); client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=20)
stdin, stdout, stderr = client.exec_command('powershell -NoProfile -Command "' + cmd.replace('"','`"') + '"', timeout=300)
out = stdout.read().decode('utf-8','replace'); err = stderr.read().decode('utf-8','replace'); rc = stdout.channel.recv_exit_status(); client.close()
print(json.dumps({'rc': rc, 'stdout': out, 'stderr': err}, ensure_ascii=False, indent=2))
