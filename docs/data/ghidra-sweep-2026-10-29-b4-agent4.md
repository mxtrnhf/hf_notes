# Unnamed-function sweep, batch 4, 2026-10-29 — agent 4

Ranges: `0x140070000–0x14011FFFF` and `0x1401B0000–0x1401FFFFF`
(large leftovers + `0x1401B`–`0x1401F` stragglers). Program
`Highfleet.exe.unpacked.exe` v1.163.

Scope note: the two ranges held **64 `FUN_*`**. All `rep_*` copies were left
alone (same policy as batch 3 agent 2). **30 were renamed** with
`rename_function_by_address` and given a doc-style plate comment
(summary / Algorithm / Parameters / Returns); **34 remain** (listed below).

Several priority addresses from the assignment (`0x1401b5420`,
`0x1401b6e00`, `0x1401bc280`, `0x1401bc6b0`, `0x1401bccb0`, `0x1401bdc20`)
were already named in earlier waves (`Ballistics_PredictHit`,
`Gun_SwapAmmoCounters`, `Arcade_ClearCreatureSlots`,
`Battle_ApplySurvivorState`, `ShipLink_SnapAllBodies`,
`Battle_ChooseDeployShip`) and were not touched.

## Renames — dialogue / Shipworks / scene

| addr | new name | description |
|---|---|---|
| 0x1400b1440 | `Dialog_ExecuteChoiceActions` | 0x77aa-byte interpreter for dialogue answer action tokens (attitudes, GIFT/ASK_*, TRG_ADD, NPC_JOINED, fleet/city effects); called from `mainDialogWithChoices`, `!ClickFunc`, `Dialog_HandleAnswerKey` |
| 0x1400dd0d0 | `Shipworks_BuildResultCards` | builds the ED_SHPWRK_MINIFIG card grid + repair buttons + `Precombat_BuildStatRows` for the post-battle/shipworks result screen |
| 0x1400beea0 | `Scene_InitializeForMode` | resets camera/render globals, defines the part catalogue, loads `Designs/<name>.seria`, sets mode backgrounds/zoom when entering menu/game/editor |
| 0x1400dac70 | `Editor_ToggleSelectionAtPoint` | editor hit-test / add-or-remove selection in the two global editor selection vectors |
| 0x1400bbb10 | `Editor_HandleClickMode9` | editor click handler, edit mode 9: swaps the hovered element into the selection |
| 0x1400bc580 | `Editor_HandleClickMode5` | editor click handler, edit mode 5 |
| 0x1400d40e0 | `Roster_RemoveEntry` | destroys a roster entry and prunes the global roster |

## Renames — strategic fleet / aircraft AI (`0x1400E–0x1400F`)

| addr | new name | description |
|---|---|---|
| 0x1400ebc40 | `AircraftGroup_MergeInto` | merges a same-side aircraft group into another, recalculates stats, refreshes `LOADOUT_LIST` / `CRAFT_UNREADY_LIST` |
| 0x1400f00c0 | `StrategicFleet_TryDetectContact` | IRST/ELINT detection test, resets the 24 h scan timer, reveals the contact via `showMissileInShop` |
| 0x1400f07c0 | `Fleet_BuildManeuverPath` | builds the curved turn path from current position to a packed destination |
| 0x1400f1490 | `AircraftGroup_FindAttackTarget` | current-target lookup else enemy-ship scoring/range selection |
| 0x1400f5be0 | `StrategicFleet_SelectPursuitTarget` | fuel-range candidate scoring/sort, sets state 4 PURSUE and rebuilds the path |
| 0x1400f8eb0 | `Escadra_MergeAdjacentFleet` | absorbs an adjacent fleet (ships, shop items, crew/fuel, home link) |
| 0x1400f9a40 | `StrategicFleet_UpdateAIState` | per-frame strategic-fleet AI state machine (IDLE/TRADE/PATROL/PURSUE/BOOMER/SEARCH/REFUEL/FLAGSHIP_LOST) + `STATE ...` debug labels |

## Renames — creature / property helpers

| addr | new name | description |
|---|---|---|
| 0x140074050 | `Creature_CanBeRepaired` | evac pods or damage above the repair threshold; gates the Shipworks repair card |
| 0x1400782b0 | `Creature_DestroyPartsWithLogicIdD84` | destroys parts whose +0x3c4 logic id is 0xd84 |
| 0x140079b20 | `Creature_BroadcastCommand19A` | sends part command 0x19a with a scalar to every body part |
| 0x140092ff0 | `Property_SetFloat168` | float setter for the field object at +0x168 |
| 0x140093020 | `Property_SetFloat158` | float setter for the field object at +0x158 |
| 0x140093050 | `Property_SetFloat148` | float setter for the field object at +0x148 |
| 0x140104950 | `Node_RelinkAndNotify` | `Node::Relink` + virtual +0x80 notification |

## Renames — containers / render / HUD / misc

| addr | new name | description |
|---|---|---|
| 0x14008dc30 | `VectorStride32_Insert` | insert one 0x20-byte element (capacity growth + tail copy) |
| 0x140086c90 | `StreamReader_ReadByte` | buffered byte read with virtual refill; 0xffffffff at EOF |
| 0x140094180 | `ComputeShader_GatherParamsAndDispatch` | gathers 9 floats from child objects (+0x1c8..+0x238) into +0x138..+0x158 and dispatches the +0x118 compute shader 3x1 |
| 0x14011c760 | `Hud_RegisterMarkerForBody` | registers a HUD marker keyed by the smallest part +0x114 type, global 40000-entry table |
| 0x1400f3a20 | `Object_GetSubObject2A0` | returns `this + 0x2a0` |

## Renames — `0x1401B`–`0x1401F` stragglers

| addr | new name | description |
|---|---|---|
| 0x1401b45f0 | `AllocArrayStride40` | `operator new[]` for 0x28-byte elements (aligned-allocation convention) |
| 0x1401be450 | `Geometry_PointsNearlyEqual` | point-coincidence / separation predicate (box half-size + squared radius) |
| 0x1401c2ba0 | `Captain_CreatePanelForSlot` | slot-id -> rectangle preset, forwards to the panel builder `FUN_1401a7120`; called twice right after two Captain objects are built in `Scene_ResetGlobalLinks` |
| 0x1401c7270 | `FX_SpawnExplosionDebris` | explosion particle spawner (`sparcles.psi`, `debris.psi`, `airblast_01.psi`, `dust_JET2.psi`; strides/cloudblast/airblast/explosion_* sprites) |

## Skipped / open (34 `FUN_*` remain)

Grouped by reason. Addresses and sizes (bytes) are from the final listing.

### Unknown field semantics (agent 2's batch-3 reasons still stand)

* **0x1400702a0** (33) - sum of four floats at +0x15e8..+0x15f4; quantity unknown.
* **0x140070620** (44) - `(a/b * float@+0x1614)/1000`; fuel-tonnage shape but +0x1614 undocumented.
* **0x140073450** (72) - `name == "Titan" || float@+0x1604 != 0`.
* **0x1400734a0** (52) - list at +0x13d8 has more than 5 entries.
* **0x1400738d0** (48) - sets +0x80c = 1.0 on the +0x1498 part list.
* **0x140078930** (513) - rebuilds the +0x1558 Link list from parts whose +0x888 != 0
  (caller `EDITORCPP`); +0x888 role unknown.
* **0x140079790** (126) - sets the per-player-slot global timer `DAT_147fc7020[i]` to 4.0.
* **0x140079ed0** (649) - stores 3 floats at +0xd18/+0xd1c/+0xd20, then writes the
  min/max part (by part+0x1f8) fields and rebuilds the +0xd28 link list. Which
  three quantities these are is not recoverable; called from `CreatureUpdate`.
* **0x1400a2fb0** (62) - clears +0x68..+0x88 and the string at +0xd8; class unknown.
* **0x1400a6210** (24) - predicate `+0xf8 == 0 && +0xf6 != 0`.
* **0x1400bee20** (58) - zeroes +0x128 on every +0x8c0 element with byte +0x71 set.
* **0x1400f51c0** (52) - returns vtable +0x1d0 result or 1.0.
* **0x1400fdec0** (61) - clears ints at +0x1d0/+0x1a4 and the string at +0x1a8.

### Render / GUI plumbing (generic, would need the owning class)

* **0x140083450** (137), **0x1400834e0** (182), **0x1400835a0** (177) - three
  siblings that call the draw helper inside `rep_140079ca0...` with 1 or 2 quads;
  differ only by source object (+0x228 vs argument) and quad count.
* **0x140083760** (54) - forwards `(param_2+8, 1, 1.0, 0)` to child vtable +0x1a8.
* **0x140083d60** (5) - getter for byte +0x10.
* **0x140085e80** (36), **0x140085eb0** (144) - hidden-flag gated forwards to a
  child vtable (+0x40 / +0x58 with a blend state).
* **0x140088950** (21) - 0x28-byte object field init (sets [0],[1],[3],[4]).
* **0x140092e70** (44) - detaches the object at +0x38 and clears the field.
* **0x1400a07a0** (178) - detach/clear sequence over a GUI binding object.

### Editor handlers with undocumented mode enum

* **0x1400bc5c0** (32) - editor-only no-argument handler; called from
  `Input_HandleMouseMove`, body is one call into the mode handler. Mode flag not
  visible in this body, so no honest name.
* **0x1400bee20** - see above.

### CRT / thunk / padding

* **0x1400e8140** (67) - deleting destructor with a Link at +0xa48; owning class
  (0xa48+ sized) not certain.
* **0x1400e85a0** (20) - thunk to `_invalid_parameter_noinfo_noreturn`.
* **0x1400f8da0** (12) - tail call into misnamed `_Init_thread_footer` target.
* **0x14010f1a0** (69) - global vector trim through a misnamed CRT target.
* **0x140118699** (7) - INT3 padding, not a real function.
* **0x14011bbc0** (8) - returns `&DAT_1403ef5f8`; global meaning unknown.

### Single-field helpers left unnamed deliberately

* **0x1401102c0** (117) - called only from `StrategicFleet_UpdateAIState` when
  state == 5; sets state 5 when `dist*1000/field+0x494 < 7200`, else state 7.
  The 5/7 pair is BOOMER/REFUEL in the debug string order but the branch
  condition is not understood well enough for a name.
* **0x140110340** (180) - stores +0x2a8 and draws two random values into
  +0x2ac/+0x2b0 through HGE +0x100/+0x108/+0x110; the HGE slot meanings are not
  documented.
