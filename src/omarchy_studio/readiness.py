"""Versioned prerequisite checklist, not a performance benchmark."""


def evaluate(probes):
    system, audio, pw, hardware, rt = (probes[k] for k in
                                      ("system", "audio_engine", "pipewire", "hardware", "realtime"))
    checks = []

    def add(id, label, value, evidence, recommendation):
        checks.append({"id": id, "label": label, "weight": 10,
                       "status": "PASS" if value is True else "FAIL" if value is False else "UNKNOWN",
                       "evidence": evidence, "recommendation": recommendation})

    compatible = system["integration_compatibility"]
    add("omarchy_target", "Omarchy integration target", True if compatible == "TARGET_VERSION" else
        False if compatible == "UNSUPPORTED" else None, "system.integration_compatibility",
        "Validate the plugin in an Omarchy 4.0.3 x86_64 session; other releases need compatibility review.")
    add("linux", "Linux kernel detected", system["linux"], "system.linux",
        "Run the Doctor in the target Linux user session.")
    reachable = pw["server_reachable"]
    if (reachable is None and audio["packages"]["pipewire"]["installed"] is False
            and pw.get("command_status") == "missing"
            and audio["services"]["pipewire"]["active_state"] in ("inactive", "failed")):
        reachable = False
    add("pipewire", "PipeWire server reachable", reachable, "pipewire.server_reachable; audio_engine.packages.pipewire",
        "Inspect PipeWire in the graphical user session; an absent tool or inaccessible bus needs investigation.")
    wp_active = audio["services"]["wireplumber"]["active_state"]
    wp = True if pw["wireplumber_client"] is True else (
        False if pw["snapshot_complete"] and pw["wireplumber_client"] is False and wp_active in ("inactive", "failed") else None)
    add("wireplumber", "WirePlumber connected to the graph", wp, "pipewire.wireplumber_client; audio_engine.services.wireplumber",
        "Inspect WirePlumber and its connection to the current PipeWire instance.")
    add("alsa", "ALSA kernel interface present", audio["alsa_present"], "audio_engine.alsa_present",
        "Inspect kernel sound support and device detection; ALSA userspace packages alone do not prove a device exists.")

    physical = [c for c in hardware["cards"] if c["physical"] is True]
    unknown_cards = any(c["physical"] is None for c in hardware["cards"])
    for direction in ("capture", "playback"):
        present = any(e["direction"] == direction for c in physical for e in c["pcm_endpoints"])
        value = True if present else (False if hardware["scan_complete"] and not unknown_cards else None)
        add("pcm_" + direction, f"Physical ALSA {direction} endpoint", value, "hardware.cards[].pcm_endpoints; physical",
            f"Connect a suitable interface and inspect its ALSA {direction} endpoints.")
    for direction, media_class in (("capture", "Audio/Source"), ("playback", "Audio/Sink")):
        physical_ids = {nid for c in physical for nid in c["pipewire_node_ids"] if nid is not None}
        matching = [n for n in pw["nodes"] if n["id"] in physical_ids
                    and n["media_class"] == media_class and n["state"] in ("suspended", "idle", "running")]
        present = bool(matching)
        value = True if present else (False if pw["snapshot_complete"] and hardware["scan_complete"] and not unknown_cards else None)
        if pw.get("custom_remote"):
            value = None
        add("graph_" + direction, f"Physical PipeWire {direction} node", value, "hardware.cards[].pipewire_node_ids; pipewire.nodes",
            f"Inspect the interface profile and {direction} route in PipeWire. Suspended nodes are normal when idle.")
    add("realtime", "PipeWire realtime thread observed", rt["runtime_rt_observed"], "realtime.threads",
        "Observe PipeWire data threads during a representative session; inspect daemon limits and RT module logs if needed.")

    confirmed = sum(c["weight"] for c in checks if c["status"] == "PASS")
    unknown = sum(c["weight"] for c in checks if c["status"] == "UNKNOWN")
    failures = any(c["status"] == "FAIL" for c in checks)
    status = ("NEEDS_ATTENTION" if failures else "INCOMPLETE" if unknown else "FOUNDATION_CHECKS_PASSED")
    return {"model_version": "0.1", "score": confirmed, "maximum": 100,
            "possible_score": confirmed + unknown, "coverage_percent": 100 - unknown,
            "status": status, "checks": checks,
            "limitation": "Prerequisites observed in one snapshot. Not certification of recording, latency, "
                          "duplex operation, hardware support or a DAW workload."}


def advisories(probes):
    result = []
    def add(id, message, recommendation):
        result.append({"id": id, "message": message, "recommendation": recommendation})
    packages = probes["audio_engine"]["packages"]
    for package, purpose in (("pipewire-jack", "JACK applications"),
                             ("pipewire-alsa", "ALSA applications routed through PipeWire"),
                             ("pipewire-pulse", "PulseAudio applications")):
        if packages[package]["installed"] is False:
            add(package, f"{package} is not installed.", f"Review whether {purpose} are required by the selected DAW; no score penalty.")
    memory = probes["memory"]
    if memory["available_fraction"] is not None and memory["available_fraction"] < 0.1:
        add("memory_pressure", "Less than 10% of memory is currently available.",
            "Review memory use with the actual session and sample libraries; this is an advisory threshold.")
    governors = {p["governor"] for p in probes["cpu"]["frequency_policies"]}
    if governors.intersection({"powersave", "conservative"}):
        add("cpu_policy", "A powersave or conservative CPU policy is present.",
            "Measure the workload before changing it; governor behavior depends on the scaling driver.")
    if probes["system"]["root_user"]:
        add("root_session", "Doctor is running as root; results may differ from the musician's session.",
            "Run as the desktop user for meaningful permissions and user-service observations.")
    if probes["pipewire"].get("custom_remote"):
        add("custom_remote", "PipeWire remote/runtime environment override detected.",
            "Physical graph correlation is UNKNOWN because the dump may describe a different instance.")
    return result
