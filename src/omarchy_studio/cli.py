import argparse
import json
import logging
import sys
import unicodedata

from . import __version__
from .core import diagnose


def display(value):
    if value is None:
        return "UNKNOWN"
    if value is True:
        return "yes"
    if value is False:
        return "no"
    # Device labels and command output must not inject terminal control codes.
    return "".join(c if not unicodedata.category(c).startswith("C") else "?" for c in str(value))


def render(report):
    p = report["probes"]
    system, cpu, memory = p["system"], p["cpu"], p["memory"]
    lines = [f"OMARCHY STUDIO {report['plugin_version']} — STUDIO DOCTOR", "",
             f"Omarchy: {display(system['omarchy_detected'])} | Version: {display(system['omarchy_version'])}",
             f"Integration: {system['integration_compatibility']} | OS: {display(system['os_id'])}",
             f"Kernel: {display(system['kernel'])} | Architecture: {display(system['architecture'])}",
             f"Session: {display(system['session_type'])} | Desktop: {display(system['desktop'])}", "",
             "CPU / MEMORY",
             f"CPU: {display(', '.join(cpu['models']) or None)}",
             f"Cores: {display(cpu['physical_cores'])} | Threads: {display(cpu['logical_cpus'])}"]
    for policy in cpu["frequency_policies"]:
        lines.append(f"  {policy['policy']}: {display(policy['driver'])} / {display(policy['governor'])}, "
                     f"frequency {display(policy['frequency_khz'])} kHz")
    if not cpu["frequency_policies"]:
        lines.append("CPU governor / frequency: UNKNOWN")
    if cpu["cpuinfo_reported_frequencies"]:
        mhz_values = [item["mhz"] for item in cpu["cpuinfo_reported_frequencies"]]
        lines.append(f"cpuinfo reported frequency: {min(mhz_values):.1f}–{max(mhz_values):.1f} MHz (snapshot)")
    def gib(value):
        return f"{value / 1024 ** 3:.2f} GiB" if value is not None else "UNKNOWN"
    lines.extend([f"Memory available: {gib(memory['available_bytes'])} / {gib(memory['total_bytes'])}", "", "AUDIO ENGINE"])
    audio = p["audio_engine"]
    for name in ("pipewire", "wireplumber", "pipewire-pulse"):
        lines.append(f"{name}: package {display(audio['packages'][name]['version'])}; "
                     f"service {display(audio['services'][name]['active_state'])}")
    lines.append(f"Runtime/tool versions: PipeWire {display(p['pipewire']['server_version'] or audio['versions']['pipewire'])}, "
                 f"WirePlumber {display(audio['versions']['wireplumber'])}")
    for name in ("pipewire-alsa", "pipewire-jack", "alsa-lib"):
        lines.append(f"{name}: {display(audio['packages'][name]['installed'])} ({display(audio['packages'][name]['version'])})")
    lines.append(f"ALSA: {display(audio['alsa_version'])}")
    lines.extend(["", "REALTIME", f"PipeWire RT thread observed: {display(p['realtime']['runtime_rt_observed'])}",
                  f"rtkit: installed {display(p['realtime']['rtkit_installed'])}; "
                  f"service {display(p['realtime']['rtkit_service']['active_state'])}",
                  f"Doctor process limits: {display(p['realtime']['doctor_limits'])}"])
    for t in p["realtime"]["threads"]:
        lines.append(f"  PipeWire thread {t['tid']}: {t['policy']}, priority {t['rt_priority']}")
    lines.extend(["", "PIPEWIRE"])
    settings = p["pipewire"]["settings"]
    lines.extend([f"Configured default rate: {display(settings.get('clock.rate'))} Hz",
                  f"Configured default quantum: {display(settings.get('clock.quantum'))} samples",
                  f"Forced rate/quantum: {display(settings.get('clock.force-rate'))} / {display(settings.get('clock.force-quantum'))} (0 = unforced)",
                  "Observed graph rate / quantum / XRUNs: UNKNOWN (not measured)"])
    for node in p["pipewire"]["nodes"]:
        if (node["media_class"] or "").startswith("Audio/"):
            lines.append(f"  {display(node['media_class'])}: {display(node['description'])} [{display(node['state'])}]")
    lines.extend(["", "AUDIO HARDWARE"])
    for card in p["hardware"]["cards"]:
        lines.extend([f"{display(card['name'])} (ALSA card {card['alsa_card']}) — detected",
                      f"  Vendor: {display(card['vendor'])} | Transport: {display(card['transport'])} | Driver: {display(card['driver'])}",
                      f"  Support: {card['support_status']} | Physical: {display(card['physical'])}",
                      "  Supported inputs / outputs / rates / bit depths: UNKNOWN"])
        for active in card["active_hw_params"]:
            lines.append(f"  Active {active['direction']} PCM {active['device']}: "
                         f"{display(active['channels'])} channels, {display(active['rate'])} Hz, {display(active['format'])}")
    if not p["hardware"]["cards"]:
        lines.append("No ALSA cards observed." if p["hardware"]["scan_complete"] else "Hardware inventory: UNKNOWN")
    lines.extend(["", "MIDI"])
    midi = p["midi"]
    for dev in midi["raw_devices"]:
        lines.append(f"ALSA raw MIDI: {dev['id']}")
    for client in midi["sequencer_clients"]:
        lines.append(f"ALSA client {client['id']}: {display(client['name'])} [{display(client['type'])}]")
        for port in client["ports"]:
            lines.append(f"  Port {port['id']}: {display(port['name'])} ({display(port['flags'])})")
    for port in midi["pipewire_ports"]:
        lines.append(f"PipeWire MIDI port: {display(port['name'])} ({display(port['direction'])})")
    if not (midi["raw_devices"] or midi["sequencer_clients"] or midi["pipewire_ports"]):
        lines.append("No MIDI endpoints observed; see JSON for backend availability.")
    score = report["readiness"]
    lines.extend(["", "STUDIO READINESS — prerequisite checklist"])
    for check in score["checks"]:
        lines.append(f"[{check['status']}] {check['label']} ({check['weight']} points)")
    lines.extend([f"{score['score']} / 100 confirmed | possible range {score['score']}–{score['possible_score']} | "
                  f"evidence coverage {score['coverage_percent']}%", score["status"], score["limitation"], "", "RECOMMENDATIONS"])
    recommendations = [c["recommendation"] for c in score["checks"] if c["status"] != "PASS"]
    for item in report["advisories"]:
        recommendations.append(item["message"] + " " + item["recommendation"])
    lines.extend("- " + text for text in recommendations)
    if not recommendations:
        lines.append("- Validate recording/playback with the chosen DAW, hardware and workload.")
    if report["issues"]:
        lines.append(f"\nCollection issues: {len(report['issues'])}; use --json or --verbose for evidence.")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="omarchy-studio", description="Read-only diagnostics for music production on Omarchy.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor", help="inspect the current user session without changing settings")
    doctor.add_argument("--json", action="store_true", help="emit a single JSON report (schema version 1)")
    doctor.add_argument("--verbose", action="store_true", help="log probe operations to stderr; no persistent logs")
    doctor.add_argument("--strict", action="store_true", help="exit 1 unless all foundation checks pass")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING,
                        format="%(levelname)s %(message)s", stream=sys.stderr)
    try:
        report = diagnose()
        print(json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False) if args.json else render(report))
        return 1 if args.strict and report["readiness"]["status"] != "FOUNDATION_CHECKS_PASSED" else 0
    except BrokenPipeError:
        return 0
    except KeyboardInterrupt:
        return 130
