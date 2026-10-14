# Probe run 1 (debug DLL `hf_probe`, 2026-10-14)

A debug-only DLL that records what the game does while the user presses keys, hovers, clicks and drives. Goal: find the unknown variables (hover, selection, mode, cursor) by observation. **Not part of QoL.**

## The probe
* Crate `/home/maksim/Development/hf_probe` (local git, commit `7e7a0c0`), DLL `/home/maksim/Development/hf_probe_build/Modloader/mods/hf_probe.dll`, test steps in `hf_probe_build/TEST.md`. Output: `Modloader/probe.log` in the game dir (`/home/maksim/.local/share/Steam/steamapps/common/HighFleet/Modloader/probe.log`), written by its own buffered thread.
* A 15 ms poll thread that works in **every screen** while the game window has focus: key and mouse-button edges (`GetAsyncKeyState`), the cursor (`GetCursorPos` + `ScreenToClient`, mapped to the 1920x1080 frame), and a memory diff of regions: `editor_flags` `0x1403ef300`+0x100, `held_and_zoom` `0x1403c0d00`+0x180, `layer_flags` `0x1403bd000`+0x200, `mode_globals` `0x143a11960`+0x40, `mode_flags` `0x147fc6f80`+0x80, and the held part's whole `0xa40`-byte `Body`.
* `HELD` lines: the held-part pointer `0x1403c0d88`, gated by the editor flag `0x1403ef368`. Optional raise of `dbgLogMode`.
* **Editor only:** a HUD (right side, `x=1890`, `y=120`, right aligned, `fixed_16`) and a one-sprite test, drawn from the label-pass hook `0x140303fb4` (see [render-pipeline.md](render-pipeline.md)).
* F9 drops a numbered mark, F10 learns noise for 3 s.

## The run [game]
User actions: opened the ship editor, hovered palette widgets, picked and held parts, rotated chassis legs, loaded a ship, then TEST (drive).

* The log has **3257 lines**: 3144 `MEM`, 68 `MOUSE`, 28 `KEY`, 10 `HELD`, 4 `FOCUS`, 1 `SPRITE`, 1 `PROBE`, 1 `HUD`.
* `HELD`: `MDL_RSZO_220` floor 0 (23.8 s and 24.6 s), `MDL_LEG_02` floor 0 (27.5 s), `MDL_FUEL_02` **floor 3** (38.2 s), `CRAFT_LA29` floor 0 (39.8 s).
* Keys `D W Shift S A` appear between 53 s and 75 s (TEST drive), `Esc` at 77.08 s. So polling and the memory diff work in the drive screen too.
* F9 and F10 were **not** pressed: no marks and no noise learning, which is why `MEM` dominated the log.
* `SPRITE "shpwrk_slide" -> 0x1bedfb50`: `GetAnimation` returned a non-null pointer. **The drawing itself is unconfirmed** (no screenshot of the sprite test yet).

## What it showed
| Finding | Evidence | Tag |
|---|---|---|
| After the first click, `GetCursorPos` + `ScreenToClient` returns client `(960,540)` on every poll in a 2560x1440 client: the OS cursor is pinned, so the `MOUSE` positions in the log are meaningless | log | [game] |
| The game warps the cursor itself and keeps its own virtual cursor | inference | [guess] |
| `0x1403ef304`, `0x1403ef308`, `0x1403ef30c` are zeroed at the start of every `VideoTask`: per-frame counters, pure noise (they changed in about 3000 snapshots) | decompile + log | [code] |
| `0x1403c0e60`..`67` (a 10.0f timer and neighbours) and `0x143a1197c`..`7f` (a timer 0..9.8) also change by themselves | log | [game] |
| `0x143a11963` is `VideoTask`'s skip-one-frame flag and toggles on screen transitions | decompile + log | [code] |
| `0x143a11984` is `VideoTask`'s lighting index, nonzero only on the arcade-battle branch (`IS_IN_ARCADE_BATTLE` `0x147fc6fb7` or `0x147fc6f82`); it went 0 -> 6 at 50.97 s and 6 -> 0 at 75.80 s, bracketing the WASD keys, so **TEST drive runs the arcade-battle renderer branch** | decompile + log | [code]+[game] |
| `0x143a11964` became 1 on entering the editor (2 for the editor-from-menu case in `FUN_1400beea0`) | decompile + log | [code]+[game] |
| `0x147fc6fc4` stepped `0, 8, 9, 2, 1, 2, 3, 4, 0x64, 2, 0, 8->9` | log | [game], meaning unknown |
| `0x1403bd078` cycled 1..4 about every 0.25 s while LMB was held in TEST | log | [game], meaning unknown |
| `0x1403bd00c` flips at screen changes; `IS_IN_CAMPAIGN?` is `0x147fc6fd0` | log + symbol | [game]/[code] |
| `0x1403c0dc8` / `0x1403c0dcc` are floats that changed continuously (about -40..85) while the mouse moved | log | [guess]: candidate virtual cursor or grid position |

## Design flaws found (fix in v1.1)
* The noise filter relied on F10, which was never pressed.
* Per-byte `MEM` lines are unreadable (3144 of 3257 lines).

## Unknowns
* Where the game keeps its **virtual cursor** (the arrow it draws). See the HGE input layout in [engine-hge.md](../engine-hge.md): `HGE+0x9fc/0xa00` is what the game's HGE layer sees, not necessarily the arrow.
* Meaning of `0x147fc6fc4` and `0x1403bd078`.
* Whether the sprite test draws at all.
* Whether `DBG_LOG_DEPTH` in `Config.ini` gives a verbose `client.log` (see `../../ref/config-ini.md`).
* Map and battle HUD seams (flush sites listed in [render-pipeline.md](render-pipeline.md)).

## Probe v1.1 plan
* Automatic noise filtering: hard-exclude `0x1403ef304`-`30f`, `0x1403c0e60`-`67`, `0x143a1197c`-`7f`; suppress addresses that change in more than about 25% of recent polls. F10 stays as an extra.
* A `MODE` line recomputed from the dispatcher flags, logged only on change.
* Readable `MEM` lines (hex / float / int, named globals), a verbose switch, a per-second cap.
* HGE mouse position (`HGE+0x9fc/0xa00`), wheel (`HGE+0x9f8`) and the key-state array (`HGE+0xa06`) instead of the OS cursor.
* HUD seams for map and battle after the RE below.
* Later: log-only entry hooks on the string lookup `0x1401ae090`, `GUI::HandleClick` `0x14012d050`, the sound-play function, `Editor_OnMouseWheel` `0x1400bc5e0`, and text drawn through `hgeFont::Render` as per-frame `+` / `-` differences. Function entries have RSP = 8 mod 16, so the hook needs an alignment wrapper.

## Live-test recipe
1. Run v1.1 in the editor, then the map, then a battle; press F9 before and after each action and write down what each pair of marks was.
2. Show `HGE+0x9fc/0xa00` next to the game's arrow on the HUD and compare; do the same with `0x1403c0dc8/dcc`.
3. Screenshot the editor with the probe HUD running to settle the sprite test.
4. Set `DBG_LOG_DEPTH=3` in `Config.ini` once (back it up first) and look at `client.log`.
