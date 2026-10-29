# Ghidra sweep, batch 8 agent 6 — `rep_*` re-match in `0x140200000–0x1402FFFFF`

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: every `rep_*` in `0x140200000–0x1402FFFFF`. **317 `rep_*`** at start.
**29 renamed, all plated. 0 created, 0 unreadable.**

| | before | after |
|---|---|---|
| `rep_*` in range | 317 | 287 |
| `FUN_*` in range (agent 8's) | 1 | 1 |
| total unnamed in range | 318 | 288 |

`0x140202010` was renamed by another agent **during** this pass
(`Moral_BuildMiniFigPanel`), so 317 − 29 = 288 but the final `rep_*` count is
287.

Appended **49 rows** to `rep-audit-2026-10-29-q3.tsv` (now 446 data rows):
29 `renamed` + 20 `stale label` rows whose partial identity this pass
sharpened. Append only; no prior row was rewritten.

## Method

All 317 in-scope `rep_*` are already present in `q3` (b6 agent 4 / b7 agent 4),
so this was a true re-match, not a first pass. Listing script
`/home/maksim/ghidra_scripts/B8A6List.java` produced address, body size, SHA-1,
embedded target class, direct callees, string literals, callers and data-xref
count for the whole range (`/tmp/opencode/b8a6_list.tsv`). No in-range `rep_*`
has a byte-identical twin. Then ~60 bodies were read with `batch_decompile`
(≤10 per call, all ≤0x2000 bytes except one 8,650-byte body at `0x140217470`
that was skipped by rule 6), plus targeted re-reads of already-named neighbours
(`Node::Node`, `SpriteLoad_`, `Hud_DrawDamageMarkers`,
`Body_SubtreeEqualsControlledNode`) to prove the new names rather than infer
them from the stale labels.

The shared script bundle is working again this batch (a root-level script
compiles); a **subdirectory bundle could not be loaded** by
`run_ghidra_script`, so the listing/check scripts were placed at the bundle
root.

## Renames (29)

### Node / Body

| addr | new name | body evidence |
|---|---|---|
| 0x14027f0e0 | `Node_CopyConstructor` | 782 B: ISerializable + NodeVFTABLE + the three sentinel lists, then `Node_InitDefaults` and the already-named `copyNode_` 0x14027f620; same prologue as the named `Node::Node` ctor at 0x14027f200 |
| 0x1402804b0 | `Node_InitDefaults` | 276 B: class name 'Node', CODE_NODE, default name, state=1, desowningTime=0.75, `AssignRandomId`, insert into `ALL_NODES_` (+0x60). Only called by the two Node constructors |
| 0x14021fe10 | `Body_SubtreeListsEqual` | 782 B: `Body_RebuildSubtreeList` on both bodies, drop links with id 0x38e, compare counts, `__RTDynamicCast`. Sole caller `Body_SubtreeEqualsControlledNode` 0x14021fdb0 already had a plate describing exactly this body |
| 0x1402a7cb0 | `Body_SetSlotOccupant` | 359 B: key match in the 0xa8-count 0x18-stride slot array at +0x50, `+0xbd4` hand-over, then battle-background or `ED_SHPWRK_AUTO` refresh |

### Sprite / Anistate

| addr | new name | body evidence |
|---|---|---|
| 0x1402debd0 | `Sprite_SelectAnimation` | 509 B: HGE `Random_Float` vs the per-animation probability at anim+4, copies anim name (+0x68) into sprite+0x90, `SpriteLoad_`, index at +0xec |
| 0x1402dd900 | `Anistate_CopyConstructor` | 418 B: Anistate vtable, 'Anistate' class name, copies name/type/+0x88/+0x90/+0x94 and the animation vector |
| 0x1402dfbe0 | `Anistate_ConstructorDefault` | 121 B: 'Anistate', type 0x4000000003 at +0x28, clears three strings and the vector |
| 0x1402ddcb0 | `Sprite_ConstructorDefault` | 240 B: SpriteVFTABLE, `CreateHGE(0x180)`, flag at +0x40, `createSprite_` installs 'Sprite' |
| 0x1402ec7a0 | `Sprite_CreateChild` | 214 B: `New(0x1a8)` + Sprite ctor, name/scale fields, push into the holder's vector at +0x18 |

### GUI / HUD / profiler

| addr | new name | body evidence |
|---|---|---|
| 0x1402566c0 | `Gui_SetScreenShade` | 114 B: writes the exact shade block (`DAT_143a1196c`, `DAT_143a11970`, `DAT_1403c0e58/5c`, `DAT_1403c12e8/ec`) and `SetLink(GLOBAL_143944470)` that the `Menu_Setup*Screen` functions fill from `<SCREEN>_BLACK` |
| 0x1402fc890 | `Hud_MarkerRenderLayerTimeFade` | 1,299 B: marker loop + `Trail_UpdateLayerTimeFade(layer)` |
| 0x1402fcdb0 | `Hud_MarkerRenderLayerZoomFade` | 1,007 B: same loop gated on zoom threshold + `Trail_UpdateLayerZoomFade` |
| 0x1402fd1a0 | `Hud_MarkerRenderLayers` | 981 B: layer 6 in campaign else 1..0x27, trail-zoom property, marker types 4/2/1, `Trail_DrawLayer` |
| 0x1402ab980 | `Profiler_RecordFrameTime` | 98 B: QPC -> µs since +0x378 via +0x380, 100-entry ring at +0x50/+0x48, +0x388 |
| 0x1402abed0 | `Profiler_InitClock` | 41 B: QPF -> +0x380, QPC -> +0x378 |

### Sound

| addr | new name | body evidence |
|---|---|---|
| 0x1402c99e0 | `Sound_QueueThrottled` | 496 B: per-id cooldown (`DAT_147fc7030` / `DAT_147fc71c0`), duplicate-suppressed sorted insert into `DAT_147fc7560`, queue trimmed to 3 |
| 0x1402db880 | `Sound_PlayNextQueued` | 128 B: pops the queue head and calls `PlayRadioSounds_` while `0x140392bf0 == -1.0` |
| 0x1402e4dc0 | `Sound_UpdateActiveChannels` | 573 B: 13 channel arrays, `Sound_IsFinished` test, destroy/compact, fizzled list `DAT_147fc76a0` |

### Shop / loadout / tutorial / radio

| addr | new name | body evidence |
|---|---|---|
| 0x140221700 | `Shipworks_BuyPart` | 240 B: node-list search by part name (+400) and +0x48, then `_BuyPartShop` |
| 0x1402217f0 | `Shipworks_RepairPart` | 423 B: same search, `+0x7ad` stock test / `repairPartsStats * amount` recursion |
| 0x1402aa810 | `Shipworks_BuyPartFromLibraries` | 1,040 B: builds the location + hull/armor/fuel/ammo/leg (+9 editor-only) library list, calls `Shipworks_BuyPart` |
| 0x1402aac30 | `Shipworks_RepairPartFromLibraries` | 1,040 B: same library list, calls `Shipworks_RepairPart` |
| 0x1402a8bf0 | `Loadout_ApplyAmmo` | 734 B: `PLANE_LOADOUTS` lookup by craft name +0x3f8, `Item_Constructor` per ammo record, custom-list path via +0xa20 |
| 0x1402a7820 | `Tutorial_BuildStepList` | 808 B: `CreateTriggerVal` 'TUTORIAL'/'PRESENT4'/'PRESENT2', `Sort_PartitionByStatsKey`, append ids to +0x4f0 |
| 0x1402abfd0 | `RadioBeacon_ScalarDeletingDtor` | 214 B: unlink from `DAT_147fc6db8`, decrement count, `ISerializable_Destructor`, conditional free |

### Containers / math

| addr | new name | body evidence |
|---|---|---|
| 0x1402e5dd0 | `Vector_InsertStride12` | 638 B: `vector<12-byte>::insert`, same shape as the named `Vector_Insert32` 0x140058550 |
| 0x1402ea960 | `VectorGSI_DestroyVector` | 173 B: destroy 0x38-stride elements, free, zero |
| 0x1402eb820 | `VectorGSI_DestroyRange` | 49 B: destroy loop over `[param_2,param_3)` step 0x38 |
| 0x1402e51c0 | `Vec2_FloorIfGridEnabled` | 52 B: `floorf` both components when `DAT_1403ef317` is set; directly after the named `Vec2_TransformByMat2` |

## Stale labels sharpened (20 rows appended)

No name applied; each row in the TSV now carries the concrete role:

* **0x1402f3fd0** — 4-float colour/alpha ramp from a fraction and a
  damage/zoom level, mixed by `DAT_143a119a0` and `pow(1-scale,12)`. The b7
  hand-over asked for a re-match; the caller pair (`FUN_140316a50`,
  0x1402c93a0) shows an aircraft/formation input, not a UI colour.
* **0x1402dfe10** — the `SetBackground`-side Sprite media loader (the full
  loader is the already-named `SpriteLoad_` 0x1402dfef0); loads anim +0x78 and
  the second media +0x80, logs the same Sprite::load error.
* **0x1402c8fd0 / 0x1402c9230 / 0x1402c8b80 / 0x1402c93a0** — the Level.cpp
  aircraft formation/weapon-bay cluster: availability scan with flag masks and
  RbTree insert; the `+0x3c4 == 500` state reset with `CHECK ERROR` at
  Level.cpp:1054; the two formation updaters (`+0x150`/`+0x154`/`+0x15c`).
* **0x1402f6910 / 0x1402fa180** — HUD marker passes. 0x1402fa180 is
  **not** `Hud_DrawDamageMarkers` (that is 0x1403007f0): it draws bodies that
  share the controlled body's name string, colour-banded by
  `calcDMGPercentage`.
* **0x1402fd9f0 / 0x1402fdc60** — D3D quad/vertex blits for five 8-byte
  records, technique table `DAT_143a13998[0x23..0x27]` / `[0x28..0x2c]`.
* **0x1402e6b00** — float-pair introsort (insertion ≤0x100 B,
  `Sort_PartitionVec2`, heapsort fallback).
* **0x1402dcf30** — `Body_TearOffFromFrame`'s sibling relink helper (walks the
  frame list at node+0x230).
* **0x1402dcbc0 / 0x1402ddad0 / 0x1402e5000 / 0x1402e0830 / 0x1402ab940 /
  0x1402abf90 / 0x1402e5200 / 0x1402f4150** — property setter, Sprite ctor
  variant, finished-sound position commit, zero-arg forwarder, two-global
  vector reset, RadioBeacon ctor front-end, `vector<vector<CHN*>>` fill ctor,
  and the timer-token validity check. Details in the TSV.

## Hand-offs

1. **`0x1402f3fd0`** — now has two concrete callers; a colour/alpha ramp used
   by aircraft formation and `FUN_140316a50`. Naming needs the meaning of
   param_2/param_3 (fraction and level/altitude?), not more decompilation.
2. **`0x1402fa180`** vs `Hud_DrawDamageMarkers` — two near-identical marker
   passes with different body predicates (name equality vs
   `Body_IsBadlyDamaged`); the caller split should decide whether one is the
   "duplicate/sister ship" marker.
3. **`0x1402fd9f0` / `0x1402fdc60`** — the technique index tables
   `DAT_143a13998[0x23..0x2d]` are the last unnamed part of the marker/quad
   blit family; a read of the `DAT_143a13998` object's initialiser would name
   both.
4. **`0x1402e3580`** (b7 hand-over, sound-name normaliser) was **not**
   re-read this pass — it remains the highest-value stale body in the range.
5. **`0x1402c8fd0`** — sets part `+0x33c = 4`; the same field is read by
   0x1402c93a0, so the two together define the aircraft weapon-state enum.
