#!/usr/bin/env python3
"""Test managed OpenCode instruction loading with installed local models, one at a time.

Starts and stops its own servers. Does not download weights. OpenCode setup
may download its pinned binary on first use. This checks instruction delivery
and client/server cleanup, not native tool compliance or external MCP services.
"""
import argparse
import json
from pathlib import Path
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from local_skills import skill_names
from model_config import catalog, model_ready, selection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", choices=list(catalog()["models"]),
                        default=["qwen3.5-4b", "gemma4-e2b", "phi4-mini", "qwen3.8-27b"])
    parser.add_argument("--backend", choices=("auto", "cpu", "vulkan"), default="auto")
    args = parser.parse_args()
    for preset in args.models:
        spec = selection(preset)
        if not model_ready(ROOT / "models" / spec["filename"], spec):
            parser.error(f"{preset} is not installed; this test does not download weights")
    workspace = ROOT / "runtime/opencode-smoke-workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    report = {"checks": [], "context": 16384, "backend": args.backend,
              "scope": "OpenCode one-shot instruction loading; not native tools, MCP or browser UI"}
    for preset in args.models:
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        print(f"OpenCode shared-instruction check: {preset}", flush=True)
        began = time.monotonic()
        completed = subprocess.run([
            sys.executable, str(ROOT / "run_server.py"), "--client", "opencode", "--preset", preset,
            "--backend", args.backend, "--thinking", "off", "--context", "16384", "--port", str(port),
            "--workspace", str(workspace), "--prompt",
            "Without calling tools, list the four exact skill names from the preloaded instructions, "
            "then print LOCAL_OPENCODE_OK. Do not modify files.",
        ], cwd=ROOT, text=True, capture_output=True)
        events = [json.loads(line) for line in completed.stdout.splitlines() if line.startswith('{"type":')]
        text = "\n".join(event.get("part", {}).get("text", "") for event in events if event["type"] == "text")
        with socket.socket() as check:
            stopped = check.connect_ex(("127.0.0.1", port)) != 0
        passed = completed.returncode == 0 and stopped and all(
            name in text.lower() for name in skill_names())
        record = {"model": preset, "pass": passed, "exit_code": completed.returncode,
                  "server_stopped": stopped, "format_marker_received": "LOCAL_OPENCODE_OK" in text,
                  "answer": text, "seconds": round(time.monotonic() - began, 2)}
        if not passed:
            record["stderr"] = completed.stderr[-3000:]
        (logs / f"opencode-{preset}-smoke.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        report["checks"].append(record)
        report["success"] = all(item["pass"] for item in report["checks"])
        (logs / "opencode-smoke-test.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(record), flush=True)
    return 0 if report["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
