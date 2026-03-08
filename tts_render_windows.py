#!/usr/bin/env python3
"""Render TTS audio files for video publish kits on Windows via System.Speech."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List


VOICE_BY_PLATFORM = {
    "douyin": "Microsoft Yunxi Desktop",
    "bilibili": "Microsoft Yunyang Desktop",
}


def load_pack(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def render_one(text: str, out_path: Path, voice_name: str, rate: int) -> None:
    escaped_text = text.replace("'", "''")
    escaped_voice = voice_name.replace("'", "''")
    ps = f"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {{
  $voice = $synth.GetInstalledVoices() | Where-Object {{ $_.VoiceInfo.Name -like '*{escaped_voice}*' }} | Select-Object -First 1
  if ($voice) {{ $synth.SelectVoice($voice.VoiceInfo.Name) }}
  $synth.Rate = {rate}
  $synth.SetOutputToWaveFile('{str(out_path).replace("'", "''")}')
  $synth.Speak('{escaped_text}')
}} finally {{
  $synth.Dispose()
}}
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        check=True,
        timeout=300,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    pack = load_pack(Path(args.input))
    kits = pack.get("video_publish_kits", {})
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results: List[Dict[str, Any]] = []
    for key in ["douyin", "bilibili"]:
        kit = kits.get(key, {})
        script = str(kit.get("tts_script", "")).strip()
        if not script:
            continue
        out_path = out_dir / f"{key}_tts.wav"
        voice = VOICE_BY_PLATFORM.get(key, "")
        rate = 1 if key == "douyin" else -1
        render_one(script, out_path, voice_name=voice, rate=rate)
        results.append(
            {
                "platform": key,
                "output_file": str(out_path),
                "exists": out_path.exists(),
                "size_mb": round(out_path.stat().st_size / (1024 * 1024), 2) if out_path.exists() else 0.0,
            }
        )

    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
