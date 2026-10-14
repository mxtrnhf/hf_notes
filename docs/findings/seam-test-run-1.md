# Seam test, run 1 (probe v2.2, 2026-10-14 18:01) [game, observed unless marked]

Goal: find where extra text can be drawn on the map, battle/city and menu screens, as the editor label pass (`0x140303fb4`) allows in the editor. Log: `hf_probe_build/logs/2026-10-14_1801_v2.2/probe.log`, probe `t = 0` is `18:01:09`.

## Method [code]
Probe 2.2 wraps every `call 0x140083b50` (flush) in three renderers with a trampoline: call the flush, then draw a label. 79 sites: map `M00..M18` (renderer `0x14030a6b0`, sites in [render-pipeline.md](render-pipeline.md)), battle `B00..B28` (`0x1403050a0`), other `O00..O30` (`0x14030f250`). Label = id in `fixed_16`, white, blend 2, at x=1890 right-aligned and x=760 left-aligned, y = 40 + 17 * id (a second column for ids from 40). `F7` toggles drawing; `SEAMS hits/5s` lines count hits per seam.

## Screens per renderer
* `0x14030a6b0` (flags `campaign_d0` / `campaign_d2`): strategic map **and** story dialogue scenes (over a blurred map).
* `0x1403050a0`: combat (`bb7`) **and** city, supplies, shop, repair screens (`bc8`, `bc9`, `bd4`).
* `0x14030f250`: main menu and difficulty screens. Editor-branch frames show labels only on transition frames.

## Which seams fire (hits over the run)
* Map: M00-M09, M11, M16-M18 every frame; M10 about 75 %; M12, M14, M15 only about 30 % (dialogue frames); M13 once (486 s). **Corrected by run 2 (below):** M13-M15 fire together when the Esc menu opens (run 1 saw them on dialogue frames too); M12 never fired in run 2.
* Battle/city: B00-B12, B16, B22-B24 every frame; B21 about 95 % (combat); B13 some frames (`bd4`, `bc8`); B17, B19, B20 only in `bc8` city screens; B14, B15, B18, B25-B28 never.
* Other: O19 and O20 about 8 times per frame (inner loop); O17 rare; O23 never.

## Visibility (from screenshots)
* Clean (readable, screen space, on top of the HUD): battle B21-B24, B16, B10-B12; city screens B22-B24, B16, B10-B12; map M11.
* B00-B09: faded or glitched (under glitch/blur layers).
* Map M16 and especially M17: **inside the glitch distortion pass**, labels glitch (user report).
* Map M08/M09: labels at wrong positions (about x 480-490, y 44 and 114 in 2000 px screenshot coordinates; a 70 px gap instead of 17 px), so a transformed layer [guess: map world space].
* M14-M16 visible on dialogue frames. (Partly corrected by run 2: M13-M15 were not visible in the Esc-menu screenshots.)
* **No clean map screenshot** (no dialogue, fleet flying) exists, so the best map seam is **not decided**.

## Static check (Ghidra read-only, objdump) [code]
After flush M05 (`0x14030c639`): `[0x1403bd09f]` is read at `0x14030c673`; if set, one global sprite is drawn (`0x1401725c0`) and flush M06 (`0x14030c721`) runs. The map has no `0x1400835a0` binds; it uses the bind variant `0x1400834e0` once.

## Other probe findings
* `FLEET`: pos, speed, heading, fuel/capacity doubles. Test ship speed 356.009 with custom 50*TWR (m/s presumably [guess]). On city/location screens the line shows 0/0 or reset values (pos 0,11000, speed 0), so the pointer is a re-initialised or other fleet then [guess].
* `LOCATION` record `0x211c67d0`: `+0xc8 "UR"`, `+0x130 "SARGAS"`, `+0x210 "MARK_INIT"`, `+0x25c` = 1.
* `GOLD` deltas: -18660, -18660, +37320, -15260 x2, -5900 (the last matches 118 shells at 50 each in the shop dialog).
* `TEXT` `LOCATION_NAME_*` keys are requested for every map city on the first map frame (caller `+0x1ae078`).

## Mod verification (user report) [game]
QoL refuel x10 (patches 200 -> 2000, 100 -> 1000) and custom speed 50*TWR (patch `0x140080699`) both visibly work ("insane"); elevation U / P / Backslash worked (floor 0..3 in the log). Refuel samples (1 Hz, docked): +102,000 fuel/s for several seconds, then +1,192,000 in one second; **not a clean A/B yet**.

## Run 2: map only (probe.json `seam_only` M10-M16) [game, observed]
Log: `hf_probe_build/logs/2026-10-14_run_map_clean_v2.2/probe.log`; 7 screenshots in `hf_probe_build/seams_screenshots_2` (real strategic map inside the cockpit frame, no dialogue: docked, flying, zoomed, panned, paused).
* **Seam ids in a filtered run are positions in the filtered list**, so y = 40 + 17 * position: M10 y=40, M11 y=57, M12 74, M13 91, M14 108, M15 125, M16 142. Labels are at x=760 (left aligned) and x=1890 (right aligned, over the launch-controls panel).
* **M11 and M16 are drawn on top of the whole cockpit frame, clean (no glitch), in fixed screen space**: same screen position while the map is panned, zoomed, paused and with the fleet flying; both x copies visible.
* **M10 was not visible anywhere**: hidden under the cockpit frame and panels at both x positions, although it fires about 75 % of frames [observed absence].
* M12 never fired in this run. **M13, M14, M15 first fired together at 99.379 s, when Esc was pressed** (the pause menu; text keys `CANCEL_BUTTON`, `SAVE_RP_BUTTON`, `LOAD_RP_BUTTON` appear at that moment); hits then ran about 44 and 188 per 5 s. They were not visible in the Esc-menu screenshots (drawn under the overlay).
* Corrects run 1: M12/M14/M15 are not simply "dialogue frames"; in run 1 they fired together on dialogue frames (`campaign_d2`) and M13 once at 486 s, in run 2 M13-M15 follow the Esc menu [guess: all belong to modal overlays].
* **Decision [observed, strong]: M11 = flush at `0x14030dae4` (index 11 of the map list) is the best map seam for screen-space text above the UI.** Second choice M16 = `0x14030e1a6`. In run 1 M16 and M17 glitched on dialogue frames while M11 stayed clean there too, so prefer M11. M10 is `0x14030da75`. The "no clean map screenshot" gap from run 1 is resolved.
* Keys seen as `KEY` lines: F7 toggles the labels (at 27.4, 28.0, 28.8, 29.0, 76.8, 77.1 s), Esc, WASD.

## Live-test recipe for the map seam
1. Install probe v2.2; copy `hf_probe_build/run_map_clean/Modloader/config/probe.json` (keeps M10-M16 only).
2. Take screenshots with **no dialogue open**: map docked; fleet flying; zoomed in and out; panned; a city selected; a panel open.
3. Per label: readable? at the right place? stable under zoom and pan? glitching? Pick the highest clean seam; prefer one that fires every frame (M10 and M12-M15 are conditional).
4. Check `SEAMS hits/5s` for that seam on the same screen.
