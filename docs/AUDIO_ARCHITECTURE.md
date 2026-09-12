# Audio observations

PipeWire is the preferred server, WirePlumber the session manager, ALSA the kernel-facing audio/MIDI layer, and pipewire-jack the JACK compatibility layer. No server is replaced.

A service being active does not prove the graph is reachable. A package being installed does not prove its libraries work in a DAW. Hardware inventory is not a claim of professional capability. Empty lists are valid only when the source was successfully observed; unavailable sources have an explicit unknown state.

Clock settings are published separately from active graph measurements. `quantum / rate` is a theoretical period duration, never measured round-trip latency. XRUN counts and round-trip latency remain unknown.

Active clocks use a bounded `pw-top -b -n 2` sample, retaining the final batch view. Only running driver rows contribute clocks; follower rows contain requests, not actual driver values. Audio groups are identified through matching `pw-dump` nodes with audio media classes, including support drivers with audio followers. Video-only groups are excluded. Two independent drivers remain separate even if their clock values happen to agree. The optional summary rate/quantum is populated only for exactly one observed active audio driver.

Idle means no running audio driver was observed among the matched audio groups; it is not proof of silence or future readiness. Missing tools/profiler, timeout, malformed output, transitional nodes, zero active clocks and mismatched snapshots produce unavailable observations. No audio nodes is unavailable, not a known idle workstation. A failed probe's partial stdout is discarded. The two-second probe deadline is unchanged; normal sampling adds about one second to each explicit refresh.

The parser deliberately targets the inspected PipeWire 1.6 batch layout. Names are matched privately with node IDs to reduce ID-reuse/hotplug mistakes, never exported from the sample. Truncated names cannot be safely matched and yield unavailable data. Snapshots are sequential, not atomic: a route or clock can change immediately after a sample. This is not a continuous meter or routing validator. No playback/capture stream is opened to force activity, and raw profiler output is never stored.

Realtime observations use the managed PipeWire process's thread scheduling classes. FIFO/RR on a thread is evidence at one instant, not a performance guarantee. An idle server may have no active realtime data thread. RTKit state and the invoking shell's limits are supplementary and cannot prove that a running DAW has realtime permissions. No journal contents are collected; targeted journal analysis with redaction is deferred.

ALSA MIDI sources send events; destinations receive them. `aconnect -i` lists readable/source ports, while `-o` lists writable/destination ports. Names are kept separately from numeric client/port identifiers. System and MIDI Through clients are virtual infrastructure, not connected controllers. PipeWire MIDI endpoints are listed separately and are not counted as additional physical devices.

Operational health is evaluated separately from optional capabilities and performance measurements in JSON schema 2. An unimplemented collector is not a discovered system misconfiguration. Selected default nodes come from current WirePlumber metadata; a remembered preference, a DAW route, and an actively running stream are different concepts. No probe opens a playback or capture stream.
