# Raw DeepSeek reports for the hot-reload study (2026-10-27)
Five AI-written, read-only Ghidra reports (v4.1 flash). **Unverified except where [../../docs/findings/hot-reload-feasibility.md](../../docs/findings/hot-reload-feasibility.md) says `verified`.** Earlier DeepSeek reports contained arithmetic and polarity errors; check an address before relying on it.
* `ds4-files.md`: how the game reads files
* `ds4-threads.md`: frame loop, threads, safe points (the best of the five)
* `ds4-builtin.md`: built-in dev/reload facilities
* `ds4-data.md`: in-memory tables and loader re-runs
* `ds4-modside.md`: mod loader, patchy, config reload designs
