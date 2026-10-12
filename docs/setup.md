# Setup, tooling, pitfalls

Game: Steam 1.163 (also 1.151 exists; GOG 1.163 is reported by the modloader but unsupported here). Image base `0x140000000`.
Runs under Proton on Linux; our DLLs are plain 64-bit Windows DLLs.

## Analysis
* `Highfleet.exe` on disk is Steam-DRM packed. The shared Ghidra project's main program is the **DRM-stripped `Highfleet.exe.unpacked.exe`** (v1.163, with names and structs).
  A **memory dump** of the running process (`/proc/<pid>/mem`, file offset = RVA) is kept as a reference copy (`Highfleet_1.163_dump.exe`): same code addresses and the same
  instruction bytes at the sites we compared, but a different section layout (`.bind` section, split `.data`) and fewer analysed functions (4,638 vs 5,115).
  Neither is a full-file hash match; verify patch-site bytes before trusting an address on a new build.
* Ghidra + a Ghidra MCP bridge: decompile, xrefs, `search_instructions`, `disassemble_bytes`, `read_memory`.
  Huge functions (the scenario script `FUN_1402ac970`) time out: read the jump tables with `read_memory` and disassemble the blocks.
* Cheapest live probe: a **log-only hook in our own DLL** that writes what it sees, driven by a test the player performs.
  `gdb` attach also works with `kernel.yama.ptrace_scope=0` (restore it to 1 afterwards).
* Naming: `FUN_...` are Ghidra auto names; named ones come from public work (ShipworksExtended, highfleet-qol) or from us.

## Modloader (logdot, `bass.dll` proxy; current 4.1.0)
* Original `bass.dll` is kept as `bass.dll_`. Mods are `Modloader/mods/*.dll`, loaded in an **unspecified order**; configs in `Modloader/config/`.
* A mod may export `version(const char*)` (`Steam 1.151`, `Steam 1.163`, `Gog 1.163`) and `init()`.
  **`init` is called even when `version` returned false**: a mod must guard itself.
* 4.1.0 adds a header-only C++ logging SDK (`sdk/include/highfleet/log.hpp`, `HIGHFLEET_SETUP_LOGGER()`, `highfleet::logging::info/warn/...`):
  messages go to `Modloader/logs` and the console, filtered per DLL name in `Modloader/config/logging.json`. No-op on older loaders.
  Our mods still write their own log files (candidate follow-up: adopt the SDK).
* The game code may still be encrypted when mods load: our mods wait (up to 3 min) until the expected bytes are visible before patching.

## Build
MinGW-w64 cross compiler, static (`-static -static-libgcc -static-libstdc++`), C++17; one `Makefile` per repo (`make`, `make dist`).
Editor support: a `.clangd` pointing at the MinGW headers.

## Pitfalls
* Memory scans must accept `PAGE_WRITECOPY`. The "window focused" check fails under Proton: hotkey mods must not depend on it.
* `pkill -f <pattern>` can match the shell that runs it.
* The game **rewrites `Libraries/OL.seria` and `Libraries/parts.seria` at startup**: edit them only with the game closed.
  A game update overwrites `Libraries/`, `Data/Dialogs/`, `Media/`.
* A clean reinstall deletes `Saves/`, `Ships/`, `Config.ini`: back them up first (a Steam Cloud marker exists but do not rely on it).
