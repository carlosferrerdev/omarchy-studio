import re
from pathlib import Path

from .common import fields, integer, service


class RealtimeProbe:
    """Observe the PipeWire daemon's scheduling, never attempt sched_setscheduler."""

    def __init__(self, host):
        self.host = host

    def collect(self, audio):
        h = self.host
        kit = service(h, "rtkit-daemon.service", user=False)
        threads = []
        limits = h.limits()
        pid = audio["services"]["pipewire"]["main_pid"]
        pids = [str(pid)] if pid else [Path(p).name for p in (h.glob("/proc", "[0-9]*") or [])]
        daemon_limits = []
        inspected = 0
        incomplete = False
        for process in pids:
            comm = h.read(f"/proc/{process}/comm")
            if comm != "pipewire":
                continue
            status = fields(h.read(f"/proc/{process}/status"))
            uid = integer(status.get("Uid", "").split()[0]) if status.get("Uid", "").split() else None
            if uid != h.uid:
                continue
            inspected += 1
            proc_limits = h.read(f"/proc/{process}/limits")
            selected_limits = {}
            for line in (proc_limits or "").splitlines():
                match = re.match(r"^(Max realtime priority|Max locked memory|Max realtime timeout)\s+(\S+)\s+(\S+)(?:\s+(\S+))?", line)
                if match:
                    selected_limits[match[1]] = {"soft": match[2], "hard": match[3], "units": match[4]}
            daemon_limits.append({"pid": int(process), "limits": selected_limits})
            tasks = h.glob(f"/proc/{process}/task", "[0-9]*")
            if not tasks:
                incomplete = True
            for task in tasks or []:
                stat = h.read(task + "/stat")
                try:
                    # comm may contain spaces and ')': fields after its last ')'
                    # start at field 3. policy = field 41, rt_priority = field 40.
                    rest = stat[stat.rindex(")") + 2:].split() if stat else []
                    policy = integer(rest[38])
                    priority = integer(rest[37])
                    if policy is None or priority is None:
                        raise ValueError("invalid scheduler fields")
                except (ValueError, IndexError):
                    incomplete = True
                    continue
                threads.append({"pid": int(process), "tid": int(Path(task).name),
                                "policy": {0: "OTHER", 1: "FIFO", 2: "RR", 3: "BATCH", 5: "IDLE", 6: "DEADLINE"}.get(policy, f"UNKNOWN({policy})"),
                                "rt_priority": priority})
        observed = any(t["policy"] in ("FIFO", "RR") and t["rt_priority"] > 0
                       for t in threads)
        if not observed:
            observed = False if threads and not incomplete else None
        capability_text = fields(h.read("/proc/self/status")).get("CapEff")
        try:
            cap_sys_nice = bool(int(capability_text, 16) & (1 << 23)) if capability_text else None
        except ValueError:
            cap_sys_nice = None
        rtprio = limits.get("rtprio", {}).get("soft")
        return {"runtime_rt_observed": observed, "inspection_complete": bool(inspected) and not incomplete,
                "threads": threads, "daemon_limits": daemon_limits, "doctor_limits": limits,
                "doctor_cap_sys_nice": cap_sys_nice,
                "direct_rt_limit_positive": rtprio == "unlimited" or (isinstance(rtprio, int) and rtprio > 0),
                "rtkit_service": kit,
                "rtkit_installed": audio["packages"]["rtkit"]["installed"],
                "realtime_privileges_installed": audio["packages"]["realtime-privileges"]["installed"],
                "portal_availability": None, "mechanism_in_use": None,
                "source": "/proc/<user PipeWire pid>/task/<tid>/stat; process limits; systemd",
                "note": "Observed scheduling does not prove which mechanism granted it. "
                        "Doctor limits are not the daemon's or the DAW's limits. "
                        "A normal main thread is expected; data threads are inspected individually."}
