# Fonts: what the game ships and how to draw with them

Everything about the game's bitmap fonts: where they are defined, every font's metrics, what the editor uses, what they look like on screen, and how a mod draws text with them. Steam 1.163, image base `0x140000000`. Tags: legend in `../../README.md`.

## Where fonts are defined [code]
* `Media/Fnt/fonts.res` declares **58 fonts**: `Font <name>`, then `{ filename=Media\Fnt\<name>.fnt }`. `media.res` includes `Media/Tex/Fnt1.res` and `Fnt2.res`; the glyph bitmaps live in the texture atlases, not as PNGs in `Media/Fnt`.
* `Media/Fnt` holds **59 `.fnt` files**. The extra one, `flash_large_shadow_special.fnt`, is **not declared** in `fonts.res`. The folder also has stray HGE tool files (`hge.dll`, `texasm.exe`, `texasm.log`).
* `.fnt` format is stock HGE `fonted`: `[HGEFONT]`, `Bitmap=<name>.png`, then `Char="x",x,y,w,h,pre,post` per glyph (`pre`/`post` become `hgeFont::pre[]`/`post[]`). See [engine-hge.md](../engine-hge.md).
* In the exe a font is an `hgeFont` fetched by name: `hgeResourceManager::GetFont` `0x1401703e0` (the manager is the global `Media.res` `0x143a119e8`); `0x1401a8710(name, scale, blend, colour)` fetches it and sets scale (`+0x100c`), blend (`+0x1028`) and colour (`+0x1020`, only if non-zero). Details: [render-pipeline.md](render-pipeline.md).

## Charsets: ASCII only [code]
Every font is plain ASCII `0x20`-`0x7E` (95 glyphs; `B52_26` and `impact_24` have 94) with **no Cyrillic or other glyphs**, except three digit-only fonts: `dinpro_200_black` (digits, `|`, `.`; cells about 138x199 px), `nixies_30` (digits and space, 30x54 cells) and `radio_20` (digits and space, 19x21 cells).
So the editor's Cyrillic stats panel text is **not** drawn with these fonts through this path; how localised and Cyrillic text is drawn is unknown. Text drawn through the `hgeFont` path (hints, mods) must be ASCII.

## All fonts, metrics [code]
Max glyph cell height is the tallest `Char` height in the `.fnt` (the runtime `fHeight` at `font+0x1008` was not read).

| Font | In fonts.res | Bitmap | Glyphs | Max glyph cell height (px) | Glyph width range | Charset |
|---|---|---|---|---|---|---|
| B52_18 | Y | B52_18.png | 95 | 20 | 3-16 | ASCII 0x20-0x7E |
| B52_26 | Y | B52_26.png | 94 | 44 | 4-45 | ASCII 0x20-0x7E |
| courier | Y | courier.png | 95 | 42 | 4-28 | ASCII 0x20-0x7E |
| courier_28 | Y | courier_28.png | 95 | 31 | 5-21 | ASCII 0x20-0x7E |
| dinpro_10_med | Y | dinpro_10_med.png | 95 | 12 | 3-11 | ASCII 0x20-0x7E |
| dinpro_14_bold | Y | dinpro_14_bold.png | 95 | 18 | 3-14 | ASCII 0x20-0x7E |
| dinpro_14_med | Y | dinpro_14_med.png | 95 | 18 | 3-14 | ASCII 0x20-0x7E |
| dinpro_14_reg | Y | dinpro_14_reg.png | 95 | 18 | 3-14 | ASCII 0x20-0x7E |
| dinpro_16_med | Y | dinpro_16_med.png | 95 | 21 | 4-16 | ASCII 0x20-0x7E |
| dinpro_18_black | Y | dinpro_18_black.png | 95 | 23 | 5-19 | ASCII 0x20-0x7E |
| dinpro_18_black_shadow | Y | dinpro_18_black_shadow.png | 95 | 23 | 5-18 | ASCII 0x20-0x7E |
| dinpro_18_med | Y | dinpro_18_med.png | 95 | 21 | 4-17 | ASCII 0x20-0x7E |
| dinpro_200_black | Y | dinpro_200_black.png | 12 | 205 | 38-138 | digits+symbols (.0123456789|) |
| dinpro_20_black | Y | dinpro_20_black.png | 95 | 26 | 5-20 | ASCII 0x20-0x7E |
| dinpro_20_bold | Y | dinpro_20_bold.png | 95 | 26 | 4-20 | ASCII 0x20-0x7E |
| dinpro_20_reg | Y | dinpro_20_reg.png | 95 | 26 | 3-19 | ASCII 0x20-0x7E |
| dinpro_25_bold | Y | dinpro_25_bold.png | 95 | 32 | 5-24 | ASCII 0x20-0x7E |
| dinpro_25_bold_blured | Y | dinpro_25_bold_blured.png | 95 | 32 | 5-24 | ASCII 0x20-0x7E |
| dinpro_30_black | Y | dinpro_30_black.png | 95 | 38 | 6-35 | ASCII 0x20-0x7E |
| dinpro_30_reg | Y | dinpro_30_reg.png | 95 | 38 | 4-27 | ASCII 0x20-0x7E |
| dinpro_32_bold | Y | dinpro_32_bold.png | 95 | 41 | 6-30 | ASCII 0x20-0x7E |
| dinpro_45_black | Y | dinpro_45_black.png | 95 | 58 | 8-43 | ASCII 0x20-0x7E |
| dinpro_48_black | Y | dinpro_48_black.png | 95 | 61 | 9-45 | ASCII 0x20-0x7E |
| dinpro_48_black_blured | Y | dinpro_48_black_blured.png | 95 | 67 | 9-45 | ASCII 0x20-0x7E |
| dinpro_80_black | Y | dinpro_80_black.png | 95 | 98 | 13-74 | ASCII 0x20-0x7E |
| elizabeth_16 | Y | elizabeth_16.png | 95 | 20 | 4-17 | ASCII 0x20-0x7E |
| fixed_16 | Y | fixed_16.png | 95 | 16 | 4-10 | ASCII 0x20-0x7E |
| fixed_20 | Y | fixed_20.png | 95 | 25 | 6-17 | ASCII 0x20-0x7E |
| fixed_50 | Y | fixed_50.png | 95 | 51 | 9-42 | ASCII 0x20-0x7E |
| flash_large | Y | flash_large.png | 95 | 13 | 4-14 | ASCII 0x20-0x7E |
| flash_large_shadow | Y | flash_large_shadow.png | 95 | 13 | 4-14 | ASCII 0x20-0x7E |
| flash_large_shadow_special | N | flash_large_shadow_special.png | 95 | 13 | 4-14 | ASCII 0x20-0x7E |
| flash_small | Y | flash_small.png | 95 | 8 | 3-7 | ASCII 0x20-0x7E |
| fun_crayon | Y | fun_crayon.png | 95 | 65 | 21-83 | ASCII 0x20-0x7E |
| georgia_15 | Y | georgia_15.png | 95 | 18 | 3-17 | ASCII 0x20-0x7E |
| impact_18 | Y | impact_18.png | 95 | 22 | 4-16 | ASCII 0x20-0x7E |
| impact_24 | Y | impact_24.png | 94 | 45 | 4-45 | ASCII 0x20-0x7E |
| myriad_10 | Y | myriad_10.png | 95 | 12 | 3-10 | ASCII 0x20-0x7E |
| myriad_15 | Y | myriad_15.png | 95 | 18 | 3-14 | ASCII 0x20-0x7E |
| myriad_40 | Y | myriad_40.png | 95 | 48 | 5-35 | ASCII 0x20-0x7E |
| nixies_30 | Y | nixies_30.png | 11 | 54 | 30-30 | digits+symbols ( 0123456789) |
| olga_24 | Y | olga_24.png | 95 | 33 | 4-21 | ASCII 0x20-0x7E |
| pollock2_52 | Y | pollock2_52.png | 95 | 61 | 6-40 | ASCII 0x20-0x7E |
| pollock_100 | Y | pollock_100.png | 95 | 118 | 10-74 | ASCII 0x20-0x7E |
| pollock_20 | Y | pollock_20.png | 95 | 24 | 4-17 | ASCII 0x20-0x7E |
| pollock_30 | Y | pollock_30.png | 95 | 35 | 4-23 | ASCII 0x20-0x7E |
| pollock_38 | Y | pollock_38.png | 95 | 45 | 5-29 | ASCII 0x20-0x7E |
| pollock_52 | Y | pollock_52.png | 95 | 61 | 6-47 | ASCII 0x20-0x7E |
| pollock_60 | Y | pollock_60.png | 95 | 65 | 8-50 | ASCII 0x20-0x7E |
| pollock_80 | Y | pollock_80.png | 95 | 94 | 9-62 | ASCII 0x20-0x7E |
| radio_20 | Y | radio_20.png | 11 | 21 | 19-19 | digits+symbols ( 0123456789) |
| son_45_blured | Y | son_45_blured.png | 95 | 57 | 5-45 | ASCII 0x20-0x7E |
| sourcepro_14_bold | Y | sourcepro_14_bold.png | 95 | 18 | 4-10 | ASCII 0x20-0x7E |
| vcr_12 | Y | vcr_12.png | 95 | 16 | 4-11 | ASCII 0x20-0x7E |
| vcr_14 | Y | vcr_14.png | 95 | 14 | 4-13 | ASCII 0x20-0x7E |
| vcr_16 | Y | vcr_16.png | 95 | 22 | 4-14 | ASCII 0x20-0x7E |
| vcr_21 | Y | vcr_21.png | 95 | 20 | 4-14 | ASCII 0x20-0x7E |
| vcr_30 | Y | vcr_30.png | 95 | 24 | 5-20 | ASCII 0x20-0x7E |
| vcr_40 | Y | vcr_40.png | 95 | 46 | 6-30 | ASCII 0x20-0x7E |

## What the editor requests [code]
The editor label pass (`0x1400d4380`) asks `0x1401a8710` for these fonts, all at scale `[0x1403524d8]` = 1.0 and blend 2 (the next float, at `+4`, is 30.0); the second label function (`0x1400d6f70`) adds two more:

| Font | Colour | Where |
|---|---|---|
| `pollock_52` | `0xffffffff` | label pass, string `0x14035bda0` |
| `dinpro_45_black` | `0xff73604c` | label pass, `0x14035bdb0` |
| `dinpro_14_bold` | `0xff73604c` | label pass, `0x14035bdc0`; held in `R14`, used by most label calls |
| `flash_large` | `0xffffffff` | label pass `0x14035bdd0`; also `0x1400d649a` |
| `vcr_21` | `0xffffffff` | label pass, `0x14035bddc` |
| `dinpro_80_black` | `0x0cffffff` | `0x1400d6f70`: the big faint `DOCK A` background text ([game]: visible in screenshots) |

## What they look like (live sampler) [game]
2026-10-14: the debug DLL `hf_draw_test` (`$HF_DEV/hf_draw_test`, commit `0383a69`, local git) drew one line per font, right-aligned at x=1900 (1920x1080 frame), y = 90 + 40 i, white `0xffffffff`, scale 1.0, blend 2, text `<fontname>   ELEVATION  U up  P down  holding: ITEM_GUN_30  floor=2 (manual)`. Screenshot (2560x1440): `$HF_DEV/hf_draw_test_build/screenshot_font_test.png`. 20 fonts were sampled; the other 38 are **visual: pending** (a second sampler, all remaining fonts normalised to about 24 px height through `fHeight`, is being built). The first elevation hint (bold `dinpro_14_bold`) is in `$HF_DEV/hf_draw_test_build/screenshot_working_2.png`, next to the lighter DIN-style stats panel.

| Font | Look | Used by the editor |
|---|---|---|
| `B52_18` | visual: pending |  |
| `B52_26` | visual: pending |  |
| `courier` | [game] very large at scale 1 (42 px cell, serif monospace); the sample line crossed most of the screen, needs scale about 0.5 |  |
| `courier_28` | visual: pending |  |
| `dinpro_10_med` | [game] tiny condensed sans (12 px cell) |  |
| `dinpro_14_bold` | [game] clearly bold; first elevation hint font, the user found it too bold | editor label pass, colour `0xff73604c` (`0x14035bdc0`); `R14`, most label calls |
| `dinpro_14_med` | [game] slightly heavier than `_reg` |  |
| `dinpro_14_reg` | [game] light regular DIN-style sans; closest look to the stats panel text on the left [guess, by eye] |  |
| `dinpro_16_med` | [game] larger medium weight |  |
| `dinpro_18_black` | visual: pending |  |
| `dinpro_18_black_shadow` | visual: pending |  |
| `dinpro_18_med` | [game] larger medium weight |  |
| `dinpro_200_black` | visual: pending |  |
| `dinpro_20_black` | visual: pending |  |
| `dinpro_20_bold` | visual: pending |  |
| `dinpro_20_reg` | [game] larger regular weight |  |
| `dinpro_25_bold` | visual: pending |  |
| `dinpro_25_bold_blured` | visual: pending |  |
| `dinpro_30_black` | visual: pending |  |
| `dinpro_30_reg` | visual: pending |  |
| `dinpro_32_bold` | visual: pending |  |
| `dinpro_45_black` | visual: pending | editor label pass, colour `0xff73604c` (`0x14035bdb0`) |
| `dinpro_48_black` | visual: pending |  |
| `dinpro_48_black_blured` | visual: pending |  |
| `dinpro_80_black` | visual: pending | second label function `0x1400d6f70`, colour `0x0cffffff` (very transparent white): the big faint `DOCK A` background text |
| `elizabeth_16` | [game] small calligraphic serif, old-style digits |  |
| `fixed_16` | [game] small monospace pixel-style font, lowercase, wide tracking, readable, looks like game UI. **The user's favourite; used by the native elevation hint** |  |
| `fixed_20` | visual: pending |  |
| `fixed_50` | visual: pending |  |
| `flash_large` | visual: pending | editor label pass (`0x14035bdd0`) and second label function at `0x1400d649a`, colour `0xffffffff` |
| `flash_large_shadow` | visual: pending |  |
| `flash_large_shadow_special` | visual: pending |  |
| `flash_small` | [game] tiny (8 px) ALL-CAPS pixel font, hard to read |  |
| `fun_crayon` | visual: pending |  |
| `georgia_15` | [game] serif |  |
| `impact_18` | [game] heavy condensed bold |  |
| `impact_24` | visual: pending |  |
| `myriad_10` | [game] tiny narrow humanist sans |  |
| `myriad_15` | [game] narrow humanist sans, tight spacing |  |
| `myriad_40` | visual: pending |  |
| `nixies_30` | visual: pending |  |
| `olga_24` | visual: pending |  |
| `pollock2_52` | visual: pending |  |
| `pollock_100` | visual: pending |  |
| `pollock_20` | visual: pending |  |
| `pollock_30` | visual: pending |  |
| `pollock_38` | visual: pending |  |
| `pollock_52` | visual: pending | editor label pass, colour `0xffffffff` (`0x14035bda0`) |
| `pollock_60` | visual: pending |  |
| `pollock_80` | visual: pending |  |
| `radio_20` | [game] digits and space only: blocky dark cells, the sample showed only the digits `20`, `30`, `2` and nothing for letters |  |
| `son_45_blured` | visual: pending |  |
| `sourcepro_14_bold` | [game] bold slab / typewriter-like, wide tracking |  |
| `vcr_12` | [game] VCR / terminal style; lowercase is drawn as capitals |  |
| `vcr_14` | [game] VCR / terminal style; lowercase is drawn as capitals |  |
| `vcr_16` | [game] VCR / terminal style; lowercase is drawn as capitals |  |
| `vcr_21` | visual: pending | editor label pass, colour `0xffffffff` (`0x14035bddc`) |
| `vcr_30` | visual: pending |  |
| `vcr_40` | visual: pending |  |

## Choosing a font
| Need | Candidates |
|---|---|
| Small readable UI text | `dinpro_14_reg`, `dinpro_14_med`, `fixed_16`, `vcr_14` |
| Bold emphasis | `dinpro_14_bold`, `sourcepro_14_bold`, `impact_18` |
| Pixel / terminal look | `fixed_16` (chosen for the elevation hint), `vcr_12/14/16` (`vcr_12` at scale 1.5, white: the `hf_ally` pre-combat "PLAYER" label [game], same `StyleFn` + `Render` recipe as the elevation hint), `flash_small` (tiny, caps only) |
| Digits only (counters, readouts) | `nixies_30`, `radio_20`, `dinpro_200_black` |

## How a mod draws text [code, proven by the elevation hint [game]]
1. Get the font: `font = GetFont(*(0x143a119e8), name)` (`0x1401703e0`).
2. Style it, either through `0x1401a8710(name, scale, blend, colour)` or by writing `+0x100c` scale, `+0x1020` colour, `+0x1028` blend yourself. Fonts are **shared objects** that every caller restyles before use, so save the three fields first and put them back after drawing.
3. Draw: `0x14016eb40(font, x, y, align, text, null, null, 0, 0.0)` with `align` 0 left, 1 right, 2 centre. Coordinates are the 1920x1080 frame, `y` is the top of the line.
4. Text is **ASCII only**; `\n` and `@` break lines (replace `@` in user text), and a NUL ends the text.
5. Drawing only shows while the scene is rendered: use the editor label-pass hook at `0x140303fb4` (see [render-pipeline.md](render-pipeline.md)).

## Unknowns
* What draws the stats panel (Cyrillic) text, and with which font.
* What `flash_large_shadow_special` is used for (undeclared in `fonts.res`).
* Which fonts the HUD, battle and map screens use.
* How fonts get their atlas rectangles (`Fnt1.res` / `Fnt2.res` not read).
* `fHeight` semantics (max cell height versus the value at `font+0x1008`; check at runtime).
* Whether `Render` clips at the frame edge.
* The look of the blurred and shadow variants (`*_blured`, `*_shadow`) and of the 38 fonts not yet sampled on screen.

## Live-test recipe
1. Second sampler: all 38 remaining fonts, each scaled to about 24 px height (`24 / *(float*)(font+0x1008)`), two columns; photograph it and fill in the `visual: pending` rows.
2. Log-only detour on `0x1401a8710` printing every `(name, scale, blend, colour)` over a play session (editor, map, battle, dialogue) to map font usage per screen.
3. Read `Media/Tex/Fnt1.res` and `Fnt2.res` for the atlas rectangles, and find the Cyrillic text path (start from the localised string lookup `0x1401ae090`).
