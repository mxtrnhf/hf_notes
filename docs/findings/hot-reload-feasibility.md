# Hot-reloading mods and data without restarting (feasibility study, 2026-10-27)

Question: can a Highfleet 1.163 mod (a) be hot-swapped, (b) re-read its JSON config, (c) make the game re-read its own data, all without restarting the game? Static study only: five DeepSeek v4.1 flash agents read Ghidra and our sources (reports in [../../ref/hot-reload-ds4-reports/](../../ref/hot-reload-ds4-reports/)); the curator then re-checked the claims marked `verified` below in Ghidra or in the `patchy` source. Nothing here has been run in the game.

## Verdicts
| Idea | Verdict | Why in one line |
|---|---|---|
| (b) re-read mod JSON, values read per call | **feasible**, small | the game has no JSON code; config is purely mod-side. Values that live in plain statics/atomics (refuel rate, sell, zoom, most of hf_ally) can be swapped any time |
| (b) re-read JSON, values baked into patched bytes | **feasible with caveats** | on/off switches and rule sets are code (trampolines, immediates). `patchy` cannot un-patch or re-patch, so these need our own byte ledger, or an identity value (refuel and sell: 1.0 reproduces the original) |
| (a) unload and reload a mod DLL | **not feasible** | trampolines hold absolute pointers into the DLL; the loader never unloads; mods start threads |
| (a') resident shim plus swappable logic DLL | **feasible with caveats** | shim owns all patch sites and a function table; generations are `LoadLibrary`'d and swapped at a frame boundary; old DLL stays mapped forever. Not tried |
| (c) game re-reads a level script | **feasible** (the game already does this on every scene change) | request through the game's own queue, never call the loader yourself |
| (c) language packs, `Config.ini`, ship design list | **feasible with caveats** | existing re-read paths (below) |
| (c) `OL.seria` stats table | in-place edits **feasible**; full re-run **feasible with caveats** (leaks ~67 KiB, empty table on a parse failure); the game writes the table back on quit |
| (c) `Media/*.res`, textures, Box2D world | **not feasible** | built once, engine rejects redefinition, sprites keep pointers |

## The frame loop and the safe point (verified)
* `Main` -> `PrepareMainLoop` 0x1401ad5a0 -> HGE `System_Start` 0x14017e080 -> frame function `!FrameFunc` 0x1401a8970 once per iteration. The seven tasks run in a fixed chain at 0x1401a8eb8..0x1401a8eda: `SomethingPreTask` 0x140286e40, Physic, Input, AI, Game, Sound, Video. Only this block calls them.
* **Hook site S1:** 5 bytes `E8 83 DF 0D 00` (`CALL SomethingPreTask`) at 0x1401a8eb8 (verified). A call-site wrapper there runs on the game thread at a frame boundary; call PreTask yourself, then do the swap/reload work. Call-site RSP is 16-aligned (the entry-hook misalignment crash in sound.md does not apply). Not yet hooked by any mod.
* The exe creates no threads (verified: no `CreateThread`/`_beginthread`). It does use OpenMP (`vcomp140`) in texture precache at startup, where a "Texture not found" message box can appear on a worker thread. Mod init runs on the loader's `CreateThread` thread (the loader imports it; verified), not the game thread.
* Time freeze byte 0x143a11909 (Ghidra's old name `doRecoil_global`, now `g_bGameTimeFreezeFlag`) freezes only game time. All tasks still run, so it is not a barrier. The window proc and `Sleep` are not safe points either (reasons in the ds4-threads report, section 4.4).

## The game's own reload paths (verified unless noted)
* **Levels:** `SetLevelSeriaToLoad_` 0x14025afd0 only copies the name into `SeriaToLoad` 0x1403c1390 (and sets flags 0x143a11903/08). Next frame `SomethingPreTask` sees a non-empty `SeriaToLoad` and calls `reload_sg` 0x140240b90 -> `LoadSeriaFile` 0x140225930. `LoadSeriaFile` opens the file on every call (`fopen`), no cache, no mtime check. A failed load calls `ExitGame`; the name `exit` also calls it. `ExitGame` (0x140211e10, was `FUN_140211e10`) writes `Libraries/OL.seria` and `Config.ini`, then sets `g_bExitRequested` 0x143a11901.
* **Language:** `LoadDialogue` 0x1402253a0 frees the old table, re-reads and decrypts `Data/Dialogs/<language>.seria_enc`; the options language button runs it live.
* **Config.ini:** `ReadConfigIniFile` 0x140224c60 (was `FUN_140224c60`) re-reads and deserializes it, then calls `SetDefaultKeyBindings` 0x14018d3d0. Vanilla calls it only from `Main`. Whether re-running it overrides your key bindings is not verified. Writer: `WriteConfigIniFile` 0x14024d520.
* **Ship designs / parts (from the reports, not re-checked):** `get_filenames` 0x140212850 re-scans `Ships/` and `Objects/Designs/` when the shipworks screen is built; `parts.seria` is re-read on editor entry but only into the editor library, and leaving the editor writes it back.
* **Stats table (partly verified):** `GetStats` 0x140281e00 is a bounds-checked index lookup into `StatListBase` (verified). From the report: consumers re-read the record every tick (so in-place edits are hot); live parts store an index at Body+0x188, so reordering the file re-points every part to wrong stats; `Clear` skips class 0x803, so records leak.
* **Correction to our notes:** `m_stats=2051` is the class code, not a record count; the shipped `OL.seria` has 176 records and `parts.seria` 162 prototypes (report claim, count not re-checked).

## Mod side (patchy source verified, rest from the ds4-modside report)
* `patchy` (tag v0.1.0): installed patches are permanent, only address and size are kept, no original bytes, and a second patch over an installed range fails with `OverlappingPatch` (verified in `src/session.rs`). The Modloader's `bass.dll` imports `CreateThread` and `FreeLibrary`; its README and the report say mods are never unloaded (the Rust `mem::forget` itself was not checked from the binary).
* Class L (hot already): refuel `AtomicU32`, sell/zoom `static mut`, about a dozen atomics in hf_ally. Class C (code): feature toggles, elevation rules. Class D (game data surgery, leave alone): `planes`, loadouts, shop parts.
* Restoring patched bytes does not restore values: the three zoom globals are written by the game as a triple (not re-checked).

## Recommended path
1. **Stage 1, frame tap** (ds4-threads section 9): hook S1 with a log-only function; confirm one line per frame, one thread id different from `init`'s, and the blocking gap at scene loads.
2. **Config reload for class L** in the QoL fork and hf_ally: mtime check at S1 or on a hotkey, parse and validate a new config, swap statics in one block, keep old values on any error.
3. Optionally request a level re-read through `SeriaToLoad` for data edits (watch the failure path: a bad name exits the game and rewrites `OL.seria`/`Config.ini`).
4. Shim plus generation DLL only if 2 proves too limited; test it first with a throwaway mod pair (ds4-threads stage 2).
Do not use any of this on a save you care about before the stage-1 log is clean.

## Not determined
Whether `ReadConfigIniFile` is safe to re-run mid-game; the D3D11 device threading flag; what sets `HGE+0x978`; whether the video task uses its bool argument; meaning of `FUN_14000e430` (resets the intrusive list heads at 0x1403c6320..0x1403c6380, called on every level request; left unnamed), `FUN_1400beea0` (editor/shipworks entry, 3 args), flags 0x143a11903/08.
