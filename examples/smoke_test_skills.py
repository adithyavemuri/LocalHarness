#!/usr/bin/env python3
"""Check automatic and forced skill-read tool calls against a running local server.

This is an API compatibility probe, not a Cline end-to-end test. No shell,
external MCP server or image backend is exposed to the model.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from local_skills import read_skill
TOOL = {"type": "function", "function": {
    "name": "read_skill", "description": "Read the installed Karpathy coding guidelines.",
    "parameters": {"type": "object", "properties": {
        "name": {"type": "string", "enum": ["karpathy-guidelines"]}},
        "required": ["name"], "additionalProperties": False},
}}


def completion(base: str, body: dict, timeout: int) -> dict:
    request = urllib.request.Request(base + "/chat/completions", json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)["choices"][0]["message"]


def probe(base: str, model: str, mode: str, timeout: int) -> dict:
    messages = [
        {"role": "system", "content": "Use the read_skill tool before answering. "
         "After reading it, answer the user's question briefly. Do not call the tool twice."},
        {"role": "user", "content": "Read karpathy-guidelines, then describe one concrete "
         "check you should make before changing code."},
    ]
    body = {"model": model, "messages": messages, "tools": [TOOL],
            "tool_choice": "auto" if mode == "auto" else "required",
            "temperature": 0, "max_tokens": 256, "stream": False}
    first = completion(base, body, timeout)
    calls = first.get("tool_calls") or []
    if len(calls) != 1 or calls[0].get("function", {}).get("name") != "read_skill":
        raise ValueError(f"Expected one read_skill call; received {first!r}")
    call = calls[0]
    if json.loads(call["function"]["arguments"]) != {"name": "karpathy-guidelines"}:
        raise ValueError(f"Unexpected tool arguments: {call!r}")
    # Only this fixed file can be read; model arguments never become a path/command.
    messages.extend([first, {"role": "tool", "tool_call_id": call["id"],
                             "content": read_skill("karpathy-guidelines")}])
    body["tool_choice"] = "none"
    final = completion(base, body, timeout)
    if final.get("tool_calls") or not (final.get("content") or "").strip():
        raise ValueError(f"Expected an answer after the tool result; received {final!r}")
    return {"mode": mode, "pass": True, "tool_call": call, "answer": final["content"]}


def check_model(base: str, model: str, timeout: int = 180) -> dict:
    report = {"model": model, "base_url": base, "checks": [], "success": False,
              "scope": "API tool round-trip only; Cline/MCP/image generation not tested"}
    for mode in ("auto", "forced"):
        try:
            report["checks"].append(probe(base.rstrip("/"), model, mode, timeout))
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            report["checks"].append({"mode": mode, "pass": False, "error": str(exc)})
    report["success"] = all(check["pass"] for check in report["checks"])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    parser.add_argument("--model", default="qwen3.5-4b", help="Use the ID advertised by /v1/models")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--report", type=Path, default=ROOT / "logs/skills-smoke-test.json")
    args = parser.parse_args()
    url = urllib.parse.urlsplit(args.base_url)
    if url.scheme != "http" or url.hostname not in ("localhost", "127.0.0.1", "::1"):
        parser.error("Use an HTTP loopback endpoint; this probe is for local inference.")
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    report = check_model(args.base_url, args.model, args.timeout)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Saved: {args.report}")
    return 0 if report["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
