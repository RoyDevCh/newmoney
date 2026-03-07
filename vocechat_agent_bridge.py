import json
import queue
import re
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HOST = "0.0.0.0"
PORT = 8091
BASE_URL = "http://localhost:3009"

ROOT = Path.home() / ".openclaw"
WORKSPACE_BY_AGENT = {
    "main": ROOT / "workspace",
    "main-brain": ROOT / "workspace-main-brain",
    "content": ROOT / "workspace-content",
    "multimodal": ROOT / "workspace-multimodal",
    "monitor": ROOT / "workspace-monitor",
    "publisher": ROOT / "workspace-publisher",
    "tasks": ROOT / "workspace-tasks",
}

UID_TO_AGENT = {
    8: "main",
    2: "main-brain",
    3: "content",
    4: "multimodal",
    5: "monitor",
    6: "publisher",
    7: "tasks",
}

AGENT_NAMES = set(WORKSPACE_BY_AGENT.keys())

JOBS = queue.Queue()
SEEN_MIDS = {}
SEEN_LOCK = threading.Lock()
SEEN_TTL_SECONDS = 600


def now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def log(msg: str) -> None:
    print(f"[{now_ts()}] {msg}", flush=True)


def normalize_agent_name(name: str) -> str:
    t = (name or "").strip().lower().replace("_", "-")
    aliases = {
        "mainbrain": "main-brain",
        "main-brain": "main-brain",
        "main": "main",
        "content": "content",
        "multimodal": "multimodal",
        "monitor": "monitor",
        "publisher": "publisher",
        "tasks": "tasks",
    }
    return aliases.get(t, t)


def load_agent_keys() -> dict:
    keys = {}
    for agent, ws in WORKSPACE_BY_AGENT.items():
        cfg = ws / "vocechat_config.json"
        if not cfg.exists():
            continue
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            api_key = str(data.get("api_key", "")).strip()
            if api_key:
                keys[agent] = api_key
        except Exception as exc:
            log(f"WARN failed to read {cfg}: {exc}")
    return keys


AGENT_KEYS = load_agent_keys()


def should_skip_mid(mid) -> bool:
    if mid is None:
        return False
    key = str(mid)
    now = time.time()
    with SEEN_LOCK:
        expired = [k for k, ts in SEEN_MIDS.items() if now - ts > SEEN_TTL_SECONDS]
        for k in expired:
            SEEN_MIDS.pop(k, None)
        if key in SEEN_MIDS:
            return True
        SEEN_MIDS[key] = now
    return False


def trim_text(text: str, max_chars: int = 1800) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...(truncated)"


def send_group_message(gid: int, agent: str, text: str) -> None:
    api_key = AGENT_KEYS.get(agent)
    if not api_key:
        log(f"WARN no api_key for agent={agent}, message not sent")
        return

    url = f"{BASE_URL}/api/bot/send_to_group/{gid}"
    req = Request(
        url,
        data=text.encode("utf-8"),
        headers={"x-api-key": api_key, "content-type": "text/plain"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=10) as resp:
            status = getattr(resp, "status", 200)
            log(f"send_group_message gid={gid} agent={agent} status={status}")
    except HTTPError as exc:
        log(f"ERROR send_group_message HTTP {exc.code} agent={agent}: {exc.reason}")
    except URLError as exc:
        log(f"ERROR send_group_message URL agent={agent}: {exc}")
    except Exception as exc:
        log(f"ERROR send_group_message agent={agent}: {exc}")


def extract_target_agent_and_task(payload: dict):
    detail = payload.get("detail") or {}
    if detail.get("type") not in {"normal", "reply"}:
        return None, None

    content = detail.get("content")
    if not isinstance(content, str):
        return None, None
    text = content.strip()
    if not text:
        return None, None

    target_agent = None
    props = detail.get("properties")
    if isinstance(props, dict):
        mentions = props.get("mentions")
        if isinstance(mentions, list):
            for m in mentions:
                if not isinstance(m, dict):
                    continue
                uid = m.get("uid")
                try:
                    uid_i = int(uid)
                except Exception:
                    continue
                if uid_i in UID_TO_AGENT:
                    target_agent = UID_TO_AGENT[uid_i]
                    break

    patterns = [
        r"^[＠@](?P<agent>[A-Za-z0-9_-]+)\s+(?P<body>.+)$",
        r"^to\s*[:=]\s*(?P<agent>[A-Za-z0-9_-]+)\s+(?P<body>.+)$",
        r"^/task\s+(?P<agent>[A-Za-z0-9_-]+)\s+(?P<body>.+)$",
        r"^(?P<agent>[A-Za-z0-9_-]+)\s*[：:]\s*(?P<body>.+)$",
    ]
    matched_agent = None
    matched_body = None
    for pat in patterns:
        m = re.match(pat, text, flags=re.IGNORECASE)
        if m:
            matched_agent = normalize_agent_name(m.group("agent"))
            matched_body = m.group("body").strip()
            break

    if matched_agent in AGENT_NAMES:
        target_agent = matched_agent
        text = matched_body or text

    if target_agent not in AGENT_NAMES:
        return None, None
    return target_agent, text


def run_agent_task(agent: str, message: str):
    cmd = [
        "cmd",
        "/c",
        "openclaw",
        "agent",
        "--agent",
        agent,
        "--message",
        message,
        "--timeout",
        "900",
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1200,
            check=False,
        )
    except Exception as exc:
        return False, f"router error: {exc}"

    output = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if proc.returncode != 0:
        return False, trim_text(f"exit={proc.returncode}\n{output}\n{err}")
    return True, trim_text(output or "OK")


def worker_loop() -> None:
    while True:
        job = JOBS.get()
        if not job:
            continue
        agent = job["agent"]
        gid = job["gid"]
        body = job["body"]
        sender = job.get("sender", "unknown")

        send_group_message(gid, agent, f"[router] {sender} -> {agent} 收到任务，开始执行")
        ok, result = run_agent_task(agent, body)
        if ok:
            send_group_message(gid, agent, f"[{agent}] 执行完成\n{result}")
            log(f"task done agent={agent} gid={gid}")
        else:
            send_group_message(gid, agent, f"[{agent}] 执行失败\n{result}")
            log(f"task failed agent={agent} gid={gid}: {result}")


class Handler(BaseHTTPRequestHandler):
    server_version = "VoceChatOpenClawBridge/1.0"

    def log_message(self, fmt, *args):
        log("HTTP " + (fmt % args))

    def _write(self, code: int, body: str = "ok"):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._write(200, "ok")

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            self._write(400, "invalid json")
            return

        mid = payload.get("mid")
        if should_skip_mid(mid):
            self._write(200, "duplicate")
            return

        target = payload.get("target") or {}
        gid = target.get("gid")
        if gid is None:
            self._write(200, "ignore: not group")
            return
        try:
            gid_int = int(gid)
        except Exception:
            self._write(200, "ignore: invalid gid")
            return

        agent, body = extract_target_agent_and_task(payload)
        if not agent:
            self._write(200, "ignore: no route")
            return

        from_uid = payload.get("from_uid")
        sender = (
            UID_TO_AGENT.get(int(from_uid), f"uid:{from_uid}")
            if str(from_uid).isdigit()
            else str(from_uid)
        )
        JOBS.put({"agent": agent, "gid": gid_int, "body": body, "sender": sender})
        log(f"queued mid={mid} sender={sender} -> {agent} body={trim_text(body, 120)}")
        self._write(200, "queued")


def main() -> None:
    if not AGENT_KEYS:
        log("WARN no agent keys loaded from vocechat_config.json files")
    else:
        log(f"loaded keys: {', '.join(sorted(AGENT_KEYS.keys()))}")
    threading.Thread(target=worker_loop, daemon=True).start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    log(f"bridge listening on http://{HOST}:{PORT}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
