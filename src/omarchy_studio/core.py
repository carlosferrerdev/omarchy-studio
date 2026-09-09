from datetime import datetime, timezone
from pathlib import Path

from . import PLUGIN_ID, __version__
from .host import Host, xdg_dir
from .probes.common import PackageProbe
from .probes.system import SystemProbe, CpuProbe, MemoryProbe
from .probes.pipewire import AudioEngineProbe, PipeWireProbe
from .probes.hardware import HardwareProbe, MidiProbe
from .probes.realtime import RealtimeProbe
from .readiness import evaluate, advisories


def configuration_inventory(host):
    paths = []
    # User config obeys XDG. Inventory names only; do not claim to implement
    # SPA-JSON merging or to infer effective runtime configuration from files.
    user_config = xdg_dir(host, "config").parent
    for component, configs in (("pipewire", ("pipewire.conf", "pipewire-pulse.conf", "jack.conf", "client.conf")),
                               ("wireplumber", ("wireplumber.conf",))):
        for base in (Path("/usr/share") / component, Path("/etc") / component, user_config / component):
            for config in configs:
                if host.exists(base / config):
                    paths.append(str(base / config))
                paths.extend(host.glob(base / (config + ".d"), "*.conf") or [])
    return {"files": sorted(set(paths)), "effective_configuration": None,
            "note": "File inventory only. Runtime settings are reported by the PipeWire probe."}


def diagnose(host=None):
    host = host or Host()
    packages = PackageProbe(host).collect()
    probes = {"system": SystemProbe(host, packages).collect(),
              "cpu": CpuProbe(host).collect(), "memory": MemoryProbe(host).collect(),
              "audio_engine": AudioEngineProbe(host, packages).collect(),
              "pipewire": PipeWireProbe(host).collect()}
    probes["pipewire"]["custom_remote"] = any(host.env.get(k) for k in ("PIPEWIRE_REMOTE", "PIPEWIRE_RUNTIME_DIR"))
    probes["hardware"] = HardwareProbe(host).collect(probes["pipewire"])
    probes["midi"] = MidiProbe(host).collect(probes["pipewire"])
    probes["realtime"] = RealtimeProbe(host).collect(probes["audio_engine"])
    probes["configuration"] = configuration_inventory(host)
    report = {"schema_version": 1, "plugin_id": PLUGIN_ID, "plugin_version": __version__,
              "collected_at": datetime.now(timezone.utc).isoformat(),
              "probes": probes, "readiness": evaluate(probes), "advisories": advisories(probes),
              "issues": host.issues, "commands": host.trace,
              "privacy": "No upload, serial-number collection, recording or persistent logging. "
                         "Review device and port labels before sharing this report."}
    # Keep user home out of path fields and command provenance in shared reports.
    def redact(value):
        if isinstance(value, str):
            return value.replace(str(host.home) + "/", "$HOME/")
        if isinstance(value, list):
            return [redact(v) for v in value]
        if isinstance(value, dict):
            return {k: redact(v) for k, v in value.items()}
        return value
    return redact(report)
