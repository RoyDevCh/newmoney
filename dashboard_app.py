#!/usr/bin/env python3
"""Local operations dashboard for OpenClaw content production."""

from __future__ import annotations

import os
import secrets
import threading
import time
import uuid
from dataclasses import asdict
from functools import wraps
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

from flask import Flask, flash, jsonify, redirect, render_template, request, send_file, session, url_for

from dashboard_service import (
    OpenClawRemote,
    RemoteConfig,
    apply_publish_status,
    build_trend_rows,
    format_timestamp,
    make_backend,
    merge_queue_with_drafts,
    summarize_health,
    summarize_pipeline_report,
)
from metrics_adapter import adapt_metrics_payload


app = Flask(__name__)
app.secret_key = os.environ.get("OPENCLAW_DASHBOARD_SECRET", "openclaw-dashboard-dev")
BASE_DIR = Path(__file__).resolve().parent
METRICS_TEMPLATE_DIR = BASE_DIR / "metrics_templates"

PLATFORM_TEMPLATE_FILES = {
    "zhihu": METRICS_TEMPLATE_DIR / "zhihu_template.csv",
    "xiaohongshu": METRICS_TEMPLATE_DIR / "xiaohongshu_template.csv",
    "douyin": METRICS_TEMPLATE_DIR / "douyin_template.csv",
    "xigua": METRICS_TEMPLATE_DIR / "xigua_template.csv",
    "bilibili": METRICS_TEMPLATE_DIR / "bilibili_template.csv",
    "weibo": METRICS_TEMPLATE_DIR / "weibo_template.csv",
    "wechat": METRICS_TEMPLATE_DIR / "wechat_template.csv",
    "toutiao": METRICS_TEMPLATE_DIR / "toutiao_template.csv",
}


DEFAULT_REMOTE = RemoteConfig(
    host=os.environ.get("OPENCLAW_REMOTE_HOST", "192.168.3.120"),
    port=int(os.environ.get("OPENCLAW_REMOTE_PORT", "2222")),
    username=os.environ.get("OPENCLAW_REMOTE_USER", "Roy"),
    password=os.environ.get("OPENCLAW_REMOTE_PASSWORD", ""),
    workspace=os.environ.get("OPENCLAW_REMOTE_WORKSPACE", r"C:\Users\Roy\.openclaw\workspace"),
    content_dir=os.environ.get("OPENCLAW_REMOTE_CONTENT", r"C:\Users\Roy\.openclaw\workspace-content"),
    comfy_output=os.environ.get("OPENCLAW_REMOTE_COMFY", r"C:\Users\Roy\ComfyUI\output"),
)
DEFAULT_BACKEND = os.environ.get("OPENCLAW_BACKEND", "remote").strip().lower() or "remote"

_remote_lock = threading.Lock()
_remote_config = DEFAULT_REMOTE

_pipeline_lock = threading.Lock()
_pipeline_job: Dict[str, Any] = {
    "running": False,
    "job_id": None,
    "started_at": None,
    "finished_at": None,
    "result": None,
    "error": None,
}


def current_remote_config() -> RemoteConfig:
    with _remote_lock:
        return RemoteConfig(**asdict(_remote_config))


def set_remote_config(new_config: RemoteConfig) -> None:
    global _remote_config
    with _remote_lock:
        _remote_config = new_config


def remote_client() -> OpenClawRemote:
    return make_backend(current_remote_config(), DEFAULT_BACKEND)


def dashboard_password() -> str:
    password = os.environ.get("OPENCLAW_DASHBOARD_PASSWORD", "").strip()
    if password:
        return password
    password_file = os.environ.get("OPENCLAW_DASHBOARD_PASSWORD_FILE", "").strip()
    if password_file and Path(password_file).exists():
        return Path(password_file).read_text(encoding="utf-8").strip()
    return ""


def auth_enabled() -> bool:
    return bool(dashboard_password())


def logged_in() -> bool:
    if not auth_enabled():
        return True
    return bool(session.get("dashboard_auth"))


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if auth_enabled() and not logged_in():
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)

    return wrapper


def backend_ready() -> bool:
    if DEFAULT_BACKEND == "local":
        return True
    return current_remote_config().ready()


def run_pipeline_job(skip_assets: bool) -> None:
    global _pipeline_job
    with _pipeline_lock:
        _pipeline_job = {
            "running": True,
            "job_id": str(uuid.uuid4())[:8],
            "started_at": format_timestamp(time.time()),
            "finished_at": None,
            "result": None,
            "error": None,
            "skip_assets": skip_assets,
        }
    try:
        result = remote_client().run_safe_pipeline(skip_assets=skip_assets)
        with _pipeline_lock:
            _pipeline_job["running"] = False
            _pipeline_job["finished_at"] = format_timestamp(time.time())
            _pipeline_job["result"] = result
    except Exception as exc:
        with _pipeline_lock:
            _pipeline_job["running"] = False
            _pipeline_job["finished_at"] = format_timestamp(time.time())
            _pipeline_job["error"] = str(exc)


def pipeline_state() -> Dict[str, Any]:
    with _pipeline_lock:
        return dict(_pipeline_job)


def load_snapshot(pack_path: str | None = None) -> Dict[str, Any]:
    client = remote_client()
    snapshot = client.dashboard_snapshot(pack_path=pack_path)
    merged = snapshot.get("pack_items", [])
    if not merged and snapshot.get("queue"):
        merged = merge_queue_with_drafts(
            snapshot.get("queue", {}),
            snapshot.get("pack", {}),
            snapshot.get("quality", {}),
        )
        merged = apply_publish_status(
            merged,
            snapshot.get("publish_status", {}),
            snapshot.get("pack_path"),
        )
    snapshot["merged_queue_items"] = merged
    snapshot["pipeline_steps"] = summarize_pipeline_report(snapshot.get("report", {}))
    snapshot["health_rows"] = summarize_health(snapshot.get("health", {}))
    snapshot["trend_rows"] = build_trend_rows(snapshot.get("metrics_history", []))
    return snapshot


@app.context_processor
def inject_globals() -> Dict[str, Any]:
    cfg = current_remote_config()
    return {
        "remote_config": cfg,
        "remote_ready": backend_ready(),
        "pipeline_job": pipeline_state(),
        "platform_template_keys": list(PLATFORM_TEMPLATE_FILES.keys()),
        "auth_enabled": auth_enabled(),
        "logged_in": logged_in(),
    }


@app.before_request
def require_login():
    if not auth_enabled():
        return None
    if request.endpoint in {"login", "static"}:
        return None
    if not logged_in():
        return redirect(url_for("login", next=request.path))
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    if not auth_enabled():
        return redirect(url_for("index"))
    if request.method == "POST":
        password = request.form.get("password", "")
        if secrets.compare_digest(password, dashboard_password()):
            session["dashboard_auth"] = True
            flash("登录成功。", "success")
            return redirect(request.form.get("next") or url_for("index"))
        flash("密码不正确。", "error")
    return render_template("login.html", next_url=request.args.get("next") or request.form.get("next") or url_for("index"))


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("dashboard_auth", None)
    flash("已退出登录。", "success")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    snapshot = None
    error = None
    if backend_ready():
        try:
            snapshot = load_snapshot()
        except Exception as exc:
            error = str(exc)
    return render_template("dashboard.html", snapshot=snapshot, error=error)


@app.route("/content")
@login_required
def content_board():
    snapshot = None
    error = None
    if backend_ready():
        try:
            snapshot = load_snapshot(request.args.get("pack"))
        except Exception as exc:
            error = str(exc)
    return render_template("content_board.html", snapshot=snapshot, error=error)


@app.route("/metrics", methods=["GET", "POST"])
@login_required
def metrics_board():
    error = None
    result = None
    snapshot = None
    adapter_summary = None
    if request.method == "POST":
        upload = request.files.get("metrics_file")
        if not upload or not upload.filename:
            flash("请选择 CSV 或 JSON 数据文件。", "error")
            return redirect(url_for("metrics_board"))
        try:
            normalized_bytes, adapter_summary = adapt_metrics_payload(upload.filename, upload.read())
            normalized_name = upload.filename.rsplit(".", 1)[0] + "_normalized.csv"
            result = remote_client().ingest_metrics(normalized_name, normalized_bytes)
            result["adapter_summary"] = adapter_summary
            flash("数据已上传并完成分析，下一轮主脑会读取最新分析结果。", "success")
        except Exception as exc:
            flash(f"数据回灌失败: {exc}", "error")
    if backend_ready():
        try:
            snapshot = load_snapshot()
        except Exception as exc:
            error = str(exc)
    return render_template("metrics_board.html", snapshot=snapshot, error=error, ingest_result=result, adapter_summary=adapter_summary)


@app.route("/monitor", methods=["GET", "POST"])
@login_required
def monitor_board():
    error = None
    if request.method == "POST":
        try:
            result = remote_client().run_healthcheck()
            if result.get("ok"):
                flash("已触发 agent 健康检查。", "success")
            else:
                flash(f"健康检查执行失败: {result.get('stderr') or result.get('stdout')}", "error")
        except Exception as exc:
            flash(f"健康检查失败: {exc}", "error")
        return redirect(url_for("monitor_board"))
    snapshot = None
    if backend_ready():
        try:
            snapshot = load_snapshot()
        except Exception as exc:
            error = str(exc)
    return render_template("monitor_board.html", snapshot=snapshot, error=error)


@app.route("/templates/download/<platform_key>")
@login_required
def download_template(platform_key: str):
    path = PLATFORM_TEMPLATE_FILES.get(platform_key)
    if not path or not path.exists():
        return ("template not found", 404)
    return send_file(path, as_attachment=True, download_name=path.name)


@app.route("/content/status", methods=["POST"])
@login_required
def update_publish_status_view():
    pack_path = request.form.get("pack_path", "").strip()
    platform = request.form.get("platform", "").strip()
    if not pack_path or not platform:
        flash("缺少 pack_path 或 platform。", "error")
        return redirect(url_for("content_board"))
    update = {
        "published": request.form.get("published") == "1",
        "content_id": request.form.get("content_id", "").strip(),
        "publish_url": request.form.get("publish_url", "").strip(),
        "operator_note": request.form.get("operator_note", "").strip(),
    }
    try:
        remote_client().update_publish_status(pack_path, platform, update)
        flash(f"{platform} 发布状态已更新。", "success")
    except Exception as exc:
        flash(f"更新发布状态失败: {exc}", "error")
    return redirect(url_for("content_board"))


@app.route("/settings", methods=["POST"])
@login_required
def update_settings():
    try:
        cfg = RemoteConfig(
            host=request.form.get("host", "").strip(),
            port=int(request.form.get("port", "2222").strip()),
            username=request.form.get("username", "").strip(),
            password=request.form.get("password", "").strip(),
            workspace=request.form.get("workspace", "").strip(),
            content_dir=request.form.get("content_dir", "").strip(),
            comfy_output=request.form.get("comfy_output", "").strip(),
        )
        set_remote_config(cfg)
        flash("远端连接配置已更新。", "success")
    except Exception as exc:
        flash(f"更新配置失败: {exc}", "error")
    return redirect(request.referrer or url_for("index"))


@app.route("/pipeline/run", methods=["POST"])
@login_required
def trigger_pipeline():
    skip_assets = request.form.get("skip_assets") == "1"
    state = pipeline_state()
    if state.get("running"):
        flash("已有生产任务在运行，先等当前任务结束。", "error")
        return redirect(request.referrer or url_for("index"))
    thread = threading.Thread(target=run_pipeline_job, args=(skip_assets,), daemon=True)
    thread.start()
    flash("已启动安全生产任务。完成后刷新页面即可看到最新内容包。", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/api/status")
@login_required
def api_status():
    payload: Dict[str, Any] = {"pipeline_job": pipeline_state(), "remote_ready": backend_ready(), "backend": DEFAULT_BACKEND}
    if backend_ready():
        try:
            snapshot = load_snapshot()
            payload["queue_summary"] = snapshot.get("queue", {}).get("summary", {})
            payload["metrics_summary"] = snapshot.get("metrics", {}).get("platform_summary", {})
            payload["health_count"] = len(snapshot.get("health_rows", []))
        except Exception as exc:
            payload["error"] = str(exc)
    return jsonify(payload)


@app.route("/media")
@login_required
def media():
    path = request.args.get("path", "").strip()
    if not path:
        return ("missing path", 400)
    try:
        data, mimetype = remote_client().read_media(path)
    except Exception as exc:
        return (str(exc), 400)
    return send_file(BytesIO(data), mimetype=mimetype, download_name=os.path.basename(path))


@app.template_filter("nl2br")
def nl2br_filter(value: Any) -> str:
    return str(value or "").replace("\n", "<br>")


if __name__ == "__main__":
    bind_host = os.environ.get("OPENCLAW_DASHBOARD_BIND_HOST", "127.0.0.1")
    bind_port = int(os.environ.get("OPENCLAW_DASHBOARD_PORT", "8787"))
    app.run(host=bind_host, port=bind_port, debug=False)
