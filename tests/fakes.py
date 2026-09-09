import fnmatch
import json
from pathlib import Path

from omarchy_studio.host import Host, CommandResult
from omarchy_studio.probes.common import PackageProbe


class FakeHost(Host):
    def __init__(self):
        self.env = {"XDG_SESSION_TYPE": "wayland", "XDG_CURRENT_DESKTOP": "Hyprland"}
        self.home = Path("/home/test")
        self.uid = 1000
        self.platform = "Linux"
        self.machine = "x86_64"
        self.kernel = "6.18.0-test"
        self.trace, self.issues = [], []
        self.files, self.links, self.commands = {}, {}, {}
        self.denied = set()

    def read(self, path):
        if str(path) in self.denied:
            self.issue(str(path), "PermissionError")
            return None
        return self.files.get(str(path))

    def exists(self, path):
        key = str(path)
        if key in self.denied:
            return None
        return key in self.files or key in self.links or any(p.startswith(key + "/") for p in self.files)

    def glob(self, path, pattern):
        key = str(path)
        if key in self.denied:
            return None
        children = {key + "/" + p[len(key) + 1:].split("/")[0]
                    for p in list(self.files) + list(self.links) if p.startswith(key + "/")}
        return sorted(p for p in children if fnmatch.fnmatchcase(Path(p).name, pattern))

    def resolve(self, path):
        return self.links.get(str(path))

    def limits(self):
        return {"rtprio": {"soft": 0, "hard": 0}, "memlock": {"soft": 8388608, "hard": 8388608},
                "rttime": {"soft": "unlimited", "hard": "unlimited"}}

    def run(self, *argv):
        result = self.commands.get(argv, CommandResult("missing"))
        self.trace.append({"argv": list(argv), "status": result.status, "returncode": result.returncode})
        if result.status not in ("ok", "missing"):
            self.issue(" ".join(argv), result.status)
        return result

    def result(self, argv, output):
        self.commands[tuple(argv)] = CommandResult("ok", output, 0)


def scheduler_stat(tid, policy, priority, name="data-loop.0"):
    rest = ["0"] * 39
    rest[0] = "S"
    rest[37], rest[38] = str(priority), str(policy)
    return f"{tid} ({name}) " + " ".join(rest)


def set_service(host, name, state="active", *, user=True, pid=0):
    argv = ["systemctl"] + (["--user"] if user else [])
    argv += ["show", name + ".service", "--no-pager", "--property=LoadState,ActiveState,SubState,MainPID"]
    host.result(argv, f"LoadState=loaded\nActiveState={state}\nSubState=running\nMainPID={pid}")


def session():
    h = FakeHost()
    h.result(["pacman", "-Q"], "\n".join(f"{name} " + ("4.0.3-1" if name == "omarchy" else "1.0.0-1")
                                               for name in PackageProbe.NAMES if name != "omarchy-dev"))
    h.result(["pipewire", "--version"], "pipewire\nCompiled with libpipewire 1.6.8\nLinked with libpipewire 1.6.8")
    h.result(["wireplumber", "--version"], "wireplumber 0.5.17")
    h.result(["pw-dump", "--no-colors"], (Path(__file__).parent / "fixtures/pipewire.json").read_text())
    for name in ("pipewire", "wireplumber", "pipewire-pulse"):
        set_service(h, name, pid=123 if name == "pipewire" else 0)
    set_service(h, "rtkit-daemon", user=False)
    h.files = {
        "/etc/os-release": 'ID=arch\nNAME="Arch Linux"',
        "/proc/cpuinfo": "processor: 0\nmodel name: Test CPU\nphysical id: 0\ncore id: 0\n\nprocessor: 1\nmodel name: Test CPU\nphysical id: 0\ncore id: 0",
        "/proc/meminfo": "MemTotal: 16000000 kB\nMemAvailable: 12000000 kB\nSwapTotal: 1000 kB\nSwapFree: 1000 kB",
        "/proc/asound/version": "Advanced Linux Sound Architecture Driver Version k6.18.0",
        "/proc/asound/cards": " 1 [Test           ]: USB-Audio - Test USB Interface\n   Test Vendor at usb-1, high speed",
        "/proc/asound/modules": "1 snd_usb_audio",
        "/proc/asound/card1/id": "Test",
        "/proc/asound/card1/pcm0c/info": "card: 1\ndevice: 0",
        "/proc/asound/card1/pcm0p/info": "card: 1\ndevice: 0",
        "/proc/asound/card1/pcm0p/sub0/hw_params": "format: S24_3LE\nchannels: 2\nrate: 48000 (48000/1)\nperiod_size: 128\nbuffer_size: 512",
        "/proc/asound/seq/clients": 'Client 0 : "System" [Kernel]\n  Port 0 : "Timer" (Rwe-)\nClient 24 : "Test Keys" [Kernel]\n  Port 0 : "Keys MIDI 1" (RWeX)',
        "/sys/class/sound/midiC1D0/uevent": "MAJOR=116",
        "/sys/devices/pci0000:00/usb1/1-2/idVendor": "1234",
        "/sys/devices/pci0000:00/usb1/1-2/idProduct": "abcd",
        "/sys/devices/pci0000:00/usb1/1-2/manufacturer": "Test Vendor",
        "/sys/devices/pci0000:00/usb1/1-2/product": "Test USB Interface",
        "/proc/123/comm": "pipewire",
        "/proc/123/status": "Uid:\t1000\t1000\t1000\t1000",
        "/proc/123/task/123/stat": scheduler_stat(123, 0, 0),
        "/proc/123/task/124/stat": scheduler_stat(124, 1, 88),
        "/proc/123/limits": "Max realtime priority     0      0\nMax locked memory    8388608    8388608    bytes",
        "/proc/self/status": "CapEff:\t0000000000000000",
        "/sys/devices/system/cpu/cpufreq/policy0/scaling_driver": "intel_pstate",
        "/sys/devices/system/cpu/cpufreq/policy0/scaling_governor": "powersave",
        "/sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq": "2500000",
    }
    h.links["/sys/class/sound/card1/device"] = "/sys/devices/pci0000:00/usb1/1-2/1-2:1.0"
    return h


def edit_dump(h, transform):
    key = ("pw-dump", "--no-colors")
    data = json.loads(h.commands[key].stdout)
    h.result(key, json.dumps(transform(data)))


def remove_package(h, name):
    key = ("pacman", "-Q")
    h.result(key, "\n".join(line for line in h.commands[key].stdout.splitlines() if not line.startswith(name + " ")))
