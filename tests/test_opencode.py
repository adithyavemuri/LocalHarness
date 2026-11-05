"""Offline managed-client installation, configuration and lifecycle checks."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import zipfile

import local_skills
import manage_models
import opencode_client


class OpenCodeTests(unittest.TestCase):
    def setUp(self):
        self.pins = json.loads((opencode_client.ROOT / "integrations/opencode-release.json").read_text())
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        root_patch = patch.object(opencode_client, "ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def test_default_module_setup_is_opencode_and_cline_remains_selectable(self):
        local_skills.install(self.root)
        self.assertTrue((self.root / ".opencode/local-models.json").is_file())
        self.assertFalse((self.root / ".clinerules").exists())
        local_skills.install(self.root, client="cline")
        self.assertTrue((self.root / ".clinerules/10-local-skills.md").is_file())
        self.assertEqual(local_skills.install(self.root), [])

    def test_launch_defaults_to_opencode_and_honors_explicit_cline(self):
        default = manage_models.launch_command("gemma4-e2b", skills_workspace=self.root)
        cline = manage_models.launch_command("gemma4-e2b", client="cline", skills_workspace=self.root)
        plain = manage_models.launch_command("gemma4-e2b", client="browser")
        self.assertEqual(default[default.index("--client") + 1], "opencode")
        self.assertEqual(cline[cline.index("--client") + 1], "cline")
        self.assertEqual(cline[cline.index("--skills-client") + 1], "cline")
        self.assertEqual(plain[plain.index("--client") + 1], "server")
        self.assertIn("--open-browser", plain)

    def test_one_shot_preserves_workspace_and_prompt_as_separate_arguments(self):
        workspace = self.root / "project with spaces"
        command = opencode_client.client_command(self.root / "opencode", "terminal", "phi4-mini",
                                                  "--a literal user prompt", workspace)
        self.assertEqual(command[command.index("--dir") + 1], str(workspace))
        self.assertEqual(command[-2:], ["--", "--a literal user prompt"])

    def test_model_switch_keeps_all_instructions_and_uses_selected_context(self):
        local_skills.install(self.root)
        for preset in ("qwen3.5-4b", "gemma4-e2b", "phi4-mini", "qwen3.8-27b"):
            with self.subTest(preset=preset), patch.object(opencode_client.shutil, "which", return_value=None):
                config = opencode_client.configuration(self.root, preset, "http://127.0.0.1:19001", {preset: 16384})
                self.assertEqual(config["model"], f"local/{preset}")
                self.assertEqual(config["small_model"], f"local/{preset}")
                self.assertEqual(config["enabled_providers"], ["local"])
                self.assertEqual(len(config["instructions"]), len(local_skills.skill_names()))
                self.assertTrue(all(Path(path).is_file() for path in config["instructions"]))
                provider = config["provider"]["local"]
                self.assertEqual(provider["options"]["baseURL"], "http://127.0.0.1:19001/v1")
                self.assertEqual(provider["models"][preset]["limit"]["context"], 16384)

    def test_graphify_needs_both_executable_and_this_workspaces_graph(self):
        local_skills.install(self.root)
        with patch.object(opencode_client.shutil, "which", return_value="/tools/graphify-mcp"):
            config = opencode_client.configuration(self.root, "phi4-mini", "http://localhost:8080", {"phi4-mini": 8192})
            self.assertNotIn("graphify", config["mcp"])
            graph = self.root / "graphify-out/graph.json"
            graph.parent.mkdir()
            graph.write_text("{}")
            config = opencode_client.configuration(self.root, "phi4-mini", "http://localhost:8080", {"phi4-mini": 8192})
            self.assertEqual(config["mcp"]["graphify"]["command"][-1], str(graph))

    def test_child_environment_keeps_managed_state_local_without_mutating_parent(self):
        before = dict(os.environ)
        env = opencode_client.environment({"model": "local/phi4-mini"})
        self.assertEqual(dict(os.environ), before)
        self.assertTrue(Path(env["XDG_CONFIG_HOME"]).is_relative_to(self.root / "runtime"))
        self.assertEqual(json.loads(env["OPENCODE_CONFIG_CONTENT"])["model"], "local/phi4-mini")
        self.assertEqual(env["OPENCODE_DISABLE_AUTOUPDATE"], "1")

    def test_dry_run_never_downloads_executes_or_creates_runtime(self):
        with patch.object(opencode_client, "release", return_value=("1.19.5", self.pins["linux_x64"])), \
             patch.object(opencode_client.subprocess, "run", side_effect=AssertionError("download")), \
             patch.object(opencode_client.subprocess, "check_output", side_effect=AssertionError("execute")):
            opencode_client.ensure(dry_run=True)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_install_verifies_archive_and_reuses_exact_version(self):
        archive = self.root / "downloads/opencode-1.19.5-opencode-linux-x64-baseline.tar.gz"
        archive.parent.mkdir()
        with tarfile.open(archive, "w:gz") as bundle:
            member = tarfile.TarInfo("bin/opencode")
            member.size = 6
            bundle.addfile(member, io.BytesIO(b"binary"))
        spec = dict(self.pins["linux_x64"], size_bytes=archive.stat().st_size,
                    sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
        with patch.object(opencode_client, "release", return_value=("1.19.5", spec)), \
             patch.object(opencode_client.platform, "system", return_value="Linux"), \
             patch.object(opencode_client.subprocess, "run", side_effect=AssertionError("download")), \
             patch.object(opencode_client.subprocess, "check_output", return_value="1.19.5\n"):
            executable = opencode_client.ensure()
            self.assertEqual(executable.read_bytes(), b"binary")
            self.assertEqual(opencode_client.ensure(), executable)
        archive.write_bytes(b"modified")
        # Check integrity rejection before extraction, independently of the installed binary.
        with self.assertRaises(ValueError):
            opencode_client.verify_file(archive, spec)

    def test_archive_links_cannot_be_installed_as_the_executable(self):
        archive = self.root / "unsafe.tar.gz"
        with tarfile.open(archive, "w:gz") as bundle:
            member = tarfile.TarInfo("opencode")
            member.type = tarfile.SYMTYPE
            member.linkname = "/outside"
            bundle.addfile(member)
        with self.assertRaisesRegex(ValueError, "regular opencode"):
            opencode_client.extract_binary(archive, self.root / "executable")
        self.assertFalse((self.root / "executable").exists())

    def test_windows_zip_copies_only_fixed_executable_destination(self):
        archive = self.root / "windows.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr("nested/opencode.exe", b"windows binary")
            bundle.writestr("../unrelated", b"ignored")
        destination = self.root / "opencode.exe"
        opencode_client.extract_binary(archive, destination)
        self.assertEqual(destination.read_bytes(), b"windows binary")
        self.assertEqual({path.name for path in self.root.iterdir()}, {"windows.zip", "opencode.exe"})

    def test_client_failure_still_stops_its_model_server(self):
        local_skills.install(self.root)
        process = MagicMock()
        process.poll.return_value = None
        port = MagicMock()
        port.__enter__.return_value.connect_ex.return_value = 1
        with patch.object(opencode_client, "ensure", return_value=self.root / "opencode"), \
             patch.object(opencode_client.socket, "socket", return_value=port), \
             patch.object(opencode_client.urllib.request, "urlopen", return_value=io.BytesIO(b'{"status":"ok"}')), \
             patch.object(opencode_client.subprocess, "Popen", return_value=process), \
             patch.object(opencode_client.subprocess, "call", return_value=7) as client, \
             patch.object(opencode_client, "stop") as stop:
            result = opencode_client.run(["fake-server"], {}, self.root, "phi4-mini", {"phi4-mini": 8192},
                                         "127.0.0.1", 19001, prompt="hello")
        self.assertEqual(result, 7)
        self.assertEqual(client.call_args.kwargs["env"]["PWD"], str(self.root))
        stop.assert_called_once_with(process)


if __name__ == "__main__":
    unittest.main()
