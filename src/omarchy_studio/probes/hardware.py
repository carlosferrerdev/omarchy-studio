import re
from pathlib import Path

from .common import fields, integer


class UsbAudioProbe:
    """Resolve USB identity from the sound card's sysfs ancestry, never lsusb."""

    def __init__(self, host):
        self.host = host

    def identify(self, card_path):
        resolved = self.host.resolve(card_path + "/device")
        if not resolved:
            return {}
        device = Path(resolved)
        for parent in [device, *device.parents]:
            vendor_id = self.host.read(parent / "idVendor")
            product_id = self.host.read(parent / "idProduct")
            if (re.fullmatch(r"[0-9a-fA-F]{4}", vendor_id or "")
                    and re.fullmatch(r"[0-9a-fA-F]{4}", product_id or "")):
                return {"transport": "USB", "vendor": self.host.read(parent / "manufacturer"),
                        "product": self.host.read(parent / "product"),
                        "usb_vendor_id": vendor_id.lower(), "usb_product_id": product_id.lower()}
        subsystem = self.host.resolve(device / "subsystem")
        return {"transport": "PCI"} if subsystem and Path(subsystem).name == "pci" else {}


class AlsaProbe:
    def __init__(self, host):
        self.host = host

    def collect(self):
        h = self.host
        available = h.exists("/proc/asound")
        raw_cards = h.read("/proc/asound/cards")
        names = {}
        for line in (raw_cards or "").splitlines():
            match = re.match(r"^\s*(\d+)\s+\[([^]]+)\]\s*:\s*[^-]+-\s*(.+)$", line)
            if match:
                names[int(match[1])] = match[3].strip()
        modules = {}
        for line in (h.read("/proc/asound/modules") or "").splitlines():
            parts = line.split()
            if len(parts) == 2 and integer(parts[0]) is not None:
                modules[int(parts[0])] = parts[1]
        sys_cards = h.glob("/sys/class/sound", "card[0-9]*")
        proc_cards = h.glob("/proc/asound", "card[0-9]*")
        indexes = set(names)
        for item in (sys_cards or []) + (proc_cards or []):
            match = re.fullmatch(r"card(\d+)", Path(item).name)
            if match:
                indexes.add(int(match[1]))
        cards = []
        scan_complete = sys_cards is not None and proc_cards is not None
        for index in sorted(indexes):
            sys_card = f"/sys/class/sound/card{index}"
            proc_card = f"/proc/asound/card{index}"
            usb = UsbAudioProbe(h).identify(sys_card)
            driver_link = h.resolve(sys_card + "/device/driver")
            driver = modules.get(index) or (Path(driver_link).name if driver_link else None)
            device_path = h.resolve(sys_card + "/device")
            physical = ("/virtual/" not in device_path and driver not in ("snd_aloop", "snd_dummy")) if device_path else None
            pcms = h.glob(proc_card, "pcm[0-9]*")
            if pcms is None or h.exists(proc_card) is not True:
                scan_complete = False
            endpoints = []
            active_params = []
            for pcm in pcms or []:
                match = re.fullmatch(r"pcm(\d+)([pc])", Path(pcm).name)
                if not match:
                    continue
                direction = "playback" if match[2] == "p" else "capture"
                endpoints.append({"device": int(match[1]), "direction": direction})
                for sub in h.glob(pcm, "sub[0-9]*") or []:
                    params = fields(h.read(sub + "/hw_params"))
                    if params:
                        active_params.append({"device": int(match[1]), "direction": direction,
                            "subdevice": Path(sub).name, "format": params.get("format"),
                            "channels": integer(params.get("channels"), minimum=1),
                            "rate": integer(params.get("rate", "").split(" ")[0], minimum=1),
                            "period_size": integer(params.get("period_size"), minimum=1),
                            "buffer_size": integer(params.get("buffer_size"), minimum=1)})
            cards.append({"alsa_card": index, "name": usb.get("product") or names.get(index) or h.read(proc_card + "/id"),
                          "vendor": usb.get("vendor"), "transport": usb.get("transport"),
                          "usb_vendor_id": usb.get("usb_vendor_id"), "usb_product_id": usb.get("usb_product_id"),
                          "driver": driver, "status": "detected", "support_status": "UNKNOWN",
                          "physical": physical,
                          "inputs": None, "outputs": None, "sample_rates": None, "bit_depths": None,
                          "capabilities": None, "pcm_endpoints": endpoints,
                          "active_hw_params": active_params,
                          "source": "ALSA procfs + sound card sysfs ancestry"})
        return {"alsa_present": available, "scan_complete": scan_complete,
                "cards": cards, "source": "/proc/asound; /sys/class/sound"}


class HardwareProbe:
    def __init__(self, host):
        self.host = host

    def collect(self, pipewire):
        data = AlsaProbe(self.host).collect()
        device_cards = {d["id"]: d["alsa_card"] for d in pipewire["devices"]
                        if d["id"] is not None and d["alsa_card"] is not None}
        for card in data["cards"]:
            card["pipewire_node_ids"] = [node["id"] for node in pipewire["nodes"]
                if (node["alsa_card"] if node["alsa_card"] is not None
                    else device_cards.get(node["device_id"])) == card["alsa_card"]]
        return data


class MidiProbe:
    def __init__(self, host):
        self.host = host

    def collect(self, pipewire):
        raw_devices = self.host.glob("/sys/class/sound", "midiC*D*")
        devices = []
        for path in raw_devices or []:
            match = re.fullmatch(r"midiC(\d+)D(\d+)", Path(path).name)
            if match:
                devices.append({"alsa_card": int(match[1]), "device": int(match[2]),
                                "id": Path(path).name})
        clients_raw = self.host.read("/proc/asound/seq/clients")
        clients = []
        current = None
        for line in (clients_raw or "").splitlines():
            client = re.match(r'^Client\s+(\d+)\s*:\s*"(.*)"\s*\[([^]]+)\]', line.strip())
            port = re.match(r'^Port\s+(\d+)\s*:\s*"(.*)"\s*\(([^)]*)\)', line.strip())
            if client:
                current = {"id": int(client[1]), "name": client[2], "type": client[3], "ports": []}
                clients.append(current)
            elif port and current is not None:
                current["ports"].append({"id": int(port[1]), "name": port[2], "flags": port[3]})
        if clients_raw and not clients and "Client" in clients_raw:
            self.host.issue("/proc/asound/seq/clients", "unexpected_output")
        return {"raw_devices": devices, "raw_scan_complete": raw_devices is not None,
                "sequencer_available": self.host.exists("/proc/asound/seq"),
                "sequencer_clients": clients, "sequencer_readable": clients_raw is not None,
                "pipewire_ports": pipewire["midi_ports"],
                "pipewire_midi_nodes": [n for n in pipewire["nodes"] if "midi" in (n["media_class"] or "").lower()],
                "source": "sysfs raw MIDI; /proc/asound/seq/clients; pw-dump"}
