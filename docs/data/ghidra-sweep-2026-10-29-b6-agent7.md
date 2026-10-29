# Ghidra sweep 2026-10-29 — batch 6, agent 7 (large functions B + quad block)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: 0x1402410b0, 0x140247850, 0x140269d00, 0x14028bf80, 0x140292820,
0x140296530, plus the quad/UV block 0x140172550–0x140172b10.

Result: **7 renamed + plated**, **1 pre-existing name plated**, **0 skipped**,
**0 created**. Every plate has summary / `Algorithm:` / `Parameters:` /
`Returns:`. No `rep_*` was renamed (the stale `rep_*` labels of the callees are
quoted as evidence only).

## Concurrency note (read this first)

Two of the four quad helpers were **already named and plated when this agent
started working**, so they were not touched:

| addr | existing name |
|---|---|
| 0x1401725c0 | `Gfx_QuadPositionFromExtents` |
| 0x140172ee0 | `Gfx_QuadSetCornerField8` |

0x140172550 also already carried `Gfx_QuadSetCornerXY`. It was briefly renamed
`Sprite_Render4V` before the existing name was noticed; **the original name was
restored** and only the plate was added. The 0x1401725c0/aa0 "named by wave 1"
warning in the assignment therefore also applies to 550 and ee0 — the quad
family uses the `Gfx_Quad*` prefix, which this agent kept.

## Renames

| addr | new name | description |
|---|---|---|
| 0x140172aa0 | `Gfx_QuadRenderEx` | forwards (quad,x,y,angle,hscale,vscale) to 0x1401720e0 and submits through HGE slot +0x2e0; 0x1401720e0 writes per-corner angle +0xc, cos +0x10, sin +0x14, rotated/scaled extents about the cached hotspot +0x198/+0x19c, flip sign +0x54 |
| 0x1402410b0 | `Thunk_RebuildNodeFromCreature` | `LEA RDX,[DAT_143a13a78]; JMP 0x1402410c0` — 12-byte tail-call thunk that rebuilds the global controlled node from one creature |
| 0x140247850 | `Hud_DrawRaycastStrip` | 800 parallel vertical rays, 1 unit apart, 10 000 units long, from `pos.y-400` upward; per column stores the nearest body hit, then draws the first-hit outline as world lines where adjacent hits differ by < 10 |
| 0x140269d00 | `Engine_ApplyThrustCommand` | turns a desired bank thrust vector into engine codes 0x64/0x65/0x66/0x67 on one engine part, flipping the engine mesh when thrust is reversed |
| 0x14028bf80 | `Profile_CheckNoNestedActiveNodes` | counts mode-2 profile creatures, then collects mode-2 children from their +0x320 lists; true when the collected count equals the creature count (no nested active node) |
| 0x140292820 | `Thunk_Profile_BuildSavePath` | passes `BOOL_147fc6f80` as 3rd arg to 0x140292840 and returns the destination string; builds `Saves/Profile_<slot>/<label>` or `SavesSkirmish/Profile_<slot>/<label>` |
| 0x140296530 | `Npc_RollAttitudeStats` | re-rolls the NPC's eight -2..2 stats from the eight template ints at +0x108..+0x124 and retries (max 100) until sum(|v|) < 12 and exactly three |v| > 1 |

## Plated without renaming

| addr | name | why |
|---|---|---|
| 0x140172550 | `Gfx_QuadSetCornerXY` | pre-existing name; the plate now documents the exact corner offsets (+0/+4, +0x58/+0x5c, +0xb0/+0xb4, +0x108/+0x10c) and the fact that the body is stock HGE `hgeSprite::Render4V` |

## Evidence per function

### Quad block 0x140172550–0x140172b10

Census of the block (script pass): 0x140172550 (101 B), 0x1401725c0 (283 B),
0x1401726e0 (957 B `_invalid_parameter_noinfo` replica), 0x140172aa0 (63 B),
0x140172ae0 `setSpriteFields` (38 B, already named), 0x140172b10 `Gfx_QuadSetFlip`
(974 B, already named). No gaps, nothing to create.

* **Corner record = 0x58 bytes** with x +0, y +4, +8 (unknown float, set by
  `Gfx_QuadSetCornerField8`), angle +0xc, cos +0x10, sin +0x14, ARGB +0x18
  (set by `setSpriteFields`), and four uv-like pairs at +0x1c/+0x20, +0x24/+0x28,
  +0x34/+0x38, +0x44/+0x48 (the ones `Gfx_QuadSetFlip` swaps), extents +0x4c/+0x50,
  flip sign +0x54, +0x1a0/+0x1a1/+0x1a2 flags, cached origin +0x198/+0x19c on the
  quad itself.
* **HGE vtable +0x2e0** (stub 0x14016cc80) reaches **0x140085f40**: if the HGE
  byte +0x1c5 is clear it calls `Render_SetBlendState(hge, quad+0x168)` and then
  `(*(*(hge+0x1a0))+0x40)(renderer, quad)`. So the slot is a *draw quad now*
  call, not a queue; the ten callers of the family are all draw paths
  (`displayLableRotation`, `TadsDamage_DrawPopups`, `Trail_Render`,
  `Hud_DrawSlotPin`, `Gfx_DrawOverlaySprite`, `SomethingVideoTask`, …).
* 0x1401720e0 (the helper behind `Gfx_QuadRenderEx`) carries the stale label
  `rep_1401665f0_..._sinf`; its real body is the rotated/scaled quad builder, and
  it calls the real `cosf`/`sinf` replicas. It lies just below the assigned block
  and was **not** renamed.

### 0x140269d00 `Engine_ApplyThrustCommand`

* Callers: 0x1400bc740 (AiShipTick-side chunk) at 0x1400bd083 and 0x14026abc0
  (ship set-up chunk) at 0x14026adf7. The three `DATA` xrefs to the function are
  `UNWIND_INFO` / `.pdata`, **not** a vtable (checked 0x1403a2030).
* Call-site shape: `MOVSD XMM0,[creature+0x210]; CALL [vtable+0xe8]; …
  CALL 0x140269d00` with the pair in RCX and the part in RDX.
* Code: `0x140053d50(vec,code)` deletes every occurrence of `code` from the int
  vector at +0x370; then `RenderMesh_ScaleAndFlip(part,-1,1,1)` + queue
  {0x64,0x66}/{0x65,0x67} on the reversed branch, otherwise {0x67} or {0x66}.
* The four codes are exactly the engine bank commands documented in
  `docs/findings/ai/ai-steering-and-avoidance.md` §5, which is the cross-check
  for the name.

### 0x14028bf80 `Profile_CheckNoNestedActiveNodes`

* Sole caller `Prologue_HideUnusedCraft` (0x1402a8760) uses the byte result to
  decide whether a mode-3 craft can be renamed `HIDDEN`.
* Opens with a `std::vector` reserve sized on `Profile+0x218 - Profile+0x210`,
  then an RB-tree of pointers. Mode test is `*(int*)(obj+0x2e8) == 2`
  (`Prologue_HideUnusedCraft` uses the same dword as "mode").
* Return is `vectorSize == mode2CreatureCount`; the vector also grows with mode-2
  elements pulled from the +0x320 child lists, so the flag means "flat".

### 0x140296530 `Npc_RollAttitudeStats`

* Sole producer caller `Npc_Constructor` (0x140292fa0) stores eight seria ints at
  NPC +0x108..+0x124 (params 5..12) and calls this with `param_2 = 0`; the NPC
  dialog path in `ClickFunc` (0x140136ad6) calls it on the NPC returned by
  `GetNpcFromProfile` with `param_2 = 1`.
* RNG is HGE vtable +0x108 `RandomInt(min,max)` / +0x110 `RandomFloat(min,max)`.
* The retry predicate at the bottom of the function is explicit:
  `sum(|v|) < 12 && popcount(|v| > 1) == 3`, max 100 attempts.
* Field naming: the class owns the `ATTITUDE_STATS` / `ATTITUDE_NAME` /
  `attitude_star` UI page (0x1401cf1c0), and -2..2 matches its star rating, hence
  "attitude stats"; which axis is which is **not** proven and is stated as such in
  the plate.

### 0x140247850 `Hud_DrawRaycastStrip`

* Sole caller `afterBattleStars??` (0x1402a06bf), inside a loop over the creature
  list, guarded by `BOOL_147fc6f80`, with `param_2` = "on screen and near" test.
* Geometry read from the constants: step `0x1403721e0` = 0.002503129, centre
  offset 400.0 (`0x140352834`), segment length 10 000.0 (`0x14035284c`), unit
  scale 0.05 (`0x1403c0e10`, game units → Box2D metres), connect threshold 10.0
  (`0x140352818`). 800 columns (loop counter runs to 0x1900 in 8-byte steps).
* Static scratch: four 1000-qword arrays at 0x143a241a0 / 0x143a260e0 (points) and
  0x143a28030 / 0x143a29f70 (bodies), guarded by `Init_thread_header` on
  0x143a28020. They have **no xrefs outside this function**.
* Own parts are excluded by setting `part+0x224 = 1` and clearing it after the
  scan — the same exclusion idiom as `Hud_DrawAimRay` (0x140248490).
* Colours: lime `0xffa8fc00` when both hit bodies have `+0x3d0 == 0`, cyan
  `0xff00e4ff` otherwise. The `+0x1f40` second array is only ever zeroed, so its
  draw block (`+0x7b0` byte, red `0xffdd2727` / lime) is dead in this build.
* Left as an explicit uncertainty in the plate: the artistic purpose (terrain /
  hull outline vs projected shadow) and the meaning of `+0x3d0` / `+0x7b0`.

## Cross-cutting findings for the docs agent

1. **HGE slot +0x2e0 = draw quad** (0x14016cc80 → 0x140085f40 → renderer
   vtable +0x40) and blend state comes from `quad+0x168`. This settles the
   question that made batch-5 agent 8 leave the quad family unnamed.
2. **Sprite corner record is 0x58 bytes**; `+0x18` is the ARGB (via
   `setSpriteFields`), `+8` is a second per-corner float (via
   `Gfx_QuadSetCornerField8`) whose meaning is still unknown.
3. **Creature +0x1330 is the part list** (confirmed again: `Engine_ApplyThrustCommand`
   and `Hud_DrawRaycastStrip` both walk it at 0x18-stride with the pointer at +8),
   while **+0x320 is the +0x18-stride child list** used by
   `Profile_CheckNoNestedActiveNodes` / `Prologue_HideUnusedCraft`.
4. **Engine command codes** 0x64..0x67 are set per part by
   `Engine_ApplyThrustCommand`, not by the AI steering functions directly.
5. Stale `rep_*` labels encountered and disproved inside this scope:
   `rep_1401665f0_..._sinf` (quad builder), `rep_1400515a0_..._memmove`
   (vector erase-by-value at 0x140053d50), `rep_14026fd20_..._free`
   (save-path builder 0x140292840), `rep_140222060_CopyString` (node rebuild
   0x1402410c0), `rep_140248f00_New` (ship set-up chunk). None of them are
   memmove/free/CopyString/New.

## Remaining

Nothing unnamed left in the assigned scope. `Gfx_RenderQuad` (the uncreated
0x140085f40 / 0x14016cc80 target) is still without a function object — creation
is not in this agent's scope and was not requested.
