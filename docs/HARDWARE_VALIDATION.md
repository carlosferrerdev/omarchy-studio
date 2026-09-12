# Musical session validation

This is the next acceptance gate before configuration work. Fixture tests establish
parser behavior; they do not establish audible playback, successful recording,
MIDI event delivery or sustained performance on real hardware.

The opt-in `tests/hardware-smoke` runner checks one real CLI `doctor --json`
report against explicit expectations. It adds no system probes of its own, runs
unprivileged, bounds the entire collection to 30 seconds plus termination time,
and keeps the report in memory. It prints fixed diagnostic messages and counts,
not device labels, project names, raw command output or serial numbers. It never
starts a stream, changes a route, captures MIDI events or writes a report file.

## Run an observation

From the checkout, with the CLI dependencies already available:

```bash
./tests/hardware-smoke --help
./tests/hardware-smoke --live --expect-graph idle
```

While **you** play audio using your chosen application:

```bash
./tests/hardware-smoke --live --expect-graph active
```

When testing a connected USB interface and MIDI controller:

```bash
./tests/hardware-smoke --live --expect-graph active \
  --require-usb-audio --require-midi-source
```

Omit requirements that do not describe your equipment. `--expect-graph any`
accepts an observed active or idle graph, but never unavailable sampling. USB
means an enumerated audio device with USB transport, not a professional interface
certification. The MIDI requirement needs successful ALSA enumeration and a
hardware-classified source; virtual MIDI Through ports do not satisfy it. A
destination-only device does not satisfy a controller/source requirement.

## Interpret results

| Exit | Result | Meaning |
| --- | --- | --- |
| 0 | PASS | The requested observations match this snapshot. |
| 1 | FAIL | An operational problem, malformed report or unexpected CLI failure occurred. |
| 2 | Argument error | Supply `--live` and valid options. |
| 3 | Missing dependency | Install/review the documented CLI requirements yourself. |
| 4 | INCONCLUSIVE | Evidence is unavailable, the session is unsupported, collection timed out, or the expected condition was not observed. |

An idle graph while `active` was requested may simply mean playback stopped before
the sample. An absent USB device is an unmet test condition, not proof of a Studio
bug. If the diagnostic itself reports an operational error, that failure takes
precedence over other inconclusive conditions. Inspect the normal CLI doctor for
details; review friendly labels before sharing its full JSON output.

## Manual acceptance sequence

1. **Baseline:** with your applications idle, inspect the panel and run the idle
   observation. Record any application that intentionally keeps a graph active.
2. **Playback:** start playback yourself in the intended DAW/application. Run the
   active observation and compare the driver values with `pw-top -b -n 2` during
   the same workload. Compare driver rows, not follower requests or hardware FORMAT.
   Independently confirm what you hear and which output the application uses.
3. **Stop:** stop playback yourself, allow the application to settle, and inspect
   again. Some applications retain an active graph; do not force idle by restarting
   PipeWire or changing configuration just to make the test pass.
4. **Interface reconnection:** when you choose to reconnect the interface, inspect
   once disconnected and once reconnected. A snapshot mismatch during hotplug is
   inconclusive. Refresh after settling; IDs may change, and defaults need not
   prove the DAW's actual route. No script disconnects a device.
5. **MIDI:** inspect with and without your controller. Manually confirm source and
   destination availability, then use the DAW's own MIDI indicator to verify events
   if desired. Studio does not subscribe, connect ports or collect note data.
6. **Recording:** perform only as a separate, explicitly chosen manual test. Select
   the input in your DAW and verify the resulting recording yourself. A running
   driver or selected input alone does not establish successful capture.

For a local validation record, note date, Omarchy/Studio/PipeWire/WirePlumber
versions, interface/controller models, DAW version, requested conditions, observed
result, and manual playback/MIDI/capture outcomes. Mark unperformed steps **not
tested**. Do not include recordings, project titles, credentials or serial numbers.
Review any record before committing it. Convert reproducible failures into
synthetic fixtures; do not commit raw personal PipeWire dumps.

## Automation boundary and evidence

`scripts/check` lints this runner but does not execute it against the host. CI runs
`tests/session-validation.sh`, which substitutes a synthetic CLI in a temporary
checkout and covers opt-in, arguments, active/idle conditions, missing hardware,
virtual MIDI, malformed reports, exit codes and deadlines. The live test remains
separate from unit and QML integration tests.

The [pw-top documentation](https://docs.pipewire.org/page_man_pw-top_1.html) and
[ALSA sequencer documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/seq.html)
were rechecked for this workflow. Driver scheduling observations and endpoint
enumeration are distinct from successful playback/capture and MIDI event delivery.
No round-trip latency, pure XRUN count or performance certification is produced.

Initial validation on 2026-09-12: the live idle expectation passed. Requiring an
active graph, USB audio and a hardware MIDI source returned inconclusive with
each unmet condition identified. No workload was started. The 24 synthetic
wrapper scenarios and the complete foundation check suite passed. Physical
playback, recording, reconnection and MIDI delivery remain not tested.
