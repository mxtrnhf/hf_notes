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

## Comparing with the 1.151 program (method and pitfalls)
The shared project also holds logdot's annotated 1.151 program (more hand-named functions than 1.163: about 875 against 560; 535 names are in both). What was compared and how to carry names over: [version-differences.md](version-differences.md); the plan: roadmap, Ghidra side.
* **Fuzzy-match scores below about 0.9 are unreliable.** Example: 1.151 `Get_Profile` at `0x14026ff50` matched 1.163 `0x1402924b0` (score 0.8166), but that is a 4-slot array accessor; the real 1.163 `Get_Profile_` is `0x140292a90`. Treat a low score as a candidate only. The `rep_<addr>_<name>` names are machine-propagated from one program to the other, so they are not independent evidence.
* **The 1.163 `Body` struct in Ghidra is 0xa08 bytes; the object is 0xa40.** Do not trust Ghidra field offsets past about `0x2f0` in 1.163 (and the `Profile`, `Escadra`, `Creature` structs are stale too); use `structures.md`. Copying 1.151 structs over would put names on the wrong offsets.
* The 1.151 field names `mdl_covered` / `mdl_turbine` are swapped relative to what 1.163 `UpdateEngineCovered` writes; `fFireCharge`, `fFireRateTimer`, `fFireDelay`, `bFireStatus` do not match how `FireGun` uses the fields. Do not carry them across.
* Input stack differs by version: 1.163 uses SDL2 for controllers, 1.151 used DirectInput8; keep that in mind for input hooks.

## Modloader (logdot, `bass.dll` proxy; current 4.1.0)
* Original `bass.dll` is kept as `bass.dll_`. Mods are `Modloader/mods/*.dll`, loaded in an **unspecified order**; configs in `Modloader/config/`.
* A mod may export `version(const char*)` (`Steam 1.151`, `Steam 1.163`, `Gog 1.163`) and `init()`.
  **`init` is called even when `version` returned false**: a mod must guard itself.
* 4.1.0 adds a header-only C++ logging SDK (`sdk/include/highfleet/log.hpp`, `HIGHFLEET_SETUP_LOGGER()`, `highfleet::logging::info/warn/...`):
  messages go to `Modloader/logs` and the console, filtered per DLL name in `Modloader/config/logging.json`. No-op on older loaders.
  Our mods still write their own log files (candidate follow-up: adopt the SDK).
* The game code may still be encrypted when mods load: our mods wait (up to 3 min) until the expected bytes are visible before patching.

## Third-party mods we depend on (addresses from ShipworksExtended, 1.163)
* **ShipworksExtended** palette: `DefinePartEx` `0x14021b190`, `CreateLibraryEx` `0x14027f200`, `MakeGlobalEx` `0x140194de0` (the smart-ref assign `FUN_140194de0`), `New` `0x140334094`, editor libraries at `0x1403bd400..` (stride 0x18), `EditorParts` global `0x143a139f0`. It reads `Modloader/config/Shipworks.json`; the file appears after the first run with the mod (keys in `formats.md`).
* **Shops** come from logdot's highfleet-qol (`Modloader/config/qol.json`): `enable_shop_parts` and `shop_parts.<ID> = [{probability, min_parts, max_parts, city_types}]`. Rolled **only when a city's shop is first generated**. City types: 1 UR, 2 repair, 3 merchant, 4 fuel, 5 intel, 6 mercenary, 7 fleet HQ.

## Build
MinGW-w64 cross compiler, static (`-static -static-libgcc -static-libstdc++`), C++17; one `Makefile` per repo (`make`, `make dist`).
Editor support: a `.clangd` pointing at the MinGW headers.

## Pitfalls
* Memory scans must accept `PAGE_WRITECOPY`. The "window focused" check fails under Proton: hotkey mods must not depend on it.
* `pkill -f <pattern>` can match the shell that runs it.
* The game **rewrites `Libraries/OL.seria` and `Libraries/parts.seria` at startup**: edit them only with the game closed.
  A game update overwrites `Libraries/`, `Data/Dialogs/`, `Media/`.
* A clean reinstall deletes `Saves/`, `Ships/`, `Config.ini`: back them up first (a Steam Cloud marker exists but do not rely on it).
