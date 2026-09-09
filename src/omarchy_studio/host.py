"""All OS access lives here; probes accept an injectable host.

Commands never use a shell, stdin, privilege escalation or network clients.
Output and execution time are bounded, including descendants on timeout.
"""
from __future__ import annotations

import logging
import os
import platform
import resource
import selectors
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

LOG = logging.getLogger("omarchy_studio")


@dataclass(frozen=True)
class CommandResult:
    status: str
    stdout: str = ""
    returncode: int | None = None


class Host:
    def __init__(self, *, timeout: float = 2.0, budget: float = 20.0):
        self.env = dict(os.environ)
        self.home = Path.home()
        self.uid = os.getuid()
        self.platform = platform.system()
        self.machine = platform.machine()
        self.kernel = platform.release()
        self.timeout = timeout
        self.deadline = time.monotonic() + budget
        self.trace: list[dict] = []
        self.issues: list[dict] = []
        self._commands: dict[tuple, CommandResult] = {}

    def issue(self, source: str, reason: str):
        item = {"source": source, "reason": reason}
        if item not in self.issues:
            self.issues.append(item)
        LOG.debug("%s: %s", source, reason)

    def read(self, path: str | Path) -> str | None:
        try:
            with Path(path).open("rb") as stream:
                raw = stream.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                self.issue(str(path), "output_limit")
                return None
            return raw.decode("utf-8", errors="replace").strip()
        except FileNotFoundError:
            return None
        except OSError as exc:
            self.issue(str(path), type(exc).__name__)
            return None

    def exists(self, path: str | Path) -> bool | None:
        try:
            Path(path).stat()
            return True
        except FileNotFoundError:
            return False
        except OSError as exc:
            self.issue(str(path), type(exc).__name__)
            return None

    def glob(self, path: str | Path, pattern: str) -> list[str] | None:
        # Callers use a single directory plus a basename pattern. Explicitly
        # listing it avoids Path.glob silently hiding permission errors.
        import fnmatch
        try:
            return sorted(str(p) for p in Path(path).iterdir()
                          if fnmatch.fnmatchcase(p.name, pattern))
        except FileNotFoundError:
            return []
        except OSError as exc:
            self.issue(str(path), type(exc).__name__)
            return None

    def resolve(self, path: str | Path) -> str | None:
        try:
            return str(Path(path).resolve(strict=True))
        except (OSError, RuntimeError):
            return None

    def limits(self) -> dict:
        result = {}
        for name in ("RTPRIO", "MEMLOCK", "RTTIME"):
            kind = getattr(resource, "RLIMIT_" + name, None)
            if kind is not None:
                soft, hard = resource.getrlimit(kind)
                result[name.lower()] = {
                    "soft": "unlimited" if soft == resource.RLIM_INFINITY else soft,
                    "hard": "unlimited" if hard == resource.RLIM_INFINITY else hard,
                }
        return result

    def run(self, *argv: str) -> CommandResult:
        if argv in self._commands:
            return self._commands[argv]
        remaining = self.deadline - time.monotonic()
        result = (CommandResult("budget_exhausted") if remaining <= 0
                  else self._execute(argv, min(self.timeout, remaining)))
        self._commands[argv] = result
        self.trace.append({"argv": list(argv), "status": result.status,
                           "returncode": result.returncode})
        LOG.debug("command %s: %s (rc=%s)", argv, result.status, result.returncode)
        if result.status not in ("ok", "missing"):
            self.issue(" ".join(argv), result.status)
        return result

    def _execute(self, argv: tuple[str, ...], timeout: float) -> CommandResult:
        env = {**self.env, "LC_ALL": "C", "LANG": "C", "NO_COLOR": "1"}
        try:
            proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    env=env, start_new_session=True)
        except FileNotFoundError:
            return CommandResult("missing")
        except OSError:
            return CommandResult("unavailable")
        deadline = time.monotonic() + timeout
        output = bytearray()
        total = 0
        status = "ok"
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(proc.stdout, selectors.EVENT_READ)
                selector.register(proc.stderr, selectors.EVENT_READ)
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        status = "timeout"
                        break
                    for key, _ in selector.select(remaining):
                        chunk = os.read(key.fileobj.fileno(), 65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        total += len(chunk)
                        if total > 8 * 1024 * 1024:
                            status = "output_limit"
                            break
                        if key.fileobj is proc.stdout:
                            output.extend(chunk)
                    if status != "ok":
                        break
                if status == "ok":
                    try:
                        proc.wait(timeout=max(0.001, deadline - time.monotonic()))
                    except subprocess.TimeoutExpired:
                        status = "timeout"
        finally:
            # Also clean up a still-running descendant holding a pipe open.
            if status != "ok" or proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            proc.wait()
            proc.stdout.close()
            proc.stderr.close()
        if status == "ok" and proc.returncode != 0:
            status = "failed"
        return CommandResult(status, output.decode("utf-8", errors="replace")
                             if status == "ok" else "", proc.returncode)


def xdg_dir(host: Host, kind: str) -> Path:
    defaults = {"config": ".config", "data": ".local/share",
                "state": ".local/state", "cache": ".cache"}
    override = host.env.get(f"XDG_{kind.upper()}_HOME", "")
    base = Path(override) if override and Path(override).is_absolute() else host.home / defaults[kind]
    return base / "omarchy-studio"
