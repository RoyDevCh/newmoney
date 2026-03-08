from pathlib import Path
import os
import paramiko
HOST='192.168.3.120'; PORT=2222; USERNAME='Roy'; PASSWORD='kaiyic'
local = Path(r'C:\Users\Roy\Documents\New project\autopipeline_brain_content_publisher.py')
remote = r'C:\Users\Roy\.openclaw\workspace\autopipeline_brain_content_publisher.py'
client = paramiko.SSHClient(); client.set_missing_host_key_policy(paramiko.AutoAddPolicy()); client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=20)
sftp = client.open_sftp()
try:
    bak = remote + '.bak_codex'
    try: sftp.remove(bak)
    except IOError: pass
    try: sftp.rename(remote, bak)
    except IOError: pass
    sftp.put(str(local), remote)
finally:
    sftp.close(); client.close()
print('uploaded')
