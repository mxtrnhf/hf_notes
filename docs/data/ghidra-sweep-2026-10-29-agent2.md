# Ghidra unnamed-function sweep, 2026-10-29 — agent 2

Range `0x140020000`–`0x14006FFFF` (Body / Part / Creature core, weapons, damage,
alloc and container helpers) in `Highfleet.exe.unpacked.exe` v1.163, project
`HighfleetServer`. Every row was renamed with `rename_function_by_address` and
given a doc-style plate comment in the same pass (52 functions).

Naming follows `<Subsystem>_<Verb><Object>`. Where a caller/callee of an already
named function fixed the meaning, that anchor is given in the description.

## Renames

| addr | new name | description |
|---|---|---|
| 0x140023a70 | `DeleteArrayStride16` | frees an over-aligned 16-byte-stride array via its stored base pointer |
| 0x14002e590 | `AircraftLogic_AssignTargetFromOwner` | takes a target from the owner's +0xca0 list, sets the target/owner links, state 6 or 8 via FUN_1401af7b0 |
| 0x140033ac0 | `Body_GetInheritedLightShift` | multiplies +0x8f8 down the Body master chain (used for `lightShiftX`) |
| 0x140033b00 | `Body_GetInheritedStage` | adds +0x8d8 down the Body master chain |
| 0x140033b50 | `Body_GetInheritedShadow` | multiplies +0x90c down the master chain (used for `shadow`) |
| 0x140045660 | `Body_CollectSelfLinkIfDropped` | Body vtable+0x150: hands a dropped body's Link to a collector, kills id-0x38e markers |
| 0x140045800 | `FloatArray_WeightedSumRange` | `sum(v[i] * w)` over an inclusive index range |
| 0x140048b10 | `Node_GetScreenPosition` | world position via vtable+0xe8 then SetShipZoom to screen |
| 0x140048b60 | `Node_GetWorldPosition` | zero + call vtable+0xe8 (`Body::get_world_pos`); used by FireMissile, AircraftLogic |
| 0x140048ff0 | `Body_FindActiveAncestor` | nearest Body ancestor with +0x8b8 link or +0x8f4 flag set |
| 0x140049030 | `Part_GetReloadTime` | stats +0x14c, x0.8 when the owner has the int 1 in its +0x1a30 list |
| 0x1400490a0 | `Part_GetRate` | stats +0x150 |
| 0x1400494b0 | `Color_SetAlpha` | clamps alpha and replaces the high byte of a packed colour |
| 0x1400494e0 | `Color_PackRGBAFloats` | four normalised components to a packed colour |
| 0x140049540 | `Body_IsFromCurrentLocation` | master == `CURRENT_LOCATION+0x348` (or the global node); used by BuyPartShop / lootBoxCoins |
| 0x140049c10 | `Body_SetHealth` | writes +0x2c8 and +0x2cc (current = max) |
| 0x140049e30 | `Body_IsBadlyDamaged` | owner present and health/max < 0.8 |
| 0x140049e60 | `Body_HasSlotOccupant` | scans the +0x350 slot vector for a part with property == arg |
| 0x140049ea0 | `Body_Kill` | Body vtable+0x48: free projectile state (id 900), kill children, shared teardown |
| 0x140049f30 | `Body_ClearSlots` | deletes every +0x350 occupant and empties the vector |
| 0x14004a020 | `Body_StartLogic` | sets +0x3c8 = 1, +0x478 = 0, +0x47c = -10000.0 |
| 0x14004a0b0 | `Body_LocalAngleToWorld` | master vtable+0xf0 then subtract local angle (+0x138) |
| 0x14004a100 | `Body_LocalPointToWorld` | master vtable+0xf8 then rotate by the local matrix at +0x8fc |
| 0x14004a260 | `Body_CreateAntennaChain` | the 4x ANTENNA_PART (id 0x38e) + weld-joint builder, guarded on logic id 900 |
| 0x14004a280 | `Body_DetachFromOwner` | tells the owner to drop the body, then frees it when logic id == 900 |
| 0x14004af20 | `VectorLink_PushBackAlt` | `vector<Link>::push_back` growing through LinkVec_EmplaceReallocate (twin of 0x1401659c0) |
| 0x14004e7d0 | `Body_RepairForGold` | charges profile+0x2a8 for the missing health share, then vtable+0x208 |
| 0x140055c70 | `List_MergeSortRecursiveByNodeInt` | recursive merge step sorting by the int at node+0x30 |
| 0x140055e20 | `RefCount_Release` | intrusive refcount decrement, dtor at zero |
| 0x140055ea0 | `Object_DeleteViaVtable` | `vtable+0x10(this, 1)` |
| 0x140055f50 | `AllocArrayStride24` | `operator new[]` for 24-byte elements (the doc name `NewArray24` is blocked by the name checker) |
| 0x140055fd0 | `AllocArrayStride40` | `operator new[]` for 40-byte elements (same) |
| 0x140058550 | `Vector_Insert32` | vector insert for 32-byte elements |
| 0x14005c580 | `FillIntRange` | fill a half-open range of 32-bit values |
| 0x14005c620 | `FillRange8` | fill a half-open range of 64-bit values |
| 0x14005e6c0 | `Creature_Destructor` | Creature vtable, frees the lists at +0x1588 / +0xd78, releases launch lists |
| 0x14005f3c0 | `HashList_FreeBuckets` | frees the bucket array at +0x10 and every chain |
| 0x14005f420 | `Property_CopyFields48` | copies the two floats at +0x48/+0x4c |
| 0x1400603a0 | `VIProperty_Destructor` | VIProperty vtable + base teardown + optional free |
| 0x140060440 | `Property_WriteToStream` | writes `path + sep + child[+0x28]` then child vtable+0x10 |
| 0x1400604c0 | `Array_DestroyRange48` | destroys a range of 0x30-byte elements |
| 0x140061760 | `Creature_NotifyUnmountedParts` | vtable+0x198 on parts whose master is null or a plain Node |
| 0x140061da0 | `String_Clear` | length = 0 + terminator |
| 0x14006aab0 | `Creature_Die` | player-slot lookup, 4.0 s death delay in `0x147fc7020`, then `Body_DieExplode` |
| 0x14006c440 | `Creature_PopFirstVecCA0` | pop front of the +0xca0 list, return the removed element's +0x10 |
| 0x14006c480 | `Creature_TryDropBomb` | AI bombing run: geometry gates on the +0x1438 bomb list, spawns via FUN_1401b5420 |
| 0x14006d900 | `Creature_ResetLaunchItemField80c` | 1.0 into +0x80c of every part on the +0x1378 launch list |
| 0x14006e880 | `Creature_CountCarriedItems` | sums the five 0x18-stride loadout vectors |
| 0x14006eca0 | `Creature_ComputePartsCenter` | weight (property+0x90) -weighted mean of part property positions |
| 0x14006ed70 | `TimeTable_FindIndex` | first index in `0x1403ef0f8` whose double exceeds the value |
| 0x14006ede0 | `TimeTable_GetThreshold` | table double for the index at +0x4c, clamped |

## Notes on fields turned up on the way

* `Body+0x8f8`, `+0x8d8`, `+0x90c` are inherited (multiplied / added) down the master
  chain and are read by `Body_UpdateRenderTransform` as light shift, stage and shadow.
  `Body+0x8fc..+0x908` is the 2x2 local rotation matrix (`vec_rotate` on it in
  `Body_LocalPointToWorld` and `Body::get_world_pos`).
* vtable+0xe8 = `Body::get_world_pos(Vec2*)`, vtable+0xf0 = angle-to-world,
  vtable+0xf8 = point-to-world, vtable+0x150 = dropped-body link collector,
  vtable+0x208 = set health, vtable+0x298 = projectile cleanup.
* Creature `+0x1a18/+0x1a1c` is a fractional time accumulator advanced against the
  0x1403ef0f8 table (0x10-byte records, double threshold).
* `Creature+0x19b0` / `+0x19b4` are the bomb-drop timestamp and best release range.

## Skipped / open

* `0x1400211a0` — large HTML tooltip builder for a part (`DAMAGE_STAT`,
  `displayYellowLable_`); UI-shaped, needs the tooltip subsystem read before a name.
* `0x140027f90` — walks the +0x350 slot vector and pokes `node+0x58`; identity of the
  callee `rep_1402b1a80_MakeGlobal_` not established.
* `0x1400458c0` — the big body tick (`DAT_1403c0d88`, `Frame_ClassifyPartMix`,
  0x20-vec stack); too entangled to name safely.
* `0x140047f70` — `health/max * GetValue(this)` over a vtable entry; the second
  argument's role is unclear.
* `0x140048050` — `out = this[+0x210]; vtable+0xe8(out)`; probably an anchor point to
  world, but no caller function is defined for its call sites (0x1400362xx).
* `0x140049cd0` — `+0x2e8 >= arg && +0x248 != 0`; called from `creatureLogic`, fields
  unidentified.
* `0x14004bb10` (`+0x8c0` pointer vector clear), `0x14004c7f0` (body shadow draw),
  `0x14004dfa0` (fading segment draw), `0x14004e0d0` (slot-overlay draw),
  `0x14004eab0` (scale a float array), `0x140052070` (n-gon shell mesh),
  `0x140053df0` (recursive side/region walk with a +0x9bc label), `0x140054d90`
  (vtable+0x78 / +0x1d8 gate), `0x140056850` (ring raycast over a direction table),
  `0x1400608d0` (phase accumulator), `0x140060a20`, `0x140061e40`, `0x1400671d0`
  (tooltip/label builder), `0x14006bb80` — read, not identified.
* `0x140060010`, `0x140060180`, `0x14005e560`, `0x14005e6b0` — per-class destructor
  thunks whose class is only a vtable address (`0x140355108`, `0x140354b60`,
  `0x140354bf8`); naming them would just repeat the address.
* **std::sort instantiations** `0x140058840`, `0x140058a40`, `0x140058c60`, `0x140059120`,
  `0x140059a60`, `0x14005a0b0`, `0x14005a8c0`, `0x14005acf0`, `0x14005b6e0`, `0x14005c3c0`
  — introsort median/partition/heap-sift for keys at `+0x88c` (int), `+0x88` (float, a
  creature distance) and 0x20-byte records. Compiler output, left for a later pass.
* `0x14004aee0` / `0x14004af00` — plain `vector<void*>::push_back` twins of already
  named helpers; zero information in the name.
* `0x140055f20` — `return 0;` thunk used by CRT init tables; nothing to name.
