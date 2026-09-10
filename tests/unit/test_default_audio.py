"""Default selections are snapshot evidence, independent of the readiness score."""
import copy
import json
import unittest

from omarchy_studio.cli import render
from omarchy_studio.core import diagnose
from omarchy_studio.host import CommandResult
from tests.fakes import edit_dump, session


def default_metadata(objects):
    return next(o for o in objects if o["id"] == 12)


class DefaultAudioTests(unittest.TestCase):
    def report(self, transform=None):
        host = session()
        if transform:
            edit_dump(host, transform)
        return diagnose(host)

    def assert_default(self, report, direction, status, node_id=None):
        default = report["probes"]["pipewire"]["default_nodes"][direction]
        self.assertEqual((default["status"], default["node_id"]), (status, node_id))

    def test_current_defaults_resolve_without_exporting_internal_names(self):
        report = self.report()
        self.assert_default(report, "capture", "RESOLVED", 30)
        self.assert_default(report, "playback", "RESOLVED", 31)
        self.assertEqual(report["readiness"]["score"], 100)
        raw = json.dumps(report)
        for private in ("DO-NOT-EXPORT-THIS-SERIAL", "alsa_input.usb-", "alsa_output.usb-", "unplugged-saved-output"):
            self.assertNotIn(private, raw)
        output = render(report)
        self.assertIn("Input: Test Input (node 30, Audio/Source) [suspended]", output)
        self.assertIn("Output: Test Output (node 31, Audio/Sink) [running]", output)

    def test_string_json_and_object_order_are_supported(self):
        def transform(data):
            for entry in default_metadata(data)["metadata"]:
                entry["value"] = json.dumps(entry["value"])
            return list(reversed(data))
        report = self.report(transform)
        self.assert_default(report, "capture", "RESOLVED", 30)
        self.assert_default(report, "playback", "RESOLVED", 31)

    def test_saved_preference_does_not_replace_missing_current_selection(self):
        def transform(data):
            metadata = default_metadata(data)
            metadata["metadata"] = [e for e in metadata["metadata"] if e["key"] != "default.audio.sink"]
            return data
        report = self.report(transform)
        self.assert_default(report, "playback", "NOT_SET")
        self.assert_default(report, "capture", "RESOLVED", 30)
        self.assertEqual(report["readiness"]["score"], 100)
        self.assertIn("default_playback_not_set", [a["id"] for a in report["advisories"]])
        self.assertIn("Output: NOT_SET (no default published)", render(report))

    def test_missing_metadata_is_unknown(self):
        report = self.report(lambda data: [o for o in data if o["id"] != 12])
        for direction in ("capture", "playback"):
            self.assert_default(report, direction, "UNKNOWN")
        self.assertFalse(any(a["id"].startswith("default_") for a in report["advisories"]))

    def test_empty_metadata_requires_read_permission_for_not_set(self):
        for permissions, status in ((["r"], "NOT_SET"), (["w", "x"], "UNKNOWN"), (None, "UNKNOWN"), ("r", "UNKNOWN")):
            with self.subTest(permissions=permissions):
                def transform(data):
                    default_metadata(data).update(metadata=[], permissions=permissions)
                    return data
                report = self.report(transform)
                for direction in ("capture", "playback"):
                    self.assert_default(report, direction, status)

    def test_unavailable_server_or_invalid_dump_is_unknown(self):
        for status, stdout in (("missing", ""), ("failed", ""), ("timeout", ""), ("ok", "not json")):
            with self.subTest(status=status):
                host = session()
                host.commands[("pw-dump", "--no-colors")] = CommandResult(status, stdout)
                report = diagnose(host)
                for direction in ("capture", "playback"):
                    self.assert_default(report, direction, "UNKNOWN")

    def test_core_required_even_when_default_metadata_is_visible(self):
        report = self.report(lambda data: [o for o in data if o["id"] != 0])
        self.assert_default(report, "capture", "UNKNOWN")
        self.assert_default(report, "playback", "UNKNOWN")

    def test_unmatched_selection_preserves_score_and_reports_advice(self):
        def transform(data):
            default_metadata(data)["metadata"][0]["value"] = {"name": "unplugged-PRIVATE-SENTINEL"}
            return data
        report = self.report(transform)
        self.assert_default(report, "capture", "UNRESOLVED")
        self.assertEqual(report["readiness"], self.report()["readiness"])
        self.assertIn("default_capture_unresolved", [a["id"] for a in report["advisories"]])
        self.assertNotIn("PRIVATE-SENTINEL", json.dumps(report))
        self.assertIn("Input: UNRESOLVED", render(report))

    def test_partial_graph_does_not_claim_unmatched_device_is_disconnected(self):
        def transform(data):
            next(o for o in data if o["id"] == 30)["info"] = None
            return data
        report = self.report(transform)
        self.assert_default(report, "capture", "UNRESOLVED")
        self.assertEqual(report["probes"]["pipewire"]["status"], "PARTIAL")
        advice = next(a for a in report["advisories"] if a["id"] == "default_capture_unresolved")
        self.assertIn("incomplete visibility", advice["recommendation"])

    def test_malformed_values_are_unknown_and_do_not_leak(self):
        for value in (None, [], {}, {"name": []}, {"name": ""}, 42, True, "null", "[]", "PRIVATE-SENTINEL"):
            with self.subTest(value=value):
                def transform(data):
                    default_metadata(data)["metadata"][0]["value"] = value
                    return data
                report = self.report(transform)
                self.assert_default(report, "capture", "UNKNOWN")
                self.assert_default(report, "playback", "RESOLVED", 31)
                self.assertIn("invalid_default_selection", [i["reason"] for i in report["issues"]])
                self.assertNotIn("PRIVATE-SENTINEL", json.dumps(report))

    def test_wrong_metadata_type_is_unknown(self):
        def transform(data):
            default_metadata(data)["metadata"][0]["type"] = "Spa:String"
            return data
        self.assert_default(self.report(transform), "capture", "UNKNOWN")

    def test_other_subject_and_metadata_namespace_are_ignored(self):
        def transform(data):
            metadata = default_metadata(data)
            unrelated = copy.deepcopy(metadata)
            unrelated["id"] = 90
            unrelated["props"]["metadata.name"] = "other"
            metadata["metadata"][0]["subject"] = 30
            return data + [unrelated]
        report = self.report(transform)
        self.assert_default(report, "capture", "NOT_SET")
        self.assert_default(report, "playback", "RESOLVED", 31)

    def test_invalid_metadata_structure_is_unknown(self):
        malformed = (None, {}, [None], [{}], [{"subject": False, "key": "default.audio.source"}],
                     [{"subject": 0, "key": []}], [{"subject": 0.0, "key": "default.audio.source"}])
        for entries in malformed:
            with self.subTest(entries=entries):
                def transform(data):
                    default_metadata(data)["metadata"] = entries
                    return data
                report = self.report(transform)
                self.assert_default(report, "capture", "UNKNOWN")
                self.assert_default(report, "playback", "UNKNOWN")
                self.assertIn("incomplete_default_metadata", [i["reason"] for i in report["issues"]])

    def test_duplicate_default_metadata_is_unknown(self):
        def transform(data):
            duplicate = copy.deepcopy(default_metadata(data))
            duplicate["id"] = 90
            return data + [duplicate]
        report = self.report(transform)
        self.assert_default(report, "capture", "UNKNOWN")
        self.assert_default(report, "playback", "UNKNOWN")

    def test_duplicate_selection_is_unknown(self):
        def transform(data):
            entries = default_metadata(data)["metadata"]
            entries.append(copy.deepcopy(entries[0]))
            return data
        report = self.report(transform)
        self.assert_default(report, "capture", "UNKNOWN")
        self.assert_default(report, "playback", "RESOLVED", 31)

    def test_ambiguous_names_or_node_ids_are_not_resolved(self):
        for duplicate_name in (True, False):
            with self.subTest(duplicate_name=duplicate_name):
                def transform(data):
                    duplicate = copy.deepcopy(next(o for o in data if o["id"] == 30))
                    if duplicate_name:
                        duplicate["id"] = 90
                    else:
                        duplicate["info"]["props"]["node.name"] = "another-input"
                    return data + [duplicate]
                self.assert_default(self.report(transform), "capture", "UNRESOLVED")

    def test_virtual_and_monitor_defaults_do_not_imply_physical_capture(self):
        for media_class in ("Audio/Source/Virtual", "Audio/Sink"):
            with self.subTest(media_class=media_class):
                def transform(data):
                    node = next(o for o in data if o["id"] == 30)
                    node["info"]["props"]["media.class"] = media_class
                    del node["info"]["props"]["device.id"]
                    return data
                report = self.report(transform)
                self.assert_default(report, "capture", "RESOLVED", 30)
                check = next(c for c in report["readiness"]["checks"] if c["id"] == "graph_capture")
                self.assertEqual(check["status"], "FAIL")

    def test_stream_or_invalid_node_id_is_not_resolved(self):
        for field, value in (("media.class", "Stream/Input/Audio"), ("media.class", None), ("id", None), ("id", True)):
            with self.subTest(field=field, value=value):
                def transform(data):
                    node = next(o for o in data if o["id"] == 30)
                    target = node if field == "id" else node["info"]["props"]
                    target[field] = value
                    return data
                self.assert_default(self.report(transform), "capture", "UNRESOLVED")

    def test_remote_defaults_describe_that_graph_without_local_hardware_claim(self):
        host = session()
        host.env["PIPEWIRE_REMOTE"] = "other"
        report = diagnose(host)
        self.assert_default(report, "capture", "RESOLVED", 30)
        for check in report["readiness"]["checks"]:
            if check["id"].startswith("graph_"):
                self.assertEqual(check["status"], "UNKNOWN")

    def test_default_labels_are_safe_in_terminal_output(self):
        def transform(data):
            next(o for o in data if o["id"] == 30)["info"]["props"]["node.description"] = "Input\x1b[2J\nINJECTED"
            return data
        output = render(self.report(transform))
        self.assertNotIn("\x1b", output)
        self.assertNotIn("\nINJECTED", output)

    def test_renderer_accepts_older_v1_report_without_default_nodes(self):
        report = self.report()
        del report["probes"]["pipewire"]["default_nodes"]
        self.assertIn("Input: UNKNOWN (insufficient evidence)", render(report))


if __name__ == "__main__":
    unittest.main()
