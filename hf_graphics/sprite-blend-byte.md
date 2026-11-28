# The sprite blend byte: why battle-HUD art looks translucent (Steam 1.163)

A mod drew a new HUD sprite from an atlas at the battle ship-panel seam, with exactly the panel's own
sprite setup, and the art came out see-through over the landscape.
A pure-white probe sprite drawn through the same calls looked solid.
This page is the answer: the panels' blend value is **additive**, and white saturates under addition.
Everything below was read in the Steam 1.163 program on 2026-11-28 (`hf_prehud` v0.3.x) unless tagged otherwise.

## The byte

Every sprite (the game's modified `hgeSprite`, see [images and sprites](images-and-sprites.md)) carries a
blend value at `+0x168`.
`Gfx_SubmitQuadA` (`0x140085f40`, the body behind HGE slot `+0x2e0`) passes it to
`Render_SetBlendState (0x140086500)` for **every** quad, so it is a per-quad state, not a pass state.

| bits | meaning |
|---|---|
| `& 1` | pixel-shader technique: set = `ps_add`, clear = `ps_modulate` (`ShaderDefault_SetFlag118` `0x14008d290`, called with the raw flags; only bit 0 is kept) |
| `& 2` | **`DestBlend`: clear = `ONE` (additive), set = `INV_SRC_ALPHA` (ordinary alpha blending)** |
| `& 0x10` | HUD overlay handling. On a change it selects a special composite descriptor (`SrcBlend 10 INV_DEST_COLOR`, `DestBlend 2 ONE`, `Op 1 ADD`) and remembers the normal one; while set, `Render_SetBlendState` also takes the restore branch |

Practical values: `0` additive, `2` alpha with depth write, `0x10` the battle panels' additive overlay,
**`0x12` alpha with the panels' overlay handling** (what a mod that wants an opaque HUD sprite should use).

## The descriptor the flags edit

`InitD3DEngine_` (`0x140083ed0`) leaves a `D3D11_BLEND_DESC` at `engine + 0x7c` (the engine is HGE `+8`,
`HGE_POINTER 0x1439e8670`, also published at `0x143a13950`):

| offset | field | value |
|---|---|---|
| `+0x00` | AlphaToCoverageEnable | 0 |
| `+0x04` | IndependentBlendEnable | 0 |
| `+0x08` | RT0.BlendEnable | 1 |
| `+0x0c` | SrcBlend | 5 `SRC_ALPHA` |
| `+0x10` | **DestBlend** | 6 `INV_SRC_ALPHA` (rewritten per quad) |
| `+0x14` | BlendOp | 1 `ADD` |
| `+0x18` | SrcBlendAlpha | 2 `ONE` |
| `+0x1c` | DestBlendAlpha | 1 `ZERO` |
| `+0x20` | BlendOpAlpha | 1 `ADD` |
| `+0x24` | RT0.RenderTargetWriteMask | `0x0f` |

`Render_SetBlendState` copies that descriptor and overwrites **only** `DestBlend`:

```c
iVar3 = (flags & 2 | 1) * 2;      /* 2 = ONE (additive), 6 = INV_SRC_ALPHA (alpha) */
if (iVar3 == *(int *)(engine + 0x8c)) return;   /* DestBlend already what we want */
```

The applier is `Render_SetRasterizerState` (`0x1400863c0`) - **misnamed**; it compares the six cached
fields (`engine+0x88..0x9c`), copies the descriptor to `engine+0x7c`, releases the current shader (which
flushes its staged vertices), recreates the state through the device's create-state slot `+0xa0` and binds
it with the context's `OMSetBlendState` (`+0x118`).
The early return explains why a quad with `0x2` is free when the base state is in force.

## `+0x1c4` is not a blend flag

`Render_SelectBlendState` (`0x140086d00`) is also **misnamed**: it selects one of three **depth-stencil**
states (`engine+0x68` when `engine+0x1c4 == 0`; otherwise `engine+0x60` when `engine+0x10 == 0`, else
`engine+0x58`) and binds it with `OMSetDepthStencilState` (`+0x120`).
`InitD3DEngine` creates them from three depth descriptors; the `+0x1c4 == 0` one has `DepthEnable = 0`,
i.e. **depth test off** - the state a HUD overlay wants.
`D3DEngine_SubmitVertices` (`0x1400830f0`) sets `engine+0x1c4 = (param_5 != 0)` per submitted batch.

## The panels are additive on purpose

The left battle ship panel sprite `[0x14800efa0]` is set just before its blit:

```
0x14030908d   C7 80 68 01 00 00 10 00 00 00   MOV dword ptr [RAX + 0x168], 0x10
```

followed by `LAYER_Z(3)` (`0x140216480`), `SetZ` (`0x140172ee0`) and the blit itself `0x1403090fc`.
The right panel sprite `[0x14800efb0]` is not re-set in its own block (`0x140309110..`), so it keeps
whatever the sprite carries.
`0x10` = overlay bit, **bit 1 clear** = additive: the battle HUD is deliberately translucent over the
battlefield, and `hf_ally`'s extra panels (`ally_panels`, same value) look the same way for the same reason.

## Symptom, and how to measure it instead of trusting the eye

Additive means `drawn = art * k + scene`; alpha blending means `drawn = a * art + (1 - a) * scene`.
Fit the screenshot's red channel against the atlas red channel over the art's opaque pixels
(atlas `Midground4.png`, `avion_main` = `3541,2276,547,402`, drawn at panel top-left + `(-4,-96)` at 1080p):

* `hf_prehud`'s ghosting frame: `drawn = 0.92 * art + 89`, i.e. additive with the scene at ~89.
  Alpha blending at 0.92 would need a scene of `89 / 0.08 = 890`, impossible on screen.
* A scaled or misplaced probe attenuates the slope; only fit 1:1 integer-aligned draws.

Traps that cost a day:
* A **white** probe is useless: `white + scene` clips to white under additive, so it "looks opaque" in
  the broken build. Use a mid-tone sprite or a screenshot fit.
* "First quad of the batch opaque, later quads ghostly" was a measurement artefact.
  `ShaderDefault_EmitVerticesA` (`0x14008ce70`) sets the technique per quad, but the batch is only drawn
  by `Effect_Release` (`0x140088340`, effect slot `0x28`), so position in the batch does not change the
  blend state.

## Related: the texture-array slot is not an alpha control

`Shaders/Default_ps.hlsl` binds `Texture2D _base[32]`, and `ShaderDefault_EmitVerticesA` fills the vertex's
third texture coordinate as `texture + 0x24 + 0.5` when `texture + 0x10 == 1` (else `0.5`).
That is the **texture-array slot**, not a mip level and not an alpha flag; `getBase()` compares `tex.z`
against 1..8 and samples the matching `_base[i]`.

## Validated in game

`hf_prehud` v0.3.0 drew the same sprite twice, `0x12` next to `0x10`, and v0.3.1 shipped `0x12`:
the user reports the dashboard, the frame probe and the `0x12` copy opaque, with the `0x10` copy still a
ghost [game, 2026-11-28].
