# How the game draws: frame, video task, scene dispatcher, text

Question: where can a mod draw its own text (the elevation hints) so it looks native and lands in the same pass as the game's labels? Steam 1.163, image base `0x140000000`. Tags: [code] decompiled or searched in Ghidra, [guess] inferred. Ghidra stayed read-only.

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

`SomethingVideoTask` calls the **scene dispatcher `0x140300c20`** as `f(DAT_14800ee28, DAT_14800ee20, 0, 0)`. Ghidra calls it `rep_1402d5b50_WriteToClientLog`. It is anchored by the error string `D:\!ESSENTIALS\PROJECTS\HYBRID FLEET 2013EX\VideoTask.cpp` (line `0x2849`) in its branch for an unexpected mode. It first sets render state on the shader objects (`DAT_143a13960`, `DAT_143a13a20`), then dispatches on `param_4` and the game-mode flags:

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

Fonts defined in the game's `Media/*.res` (60): B52_18, B52_26, courier, courier_28, dinpro_10_med, dinpro_14_bold, dinpro_14_med, dinpro_14_reg, dinpro_16_med, dinpro_18_black, dinpro_18_black_shadow, dinpro_18_med, dinpro_200_black, dinpro_20_black, dinpro_20_bold, dinpro_20_reg, dinpro_25_bold, dinpro_25_bold_blured, dinpro_30_black, dinpro_30_reg, dinpro_32_bold, dinpro_45_black, dinpro_48_black, dinpro_48_black_blured, dinpro_80_black, elizabeth_16, fixed_16, fixed_20, fixed_50, flash_large, flash_large_shadow, flash_small, fun_crayon, georgia_15, impact_18, impact_24, myriad_10, myriad_15, myriad_40, nixies_30, olga_24, pollock_100, pollock_20, pollock2_52, pollock_30, pollock_38, pollock_52, pollock_60, pollock_80, radio_20, son_45_blured, sourcepro_14_bold, vcr_12, vcr_14, vcr_16, vcr_21, vcr_30, vcr_40.

## Drawing recipe and hook seam [guess until live-tested]
1. `font = 0x1401a8710("dinpro_14_bold", scale, 2, 0xAARRGGBB)`.
2. Call `Render` directly: `0x14016eb40(font, x, y, align, text, null, null, 0, 0.0)`. This avoids the Win64 vararg rules of `printf` and format-string injection from a part id containing `%`.
3. Glyphs are drawn immediately, so output only appears while the scene is being rendered.
4. Seam: wrap the `E8 rel32` call at `0x140300d63` with a `patchy::Trampoline` (`absolute_call` the original, `preserved_call` ours, `relative_jump` to `0x140300d68`). Never use `save_overwritten` on a rel32 call: patchy copies the bytes verbatim. This puts our text after the editor's own drawing, in the same target and coordinates, on the game thread.

## Unknowns
* Coordinate space of label `x`/`y` (probably the 1920x1080 virtual frame [guess]).
* Whether every game caller restyles the font before use.
* Whether any state drops draws when no scene is open (stock HGE batches quads and drops them outside a scene; this game's renderer is unknown).
* Next RE chunk: the sprite path (`0x1401725c0`, `0x140172aa0`, `0x140172ee0`), the renderer object behind HGE slot `+0x2e8`, the target bind `0x1400835a0`, the shader setters (`FUN_1400a0320`, `FUN_1400a0010`, `compareAndUpdateFloatArray_` `0x1400a04e0`).

## Live-test recipe
1. Throwaway debug DLL (not in QoL) that draws `QOL TEST` at (100, 100) from the wrapped call at `0x140300d63`; settles the pass and the coordinates.
2. Log-only detour on `0x14016eb40` printing font, `x`, `y`, align and text for editor frames.
