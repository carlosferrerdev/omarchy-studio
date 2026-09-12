# Audio observations

PipeWire is the preferred server, WirePlumber the session manager, ALSA the kernel-facing audio/MIDI layer, and pipewire-jack the JACK compatibility layer. No server is replaced.

A service being active does not prove the graph is reachable. A package being installed does not prove its libraries work in a DAW. Hardware inventory is not a claim of professional capability. Empty lists are valid only when the source was successfully observed; unavailable sources have an explicit unknown state.

Clock settings are published separately from active graph measurements. `quantum / rate` is a theoretical period duration, never measured round-trip latency. Active rate, active quantum, XRUN counts and round-trip latency remain unknown in the foundation release.

Realtime observations use the managed PipeWire process's thread scheduling classes. FIFO/RR on a thread is evidence at one instant, not a performance guarantee. An idle server may have no active realtime data thread. RTKit state and the invoking shell's limits are supplementary and cannot prove that a running DAW has realtime permissions. No journal contents are collected; targeted journal analysis with redaction is deferred.

ALSA MIDI sources send events; destinations receive them. `aconnect -i` lists readable/source ports, while `-o` lists writable/destination ports. Names are kept separately from numeric client/port identifiers. System and MIDI Through clients are virtual infrastructure, not connected controllers. PipeWire MIDI endpoints are listed separately and are not counted as additional physical devices.

Operational health is evaluated separately from optional capabilities and performance measurements in JSON schema 2. An unimplemented collector is not a discovered system misconfiguration. Selected default nodes come from current WirePlumber metadata; a remembered preference, a DAW route, and an actively running stream are different concepts. No probe opens a playback or capture stream.
