#!/usr/bin/env python3
"""Read-only production readiness check for OpenMontage (no paid API calls)."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("python", "ffmpeg", "ffprobe", "node", "npm")
PROJECT_FILES = ("AGENT_GUIDE.md", "requirements.txt", "pipeline_defs", "remotion-composer")

def inspect(root=ROOT):
    checks = []
    for name in REQUIRED:
        executable = sys.executable if name == "python" else shutil.which(name)
        checks.append({"name": name, "ok": bool(executable), "detail": str(executable or "not found")})
    checks.append({"name": "python>=3.10", "ok": sys.version_info >= (3, 10), "detail": sys.version.split()[0]})
    for relative in PROJECT_FILES:
        path = root / relative
        checks.append({"name": relative, "ok": path.exists(), "detail": "present" if path.exists() else "missing"})
    checks.append({"name": "remotion node_modules", "ok": (root / "remotion-composer" / "node_modules").is_dir(), "detail": "installed" if (root / "remotion-composer" / "node_modules").is_dir() else "run make setup"})
    return checks

def validate_video(path):
    command = ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(path)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
    if result.returncode:
        return {"ok": False, "error": result.stderr.strip() or "ffprobe failed"}
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    duration = float(data.get("format", {}).get("duration", 0))
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = any(s.get("codec_type") == "audio" for s in streams)
    return {"ok": bool(video and duration > 0), "duration_seconds": duration, "width": video.get("width") if video else None, "height": video.get("height") if video else None, "has_audio": audio}

def main():
    parser = argparse.ArgumentParser(description="Check local production readiness without spending credits")
    parser.add_argument("--video", type=Path, help="Optional rendered video to inspect with ffprobe")
    parser.add_argument("--require-audio", action="store_true", help="Fail if the rendered video has no audio")
    args = parser.parse_args()
    checks = inspect()
    report = {"ready": all(c["ok"] for c in checks), "checks": checks}
    if args.video:
        try:
            report["video"] = validate_video(args.video)
        except (OSError, ValueError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            report["video"] = {"ok": False, "error": str(exc)}
        report["ready"] = report["ready"] and report["video"]["ok"] and (not args.require_audio or report["video"].get("has_audio", False))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ready"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
