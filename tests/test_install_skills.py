"""Installer checks confined to ignored, repository-local temporary directories."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local" / "installer-tests"
SKILLS = ("github-sync", "ch584-ui-tuning", "embedded-link-debug")
PWSH = os.environ.get("AI_SKILL_PWSH") or shutil.which("pwsh")


def manifest(root):
    if not root.exists():
        return {}
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


@unittest.skipUnless(PWSH, "PowerShell 7 required; set AI_SKILL_PWSH")
class InstallTests(unittest.TestCase):
    def setUp(self):
        LOCAL.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=LOCAL)
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "codex-home"
        self.script = ROOT / "tools" / "Install-Skills.ps1"

    def invoke(self, *flags, script=None):
        return subprocess.run(
            [PWSH, "-NoProfile", "-File", str(script or self.script),
             "-CodexHome", str(self.home), *flags],
            env={**os.environ, "CODEX_HOME": str(self.home)},
            capture_output=True, encoding="utf-8", errors="replace")

    def seed(self):
        self.home.mkdir()
        (self.home / "AGENTS.md").write_text("Original rules 中文\n", encoding="utf-8")
        (self.home / "config.toml").write_text("# Existing config\n", encoding="utf-8")
        return manifest(self.home)

    def test_default_and_check_are_read_only(self):
        for flags in ((), ("-Check",)):
            result = self.invoke(*flags)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(self.home.exists())
        before = self.seed()
        result = self.invoke("-Check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(manifest(self.home), before)

    def test_install_and_repeat_are_byte_identical_preserve_rules(self):
        original = self.seed()
        first_manifest = None
        first_times = None
        for _ in range(2):
            result = self.invoke("-Install")
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in SKILLS:
                self.assertEqual(manifest(ROOT / "skills" / name), manifest(self.home / "skills" / name))
            current = manifest(self.home)
            for path, value in original.items():
                self.assertEqual(current[path], value)
            times = {p.relative_to(self.home): p.stat().st_mtime_ns for p in self.home.rglob("*") if p.is_file()}
            if first_manifest is not None:
                self.assertEqual(current, first_manifest)
                self.assertEqual(times, first_times)
            first_manifest, first_times = current, times

    def test_last_skill_conflict_preflight_prevents_partial_writes(self):
        self.seed()
        target = self.home / "skills" / SKILLS[-1]
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("User modification", encoding="utf-8")
        before = manifest(self.home)
        for flag in ("-Check", "-Install"):
            result = self.invoke(flag)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(manifest(self.home), before)
            self.assertFalse((self.home / "skills" / SKILLS[0]).exists())

    def test_extra_installed_file_is_conflict(self):
        result = self.invoke("-Install")
        self.assertEqual(result.returncode, 0, result.stderr)
        (self.home / "skills" / SKILLS[1] / ".user-file").write_text("keep", encoding="utf-8")
        before = manifest(self.home)
        self.assertNotEqual(self.invoke("-Install").returncode, 0)
        self.assertEqual(manifest(self.home), before)

    def test_missing_last_source_refuses_before_writes(self):
        fixture = Path(self.temp.name) / "fixture"
        (fixture / "tools").mkdir(parents=True)
        shutil.copy2(self.script, fixture / "tools" / self.script.name)
        for name in SKILLS[:-1]:
            shutil.copytree(ROOT / "skills" / name, fixture / "skills" / name)
        result = self.invoke("-Install", script=fixture / "tools" / self.script.name)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.home.exists())

    def test_child_script_returns_to_parent_host(self):
        command = "& $args[0] -CodexHome $args[1] -Check; Write-Output 'PARENT-CONTINUES'"
        # Use a file to avoid expression parsing of command-line path arguments.
        wrapper = Path(self.temp.name) / "parent.ps1"
        wrapper.write_text(command, encoding="utf-8")
        result = subprocess.run([PWSH, "-NoProfile", "-File", str(wrapper), str(self.script), str(self.home)],
                                capture_output=True, encoding="utf-8", errors="replace")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PARENT-CONTINUES", result.stdout)
        self.assertFalse(self.home.exists())

    def test_source_destination_overlap_refused(self):
        self.home = ROOT
        result = self.invoke("-Check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must not overlap", result.stderr)


if __name__ == "__main__":
    unittest.main()
