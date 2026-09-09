import json
import unittest

from omarchy_studio.cli import display, render
from omarchy_studio.core import diagnose
from omarchy_studio.host import CommandResult, xdg_dir
from tests.fakes import FakeHost, session, edit_dump, remove_package, scheduler_stat, set_service


class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.host = session()

    def report(self):
        return diagnose(self.host)

    def check(self, report, id):
        return next(c for c in report["readiness"]["checks"] if c["id"] == id)["status"]

    def test_complete_foundation(self):
        report = self.report()
        self.assertEqual(report["readiness"]["score"], 100)
        self.assertEqual(report["readiness"]["status"], "FOUNDATION_CHECKS_PASSED")
        self.assertNotIn("READY FOR RECORDING", render(report))

    def test_missing_pipewire(self):
        remove_package(self.host, "pipewire")
        self.host.commands[("pw-dump", "--no-colors")] = CommandResult("missing")
        set_service(self.host, "pipewire", "inactive")
        report = self.report()
        self.assertEqual(self.check(report, "pipewire"), "FAIL")
        self.assertLess(report["readiness"]["score"], 100)

    def test_missing_tool_does_not_prove_daemon_absent(self):
        self.host.commands[("pw-dump", "--no-colors")] = CommandResult("missing")
        self.assertEqual(self.check(self.report(), "pipewire"), "UNKNOWN")

    def test_untracked_active_pipewire_not_declared_absent(self):
        remove_package(self.host, "pipewire")
        self.host.commands[("pw-dump", "--no-colors")] = CommandResult("missing")
        self.assertEqual(self.check(self.report(), "pipewire"), "UNKNOWN")

    def test_wireplumber_absent(self):
        remove_package(self.host, "wireplumber")
        edit_dump(self.host, lambda data: [o for o in data if o["id"] != 11])
        set_service(self.host, "wireplumber", "inactive")
        self.assertEqual(self.check(self.report(), "wireplumber"), "FAIL")

    def test_active_service_alone_does_not_prove_connection(self):
        edit_dump(self.host, lambda data: [o for o in data if o["id"] != 11])
        self.assertEqual(self.check(self.report(), "wireplumber"), "UNKNOWN")

    def test_optional_jack_has_no_score_penalty(self):
        remove_package(self.host, "pipewire-jack")
        report = self.report()
        self.assertEqual(report["readiness"]["score"], 100)
        self.assertIn("pipewire-jack", [a["id"] for a in report["advisories"]])

    def test_rt_without_rtkit_or_privileges_package(self):
        remove_package(self.host, "rtkit")
        remove_package(self.host, "realtime-privileges")
        set_service(self.host, "rtkit-daemon", "inactive", user=False)
        self.assertEqual(self.check(self.report(), "realtime"), "PASS")

    def test_rtkit_active_does_not_prove_rt(self):
        self.host.files["/proc/123/task/124/stat"] = scheduler_stat(124, 0, 0)
        self.assertEqual(self.check(self.report(), "realtime"), "FAIL")

    def test_rt_permission_error_is_unknown(self):
        self.host.denied.add("/proc/123/task/124/stat")
        self.assertEqual(self.check(self.report(), "realtime"), "UNKNOWN")

    def test_unexpected_stat_is_unknown(self):
        self.host.files["/proc/123/task/124/stat"] = "bad"
        self.assertEqual(self.check(self.report(), "realtime"), "UNKNOWN")

    def test_scheduler_comm_may_contain_spaces_and_parentheses(self):
        self.host.files["/proc/123/task/124/stat"] = scheduler_stat(124, 2, 70, "data) (loop with spaces")
        self.assertEqual(self.check(self.report(), "realtime"), "PASS")

    def test_ignore_another_users_pipewire(self):
        self.host.files["/proc/123/status"] = "Uid:\t1001\t1001\t1001\t1001"
        self.assertEqual(self.check(self.report(), "realtime"), "UNKNOWN")

    def test_process_scan_without_systemd_pid(self):
        set_service(self.host, "pipewire", pid=0)
        self.assertEqual(self.check(self.report(), "realtime"), "PASS")

    def test_no_interface(self):
        self.host.files = {k: v for k, v in self.host.files.items() if not k.startswith(("/proc/asound/card", "/sys/class/sound/card"))}
        self.host.links.clear()
        report = self.report()
        self.assertEqual(report["probes"]["hardware"]["cards"], [])
        self.assertEqual(self.check(report, "pcm_capture"), "FAIL")
        self.assertEqual(self.check(report, "graph_capture"), "FAIL")

    def test_multiple_interfaces(self):
        self.host.files["/proc/asound/card2/id"] = "Other"
        self.host.files["/proc/asound/card2/pcm0p/info"] = "card: 2"
        report = self.report()
        cards = report["probes"]["hardware"]["cards"]
        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[1]["pipewire_node_ids"], [])
        self.assertEqual(cards[1]["support_status"], "UNKNOWN")

    def test_usb_identity_and_no_invented_capabilities(self):
        card = self.report()["probes"]["hardware"]["cards"][0]
        self.assertEqual((card["vendor"], card["transport"], card["driver"]), ("Test Vendor", "USB", "snd_usb_audio"))
        for key in ("inputs", "outputs", "sample_rates", "bit_depths", "capabilities"):
            self.assertIsNone(card[key])
        self.assertEqual(card["active_hw_params"][0]["rate"], 48000)

    def test_unknown_hardware(self):
        self.host.links.clear()
        card = self.report()["probes"]["hardware"]["cards"][0]
        self.assertIsNone(card["transport"])
        self.assertEqual(card["support_status"], "UNKNOWN")

    def test_virtual_alsa_is_not_physical_hardware(self):
        self.host.files["/proc/asound/modules"] = "1 snd_aloop"
        self.assertEqual(self.check(self.report(), "pcm_capture"), "FAIL")

    def test_sysfs_permission_error_does_not_claim_empty_inventory(self):
        self.host.denied.add("/sys/class/sound")
        self.assertFalse(self.report()["probes"]["hardware"]["scan_complete"])

    def test_virtual_pipewire_source_is_not_capture_route(self):
        edit_dump(self.host, lambda data: [o for o in data if o["id"] != 30])
        self.assertEqual(self.check(self.report(), "graph_capture"), "FAIL")

    def test_node_error_is_not_ready(self):
        def transform(data):
            next(o for o in data if o["id"] == 30)["info"]["state"] = "error"
            return data
        edit_dump(self.host, transform)
        self.assertEqual(self.check(self.report(), "graph_capture"), "FAIL")

    def test_custom_remote_not_correlated_to_local_cards(self):
        self.host.env["PIPEWIRE_REMOTE"] = "other"
        self.assertEqual(self.check(self.report(), "graph_capture"), "UNKNOWN")

    def test_midi_three_backends(self):
        midi = self.report()["probes"]["midi"]
        self.assertEqual(midi["raw_devices"][0]["id"], "midiC1D0")
        self.assertEqual(midi["sequencer_clients"][1]["ports"][0]["name"], "Keys MIDI 1")
        self.assertEqual(midi["pipewire_ports"][0]["name"], "Test Keyboard")

    def test_rate_quantum_defaults_are_not_actual_timing(self):
        pw = self.report()["probes"]["pipewire"]
        self.assertEqual(pw["settings"]["clock.quantum"], 1024)
        self.assertEqual(pw["settings"]["clock.force-quantum"], 128)
        self.assertIsNone(pw["observed_quantum"])
        self.assertIsNone(pw["xruns"])

    def test_malformed_external_output(self):
        for value in ("not json", "{}", "null", "[null]", '[{"type": 3}]', "[]"):
            with self.subTest(value=value):
                self.host.result(["pw-dump", "--no-colors"], value)
                report = self.report()
                self.assertEqual(self.check(report, "pipewire"), "UNKNOWN")

    def test_incomplete_pw_objects(self):
        edit_dump(self.host, lambda data: data + [{"id": 99, "type": "PipeWire:Interface:Node", "info": None}])
        self.assertEqual(self.report()["probes"]["pipewire"]["status"], "PARTIAL")

    def test_failed_commands_are_evidence(self):
        for status in ("failed", "timeout", "output_limit", "unavailable", "budget_exhausted"):
            with self.subTest(status=status):
                self.host.commands[("pw-dump", "--no-colors")] = CommandResult(status)
                report = self.report()
                self.assertEqual(self.check(report, "pipewire"), "UNKNOWN")
                self.assertIn(status, [i["reason"] for i in report["issues"]])

    def test_incompatible_omarchy(self):
        key = ("pacman", "-Q")
        self.host.result(key, self.host.commands[key].stdout.replace("omarchy 4.0.3-1", "omarchy 3.8.4-1"))
        self.assertEqual(self.check(self.report(), "omarchy_target"), "FAIL")

    def test_future_omarchy_unvalidated(self):
        key = ("pacman", "-Q")
        self.host.result(key, self.host.commands[key].stdout.replace("omarchy 4.0.3-1", "omarchy 4.1.0-1"))
        self.assertEqual(self.check(self.report(), "omarchy_target"), "UNKNOWN")

    def test_different_architecture_is_unvalidated(self):
        self.host.machine = "aarch64"
        self.assertEqual(self.check(self.report(), "omarchy_target"), "UNKNOWN")

    def test_dev_build_does_not_use_stale_version_file(self):
        remove_package(self.host, "omarchy")
        self.host.files["/usr/share/omarchy/bin/omarchy-version"] = ""
        self.host.files["/usr/share/omarchy/version"] = "4.0.3"
        self.host.result(["omarchy-version"], "dev (abc123)")
        self.assertEqual(self.check(self.report(), "omarchy_target"), "UNKNOWN")

    def test_unavailable_package_database_is_not_absent_packages(self):
        self.host.commands[("pacman", "-Q")] = CommandResult("failed")
        self.assertIsNone(self.report()["probes"]["audio_engine"]["packages"]["pipewire-jack"]["installed"])

    def test_cpu_topology_governor_and_memory(self):
        report = self.report()
        self.assertEqual(report["probes"]["cpu"]["physical_cores"], 1)
        self.assertEqual(report["probes"]["cpu"]["logical_cpus"], 2)
        self.assertEqual(report["probes"]["memory"]["available_fraction"], 0.75)
        self.assertIn("cpu_policy", [a["id"] for a in report["advisories"]])

    def test_cpuinfo_frequency_when_cpufreq_is_absent(self):
        self.host.files["/proc/cpuinfo"] += "\ncpu MHz: 2687.999"
        frequencies = self.report()["probes"]["cpu"]["cpuinfo_reported_frequencies"]
        self.assertEqual(frequencies, [{"logical_cpu": 1, "mhz": 2687.999}])

    def test_malformed_cpuinfo_is_not_one_cpu(self):
        self.host.files["/proc/cpuinfo"] = "unexpected contents"
        self.assertIsNone(self.report()["probes"]["cpu"]["logical_cpus"])

    def test_memory_pressure_is_advisory(self):
        self.host.files["/proc/meminfo"] = "MemTotal: 1000000 kB\nMemAvailable: 1000 kB"
        report = self.report()
        self.assertIn("memory_pressure", [a["id"] for a in report["advisories"]])
        self.assertEqual(report["readiness"]["score"], 100)

    def test_empty_host_never_claims_ready(self):
        report = diagnose(FakeHost())
        self.assertNotEqual(report["readiness"]["status"], "FOUNDATION_CHECKS_PASSED")

    def test_uncertainty_not_renormalized(self):
        self.host.denied.add("/proc/123/task/124/stat")
        score = self.report()["readiness"]
        self.assertEqual((score["score"], score["possible_score"], score["coverage_percent"]), (90, 100, 90))
        self.assertEqual(score["status"], "INCOMPLETE")

    def test_no_serial_or_home_leak(self):
        self.host.files["/home/test/.config/pipewire/pipewire.conf.d/test.conf"] = "secret ignored contents"
        raw = json.dumps(self.report())
        self.assertNotIn("DO-NOT-EXPORT-THIS-SERIAL", raw)
        self.assertNotIn("/home/test", raw)
        self.assertNotIn("secret ignored contents", raw)

    def test_idempotent_and_no_writes(self):
        before = self.host.files.copy()
        first, second = self.report(), self.report()
        self.assertEqual(first["probes"], second["probes"])
        self.assertEqual(first["readiness"], second["readiness"])
        self.assertEqual(before, self.host.files)
        for entry in self.host.trace:
            self.assertIn(entry["argv"][0], ("pacman", "systemctl", "pipewire", "wireplumber", "pw-dump"))

    def test_xdg_absolute_and_relative_override(self):
        self.host.env["XDG_STATE_HOME"] = "/tmp/studio state"
        self.assertEqual(str(xdg_dir(self.host, "state")), "/tmp/studio state/omarchy-studio")
        self.host.env["XDG_STATE_HOME"] = "relative"
        self.assertEqual(str(xdg_dir(self.host, "state")), "/home/test/.local/state/omarchy-studio")

    def test_terminal_escape_sequences_are_neutralized(self):
        self.assertNotIn("\x1b", display("interface\x1b[2J\n\u202ebad"))
        self.assertNotIn("\n", display("interface\n"))


if __name__ == "__main__":
    unittest.main()
