from pathlib import Path
import os
import paramiko

HOST='192.168.3.120'
PORT=2222
USERNAME='Roy'
PASSWORD='kaiyic'
LOCAL_ROOT=Path(r'C:\Users\Roy\Documents\New project')
REMOTE_WS=Path(r'C:\Users\Roy\.openclaw\workspace')
REMOTE_WSC=Path(r'C:\Users\Roy\.openclaw\workspace-content')

UPLOADS = [
    ('autopipeline_brain_content_publisher.py', REMOTE_WS),
    ('production_strategy_config.py', REMOTE_WS),
    ('platform_visual_templates.py', REMOTE_WS),
    ('platform_monetization_mapper.py', REMOTE_WS),
    ('video_publish_pack_builder.py', REMOTE_WS),
    ('tts_render_windows.py', REMOTE_WS),
    ('publish_appendix_builder.py', REMOTE_WS),
    ('manual_publish_queue_builder.py', REMOTE_WS),
    ('matrix_pack_expander.py', REMOTE_WS),
    ('content_quality_gate.py', REMOTE_WSC),
]

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=20)
sftp = client.open_sftp()

def ensure_dir(path: str):
    parts = []
    current = path
    while current and current not in ('\\', '/'):
        parts.append(current)
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    for d in reversed(parts):
        try:
            sftp.stat(d)
        except IOError:
            sftp.mkdir(d)

for name, remote_dir in UPLOADS:
    local = LOCAL_ROOT / name
    remote = str(remote_dir / name)
    ensure_dir(os.path.dirname(remote))
    bak = remote + '.bak_codex'
    try:
        sftp.remove(bak)
    except IOError:
        pass
    try:
        sftp.rename(remote, bak)
    except IOError:
        pass
    sftp.put(str(local), remote)
    print('uploaded', name)

sftp.close()
client.close()
