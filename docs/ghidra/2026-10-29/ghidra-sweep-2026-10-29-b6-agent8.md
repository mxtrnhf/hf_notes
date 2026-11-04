# Ghidra sweep 2026-10-29 — batch 6, agent 8 (containers/accessors, `FUN_*` only)

Program `Highfleet.exe.unpacked.exe` v1.163 (project `HighfleetServer`).
Scope: `FUN_*` only, `0x140070000–0x1401FFFFF` (the `rep_*` in the range belong to agents 2–4).
No `create_function`, no tags, no `save_program`. Every rename has a doc plate
(summary / `Algorithm:` / `Parameters:` / `Returns:`).

Start: 79 `FUN_*`. End: **55 `FUN_*`**.
**24 renames applied, 0 created, 55 skipped** (each with a reason below; most were
already adjudicated in batches 3–5 and are re-listed with the new evidence that
still does not settle them).

The decisive new tool this pass was **RTTI**: every vtable that a constructor or a
deleting destructor installs can be resolved statically (COL at vtable-8, TypeDescriptor
RVA at COL+0xc, name string at TD+0x10). That turned a whole family of previously
"owning class unknown" destructor clones into provable names.

## Renames (24)

### Four-corner quad family (0x140172550–0x140172ee0)

Now nameable because `Gfx_RenderQuad` (0x14016cc80, the HGE slot +0x2e0 wrapper)
exists: `Gfx_RenderQuad` calls 0x140085f40 at 0x14016cce9 as its actual draw.

| addr | new name | description |
|---|---|---|
| 0x140172550 | `Gfx_QuadSetCornerXY` | stores four (x,y) pairs into the 0x58-stride corner records at +0x00/+0x04, +0x58/+0x5c, +0xb0/+0xb4, +0x108/+0x10c, then calls HGE +0x2e0. |
| 0x1401725c0 | `Gfx_QuadPositionFromExtents` | resets the per-corner colour/alpha defaults and writes the axis-aligned rect (x,y)-(x+extentX, y+extentY) offset by the cached texture origin +0x198/+0x19c (extents +0x188/+0x18c), then draws. |
| 0x140172ee0 | `Gfx_QuadSetCornerField8` | writes the dword at +8 of one corner (`quad + index*0x58 + 8`) or, when the index is -1, of all four corners (+8/+0x60/+0xb8/+0x110). |

Corner record layout used here: 0x58 bytes, +0x00/+0x04 position, +0x08 the value written
by the setter above, +0x0c, +0x10 = 1.0 colour/alpha default, +0x1c/+0x20 and +0x24/+0x28
and +0x34/+0x38 the UV pairs, four records at +0x00, +0x58, +0xb0, +0x108; flip flags
+0x1a0/+0x1a1, active flag +0x1a2, cached origin +0x198/+0x19c, extents +0x188/+0x18c.

### Media / render-target

| addr | new name | description |
|---|---|---|
| 0x140179410 | `Media_EnsureRenderTarget` | lazy get-or-create: if proxy+0x90 is null, call HGE slot +0x300 (0x14016cbb0 -> factory 0x1400839d0) with proxy+0xa0/+0xa4, format 0x1c, flag 1, and cache the handle at +0x90. |

Proof that this is a render target and not the "unknown resource" left in batch 5:
the factory 0x1400839d0 builds a 0x60-byte object whose vtable is **0x140356768**, whose
RTTI name is `.?AVRenderTarget@@`. Batch 5 (agent 8) had already narrowed the proxy
family down to sound/music/stream/file/texture and left this slot open.

### Destructor clones, named by their RTTI-proven owner vtable

| addr | new name | owner vtable / RTTI |
|---|---|---|
| 0x140170140 | `ResDesc_ScalarDeletingDtor` | 0x140366650 = `.?AUResDesc@@` |
| 0x140170190 | `ResDesc_ScalarDeletingDtorCopy2` | same |
| 0x1401787a0 | `ResDesc_ScalarDeletingDtorCopy3` | same |
| 0x1401787f0 | `ResDesc_ScalarDeletingDtorCopy4` | same |
| 0x140178840 | `ResDesc_ScalarDeletingDtorCopy5` | same |
| 0x140178890 | `ResDesc_ScalarDeletingDtorCopy6` | same |
| 0x1401788e0 | `ResDesc_ScalarDeletingDtorCopy7` | same |
| 0x1401701e0 | `Texture_ScalarDeletingDtor` | 0x140356718 = `.?AVTexture@@` |
| 0x1400e8140 | `MapShipBody_ScalarDeletingDtor` | vtable 0x14035e1d0 = `.?AVMapShipBody@@` |
| 0x14018f940 | `IObject_ScalarDeletingDtor` | destructor target installs `IObjectVFTable`; frees 0x30 |
| 0x1401a82c0 | `Anistate_ScalarDeletingDtor` | destructor target installs 0x140369400 = `.?AVAnistate@@`; frees 0xb0 |
| 0x1401a8480 | `b2ContactFilter_DeletingDtor` | 0x140369200 = `.?AVb2ContactFilter@@` |
| 0x1401a84b0 | `b2ContactListener_DeletingDtor` | 0x140369218 = `.?AVb2ContactListener@@` |
| 0x1401a84e0 | `b2DestructionListener_DeletingDtor` | 0x1403691e0 = `.?AVb2DestructionListener@@` |

The seven `ResDesc` copies are byte-identical (install vtable, release HGE through
`AnotherHGE2` slot 0, free on flag bit 0). They are separate functions, not one ICF
object, so they are named as Copy2..Copy7 after the first one — the same convention
already used for `b2Joint_DeletingDtorCopy2/3`.

`MapShipBody` independently confirms the batch-5 open item: the destructor frees a Link
at +0xa48 and runs `Body_Destructor` over 0xa40 bytes, i.e. object size **0xa60** —
`Body` (0xa40) + one 0x18-byte Link — which matches the MapShipBody RTTI. Batch 5 had
skipped it because no documented class had that size; `Frame` is 0xa58 and is not it.

### Constructor

| addr | new name | description |
|---|---|---|
| 0x1401a47c0 | `RepairStepNewBlock_Constructor` | installs vtable 0x140369328 (`.?AURepairStepNewBlock@@`) and stores five fields: qword[1], qword[2], dword[3], dword +0x1c, byte[4]. |

### Range-destroy thunks (provable element stride/type)

| addr | new name | description |
|---|---|---|
| 0x14015c1c0 | `Thunk_DestroyStringRange48` | arg-shuffle tail thunk to 0x140128ca0: per 0x30-byte record frees the heap buffer when the capacity at +0x18 > 0xf, then resets to an empty SSO string. |
| 0x14015c1e0 | `Thunk_DestroyVectorRange24` | arg-shuffle tail thunk to 0x140128d30: per 0x18-byte `{begin,end,capacity}` header frees the buffer and zeroes the three qwords. |
| 0x140187890 | `Thunk_DestroyNodeListRange56` | arg-shuffle tail thunk to 0x140183410: per 0x38-byte record frees the chained node list at +0x28 and its head. |
| 0x1401878b0 | `Thunk_DestroyListRange16` | arg-shuffle tail thunk to 0x14011dbc0: per 0x10-byte record frees the chain at +0 and the head pointer. |
| 0x1401ae820 | `Thunk_DestroyVectorRange40` | arg-shuffle tail thunk to 0x1401963b0: per 0x28-byte record frees the vector at +0x10 (begin/end/capacity) and zeroes it. |

## Corrections to earlier notes

1. **0x14015c1c0 / 0x14015c1e0 are not `vector` `_Xlen`/`_Xrange` twins.** Batch 5
   (agent 7) guessed that from the shape. Both are pure register shuffles that tail-jump
   to element-range destroyers: 0x140128ca0 destroys 0x30-byte string records and
   0x140128d30 destroys 0x18-byte vector headers. The register shuffle is
   `(arg1..arg4) -> (arg2, arg3, arg1, arg4)`, hence the callers pass four arguments
   while the targets use two.
2. **0x1401a8510 is misnamed** `Property_ScalarDeletingDestructorAlt`. Its vtable
   0x140369248 resolves to `.?AVmiiProperty@@`, not `Property`. It is outside this
   pass's `FUN_*`-only mandate, so it was left in place; the documentation agent may
   want `miiProperty_ScalarDeletingDtor`.
3. **HGE slot +0x300 is the render-target creator**, not a generic resource factory:
   target 0x14016cbb0 (`ADD RCX,8; JMP 0x1400839d0`) builds a `RenderTarget`
   (`.?AVRenderTarget@@`, vtable 0x140356768, 0x60 bytes). This settles the open
   "0x140179410 resource type unknown" item from batch 5.
4. **0x1400839d0 = `RenderTarget_New`** (0x60-byte object, vtable 0x140356768, created
   from HGE read hooks +0x28/+0x38/+0x48). Not renamed here (it is a `rep_*`, agent 3's
   scope), but it is safe to name in the `rep_*` audit.
5. **Vtable 0x1403672f0 = `.?AVHGE_Impl@@`** (was just `HGEVFTABLE`).
6. `0x1400e8140`'s "owning class unknown" is resolved: `MapShipBody` (see above).

## Skipped (55 `FUN_*`) — grouped with reasons

### Accessors whose field is not in `structures.md` (per this pass's brief: skip)

| addr | why |
|---|---|
| 0x140073340 | Predicate `[+0x48] != 0 && +0x15f8 >= 40.0` (`0x140354834`); `+0x15f8` is the combat value, but the 40.0 threshold's meaning is still unknown (batch 5 agent 6 reached the same point). Also the "true" path returns without setting AL, so the practical return is the low byte of the pointer. |
| 0x140073530 | Releases the object at `+0x48` through its vtable +0x48 and nulls it; `+0x48` is a state int on Creature, so the owning class is not provable (callers `ClickFunc`, `Scene_RebuildFromProfile`). |
| 0x140088950 | Partial init of a 0x28-byte sub-record `{ptr, 0, untouched, 0, 0}` at ComputeShader+0x50 and Effect+0x90; the untouched +0x10 qword and the field semantics are not documented. |
| 0x14016dde0 / 0x14016ddf0 | Bare setters of TextGrid `+0x1a4` / `+0x1a0`. `structures.md` documents no TextGrid at all (the only `+0x1a0` entry is Body `m_oid`), and the decompiler loses the argument in both `TextGrid_LayoutProjected`/`TextGrid_LayoutLocal` call sites, so the values cannot be named. |

### Creature/game logic left open from batches 4–5

| addr | why |
|---|---|
| 0x140078930 | `CalculateStats`, frees the `+0x1558` Link list, rebuilds it from parts with `+0x888 != 0` sorted by `+0x88c`, writes `+0x1560` into a part field. `+0x888/+0x88c` still unknown. |
| 0x140079ed0 | Caches three floats at `+0xd18/+0xd1c/+0xd20`, then picks the min-x/max-x part of the `+0x13a8` list by body `+0x128` and writes them into those parts (looks like gun convergence, target fields unproven). |
| 0x1400bee20 | Zeroes `+0x128` on every `+0x8c0` element whose byte `+0x71` is set. |
| 0x1400a2fb0 | Zeroes `+0x68..+0x88`, `+0xe8` and clears the string at `+0xd8`; class unknown (called from `Dialog_ExecuteChoiceActions`). |
| 0x1400a6210 | Predicate `+0xf8 == 0 && +0xf6 != 0`. |
| 0x1400fdec0 | Clears `+0x1d0`, a word at `+0x1a4`, `+0x1b8` and the string at `+0x1a8`; class unknown. |
| 0x1401102c0 | Selects state 5/7 from `dist*1000/+0x494 < 7200`; the 5/7 pair is not pinned. |
| 0x140110340 | Stores `+0x2a8` and two HGE randoms into `+0x2ac/+0x2b0`; HGE +0x100/+0x108/+0x110 undocumented. |
| 0x140162fe0 | `[obj+0x88] == 0 || [[obj+0x88]+0x28] == 7` — i.e. no master or master class code 7 (Node). What the callers want from it is not provable. |
| 0x140193090 | Clamps `+0xd8` between `+0xdc/+0xe0` and pushes it into a Box2D joint; motor speed vs target angle still unresolved. |
| 0x1401941f0 | Refreshes `+0x58` through `rep_14025ecf0` (an ICF-mislabelled body, not `free`); wrapper role undecidable. |

### HGE renderer internals

| addr | why |
|---|---|
| 0x140083450 / 0x1400834e0 / 0x1400835a0 | Three siblings forwarding 1–2 positions to the quad-draw helper at 0x14007e8a0; differ only in the source object (`+0x228` vs argument). Owning render class not established. |
| 0x140083760 / 0x140085e80 / 0x140085eb0 | Forward to a child vtable (+0x1a8 / +0x40 / +0x58 with `Render_SetBlendState`) gated on the hidden byte `+0x1c5`. |
| 0x1400838e0 | HGE slot +0x308 target: builds a 0x40-byte object from device hooks +0x28/+0x50 and stores two handles; no vtable/RTTI, so the resource type is unproven. |
| 0x140083d60 | Returns byte `+0x10`; class unknown. |
| 0x140085f40 / 0x140085f80 / 0x140085fc0 | The three actual draw calls behind HGE slots +0x2e0/+0x48/+0x50: set blend state from `quad+0x168 / +0x110 / +0x20` and call device vtable +0x40/+0x48/+0x50. The blend-state source offsets and device slots are undocumented; only +0x2e0 is tied to the quad (via `Gfx_RenderQuad`), so `Gfx_DrawQuad` for 0x140085f40 was considered and rejected as under-proven. |
| 0x140172aa0 | `sinf` + HGE +0x2e0; which quad parameter the sine drives is lost in the decompiler. |
| 0x14016cd10 / 0x14016cd30 | HGE vtable slots +0x320 / +0x318: one-line `object->vtable+0x10 / +0x8` float -> int adapters. Which slot is width and which is height is not provable without sprite-vtable evidence. |
| 0x14016cf30 | Forwarder through `newValidHGE` to vtable slot 0. |
| 0x1401783c0 | 0x98-byte compiler-generated struct copy; type unknown. |

### GUI / misc

| addr | why |
|---|---|
| 0x14012d1a0 / 0x14012d370 / 0x14012d600 | GUI-element base vtable callbacks; which of hover/press/release is still not provable. |
| 0x14012b4f0 | Constructor of a 0x118-byte stack record in `lootBoxCoins` (three 0x58 groups, floats 1.0 at +0x54/+0xac/+0x104); owning type not provable. |
| 0x1400a07a0 | Detach/clear sequence over a GUI binding object. |
| 0x140092e70 | Releases `+0x38` through vtable +0x20 with the `ptr != this` deleting flag, then clears it. |
| 0x1400f51c0 | Returns vtable +0x1d0 of a nested object, or 1.0. |
| 0x1400f8da0 | Tail call to an ICF-mislabelled `_Init_thread_footer` with `this+0x520`; target role unreadable. |
| 0x14010f1a0 | Global vector trim through an ICF-mislabelled CRT target. |
| 0x14011bbc0 | Returns `&DAT_1403ef5f8`; readers are an ICF `sscanf` replica and `FUN_14033536c`, global meaning unknown. |
| 0x140118699 | `INT3` padding, not a real function. |
| 0x1400bc5c0 | Editor-only no-arg handler `if (IsInEditor) call <mislabelled>; return 1`. |
| 0x1400e85a0 | Thunk to `_invalid_parameter_noinfo_noreturn` (reordered args). |
| 0x14016cf30 | see renderer table. |
| 0x140170210 | `if (p) return (*(*p+8))(p, this); return 0` — release through vtable slot 1; owning container unproven. |
| 0x14018f910 | 36-byte facet decref: fetch facet by locale id index, call vtable +0x10; owner class unproven. |
| 0x140191f40 | Destructor calling `(**vtable)(this,1)` only when `(byte[+0x28] & 7) == 7`. |
| 0x14019ae0f / 0x14019ae66 / 0x14019ae94 | Split pieces of one 0x20-stride `CopyEscadraName` loop — function-split artefacts. |
| 0x1401a4210 | Eight-field record constructor, no vtable. |
| 0x1401a47f0 | Four-field record constructor, no vtable. |
| 0x1401a4b40 | Destructor freeing `*(this+8)+0x20` then `*(this+8)`; only a `.pdata` xref, likely an EH cleanup — owner requires agent 1's funclet map. |
| 0x1401a8340 | Deleting destructor that calls the `Gui` destructor (0x14012b7a0, installs `GuiVFTABLE`) and frees **0xe78** bytes; the existing `Gui_ScalarDeletingDestructor` (0x14012cb40) destroys a **0xe80**-byte object. The 8-byte difference means this is not a plain Gui clone, and no documented 0xe78 class exists — left unnamed. |

`rep_*` were not touched. Notable `rep_*` facts found while resolving callers:
`0x1400839d0` = `RenderTarget_New`; `0x14016cd50` (embedded name `MessageBoxA`) is
`Texture_Load`; `0x14007e8a0` is the quad-draw helper, not `free`; `0x14025ecf0` is a
string builder, not `free`.

## Remaining work in the range

Only the 55 `FUN_*` above. No container/sort clone with a provable element type is left
in `0x140070000–0x1401FFFFF`: the remaining vector/map/sort-bodied functions in this
range already carry names, and the 0x14012xxxx container cores were finished by batch 5
agent 7. The largest remaining opening is the HGE renderer dispatch family
(0x140083xx–0x140085xx), which needs a dump of the device/sprite vtables rather than
more decompilation, and the TextGrid `+0x1a0/+0x1a4` fields, which need an update to
`structures.md` before they can be named.
