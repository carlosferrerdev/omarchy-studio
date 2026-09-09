import json

from .common import integer, mapping, sequence, service, string, version


class AudioEngineProbe:
    def __init__(self, host, packages):
        self.host, self.packages = host, packages

    def collect(self):
        return {"packages": self.packages,
                "versions": {name: version(self.host, name) for name in ("pipewire", "wireplumber")},
                "services": {name: service(self.host, name + ".service")
                             for name in ("pipewire", "wireplumber", "pipewire-pulse")},
                "alsa_version": self.host.read("/proc/asound/version"),
                "alsa_present": self.host.exists("/proc/asound")}


class PipeWireProbe:
    def __init__(self, host):
        self.host = host

    def collect(self):
        result = self.host.run("pw-dump", "--no-colors")
        data = {"status": "UNKNOWN", "server_reachable": None, "server_version": None,
                "settings": {}, "devices": [], "nodes": [], "midi_ports": [],
                "wireplumber_client": None, "snapshot_complete": False,
                "observed_sample_rate": None, "observed_quantum": None, "xruns": None,
                "source": "pw-dump --no-colors",
                "measurement_note": "Settings are defaults/overrides, not observed graph timing. "
                                    "XRUNs and actual graph timing require a separate measurement."}
        if result.status != "ok":
            data["command_status"] = result.status
            return data
        try:
            objects = json.loads(result.stdout)
        except (ValueError, RecursionError):
            objects = None
        if not isinstance(objects, list) or not all(isinstance(o, dict) and isinstance(o.get("type"), str) for o in objects):
            self.host.issue("pw-dump", "unexpected_output")
            return data
        complete = True
        for obj in objects:
            info = mapping(obj.get("info"))
            props = mapping(info.get("props")) or mapping(obj.get("props"))
            kind = obj["type"].removeprefix("PipeWire:Interface:")
            if kind in ("Node", "Device", "Client") and not isinstance(info.get("props"), dict):
                complete = False
            if kind == "Core":
                data["server_reachable"] = True
                data["server_version"] = string(info.get("version"))
            elif kind == "Metadata" and props.get("metadata.name") == "settings":
                for entry in sequence(obj.get("metadata")):
                    entry = mapping(entry)
                    key = entry.get("key")
                    # Capture only known clock keys; no arbitrary metadata/client data.
                    if entry.get("subject") == 0 and key in (
                        "clock.rate", "clock.quantum", "clock.min-quantum", "clock.max-quantum",
                        "clock.force-rate", "clock.force-quantum", "clock.allowed-rates"):
                        value = entry.get("value")
                        if isinstance(value, str):
                            try:
                                value = json.loads(value)
                            except (ValueError, RecursionError):
                                value = None
                        if key == "clock.allowed-rates":
                            data["settings"][key] = [n for v in sequence(value) if (n := integer(v, minimum=1))]
                        else:
                            data["settings"][key] = integer(value)
            elif kind == "Client" and props.get("application.name") == "WirePlumber":
                data["wireplumber_client"] = True
            elif kind in ("Node", "Device"):
                target = "nodes" if kind == "Node" else "devices"
                data[target].append({"id": integer(obj.get("id")),
                                     "description": string(props.get("node.description" if kind == "Node" else "device.description")),
                                     "media_class": string(props.get("media.class")),
                                     "state": string(info.get("state")),
                                     "alsa_card": integer(props.get("api.alsa.pcm.card", props.get("api.alsa.card", props.get("alsa.card")))),
                                     "device_id": integer(props.get("device.id")),
                                     "api": string(props.get("device.api")),
                                     "audio_channels": integer(props.get("audio.channels"), minimum=1),
                                     "audio_rate": integer(props.get("audio.rate"), minimum=1)})
            elif kind == "Port":
                # port.control alone is not evidence of MIDI.
                if "midi" in (string(props.get("format.dsp")) or "").lower():
                    data["midi_ports"].append({"id": integer(obj.get("id")),
                        "node_id": integer(props.get("node.id")), "name": string(props.get("port.name")),
                        "direction": string(info.get("direction")) or string(props.get("port.direction")),
                        "format": string(props.get("format.dsp"))})
        if data["server_reachable"]:
            data["status"] = "OK" if complete else "PARTIAL"
            data["snapshot_complete"] = complete
            if complete and data["wireplumber_client"] is None:
                data["wireplumber_client"] = False
        else:
            self.host.issue("pw-dump", "core_not_visible")
        if not complete:
            self.host.issue("pw-dump", "incomplete_object_information")
        return data
