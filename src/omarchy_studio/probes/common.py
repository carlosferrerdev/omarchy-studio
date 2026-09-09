import re


def integer(value, *, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    if isinstance(value, str) and not re.fullmatch(r"[+-]?\d+", value):
        return None
    try:
        parsed = int(value)
        return parsed if parsed >= minimum else None
    except ValueError:
        return None


def mapping(value):
    return value if isinstance(value, dict) else {}


def sequence(value):
    return value if isinstance(value, list) else []


def string(value):
    return value if isinstance(value, str) and value else None


def fields(text, separator=":"):
    result = {}
    for line in (text or "").splitlines():
        if separator in line:
            key, value = line.split(separator, 1)
            if key.strip():
                result[key.strip()] = value.strip()
    return result


class PackageProbe:
    NAMES = ("omarchy", "omarchy-dev", "pipewire", "pipewire-audio", "wireplumber",
             "pipewire-pulse", "pipewire-alsa", "pipewire-jack", "alsa-lib",
             "alsa-utils", "rtkit", "realtime-privileges")

    def __init__(self, host):
        self.host = host

    def collect(self):
        result = self.host.run("pacman", "-Q")
        packages = {}
        valid = result.status == "ok"
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) != 2:
                valid = False
                continue
            if parts[0] in self.NAMES:
                packages[parts[0]] = parts[1]
        if not valid and result.status == "ok":
            self.host.issue("pacman -Q", "unexpected_output")
        return {name: {"installed": True if name in packages else (False if valid else None),
                       "version": packages.get(name), "source": "pacman -Q"}
                for name in self.NAMES}


def service(host, name, *, user=True):
    argv = ["systemctl"] + (["--user"] if user else [])
    result = host.run(*argv, "show", name, "--no-pager",
                      "--property=LoadState,ActiveState,SubState,MainPID")
    data = fields(result.stdout, "=")
    known = result.status == "ok" and data.get("LoadState") is not None and data.get("ActiveState") is not None
    if result.status == "ok" and not known:
        host.issue("systemctl " + name, "unexpected_output")
    return {"load_state": data.get("LoadState") if known else None,
            "active_state": data.get("ActiveState") if known else None,
            "sub_state": data.get("SubState") if known else None,
            "main_pid": integer(data.get("MainPID"), minimum=1) if known else None,
            "source": " ".join(argv) + " show " + name}


def version(host, binary):
    result = host.run(binary, "--version")
    if result.status != "ok":
        return None
    found = re.search(r"\b\d+\.\d+(?:\.\d+)?(?:[-+][\w.]+)?", result.stdout)
    if not found:
        host.issue(binary + " --version", "unexpected_output")
    return found.group() if found else None
