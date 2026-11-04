# Unnamed-function sweep, batch 3, 2026-10-29 — agent 2

Ranges: `0x140070000–0x14007FFFF` and `0x1400A0000–0x14011FFFF`
(engine / render / audio / resources, map and fleet data). Program
`Highfleet.exe.unpacked.exe` v1.163. Every entry below was renamed with
`rename_function_by_address` and given a doc-style plate comment
(summary / Algorithm / Parameters / Returns).

Scope note: at the start this range held **119 `FUN_*` and 256 `rep_*`**
functions. The `rep_*` ones were left untouched: almost all are duplicate
copies of functions whose real target already carries a name (the `rep_`
suffix logic), and renaming them adds no information. **74 `FUN_*` were
named**; 45 `FUN_*` remain (see "Skipped / open").

Naming follows the earlier notes: `<Subsystem>_<Verb><Object>`, with
`Property_`, `Vector*`, `List_`, `RbTree_`, `Sort*` and `Node_` prefixes for
the template-shaped helpers.

## Renames — creature / design helpers (`0x140070000–0x14007FFFF`)

| addr | new name | description |
|---|---|---|
| 0x1400702d0 | `Creature_CollectExtremeParts` | min/max-x/y parts by transformed slot origin, up to 4 `{part,x,y}` records |
| 0x140070f20 | `Creature_ComputePartBounds` | AABB over parts, centre cached in global `DAT_1403ef110` |
| 0x140073900 | `Creature_CopyDesignBlock` | copies 15 floats +0x80..+0xb8 into +0x1968..+0x19ac |
| 0x1400741c0 | `VectorUInt32_PushBack` | append one 32-bit value to a vector (grow on full) |
| 0x140074220 | `Creature_ResetWeaponReloadTimers` | loaded rounds / reload step from Stats +0x148 / +0x14c |
| 0x1400743c0 | `Property_RegisterMassXpFields` | `massXP` (+0x48) and `availableMassLevel` (+0x4c) |
| 0x140077840 | `Property_RegisterMarkFields` | `design`, `timeCreation`, `designName`, `&bounding.x/y`, `m_msg_power`, ... |
| 0x140079c20 | `Creature_UpdateDesignStats` | recompute +0x1980/+0x1984/+0x1988 and refresh the design cache |

## Renames — property setters (`0x1400A0000–0x1400A1FFF`)

| addr | new name | description |
|---|---|---|
| 0x1400a0010 | `Property_SetFloat` | scalar float setter with change notification |
| 0x1400a0060 | `Property_SetInt` | scalar int setter |
| 0x1400a00b0 | `Property_SetFloat16` | 16-float block setter |
| 0x1400a0270 | `Property_SetReferenceList` | reference field, rebuilds the target list |
| 0x1400a0320 | `Property_SetReferenceAt` | reference field, single element from an indexed array |
| 0x1400a0550 | `Property_SetFloat4` | four-float setter |
| 0x1400a0660 | `Property_ClearOwnedVectors` | frees the +0x18 and +0x30 vector buffers |
| 0x1400a0710 | `Property_AddToSelectionVectors` | append by bit mask to the +0x18 / +0x30 lists |
| 0x1400a1000 | `List_MergeSortByTargetF8` | stable merge sort of a circular list by target +0xf8 |

## Renames — containers / sorting / RB tree (`0x1400A1700–0x1400EFFFF`)

| addr | new name | description |
|---|---|---|
| 0x1400a1700 | `List_InitSentinelFlagged` | empty circular list header, both +0x18 flags 1 |
| 0x1400a1c60 | `Array_GetElementStride32` | begin + index*0x20 |
| 0x1400a2f70 | `Zoom_AdjustLevel` | level += delta, clamp [-12 or 0, 12] |
| 0x1400a6040 | `RbTree_LowerBound` | lower bound by key at node+0x20 |
| 0x1400b8d10 | `VectorStride16_PushBack` | append a 16-byte element |
| 0x1400ba2f0 | `Zoom_SetLevel` | level clamp [0, 12] into +0x48 |
| 0x1400ba370 | `VectorSize110` | element count for 0x110-byte elements |
| 0x1400c0970 | `AllocArrayStride48` | `operator new[]`, 0x30-byte elements |
| 0x1400c2400 | `Link_ClearVector` | destroy all Links, end = begin |
| 0x1400df660 | `VectorStride24_Insert` | insert one 0x18-byte element (fill 0x7f7fffff key) |
| 0x1400e0110 | `RbTree_AddUniqueNode` | insert with duplicate rejection |
| 0x1400e0ef0 | `SortIndicesByValuePartition` | quicksort partition over int indices by float table |
| 0x1400e1ae0 | `SortIndicesHeapify` | sift-down for the index heap |
| 0x1400e2550 | `List_MergeSortByOwnerField15B8` | merge sort by `(target+0x80)+0x15b8` |
| 0x1400e2b80 | `Sort8ByteRange` | introsort driver (insertion/heap fallback) |
| 0x1400e4530 | `PanelDesign_Constructor` | the 0x340-byte panel ctor on top of Mark |
| 0x1400e49f0 | `Vector_FreeBuffer` | free buffer, zero begin/end/capacity |
| 0x1400e5f40 | `Property_CopyAssign` | copy fields + reference vector |
| 0x1400e68a0 | `Escadra_CollectShipVector` | gather the +0x100 ship list into a vector |
| 0x1400e69f0 | `Escadra_RecalculateShipStats` | CalculateStats on every linked ship |
| 0x1400e8b50 | `RbTree_RotateLeft` | left rotation |
| 0x1400e8c20 | `VectorStride24_Reallocate` | grow 0x18-byte-element vector and copy |
| 0x1400e8cc0 | `RbTree_RotateRight` | right rotation |
| 0x1400e8e80 | `Link_CopyRange` | copy-construct a Link range |
| 0x1400ebbc0 | `AllocVectorStride24Block` | `operator new[]`, 0x18-byte elements |

## Renames — Escadra / map data (`0x1400F0000–0x14011FFFF`)

| addr | new name | description |
|---|---|---|
| 0x1400f3860 | `Escadra_CreateTexture268` | lazy 0x100x0x80 HGE texture + visual at +0x268/+0x278 |
| 0x1400f48c0 | `Escadra_CreateTexture248` | lazy 0x100x0x100 texture + visual at +0x248/+0x258 |
| 0x1400f4a20 | `Escadra_CreateTexture258` | same pair, keyed on the +0x258 texture slot |
| 0x1400f77d0 | `Escadra_WriteMemberLog` | log every member of the +0x1f8 list |
| 0x1400f8d90 | `Escadra_TransferShopItems` | transfer the +0x520 shop contents |
| 0x1400f9140 | `Escadra_FindMemberByField50` | member whose +0x50 equals the key |
| 0x1401048a0 | `Node_ReparentChildren` | move children to a new parent and relink |
| 0x140111cc0 | `Escadra_BurnFuelAcrossMissiles` | proportional fuel drain from linked map missiles |
| 0x140119d50 | `Aircraft_InitBotMenuWeapons` | weapon load from the +0x2fc/+0x300/+0x304 fields |
| 0x14011bdd0 | `Body_AddAndNotify` | `Body::Add` then virtual +0x1f8 |
| 0x14011ddc0 | `VectorStride24_InsertDefault` | insert zero-filled 0x18-byte element |
| 0x14011e1c0 | `VectorStride24_InsertData` | insert 0x18-byte element built from 9 fields |
| 0x14011eac0 | `SerializableSingleton_Constructor` | `ISerializable` singleton, class name "Singleton" |
| 0x14011ec20 | `FX_CreateDefault` | particle-effect ctor with default parameters |
| 0x14011f2f0 | `BitSet_GetIterator` | bit index -> (word pointer, bit offset) |
| 0x14011f370 | `SerializableSingleton_DeletingDtor` | deleting destructor of the singleton |
| 0x14011f3c0 | `SerializableSingleton_Destructor` | destroys particle/trail globals |
| 0x14011f550 | `FX_MoveTo` | offset all particles to a new position |
| 0x14011f5b0 | `FX_OffsetParticles` | add a delta / snap the particle cloud |
| 0x14011fee0 | `FX_EmitParticles` | emit `count` particles with randomised data |

## Renames — editor (`0x1400BB000–0x1400DB000`)

| addr | new name | description |
|---|---|---|
| 0x1400bbac0 | `Editor_SingletonDeletingDtor` | clears `EditorSingleton` and frees |
| 0x1400bc5e0 | `Editor_HandleZoomWheel` | wheel zoom, undo-zoom when a ship is selected |
| 0x1400d35a0 | `Editor_SetCursorBackground` | `"EDITORMODE"` / `"cursor_main"` background |
| 0x1400d40c0 | `Editor_RestartInputTask` | re-runs the input-task constructor in editor mode |
| 0x1400daaf0 | `Editor_DeleteAllParts` | remove every unprotected part in the active list |

## Renames — Node/child dispatch family (`0x14011C000–0x14011CFFF`)

| addr | new name | description |
|---|---|---|
| 0x14011c880 | `Node_BroadcastCall2A0` | forward 8 args to children until one accepts |
| 0x14011c990 | `Node_CollectMatchingChildren` | append children that pass the +0x1c0 query |
| 0x14011ca40 | `Node_BroadcastCall278` | call virtual +0x278 on every child |
| 0x14011cac0 | `Creature_FindPartResult1B0` | first Body part with non-zero +0x1b0 |
| 0x14011cb40 | `Creature_AnyPartMatches1C0` | any Body part passes +0x1c0 |
| 0x14011ccf0 | `Node_BroadcastCall260` | call virtual +0x260 on every child |
| 0x14011cd50 | `Creature_BroadcastPartCall228` | no-arg +0x228 call on every Body part |

## Skipped / open (45 `FUN_*` remain in the two ranges)

Reasons are per function; nothing here was named because the class or the
field meaning is not recoverable from the code alone.

### `0x140070000–0x14007FFFF`

* **0x1400702a0** - sum of four floats at +0x15e8..+0x15f4; two call sites in
  `SCR_COMBAT`. No structure note for that cluster, so the quantity is unknown.
* **0x140070620** - `(fuel/capacity) * float@+0x1614 / 1000`; looks like fuel
  tonnage but +0x1614 is undocumented.
* **0x140073340** - empty stub (`return`).
* **0x140073450** - `name == "Titan" || float@+0x1604 != 0`; the second term is
  unknown (agent 3 left it too).
* **0x1400734a0** - Zenith list (+0x13d8) length > 5; semantic name would be a
  guess.
* **0x140073530** - clears a pointer at +0x48 through vtable +0x48; the class is
  not clear (+0x48 is a state int on Creature).
* **0x1400738d0** - sets part+0x80c = 1.0 for the +0x1498 list; field unknown.
* **0x140074050** - "has evac pods or +0x1984 > +0x16a0"; both fields are the
  design-cache slots from `Creature_UpdateDesignStats`, meaning unclear.
* **0x1400782b0** - kills parts whose +0x3c4 logic id == 0xd84; id not in the
  projectile-id table.
* **0x140078930** - rebuilds the Link list at +0x1558 from parts with +0x888;
  field/owner unknown.
* **0x140079790** - sets a per-player-slot global float (`DAT_147fc7020[i]`) to
  4.0; the timer's meaning is not visible.
* **0x140079b20** - broadcasts `Part_HandleCommand` 0x19a to all Body parts;
  command id unknown.
* **0x140079ed0** - sets +0xd18/+0xd1c/+0xd20 then drives two part fields by
  min/max comparison; semantics unclear.

### `0x1400A0000–0x14011FFFF`

* **0x1400a07a0** - detach/clear sequence over a GUI binding object.
* **0x1400a2fb0** - resets +0x68..+0x88 and the string at +0xd8; class unknown.
* **0x1400a6210** - predicate `+0xf8 == 0 && +0xf6 != 0`.
* **0x1400b1440** - 0x77d0 bytes, `mainDialogWithChoices`/`!ClickFunc` helper;
  too large for this pass (agent 3 also left it).
* **0x1400bbb10**, **0x1400bc580**, **0x1400bc5c0** - editor click handlers
  keyed on `DAT_1403ef36c` mode 9 / 5; the mode enum is not documented.
* **0x1400bee20** - zeroes +0x128 on objects with byte +0x71 set.
* **0x1400beea0** - large scene/camera reset; control flow and size make an
  atomistic name a guess.
* **0x1400d40e0** - one-shot object removal (vtable +0x48 + list rebuild).
* **0x1400dac70** - large editor selection/hit-test routine.
* **0x1400dd0d0** - 0x950 bytes, Shipworks commit/exit (already on the global
  "needs main caller" list).
* **0x1400e8140** - deleting destructor with a Link at +0xa48; the owning class
  (Frame-sized) is not certain.
* **0x1400e85a0** - thunk to `_invalid_parameter_noinfo_noreturn`.
* **0x1400ebc40** - fleet comparison/merge; large, semantics not nailed.
* **0x1400f00c0**, **0x1400f07c0**, **0x1400f1490**, **0x1400f5be0**,
  **0x1400f8eb0**, **0x1400f9a40** - map encounter / intercept / docking
  routines; each is large and its name would need the encounter rules from
  `findings/map-air-groups.md` to be more than descriptive.
* **0x1400f3a20** - returns `this+0x2a0` (sub-object getter; no consumer read).
* **0x1400f51c0** - returns a vtable +0x1d0 result or 1.0.
* **0x1400f8da0** - tail-call into a misnamed `_Init_thread_footer` target.
* **0x1400fdec0** - clears ints and the string at +0x1a8; class unknown.
* **0x140104950** - Relink + virtual +0x80 notification (pairs with
  `Node_ReparentChildren` but the notification meaning is unknown).
* **0x14010f1a0** - vector trim helper via a misnamed CRT target.
* **0x1401102c0** - distance -> state 5/7 switch; state enum unknown.
* **0x140110340** - stores +0x2a8 and randomises +0x2ac/+0x2b0; retried per the
  batch-2 note, semantics still not pinnable.
* **0x140118699** - not a function: INT3 padding that Ghidra listed as `FUN_`.
* **0x14011bbc0** - returns `&DAT_1403ef5f8`; global meaning unknown.
* **0x14011c760** - min-of-+0x114 scan plus an append into a 40000-entry
  global table; table meaning unknown.
* **0x14011ca40**-family leftovers are all named now.

### Deliberately not touched

* `0x140086000–0x14009B000` factory block (agent 1).
* `0x1400733f0`, `0x1400734e0`, `0x140315fc0` already named by batch 2.

## Note

One accidental `save_program` call was issued at the very start of this pass
(no other shared state changed). It can only have persisted renames that were
already in memory and valid; flagged on the batch-3 blackboard as well.
