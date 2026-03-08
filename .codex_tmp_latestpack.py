import paramiko
HOST='192.168.3.120'; PORT=2222; USER='Roy'; PASSWORD='kaiyic'
cmd = r"$latest = Get-ChildItem 'C:\Users\Roy\.openclaw\workspace-content' -Filter 'daily_pack_*.json' | Where-Object { $_.Name -notlike '*_raw_*' -and $_.Name -notlike '*_boosted.json' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1; if ($latest) { $latest.FullName }"
client = paramiko.SSHClient(); client.set_missing_host_key_policy(paramiko.AutoAddPolicy()); client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=20)
stdin, stdout, stderr = client.exec_command('powershell -NoProfile -Command "' + cmd.replace('"','`"') + '"', timeout=120)
out = stdout.read().decode('utf-8','replace'); err = stderr.read().decode('utf-8','replace'); rc = stdout.channel.recv_exit_status(); client.close()
print('RC=', rc)
print('OUT=', out)
print('ERR=', err)
