# Probe runs 1-3 (debug DLL `hf_probe`, 2026-10-14)

A debug-only DLL that records what the game does while the user presses keys, hovers, clicks and drives. Goal: find the unknown variables (hover, selection, mode, cursor) by observation. **Not part of QoL.**

## The probe
* Crate `/home/maksim/Development_Highfleet/hf_probe` (local git, commit `7e7a0c0`), DLL `/home/maksim/Development_Highfleet/hf_probe_build/Modloader/mods/hf_probe.dll`, test steps in `hf_probe_build/TEST.md`. Output: `Modloader/probe.log` in the game dir (`/home/maksim/.local/share/Steam/steamapps/common/HighFleet/Modloader/probe.log`), written by its own buffered thread.
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
| The game warps the cursor itself and keeps its own virtual cursor | inference | [guess] until the recentring code or the virtual cursor global is found |
| `0x1403ef304`, `0x1403ef308`, `0x1403ef30c` are zeroed at the start of every `VideoTask`: per-frame counters, pure noise (they changed in about 3000 snapshots) | decompile + log | [code] |
| `0x1403c0e60`..`67` (a 10.0f timer and neighbours) and `0x143a1197c`..`7f` (a timer 0..9.8) also change by themselves | log | [game] |
| `0x143a11963` is `VideoTask`'s skip-one-frame flag and toggles on screen transitions | decompile + log | [code] |
| `0x143a11984` is `VideoTask`'s lighting index, nonzero only on the arcade-battle branch (`IS_IN_ARCADE_BATTLE` `0x147fc6fb7` or `0x147fc6f82`); it went 0 -> 6 at 50.97 s and 6 -> 0 at 75.80 s, bracketing the WASD keys, so **TEST drive runs the arcade-battle renderer branch** | decompile + log | [code]+[game] |
| `0x143a11964` became 1 on entering the editor (2 for the editor-from-menu case in `FUN_1400beea0`) | decompile + log | [code]+[game] |
| `0x147fc6fc4` stepped `0, 8, 9, 2, 1, 2, 3, 4, 0x64, 2, 0, 8->9` | log | [game], meaning unknown |
| `0x1403bd078` cycled 1..4 about every 0.25 s while LMB was held in TEST | log | [game], meaning unknown |
| `0x1403bd00c` flips at screen changes; `IS_IN_CAMPAIGN?` is `0x147fc6fd0` | log + symbol | [game]/[code] |
| `0x1403c0dc8` / `0x1403c0dcc` are floats that changed continuously (about -40..85) while the mouse moved | log | [guess]: candidate virtual cursor or grid position |

## Design flaws found in run 1 (fixed in v1.1; more in Run 2 below)
* The noise filter relied on F10, which was never pressed.
* Per-byte `MEM` lines are unreadable (3144 of 3257 lines).

## Run 2 (v1.1, 2026-10-14) [game]
* Installed probe: v1.1 (`hf_probe.dll`, 407,040 bytes, SHA-256 starts `d8f70b24`, the `hf_probe_build` copy) [file]. Log: `/home/maksim/.local/share/Steam/steamapps/common/HighFleet/Modloader/probe.log`, **1356 lines** (`MEM` 835, `MOUSE` 212, `KEY` 110, `NOISE` 89, `WHEEL` 53, `HELD` 29, `MODE` 21, `FOCUS` 4, `SPRITE` 1), about 190 s of play. Screenshots (2560x1440, Steam names carry the wall-clock time): `/home/maksim/Development_Highfleet/hf_probe_build/2026101413xxxx_N.jpg`.
* **Aligning screenshots with the log.** Probe `t = 0` is the wall-clock time of the probe's `running` line in the modloader log `Highfleet_2026-10-14_13-32-43.log`, i.e. `13:32:43`. A screenshot named `1333xx` is then at `t = xx - 43 s` (plus minutes). This is how the screens below were tied to `MODE` lines.

| Screenshot (wall clock / probe t) | Screen | Dispatcher branch at that time |
|---|---|---|
| `133302` / 19 s | main menu (title "HIGHFLEET, DEUS in NOBIS"; campaign, settings, editor, credits, exit) | "other" branch, renderer `0x14030f250` |
| `133308`..`133349` / 25..66 s | ship editor, HUD visible | editor branch, `0x140300db0` |
| `133410` / 87 s | ship editor with the **TEST panel** open ("TESTING GROUND": ENEMIES difficulty slider, SMALL / MID / LARGE / CARRIER, AMMO primary and secondary icons, FIGHT, LANDING) | editor branch; FIGHT then switched to the battle branch at 87.717 s |
| `133552` / 189 s | **fuel shop** (title "ТОПЛИВО", liquefied methane, 125000 gold, tonne slider, a city map, a gas-masked character, an exit button) | **battle branch**, `0x1403050a0` (between `MODE` battle at 185.375 s and menu at 190.078 s) |

So shop and dialogue-like screens run the **battle branch** of the dispatcher [game+code, by timeline]. The `MODE` names used by v1.1 (`map/campaign`, `battle/arcade`, `menu/hangar`) are **branch names, not screen names**. Example: at 13.369 s `map/campaign` fired for 0.17 s on the way to the main menu, a loading transition. v1.2 prints the renderer address and the raw flag bytes instead.

* **`MODE` timeline** (see also [render-pipeline.md](render-pipeline.md)): other 0.017; campaign branch 13.369..13.536 (transition); other 13.536; editor from 21.774; other 87.667, battle branch 87.717 (FIGHT in TEST) until 125.716; other then editor 125.783; other 127.314; campaign branch 150.988 (strategic map); other 175.718; battle 175.834; other 176.759; campaign 176.793; other 179.727; battle 179.845; other 180.654; editor 180.703; battle 185.375 (fuel shop); other 190.078; campaign 190.112. **Every screen change passes through the "other" branch for about 0.05 s** (a loading frame).
* **Mouse wheel works** [game]: `WHEEL` was read from `HGE+0x9f8` as `-1` or `+1` per notch, 53 times (editor palette scrolling). First time the wheel has been observed.
* `HGE+0x9fc` / `+0xa00` printed only `-1`, `0` or `1` in v1.1, but the probe formatted them with `{:.0}` (rounding), so "these are relative mouse deltas" is only a **[guess]** until v1.2 prints three decimals. The Windows cursor stayed at client `(960,540)` in a 2560x1440 client [game].
* **Pointer slots** [game; 32-bit matches of `MEM` values against the `HELD` pointers of the same log]: the dwords at `0x1403c0d58` and `0x1403c0d70` held the same pointer value as `held_part` `0x1403c0d88` (39 and 39 matches for `MDL_FERMA1X1_01`, 18 and 18 for `MDL_FERMA2X1_01`; `d88` itself 34 and 10). So `d58`, `d70` and `d88` are three part-pointer slots set when a part is picked (selected / target / held; roles unresolved). `0x1403c0db8` changed 249 times with heap pointers and matched a held pointer only 6 times: probably the **object under the cursor** [guess]. `0x1403c0d40` (`obj_c0d40`, 57 changes) is the object the editor's coordinate readout uses [guess]. The most-changing dwords overall: `0x1403c0db8`, `d58`, `dc0`, `dc4`, `d70`, `d60`, `d64`, `layer_078` (`0x1403bd078`), `0x1403c0d40`, `0x1403ef380` / `388`, `0x1403c0d48` / `4c`, `0x147fc6fc4`.
* **The sprite test draws** [game, user-confirmed]. The user marked it with an arrow (a ship built from hazard-sign hull parts) in `20261014133349_1.jpg`: `shpwrk_slide` scaled 0.3, centred at frame `(1300,980)`, is hidden **behind the palette buttons** (bottom bar, frame y about 990-1100). Fragments of the sprite and of its label text are visible in the gaps between the buttons. So `GetAnimation` + `RenderEx` work from the label-pass hook, and the palette buttons are drawn **after** the label pass. See [images-and-sprites.md](images-and-sprites.md).
* Input source: `SDL_PollEvent` in `InputTask` is only for joysticks in this build (details in [engine-hge.md](../engine-hge.md)); where the game accumulates its virtual cursor is still unknown.

## Run 3 (v2.0, 2026-10-14, 14:21:31) [game]
First run with the log-only entry hooks and the state watchers; QoL loaded with refuel and speed disabled. All four hooks installed, clean exit, 5432 log lines. Everything about it is in [ui-events-and-screens.md](ui-events-and-screens.md); the headlines:
* `CLICK`, `TEXT`, `SOUND`, `GOLD`, `LOCATION` and `FLEET` work and turn the memory-diff noise into events in words: which element was clicked, which text keys a screen asks for, which sounds play, when gold changes (validated by three shop purchases), which city the player is in, where the fleet is and how fast its fuel changes.
* **Correction to the click field name:** v2.0 printed the string at `gui+0xad8` as `action`. Its values (`gui_mil_focus`, `gui_red_opaq`, `gui_hud_white`, `editor_white`, `slider_green`) are **Distortion resource names** from `Media/Dst/distortion.res`, not actions and not Animation names [file]. v2.1 prints it as `fx`.
* **`LOAD` read the wrong argument:** the path is the second argument (a literal `Libraries/parts.seria` arrived there). Fixed in v2.1 (commit `f094dec`, not yet run in game).
* **Supersedes** the Run 2 line that shop screens "run the battle branch": the flags now say which screen it is (`bc8` city landing hub, `bc9` supplies / shop, `bd4` flight HUD after leaving the city shipworks, `bb7` combat); see the table in the new note and in [render-pipeline.md](render-pipeline.md).
* Logs are preserved at `/home/maksim/Development_Highfleet/hf_probe_build/logs/2026-10-14_1421_v2.0/` (`probe.log` is recreated at every game start).

## Lessons / blind spots [game]
* **The v1.1 auto-noise filter hid what we hunt.** It suppressed for good any byte that changed in more than 25% of the polls, and a cursor float that moves with the mouse crosses that line within seconds. So the virtual cursor is **not missing from memory; the probe filtered it out**. v1.2 writes a summary of the hidden dwords every 5 s (count, float min..max) and un-hides them when they calm down.
* 89 `NOISE` lines in the log (v1.2: at most one summary per 5 s).
* Per-byte output was unreadable. v1.1 groups dwords with hex, int and float and names known globals; **v1.2** also resolves pointers to part names (`ptr->MDL_...`) and adds a HUD **watch panel**: the pointers `d58`, `d70`, `held`, `db8` as part names, and the floats `0x1403c0dc0`..`0xcc`, `0x1403c0d60` / `64`, `0x1403ef380`..`8c`, next to the game's own `%i %i` readout. v1.2: commit `a999689` in `/home/maksim/Development_Highfleet/hf_probe`, built to `hf_probe_build` (hash starts `1537b0dd`); the sprite test moves to `(1500,700)` in free space.
* The F9 / F10 keys must not be required: noise handling has to work unattended.

## Unknowns
* Where the game keeps its **virtual cursor** (the arrow it draws). See the HGE input layout in [engine-hge.md](../engine-hge.md): `HGE+0x9fc/0xa00` is what the game's HGE layer sees, not necessarily the arrow.
* Meaning of `0x147fc6fc4` and `0x1403bd078`.
* ~~Whether the sprite test draws at all~~: it does (Run 2), hidden under the palette.
* The roles of the pointer slots `0x1403c0d58`, `d70`, `d88`, `db8`, `0x1403c0d40`, and whether `db8` is the hovered object (v1.2 resolves them to part names).
* Whether `DBG_LOG_DEPTH` in `Config.ini` gives a verbose `client.log` (see `../../ref/config-ini.md`).
* Map and battle HUD seams (flush sites listed in [render-pipeline.md](render-pipeline.md)); the `TEXT` callers of run 3 are the shortcut ([ui-events-and-screens.md](ui-events-and-screens.md)).

## Probe v1.1 plan
* Automatic noise filtering: hard-exclude `0x1403ef304`-`30f`, `0x1403c0e60`-`67`, `0x143a1197c`-`7f`; suppress addresses that change in more than about 25% of recent polls. F10 stays as an extra.
* A `MODE` line recomputed from the dispatcher flags, logged only on change.
* Readable `MEM` lines (hex / float / int, named globals), a verbose switch, a per-second cap.
* HGE mouse position (`HGE+0x9fc/0xa00`), wheel (`HGE+0x9f8`) and the key-state array (`HGE+0xa06`) instead of the OS cursor.
* HUD seams for map and battle after the RE below.
* Done in v2.0 (see Run 3): four log-only entry hooks (checked against the v2.0 source, commit `417667c`): the GUI click handler `0x14012f120`, the string lookup `0x1401ae090`, the sound-play function `0x1402e30e0` and the .seria loader `0x140225930`; the earlier plan of hooking `GUI::HandleClick` `0x14012d050` and `Editor_OnMouseWheel` `0x1400bc5e0` was not done. Function entries have RSP = 8 mod 16, so the hook needs an alignment wrapper.

## Live-test recipe
1. Run v1.1 in the editor, then the map, then a battle; press F9 before and after each action and write down what each pair of marks was.
2. Show `HGE+0x9fc/0xa00` next to the game's arrow on the HUD and compare; do the same with `0x1403c0dc8/dcc`.
3. Screenshot the editor with the probe HUD running to settle the sprite test.
4. Set `DBG_LOG_DEPTH=3` in `Config.ini` once (back it up first) and look at `client.log`.
