# hf_probe: the debug-only logging DLL (not a QoL mod)

> **Status (2026-10-19):** debug only, not installed now (`hf_probe_v2.4.dll.bak`). See the table in [README.md](README.md).

A modloader DLL that **only reads** the game and writes what it sees to `Modloader/probe.log`. It never patches game logic (the entry hooks are log-only; the HUD and seam test draw text). It exists to answer "what does the game do when I do X" for the notes; every finding that cites a probe run is under `findings/`. Source: `hf_probe` (crate `hf-probe`, local git, no remote; the header comment of `src/lib.rs` is the full version history). Never ship it together with QoL: it hooks the same editor label site (`0x140303fb4`) as the elevation hint, see [../hooks.md](../hooks.md).

## Install and run
* Build: `cargo xwin build --release` in `hf_probe` (target `x86_64-pc-windows-msvc`). Release DLLs carry the version in the file name and are archived in `hf_probe_build/versions/` (`hf_probe_v2.4.dll`); copy one into `Modloader/mods/` and **remove older probe DLLs** from there.
* Config: `Modloader/config/probe.json` (all keys optional; defaults below). Log: `Modloader/probe.log`, **created fresh at every game start** (the writer is not in append mode: truncating the file while the game runs leaves a run of NUL bytes at the start; `tr -d '\0'` strips them). Archive a log before the next launch.
* Games: `Steam 1.163` runs everything. `Steam 1.151` (probe 2.4) runs **only the BLAST/DMG hooks** at 1.151 addresses; the rest of the probe uses 1.163 addresses and stays off there. Other versions: the probe refuses to start.
* The first lines of a log are `HOOK <name> installed at ...` or `HOOK <name> skipped: bytes at ... are not the expected ones`. A `skipped` hook means the game bytes differ (another version or another mod hooked the site); nothing was patched.

## Versions
| Version | Added |
|---|---|
| 1.0 / 1.1 | `KEY`/`MOUSE` lines, `MARK n` (F9), `MEM` diffs with automatic noise filtering (F10), `MODE` (which renderer branch/screen), game mouse position from the HGE object |
| 1.2 | noise filter reports every 5 s instead of hiding for good, `MEM` resolves pointers to part names, HUD watch panel |
| 1.3 | one-shot ammo table dump (`AMMO` lines and `Modloader/probe_ammo_raw.txt`), typed reads on the `HELD` line |
| 2.0 | log-only entry hooks: `CLICK` (GUI click handler), `TEXT` (localised-string keys, once per screen), `SOUND`, `LOAD` (.seria paths), each with its caller; watchers `GOLD`/`PROFILE`, `FLEET`, `LOCATION` |
| 2.1 | `LOAD` reads the path from the right argument; `CLICK` logs the element's `fx` string |
| 2.2 | seam test: numbered labels after every flush call of the map, battle and menu renderers |
| 2.3 | `BLAST` (explosion routine entry) and `DMG` (every Body damage call) hooks |
| 2.4 | 1.151 support (BLAST/DMG only); `DMG` lines limited to calls from the explosion code (burn and physics ticks flooded the log with ~380k lines) |

## What the lines mean
* `BLAST #n obj=... pos=(x,y) +2c0=... explosive(+2dc)=E strength(+2e0)=S kind=... +20c=...`: one explosion. `explosive` is the warhead power, `strength` is the missile's `m_missile_ap` (0 for shells: no chain), `+2c0` a float that raises the chain budget. Offsets are 1.163; on 1.151 the same fields are `0x10` lower from `+0x2b0`. Meaning of the fields: [../findings/explosion-damage-1151-vs-1163.md](../findings/explosion-damage-1151-vs-1163.md).
* `DMG <part oid> stats=<index> dmg=D hp=H/M cost_if_chain(max/20)=C r8=... caller=+0x... after-blast#n`: one damage call. `caller` tells the path: 1.163 `+0x2d01a` area damage, `+0x2a7ae` first armored part, `+0x2a828` first unarmored part, `+0x2a9d4` armored in the chain, `+0x2aad4` unarmored in the chain (1.151: `+0x2de8b`, `+0x290e2`, `+0x29142`, `+0x292d5`, `+0x293b4`). `cost_if_chain` is `maxHealth/20`, the 1.163 chain cost; it is not a measured value.
* The other line types are explained where they were used: [../runs/probe-run-1.md](../runs/probe-run-1.md) (KEY/MOUSE/MEM/MODE/HELD), [../runs/ui-events-and-screens.md](../rendering/ui-events-and-screens.md) (CLICK/TEXT/SOUND/LOAD/GOLD/FLEET/LOCATION), [../runs/seam-test-run-1.md](../rendering/seam-test-run-1.md) (SEAM), [../findings/ammo-1151-vs-1163.md](../findings/ammo-1151-vs-1163.md) (AMMO).

## Config keys (`Modloader/config/probe.json`)
`log_path` (default `Modloader/probe.log`), `mark_key` (F9), `noise_key` (F10), `hud` and `sprite_test` (editor HUD and a one-sprite drawing test, both on), `game_log_level` (0 = leave the game's `dbgLogMode` alone), `watch_memory`, `verbose_mem`, `poll_ms` (15), the hooks `hook_clicks`, `hook_text_keys`, `hook_sounds`, `hook_level_load`, `hook_blast`, the watchers `watch_gold`, `watch_fleet`, `watch_location`, and the seam test `seam_test`, `seam_map`, `seam_battle`, `seam_other`, `seam_only` (list such as `["M10","M11"]`), `seam_key` (F7). All defaults are on. For a combat damage run turn everything off except `hook_blast` (`seam_test` and the HUD off as well) so the log stays small.

## Hook sites it uses (1.163)
GUI click handler `0x14012f120`, text lookup `0x1401ae090`, sound `0x1402e30e0`, .seria loader `0x140225930`, explosion routine `0x140029b60`, Body damage `0x1400519d0`, editor label pass `0x140303fb4` (HUD), plus the seam sites listed in the seam-test finding. 1.151: explosion routine `0x140028520`, Body damage `0x14004f540`. The ownership table, with which site each shipping mod uses, is [../hooks.md](../hooks.md).

## Logs
Archived runs are in `hf_probe_build/logs/` (v2.0, v2.2, and the 1.151/1.163 damage runs as `.log.gz`).
