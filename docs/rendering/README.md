# How the game draws a frame, and how a mod draws text or sprites

A plain-language overview for someone who has never done this. It does not re-derive anything: every fact is linked to the note that proved it. Steam 1.163, image base `0x140000000`. Tags: legend in `../../README.md`. Sources: [render-pipeline.md](render-pipeline.md), [fonts.md](fonts.md), [images-and-sprites.md](images-and-sprites.md), [seam-test-run-1.md](../runs/seam-test-run-1.md), [editor-frame.md](editor-frame.md), [ui-events-and-screens.md](../runs/ui-events-and-screens.md).

## 1. The frame in one page
* **One frame function.** The game registers only a frame function (`_FrameFunc`, `0x1401a8970`) with HGE and no separate render function, so it draws inside the frame function. The last of its seven tasks is the video task `0x140316e20`. [code] ([render-pipeline.md](render-pipeline.md), [editor-frame.md](editor-frame.md))
* **One scene dispatcher.** The video task calls the scene dispatcher `0x140300c20`, which looks at the game-mode flags and calls exactly one renderer. [code]
* **Which renderer draws what.** The dispatcher has five targets; the first (mode parameter 1, `0x14030e670`) has not been matched to any screen. The other four:

| Renderer | Chosen when | Screens it draws |
|---|---|---|
| `0x14030a6b0` | campaign flags (`campaign_d0` / `campaign_d2`) | strategic map, and the story dialogue scenes over a blurred map [game] |
| `0x1403050a0` | battle/arcade flags (`bb7`, `bc8`, `bc9`, `bd4`, ...) | combat (`bb7`: TEST drive and real fights), landed city hub (`bc8`), supplies/shop and fuel purchase (`bc9`), flight HUD after leaving the city shipworks (`bd4`, meaning [guess]), repair screens [game] |
| `0x14030f250` | none of the above and `IsInEditor` = 0 | title screen / main menu, difficulty screens, and every loading frame between screens (0.05 to 0.3 s) [game] |
| `0x140300db0` | none of the above and `IsInEditor` = 1 | ship editor, TEST panel, city shipworks [game] |

  Branch names are not screen names; the flags say which screen it is. Details: [render-pipeline.md](render-pipeline.md) (dispatcher table, flag table), [ui-events-and-screens.md](../runs/ui-events-and-screens.md) (how each flag was tied to a screen by the clicks before it).
* The fonts and sprites are stock HGE objects (`hgeFont`, `hgeSprite`) modified by the game, so drawing needs no new engine knowledge, only the right moment. [code]

## 2. What a "seam" is
The frame is drawn in **layers**: background, map, cockpit frame, glitch (distortion) effect, then the UI [observed from where the test labels landed, section 4]. Each renderer binds a render target, draws a layer into it, and then calls the **flush** function `0x140083b50` ([code], called `checkD3DEngineStatus_` in the editor context in [render-pipeline.md](render-pipeline.md)). After the flush the layer is on its way to the screen and the next layer is drawn on top.

A **seam** is the place right after one of those flush calls (an `E8 rel32` call) where a mod can run its own code and draw text or a sprite. Which seam you pick decides what ends up above or below your drawing:
* **Too early**: layers drawn later (cockpit frame, UI) paint over your drawing. Example: map seam M10 is hidden under the cockpit frame; the editor seam `0x140303fb4` is under the palette buttons. [game]
* **Inside the glitch layer**: your drawing is distorted along with the game's. Example: map seams M16/M17 on dialogue frames. [game]
* **After the UI** (or in a layer with nothing drawn over it): your drawing sits cleanly on top, in fixed screen space. Example: map seam M11. [game]
* **After the whole renderer returns**: nothing appears. Drawing from a hook on the call to the whole editor renderer (`0x140300d63`) never reached the screen, although the draw calls ran; the editor label-pass call is the one that works. [game] ([render-pipeline.md](render-pipeline.md), attempts 1 and 2)

## 3. Recipe: draw text and sprites
**Text** (proven, [game] by the elevation hint; [fonts.md](fonts.md), [render-pipeline.md](render-pipeline.md)):
1. Get the font by name: `GetFont(manager, name)` at `0x1401703e0`, where `manager` is the pointer stored at `0x143a119e8` (`Media.res`). Probe: `read(MEDIA_RES)` then `get_font`. [code]
2. Style it with the helper `0x1401a8710(name, float scale, int blend, uint color)`: it fetches the font, sets scale (`+0x100c`), blend (`+0x1028`) and colour (`+0x1020`, only when non-zero); blend 2 is the default. [code]
3. Draw with `0x14016eb40(font, x, y, align, text, null, null, 0, 0.0)`. `align`: 0 left, 1 right, 2 centre. `y` is the top of the line. [code][game]
4. Fonts are **shared objects** that every caller restyles: save `+0x100c`, `+0x1020`, `+0x1028` before and restore after (the probe does exactly this in `seam_tick`). [code]
5. Coordinates are the **virtual 1920x1080 frame**, scaled uniformly to the screen (checked on a 2560x1440 16:9 screenshot only). [game]
6. Text must be **ASCII**; `\n` and `@` break lines (the probe replaces `@` and NUL by spaces). Only a few fonts are digits-only: `dinpro_200_black`, `nixies_30`, `radio_20`. [code] ([fonts.md](fonts.md))
7. **Fonts available**: 58 declared in `Media/Fnt/fonts.res` plus one undeclared (`flash_large_shadow_special`); full list, metrics and looks in [fonts.md](fonts.md). Chosen for the elevation hint: `fixed_16`, white `0xffffffff`, scale 1.0, blend 2, right-aligned at x=1880, y=24 [user decision]. The editor itself uses `dinpro_14_bold` (colour `0xff73604c`), `dinpro_45_black`, `pollock_52`, `flash_large`, `vcr_21`. [code]

**Sprites** ([images-and-sprites.md](images-and-sprites.md)):
1. Every image is an `Animation` resource defined in `Media/Tex/*.res`. Fetch with `GetAnimation(manager, name)` at `0x140170230` (same manager). [code]
2. Draw with `RenderEx(sprite, x, y, rot, hscale, vscale)` at `0x140172aa0` (or `Render(sprite, x, y)` `0x1401725c0`; the decompiler lost the `RenderEx` parameter types, they are as in stock HGE). The hotspot is the centre of the rect, so x/y place the centre. [code]
3. Confirmed on screen: `GetAnimation("shpwrk_slide")` plus `RenderEx` at scale 0.3 from the editor hook drew (it was hidden behind the palette buttons at (1300,980)). [game] Animations are shared: save and restore vertex colour if you tint.

**The working hook (editor)** [game]: wrap the `E8 rel32` call at **`0x140303fb4`** (bytes `E8 C7 03 DD FF`, it calls the label pass `0x1400d4380`) with a `patchy::Trampoline`: `absolute_call` the original, `preserved_call` your function, `relative_jump` to `0x140303fb9`. Check the 5 bytes first and skip on a mismatch. Never use `save_overwritten` on a rel32 call. In the probe this is `install_hud` (`HOOK_SITE`, `HOOK_BYTES`, `HOOK_TARGET`). The same trampoline shape wraps any flush call: the probe's `install_seams` checks that byte 0 is `0xE8` and that the call target is `0x140083b50`, then calls the flush and then `seam_tick`. [code]

**A second route**: instead of drawing from a seam, create a real GUI object the game draws and clicks itself: [gui-elements.md](gui-elements.md) (proven on the pre-combat screen). **Which seam where** is in section 4. Drawing only shows while a scene is being rendered, so always draw from inside a seam, on the render thread. [code]

## 4. Best seams per screen
Seam ids are `M` (map renderer `SEAMS_MAP`, 19 sites), `B` (battle `SEAMS_BATTLE`, 29) and `O` (other `SEAMS_OTHER`, 31); the number is the zero-based index in that array in `hf_probe/src/lib.rs` (addresses below were checked against it) [code]. Evidence: [seam-test-run-1.md](../runs/seam-test-run-1.md).

| Screen | Seam | Call address | Status |
|---|---|---|---|
| Strategic map | **M11** (best) | `0x14030dae4` | **confirmed clean** [game]: on top of the whole cockpit frame, fixed screen space while panned, zoomed, paused, fleet flying; also clean on dialogue frames; fires every frame |
| Strategic map | M16 (second) | `0x14030e1a6` | **confirmed clean** on the clean-map run (run 2); but it glitched on dialogue frames in run 1, so prefer M11 [game] |
| Strategic map | M10 | `0x14030da75` | **do not use**: hidden under the cockpit frame and panels [game] |
| Strategic map | M17 | `0x14030e25c` | **do not use**: inside the glitch distortion pass [game] |
| Strategic map | M08, M09 | `0x14030d620`, `0x14030d935` | **do not use**: labels at wrong positions, transformed layer (world space, [guess]) [game] |
| Strategic map | M13-M15 | `0x14030dd61`, `0x14030ddc8`, `0x14030dfd9` | fire only with the Esc menu; not visible in screenshots (under the overlay) [game] |
| Combat and city / shop / repair | B22, B23, B24 | `0x140309327`, `0x140309408`, `0x140309897` | **clean on screenshots** [game]; fire every frame; B24 is the latest of them in draw order, so likely topmost [guess] |
| Combat and city / shop / repair | B16 | `0x140308724` | clean on screenshots [game] |
| Combat and city / shop / repair | B10, B11, B12 | `0x140307a52`, `0x140307de1`, `0x140307fb5` | clean on screenshots [game] |
| Combat only | B21 | `0x14030915f` | clean in combat, fires about 95 % of frames [game] |
| Combat and city | B00-B09 | `0x1403063f7` .. `0x1403078fc` | faded or glitched (under glitch/blur layers); **do not use** [game] |
| Main menu, difficulty screens | O24, O25, O28 | `0x140312fb0`, `0x1403131a9`, `0x140313518` | labels looked visible, **weak evidence**: the run-1 note records no per-seam screenshot verdict for the menu, only that the three fire during the menu frames (first seen at 12.8 s) [observed, weak]; **not yet tested** with a deliberate screenshot |
| Main menu | other O seams | | not yet tested; O19/O20 fire about 8 times per frame (inner loop) and O23 never [game] |
| Ship editor, city shipworks | label-pass call | `0x140303fb4` | **confirmed working** (text and sprite), but drawn under the palette buttons; the top-right area is free [game] |
| Landing sequence (`bd4`), other battle-branch screens | B13, B17, B19, B20 | `0x140308117`, `0x1403088b2`, `0x140308a0d`, `0x140308c09` | fire only on some screens (B13 in `bd4`/`bc8`; B17/B19/B20 in `bc8` city screens); visibility not tested |

Not seen at all: B14, B15, B18, B25-B28 never fired. [game]

## 5. Glossary
* **Seam**: a call site just after a flush call where a mod can draw (section 2).
* **Flush**: the game's function `0x140083b50`, called after each layer is drawn; 19 call sites in the map renderer, 29 in the battle renderer, 31 in the menu renderer (the 79 probe seams). [code]
* **Bind**: selecting the render target to draw into: `0x1400835a0` in the editor and battle renderers (three binds in the battle renderer), the variant `0x1400834e0` in the map renderer. A layer is bind, draw, flush. [code]
* **Renderer branch**: which of the dispatcher's targets runs this frame (section 1). Not the same as the screen name.
* **Label pass**: the function `0x1400d4380` that draws the editor's text labels; reached from the editor renderer and also from the non-editor branch `0x14030f250`. Its call site `0x140303fb4` is the editor seam. [code]
* **Virtual 1920x1080 frame**: the coordinate space of `x`/`y` for text and sprites, scaled to the real window. [game]

## 6. Testing a seam with the hf_probe seam test
The seam test is in `hf_probe` v2.2 (`$HF_DEV/hf_probe`; built DLL `hf_probe_build/versions/hf_probe_v2.2.dll`). It wraps the flush calls and draws the seam id (for example `M11`) in `fixed_16`, white, after each one. The highest visible label in a screenshot is the topmost seam. [code]
1. Put the DLL in `Modloader/mods/` and a `Modloader/config/probe.json` next to the others. Keys: `seam_test`, `seam_map`, `seam_battle`, `seam_other` (group switches) and `seam_only` (a list such as `["M10","M11","M16"]`; empty means all enabled groups); `seam_key` defaults to `F7`. The example used for the map run is `hf_probe_build/run_map_clean/Modloader/config/probe.json`: `{"seam_battle": false, "seam_other": false, "seam_only": ["M10","M11","M12","M13","M14","M15","M16"], "sprite_test": false}`. [code][game]
2. Start the game, go to the screen under test, and take screenshots with nothing else open (no dialogue unless that is the case under test).
3. **F7 toggles drawing** on and off (`SEAM drawing on/off` in `probe.log`), so an A/B screenshot pair shows exactly what the labels cover. [code]
4. Read the label positions: each id sits at y = 40 + 17 * position in the **filtered** list (not the global id), at x=1890 right-aligned and x=760 left-aligned. For ids from 40 up the right column moves 90 px left and the left column 90 px right per block of 40. [code][game]
5. Judge per label: readable, in the right place, stable under zoom and pan, not glitching, above the UI. Also check `SEAMS hits/5s` in `probe.log` (a seam that never fires on your screen is useless; one that fires only with a modal overlay is conditional). `SEAM <id> first frame` lines show when each seam first fires. [code]
6. The probe log is written to `Modloader/probe.log` (default `log_path`); runs so far were copied into `hf_probe_build/logs/`.

Next tests wanted: a deliberate screenshot of O24/O25/O28 on the menu and difficulty screens; B21-B24 on a city shop screen versus combat; every non-16:9 resolution for the 1920x1080 frame; the layer order of the battle seams between B12 and B22. [guess]
