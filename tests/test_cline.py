"""Offline workspace installation checks; never modify IDE/global settings."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import local_skills
import model_config
import run_server
import setup_cline


class ClineInstallTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)

    def test_dry_run_writes_nothing(self):
        paths = setup_cline.install(self.workspace, dry_run=True)
        self.assertTrue(paths)
        self.assertEqual(list(self.workspace.iterdir()), [])

    def test_install_is_complete_preserves_unrelated_files_and_is_repeatable(self):
        existing = self.workspace / "AGENTS.md"
        existing.write_text("Existing workspace instructions\n")
        paths = setup_cline.install(self.workspace)
        for pack in (local_skills.PACK, local_skills.CLINE_PACK):
            for source in pack.rglob("*"):
                if source.is_file():
                    self.assertEqual((self.workspace / source.relative_to(pack)).read_bytes(),
                                     source.read_bytes())
        self.assertTrue(paths)
        self.assertEqual(setup_cline.install(self.workspace), [])
        self.assertEqual(existing.read_text(), "Existing workspace instructions\n")

    def test_conflict_prevents_all_new_files(self):
        destination = self.workspace / ".clinerules/10-local-skills.md"
        destination.parent.mkdir()
        destination.write_text("User's existing rule\n")
        with self.assertRaisesRegex(ValueError, "Existing file differs"):
            setup_cline.install(self.workspace)
        self.assertEqual(destination.read_text(), "User's existing rule\n")
        self.assertFalse((self.workspace / ".agents").exists())
        self.assertFalse((self.workspace / ".cline").exists())

    def test_legacy_clinerules_file_requires_manual_merge(self):
        destination = self.workspace / ".clinerules"
        destination.write_text("Existing legacy rules\n")
        with self.assertRaisesRegex(ValueError, "Expected a directory"):
            setup_cline.install(self.workspace)
        self.assertFalse((self.workspace / ".agents").exists())
        self.assertEqual(destination.read_text(), "Existing legacy rules\n")

    def test_symlink_cannot_redirect_install_outside_workspace(self):
        with tempfile.TemporaryDirectory() as outside:
            (self.workspace / ".agents").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                setup_cline.install(self.workspace)
            self.assertEqual(list(Path(outside).iterdir()), [])
            self.assertFalse((self.workspace / ".cline").exists())

    def test_generic_client_installs_skills_without_cline_configuration(self):
        existing = self.workspace / ".clinerules"
        existing.write_text("Keep these client rules\n")
        local_skills.install(self.workspace, client="generic")
        self.assertEqual(existing.read_text(), "Keep these client rules\n")
        self.assertFalse((self.workspace / ".cline").exists())
        installed = self.workspace / ".agents/skills"
        self.assertEqual({path.name for path in installed.iterdir()}, set(local_skills.skill_names()))

    def test_requested_instructions_load_all_skills_before_model_selection(self):
        names = list(local_skills.skill_names())
        text = local_skills.instructions(names)
        for name in names:
            self.assertIn(local_skills.read_skill(name), text)
        setup_cline.install(self.workspace)
        self.assertTrue((self.workspace / ".clinerules/10-local-skills.md").is_file())
        self.assertFalse((self.workspace / ".opencode").exists())

    def test_unknown_skill_cannot_become_a_file_path(self):
        for name in ("../README.md", "not-a-skill", "/etc/passwd"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "Unknown skill"):
                local_skills.read_skill(name)

    def test_every_preset_uses_same_workspace_module_before_launch(self):
        def launch(*args, **kwargs):
            self.assertTrue((self.workspace / ".agents/skills/context7/SKILL.md").is_file())
            self.assertTrue((self.workspace / ".clinerules/10-local-skills.md").is_file())
            return 0

        with patch.object(run_server, "command", return_value=["fake-server"]), \
             patch.object(run_server, "server_environment", return_value={}), \
             patch.object(run_server.subprocess, "call", side_effect=launch), \
             contextlib.redirect_stdout(io.StringIO()):
            for preset in model_config.catalog()["models"]:
                with self.subTest(preset=preset), patch.object(sys, "argv", [
                    "run_server.py", "--preset", preset, "--context", "4096",
                    "--skills-workspace", str(self.workspace), "--skills-client", "cline",
                ]), self.assertRaises(SystemExit) as stopped:
                    run_server.main()
                self.assertEqual(stopped.exception.code, 0)
        self.assertEqual(local_skills.install(self.workspace, client="cline"), [])

    def test_launcher_dry_run_plans_skills_without_writing_or_starting(self):
        with patch.object(sys, "argv", ["run_server.py", "--context", "4096", "--dry-run",
                                       "--skills-workspace", str(self.workspace)]), \
             patch.object(run_server, "command", return_value=["fake-server"]), \
             patch.object(run_server.subprocess, "call") as called, \
             contextlib.redirect_stdout(io.StringIO()):
            run_server.main()
        called.assert_not_called()
        self.assertEqual(list(self.workspace.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
