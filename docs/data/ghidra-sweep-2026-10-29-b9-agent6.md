# Ghidra sweep, batch 9 agent 6 — `rep_*` re-match in `0x140200000–0x1402FFFFF`

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: remaining `rep_*` in `0x140200000–0x1402FFFFF`. **287 `rep_*` at start**
(batch 8 left 287 after its own 29 renames plus one neighbour rename).
**85 renamed, all plated. 0 created, 0 unreadable. 15 stale rows sharpened.**

| | before | after |
|---|---|---|
| `rep_*` in range | 287 | 195 |
| `FUN_*` in range (agent 9's) | 1 | 1 |
| total functions in range | — | 851 |

The 7-function gap (287 − 85 = 202 vs 195 left) is other agents' concurrent
renames inside the range during this pass (e.g. `0x14023c820` →
`Ship_RecreateFromBackup` by agent 2). Nothing was renamed twice.

Appended **100 rows** to `rep-audit-2026-10-29-q3.tsv` (now 547 lines = 546 data
rows; 157 renamed / 389 stale after append): 85 `renamed` + 15 `stale label`.
Append only; no prior row rewritten (`/tmp/opencode/q3_before.tsv` is the
pre-append copy).

## Method

All 287 were already present in `q3` from batches 6–8, so this was a re-match.
Listing script `B9A6List` (bundle root `/home/maksim/ghidra_scripts/`) produced
address, body size, current label, direct callees, callers and string literals
for the whole range (`/tmp/opencode/b9a6_list.tsv`); a second script dumped all
function names (`/tmp/opencode/b9a6_names.txt`) so every proposed name could be
checked against the name-collision rule (token-subset) before writing.

Then ~110 bodies were read with `batch_decompile` (≤10 per call). All reads were
≤0x2000 bytes; the 8,650-byte `0x140217470` and the 4,886-byte `0x140222510`
were left unread (rule 6). Every rename carries a 5-section plate written from
the body, not from the stale `rep_*` label; several labels were proved actively
wrong (`rep_..._free` that is a `vector<bool>` setter, `rep_..._memcmp` that is a
name lookup, `rep_..._New` that is a red-black-tree insert, `rep_..._Xlength_error`
that is a list push).

`run_script_inline` writes the supplied source to the file named after the class,
so it overwrote the on-disk `B9A6List.java`; re-running needs the full source.

## Renames (85)

### Containers / CRT helpers
`VectorStride8_InsertValueIntByte`, `VectorStride8_InsertValueFloatByte`,
`VectorStride8_InsertValuePair32`, `VectorStride64_InsertDefault`,
`VectorStride64_DestroyRange`, `VectorStride8_InsertPtrFieldFromStride24Range`,
`VectorStride16_InsertDefault`, `VectorStride16_InsertValue`,
`VectorStride16_Resize`, `VectorStride24_ResizeDefault`, `Vector24_ConstructFillN`,
`VectorBool_SetElement`, `QwordList_CopyConstructor`, `QwordList_ScalarDeletingDtor`,
`QwordList_*`, `RbTree_InsertNode56`, `List_PushBackEscadraName`,
`List_PushBackPayload24`, `List_RemoveEntriesWithoutId`,
`Heap_FreeOverAlignedStride3`, `Heap_FreeOverAlignedStride272`,
`Streambuf_Overflow`, `String_ReplaceRange`, `String_RemoveChars`,
`String_IncrementNumericSuffix`, `String_StripAngleBracketTags`.

### Math / geometry
`Math_InverseCubeFalloffCapped`, `Math_NormalizeAngleDifference`,
`Math_CircleCircleIntersections`, `Math_GenerateZigzagPoints`,
`Math_ProximityFactorToPlayer`, `Math_RaySegmentIntersection`,
`Math_SegmentSegmentIntersect`, `Polygon_RaycastNearestHit`,
`Transform_EqualsApprox`.

### Rendering / HUD
`Gfx_DrawLineClippedToRect`, `Gfx_DrawCircleClipped`, `Gfx_DrawArcClipped`,
`Gfx_DrawDashedWorldLine`, `Gfx_DrawAxisArrow`, `Gfx_DrawSolidRect`,
`Hud_DrawVerticalScale`, `Hud_DrawRotatedLabelAndClear`,
`Sprite_LoadByNameAndSetFields`, `Color_SetPulsingAlpha`,
`Sky_ComputeColourRamp`, `Time_GetTicksMsAbsolute`, `FrameCounter_Update`,
`Window_ComputeAdjustedClientRect`.

### GUI / shop / fleet
`Gui_SetActiveElement`, `Gui_ClearActiveElement`, `Gui_CloseRadioPanel`,
`Gui_ResetHelpIcons`, `Map_SetSelectedObject`, `Map_FindFreeSpawnPosition`,
`Shop_GiveItemToPlayerIfMissing`, `Shop_SellPartValue`,
`Shop_ReturnItemToPlayer`, `Shipworks_TransferPartToShip`,
`Ship_RebuildAfterPartEdit`, `Ship_AttachFirstPartTo`,
`Fleet_TallyPartNameCounts`, `Escadra_CollectItemsToPlayer`,
`Roster_PruneReturnNonEmpty`, `Creature_SpawnRecalculateStats`,
`Creature_CreateEngineThrustEffects`, `Creature_CanRefuelAtNearestDesign`,
`ShipDesign_FindNearPointSorted`, `Game_LoadMapSeria`,
`City_RebuildSpecialLocationShips`, `Radio_AdjustAndPlaySound`.

### Body / Node / Stats / physics
`Body_FindFirstSelectablePart`, `Body_DestroyChildrenInState910`,
`Node_CollectChildrenByOwnerId`, `Node_FindByName`,
`Stats_CopyConstructor`, `Stats_Destructor`, `Stats_ConstructorDefault`,
`Stats_GetSortCategory`, `StatsLibrary_FindByName`,
`ObjectsLibrary_Destructor`, `ObjectsLibrarySingleton_ScalarDeletingDtor`,
`Profile_IsVersionWordSet`, `Profile_PickUnusedRandomFloat`,
`Npc_FindFlaggedFromProfile`, `Input_RestoreCursorClip`.

Full per-function evidence is in the 85 `renamed` rows of `q3.tsv`; the plates on
the functions themselves are longer (summary / `Algorithm:` / `Parameters:` /
`Returns:`).

## Stale labels sharpened (15 new rows)

Read but not named, each with a concrete role now in the TSV:

* **0x140210450 / 0x1402697e0** — the `BOOL_147fc6f80`-gated part buy/sell pair
  (same `{+8 part, +0x10 amount}` layout); 0x1402697e0 was named
  `Shop_SellPartValue`, 0x140210450 still needs the flag's meaning.
* **0x140269690** — remove a ship from the fleet map by RbTree key and hand its
  items to the player.
* **0x140216bb0** — exact zoom-scaled offset formula (camera/target/shake/zoom).
* **0x140221be0** — sort a ship's children by stats and re-attach them.
* **0x14024bf80** — clears per-body flag `+0x220` on all live bodies (flag meaning
  open; same field toggled by 0x140246de0).
* **0x14024d360** — timer-gated drum ambient: spawns a 5×5×5 shell at the player
  and plays `STOP` + `drums_01`.
* **0x140242c10 / 0x1402426d0 / 0x140242920** — the `DAT_143a15a50` named-entry
  map, the `newNode_+0x100` destroy-by-name walk, and the `"A_"` prefix group
  close (all use vtable `+0x48`).
* **0x140237e30** — fraction-of-lines text wrapper that replaces non-punctuation
  characters with `_`.
* **0x140223f60 / 0x140225240** — profile body-copy rebuild and the global name
  registration in `DAT_143a1c3a0`.
* **0x14024a4d0** — camera-transform up to 500 points and draw index triples via
  HGE vtable `+0x2d0`.
* **0x14027fb50** — attach a joint entry to `owner+0x110` and create the Box2D
  joint when the owner is `GlobalNode_`.
* **0x140246de0** — the paired-body connection-line pass (two 0x1900-entry
  passes, |y0−y1| < 10 filter).

## Hand-offs

1. **`0x1402e3580`** (4,845 B sound-name normaliser, batch-8 hand-off) was again
   **not** re-read — it exceeds the per-call budget combined with anything else
   and remains the highest-value stale body in the range.
2. **`0x140217470`** (8,650 B) and **`0x140222510`** (4,886 B) skipped by rule 6.
3. **`BOOL_147fc6f80`** gates at least six part-economy functions in this range
   (buy/repair/sell/return). One read of its setter would name the whole family.
4. **`DAT_143a13e00/143a13e08`** — the element link pair behind
   `Gui_SetActiveElement`/`Gui_ClearActiveElement`; `+0x328`/`+0x330` are the
   enter/leave vtable slots. Confirming "hover" vs "focus" would let the plate
   drop the neutral "active element" wording.
5. **Wrong-name rule**: nothing already-named **outside** `rep_*` in this range
   looked provably wrong, so no `**@agent6 -> rename**` proposal was posted.
   Every misleading name found here was itself a `rep_*` and therefore inside the
   slice.
