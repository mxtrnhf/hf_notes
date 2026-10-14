# How the game draws: frame, video task, scene dispatcher, text

Question: where can a mod draw its own text (the elevation hints) so it looks native and lands in the same pass as the game's labels? Steam 1.163, image base `0x140000000`. Tags: legend in `../../README.md`. Ghidra stayed read-only.

## Frame and video task [code]
`Init_HGE` (`0x1401ad080`) registers only `HGE_FRAMEFUNC` = `_FrameFunc` (`0x1401a8970`); there is no `HGE_RENDERFUNC`, so the game renders inside the frame function. Task order in `_FrameFunc`:

| Task | Address |
|---|---|
| Pre | `0x140286e40` |
| Physic | `0x140286380` |
| Input | `0x14018dbf0` (reads the editor held-part global `0x1403c0d88`) |
| AI | `0x140011180` |
| Game | `0x140127590` |
| Sound | `0x1402dd890` |
| Video | `0x140316e20` (takes a "render this frame" bool from a frame-skip heuristic) |

`SomethingVideoTask` calls the **scene dispatcher `0x140300c20`** as `f(DAT_14800ee28, DAT_14800ee20, 0, 0)`. Ghidra calls it `rep_1402d5b50_WriteToClientLog`. It is anchored by the error string `D:\!ESSENTIALS\PROJECTS\HYBRID FLEET 2013EX\VideoTask.cpp` (line `0x2849`) in its branch for an unexpected mode. The scene dispatcher and all four screen renderers reference that string, so this code lives in VideoTask.cpp; see [source-file-names.md](source-file-names.md) for the per-file function cross-reference. It first sets render state on the shader objects (`DAT_143a13960`, `DAT_143a13a20`), then dispatches on `param_4` and the game-mode flags:

| Condition | Renderer |
|---|---|
| `param_4 == 1` | `0x14030e670` (Ghidra `cosf`) |
| campaign map (`IS_IN_CAMPAIGN_` or `BOOL_147fc6fd2`) | `0x14030a6b0` (Ghidra `New`) |
| battle/arcade flags (`DAT_147fc6fc8`, `DAT_147fc6fd4`, `IS_IN_ARCADE_BATTLE`, `DAT_147fc6f82`, `DAT_147fc6fda`, `BOOL_147fc6fdb/dc/dd`, `DAT_147fc6fc9`) | `0x1403050a0` (Ghidra `pow`) |
| otherwise, `IsInEditor == 0` | `0x14030f250` (Ghidra `pow`) |
| otherwise, `IsInEditor != 0` | `0x140300db0` (Ghidra `pow`) |

`IsInEditor` is `0x1403ef368`, the same editor-active flag the elevation mod polls. The call to `0x140300db0` is at **`0x140300d63`**, bytes `E8 48 00 00 00` (rel32).

Both `0x140300db0` and `0x14030f250` call the **label pass `0x1400d4380`** (body `0x1400d4380`-`0x1400d6f63`, Ghidra `rep_1400cf430_VCRUNTIME140.DLL::memmove`; the number in a `rep_` name is the 1.151 address, see `setup.md`). So call it "the shipworks/editor label pass, also reached from the non-editor branch", not simply "the editor draw". `0x1400d6f70` (body to `0x1400da61c`) is a second label function called from it. The 38 KB `FUN_1400c7400` is the editor GUI **builder**, run once when the editor opens; it draws nothing.

Rest of `SomethingVideoTask` [code, shallow]: it drives shader parameters with `compareAndUpdateFloatArray_` on GUI objects (`DAT_143a139a8`, `DAT_143a13a20`, `DAT_143a139d0`, `DAT_143a13a58`), binds targets with `FUN_1400835a0`, renders sprites such as `DAT_14800ee20` with `FUN_1401725c0`, and scales to the window when `ScreenWidth`/`ScreenHeight` differ from `graphicsFrameWidth`/`graphicsFrameHeight`. [guess] The level is drawn to an internal target, post-processed through the shader objects, then composited to the backbuffer with letterboxing; not confirmed until the renderer callees are read.

## The text path is stock `hgeFont` [code]
The font object matches `hgefont.h` field for field (64-bit: `hTexture` is 8 bytes):

| Offset | Field | Offset | Field |
|---|---|---|---|
| `+0x8` | `letters[256]` (sprite pointers) | `+0x1014` | `fRot` |
| `+0x808` | `pre[256]` | `+0x1018` | `fTracking` |
| `+0xc08` | `post[256]` | `+0x101c` | `fSpacing` |
| `+0x1008` | `fHeight` | `+0x1020` | `dwCol` |
| `+0x100c` | `fScale` | `+0x1024` | `fZ` |
| `+0x1010` | `fProportion` | `+0x1028` | `nBlend` |

| Address | Is | Notes |
|---|---|---|
| `0x14016eb40` | `hgeFont::Render`, modified | `(font, x, y, align, text, float* out_w, float* out_h, ?, float angle)`. Adds `@` as a line break (besides `\n`), a rotation argument and width/height outputs. Line height `int(fHeight*fScale*fSpacing)`; glyphs go through `RenderEx(fx, y, fRot, fScale*fProportion, fScale)` as in `hgefont.cpp`. `align & 3`: 0 left, 1 right, 2 centre. |
| `0x14016f290` | `hgeFont::printf` | `vsprintf` into the global 0x3ff-byte buffer `0x1439e8240`, then `Render` with angle 0. |
| `0x14016f120` | `hgeFont::SetColor` | loops the 256 letters. |
| `0x14016f0c0` | `hgeFont::SetBlendMode` | sets `+0x1028` and each sprite `+0x168`. |
| `0x1401a8710` | get-font-and-style helper `(name, float scale, int blend, uint color)` | `GetFont` through `Media_res`, sets `fScale`, `SetBlendMode`, `SetColor` if `color != 0`, returns the font. |
| `0x1401703e0` | `hgeResourceManager::GetFont` | `CopyNameIntoMedia_(mgr, 9, name)` then vtable slot 1; 9 is `RES_FONT` in `resources.h`. |
| `0x140172aa0` / `0x1401725c0` | sprite `RenderEx(sprite, x, y, rot, hscale, vscale)` / `Render(sprite, x, y)` [likely] | `0x140172ee0` role unknown. |
| `0x1401ae090` | localised string lookup `(std::string* out, key)` | FNV-1a 64 (`0xcbf29ce484222325`, prime `0x100000001b3`) into the table `DAT_143a1c3b8`/`DAT_143a1c3a8`, mask `DAT_143a1c3d0`. |

`Media_res` is an `hgeResourceManager` built from `Media/media.res`.

## Fonts in the label pass [code]
The editor label pass sets `R14` at `0x1400d445e`/`0x1400d4463` from `0x1401a8710("dinpro_14_bold", scale from XMM13, 2, 0xff73604c)` (name string at `0x14035bdc0`). Neighbouring calls use `dinpro_45_black` (`0x14035bdb0`, `0xff73604c`), `flash_large` (`0x14035bdd0`, `0xffffffff`) and `vcr_21` (`0x14035bddc`, `0xffffffff`). The blend 2 is `BLEND_DEFAULT` in `hge.h`.

Fonts are **shared, mutable objects** and callers restyle them (scale, blend, colour) before drawing. A mod must either fully restyle before drawing or save and restore `+0x100c`, `+0x1020`, `+0x1028`.

Fonts defined in the game's `Media/Fnt/fonts.res` (**58 declared plus one undeclared `.fnt`**, `flash_large_shadow_special`; full table, metrics, looks and usage in [fonts.md](fonts.md)): B52_18, B52_26, courier, courier_28, dinpro_10_med, dinpro_14_bold, dinpro_14_med, dinpro_14_reg, dinpro_16_med, dinpro_18_black, dinpro_18_black_shadow, dinpro_18_med, dinpro_200_black, dinpro_20_black, dinpro_20_bold, dinpro_20_reg, dinpro_25_bold, dinpro_25_bold_blured, dinpro_30_black, dinpro_30_reg, dinpro_32_bold, dinpro_45_black, dinpro_48_black, dinpro_48_black_blured, dinpro_80_black, elizabeth_16, fixed_16, fixed_20, fixed_50, flash_large, flash_large_shadow, flash_small, fun_crayon, georgia_15, impact_18, impact_24, myriad_10, myriad_15, myriad_40, nixies_30, olga_24, pollock_100, pollock_20, pollock2_52, pollock_30, pollock_38, pollock_52, pollock_60, pollock_80, radio_20, son_45_blured, sourcepro_14_bold, vcr_12, vcr_14, vcr_16, vcr_21, vcr_30, vcr_40.

## Drawing recipe and hook seam [game]
1. `font = 0x1401a8710("dinpro_14_bold", scale, 2, 0xAARRGGBB)`.
2. Call `Render` directly: `0x14016eb40(font, x, y, align, text, null, null, 0, 0.0)`. This avoids the Win64 vararg rules of `printf` and format-string injection from a part id containing `%`.
3. Glyphs are drawn immediately, so output only appears while the scene is being rendered.
4. Seam: wrap the `E8 rel32` call at **`0x140303fb4`** (bytes `E8 C7 03 DD FF`, calls the label pass `0x1400d4380`) with a `patchy::Trampoline` (`absolute_call` the original, `preserved_call` ours, `relative_jump` to `0x140303fb9`). Never use `save_overwritten` on a rel32 call (patchy copies the bytes verbatim). Wrapping the call at `0x140300d63` instead draws nothing visible (below).

## Live test (debug DLL `hf_draw_test`)
Crate `$HF_DEV/hf_draw_test` (local git, commit `45b477c`, no remote; built DLL in `hf_draw_test_build/Modloader/mods/`), Rust + `patchy::Trampoline`, installed by the user on the Steam 1.163 install next to `highfleet_qol.dll`. Per editor frame it draws four yellow lines with `dinpro_45_black`: font from `GetFont` `0x1401703e0` on `Media.res` `0x143a119e8` (that pointer is the resource manager and works), style via `0x1401a8710(name, 0.5, 2, 0xffffff00)`, text via `0x14016eb40 Render(font, x, y, align, text, null, null, 0, 0.0)`, then the style is restored from the saved `+0x100c`/`+0x1020`/`+0x1028`. Lines: `QOL TEST left (100,100)` align 0, `QOL TEST centre (960,540)` align 2, `QOL TEST right (1820,1000)` align 1, `frame N` at (100,200).

**Hook at `0x140300d63`** (the call to the editor renderer `0x140300db0`; original call first, then ours). Screenshot `$HF_DEV/hf_draw_test_build/Screenshot_20261014_123328.png`.
* Log: `hook installed at 0x140300d63`, `first editor frame, font 0x1b93b780, scale 1, colour 0xff73604c, blend 2` [game]. The hook ran, the font was found and already carries the editor's own style (colour `0xff73604c`, blend 2).
* **No test text visible** [game]. The QoL GDI overlay is visible top-left and reads `ELEVATION  U up  P down  Backslash auto` (the configurable keys work).
* Likely reason [guess]: the editor labels are drawn into an offscreen target that is flushed and composited inside `0x140300db0`, so output issued after it returns is lost.

**Code sequence inside `0x140300db0`** [code, call-site context only]:
| Address | Call | Meaning |
|---|---|---|
| `0x140303faf` | `0x1400835a0(rcx=[0x143a13950], rdx=R13, r8=0, r9b=1)` | bind target R13 |
| `0x140303fb4` | `0x1400d4380` | **label pass** |
| `0x140303fc2` | `0x140083b50(rcx=[0x143a13950], dl=1)` | flush / status check (`checkD3DEngineStatus_`) |
| `0x14030402e` | `0x140083450(rcx=[0x143a13950], rdx=[0x143a13a20], r8=R13, r9=[0x14800eed8], 0)`, gated by byte `[0x1403bd0a0]` | looks like draw-target-through-shader / composite [guess] |

The whole bind, labels, flush block is skipped when byte `[0x1403bd09f]` is 0 (`JZ` at `0x140303f9d`). That byte has only **read** xrefs (`0x140303f96` in the editor renderer, `0x14030c673` in the campaign renderer `0x14030a6b0`, `0x1403124b8` in `0x14030f250`), no writer, and is 1 in the process dump together with its neighbours `0x1403bd098`..`0x1403bd0a3` (all 1) [code]. So it is a static "layer enabled" flag, not a UI-hide toggle, and the block runs in the editor every frame; the neighbouring flags are probably per-layer switches [guess].

**Hook at `0x140303fb4`** (the call to the label pass; original call first, then ours). Screenshot `$HF_DEV/hf_draw_test_build/screenshot_working.png` (2560x1440, 16:9).
* Log: `hook installed at 0x140303fb4`, `first editor frame, font 0x1ae0c820, scale 1, colour 0xff73604c, blend 2` [game].
* All markers visible and sharp, `frame N` counting (345 in the shot) [game].

| Finding | Tag |
|---|---|
| Text drawn after `0x140300db0` returns never reaches the screen, although the draw calls ran | [game] |
| Wrapping the label-pass call at `0x140303fb4` draws visibly | [game] |
| `x`/`y` are the 1920x1080 virtual frame scaled uniformly to the screen (screenshot shown at 2000x1125, factor 1.0417: left text edge about 104 for x=100, centre text centred at about 1000 for 960, right text ends at about 1895 for 1820) | [game], 16:9 only |
| `align` 0/1/2 = left/right/centre as in stock HGE; `y` is the top of the line | [game] |
| The right marker is partly hidden behind the last bottom palette button, so the palette buttons are drawn after (over) the label pass; the text is drawn over the ship/part area | [game] |
| `Media.res` `0x143a119e8` works as the resource manager for `GetFont`; `[0x143a13950]` is the renderer object passed to bind and flush | [game] / [code] |
| Style and restore every frame did not visibly change the game's own labels (stats panel colours normal in attempt 1) | [game], weak evidence |

## Built: native elevation hint
Shipped in the QoL fork `elevation` branch ([../mods/elevation.md](../mods/elevation.md)).
* Draw in the `0x140303fb4` hook with a game font at scale 1, in a free region. The shipped hint uses `fixed_16` (see 'Font decision' below and [fonts.md](fonts.md)); the editor's own label font is `dinpro_14_bold`, scale from the editor, blend 2, colour `0xff73604c`. Region: top-right looked free in the screenshots; avoid the top-left SAVE/LOAD row and the bottom palette.
* Do the key edge detection and the `m_floor` writes in the same game-thread hook, which retires the polling thread, the race and the GDI window (done in `hint: native`; the window stays as the `hint: window` fallback).
* `GetAsyncKeyState` is global, so also check that the game window is in the foreground.
* Pre-check the 5 bytes at `0x140303fb4` before preparing the patch and skip the hint on a mismatch (see `../hooks.md`).

## Unknowns
* Whether the label-pass hook behaves the same when the editor is entered from the main menu versus the hangar (the hint was seen in all editor states of one session, [../mods/elevation.md](../mods/elevation.md)).
* Whether the composite description of `0x140083450` (table above, `[guess]`) is right.
* Whether restyling and restoring a shared font disturbs the game's own labels (screenshots looked normal; weak evidence).
* Coordinate space on screens that are not 16:9 (it is the 1920x1080 virtual frame on 2560x1440 [game]); VideoTask letterboxes when screen and frame sizes differ, text should follow the frame target but is unproven.
* Whether every game caller restyles the font before use.
* Whether any state drops draws when no scene is open (stock HGE batches quads and drops them outside a scene; this game's renderer is unknown).
* Next RE chunk: the sprite path (`0x1401725c0`, `0x140172aa0`, `0x140172ee0`), the renderer object behind HGE slot `+0x2e8`, the target bind `0x1400835a0`, the shader setters (`FUN_1400a0320`, `FUN_1400a0010`, `compareAndUpdateFloatArray_` `0x1400a04e0`).

## Live-test recipe
1. Draw a test string from the wrapped call at `0x140303fb4` (as `hf_draw_test` does) on a 4:3 or 21:9 setup and in the other editor states (part held, test drive, dialogs, save/load screen).
2. Log-only detour on `0x14016eb40` printing font, `x`, `y`, align and text for editor frames.

## Font decision [user decision]
The hint uses `fixed_16`, white `0xffffffff`, scale 1.0, blend 2, right-aligned at x=1880, y=24; `dinpro_14_bold` (the editor's own font) was too bold and not pixel-like enough (screenshot `$HF_DEV/hf_draw_test_build/screenshot_working_2.png`). `fixed_16` was picked after a 20-font live sampler ([game], `screenshot_font_test.png` in the same folder). Every game font is ASCII only; see [fonts.md](fonts.md).

## Map and battle renderers: flush sites, state bytes [code]
Data only. The label-pass equivalents of the editor's bind, labels, flush pattern (`0x140303faf` / `fb4` / `fc2`) are not found for these renderers.

* Map renderer `0x14030a6b0` (Ghidra `rep_1402df4f0_New`) calls the flush `0x140083b50` at 19 `E8 rel32` sites: `0x14030bb28`, `0x14030bda8`, `0x14030be50`, `0x14030bf37`, `0x14030c13b`, `0x14030c639`, `0x14030c721`, `0x14030caba`, `0x14030d620`, `0x14030d935`, `0x14030da75`, `0x14030dae4`, `0x14030dc7d`, `0x14030dd61`, `0x14030ddc8`, `0x14030dfd9`, `0x14030e1a6`, `0x14030e25c`, `0x14030e2cf`. The label-gating flag `0x1403bd09f` is read at `0x14030c673` there.
* Battle renderer `0x1403050a0` (Ghidra `rep_1402da020_...pow`) has 29 flush sites from `0x1403063f7` to `0x140309c17` and only three target binds `0x1400835a0`: `0x14030627e`, `0x14030930c`, `0x140309bf5`.
* Also: `0x14030e670` (mode parameter 1) and `0x14030f250` (the non-editor branch).

### Mode timeline and screens (probe run 2) [game]
Dispatcher branches (`0x140300c20`) seen over about 190 s: other 0.017 s; campaign branch 13.369..13.536 (a loading transition on the way to the main menu); other; editor from 21.774; other 87.667, **battle branch** 87.717 (FIGHT in the TEST panel) until 125.716; editor 125.783; other 127.314; campaign branch 150.988 (strategic map); other 175.718, battle 175.834; other 176.759, campaign 176.793; other 179.727, battle 179.845; other 180.654, editor 180.703; battle 185.375 (**fuel shop**); other 190.078; campaign 190.112. **Every screen change passes through the "other" branch for about 0.05 s** (a loading frame).
* **Branch names are not screen names.** Main menu = "other" branch (screenshot `133302`, probe t 19 s). Editor and the **TEST panel** ("TESTING GROUND": ENEMIES difficulty slider, SMALL / MID / LARGE / CARRIER, AMMO primary and secondary, FIGHT, LANDING; screenshot `133410`, t 87 s) = editor branch. The **fuel shop** screen (screenshot `133552`, t 189 s) = **battle branch** [game+code, by timeline]. The flags say which screen it is (table below); shop and landing screens are the battle branch with `bc8` / `bc9` set, not a generic "battle".
* Screenshot alignment: probe `t = 0` is `13:32:43` (modloader log `Highfleet_2026-10-14_13-32-43.log`); details in [probe-run-1.md](probe-run-1.md).
* The editor label pass is drawn **under** the palette buttons: a sprite and text drawn from the hook at `0x140303fb4` at frame y about 990-1100 are hidden behind the bottom palette (see [images-and-sprites.md](images-and-sprites.md)).

#### Flag to screen (probe run 3, v2.0) [game]
Anchored by the clicks logged just before each change; details, text keys and the timeline in [ui-events-and-screens.md](ui-events-and-screens.md). Flags are bytes in the `0x147fc6f80..` region read by the dispatcher.

| Branch and flag | Screen |
|---|---|
| other (`0x14030f250`) | title screen and every loading frame (0.05 to 0.3 s between screens) |
| editor (`IsInEditor` `0x1403ef368` = 1) | ship editor, TEST panel and the city shipworks |
| battle, `bb7` (`IS_IN_ARCADE_BATTLE` `0x147fc6fb7`) | combat (TEST drive and real fights) |
| campaign, `campaign_d2` then `campaign_d0` (`0x147fc6fd2`, `0x147fc6fd0`) | strategic map |
| battle, `bc8` (`0x147fc6fc8`) | landed in a city: landing hub with event / dialogue text |
| battle, `bc9` (`0x147fc6fc9`) | supplies / shop screen, also the fuel purchase |
| battle, `bd4` (`0x147fc6fd4`) | flight HUD after `ED_SHPWRK_LAND`: landing / take-off arcade sequence [guess] |

### Seam test, probe v2.2 (2026-10-14) [game, observed]
Probe 2.2 wrapped all 79 flush calls (map M00-M18 = sites above in order, battle B00-B28, other O00-O30) and drew a label after each. Full results and recipe in [seam-test-run-1.md](seam-test-run-1.md). Summary:
* Map renderer `0x14030a6b0` also draws the **story dialogue scenes** (over a blurred map); battle renderer `0x1403050a0` draws combat **and** the city, shop, supplies and repair screens; `0x14030f250` draws the main menu and difficulty screens.
* Clean screen-space seams (observed): battle and city **B22-B24, B16, B10-B12**; map **M11**. B00-B09 are faded or glitched; **M16 and M17 are inside the glitch distortion pass** (labels glitch); **M08/M09 labels landed at wrong positions** (transformed layer, [guess] world space).
* **Best map seam decided by run 2 [game]: M11 = flush call `0x14030dae4`** (clean, above the cockpit frame, fixed screen space, also clean on dialogue frames); second M16 = `0x14030e1a6`. M10 (`0x14030da75`) is hidden under the cockpit frame; M13-M15 fire only with the Esc menu. Details in seam-test-run-1.md, Run 2.
* [code] After flush M05 (`0x14030c639`) the gate flag `0x1403bd09f` is read at `0x14030c673`; if set, one global sprite is drawn (`0x1401725c0`) and flush M06 (`0x14030c721`) runs. The map uses the bind variant `0x1400834e0`, not `0x1400835a0`.

Next for the map and battle seams: take the `TEXT` callers of the map screen (`RADAR_MAP_LABLE`, `FUEL_MAP_LABLE`) and of combat (`HONOR_LABLE`, `RETREAT_LABLE`, `TADS_*`), find the functions that contain them, then look for the bind, pass, flush bracket inside `0x14030a6b0` and `0x1403050a0` instead of scanning the 19 and 29 flush sites by hand.

State bytes seen in the first probe run (full table and the run itself: [probe-run-1.md](probe-run-1.md)):

| Address | Meaning | Tag |
|---|---|---|
| `0x143a11963` | `VideoTask` skip-one-frame flag, toggles on screen transitions | [code] |
| `0x143a11964` | 1 in the editor (2 for editor-from-menu) | [code]+[game] |
| `0x143a11984` | `VideoTask` lighting index, nonzero only on the arcade-battle branch; 0 -> 6 around the TEST drive | [code]+[game] |
| `0x147fc6fb7` / `0x147fc6f82` | `IS_IN_ARCADE_BATTLE` and a second battle flag | [code] |
| `0x147fc6fd0` | `IS_IN_CAMPAIGN?` | [code] |
| `0x147fc6fc4` | stepped `0, 8, 9, 2, 1, 2, 3, 4, 0x64, 2, 0`: a phase id, meaning unknown | [game] |
| `0x1403bd078` | cycled 1..4 while LMB was held in TEST, meaning unknown | [game] |
| `0x1403ef304`, `308`, `30c`; `0x1403c0e60`..`67`; `0x143a1197c`..`7f` | per-frame counters and timers: noise | [code]+[game] |

**TEST drive runs the arcade-battle renderer branch** [code]+[game].

