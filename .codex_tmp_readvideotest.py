import json, paramiko
HOST='192.168.3.120'; PORT=2222; USER='Roy'; PASSWORD='kaiyic'
out_pack = r'C:\Users\Roy\.openclaw\workspace-content\daily_pack_20260308_224019_xigua_test.json'
tts_dir = r'C:\Users\Roy\.openclaw\workspace-content\tts_20260308_224019_xigua_test'
client = paramiko.SSHClient(); client.set_missing_host_key_policy(paramiko.AutoAddPolicy()); client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=20)
sftp = client.open_sftp()
with sftp.open(out_pack, 'r') as f:
    pack = json.loads(f.read().decode('utf-8-sig'))
files = []
for attr in sftp.listdir_attr(tts_dir):
    if attr.filename.lower().endswith('.wav'):
        files.append({'name': attr.filename, 'size_mb': round(attr.st_size / (1024*1024), 2)})
files.sort(key=lambda x: x['name'])
print(json.dumps({
    'drafts': [d.get('platform') for d in pack.get('drafts', [])],
    'video_kits': list((pack.get('video_publish_kits') or {}).keys()),
    'xigua_kit_exists': 'xigua' in (pack.get('video_publish_kits') or {}),
    'tts_files': files,
}, ensure_ascii=False, indent=2))
sftp.close(); client.close()
