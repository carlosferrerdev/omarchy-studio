import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from omarchy_studio.host import Host


class HostTests(unittest.TestCase):
    def test_missing_command(self):
        self.assertEqual(Host().run("/does-not-exist/studio").status, "missing")

    def test_no_shell_interpolation(self):
        literal = "hello; $(false) `false` with spaces"
        result = Host().run(sys.executable, "-c", "import sys; print(sys.argv[1])", literal)
        self.assertEqual(result.stdout.strip(), literal)

    def test_timeout(self):
        start = time.monotonic()
        result = Host(timeout=0.1).run(sys.executable, "-c", "import time; time.sleep(20)")
        self.assertEqual(result.status, "timeout")
        self.assertLess(time.monotonic() - start, 3)

    def test_inherited_pipe_from_descendant_is_bounded(self):
        result = Host(timeout=0.1).run(sys.executable, "-c",
            "import os,time; pid=os.fork(); time.sleep(20) if pid == 0 else None")
        self.assertEqual(result.status, "timeout")

    def test_output_limit(self):
        result = Host().run(sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'x' * (9 * 1024 * 1024))")
        self.assertEqual(result.status, "output_limit")
        self.assertEqual(result.stdout, "")

    def test_nonzero_exit_does_not_parse_partial_stdout(self):
        result = Host().run(sys.executable, "-c", "print('partial'); raise SystemExit(2)")
        self.assertEqual((result.status, result.stdout, result.returncode), ("failed", "", 2))

    def test_stderr_not_exported(self):
        host = Host()
        result = host.run(sys.executable, "-c", "import sys; print('private', file=sys.stderr)")
        self.assertNotIn("private", result.stdout)
        self.assertEqual(result.status, "ok")

    def test_budget_and_cache(self):
        host = Host(budget=0)
        self.assertEqual(host.run("anything").status, "budget_exhausted")
        host.run("anything")
        self.assertEqual(len(host.trace), 1)

    def test_read_permission_error(self):
        host = Host()
        with patch.object(Path, "open", side_effect=PermissionError):
            self.assertIsNone(host.read("/fake"))
        self.assertEqual(host.issues[0]["reason"], "PermissionError")

    def test_file_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "large"
            path.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
            self.assertIsNone(Host().read(path))

    def test_directory_permission_error(self):
        with patch.object(Path, "iterdir", side_effect=PermissionError):
            self.assertIsNone(Host().glob("/fake", "*"))

    def test_invalid_utf8_is_tolerated(self):
        result = Host().run(sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'\\xff')")
        self.assertEqual(result.stdout, "\ufffd")
