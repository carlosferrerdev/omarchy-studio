import math
import re
from pathlib import Path

from .. import __version__
from .common import fields, integer


class SystemProbe:
    def __init__(self, host, packages):
        self.host, self.packages = host, packages

    def collect(self):
        h = self.host
        candidates = [h.env.get("OMARCHY_PATH", "/usr/share/omarchy"),
                      "/usr/share/omarchy", str(h.home / ".local/share/omarchy")]
        roots = [p for p in dict.fromkeys(candidates) if Path(p).is_absolute()
                 and h.exists(Path(p) / "bin/omarchy-version") is True]
        package = next((self.packages[p] for p in ("omarchy-dev", "omarchy")
                        if self.packages[p]["installed"]), None)
        detected = bool(package or roots)
        release = package["version"] if package else None
        if detected and release is None:
            result = h.run("omarchy-version")
            release = (result.stdout.strip() or None) if result.status == "ok" else None
        # Upstream's source-tree `version` file can be stale (4.0.0.alpha in
        # the researched release). Do not treat that file as installed version.
        matched = re.fullmatch(r"(?:\d+:)?(\d+)\.(\d+)\.(\d+)(?:-\d+(?:\.\d+)*)?", release or "")
        release_tuple = tuple(map(int, matched.groups())) if matched else None
        if not detected:
            compatibility = "UNSUPPORTED"
        elif release_tuple and release_tuple[0] < 4:
            compatibility = "UNSUPPORTED"
        elif release_tuple == (4, 0, 3) and h.machine == "x86_64" and not self.packages["omarchy-dev"]["installed"]:
            compatibility = "TARGET_VERSION"
        else:
            compatibility = "UNKNOWN"
        os_release = fields(h.read("/etc/os-release"), "=")
        return {"omarchy_detected": detected, "omarchy_version": release,
                "omarchy_roots": roots, "integration_compatibility": compatibility,
                "linux": h.platform == "Linux", "architecture": h.machine,
                "kernel": h.kernel, "os_id": os_release.get("ID", "").strip('"') or None,
                "session_type": h.env.get("XDG_SESSION_TYPE"),
                "desktop": h.env.get("XDG_CURRENT_DESKTOP"), "root_user": h.uid == 0,
                "plugin_version": __version__,
                "source": "pacman -Q; Omarchy markers; uname; /etc/os-release"}


class CpuProbe:
    def __init__(self, host):
        self.host = host

    def collect(self):
        h = self.host
        raw = h.read("/proc/cpuinfo")
        blocks = [fields(block) for block in (raw or "").split("\n\n") if block.strip()]
        cpus = [c for c in blocks if integer(c.get("processor")) is not None]
        models = sorted({c.get("model name") or c.get("Hardware") for c in blocks
                         if c.get("model name") or c.get("Hardware")})
        pairs = {(c["physical id"], c["core id"]) for c in cpus
                 if "physical id" in c and "core id" in c}
        policies = []
        reported_frequencies = []
        for cpu in cpus:
            try:
                mhz = float(cpu.get("cpu MHz", ""))
            except (ValueError, OverflowError):
                continue
            if math.isfinite(mhz) and mhz > 0:
                reported_frequencies.append({"logical_cpu": int(cpu["processor"]), "mhz": mhz})
        for path in h.glob("/sys/devices/system/cpu/cpufreq", "policy[0-9]*") or []:
            policies.append({"policy": Path(path).name,
                             "driver": h.read(path + "/scaling_driver"),
                             "governor": h.read(path + "/scaling_governor"),
                             "frequency_khz": integer(h.read(path + "/scaling_cur_freq"), minimum=1),
                             "min_khz": integer(h.read(path + "/scaling_min_freq"), minimum=1),
                             "max_khz": integer(h.read(path + "/scaling_max_freq"), minimum=1)})
        return {"models": models, "architecture": h.machine,
                "logical_cpus": len(cpus) or None,
                "physical_cores": len(pairs) if pairs and all("physical id" in c and "core id" in c for c in cpus) else None,
                "frequency_policies": policies,
                "cpuinfo_reported_frequencies": reported_frequencies,
                "source": "/proc/cpuinfo; /sys/devices/system/cpu/cpufreq"}


class MemoryProbe:
    def __init__(self, host):
        self.host = host

    def collect(self):
        values = fields(self.host.read("/proc/meminfo"))
        def kib(key):
            match = re.fullmatch(r"(\d+)\s+kB", values.get(key, ""))
            return int(match[1]) * 1024 if match else None
        total, available = kib("MemTotal"), kib("MemAvailable")
        ratio = available / total if total and available is not None and available <= total else None
        return {"total_bytes": total, "available_bytes": available,
                "available_fraction": ratio, "swap_total_bytes": kib("SwapTotal"),
                "swap_free_bytes": kib("SwapFree"), "source": "/proc/meminfo"}
