# Installing the mods on a clean game (Steam 1.163, Linux/Proton)

Order matters in two places: the modloader before any mod, and the game must have run **once with ShipworksExtended** before the data tool can add parts to the shipworks palette.
Facts below come from our own installs; the Proton launch options are the part of this page you may not need (see "Proton").

## 0. Before the reinstall
* Back up `Saves/`, `SavesSkirmish/`, `Ships/`, `Config.ini`, `Modloader/config/` (a tarball of these plus `Modloader/config` is in `~/Development_Highfleet/hf_game_backup`).
* Steam may install a newer build than 1.163. Check after step 2: `error.log` starts with `HIGHFLEET v.1.163`, and later the modloader log says `Highfleet version: Steam 1.163`. Our DLLs refuse to run on any other build.

## 1. Clean reinstall
1. Steam: uninstall Highfleet. 
2. Delete what is left of the folder. The game folder must show only Steam's files.
3. Install through Steam, then **verify the game files** once.
4. Restore `Saves/`, `SavesSkirmish/`, `Ships/`, `Config.ini` from the backup (`Modloader/config/` only after step 3 has created it) *while the game is closed*.
-# Linux only: The Wine prefix (`~/.local/share/Steam/steamapps/compatdata/1434950`) survives an uninstall and already has `gdiplus.dll`; no launch options are set on our machine and everything works.

## 2. Modloader 4.1.0 (logdot)
Download `Modloader.zip` from the latest release (v4.1.0; the asset was called `Artifacts.zip` in older releases and the upstream README still says so). The zip contains **only the loader `bass.dll`** (about 2.3 MB), no `bass.dll_`. **First rename the game's own `bass.dll` (257,536 bytes, the real BASS audio library) to `bass.dll_`, then copy the loader's `bass.dll` in**; the loader loads `<its own path>_` and forwards audio calls to it, and nothing renames the original for you. You must end up with **`bass.dll` (the loader) and `bass.dll_` (the original)** next to `Highfleet.exe`. If you copied first, Steam's 'Verify integrity of game files' restores the original. [game, checked on the 2026-10-14 install; loader source `src/lib.rs`]
Start the game once and close it: `Modloader/` appears with `logs/`, `config/logging.json`, `mods/`. Its newest log (`Modloader/logs/Highfleet_<date>.log`) must say `Highfleet version: Steam 1.163`.

## 3. Companion mods (drop DLLs in `Modloader/mods`, configs in `Modloader/config`)
| Mod | Source | Notes |
|---|---|---|
| ShipworksExtended | logdot release (Linux support is merged) or our saved working copy `hf_aa_missile/ShipworksExtended.dll` | needs `gdiplus` in the prefix; **open the shipworks once** so `Modloader/config/Shipworks.json` is created, then close the game |
| highfleet-qol | logdot release | creates `qol.json`; for the elevation test keep `"enable_unblocked_guns": false` (gun arcs blocked) |
Do not hand-edit `Shipworks.json` with ids that do not exist: a part that is missing or malformed in the shipworks list crashes the game on entering the shipworks (ShipworksExtended README).

## 4. Our mods (each zip merges into the game folder)
`highfleet-elevation` (**do not keep an older `elevation.dll` next to `highfleet_elevation.dll`**), `highfleet-speed`, `highfleet-refuel`, `highfleet-salvo` are plain drop-ins (config files are shipped or created on first run).
**`highfleet-multicharge` has one extra step**, with the game *closed* and `Shipworks.json` present:
```
python3 tools/apply_data.py "<game folder>"
```
Expected output: each section `OL.seria stats : [...]`, `parts.seria body: [...]`, `language packs : {...}`, `shipworks palette: [...]` listing the new ids (`MDL_AA_X3/X2/X1`, `MDL_A101_4..1`), then `done`.
It makes `.bak` copies once; running it again prints `already present`. A game update overwrites the edited files: run it again.

### QoL fork variant (elevation, speed, refuel)
The QoL fork (logdot's highfleet-qol plus our ports; open pull requests in [../STATUS.md](../STATUS.md)) provides these three as sections `elevation`, `refuel` and `speed` of `Modloader/config/qol.json`, 1.163 only. **Never install both** a standalone DLL and its QoL section: they patch the same sites ([hooks.md](hooks.md)). With the QoL build, remove `highfleet_elevation.dll` / `elevation.dll`, `speed.dll` and `refuel.dll`; `elevation.ini`, `speed.ini` and `refuel.ini` are no longer read, and config is read at startup only. Expected log lines are quoted in [mods/speed.md](mods/speed.md) (`Speed curve patch prepared at 0x140080699`) and [mods/refuel.md](mods/refuel.md) (`Refuel rate patch prepared at 0x14011521f (200 -> 2000)`); the elevation hint is drawn inside the game by default (`hint: native`, see [mods/elevation.md](mods/elevation.md)), so the standalone mod's own log lines (`Modloader/elevation.log`) do not apply to the QoL build.

## 5. Settings used for the tests (everything ships at vanilla values)
| File | Setting | Test value |
|---|---|---|
| `salvo.ini` | `map_launch_delay` / `group_missiles` | `3` / `1` (shipped `-1` / `0` = off) |
| `refuel.ini` | `player_rate_multiplier` | `5` (shipped `1`) |
| `speed.ini` | `preset` | `classic` for the second half of the speed test (shipped `vanilla`) |
Restart the game after any change (the standalone `speed.ini` also reloads by itself within about 1 s; the QoL port reads its config at startup only).

## 6. Pass/fail record: what each mod writes when it works
| Mod | File | Expected lines |
|---|---|---|
| Modloader | `Modloader/logs/Highfleet_*.log` | `Highfleet version: Steam 1.163`, `Loading mod: ...` for every DLL, no `Failed` |
| elevation | `Modloader/elevation.log` | `elevation mod loaded: U raise, P lower, \ auto ...`, `overlay created` |
| speed | `Modloader/speed.log` | `patch installed (call site 0000000140080699 ...)`, then `speed: TWR=... -> ... km/h` lines when ships are shown |
| multicharge | `Modloader/multicharge.log` | `charges: enabled=1, 2 part chain(s)`, `detours: player=1 ai=1 map=1`; in battle `... launched a clone of part ... now MDL_AA_X2 (2 of 3 left)` and finally `last charge (MDL_AA_X1) launched the real part`; on the map `map launch: ... level MDL_A101_4 (4 of 4 charges left)` |
| salvo | `Modloader/salvo.log` | `salvo: enabled=1 map_launch_delay=3 group_missiles=1 ...`, `loader hook=1, launch cooldown patch=1`, `launch cooldown: 300 -> 3`; a grouped defence logs `group: merged N object(s); the defence will face N+1 missile(s)` |
| refuel | `Modloader/refuel.log` | `rate patch: 1` and three `rate: ...` lines (`player (fuel station) rate 200 -> 1000`, `player rate 100 -> 500`, `AI rate 100 -> 100`) |
In-game checks, in the order of the checklist: elevation (U/P/\\ on a held part), speed (shipworks stats: vanilla numbers first, then classic = `25 * TWR`), Triumph in a shipworks test battle (names go "С-4 Триумф" > "(2/3)" > "(1/3)" and the part vanishes after the third launch),
A-101 in the campaign (map launch 4/4 -> 1/4, then gone), the Kh-15 salvo (volley leaves together; grouped defence faces several missiles in one battle), refueling (compare the time at multiplier 1 and 5).

## 7. If something does nothing
1. The mod's own log first (table above): a `unsupported game version` line means the build is not Steam 1.163; `... never matched the expected bytes` means the game code differs.
2. The modloader log: the DLL must be listed as loaded; `does not expose highfleet_mod_setup_v1` is only the optional logging bridge and is harmless.
3. Crash when entering the shipworks: `gdiplus` (`protontricks 1434950 gdiplus`) or a bad entry in `Shipworks.json`.
4. After a game update: run `apply_data.py` again; if the build changed, our mods stay inactive by design.
5. Roll back: delete the mod DLLs; restore the `.bak` files (`Libraries/OL.seria`, `parts.seria`, `Data/Dialogs/*`); Steam "verify files". Saves containing the multi-charge parts will not load without their definitions.

## Proton
Logdot's ShipworksExtended README suggests launch options `WINEDLLOVERRIDES="dinput8=n,b;gdiplus=n,b;bass=n,b" %command%` and `protontricks 1434950 gdiplus` for Linux. On our machine neither was needed (no launch options; `gdiplus.dll` already in the prefix);
add them only if the shipworks crashes or the loader is not picked up.
