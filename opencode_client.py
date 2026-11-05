"""Pinned, package-local OpenCode installation and local-server lifecycle."""
from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import shutil
import signal
import socket
import subprocess
import tarfile
import tempfile
import time
import urllib.request
import zipfile

from model_config import ROOT, selection, verify_file
from local_skills import skill_names


def release() -> tuple[str, dict]:
    pins = json.loads((ROOT / "integrations/opencode-release.json").read_text(encoding="utf-8"))
    system = platform.system()
    if platform.machine().lower() not in ("x86_64", "amd64") or system not in ("Linux", "Windows"):
        raise ValueError("Managed OpenCode supports Linux/Windows x64; use an external client on other platforms.")
    return pins["version"], pins["windows_x64" if system == "Windows" else "linux_x64"]


def environment(config: dict | None = None) -> dict:
    env = os.environ.copy()
    state = ROOT / "runtime/opencode/state"
    for kind in ("DATA", "CACHE", "CONFIG", "STATE"):
        env[f"XDG_{kind}_HOME"] = str(state / kind.lower())
    env.update(OPENCODE_DISABLE_AUTOUPDATE="1", OPENCODE_DISABLE_MODELS_FETCH="1",
               OPENCODE_DISABLE_DEFAULT_PLUGINS="1", OPENCODE_DISABLE_LSP_DOWNLOAD="1")
    if config is not None:
        env["OPENCODE_CONFIG_CONTENT"] = json.dumps(config)
    return env


def extract_binary(archive: Path, destination: Path) -> None:
    """Copy only the one regular executable; never extract archive paths or links."""
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as bundle:
            members = [item for item in bundle.infolist()
                       if Path(item.filename).name == "opencode.exe" and not item.is_dir()]
            if len(members) != 1 or (members[0].external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Expected exactly one regular opencode.exe in the archive.")
            with bundle.open(members[0]) as source, destination.open("xb") as target:
                shutil.copyfileobj(source, target)
    else:
        with tarfile.open(archive) as bundle:
            members = [item for item in bundle.getmembers() if Path(item.name).name == "opencode"]
            if len(members) != 1 or not members[0].isfile():
                raise ValueError("Expected exactly one regular opencode in the archive.")
            with bundle.extractfile(members[0]) as source, destination.open("xb") as target:
                shutil.copyfileobj(source, target)
        destination.chmod(0o755)


def ensure(dry_run: bool = False) -> Path:
    version, spec = release()
    name = "opencode.exe" if platform.system() == "Windows" else "opencode"
    destination = ROOT / "runtime/opencode" / version / name
    if dry_run:
        print(f"OpenCode {version}: {'reuse' if destination.is_file() else 'download and verify'} {destination}")
        return destination
    env = environment()
    if destination.is_file():
        actual = subprocess.check_output([str(destination), "--version"], env=env, text=True).strip()
        if actual != version:
            raise ValueError(f"Managed OpenCode version mismatch: expected {version}, received {actual!r}.")
        return destination
    archive = ROOT / "downloads" / f"opencode-{version}-{spec['filename']}"
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.is_file():
        verify_file(archive, spec)
    else:
        partial = archive.with_name(archive.name + ".part")
        print(f"Downloading pinned OpenCode {version} ({spec['size_bytes'] / 1e6:.0f} MB)...", flush=True)
        subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error", "--retry", "3",
                        "--continue-at", "-", "--output", str(partial), spec["url"]], check=True)
        verify_file(partial, spec)
        partial.rename(archive)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="install-", dir=destination.parent) as directory:
        staged = Path(directory) / name
        extract_binary(archive, staged)
        actual = subprocess.check_output([str(staged), "--version"], env=env, text=True).strip()
        if actual != version:
            raise ValueError(f"Downloaded OpenCode version mismatch: {actual!r}")
        staged.rename(destination)
    print(f"OpenCode {version} installed: {destination}", flush=True)
    return destination


def configuration(workspace: Path, preset: str, base: str, contexts: dict[str, int]) -> dict:
    skills = workspace.resolve() / ".agents/skills"
    config = {
        "$schema": "https://opencode.ai/config.json", "model": f"local/{preset}",
        "small_model": f"local/{preset}", "enabled_providers": ["local"], "share": "disabled",
        "instructions": [str(skills / name / "SKILL.md") for name in skill_names()],
        "provider": {"local": {
            "npm": "@ai-sdk/openai-compatible", "name": "Package-local llama.cpp",
            "options": {"baseURL": base + "/v1"},
            "models": {key: {"name": selection(key)["name"], "limit": {
                "context": context, "output": min(4096, context // 4)}} for key, context in contexts.items()},
        }},
        "mcp": {"context7": {"type": "remote", "url": "https://mcp.context7.com/mcp",
                               "enabled": True, "timeout": 10000}},
    }
    graphify = shutil.which("graphify-mcp")
    graph = workspace.resolve() / "graphify-out/graph.json"
    if graphify and graph.is_file():
        config["mcp"]["graphify"] = {"type": "local", "command": [graphify, "--graph", str(graph)],
                                     "environment": {"GRAPHIFY_BACKEND": "none"}, "enabled": True}
    return config


def client_command(executable: Path, interface: str, preset: str, prompt: str | None = None,
                   workspace: Path | None = None) -> list[str]:
    if prompt is not None:
        return [str(executable), "run", "--model", f"local/{preset}", "--format", "json",
                "--dir", str((workspace or Path.cwd()).resolve()), "--", prompt]
    if interface == "terminal":
        return [str(executable), str((workspace or Path.cwd()).resolve()), "--model", f"local/{preset}"]
    return [str(executable), "web", "--hostname", "127.0.0.1"]


def stop(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        # Router children are descendants, not separately owned user servers.
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()


def run(invocation: list[str], server_env: dict, workspace: Path, preset: str,
        contexts: dict[str, int], host: str, port: int, interface: str = "web",
        prompt: str | None = None) -> int:
    executable = ensure()
    base = f"http://{'127.0.0.1' if host == '0.0.0.0' else host}:{port}"
    with socket.socket() as check:
        if check.connect_ex(("127.0.0.1" if host == "0.0.0.0" else host, port)) == 0:
            raise ValueError(f"Model-server port {port} is already in use; stop it or choose another port.")
    config = configuration(workspace, preset, base, contexts)
    env = environment(config)
    env["PWD"] = str(workspace.resolve())
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    with (logs / "opencode-model-server.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(invocation, cwd=ROOT, env=server_env, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=os.name != "nt")
        try:
            print(f"Loading {preset}; server log: {logs / 'opencode-model-server.log'}", flush=True)
            deadline = time.monotonic() + 300
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("Model server exited during startup; inspect opencode-model-server.log.")
                try:
                    with urllib.request.urlopen(base + "/health", timeout=1) as response:
                        if json.load(response).get("status") == "ok":
                            break
                except (OSError, ValueError):
                    pass
                time.sleep(0.25)
            else:
                raise RuntimeError("Model server startup timed out after five minutes.")
            print(f"Starting OpenCode ({'one-shot' if prompt is not None else interface}); "
                  "shared skill instructions loaded for every selected model.", flush=True)
            return subprocess.call(client_command(executable, interface, preset, prompt, workspace),
                                   cwd=workspace, env=env)
        finally:
            stop(process)
            print("Package model server stopped.", flush=True)
