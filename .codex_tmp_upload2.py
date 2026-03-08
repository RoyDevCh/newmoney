from pathlib import Path
import os
import paramiko
HOST='192.168.3.120'; PORT=2222; USERNAME='Roy'; PASSWORD='kaiyic'
LOCAL_ROOT=Path(r'C:\Users\Roy\Documents\New project')
UPLOADS = [
    (LOCAL_ROOT / 'autopipeline_brain_content_publisher.py', r'C:\Users\Roy\.openclaw\workspace\autopipeline_brain_content_publisher.py'),
    (LOCAL_ROOT / 'content_autotune_runner.py', r'C:\Users\Roy\.openclaw\workspace-content\content_autotune_runner.py'),
]
client = paramiko.SSHClient(); client.set_missing_host_key_policy(paramiko.AutoAddPolicy()); client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=20)
sftp = client.open_sftp()
def ensure_dir(path:str):
    parts=[]; current=path
    while current and current not in ('\\','/'):
        parts.append(current); parent=os.path.dirname(current)
        if parent==current: break
        current=parent
    for d in reversed(parts):
        try: sftp.stat(d)
        except IOError: sftp.mkdir(d)
for local, remote in UPLOADS:
    ensure_dir(os.path.dirname(remote))
    bak = remote + '.bak_codex'
    try: sftp.remove(bak)
    except IOError: pass
    try: sftp.rename(remote, bak)
    except IOError: pass
    sftp.put(str(local), remote)
    print('uploaded', remote)
sftp.close(); client.close()
