# Images and sprites

How the game stores and draws images (Steam 1.163). Sprite **drawing is confirmed in game** (probe run 2, see "Sprite drawing confirmed" below); a sprite drawn from the editor label-pass hook is hidden behind the palette buttons ([probe-run-1.md](../runs/probe-run-1.md)).

## Every image is an `Animation` resource [code+file]
Image definitions live in `Media/Tex/*.res` (included from `media.res`). A `Texture` resource names the atlas, then each image is an `Animation` (stock `hgeAnimation`, a sprite subclass):
```
Texture Fnt1
{
 filename = Media/Tex/Fnt1.png
 resgroup = 0
}
Animation dinpro_200_black
{
 texture = Fnt1
 rect = 3,1031,1024,512
 hotspot = 512,256
 zorder = 0.000000
 resgroup = 0
 frames = 1
}
```
* The **hotspot is the centre of the rect**, so `Render(x, y)` places the centre.
* Font glyph atlases are Animations too (`Fnt1.res`: `pollock_100` rect `3,3,2048,1024`; `dinpro_200_black` as above).
* Editor art is in `Editor1.res`: `shpwrk_back` 1920x1391, `shpwrk_back_eng`, `shpwrk_inv_frame` 1659x239, `shpwrk_slide` 1659x58.
* About 1100 Animations over `Background1`-`6`, `Hall3`-`8`, `Static4`-`7`, `Midground1`-`3`, `Desk1` (43), `Mapmode7` (87), `Fnt2` (3) and others.

## Resource getters [code]
Looked up by resource type through `CopyNameIntoMedia_` `0x140178950` (stock enum: `RES_TEXTURE` 2, `EFFECT` 3, `TARGET` 6, `SPRITE` 7, `ANIMATION` 8, `FONT` 9, `DISTORT` 11); each calls virtual `Get` (slot 1) on the found `ResDesc`.

| Address | Type | Role |
|---|---|---|
| `0x140170230` | 8 | `GetAnimation(manager, name)` (Ghidra name `loadMediaByName?`) |
| `0x1401703e0` | 9 | `GetFont` |
| `0x140170270` | 0xb (11) | `GetDistort?` |
| `0x1401702b0` | 3 | `GetEffect`; falls back to loading a file through HGE slot `+0x138`; returns the effect handle |
| `0x140170420` | 2 | `GetTexture`; parses a mipmap suffix, falls back to HGE `Texture_Load` slot `+0x310` |

A `GetSprite` (type 7) wrapper was **not found**; the game seems to use Animations for everything. The manager is the global `Media.res` `0x143a119e8`.

## Sprite object layout (the game's modified `hgeSprite`) [code]
| What | Where |
|---|---|
| quad: 4 vertices, stride `0x58` | start of the object |
| vertex colour | `+0x18` of each vertex (`SetColor` `0x140172ae0`: all four when index is -1, writes `+0x18`, `+0x70`, `+0xc8`, `+0x120`; else `index*0x58+0x18`) |
| blend | `+0x168` (set by `hgeFont::SetBlendMode`) |
| width / height | `+0x188` / `+0x18c` |
| hotspot x / y | `+0x198` / `+0x19c` |

Drawing:
* `Render(sprite, x, y)` is `0x1401725c0`: fills the four vertices from hotspot and size, then calls HGE vtable `+0x2e0` (`Gfx_RenderQuad`) on `newValidHGE` `0x1439e8670`.
* `RenderEx(sprite, x, y, rot, hscale, vscale)` is `0x140172aa0`: a sinf/cosf helper, then the same `+0x2e0` call. The decompiler lost its parameters; they are as in the stock helper [guess].
* Animations are shared objects: save and restore the vertex colour if you tint.

## Sprite drawing confirmed [game, 2026-10-14]
The probe's sprite test **draws**: `GetAnimation("shpwrk_slide")` (`0x140170230`) returned a non-null object and `RenderEx` (`0x140172aa0`) with scale 0.3 and a centre hotspot, called from the editor label-pass hook `0x140303fb4`, put it on screen. The user confirmed it from screenshot `$HF_DEV/hf_probe_build/20261014133349_1.jpg`: at frame `(1300,980)` it is **hidden behind the editor's palette buttons** (bottom bar, frame y about 990-1100), with fragments of the sprite and of its label text visible in the gaps between the buttons. Draw order: the **label pass is drawn under the palette buttons**, which are drawn afterwards. Probe v1.2 moves the test to `(1500,700)` for a clean look.
The editor screen itself (palette of 14 category buttons, SAVE/LOAD / RESET / TEST at the top left, the `DOCK A` watermark, the stats panel, the TEST panel) uses the same `Animation` resources; their names are unknown (see `Editor1.res`, `Desk1.res`).

## Unknowns
* Parameter types of `RenderEx`: it draws with `(sprite, x, y, rot, hscale, vscale)` as in the stock helper (works), but the decompiler still lost them.
* Names of the Animations behind the editor palette, panels and buttons.
* Whether a type-7 sprite getter exists anywhere.
* What `0x140172ee0` does (called around glyph rendering with `(sprite, char, -1)`).
* Animations with more than one frame: `frames` and how `hgeAnimation` advances them.

## Live-test recipe
1. Done (Run 2): the sprite draws. Next, check the v1.2 position `(1500,700)` for an unobstructed look.
2. Draw a few small Animations (`Desk1`, `Mapmode7`) in a gallery with their names to document what each looks like.
3. Try tinting through `0x140172ae0` and restoring afterwards.
