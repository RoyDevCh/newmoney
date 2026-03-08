#!/usr/bin/env python3
"""Remote access helpers for the OpenClaw operations dashboard."""

from __future__ import annotations

import base64
import json
import mimetypes
import ntpath
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from stat import S_ISDIR
from typing import Any, Dict, Iterable, List, Tuple

import paramiko

from production_strategy_config import build_strategy_matrix


@dataclass
class RemoteConfig:
    host: str
    port: int
    username: str
    password: str
    workspace: str = r"C:\Users\Roy\.openclaw\workspace"
    content_dir: str = r"C:\Users\Roy\.openclaw\workspace-content"
    comfy_output: str = r"C:\Users\Roy\ComfyUI\output"

    def ready(self) -> bool:
        return bool(self.host and self.username and self.password)


class OpenClawRemote:
    def __init__(self, config: RemoteConfig) -> None:
        self.config = config

    def _connect(self) -> paramiko.SSHClient:
        if not self.config.ready():
            raise RuntimeError("remote config incomplete")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=self.config.host,
            port=self.config.port,
            username=self.config.username,
            password=self.config.password,
            timeout=20,
            banner_timeout=20,
            auth_timeout=20,
        )
        return client

    def _read_bytes(self, path: str) -> bytes:
        client = self._connect()
        try:
            sftp = client.open_sftp()
            try:
                with sftp.open(path, "rb") as f:
                    return f.read()
            finally:
                sftp.close()
        finally:
            client.close()

    def read_text(self, path: str, encoding: str = "utf-8-sig") -> str:
        return self._read_bytes(path).decode(encoding, errors="replace")

    def read_json(self, path: str) -> Dict[str, Any]:
        return json.loads(self.read_text(path))

    def write_bytes(self, path: str, data: bytes) -> None:
        client = self._connect()
        try:
            sftp = client.open_sftp()
            try:
                self._ensure_dir(sftp, ntpath.dirname(path))
                with sftp.open(path, "wb") as f:
                    f.write(data)
            finally:
                sftp.close()
        finally:
            client.close()

    def list_files(self, directory: str, startswith: str = "", endswith: str = "") -> List[Dict[str, Any]]:
        client = self._connect()
        try:
            sftp = client.open_sftp()
            try:
                rows: List[Dict[str, Any]] = []
                for attr in sftp.listdir_attr(directory):
                    if not S_ISDIR(attr.st_mode):
                        name = attr.filename
                        if startswith and not name.startswith(startswith):
                            continue
                        if endswith and not name.endswith(endswith):
                            continue
                        rows.append(
                            {
                                "name": name,
                                "path": ntpath.join(directory, name),
                                "mtime": attr.st_mtime,
                                "size": attr.st_size,
                            }
                        )
                rows.sort(key=lambda x: x["mtime"], reverse=True)
                return rows
            finally:
                sftp.close()
        finally:
            client.close()

    def latest_file(self, directory: str, startswith: str = "", endswith: str = "") -> str | None:
        rows = self.list_files(directory, startswith=startswith, endswith=endswith)
        return rows[0]["path"] if rows else None

    def run_powershell(self, script: str, timeout: int = 300) -> Dict[str, Any]:
        encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
        client = self._connect()
        try:
            cmd = f"powershell -NoProfile -EncodedCommand {encoded}"
            stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            rc = stdout.channel.recv_exit_status()
            return {"ok": rc == 0, "rc": rc, "stdout": out.strip(), "stderr": err.strip()}
        finally:
            client.close()

    def run_python(self, script_path: str, args: Iterable[str], timeout: int = 300) -> Dict[str, Any]:
        parts = ["py", "-3", self._ps_quote(script_path)]
        parts.extend(self._ps_quote(arg) for arg in args)
        ps = "& " + " ".join(parts)
        return self.run_powershell(ps, timeout=timeout)

    def run_healthcheck(self) -> Dict[str, Any]:
        script = ntpath.join(self.config.workspace, "full_agent_healthcheck.py")
        return self.run_python(script, [], timeout=600)

    def run_safe_pipeline(self, skip_assets: bool = False) -> Dict[str, Any]:
        script = ntpath.join(self.config.workspace, "autopipeline_brain_content_publisher.py")
        args = ["--skip-publisher"]
        if skip_assets:
            args.append("--skip-assets")
        return self.run_python(script, args, timeout=2400)

    def ingest_metrics(self, filename: str, payload: bytes) -> Dict[str, Any]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        remote_input = ntpath.join(self.config.content_dir, "metrics_uploads", f"{timestamp}_{ntpath.basename(filename)}")
        out_json = ntpath.join(self.config.content_dir, f"metrics_analysis_{timestamp}.json")
        out_md = ntpath.join(self.config.content_dir, f"metrics_analysis_{timestamp}.md")
        latest_json = ntpath.join(self.config.content_dir, "metrics_analysis_latest.json")
        latest_md = ntpath.join(self.config.content_dir, "metrics_analysis_latest.md")
        self.write_bytes(remote_input, payload)
        script = ntpath.join(self.config.workspace, "daily_metrics_ingest.py")
        result = self.run_python(
            script,
            [
                "--input",
                remote_input,
                "--output-json",
                out_json,
                "--output-md",
                out_md,
                "--latest-json",
                latest_json,
                "--latest-md",
                latest_md,
            ],
            timeout=300,
        )
        result["paths"] = {
            "input": remote_input,
            "output_json": out_json,
            "output_md": out_md,
            "latest_json": latest_json,
            "latest_md": latest_md,
        }
        return result

    def read_publish_status(self) -> Dict[str, Any]:
        path = ntpath.join(self.config.content_dir, "publish_status_latest.json")
        if not self.exists(path):
            return {"updated_at": "", "items": {}}
        return self.read_json(path)

    def update_publish_status(self, pack_path: str, platform: str, update: Dict[str, Any]) -> Dict[str, Any]:
        path = ntpath.join(self.config.content_dir, "publish_status_latest.json")
        data = self.read_publish_status()
        items = data.setdefault("items", {})
        key = f"{pack_path}::{platform}"
        current = items.get(key, {})
        current.update(update)
        current["pack_path"] = pack_path
        current["platform"] = platform
        current["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        items[key] = current
        data["updated_at"] = current["updated_at"]
        self.write_bytes(path, json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
        return current

    def metrics_history(self, limit: int = 14) -> List[Dict[str, Any]]:
        rows = []
        for file in self.list_files(self.config.content_dir, "metrics_analysis_", ".json"):
            if ntpath.basename(file["path"]) == "metrics_analysis_latest.json":
                continue
            try:
                payload = self.read_json(file["path"])
            except Exception:
                continue
            rows.append(
                {
                    "path": file["path"],
                    "mtime": file["mtime"],
                    "timestamp": format_timestamp(file["mtime"]),
                    "platform_summary": payload.get("platform_summary", {}),
                }
            )
            if len(rows) >= limit:
                break
        return list(reversed(rows))

    def content_packs(self, limit: int = 20) -> List[Dict[str, Any]]:
        rows = []
        for file in self.list_files(self.config.content_dir, "daily_pack_", ".json"):
            name = file["name"]
            if "_raw_" in name or name.endswith("_boosted.json"):
                continue
            rows.append(file)
            if len(rows) >= limit:
                break
        return rows

    def dashboard_snapshot(self, pack_path: str | None = None) -> Dict[str, Any]:
        latest_report = self.latest_file(ntpath.join(self.config.workspace, "reports"), "pipeline_autorun_", ".json")
        latest_health = self.latest_file(ntpath.join(self.config.workspace, "reports"), "agent_health_full_", ".json")
        latest_queue = ntpath.join(self.config.content_dir, "manual_publish_queue_latest.json")
        latest_metrics = ntpath.join(self.config.content_dir, "metrics_analysis_latest.json")

        report = self.read_json(latest_report) if latest_report else {}
        queue = self.read_json(latest_queue) if self.exists(latest_queue) else {}
        metrics = self.read_json(latest_metrics) if self.exists(latest_metrics) else {}
        selected_pack_path = pack_path or queue.get("source_pack") or self.latest_content_pack()
        pack_history = self.content_packs()
        pack = self.read_json(selected_pack_path) if selected_pack_path and self.exists(selected_pack_path) else {}
        health = self.read_json(latest_health) if latest_health else {}
        quality_path = self._quality_path_from_pack(selected_pack_path)
        quality = self.read_json(quality_path) if quality_path and self.exists(quality_path) else {}
        asset_path = asset_manifest_path(self.config.content_dir, selected_pack_path)
        asset_manifest = self.read_json(asset_path) if asset_path and self.exists(asset_path) else {}
        tts_dir = tts_dir_path(self.config.content_dir, selected_pack_path)
        tts_files = self.list_files(tts_dir, endswith=".wav") if tts_dir and self.exists(tts_dir) else []
        publish_status = self.read_publish_status()
        metrics_history = self.metrics_history()
        pack_items = apply_publish_status(build_pack_items(pack, quality, asset_manifest, tts_files), publish_status, selected_pack_path)

        return {
            "report_path": latest_report,
            "health_path": latest_health,
            "queue_path": latest_queue if queue else None,
            "metrics_path": latest_metrics if metrics else None,
            "pack_path": selected_pack_path,
            "quality_path": quality_path,
            "asset_manifest_path": asset_path,
            "tts_dir": tts_dir,
            "report": report,
            "queue": queue,
            "metrics": metrics,
            "pack": pack,
            "quality": quality,
            "asset_manifest": asset_manifest,
            "tts_files": tts_files,
            "health": health,
            "publish_status": publish_status,
            "metrics_history": metrics_history,
            "pack_history": pack_history,
            "pack_items": pack_items,
        }

    def latest_content_pack(self) -> str | None:
        files = self.list_files(self.config.content_dir, "daily_pack_", ".json")
        for row in files:
            name = row["name"]
            if "_raw_" in name or name.endswith("_boosted.json"):
                continue
            return row["path"]
        return None

    def exists(self, path: str) -> bool:
        client = self._connect()
        try:
            sftp = client.open_sftp()
            try:
                sftp.stat(path)
                return True
            except IOError:
                return False
            finally:
                sftp.close()
        finally:
            client.close()

    def read_media(self, path: str) -> Tuple[bytes, str]:
        self._assert_allowed(path)
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        return self._read_bytes(path), mime

    def _quality_path_from_pack(self, pack_path: str | None) -> str | None:
        if not pack_path:
            return None
        name = ntpath.basename(pack_path)
        if not name.startswith("daily_pack_") or not name.endswith(".json"):
            return None
        stamp = name[len("daily_pack_") : -len(".json")]
        return ntpath.join(self.config.content_dir, f"quality_{stamp}_recheck.json")

    def _assert_allowed(self, path: str) -> None:
        allowed_roots = [
            self.config.content_dir.lower(),
            self.config.workspace.lower(),
            self.config.comfy_output.lower(),
        ]
        normalized = path.lower()
        if not any(normalized.startswith(root) for root in allowed_roots):
            raise ValueError("remote path not allowed")

    def _ensure_dir(self, sftp: paramiko.SFTPClient, path: str) -> None:
        parts = []
        current = path
        while current and current not in (ntpath.sep, "\\"):
            parts.append(current)
            parent = ntpath.dirname(current)
            if parent == current:
                break
            current = parent
        for directory in reversed(parts):
            try:
                sftp.stat(directory)
            except IOError:
                sftp.mkdir(directory)

    @staticmethod
    def _ps_quote(value: str) -> str:
        return "'" + str(value).replace("'", "''") + "'"


def format_timestamp(epoch: int | float | None) -> str:
    if not epoch:
        return ""
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")


def pack_stamp(pack_path: str | None) -> str:
    if not pack_path:
        return ""
    name = ntpath.basename(pack_path)
    if not name.startswith("daily_pack_") or not name.endswith(".json"):
        return ""
    return name[len("daily_pack_") : -len(".json")]


def asset_manifest_path(content_dir: str, pack_path: str | None) -> str | None:
    stamp = pack_stamp(pack_path)
    if not stamp:
        return None
    return ntpath.join(content_dir, f"asset_manifest_daily_{stamp}.json")


def tts_dir_path(content_dir: str, pack_path: str | None) -> str | None:
    stamp = pack_stamp(pack_path)
    if not stamp:
        return None
    return ntpath.join(content_dir, f"tts_{stamp}")


def map_assets(manifest: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    rows = manifest.get("results", []) if isinstance(manifest, dict) else []
    mapped: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict):
            platform = str(row.get("platform", "")).strip()
            if platform:
                mapped[platform] = row
    return mapped


def map_tts_files(tts_files: List[Dict[str, Any]]) -> Dict[str, str]:
    mapped: Dict[str, str] = {}
    for row in tts_files:
        path = str(row.get("path", "")).strip()
        name = ntpath.basename(path).lower()
        if "douyin" in name:
            mapped["抖音"] = path
        elif "xigua" in name:
            mapped["西瓜视频"] = path
        elif "bilibili" in name:
            mapped["B站"] = path
    return mapped


def quality_map(quality: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    rows = quality.get("results", []) if isinstance(quality, dict) else []
    mapped: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict):
            platform = str(row.get("platform", "")).strip()
            if platform:
                mapped[platform] = row
    return mapped


def build_pack_items(
    pack: Dict[str, Any],
    quality: Dict[str, Any],
    manifest: Dict[str, Any],
    tts_files: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    strategies = build_strategy_matrix()
    qmap = quality_map(quality)
    amap = map_assets(manifest)
    tmap = map_tts_files(tts_files)
    items: List[Dict[str, Any]] = []
    for draft in pack.get("drafts", []):
        if not isinstance(draft, dict):
            continue
        platform = str(draft.get("platform", "")).strip()
        strategy = strategies.get(platform, {})
        score_row = qmap.get(platform, {})
        asset_row = amap.get(platform, {})
        items.append(
            {
                "platform": platform,
                "title": draft.get("title", ""),
                "body": draft.get("body", draft.get("content", "")),
                "tags": draft.get("tags", []),
                "hook": draft.get("hook", ""),
                "cta": draft.get("cta", ""),
                "score": float(score_row.get("total_score", score_row.get("score", 0.0)) or 0.0),
                "pass": bool(score_row.get("pass_gate", score_row.get("pass", False))),
                "issues": score_row.get("issues", []),
                "platform_quality": score_row,
                "publish_windows": strategy.get("publish_windows", []),
                "recommended_publish_per_day": strategy.get("recommended_publish_per_day", 1),
                "recommended_produce_per_day": strategy.get("recommended_produce_per_day", 1),
                "primary_goal": strategy.get("primary_goal", ""),
                "post_type": strategy.get("post_type", ""),
                "manual_publish_priority": strategy.get("manual_publish_priority", 9),
                "notes": strategy.get("notes", ""),
                "cover_file": asset_row.get("output_file", ""),
                "tts_file": tmap.get(platform, ""),
            }
        )
    items.sort(key=lambda x: (x["manual_publish_priority"], -x["score"]))
    return items


def merge_queue_with_drafts(queue: Dict[str, Any], pack: Dict[str, Any], quality: Dict[str, Any]) -> List[Dict[str, Any]]:
    drafts = {str(item.get("platform", "")).strip(): item for item in pack.get("drafts", []) if isinstance(item, dict)}
    qrows = {str(item.get("platform", "")).strip(): item for item in quality.get("results", []) if isinstance(item, dict)}
    merged: List[Dict[str, Any]] = []
    for item in queue.get("items", []):
        platform = str(item.get("platform", "")).strip()
        draft = drafts.get(platform, {})
        score_row = qrows.get(platform, {})
        merged.append(
            {
                **item,
                "body": draft.get("body", draft.get("content", "")),
                "tags": draft.get("tags", []),
                "hook": draft.get("hook", item.get("hook", "")),
                "cta": draft.get("cta", item.get("cta", "")),
                "issues": score_row.get("issues", []),
                "platform_quality": score_row,
            }
        )
    return merged


def apply_publish_status(items: List[Dict[str, Any]], publish_status: Dict[str, Any], pack_path: str | None) -> List[Dict[str, Any]]:
    rows = publish_status.get("items", {}) if isinstance(publish_status, dict) else {}
    updated: List[Dict[str, Any]] = []
    for item in items:
        platform = str(item.get("platform", "")).strip()
        key = f"{pack_path}::{platform}"
        updated.append({**item, "publish_status": rows.get(key, {})})
    return updated


def summarize_pipeline_report(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps = []
    for key in [
        "main_brain",
        "autotune",
        "final_refine",
        "matrix_expand",
        "repair",
        "quality_gate",
        "specificity_boost",
        "quality_recheck",
        "tts_render",
        "asset_render",
        "manual_publish_queue",
        "publisher",
    ]:
        row = report.get(key, {})
        if not isinstance(row, dict):
            continue
        steps.append(
            {
                "step": key,
                "ok": row.get("ok"),
                "skipped": row.get("skipped", False),
                "duration_sec": row.get("duration_sec", ""),
                "stderr": row.get("stderr", ""),
            }
        )
    return steps


def summarize_health(health: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [row for row in health.get("results", []) if isinstance(row, dict)]


def build_trend_rows(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    platform_map: Dict[str, List[Dict[str, Any]]] = {}
    for snapshot in history:
        for platform, row in snapshot.get("platform_summary", {}).items():
            platform_map.setdefault(platform, []).append(
                {
                    "timestamp": snapshot.get("timestamp"),
                    "views": row.get("views", 0),
                    "engagement_rate": row.get("engagement_rate", 0),
                    "follow_rate": row.get("follow_rate", 0),
                    "revenue": row.get("revenue", 0),
                }
            )
    summary: List[Dict[str, Any]] = []
    for platform, points in platform_map.items():
        latest = points[-1]
        previous = points[-2] if len(points) > 1 else None
        summary.append(
            {
                "platform": platform,
                "points": points,
                "latest_views": latest.get("views", 0),
                "latest_revenue": latest.get("revenue", 0),
                "latest_engagement_rate": latest.get("engagement_rate", 0),
                "views_delta": (latest.get("views", 0) - previous.get("views", 0)) if previous else 0,
                "revenue_delta": (latest.get("revenue", 0) - previous.get("revenue", 0)) if previous else 0,
            }
        )
    summary.sort(key=lambda x: x["latest_views"], reverse=True)
    return summary


class OpenClawLocal:
    def __init__(self, config: RemoteConfig) -> None:
        self.config = config

    def read_text(self, path: str, encoding: str = "utf-8-sig") -> str:
        return Path(path).read_text(encoding=encoding, errors="replace")

    def read_json(self, path: str) -> Dict[str, Any]:
        return json.loads(self.read_text(path))

    def write_bytes(self, path: str, data: bytes) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def list_files(self, directory: str, startswith: str = "", endswith: str = "") -> List[Dict[str, Any]]:
        rows = []
        for path in Path(directory).iterdir():
            if path.is_file():
                if startswith and not path.name.startswith(startswith):
                    continue
                if endswith and not path.name.endswith(endswith):
                    continue
                stat = path.stat()
                rows.append(
                    {
                        "name": path.name,
                        "path": str(path),
                        "mtime": stat.st_mtime,
                        "size": stat.st_size,
                    }
                )
        rows.sort(key=lambda x: x["mtime"], reverse=True)
        return rows

    def latest_file(self, directory: str, startswith: str = "", endswith: str = "") -> str | None:
        rows = self.list_files(directory, startswith=startswith, endswith=endswith)
        return rows[0]["path"] if rows else None

    def run_powershell(self, script: str, timeout: int = 300) -> Dict[str, Any]:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "ok": proc.returncode == 0,
            "rc": proc.returncode,
            "stdout": (proc.stdout or "").strip(),
            "stderr": (proc.stderr or "").strip(),
        }

    def run_python(self, script_path: str, args: Iterable[str], timeout: int = 300) -> Dict[str, Any]:
        proc = subprocess.run(
            ["py", "-3", script_path, *list(args)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "ok": proc.returncode == 0,
            "rc": proc.returncode,
            "stdout": (proc.stdout or "").strip(),
            "stderr": (proc.stderr or "").strip(),
        }

    def run_healthcheck(self) -> Dict[str, Any]:
        script = ntpath.join(self.config.workspace, "full_agent_healthcheck.py")
        return self.run_python(script, [], timeout=600)

    def run_safe_pipeline(self, skip_assets: bool = False) -> Dict[str, Any]:
        script = ntpath.join(self.config.workspace, "autopipeline_brain_content_publisher.py")
        args = ["--skip-publisher"]
        if skip_assets:
            args.append("--skip-assets")
        return self.run_python(script, args, timeout=2400)

    def ingest_metrics(self, filename: str, payload: bytes) -> Dict[str, Any]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        remote_input = ntpath.join(self.config.content_dir, "metrics_uploads", f"{timestamp}_{ntpath.basename(filename)}")
        out_json = ntpath.join(self.config.content_dir, f"metrics_analysis_{timestamp}.json")
        out_md = ntpath.join(self.config.content_dir, f"metrics_analysis_{timestamp}.md")
        latest_json = ntpath.join(self.config.content_dir, "metrics_analysis_latest.json")
        latest_md = ntpath.join(self.config.content_dir, "metrics_analysis_latest.md")
        self.write_bytes(remote_input, payload)
        script = ntpath.join(self.config.workspace, "daily_metrics_ingest.py")
        result = self.run_python(
            script,
            [
                "--input",
                remote_input,
                "--output-json",
                out_json,
                "--output-md",
                out_md,
                "--latest-json",
                latest_json,
                "--latest-md",
                latest_md,
            ],
            timeout=300,
        )
        result["paths"] = {
            "input": remote_input,
            "output_json": out_json,
            "output_md": out_md,
            "latest_json": latest_json,
            "latest_md": latest_md,
        }
        return result

    def read_publish_status(self) -> Dict[str, Any]:
        path = ntpath.join(self.config.content_dir, "publish_status_latest.json")
        if not Path(path).exists():
            return {"updated_at": "", "items": {}}
        return self.read_json(path)

    def update_publish_status(self, pack_path: str, platform: str, update: Dict[str, Any]) -> Dict[str, Any]:
        path = ntpath.join(self.config.content_dir, "publish_status_latest.json")
        data = self.read_publish_status()
        items = data.setdefault("items", {})
        key = f"{pack_path}::{platform}"
        current = items.get(key, {})
        current.update(update)
        current["pack_path"] = pack_path
        current["platform"] = platform
        current["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        items[key] = current
        data["updated_at"] = current["updated_at"]
        self.write_bytes(path, json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
        return current

    def metrics_history(self, limit: int = 14) -> List[Dict[str, Any]]:
        rows = []
        for file in self.list_files(self.config.content_dir, "metrics_analysis_", ".json"):
            if ntpath.basename(file["path"]) == "metrics_analysis_latest.json":
                continue
            try:
                payload = self.read_json(file["path"])
            except Exception:
                continue
            rows.append(
                {
                    "path": file["path"],
                    "mtime": file["mtime"],
                    "timestamp": format_timestamp(file["mtime"]),
                    "platform_summary": payload.get("platform_summary", {}),
                }
            )
            if len(rows) >= limit:
                break
        return list(reversed(rows))

    def content_packs(self, limit: int = 20) -> List[Dict[str, Any]]:
        rows = []
        for file in self.list_files(self.config.content_dir, "daily_pack_", ".json"):
            name = file["name"]
            if "_raw_" in name or name.endswith("_boosted.json"):
                continue
            rows.append(file)
            if len(rows) >= limit:
                break
        return rows

    def dashboard_snapshot(self, pack_path: str | None = None) -> Dict[str, Any]:
        latest_report = self.latest_file(ntpath.join(self.config.workspace, "reports"), "pipeline_autorun_", ".json")
        latest_health = self.latest_file(ntpath.join(self.config.workspace, "reports"), "agent_health_full_", ".json")
        latest_queue = ntpath.join(self.config.content_dir, "manual_publish_queue_latest.json")
        latest_metrics = ntpath.join(self.config.content_dir, "metrics_analysis_latest.json")

        report = self.read_json(latest_report) if latest_report else {}
        queue = self.read_json(latest_queue) if self.exists(latest_queue) else {}
        metrics = self.read_json(latest_metrics) if self.exists(latest_metrics) else {}
        selected_pack_path = pack_path or queue.get("source_pack") or self.latest_content_pack()
        pack_history = self.content_packs()
        pack = self.read_json(selected_pack_path) if selected_pack_path and self.exists(selected_pack_path) else {}
        health = self.read_json(latest_health) if latest_health else {}
        quality_path = self._quality_path_from_pack(selected_pack_path)
        quality = self.read_json(quality_path) if quality_path and self.exists(quality_path) else {}
        asset_path = asset_manifest_path(self.config.content_dir, selected_pack_path)
        asset_manifest = self.read_json(asset_path) if asset_path and self.exists(asset_path) else {}
        tts_dir = tts_dir_path(self.config.content_dir, selected_pack_path)
        tts_files = self.list_files(tts_dir, endswith=".wav") if tts_dir and self.exists(tts_dir) else []
        publish_status = self.read_publish_status()
        metrics_history = self.metrics_history()
        pack_items = apply_publish_status(build_pack_items(pack, quality, asset_manifest, tts_files), publish_status, selected_pack_path)

        return {
            "report_path": latest_report,
            "health_path": latest_health,
            "queue_path": latest_queue if queue else None,
            "metrics_path": latest_metrics if metrics else None,
            "pack_path": selected_pack_path,
            "quality_path": quality_path,
            "asset_manifest_path": asset_path,
            "tts_dir": tts_dir,
            "report": report,
            "queue": queue,
            "metrics": metrics,
            "pack": pack,
            "quality": quality,
            "asset_manifest": asset_manifest,
            "tts_files": tts_files,
            "health": health,
            "publish_status": publish_status,
            "metrics_history": metrics_history,
            "pack_history": pack_history,
            "pack_items": pack_items,
        }

    def latest_content_pack(self) -> str | None:
        files = self.list_files(self.config.content_dir, "daily_pack_", ".json")
        for row in files:
            name = row["name"]
            if "_raw_" in name or name.endswith("_boosted.json"):
                continue
            return row["path"]
        return None

    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def read_media(self, path: str) -> Tuple[bytes, str]:
        self._assert_allowed(path)
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        return Path(path).read_bytes(), mime

    def _quality_path_from_pack(self, pack_path: str | None) -> str | None:
        if not pack_path:
            return None
        name = ntpath.basename(pack_path)
        if not name.startswith("daily_pack_") or not name.endswith(".json"):
            return None
        stamp = name[len("daily_pack_") : -len(".json")]
        return ntpath.join(self.config.content_dir, f"quality_{stamp}_recheck.json")

    def _assert_allowed(self, path: str) -> None:
        normalized = str(Path(path).resolve()).lower()
        allowed_roots = [
            str(Path(self.config.content_dir).resolve()).lower(),
            str(Path(self.config.workspace).resolve()).lower(),
            str(Path(self.config.comfy_output).resolve()).lower(),
        ]
        if not any(normalized.startswith(root) for root in allowed_roots):
            raise ValueError("local path not allowed")


def make_backend(config: RemoteConfig, backend: str = "remote"):
    if backend == "local":
        return OpenClawLocal(config)
    return OpenClawRemote(config)
