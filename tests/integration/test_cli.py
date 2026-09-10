"""Real Python processes and files; no audio daemon or hardware required."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class CliIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="studio-test-")
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.env = {"HOME": str(self.home), "PATH": str(self.home / "empty-path"), "LC_ALL": "C"}

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "bin/omarchy-studio"), *args],
                              env=self.env, capture_output=True, text=True, timeout=30)

    def test_json_stdout_and_verbose_stderr(self):
        result = self.run_cli("doctor", "--json", "--verbose")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["plugin_version"], "0.1.0")
        self.assertEqual(len(report["readiness"]["checks"]), 10)
        for default in report["probes"]["pipewire"]["default_nodes"].values():
            self.assertEqual(default["status"], "UNKNOWN")
            self.assertIsNone(default["node_id"])
        self.assertIn("DEBUG", result.stderr)

    def test_strict_exit_status_keeps_valid_json(self):
        result = self.run_cli("doctor", "--json", "--strict")
        self.assertEqual(result.returncode, 1)
        self.assertNotEqual(json.loads(result.stdout)["readiness"]["status"], "FOUNDATION_CHECKS_PASSED")

    def test_default_has_no_persistent_writes(self):
        before = sorted(self.home.rglob("*"))
        result = self.run_cli("doctor")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, sorted(self.home.rglob("*")))
        self.assertIn("DEFAULT AUDIO", result.stdout)
        self.assertIn("Input: UNKNOWN", result.stdout)
        self.assertIn("Output: UNKNOWN", result.stdout)

    def test_unsupported_mutation_command(self):
        result = self.run_cli("setup", "--dry-run")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")

    def test_checkout_with_spaces_and_metacharacters(self):
        checkout = self.home / "studio spaces $(false)"
        shutil.copytree(ROOT / "src", checkout / "src")
        (checkout / "bin").mkdir()
        shutil.copy(ROOT / "bin/omarchy-studio", checkout / "bin/omarchy-studio")
        result = subprocess.run([sys.executable, str(checkout / "bin/omarchy-studio"), "--version"],
                                env=self.env, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.stdout.strip(), "0.1.0")

    def test_terminal_wrapper_preserves_path_arguments(self):
        checkout = self.home / "wrapper with spaces $(false)"
        checkout.mkdir()
        shutil.copy(ROOT / "bin/studio-doctor-terminal", checkout / "studio-doctor-terminal")
        fake = checkout / "omarchy-studio"
        fake.write_text('#!/bin/bash\nprintf "%s\\n" "$1"\nexit 7\n')
        fake.chmod(0o700)
        result = subprocess.run(["/bin/bash", str(checkout / "studio-doctor-terminal")],
                                env={**self.env, "PATH": "/usr/bin:/bin"},
                                capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=5)
        self.assertEqual(result.stdout, "doctor\n")
        self.assertEqual(result.returncode, 7)

    def test_official_manifest_validator(self):
        upstream = os.environ.get("OMARCHY_UPSTREAM")
        if not upstream:
            self.skipTest("Set OMARCHY_UPSTREAM to the reviewed Omarchy source checkout")
        script = Path(upstream) / "bin/omarchy-plugin-validate"
        result = subprocess.run(["bash", str(script), str(ROOT)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_versions_agree(self):
        import tomllib
        manifest = json.loads((ROOT / "manifest.json").read_text())
        metadata = tomllib.loads((ROOT / "pyproject.toml").read_text())
        self.assertEqual(manifest["version"], metadata["project"]["version"])
        self.assertEqual(self.run_cli("--version").stdout.strip(), manifest["version"])
