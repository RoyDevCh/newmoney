#!/usr/bin/env python3
"""Remote OpenClaw validation suite with monetization-grade content checks."""

from __future__ import annotations

import argparse
import base64
import json
import re
import time
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import paramiko

from content_quality_gate import DraftScore, score_one


AGENT_PROMPTS = {
    "main": "你是总控agent。只输出JSON对象：{\"status\":\"ok\",\"summary\":\"一句系统状态摘要\",\"next_action\":\"一句下一步\"}",
    "main-brain": (
        "你是策略agent。主题是“AI办公自动化提效与变现”。"
        "只输出JSON对象，字段: audience,platform_priority,conversion_goal,angle。"
    ),
    "content": (
        "你是内容agent。只输出JSON对象，字段: platform,title,hook,body,cta,tags。"
        "平台固定为知乎，主题“AI办公自动化提效与变现”。"
        "要求：开头有冲突点、正文有来源/实测语气、结尾有评论或收藏CTA。"
    ),
    "multimodal": (
        "你是多模态agent。只输出JSON对象，字段: prompt,negative_prompt,style。"
        "主题是AI办公自动化封面图。"
    ),
    "publisher": (
        "你是发布agent。只输出JSON对象，字段: supported_platforms,checks,blockers。"
        "说明当前可测试发布的平台，以及每个平台的前置检查项。"
    ),
    "monitor": "你是监控agent。只输出JSON对象，字段: metrics,risk,action。metrics必须是5项数组。",
    "tasks": "你是执行agent。只输出JSON对象，字段: tasks。tasks必须是3项数组，每项是一句可执行动作。",
}

ARTICLE_PLATFORMS = ["知乎", "小红书"]
VIDEO_PLATFORMS = ["抖音", "B站"]

PLATFORM_THRESHOLDS = {
    "知乎": 86.0,
    "小红书": 85.0,
    "抖音": 85.0,
    "B站": 86.0,
}

BLOCKING_ISSUES = {
    "missing_title",
    "missing_hook",
    "missing_body",
    "missing_cta",
    "body_maybe_truncated",
    "no_source_or_test_context",
    "cta_weak",
    "tags_insufficient",
    "body_too_short_for_platform",
}


def extract_json(text: str) -> Any:
    text = (text or "").strip()
    if not text:
        raise ValueError("empty text")
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.S | re.I)
    candidate = match.group(1) if match else text

    for left, right in [("[", "]"), ("{", "}")]:
        start = candidate.find(left)
        end = candidate.rfind(right)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(candidate[start : end + 1])
            except Exception:
                continue
    raise ValueError("could not extract json")


def unwrap_openclaw_payload(raw: str) -> str:
    data = extract_json(raw)
    if isinstance(data, dict):
        result = data.get("result", {})
        payloads = result.get("payloads", [])
        if payloads and isinstance(payloads[0], dict):
            text = payloads[0].get("text")
            if isinstance(text, str):
                return text.strip()
    return raw.strip()


def normalize_drafts(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        if isinstance(data.get("drafts"), list):
            return [x for x in data["drafts"] if isinstance(x, dict)]
        return [data]
    raise ValueError("unsupported draft payload")


def select_best_drafts(drafts: List[Dict[str, Any]], target_platforms: List[str]) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    for platform in target_platforms:
        candidates = [d for d in drafts if str(d.get("platform", "")).strip() == platform]
        if not candidates:
            continue
        threshold = PLATFORM_THRESHOLDS.get(platform, 85.0)
        best = max(candidates, key=lambda d: score_one(d, threshold).total_score)
        selected.append(best)
    return selected


def is_monetization_ready(score: DraftScore, threshold: float) -> bool:
    if score.total_score < threshold:
        return False
    return not any(issue in BLOCKING_ISSUES for issue in score.issues)


class SSHRunner:
    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client: paramiko.SSHClient | None = None

    def connect(self) -> None:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=20,
            banner_timeout=20,
            auth_timeout=20,
        )
        self.client = client

    def close(self) -> None:
        if self.client:
            self.client.close()
            self.client = None

    def run_powershell(self, script: str, timeout: int = 180) -> Dict[str, Any]:
        if not self.client:
            raise RuntimeError("ssh not connected")
        encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
        cmd = f"powershell -NoProfile -EncodedCommand {encoded}"
        started = time.time()
        stdin, stdout, stderr = self.client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode("utf-8", "replace")
        err = stderr.read().decode("utf-8", "replace")
        return {
            "ok": True,
            "stdout": out.strip(),
            "stderr": err.strip(),
            "duration_sec": round(time.time() - started, 2),
        }

    def run_agent(self, agent: str, message: str, timeout_sec: int = 180) -> Dict[str, Any]:
        session_id = f"codex-{agent}-{uuid.uuid4()}"
        compact_message = re.sub(r"\s+", " ", message).strip()
        message_b64 = base64.b64encode(compact_message.encode("utf-8")).decode("ascii")
        script = rf"""
$msg = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("{message_b64}"))
$node = "C:\Program Files\nodejs\node.exe"
$entry = "$env:USERPROFILE\AppData\Roaming\npm\node_modules\openclaw\openclaw.mjs"
& $node $entry agent --agent "{agent}" --session-id "{session_id}" --message $msg --timeout {timeout_sec} --json
"""
        result = self.run_powershell(script, timeout=timeout_sec + 120)
        raw = result["stdout"]
        payload_text = ""
        parse_error = ""
        try:
            payload_text = unwrap_openclaw_payload(raw)
        except Exception as exc:
            parse_error = str(exc)
        result.update(
            {
                "agent": agent,
                "session_id": session_id,
                "raw": raw,
                "payload_text": payload_text,
                "parse_error": parse_error,
            }
        )
        return result


def test_agent_availability(runner: SSHRunner) -> List[Dict[str, Any]]:
    results = []
    for agent, prompt in AGENT_PROMPTS.items():
        res = runner.run_agent(agent, prompt, timeout_sec=180)
        payload = res.get("payload_text", "")
        parsed = None
        ok = False
        try:
            parsed = extract_json(payload)
            ok = True
        except Exception:
            ok = bool(payload)
        results.append(
            {
                "agent": agent,
                "ok": ok and not res.get("stderr"),
                "duration_sec": res["duration_sec"],
                "stderr": res["stderr"],
                "payload_text": payload[:2000],
                "parsed": parsed,
                "parse_error": res["parse_error"],
            }
        )
    return results


def build_strategy_prompt(topic: str, platforms: List[str], style: str) -> str:
    ps = "、".join(platforms)
    return (
        f"你是平台策略agent。主题是“{topic}”，目标平台是{ps}，内容类型={style}。"
        "只输出JSON对象，字段: angle,audience,platform_priority,conversion_goal,content_pillars。"
        "content_pillars必须是3项数组。"
    )


def build_generation_prompt(topic: str, platforms: List[str], strategy: Dict[str, Any], style: str) -> str:
    ps = "、".join(platforms)
    if isinstance(strategy, dict):
        strategy_brief = {
            "angle": strategy.get("angle", ""),
            "audience": strategy.get("audience", ""),
            "conversion_goal": strategy.get("conversion_goal", ""),
        }
    else:
        strategy_brief = {"pillars": strategy[:3] if isinstance(strategy, list) else str(strategy)}
    strategy_json = json.dumps(strategy_brief, ensure_ascii=False)
    platform_rules = (
        "平台细则：知乎正文550-900字、不得使用emoji数字序号；"
        "小红书正文180-420字、可少量emoji；"
        "抖音正文140-260字、至少5个短句分段；"
        "B站正文320-700字、分点写清证据和动作、尽量不用emoji。"
    )
    return (
        f"只输出JSON数组。基于主题“{topic}”和策略{strategy_json}，为{ps}各生成且仅生成1篇{style}内容草稿。"
        "每个平台字段必须包含platform,title,hook,body,cta,tags。"
        "硬性要求：1) 前50字必须有反常识或冲突点；"
        "2) 正文必须出现来源、公开评测、实测环境、官方信息中的至少一种语气；"
        "3) 每段不超过3句，避免空泛形容词；"
        "4) CTA必须匹配平台行为；"
        f"5) {platform_rules}"
        "6) 输出必须可直接json.loads，且数组顺序与目标平台顺序一致。"
    )


def build_fallback_generation_prompt(topic: str, platforms: List[str]) -> str:
    ps = "、".join(platforms)
    return (
        f"只输出JSON数组。为{ps}各生成1条主题“{topic}”的内容，字段platform,title,hook,body,cta,tags。"
        "知乎正文550-900字且不要emoji；"
        "小红书正文180-420字；"
        "抖音正文140-260字且至少5个短句；"
        "B站正文320-700字且证据先行。"
        "正文必须有来源、公开评测、实测环境或官方信息语气。"
    )


def build_rewrite_prompt(topic: str, draft: Dict[str, Any], score: DraftScore, threshold: float) -> str:
    draft_json = json.dumps(draft, ensure_ascii=False)
    issues = ";".join(score.issues) if score.issues else "无"
    platform = str(draft.get("platform", "")).strip()
    platform_rule = {
        "知乎": "正文必须550字以上，不要emoji或emoji数字序号，结构更像深度答主分析。",
        "小红书": "正文控制在180-420字，可保留少量情绪词，但必须具体。",
        "抖音": "正文140-260字，至少5个短句分段，适合口播。",
        "B站": "正文320-700字，证据先行，分点结构，不要emoji数字序号。",
    }.get(platform, "")
    return (
        "只输出JSON对象。你是平台增长编辑，不是文案学徒。"
        f"平台={platform}，主题={topic}，目标分数>={threshold}。"
        f"当前草稿={draft_json}。问题清单={issues}。"
        "强制要求：1) 去除无法验证的绝对化结论，数字必须带来源/实测语气；"
        "2) 前50字必须有冲突点；"
        "3) 结构只保留结论->证据->动作；"
        "4) 每段不超过3句；"
        "5) CTA必须匹配平台；"
        f"6) {platform_rule}"
        "7) 输出合法JSON字段platform,title,hook,body,cta,tags。"
    )


def optimize_drafts(
    runner: SSHRunner,
    topic: str,
    drafts: List[Dict[str, Any]],
    max_rounds: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    final_drafts: List[Dict[str, Any]] = []
    logs: List[Dict[str, Any]] = []
    for draft in drafts:
        cur = draft
        platform = str(cur.get("platform", "")).strip()
        threshold = PLATFORM_THRESHOLDS.get(platform, 85.0)
        current_score = score_one(cur, threshold)
        rounds = 0

        while not is_monetization_ready(current_score, threshold) and rounds < max_rounds:
            rounds += 1
            prompt = build_rewrite_prompt(topic, cur, current_score, threshold)
            res = runner.run_agent("content", prompt, timeout_sec=300)
            try:
                rewritten = extract_json(res["payload_text"])
                if isinstance(rewritten, list):
                    rewritten = rewritten[0]
                if isinstance(rewritten, dict):
                    cur = rewritten
            except Exception:
                break
            current_score = score_one(cur, threshold)

        final_drafts.append(cur)
        logs.append(
            {
                "platform": platform,
                "threshold": threshold,
                "score": current_score.total_score,
                "ready": is_monetization_ready(current_score, threshold),
                "issues": current_score.issues,
                "rounds": rounds,
                "subscores": current_score.subscores,
            }
        )
    return final_drafts, logs


def run_content_phase(
    runner: SSHRunner,
    topic: str,
    platforms: List[str],
    style: str,
    max_rounds: int,
) -> Dict[str, Any]:
    phase: Dict[str, Any] = {
        "platforms": platforms,
        "style": style,
        "strategy": None,
        "strategy_raw": "",
        "drafts": [],
        "scores": [],
        "publisher_review": None,
        "errors": [],
    }

    strategy_result = runner.run_agent("main-brain", build_strategy_prompt(topic, platforms, style), timeout_sec=180)
    phase["strategy_raw"] = strategy_result["payload_text"][:2000]
    try:
        strategy = extract_json(strategy_result["payload_text"])
        phase["strategy"] = strategy
    except Exception as exc:
        phase["errors"].append(f"strategy_parse_failed: {exc}")
        return phase

    gen_result = runner.run_agent("content", build_generation_prompt(topic, platforms, strategy, style), timeout_sec=360)
    phase["generation_raw"] = gen_result["payload_text"][:3000]
    if gen_result.get("stderr"):
        phase["errors"].append(f"generation_stderr: {gen_result['stderr'][:500]}")
    try:
        drafts = normalize_drafts(extract_json(gen_result["payload_text"]))
    except Exception as exc:
        phase["errors"].append(f"generation_parse_failed: {exc}")
        fallback_result = runner.run_agent("content", build_fallback_generation_prompt(topic, platforms), timeout_sec=240)
        phase["generation_fallback_raw"] = fallback_result["payload_text"][:3000]
        if fallback_result.get("stderr"):
            phase["errors"].append(f"generation_fallback_stderr: {fallback_result['stderr'][:500]}")
        try:
            drafts = normalize_drafts(extract_json(fallback_result["payload_text"]))
        except Exception as fallback_exc:
            phase["errors"].append(f"generation_fallback_parse_failed: {fallback_exc}")
            return phase
    drafts = select_best_drafts(drafts, platforms)
    if len(drafts) != len(platforms):
        phase["errors"].append("missing_platform_drafts_after_selection")

    optimized_drafts, score_log = optimize_drafts(runner, topic, drafts, max_rounds=max_rounds)
    phase["drafts"] = optimized_drafts
    phase["scores"] = score_log

    publisher_prompt = (
        "你是发布前审核agent。不要外发，不要真的发布。"
        f"请审核下面这些平台草稿是否具备可发布与可转化潜力：{json.dumps(optimized_drafts, ensure_ascii=False)}。"
        "只输出JSON对象，字段: verdict,platform_reviews,global_risks,next_action。"
    )
    pub_result = runner.run_agent("publisher", publisher_prompt, timeout_sec=240)
    try:
        phase["publisher_review"] = extract_json(pub_result["payload_text"])
    except Exception:
        phase["publisher_review"] = {"raw": pub_result["payload_text"][:2000]}
        phase["errors"].append("publisher_review_parse_failed")

    return phase


def test_collaboration(runner: SSHRunner, article_result: Dict[str, Any], video_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    results = []

    main_prompt = (
        "只输出JSON对象，字段: task。"
        "给tasks agent生成一句明确可执行的任务，目标是复核知乎和小红书内容包是否达到可转化发布标准。"
    )
    main_result = runner.run_agent("main", main_prompt, timeout_sec=120)
    main_json = extract_json(main_result["payload_text"])
    task_text = str(main_json.get("task", "")).strip()
    tasks_result = runner.run_agent(
        "tasks",
        f"只输出JSON对象，字段: checklist。根据这句任务生成3项执行清单：{task_text}",
        timeout_sec=120,
    )
    results.append(
        {
            "name": "main_to_tasks",
            "ok": bool(task_text) and bool(tasks_result.get("payload_text")),
            "main_output": main_json,
            "tasks_output": extract_json(tasks_result["payload_text"]),
        }
    )

    results.append(
        {
            "name": "brain_content_publisher_articles",
            "ok": bool(article_result.get("scores")) and all(x.get("ready") for x in article_result["scores"]),
            "scores": article_result.get("scores", []),
            "errors": article_result.get("errors", []),
            "publisher_review": article_result["publisher_review"],
        }
    )
    results.append(
        {
            "name": "brain_content_publisher_videos",
            "ok": bool(video_result.get("scores")) and all(x.get("ready") for x in video_result["scores"]),
            "scores": video_result.get("scores", []),
            "errors": video_result.get("errors", []),
            "publisher_review": video_result["publisher_review"],
        }
    )
    return results


def build_summary(report: Dict[str, Any]) -> Dict[str, Any]:
    article_scores = report["content_tests"]["articles"].get("scores", [])
    video_scores = report["content_tests"]["videos"].get("scores", [])
    return {
        "agents_ok": [x["agent"] for x in report["agent_tests"] if x["ok"]],
        "agents_failed": [x["agent"] for x in report["agent_tests"] if not x["ok"]],
        "article_ready": [x["platform"] for x in article_scores if x["ready"]],
        "article_failed": [x["platform"] for x in article_scores if not x["ready"]],
        "video_ready": [x["platform"] for x in video_scores if x["ready"]],
        "video_failed": [x["platform"] for x in video_scores if not x["ready"]],
        "collaboration_ok": [x["name"] for x in report["collaboration_tests"] if x["ok"]],
        "collaboration_failed": [x["name"] for x in report["collaboration_tests"] if not x["ok"]],
        "article_errors": report["content_tests"]["articles"].get("errors", []),
        "video_errors": report["content_tests"]["videos"].get("errors", []),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="192.168.3.120")
    ap.add_argument("--port", type=int, default=2222)
    ap.add_argument("--username", default="Roy")
    ap.add_argument("--password", default="kaiyic")
    ap.add_argument("--topic", default="AI办公自动化提效与变现")
    ap.add_argument("--max-rewrite-rounds", type=int, default=3)
    ap.add_argument("--out-dir", default="reports")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    report: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "remote": {
            "host": args.host,
            "port": args.port,
            "username": args.username,
        },
    }

    runner = SSHRunner(args.host, args.port, args.username, args.password)
    runner.connect()
    try:
        report["agent_tests"] = test_agent_availability(runner)
        report["content_tests"] = {
            "articles": run_content_phase(
                runner,
                topic=args.topic,
                platforms=ARTICLE_PLATFORMS,
                style="文章平台内容",
                max_rounds=args.max_rewrite_rounds,
            ),
            "videos": run_content_phase(
                runner,
                topic=args.topic,
                platforms=VIDEO_PLATFORMS,
                style="视频平台脚本型内容",
                max_rounds=args.max_rewrite_rounds,
            ),
        }
        report["collaboration_tests"] = test_collaboration(
            runner,
            article_result=report["content_tests"]["articles"],
            video_result=report["content_tests"]["videos"],
        )
        report["summary"] = build_summary(report)
    finally:
        runner.close()

    out_file = out_dir / f"remote_openclaw_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(out_file), "summary": report["summary"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
