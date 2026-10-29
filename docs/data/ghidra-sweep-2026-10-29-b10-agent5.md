# Ghidra sweep, batch 10 agent 5 — remaining `rep_*` in `0x140200000–0x1402FFFFF`

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: remaining `rep_*` in `0x140200000–0x1402FFFFF`.

**51 renamed, all plated. 0 created, 0 unreadable. 26 stale rows sharpened.**

| | before | after |
|---|---|---|
| `rep_*` in range | 195 | 137 |
| `FUN_*` in range | 0 | 0 |
| named (non-`rep_`/`FUN_`) in range | 656 | 714 |
| total functions in range | 851 | 851 |

195 − 51 = 144 vs 137 left: the 7-function gap is other agents' concurrent
renames inside the range during the pass (e.g. `0x1402e3580` →
`Sound_ResolveVariantName` by agent 9). Nothing was renamed twice.

Appended **77 rows** to `rep-audit-2026-10-29-q3.tsv` (now 624 lines = 623 data
rows; 208 renamed / 415 stale after append): 51 `renamed` + 26 `stale label`.
Append only; no prior row rewritten.

## Method

Fresh listing script `B10A5List` dumped all 5,424 function names to
`/tmp/opencode/b10a5_names.txt` and the 195 in-scope `rep_*` to
`/tmp/opencode/b10a5_list.tsv` (address, body size, label, direct callees,
string literals, callers, data-xref count).

Bodies were read with `batch_decompile` (≤10 per call). All reads were
≤3.1 KB; the ten largest in-scope bodies (`0x140217470` 8,650 B,
`0x140222510` 4,886 B, `0x14027c170` 4,648 B, `0x1402fa610` 6,041 B,
`0x1402f73f0` 2,819 B, `0x1402641f0` 2,764 B, `0x1402d3150` 2,744 B, etc.)
were not re-read by rule 6 and keep their batch-6..9 plates.

Every rename was checked against the token-subset collision rule using the
fresh name dump; `Node_FindChildByNameInVector` and
`Escadra_HasFuelToReachNearestDesign` were rejected because bare `Node` and
`Escadra` functions exist, and became `NodeList_FindChildByName` /
`PlayerEscadra_HasFuelToReachNearestDesign`. Names were written only where the
body proves the role; the 26 read-but-unnamed bodies got a sharper stale row
stating exactly what blocks the name.

## Renames (51)

### Containers / CRT helpers (17)
`VectorStride24_DestroyVector`, `VectorStride40_Assign`,
`VectorStride48_CopyRange`, `VectorStride48_InsertValue`,
`VectorStride48_PushBack`, `VectorStride64_DestroyVector`,
`VectorStride80_Assign`, `VectorStride80_DestroyVector`,
`VectorGSI_DestroyElements`, `VectorGSI_InsertValue`,
`HashMap64_EraseEntry`, `RbTree_EraseKeyRange`,
`Map_EraseKeyRangeWithVectors`, `List_PushBackPointer`,
`Sort_FloatPairIntrosort`, `TimerToken_IsValid`, `Scene_ClearGlobalListTables`.

### Object model / lifecycle (10)
`Level_Destructor`, `LevelSingleton_ScalarDeletingDtor`,
`SX_SingletonScalarDeletingDtor`, `Sound_Constructor`,
`Level_ReleaseCompletedObjects`, `NodeList_FindChildByName`,
`NodeList_RemoveAndDestroyChild`, `Body_DestroyByDisplayName`,
`Body_TryPairWith`, `Frame_DetachSiblingLink`.

### Rendering / HUD / D3D (7)
`Hud_DrawGroundMarkerPass`, `Hud_DrawSameNameBodyMarkers`,
`D3D_DrawShipCardRange`, `D3D_DrawShipCardRangeNoFlag`,
`Gfx_SetMirroredOrthoProjection`, `Fx_UpdateDrumAmbient`,
`Sprite_UpdateAnimation`.

### Aircraft / ship design (4)
`AircraftGroup_UpdateFormationSlots`, `AircraftGroup_UpdateAttackMove`,
`ShipDesign_FindNearestToPoint`, `ShipDesign_FindNearestInList`.

### Sound (4)
`Sound_ClearQueuedSounds`, `Sound_CommitChannelPosition`,
`Sprite_LoadAnimationAndMedia`, `Sprite_CreateAnimation`.

### Game / economy / map (9)
`Game_TogglePauseForActiveProfile`, `PlayerEscadra_HasFuelToReachNearestDesign`,
`ItemList_ConsumeCount`, `EscadraMap_AddCountByName`,
`Localization_FindNoteMiniPanelEntry`, `Dialogue_RegisterStringInGlobalTable`,
`Gui_DestroyElementsWithPrefix`, `GlobalRenderLists_DestroyAll`,
`FX_SampleTrailAngle`.

Full per-function evidence is in the 51 `renamed` rows of `q3.tsv`; the plates
on the functions themselves are longer (summary / `Algorithm:` /
`Parameters:` / `Returns:`).

Notable proofs:

* **`0x1402c9780` / `0x1402c9730` / `0x1402e2a10`** — vtable stores name the
  classes outright (`LevelVFTABLE`, `Singleton<Level>VFTABLE`,
  `Singleton<SX>VFTABLE`) and the globals (`LevelSingleton`, `SXSingleton`),
  so the destructor pair is no longer guessed.
* **`0x140210c20`** — the FNV-1a 64 basis/prime constants and the `+0x30`
  bucket mask prove a hash-map erase, not a "free" helper.
* **`0x1402e27d0`** — its field block (`+0x9c..+0xac`, `+0x2c` channel id) is
  exactly the block consumed by `Sound_CommitChannelPosition 0x1402e5000`,
  which anchors it as the sound-channel constructor.
* **`0x1402426d0`** — compares `body+0xa90` (length `+0xaa0`) and calls
  vtable `+0x48`, i.e. destroy-by-name, in the `newNode_+0x100` list.
* **`0x14024d360`** — timer, `CreateShell_` 5×5×5 at the player, and the
  little-endian `STOP` / `drums_01` literals make the drum ambience certain.

## Stale labels sharpened (26 new rows)

Read but not named, each with the blocking field in the TSV:

* **`0x1402ab6a0` / `0x1402ab6f0` / `0x1402eb500` / `0x1402eb5e0` /
  `0x1402eb620` / `0x1402ab760`** — singleton/member destructors: the
  destructor shape is proven, the class is not (no RTTI/name string in body).
* **`0x1402898f0` / `0x140289970` / `0x140289ca0`** — the three Location
  member destructors; member offsets are now exact but element types are not.
* **`0x1402eaa10` / `0x1402eaae0` / `0x1402e2c10` / `0x1402899e0`** —
  container/object-vector destroyers with exact strides (0x38 / 8) and the
  vtable constants, class unknown.
* **`0x1402abf90`** — RadioBeacon ctor front-end; blocked only by the
  name-collision rule (`RadioBeacon_Constructor` is a token subset).
* **`0x140215110`** — Tutorial trigger arming (`CreateTriggerVal` on
  `profile+0x3f0` with `"TUTORIAL"`); the verb is not provable.
* **`0x1402c8fd0`** — weapon-bay availability scan; exact masks and the
  `+0x33c = 4` state are recorded, no narrower name.
* **`0x1402333c0` / `0x1402c88e0` / `0x14028a960` / `0x1402d41d0` /
  `0x1402e0830` / `0x140225ee0`** — small math/record/accessor bodies whose
  identity depends on an unnamed callee or on an unknown record type.

## Hand-offs

1. **BOOL_147fc6f80** still blocks the part-economy pair
   (`0x140210450` / `0x1402697e0`); one read of its setter names both.
2. **`0x140217470`** (8,650 B), **`0x140222510`** (4,886 B),
   **`0x1402fa610`** (6,041 B), **`0x14027c170`** (4,648 B) remain
   unread-by-rule-6 and are the largest stale `rep_*` in the range.
3. **`0x1402eaa10`** shares the 0x38 stride with `GSISymbolEntry` but frees a
   `Link` at `+0x10`; its caller `DtorGlobal_ExplosionDebrisLink` suggests a
   debris-link array, not the GSI vector.
4. **Wrong-name rule**: nothing already named outside `rep_*` in this range
   looked provably wrong, so no `**@agent5 -> rename**` proposal was posted.
5. `run_script_inline` overwrote the on-disk `B10A5List.java` with the supplied
   source (it is the same source); re-running needs the full body again.
