# Ghidra changes, 2026-10-29 (unnamed-function sweep)

Program `Highfleet.exe.unpacked.exe` v1.163, saved (version after the sweep). The
check-in to the shared project is the user's.

The sweep ran in nine waves. The first was the single-agent pass documented in
the tables below (`166` renames). Waves 2–9 were five, five, five, ten, ten, ten,
ten and ten parallel agents on disjoint ranges. After all nine waves the unnamed
set went from 3,875 functions (2,201 `FUN_*` + 1,674 `rep_*`) to **93 `FUN_*` +
979 `rep_*`**; the program now has **4,350 named functions** (about 2,844
renames of existing functions plus 516 named functions created at missing
function objects). Coverage is **80.23%** of 5,422 function objects.

Every rename in all six waves was verified against the live program after the
agents finished (over 1,200 tabulated addresses compared by address and name;
two mismatches found and fixed: `Sort3WithComparator` -> `Sort3ByComparator`, and
`Body_Constructor`, whose entry moved 0x30 bytes down to `0x140015ed0` under
re-analysis and needed its plate re-applied). Plate audits found and fixed two
missing plates (`Property_SetFloat`, `App_ReloadSeria`).

This pass started from the full function list and worked through the unnamed
`FUN_*` / `rep_*` functions, prioritising (a) helpers that almost every game
function calls, (b) game logic whose callers/callees were already named, and
(c) clusters that can be identified from an existing note or from a string
reference. `!FrameFunc`, one of the two `!` (decompile-size) functions, also got
a plate comment.

Conventions used in this pass:

* names follow the existing `<Subsystem>_<Verb><Object>` shape (`Body_Explode`,
  `Part_GetRange`, `AircraftLogic_SetState`);
* std/CRT helpers keep a `String_` / `Vector` / `RbTree_` / `AllocArray` prefix
  instead of being named after the C++ symbol, because the exact template
  instantiation is not recoverable from the call sites;
* plate comments say what the function does, not how it was found; the old
  Ghidra name is not repeated (the examples from 2026-10-26 do, but here the
  new name is only a rename of `FUN_*`, so nothing is lost);
* uncertain names are not applied; those functions are listed under "Left
  for a later pass" below.

## Renames

### Allocators, containers and std::string (used everywhere)

| addr | new name | what it is |
|---|---|---|
| 0x140006d70 | `String_Tidy` | frees a std::string buffer, resets to empty (2648 callers) |
| 0x140006020 | `Array_DestroyStringRange40` | destroys a range of strings with 0x28 stride |
| 0x140018a50 | `String_AppendString` | `string::append(const string&)` |
| 0x140018a70 | `String_AppendCStr` | `string::append(const char*)` |
| 0x140011510 | `String_ConstructFromCStr` | string copy-construct from C string |
| 0x140057d50 | `String_CopyConstruct` | string copy-construct from string |
| 0x140057db0 | `String_ConcatStringString` | `operator+` for two strings |
| 0x140028340 | `String_End` | end pointer (`c_str() + size()`) |
| 0x140005620 | `ThrowBadArrayLengthException` | throws `std::bad_array_new_length` |
| 0x1400051e0 | `Exception_InitBadArrayNewLength` | builds that exception object |
| 0x1400055e0 | `Link_DestroyRange` | destroys a range of `Link` |
| 0x140005270 | `Link_DestroyVector` | destroys a vector of `Link` |
| 0x1400076d0 | `RbTree_Insert` | std::map/set red-black insert |
| 0x140006e60 | `RbTree_Destroy` | destroys a whole tree |
| 0x140012e20 | `RbTree_DestroySubtree` | recursive subtree free |
| 0x1400171e0 | `RbTree_DestroyHeader` | tree clear for the header-node variant |
| 0x1400e85c0 | `RbTree_EraseRebalance` | erase a node and rebalance |
| 0x140006dd0 | `HashList_Destroy` | frees a chained hash table |
| 0x140006f80 | `Array_Deallocate` | frees a dynamic array buffer |
| 0x140017470 | `Array_Deallocate2` | same for the second layout |
| 0x140019950 | `Array_DestroyRange24` | destroys 24-byte elements |
| 0x14001c7d0 | `Array_ClearRange24` | destroys and empties a vector |
| 0x14002d610 | `Array_SubtractClampZero` | `v[i] = max(v[i] - d, 0)` |
| 0x1400b8d30 | `VectorString_MovePushBack` | `vector<string>::push_back(move)` (381 callers) |
| 0x140012c20 | `VectorString_InsertReallocate` | grow + insert for vectors of strings |
| 0x1400dfc80 | `VectorLink_Insert` | `vector<Link>::insert` |
| 0x1400e82d0 | `Vector_Resize8` | resize a `vector<void*>` |
| 0x1400fd910 | `Vector_PopBack56` | pop_back for 0x38-byte elements |
| 0x1401a70d0 | `Vector_ResetField220` | zeroes object+0x220 over a vector |
| 0x1400530b0 | `VectorSize24` | element count for 24-byte elements |
| 0x140053d10 | `IntVector_Contains` | linear search in an int vector |
| 0x14005aa50 | `List_MergeSortByNodeKey` | stable merge sort by node+0x30 |
| 0x14005ab80 | `List_MergeSortByCreatureKey` | stable merge sort by creature+0xf8 |
| 0x1400e26e0 | `List_MergeSortByCreatureKeyAsc` | same, ascending tie-break |
| 0x1401ae740 | `Array_DestroyNPCRange` | destroys a range of NPC |
| 0x140237540 | `VectorPointer_PushBack` | `vector<void*>::push_back` |
| 0x140237560 | `VectorEscadra_PushBack` | append a 0x28 name record |
| 0x1402375b0 | `LoadoutVector_PushBack` | append a 0x28 loadout item |
| 0x140237600 | `VectorNameItem_PushBack` | append a 0x28 name item |
| 0x140237650 | `VectorShipEntry_PushBack` | append a 0x110 ship entry |
| 0x140265b40 | `VectorSize40` | element count for 40-byte elements |
| 0x1400a1bf0 | `RbTreeIterator_Next` | in-order iterator step |
| 0x1400a16d0 | `List_InitSentinel` | empty doubly linked list |
| 0x140280770 | `Node_AreAllPropertiesAlive` | all linked properties alive |
| 0x140110400 | `Creature_SetMissileGroupId` | group id on all linked missiles |
| 0x1401a8110 | *(skipped, destructor thunk)* | |
| 0x140007d00 | `AllocateArrayOf8Byte` | `operator new[]` for 8-byte elements |
| 0x140055f50 | `AllocArrayStride24` | 24-byte elements |
| 0x140055fd0 | `AllocArrayStride40` | 40-byte elements |
| 0x1400099e0 | `DeleteArray16` | `operator delete[]` for 16-byte elements |
| 0x140009a30 | `DeleteArray32` | 32-byte elements |
| 0x140023a30 | `DeleteArray56` | 56-byte elements |
| 0x14020ea10 | `DeleteArray392` | 392-byte elements |
| 0x140006940 | `TreeNode_DestroyRecursive` | frees a child/sibling tree |

### Math, colour, geometry

| addr | new name | what it is |
|---|---|---|
| 0x140018a90 | `Vec2_Add` | in-place 2D add |
| 0x140018b40 | `Vec2_Subtract` | in-place 2D subtract |
| 0x1400188f0 | `Vec2_Scale` | 2D scale |
| 0x1400188c0 | `Vec2_IsZero` | both components zero |
| 0x140028010 | `Vec2_DistanceSq` | squared 2D distance |
| 0x140018df0 | `Color_ToARGB` | float RGBA -> packed int |
| 0x140019540 | `Color_FromARGB` | packed int -> float RGBA |
| 0x140053090 | `SignFloat` | -1.0 / +1.0 |
| 0x14001c790 | `ClampInt` | clamp to `[lo, hi]` |
| 0x140055b70 | `Angle_Wrap` | wrap an angle into a period |
| 0x14016d820 | `Matrix3x3_Identity` | reset a 3x3 transform |
| 0x14020f6e0 | `Geometry_PointSegmentDistanceSq` | point to segment |
| 0x14020f610 | `Geometry_MaxSegmentSeparation` | max of four point/segment terms |
| 0x1400e0cd0 | `Sort3IndicesByValue` | order three indices by array value |
| 0x1400e0da0 | `Sort3ByComparator` | sort three handles |

### Body / Part / Creature / physics

| addr | new name | what it is |
|---|---|---|
| 0x140015ed0 | `Body_Constructor` | `Body::Body` |
| 0x140024f70 | `Body_DestroyPhysics` | destroy the b2Body and clear links |
| 0x140048030 | `Body_GetB2AngularVelocity` | b2Body+0x48 |
| 0x1400486a0 | `Body_GetLinearVelocity` | b2Body+0x40, scaled |
| 0x140048500 | `Body_RebuildSubtreeList` | rebuild the subtree link list |
| 0x14001cfa0 | `Body_CollectSubtreeLinks` | collect bodies into a link vector |
| 0x14001cec0 | `Creature_CollectLiveParts` | collect live parts recursively |
| 0x140019250 | `Creature_DisableBody` | `b2Body_SetEnabled(false)` + pause |
| 0x1400192b0 | `Creature_EnableBody` | `b2Body_SetEnabled(true)` + resume |
| 0x140029b60 | `Body_Explode` | blast damage + knock-back pipeline |
| 0x14001a3b0 | `Body_SpawnFireEffect` | spawn the fire/smoke particle |
| 0x14002d3b0 | `Body_ApplyInverseSquareForce` | 1/r^2 force from a point |
| 0x140048f90 | `GetSpriteByIndex` | sprite vector lookup with fallback |
| 0x140049e00 | `HasAllFlags` | mask test on a 32-bit flag word |
| 0x14001dab0 | `Part_HasAllFlags` | mask test on the 64-bit part flags |
| 0x1400485e0 | `Part_GetLaunchedHealth` | stats +0x184 |
| 0x140048610 | `Part_GetRange` | stats +0x160 |
| 0x140048640 | `Part_GetSpeed2` | stats +0x15c |
| 0x140048670 | `Part_GetLaunchedSpeed` | stats +0x158 |
| 0x140048750 | `Part_GetFuelNeed` | stats +0xd0 |
| 0x140048780 | `Part_GetLegForce` | stats +0x104 |
| 0x140048810 | `Part_GetAgility` | stats +0x174 |
| 0x140048840 | `Part_GetArmorPiercing` | stats +0x170 |
| 0x140048870 | `Part_GetExplosive` | stats +0x168 |
| 0x1400488a0 | `Part_GetCluster` | stats +0x16c |
| 0x140048900 | `Part_GetRadarCone` | stats +0x17c |
| 0x1400f5bb0 | `Part_GetRadarRange` | stats +0x178 |
| 0x1400f5240 | `Part_GetAccelerationTime` | stats +0x154 |
| 0x1400282a0 | `Part_GetHalfExtents` | half size at +0x218/+0x21c |
| 0x140028070 | `Creature_DrawParts` | draws the part vector at +0x118 |
| 0x1400250a0 | `Creature_WorldToScreen` | map/world -> screen with zoom+shake |
| 0x1400f6ab0 | `Creature_GetFuelRate` | current burn rate |
| 0x1400f6b00 | `Creature_GetFuelRateAfterBurn` | burn rate after spending fuel |
| 0x14002e1e0 | `CollectObjectsByMask` | flagged-object collector |

### Box2D

| addr | new name | what it is |
|---|---|---|
| 0x14031a190 | `b2Body_SetEnabled` | create/destroy proxies and contacts |
| 0x140322240 | `b2Mat22_GetInverse` | 2x2 inverse |
| 0x1403222d0 | `b2Mat33_GetSymInverse33` | symmetric 3x3 inverse |
| 0x140322440 | `b2Mat22_Solve` | 2x2 linear solve |
| 0x1403224c0 | `b2Mat33_Solve33` | 3x3 linear solve |
| 0x1403226d0 | `b2World_ResetProfile` | zero the world profile counters |
| 0x140327d20 | `b2Island_Destroy` | free the island stacks |

### Aircraft

| addr | new name | what it is |
|---|---|---|
| 0x14000ebb0 | `AircraftLogic_SetState` | state machine setter (log names STATE_*) |
| 0x14000a620 | `Aircraft_UpdateSpeed` | target/current speed ramp |
| 0x14000ac70 | `Aircraft_ComputeBankDirection` | roll direction for an attack run |
| 0x14000e680 | `Aircraft_SetSide` | side id at +0xc8 and body+0x248 |
| 0x14000abf0 | `Aircraft_GetActiveEscapePod` | usable pod or null |
| 0x14000b360 | `Aircraft_IsStateNotParked` | state outside {6, 7} |
| 0x140007970 | `Aircraft_AddAmmoToList140` | append ammo nodes, list +0x140 |
| 0x140007aa0 | `Aircraft_AddAmmoToList120` | list +0x120 |
| 0x140007bd0 | `Aircraft_AddAmmoToList130` | list +0x130 |
| 0x140215f00 | `Weapon_GetBlastRadiusForCode` | code -> blast radius table |

### Distance / bounds / screen helpers

| addr | new name | what it is |
|---|---|---|
| 0x14020f7c0 | `Object_DistanceSq` | squared distance between object positions |
| 0x14020fc80 | `Object_DistanceToPoint` | object to point |
| 0x14020fce0 | `Creature_Distance` | centre-to-centre with sqrt cache |
| 0x14020ff80 | `Object_DistanceAt150` | distance between `+0x150` positions |
| 0x14020ffb0 | `Object_GetPos150` | `+0x150` position |
| 0x14020ffd0 | `Object_DistanceToOffsetB0` | `+0x150` to `+0xb0` |
| 0x1400f8db0 | `Object_IsSameSide` | sign product of both sides |
| 0x14021ccb0 | `Body_IsInsideLevelBounds` | bounds test with radius margin |
| 0x14021cda0 | `Body_IsOnScreen` | screen test |
| 0x14021ce40 | `Screen_IsPointInside` | frame test with margin |
| 0x140221e70 | `Body_ClampToLevelBounds` | clamp one body, log the edge |
| 0x1402220d0 | `Fleet_ClampShipsToBounds` | clamp every live ship |
| 0x1402213e0 | `IsHighZoomActive` | `DAT_147fc6fe0 && ZOOM_LEVEL > 3` |
| 0x140210990 | `Map_ResetBounds` | bounds +-6000, zoom 4 |

### Fleet, missiles, shops, player

| addr | new name | what it is |
|---|---|---|
| 0x1402a7e20 | `Profile_SetPlayerShip` | `SetControlledShip(profile, ship, 0)` |
| 0x1400e6920 | `Profile_AddShipToListBySide` | friendly vs hostile roster |
| 0x1400f5490 | `Fleet_FindShipsWithinRadius` | same-side ships in radius |
| 0x14020eb20 | `Fleet_SetVolume` | volume over the ship list |
| 0x14020f550 | `Fleet_ClearWeaponTargets` | clear target links and list |
| 0x1400f55f0 | `Creature_FindMissileProperty` | first missile property |
| 0x1400f5660 | `Creature_FindBestMissile` | highest-score missile property |
| 0x1400f7430 | `Creature_GetMissilePropertyByIndex` | index-th missile property |
| 0x1400f7560 | `Creature_FindMissileWithMaxField` | max `+0x15f8` |
| 0x1400f4b80 | `Creature_CountMissiles` | carried missile count |
| 0x1401b9940 | `Creature_FindLinkedById` | entry in the `+0x1f8` list |
| 0x1400f39c0 | `Missile_GetTargetOwner` | target node -> owner ship |
| 0x1400f0060 | `Ship_GetAmmoCount` | ammo count on a ship |
| 0x1400f4fd0 | `Player_GetAimPoint` | current aim point |
| 0x1400f3700 | `ShipCard_InitTextOverlays` | per-card HGE text objects |
| 0x140053090… | see math | |
| 0x14005c6b0 | `Captain_Constructor` | `Captain` serialisable, copy form |
| 0x14005c730 | `Captain_ConstructorDefault` | `Captain` serialisable, default |
| 0x1401a9130 | `Time_GetTicksMs` | ms since start |
| 0x1401b6da0 | `Frame_ResetCounter` | reset frame counter |
| 0x1401b6dd0 | `Camera_CommitTarget` | move camera to target screen pos |
| 0x1401a8110… | see text | |

### GUI / text

| addr | new name | what it is |
|---|---|---|
| 0x14016e9f0 | `Font_MeasureString` | HGE font string width |
| 0x14016f0c0 | `Font_SetGlyphParam` | one scalar on all 256 glyphs |
| 0x14016f170 | `Font_SetGlyphColour` | colour/sprite on all glyphs |
| 0x14016d970 | `TextGrid_InitSlots` | initialise grid cell positions |
| 0x14016de30 | `TextGrid_SetCellPosition` | position one cell |
| 0x14016d450 | `Text_SetDirection` | RTL/LTR + rewind |
| 0x1402212a0 | `Gui_HasPreselectBack` | `PRESELECT_BACK` element present |
| 0x1400dda70 | `Gui_ClearElementListA` | destroy a GUI element list |
| 0x1400ddbd0 | `Gui_ClearElementListB` | second element list |
| 0x1400db0b0 | `Gui_GetTopElementA` | last element of list A |
| 0x1400db0f0 | `Gui_GetTopElementB` | last element of list B |
| 0x1400da830 | `Editor_UndoZoom` | pops the editor zoom stack |

### Global static initialisers (`rep_*_atexit`)

| addr | new name | what it initialises |
|---|---|---|
| 0x1400011f0 | `InitGlobal_PropertySentinel` | property sentinel node |
| 0x140001410 | `InitGlobal_ShipListContainer` | ship-list container |
| 0x140001450 | `InitGlobal_NpcPrototype` | `somethingNPC_` |
| 0x140002e50 | `InitGlobal_DeadJointList` | `DeadJointList` |
| 0x140002e80 | `InitGlobal_OutputStream2` | `oStream2` |
| 0x140002eb0 | `InitGlobal_OutputStream1` | `oStream1` |
| 0x140002fc0 | `InitGlobal_DialogPath` | `Data/Dialogs/english.seria` |

## Batch 2: five parallel agents (same day)

Five agents worked disjoint address ranges, coordinating through a shared
blackboard for name collisions and "what is this" questions. Total: **221
renames**, every one plated. Their detailed tables (including the "skipped /
open" lists with reasons) are the per-agent files:

| agent | range | renames | note |
|---|---|---|---|
| 1 | 0x140005000–0x14001FFFF | 34 | [ghidra-sweep-2026-10-29-agent1.md](ghidra-sweep-2026-10-29-agent1.md) |
| 2 | 0x140020000–0x14006FFFF | 52 | [ghidra-sweep-2026-10-29-agent2.md](ghidra-sweep-2026-10-29-agent2.md) |
| 3 | 0x140070000–0x14011FFFF + 0x140300000–0x140350510 | 56 | [ghidra-sweep-2026-10-29-agent3.md](ghidra-sweep-2026-10-29-agent3.md) |
| 4 | 0x140120000–0x1401FFFFF | 40 | [ghidra-sweep-2026-10-29-agent4.md](ghidra-sweep-2026-10-29-agent4.md) |
| 5 | 0x140200000–0x1402FFFFF | 39 | [ghidra-sweep-2026-10-29-agent5.md](ghidra-sweep-2026-10-29-agent5.md) |

What the batch added that is worth remembering:

* **The `SCR_*` scene ticks are named.** Agent 5 recovered the
  `SomethingWithLevelSerias` branch map (each scene string is referenced once;
  the `LEA RDX` is the branch test; `DAT_147fc6fc4` is the per-frame state, 0x61
  = leave scene) and named `SCR_COMBAT`, `SCR_COMBAT_TickWaveSpawner`,
  `SCR_COMBAT_ReturnToMap`, `SCR_COMBAT_SpawnPlayerShip`, the
  `SCR_COMBAT_SKIRMISH_*` family, `SCR_BOMBERS(_Tick)`, the `SCR_MISSILE_*`
  pair, `SCR_CRAFTS_VS_CRAFTS(_CheckEnd)` and
  `SCR_CRAFTS_VS_MISSILE_ReturnShips`. The full table is in agent 5's note.
* **Box2D is essentially complete** up to `0x140350510`: the GJK/`b2Distance`
  layer, the TOI layer, the polygon shape maths, the contact/broadphase
  internals and the pulley/wheel/mouse/gear/friction/rope solver sets.
  Agent 3 warns that **the stock 2.3 joint-type enum does not match this
  build**: the type-4 `Dump` is `b2WheelJoint`, type-7 is `b2PulleyJoint`,
  type-10 is `b2MouseJoint`. Re-derive `b2Joint_Destroy`'s size table from the
  constructors, not the enum.
* **Pre-combat builders identified** (`Precombat_BuildLayoutDispatch`,
  `Precombat_BuildMapLayout`, `Precombat_BuildCardLayout`), which closes the
  "which of the two builders is the map layout" question in
  [../rendering/precombat-screen.md](../rendering/precombat-screen.md).
* **`.seria` is read out of a ZIP container**: `Zip_ReadLocalFileHeader`,
  `Zip_ReadInt32BE`, `Zlib_Adler32` are in the resource path.
* **Name-collision rule in the MCP server**: a new name is rejected when an
  existing function's token set is a subset of it (e.g. `NewArray8` vs `New`).
  That is why the array helpers are now `AllocateArrayOf8Byte` /
  `AllocArrayStride24` / `AllocArrayStride40` and the throw helper is
  `ThrowBadArrayLengthException`. Keep it in mind for future passes.

### Cross-agent notes worth keeping

* **Scene-branch map** (agent 5): each `SCR_*` string is referenced once from
  `SomethingWithLevelSerias`, and the `LEA RDX` address is the branch test:
  `SCR_RUINS` 0x1402c1f4b, `SCR_COMBAT` 0x1402c24d9, `SCR_COMBAT_SKIRMISH`
  0x1402c3c78, `SCR_COMBAT_SKIRMISH_PVP` 0x1402c44c4, `SCR_COMBAT_TEST`
  0x1402c4848, `SCR_MISSILE` 0x1402c4baf, `SCR_CRAFTS_VS_MISSILE` 0x1402c510c,
  `SCR_BOMBERS` 0x1402c52ee, `SCR_CRAFTS_VS_CRAFTS` 0x1402c5890, `SCR_CREDITS`
  0x1402c5a86. `DAT_147fc6fc4` is the per-frame state, 0x61 = leave scene. Any
  tick call site can be attributed to a scene by its address.
* **Body vtable slot map** (agent 2, read from memory): +0xe8 world position,
  +0xf0 local angle -> world, +0xf8 local point -> world, +0x150
  dropped-body link collector, +0x208 set health, +0x298 projectile cleanup.
  Body/Frame/Creature/Missile vtables copy most of these slots, so a DATA xref
  from `0x148079xxx` / `0x14036xxxx` does not tell you the class.
* **World-to-screen has two flavours** (agent 4):
  `Gui_WorldToScreenPoint` 0x1401a8670 is the cheap GUI-frame transform used all
  over the pre-combat/GUI code; `Creature_WorldToScreen` 0x1400250a0 is the
  richer one with zoom, shake and camera offsets.
* **Input stack** 0x140184f90..0x14018ac30 is now `InputTask_Constructor`,
  `Input_InitRawInputDevices`, `Input_Joystick_Constructor`,
  `Input_HandleJoystickEvent`, `Input_HandleKeyDown`, `Input_HandleMouseMove`,
  `Input_SwapJoystickPlayerIndex`, `InputTask_Destructor`.
  `rep_14018b530_InputTask` is a duplicate copy of `InputTask_Constructor`; it
  was left under its `rep_` name on purpose.
* **Box2D joint-class trick** (agent 3): every joint's `Dump` virtual prints its
  own `b2XxxJointDef` string. Read vtable slot [4] and follow it; the literal in
  the body names the class in one step.

## Batch 3: five more agents (same day)

A second wave of five agents covered the remaining game code. Total: **575
renames**, all plated. Per-agent tables and skip lists:

| agent | range | renames | note |
|---|---|---|---|
| 1 | 0x140080000–0x14009FFFF | 246 | [ghidra-sweep-2026-10-29-b3-agent1.md](ghidra-sweep-2026-10-29-b3-agent1.md) |
| 2 | 0x140070000–0x14007FFFF + 0x1400A0000–0x14011FFFF | 74 | [ghidra-sweep-2026-10-29-b3-agent2.md](ghidra-sweep-2026-10-29-b3-agent2.md) |
| 3 | 0x140120000–0x14016FFFF | 46 | [ghidra-sweep-2026-10-29-b3-agent3.md](ghidra-sweep-2026-10-29-b3-agent3.md) |
| 4 | 0x140170000–0x1401FFFFF | 68 | [ghidra-sweep-2026-10-29-b3-agent4.md](ghidra-sweep-2026-10-29-b3-agent4.md) |
| 5 | 0x140200000–0x1402FFFFF | 141 | [ghidra-sweep-2026-10-29-b3-agent5.md](ghidra-sweep-2026-10-29-b3-agent5.md) |

What the batch corrected or added:

* **The "class factory block" is the D3D11 shader layer, not a factory.**
  `0x140080000–0x14009FFFF` holds the game's shader classes: `ComputeShader` /
  `CSGlitch`, `Texture`, the `RenderState_*` and D3D11 blend/rasterizer helpers,
  `Effect` / `Shader` / `VShader` / `PShader`, 29 concrete `Shader*` classes with
  their `ConstantBuffer<CBConstants<...>>`, and `ShaderData` /
  `ShaderResourceView` / the `ShaderParam*New` family. Every class was taken
  from MSVC RTTI (`vtable[-1]` -> CompleteObjectLocator -> TypeDescriptor ->
  `.?AV<Class>@@`), not guessed. This closes the biggest open cluster in the
  first-pass note.
* **The "ship-zoom LOD" cluster is the trail/world-sprite system**:
  `Trail_CreateForBody`, `Trail_AddSprite`, `Trail_UpdateAll/Geometry/
  LayerTransforms`, `Trail_DrawLayer`, `Trail_Render`. Source of the
  `trail_black_*` sprites: burning bodies at `ZOOM_LEVEL > 2`.
* **Pre-combat card drag identified** (`Precombat_PickUpCard`,
  `Precombat_DragCard`, `Precombat_ApplyCardOrder`) and `0x1401574b0` corrected
  from "slider factory" to `Gui_HandleSliderChange`, the one change callback for
  every slider.
* **The input record is documented**: `+0xde..+0xe1` move flags, `+0xe2/+0xe3`
  rotate flags, plus `Input_MapHatToKeyModern/Legacy` and joystick lookup.
* **Large game-logic haul** in 0x140200000–0x1402FFFFF: battle/fleet
  (`Roster_*`, `Fleet_*`, `Body_GetSlotWorldPos`), shop/shipworks
  (`Shop_TransferItemForLocation`, `Shipyard_SpawnShip`), the `Hud_Marker*`
  family, and the `+0x1604` introsort family used by `SCR_BOMBERS`.
* **`.seria` is a ZIP** confirmed again from the resource side, with `Inflate_*`
  and `Crc32_GetTable` named.

## Batch 4: five agents on the leftovers (same day)

The final wave covered the clusters the earlier waves had deliberately skipped.
It added **372 named functions: 364 renames + 8 functions created at vtable
slots that had no function object**. Per-agent tables and inventory:

| agent | range | result | note |
|---|---|---|---|
| 1 | 0x140330000–0x14033FFFF | 16 renamed + 2 created | [ghidra-sweep-2026-10-29-b4-agent1.md](ghidra-sweep-2026-10-29-b4-agent1.md) |
| 2 | 0x140340000–0x140350510 | 53 renamed; 514 documented clones | [ghidra-sweep-2026-10-29-b4-agent2.md](ghidra-sweep-2026-10-29-b4-agent2.md) |
| 3 | 0x140000000–0x14006FFFF | 124 renamed (87 `FUN_*` + 37 `rep_*_atexit`) | [ghidra-sweep-2026-10-29-b4-agent3.md](ghidra-sweep-2026-10-29-b4-agent3.md) |
| 4 | 0x140070000–0x14011FFFF + 0x1401B0000–0x1401FFFFF | 30 renamed | [ghidra-sweep-2026-10-29-b4-agent4.md](ghidra-sweep-2026-10-29-b4-agent4.md) |
| 5 | 0x140120000–0x1401AFFFF + 0x140200000–0x1402FFFFF | 143 renamed + 6 created | [ghidra-sweep-2026-10-29-b4-agent5.md](ghidra-sweep-2026-10-29-b4-agent5.md) |

What the batch corrected or added:

* **`0x1400b1440` is `Dialog_ExecuteChoiceActions`** — the 0x77aa-byte token
  interpreter for dialogue answers, confirmed from ~170 action literals and the
  `mainDialogWithChoices` / `!ClickFunc` callers. This was the last big unknown
  in the dialogue path.
* **`0x1401a7120` is the random fleet/shop generator**, not a panel builder:
  `Fleet_CreateRandomEscadra`, `Fleet_GenerateShipNames`,
  `Fleet_SelectShipsForBudget`, `Fleet_BuildShopOffer`,
  `Fleet_AddNamedShipToPool`.
* **HGE vtable `0x1403672f0` resolved** (file +0x90/+0x98, sound +0x138/+0x140,
  music +0x160/+0x168/+0x178, stream +0x1c0/+0x1c8), which named the whole
  `Media_Ensure*/Release*` proxy family plus `Sound_Load`, `Music_Free`.
* **Box2D contact/edge layer finished**: the six contact `_Evaluate` slots,
  `b2CollideEdgeAndCircle/Polygon`, `b2EPCollider_*`, `b2PolygonEdgeSeparation`,
  `b2EdgeShape`'s vtable, `b2ChainShape_GetChildEdge`.
* **Static-init/destructor pairing**: 90 `InitGlobal_*` initialisers in the CRT
  header and 43 `DtorGlobal_*` teardown twins at the tail, matched by global
  address. `InitGlobal_BigRecordPool` allocates 2.8M × 0x18 records at startup.
* **Two corrections made during reconciliation**: `0x1401c2ba0`
  (`Captain_CreatePanelForSlot` -> `Fleet_CreateRandomEscadraForSlot`; its
  arguments are slot presets fed to the random-fleet builder) and `0x14018f7d0`
  (mis-named `rep_..._free` -> `ISerializable_Destructor`, the base destructor
  the `Captain_Destructor` thunks tail-jump into).

## Batch 5: ten agents on the remainder (same day)

The last wave split the remainder into ten disjoint ranges (5–10 agents is the
practical range; ten works when most ranges are compiler output). It named
**~160 more functions** (153 renames + 7 created), raising the program from
2,323 to 2,483 named. Per-agent notes:
`hf_notes/docs/data/ghidra-sweep-2026-10-29-b5-agent1..10.md`.

| agent | range | result |
|---|---|---|
| 1 | 0x140330000–0x140336FFF | 1 rename + 5 created UCRT/SSE helpers (`__GSHandlerCheck*`, `__crt_thread_safe_statics_cleanup`, `__scrt_unhandled_exception_filter`, `__sse41_sinf4`) |
| 2 | 0x140337000–0x14033FFFF | 8 funclet anchors; 233 clones catalogued |
| 3 | 0x140340000–0x140347FFF | 32 `EhCleanup_*` anchors; 313 clones catalogued |
| 4 | 0x140348000–0x140350510 | 23 (4 funclet anchors + 19 static-object destructors) |
| 5 | 0x140000000–0x14006FFFF | 15 (RTTI-proved destructors, exception wrappers) |
| 6 | 0x140070000–0x14011FFFF | 6 creature accessors (`SumOffensiveScore`, `ComputeFuelRange`, `HasTWRStat`, …) |
| 7 | 0x140120000–0x14016FFFF | 25 (container clones, font glyph loops, the 4 Stats getters now proven: power/ammobox/ammobox-pri/rotation) |
| 8 | 0x140170000–0x1401FFFFF | 13 (HGE `Texture_Load` resolved, ZIP central-directory readers, `Media_EnsureTexture`) |
| 9 | 0x140200000–0x1402FFFFF | 16 (`Hud_DrawIncomingShellWarnings`, `Ship_UpdatePartElevation`, `Endgame_BuildEscadra`, prologue spawners) |
| 10 | 0x140300000–0x14032FFFF | 13 (`b2PolygonShape_ComputeAABB`, `b2PrismaticJoint_Dump`, joint dtors, `World_Render`, `FrameLimiter_Update`) |

What this wave established:

* **`rep_*` names are not trustworthy ICF replicas.** Hashing every body in
  `0x140000000–0x14006FFFF` showed **0 of 207** has an identical twin; 174 of 199
  embedded targets point *inside* an unrelated function. The `rep_` prefix is a
  stale 1.151 heuristic, and any earlier conclusion that relied on it should be
  re-checked from the body. Only rename a `rep_*` when the body disproves the
  embedded name.
* **`0x1480xxxx` xrefs are `.pdata`/unwind, not vtables.** They do not identify
  a class or a vtable slot.
* **`b2Pair` is 12 bytes in this build** (pair buffer at `+0x40`, count at
  `+0x4c`), not the stock 8.
* **The funclet runs have no per-function ownership.** Parsing the unwind/scope
  tables at `0x14808a000` would collapse the ~400 remaining clones into 20–30
  class maps; that is the single highest-leverage next step for the tail.
* **`create_function` can split the containing function.** Creating
  `Gfx_RenderQuad` (0x14016cc80) carved it out of a larger body and produced
  four new `FUN_*` fragments nearby, so raw `FUN_*` deltas undercount created
  functions. Count named functions instead.
* **`0x140324330` is `b2Island_SolveTOI`** and `0x1403345cc` is the UCRT
  thread-safe-statics initialiser; both were re-named during reconciliation
  because their `rep_*`/import labels were wrong.

## Batch 6: structural + volume (same day)

Sixth wave, ten agents. Unlike waves 2–5 this one is not a name sweep: agent 1
owns the unwind/scope-table pass, agents 2–5 re-match `rep_*` bodies by hash
instead of by their embedded labels, and agents 6–9 work the large/remaining
`FUN_*` clusters. Agent 10 only consolidates docs (`structures.md`, the audit
TSV, this section) and renames nothing.

Counts below are folded from the agents' `DONE` lines, notes and TSVs as they
landed; the program totals and anything marked `TODO` are left for the parent to
reconcile. Do not treat a `TODO` as a result.

| agent | role | scope | result |
|---|---|---|---|
| 1 | unwind/funclet owner | `.pdata`/`RUNTIME_FUNCTION` + the FH4 `FuncInfo4` funclet lists; `funclet -> owner -> member` TSV; owner-named `/EH` funclets | 926/926 funclets owned (347 owners, 97 ICF-shared, 165 without a function object); 448 renamed, 176 left with a recorded owner |
| 2 | `rep_*` re-match | `rep_*` in 0x140000000–0x1400FFFFF (minus the funclet range) | 513 audited, 21 renamed, 492 stale labels |
| 3 | `rep_*` re-match | `rep_*` in 0x140100000–0x1401FFFFF | 498 audited, 49 renamed, 448 stale, 1 unreadable |
| 4 | `rep_*` re-match | `rep_*` in 0x140200000–0x1402FFFFF | 361 audited, 34 renamed, 327 stale |
| 5 | `rep_*` re-match | `rep_*` in 0x140300000–0x140350510 (minus the funclet range) | 50 audited, 28 renamed (TSV rows: 27), 22 stale |
| 6 | large functions A | `0x14021cf40`, `0x140211e60`, `0x1402130b0`, `0x140213fc0`, `0x140216f00`, `0x14021b110` | 6 renamed, 0 skipped |
| 7 | large functions B | `0x1402410b0`, `0x140247850`, `0x140269d00`, `0x14028bf80`, `0x140292820`, `0x140296530`, quad/UV helpers `0x140172550–0x140172b10` | 10 targets: 7 renamed, 1 re-plated, 2 already named |
| 8 | containers / accessors | `FUN_*` in 0x140070000–0x1401FFFFF; `0x14015f7b0..f8a0`, `0x140073340`, `0x140073530`, `0x140088950` | 24 renamed, 55 skipped |
| 9 | CRT / Box2D remainder | `FUN_*` in 0x140000000–0x14006FFFF and 0x140300000–0x140336FFF; missing vtable slots | 4 renamed, **36 created** at Box2D joint/shape vtable slots, 33 skipped |
| 10 | documentation | `structures.md`, `rep-audit-2026-10-29.tsv`, this section | no renames; see below |

Program after the wave: **3,141 named functions, 333 `FUN_*`, 1,446 `rep_*`**
(from 2,483 named, 822 `FUN_*`, 1,579 `rep_*` before it): 621 renames by the
agents, 1 correction by the parent (`0x14016cd50` -> `Texture_Load`) and 36
functions created. Per-agent notes:
`hf_notes/docs/data/ghidra-sweep-2026-10-29-b6-agent1..10.md`.

### Results by agent

* **Agent 1 (funclet ownership)** — 926 funclets all owned (347 distinct owning
  functions) from `.pdata` + the FH4 `FuncInfo4` funclet list; 829 single-owner,
  97 ICF-shared by 2+ owners (up to 34 classes on one body); 761 have a Ghidra
  function object, 165 do not. 448 renamed (112 owners) as
  `<Owner>_EhCleanup_<member>`, 124 with an `_sz`/`_b` disambiguator; 176 `FUN_*`
  keep a recorded owner but stay unnamed (73 ICF-shared, 72 owner is a `rep_*`
  label, 27 owner is `!ClickFunc`). Also proved the handler census: 795
  `__CxxFrameHandler4`, 447 `__GSHandlerCheck_EH4`, 135 `__GSHandlerCheck`, and
  that there is **no FH3 data** in the image. Output:
  `data/funclet-ownership-2026-10-29.tsv`.
* **Agents 2–5 (`rep_*` re-match)** — 1,421 rows audited in total; the
  consolidated `data/rep-audit-2026-10-29.tsv` records **131 `renamed`, 1,289
  `stale label`, 1 `unreadable`**. Each slice independently found **0
  byte-identical twins** in the whole image, so the batch-5 "the `rep_*` prefix
  is not ICF evidence" conclusion now rests on all four slices. (The batch-7
  rebuild below found that this first merge had dropped q2's first row
  `0x140100c30`; the corrected totals are 1,421 rows / 131 renamed.) The
  worklog-vs-TSV difference was reconciled against the live program: all 131
  tabulated renames exist and the live named count matches the agents' totals,
  so the one remaining extra rename (agent 5's q4) is a TSV omission, not a
  lost rename.
* **Agent 6 (large functions A)** — all six proved: `Shipworks_BuildAutoRepairSteps`
  0x14021cf40 (the 8.7 KB body), `Grid2D_MergeAdjacentCells` 0x140211e60,
  `Gui_BlackoutOverlay_BeginClear` 0x1402130b0 /
  `Gui_BlackoutOverlay_BeginOpaque` 0x140213fc0 (the `DAT_143a13b08` singleton
  is the **"BLACK" blackout overlay**), `Fleet_RebuildShipListByValue`
  0x140216f00 and `Scene_CloneNodeSubtreeByName` 0x14021b110. Docs bonus:
  creature **+0x15d0 = ship total value** (single writer 0x14007171d),
  **+0x8f8 = GUI alpha**, `DAT_1403ef4b0` = the auto-repair state block.
* **Agent 7 (large functions B)** — 7 of the 10 targets proved: `Gfx_QuadRenderEx`
  0x140172aa0, `Thunk_RebuildNodeFromCreature` 0x1402410b0,
  `Hud_DrawRaycastStrip` 0x140247850, `Engine_ApplyThrustCommand` 0x140269d00,
  `Profile_CheckNoNestedActiveNodes` 0x14028bf80,
  `Thunk_Profile_BuildSavePath` 0x140292820, `Npc_RollAttitudeStats`
  0x140296530; HGE slot +0x2e0 proved to be the quad draw (0x140085f40), sprite
  corner record 0x58 B with colour at +0x18.
* **Agent 8 (containers/accessors)** — 24 renames: RTTI-proved destructor clones
  (`ResDesc` ×7, `Texture`, `MapShipBody`, `Anistate`, `IObject`,
  `b2ContactFilter`/`Listener`/`DestructionListener`), `RepairStepNewBlock` ctor,
  the quad helpers, five range-destroy thunks and `Media_EnsureRenderTarget`
  (HGE +0x300 -> 0x1400839d0 -> vtable 0x140356768, so the slot is the
  render-target factory). Corrections: 0x14015c1c0/e0 are destroy-range thunks
  (not `vector` `_Xlen`/`_Xrange`), 0x1401a8510 belongs to `miiProperty`
  (vtable 0x140369248), and `0x1403672f0` is `HGE_Impl`.
* **Agent 9 (CRT/Box2D remainder)** — 4 renamed and **36 functions created** at
  joint/shape vtable slots, so every table in `0x1403785e8–0x140378e00` and
  `b2PolygonShape` 0x1403529d8 now resolves to a function object; 0x1403198c0
  closed as `b2EdgeShape_GetChildCount`; 0x140334e00 identified as `__sincosf`.
  Census after: 5 `FUN_*` left in 0x140000000–0x14006FFFF and 27 in
  0x140300000–0x140336FFF (5 render helpers, 0x140319da0, 0x1403340d8, 7
  `__scrt_*`, 13 `/EH` funclets). Two hand-offs: the CRT C-initialiser table
  `0x1403519e8–0x1403521a8` (150 targets, all `LEA RCX,[global]; JMP ctor`,
  `CInit_<Global>` naming is provable) and 19 Body/Node base-class vtable slots
  with no function object.
* **Agent 10 (documentation)** — updated `structures.md` (Stats +0xdc/+0xe8/
  +0xf0/+0x108, the per-player input record, the HGE vtable, the Body vtable
  slot map, the D3D11 shader-layer summary, `b2Pair` = 12 bytes, the `rep_*`
  and funclet caveats, `+0x15d0`/`+0x8f8`), concatenated the four audit TSVs
  into `data/rep-audit-2026-10-29.tsv` (+ a format note) and wrote this
  skeleton. No renames.

### What this wave established

* **The funclet tail is a class map after all.** Owner attribution from the
  `FuncInfo4` funclet list collapses the whole clone run into 347 owners, and
  the four biggest owners are game code (`SomethingWithLevelSerias` 83 funclets,
  `lootBoxCoins` 37, `Dialog_ExecuteChoiceActions` 35,
  `TarkhanGUIDispatchOperator` 26). Naming is `<Owner>_EhCleanup_<member>` where
  the scope guard offset and the destroyed-member offset agree; the ICF-shared
  bodies keep a family anchor and a full owner list in the TSV.
* **The `rep_*` labels are worthless as identity evidence.** 1,420 bodies
  re-checked, 0 byte-identical twins, most embedded targets mid-function: the
  prefix is a stale 1.151 FID artefact. 130 renamed from the body, 1,289 recorded
  as stale with per-row evidence.
* **Box2D is complete.** The joint/shape vtable sweep created the 36 missing
  slots; no unnamed Box2D helper remains and every joint table resolves to a
  function object.
* **Verified on reconciliation:** all 131 tabulated `rep_*` renames exist under
  their expected names, all 502 `EhCleanup_*` functions in the tail carry
  plates, `0x140172550` settled on `Gfx_QuadSetCornerXY` (two agents raced on
  it; the loser restored the name), and `0x14016cd50` was corrected from a stale
  `MessageBoxA` label to `Texture_Load`. Final totals: 3,141 named, 333 `FUN_*`,
  1,446 `rep_*`.

## Batch 7: completion + C-initialisers + body slots (same day)

Seventh wave, ten agents. Unlike waves 2–6 this one has no broad name-sweep
range: it closes the concrete leftovers batch 6 handed over (funclet
completion, the CRT C-initialiser table, the Body/Node vtable slots) and
re-matches the `rep_*` that are left. Agent 10 only consolidates documentation
and renames nothing. Baseline at the start of the wave: **3,141 named, 333
`FUN_*`, 1,446 `rep_*`**.

> **Results folded by the parent.** Agent 10 wrote this section while the wave
> was still running; the parent reconciled the nine worker reports against the
> live program and filled the table below.

### Assignment

| agent | role | scope | result |
|---|---|---|---|
| 1 | funclet completion | `0x140337000–0x140350510` + the 13 at `0x140336730–0x140336f50`: the 176 owned-but-unnamed funclets and the funclet addresses with no function object; stale-`rep_*` owners (72), ICF-shared (73), `!ClickFunc` (27) | 120 renamed in place + **161 created**; 73 still open (68 stale-owner, 5 edge) |
| 2 | `rep_*` re-match | `rep_*` in `0x140000000–0x1400FFFFF`, minus the funclet-ownership TSV; appends to `q1` | 492 audited, 27 renamed, 465 stale |
| 3 | `rep_*` re-match | `rep_*` in `0x140100000–0x1401FFFFF`; appends to `q2` | 448 audited, 65 renamed, 382 stale, 1 unreadable |
| 4 | `rep_*` re-match | `rep_*` in `0x140200000–0x140336FFF`; appends to `q3` | 349 audited, 9 renamed, 340 stale |
| 5 | `rep_*` re-match | `rep_*` in `0x140337000–0x140350510`, minus the funclet TSV; appends to `q4` | 75 audited, 75 renamed, 0 stale (all proven `DtorGlobal_*`) |
| 6 | CRT C-initialisers | `.rdata` table `0x1403519e0` (249 entries): create + `CInit_<Global>` the targets without a function object; plate by constructor | **149 created**, 1 skipped (`0x140334c38`); 129 are `CInit_Atexit_*`, 20 real `CInit_*` |
| 7 | Body/Node vtable slots | the 19 slots listed in "Left for a later pass" item 5; build the Node/Body slot map, then create + name each | **19 created** (15 named, 4 recorded but unnamed) |
| 8 | real `FUN_*` A | `FUN_*` in `0x140070000–0x1401AFFFF`, minus the funclet TSV (~54) | 14 renamed, 41 skipped |
| 9 | real `FUN_*` B | `FUN_*` in `0x140200000–0x140336FFF` (~9), then the remaining CRT `FUN_*` in `0x140000000–0x14006FFFF` | 8 renamed, 19 skipped |
| 10 | documentation | `structures.md`, the audit TSV/`.md`, this section; no renames | done (below) |

### Documentation results (agent 10)

These are done and do not depend on the other agents:

* `structures.md` gained a **Body vtable slot map** for `0x140352a30`. All 19
  addresses on the hand-over list are slots of that one table (slot 0 =
  0x140018b60, RTTI locator at `0x140352a28`), with the slot/offset of each —
  so no separate Node table is needed just to locate them. The map also records
  that slot +0x298 (`0x14004bba0`) is a five-instruction forwarder to slot
  +0x48 of the object at Body `+0x9d0`, which contradicts both
  `Body_ClosePartInfoPanel` and "projectile cleanup"; the name needs a caller
  read.
* The **CRT C-initialiser table actually starts at `0x1403519e0`**, not
  `0x1403519e8` (249 pointers, `0x7c8` bytes): 247 targets in
  `0x140001000–0x140004a60`, one null entry, one target at `0x140334c38` in the
  funclet tail. Entry shape is mixed (full constructors as well as the
  `LEA RCX,[global]; JMP ctor` stub), so `CInit_<Global>` is only mechanically
  derivable for the stub subset.
* `data/rep-audit-2026-10-29.tsv` was rebuilt from `q1..q4` with address
  normalisation, **de-duplication by address (newest row wins)** and sorting.
  The rebuild restored q2's first row `0x140100c30` (`Explosion_AddProperty`),
  which the batch-6 merge had dropped: **1,421 rows, 131 `renamed`, 1,289
  `stale label`, 1 `unreadable`** (was 1,420 / 130 / 1,289 / 1). The rebuild
  command in `data/rep-audit-2026-10-29.md` is updated to the de-duplicating
  version, so it can be re-run after the batch-7 appends.

### What this wave established

Program after the wave: **5,251 function objects, 3,772 named, 197 `FUN_*`,
1,282 `rep_*`** (71.83% named). The wave reported 318 renames and created 329
functions; net named +631 over the 3,141 baseline. Every tabulated rename exists
under its expected name, and all 786 `EhCleanup*` + 151 `CInit_*` functions
carry plates.

* **Funclet completion.** 281 of the 354 in-scope funclet addresses are now
  named: 120 renamed in place, 161 created (`create_function`) and plated. The
  13-object block at `0x140336730–0x140336f50` was covered too (7 named, 6
  open). ICF-shared bodies use `EhCleanup_Shared_<family>_<n>` with the owner
  list in the plate (90); `!ClickFunc`-owned use `ClickFunc_EhCleanup_*` (28);
  163 single-owner use `<Owner>_EhCleanup_<member>`. 73 remain open: 68 whose
  owner still has a stale `rep_*` label the body disproves but does not replace,
  and 5 edge cases (no member displacement / owner has no function object).
* **C-initialisers.** 149 created; the table is `0x1403519e0–0x1403521a8` (249
  pointers). **129 entries register an `atexit` destructor callback** (`LEA
  RCX,[<dtor>]; JMP 0x14033447c`) and only **20 are real constructor/store
  initialisers** — the original "uniform `LEA RCX,[global]; JMP ctor`" reading
  was wrong. Naming: `CInit_Atexit_<Tag>` (76 with a resolved `DtorGlobal_*`
  symbol, 53 by callback address) and `CInit_<Global>` for the 20. The one skip,
  `0x140334c38`, is the `__scrt_set_unhandled_exception_filter` /
  `_set_new_mode` worker with no single global.
* **Body slots.** All 19 hand-over addresses are slots of the single 88-slot
  Body vtable `0x140352a30` (no separate Node table); 15 named, 4 created but
  left unnamed with the behaviour recorded. `0x14004bba0` is
  `Body_ClosePartInfoPanel` after all: it forwards to slot +0x48 of the cached
  panel at Body `+0x9d0`, which the agent-10 note had doubted.
* **`rep_*` re-match.** 1,364 more bodies audited; 176 promoted to real names,
  the rest stayed stale with sharper partial identities. The atexit-destructor
  tail (75) was fully proven and pairs with `InitGlobal_*`/`DtorGlobal_*`.
* **Caveats confirmed:** 0 byte-identical twins anywhere; the shared Ghidra
  script bundle is broken (use a subdirectory bundle); `0x14021fe10` and
  `0x1402f3fd0` are stale `rep_*` labels still worth a re-match; ~170 `.rdata`
  targets into `0x140070000–0x1401AFFFF` still have no function object.

## Batch 8: `.rdata` creation + slots + audit (same day)

Eighth wave, ten agents. Baseline at the start of the wave: **5,251 function
objects, 3,772 named (71.83%), 197 `FUN_*`, 1,282 `rep_*`**. This wave is not a
broad name sweep: agents 1–2 create the missing function objects behind the
`.rdata` vtable slots, agent 3 closes the 73 open funclets, agents 4–7 re-match
the remaining `rep_*`, agents 8–9 take the last real `FUN_*` and the Body/HGE
slot families, and agent 10 only consolidates documentation (no renames).

> **Results folded by the parent.** Agent 10 wrote the assignment table while
> the wave was running; the parent reconciled all ten worker reports against
> the live program and filled the results below.

### Assignment

| agent | role | scope | result |
|---|---|---|---|
| 1 | `.rdata` creation A | qwords in `0x140352000–0x14036A000` that point into `0x140070000–0x1400FFFFF` and have no function object; create + name/plate | **46 created**, all named + plated; re-scan reports 0 functionless targets left |
| 2 | `.rdata` creation B | same for `0x140100000–0x1401AFFFF`; excludes the four HGE RNG slots (agent 9) | **120 created** (89 named + plated, 31 created/plated with name withheld as unprovable), 0 skipped |
| 3 | open funclets | the 73 still-open funclets in `0x140336730–0x140350510` (owner first, then funclet) | 7 owners renamed + **7 funclets named/plated**, 66 still open (61 with an owner function object but no proven identity, 5 without a function object at the funclet address) |
| 4 | `rep_*` re-match A | `rep_*` in `0x140000000–0x1400FFFFF`, minus funclet addresses; appends to `q1` | 410 audited, 26 renamed, 384 stale |
| 5 | `rep_*` re-match B | `rep_*` in `0x140100000–0x1401FFFFF`; appends to `q2` | 382 audited, 54 renamed, 325 stale, 1 unreadable |
| 6 | `rep_*` re-match C | `rep_*` in `0x140200000–0x1402FFFFF`; appends to `q3` | 317 audited, 29 renamed, 20 stale (rest already audited) |
| 7 | `rep_*` re-match D | `rep_*` in `0x140300000–0x140336FFF`; appends to `q4` | 21 audited, **15 renamed**, 6 stale, 0 unreadable; q4 now 145 data rows (the 21 rows override earlier ones, so the consolidated row count does not move) |
| 8 | last real `FUN_*` | the D3DEngine dispatch family, GUI callbacks, small predicates, padding/thunks, `__scrt_*`, `0x140319da0`, `0x1403340d8`, `0x14028b340` (~56) | **76 renamed** (63 `DtorGlobal_*` tail + 7 `Gfx_*` + 2 texture + 4 misc), 55 left |
| 9 | slots | the four created-but-unnamed Body slots (`0x140018fb0`, `0x140053110`, `0x14004c7e0`, `0x14004d8e0`) and the four HGE RNG vtable slots (`0x140174350/320/2d0/310`) | 4 created + 3 renamed (`Body_OnClick`, `Body_LinkAdjacentParts`, `Body_DrawMeshPolygon`), 1 skipped |
| 10 | documentation | `structures.md`, the audit TSV/`.md`, this section; no renames | done (below) |

### Creation requests posted (not results)

These are the blackboard `-> creation` posts as they stood when this skeleton
was written. None of them is a completed count — the parent should replace each
with the agent's actual `created` / `named` / `skipped` line.

* **Agent 2** — 120 `.rdata` targets into `0x140100000–0x1401AFFFF` with no
  function object, derived from the batch-7 agent-8 list; the four HGE RNG
  slots are explicitly excluded (agent 9 owns them).
* **Agent 1** — 46 `.rdata` targets into `0x140070000–0x1400FFFFF`, each
  re-checked against the live program and attributed to a vtable through the
  MSVC RTTI locator preceding the table. The posted family map (owning table ->
  targets) is specific enough to name most of them: `.?AVCreature@@` slot 9,
  `basic_ofstream` / `basic_filebuf` slots, `TextureSingle` / `RenderTarget`
  slots 1–3, `Effect` / `IShader` slot 18, twelve `Shader*` tables
  (`Init` / `EmitVerticesA` / `EmitInstances`), four `std::function<float(float)>`
  lambda tables around `0x140092f30–0x1400930c0`, `Intel` / `Launched` scalar
  deleting destructors, `MapShip@Escadra`, the three property containers,
  `Escadra` / `Location` slot 43, `MapShipBody` slot 58 and two
  `ShaderParam*New` slots.
* **Agent 9** — 4 HGE RNG slots. The posted disassembly agrees with the
  independent read now in
  [../structures.md](../structures.md#hge-rng-one-msvc-rand-lcg-code-2026-10-29):
  seed setter 0x140174350, int range 0x140174320, float range 0x1401742d0,
  getter 0x140174310, LCG state `0x1439e8688`.

### Worker results

**Agent 3 (open funclets)** — full detail in
[ghidra-sweep-2026-10-29-b8-agent3.md](ghidra-sweep-2026-10-29-b8-agent3.md).
Of the 73 open funclets, **7 owners were proven and renamed, and their 7
funclets named + plated; 66 remain open** (61 with an owner function object but
no provable identity, 5 with no function object at the funclet address). The
proved owners are all real game classes hiding behind stale `rep_*` labels:

| owner addr | new owner name | funclet |
|---|---|---|
| 0x1401c7060 | `Fleet_CreateEscadraFromShips` | 0x140343460 |
| 0x140202010 | `Moral_BuildMiniFigPanel` | 0x140343ff0 |
| 0x1400eb460 | `Escadra_AddIntelEntry` | 0x14033d640 |
| 0x1400e5530 | `Escadra_CopyFrom` | 0x14033d500 |
| 0x140061000 | `Creature_AddLandingLights` | 0x140338a10 |
| 0x14012c280 | `Gui_CopyConstructor` | 0x14033ec50 |
| 0x140087790 | `Shader_AddParam` | 0x140339240 |

The extra proof signal was the `FUNCINFO4` sized-delete operand: the funclet's
`sz=` equals the size of the temporary the owner allocates (`New(sz)`), which
confirms the owner↔funclet pair independently of the `.pdata` mapping. The 66
open split into 31 generic container/allocator helpers, 2 FX spawners, 23
subsystem procedures, 5 edge cases and 5 with no function object.

**Agent 7 (`rep_*` re-match D)** — full detail in
[ghidra-sweep-2026-10-29-b8-agent7.md](ghidra-sweep-2026-10-29-b8-agent7.md).
Only 21 `rep_*` remained in its two ranges (not ~120: the earlier waves had
renamed the rest), and 15 are now proven; the 6 stale are five EH funclets plus
`0x1403182a0`.

* **The VideoTask render dispatch is resolved.** `VideoTask_Dispatch`
  (0x140300c20) has mutually exclusive branches that map to
  `VideoTask_RenderEditorScene` 0x140300db0, `VideoTask_RenderBattleScene`
  0x1403050a0, `VideoTask_RenderMapScene` 0x14030a6b0 and
  `VideoTask_RenderMenuScene` 0x14030f250; the branch flags match the
  `source-file-names.md` screen table and the probe run. The four bodies are
  17–19 KB, so identity is caller-side, not from decompiling them.
* **`0x140334b70` / `0x140334c28` are C initialisers, not `__scrt_*` stages.**
  `mainCRTStartup` walks `_initterm_e(0x1403521b8, 0x1403521e0)` and both
  addresses are entries of that table (`_set_app_type`, fmode, commode, onexit,
  argv, locale …). Named `CRT_InitializeProcess` / `CRT_InitializeStdioOptions`.
  This is a correction to the old "`__scrt_*` stubs" reading.
* Also renamed: `MapMode_DrawRadarSweep` 0x140314290,
  `Hud_DrawZoomViewOverlay` 0x140315580, `ShipCard_DrawBearingTrail` 0x140315b40,
  `VideoTask_LayoutShipCards` 0x140316230, `Physics_ShapeDistance` 0x140318920,
  `CRT_InitializeSListThunk` 0x14033535c, `CRT_GuardDispatchThunk` 0x1403353a4,
  `sinf4` 0x140334de0 and `sinf4_ScalarShim` 0x140334e43.
* `0x1403353a4` is the guard-**check** table walker, not the dispatch thunk; the
  dispatch itself is the import thunk at 0x1403366f0.
* **Open disagreement to settle:** agent 7 left the five bodies
  `0x140336c80/d20/df0/ea0/f00` as EH funclets that belong to agent 3's band but
  are absent from the ownership TSV; agent 3 replied that each has its own
  `UNWIND_INFO` and a real prologue, so they are primary functions ICF-aliased
  onto funclet-shaped bodies, not funclets, and did not rename them. The parent
  should decide; they are inside agent 7's `0x140330000–0x140336FFF` range.

**Other workers.** Agent 1 created the 46 targets in its slice and proved each
one through the MSVC RTTI CompleteObjectLocator, so every target got a class +
slot (`Effect+0xc0` projection matrix; four `std::function<float(float)>`
wrappers around `Property_SetFloat148/158/168`; Escadra/Location slot-43
virtuals with `ESCADRA_NAME_`/`LOCATION_NAME_`). Agent 2 created 120, resolving
the full `HGE_Impl` vtable `0x1403672f0` and the GUI-element/ResDesc families.
Agent 4 renamed 26 (the `InitBaseFields` family, seven `basic_filebuf`
overrides, `Shader_CompileFromFile`, `RenderTarget_Create`, …) and found that
this build's COL stores `pTypeDescriptor`/`pClassHierarchy` as **32-bit
image-relative offsets at COL+0x0c/+0x10**, which resolves 247 vtables. Agent 5
renamed 54 (HGE/I-O loaders, 17 GUI/map builders, FNV-1a hash map, game logic).
Agent 6 renamed 29 (Node/Body, Sprite/Anistate, HUD markers, profiler,
sound/shop, containers). Agent 8 renamed 76 (63 atexit `DtorGlobal_*`, 7
`Gfx_*` dispatch, 2 texture size adapters, 4 misc) and mapped HGE `+0x18` =
ID3D11Device, `+0x20` = DeviceContext, `+0x28` = SwapChain, `+0x1a0` = current
shader. Agent 9 named the four HGE RNG slots and three Body slots.

**Disagreement settled.** `0x140336c80/d20/df0/ea0/f00` are primary functions
that carry stale `rep_..._CxxThrowException` labels and their own `UNWIND_INFO`
— agent 3 is right; they are not funclets and remain for a `rep_*` re-match.

### Documentation results (agent 10)

These are done and do not depend on the worker agents:

* `structures.md` gained the **HGE RNG** subsection (four vtable slots, 32-bit
  LCG state `0x1439e8688`, `0x343fd` / `0x269ec3`, the high-16-bit output with
  its ~2^-16 scale, and the note that the state lives in zero-initialised
  `.data` and has no file bytes at load time).
* `structures.md` resolved the Body slot +0x298 row: `0x14004bba0` is
  **`Body_ClosePartInfoPanel`** (batch-7 caller proof), not "projectile cleanup";
  the four created-but-unnamed slots now point at their recorded behaviour.
* `data/rep-audit-2026-10-29.tsv` was rebuilt from `q1..q4` with `0x`
  normalisation, de-duplication by address (newest row wins, order q1 -> q4) and
  numeric sort. Snapshot after the batch-8 agent-7 append: **1,496 rows, 321
  `renamed`, 1,174 `stale label`, 1 `unreadable`**. **TODO (parent):** re-run
  the rebuild after agents 4–6 append and refresh both count tables.
* Added the batch-8 assignment table, the agent-7 result summary and this
  skeleton.

### Counts

Program after the wave: **5,421 function objects, 4,128 named (76.15%), 142
`FUN_*`, 1,151 `rep_*`**. The wave reported **217 renames and 170 created
functions** (139 of them named), so net named +356 over the 3,772 baseline.

* Everybody's tabulated renames verify: 431 audit-TSV rows and the 13-row
  `Gfx_*`/misc table all match the live program; 24 `Gfx_*` and 4 `HGE_Rand*`
  functions all carry plates; 32 `FUN_*` carry plates (the created-but-unnamed
  families) and 110 do not.
* `.rdata` creation is complete for both slices: 166 new function objects, 0
  functionless `.rdata` targets left in `0x140070000–0x1401AFFFF`.
* HGE RNG (4 slots), the CInit table, the funclet tail and the Body vtable are
  all resolved; the remaining work is the 73 open funclets, 1,151 stale `rep_*`,
  and ~110 `FUN_*` (mostly open funclets/padding).

## Batch 9: final tail (same day)

Ninth and last wave, ten agents. Baseline at the start of the wave: **5,421
function objects, 4,128 named (76.15%), 142 `FUN_*`, 1,151 `rep_*`**. The wave
has no broad name-sweep range: it finishes the 66 open funclets, re-matches the
remaining 1,151 `rep_*`, names the 32 created-but-unnamed functions (31
`.rdata` slots + Body `+0x240`) and plates the last real `FUN_*`. Agent 10 only
consolidates documentation (`structures.md`, the audit TSV/`.md`, this section)
and renames nothing.

Mid-wave the blackboard gained the **rename protocol** (ground rule 2): an
existing name that is *provably wrong or misleading* may now be renamed (never
for style), with the old name recorded. Those renames are **corrections**, not
new discoveries — they are recorded separately below and must not be counted as
newly named functions.

> **Results folded by the parent.** Agent 10 wrote the assignment table while
> the wave was running; the parent reconciled all ten worker reports against
> the live program and filled the results below.

### Assignment

| agent | role | scope | result |
|---|---|---|---|
| 1 | open funclets A | open funclets in `0x140336730–0x14033FFFF`; stale-owner cases: rename the owner first, then the funclet | 2 owners renamed + 4 funclets named; 33 open (29 with an object, 4 without) |
| 2 | open funclets B | open funclets in `0x140340000–0x140347FFF` (same method) | 2 owners renamed + 3 funclets named; 18 open |
| 3 | open funclets C | open funclets in `0x140348000–0x140350510` (same method) | 5 owners renamed + 9 funclets named (1 created from a 29-byte `.pdata` extent); 1 open |
| 4 | `rep_*` re-match A | remaining `rep_*` in `0x140000000–0x1400FFFFF` (~437); appends to `q1` | 384 audited, 42 renamed, 342 stale; 1 correction (`Escadra` -> `Escadra_Constructor`) |
| 5 | `rep_*` re-match B | remaining `rep_*` in `0x140100000–0x1401FFFFF` (~328); appends to `q2` | 326 audited, 33 renamed, 293 stale, 0 unreadable |
| 6 | `rep_*` re-match C | remaining `rep_*` in `0x140200000–0x1402FFFFF` (~288); appends to `q3` | 287 audited, 85 renamed, 15 stale; 195 left |
| 7 | `rep_*` re-match D + primaries | remaining `rep_*` in `0x140300000–0x140350510` (~105), **including** the five `_CxxThrowException` addresses; appends to `q4` | 6 effective, 3 renamed, 3 stale. **Correction: the five are EH funclets, not primaries** |
| 8 | created-but-unnamed | the 32 created-but-unnamed functions: 31 `.rdata` targets + `FUN_14004c7e0` (Body `+0x240`) | 29 named + re-plated, 3 left with reasons (`0x14017c780`, `0x14017c800`, `0x14004c7e0`) |
| 9 | last unplated `FUN_*` | the ~110 `FUN_*` without plates | 54 in scope, 5 named + plated (`type_info_*`, `Cloud/Ground_SetSpawnParams`, two destroy-range thunks), 49 skipped |
| 10 | documentation | `structures.md`, the audit TSV/`.md`, this section; no renames | done (below) |

The "66" in rows 1–3 is the batch-8 **total** for all three funclet agents, not
each slice: the blackboard assignment repeated the total, and the live split
reported by agent 2 is **35 / 21 / 10** for `0x140336730–0x14033FFFF`,
`0x140340000–0x140347FFF` and `0x140348000–0x140350510`. Agent 2's slice had 21
open funclets, not 66.

### Worker results

* **Agents 1–3 (open funclets).** 9 owners renamed and 16 funclets named (1
  created from a 29-byte `.pdata` extent); 52 open. The live split was
  35 / 21 / 10, not 66 each. Proven owners include `Escadra_FindRefuelTarget`,
  `Gui_BuildMinifigCard`, `HistoryDesign_CreateFromCreature`,
  `Ship_RecreateFromBackup`, `Battle_DeployFromReserve`,
  `Body_TryAttachBodies`, `Sprite_CopyFrom`, `Ground_DrawMarker`,
  `CityLandscape_RenderTiles`. `0x14034b743` is not a cleanup at all (it tests
  `STATUS_ACCESS_VIOLATION`). Two owners had already been renamed by agent 6.
* **Agents 4–7 (`rep_*` re-match).** 1,003 bodies re-checked; 163 promoted,
  the rest stale. `q1` 42, `q2` 33, `q3` 85, `q4` 3. The consolidated audit is
  **1,496 rows / 593 `renamed` / 903 `stale label`**.
* **Agent 7 (five `_CxxThrowException` addresses).** The five are **EH funclets,
  not primaries**: no CALL xref, establisher frame in RDX, `UNWIND_INFO` flags 0,
  `_CxxThrowException(0,0)` rethrow epilogue, sitting in the funclet-only band.
  This reverses the batch-8 conclusion (which `structures.md` had recorded).
  Three are now named `Vector24/VectorString56/VectorString_InsertReallocate_EhCleanup_*`;
  two remain stale because their owner (`0x140013160`) is still a `rep_*`.
* **Agent 8 (created-but-unnamed).** 29 of 32 named: `Slider_SetValue` (which
  unblocks two funclets), `Gui_ActivateElement`/`DeactivateElement`,
  `Gui_OnHoverEnter`, `Gui_DrawElement`, `Gui_Update`, `List_*`/`ObjectList_*`
  accessors, `Frame_IsStatic`, `Escadra_OnElementRemoved`,
  `lProperty_WriteField`. Three left: `0x14017c780`, `0x14017c800`,
  `0x14004c7e0`.
* **Agent 9 (last unplated `FUN_*`).** 54 in scope; 5 named
  (`type_info_ScalarDeletingDestructor`, `Cloud_SetSpawnParams`,
  `Ground_SetSpawnParams`, two `Vector*_DestroyRangeThunk`s); 49 skipped
  (`__scrt_*`, padding, split fragments, record ctors with no owner).
* **Agent 10 (documentation).** Updated `structures.md` (Body rows, the five
  rethrow bodies, the 31 withheld `.rdata` slots), rebuilt the audit TSV and
  wrote this section.

### Corrections to existing names (rename protocol)

| addr | old name | new name | evidence | agent |
|---|---|---|---|---|
| 0x1400e36a0 | `Escadra` | `Escadra_Constructor` | ctor body (base init + vtable) — old name was a bare class name | 4 |

No other already-named function was renamed; the misleading names encountered
were all `rep_*` labels or were already in the agent's own scope.

### Counts

Program after the wave: **5,422 function objects, 4,350 named (80.23%), 93
`FUN_*`, 979 `rep_*`**. The wave reported **221 renames + 1 created function**
(net +222 named over the 4,128 baseline). All 593 tabulated renames exist under
their expected names and all carry plates; the owner/funclet names quoted in
the notes were spot-checked live.

The remaining work is now small: 52 open funclets, 903 stale `rep_*`, 93
`FUN_*` (mostly the same open funclets and padding), and three withheld names.

## `!` functions

Only two functions carry the `!` prefix in this database:

* `!ClickFunc` (0x14012f120) - already had a plate comment from
  [click-func.md](../rendering/click-func.md); unchanged.
* `!FrameFunc` (0x1401a8970) - **new plate comment**. It is the game loop's
  per-frame callback: frame delta from `QueryPerformanceCounter`, the global
  `GameClock` advance, the day/night phase (`_DAT_143a119d0`, 15-hour cycle),
  the current time-speed selection (`DAT_1403c1270`), then the fixed task chain
  `SomethingPreTask -> SomethingPhysicTask -> SomethingInputTask ->
  SomethingAITask -> SomethingGameTask -> SomethingSoundTask ->
  SomethingVideoTask`. Read from the decompiler (it decompiled after all, with
  the `!` name); no ASM pass was needed.

## Left for a later pass

The unnamed set at the start of the day was 2,201 `FUN_*` and 1,674 `rep_*`
(3,875 total; 990 named). After all nine waves: **93 `FUN_*` and 979 `rep_*`**
remain unnamed, and the program has 4,350 named functions (80.23% of 5,422).
What is left:

1. **52 open funclets** in `0x140336730–0x140350510`: mostly generic
   container/allocator replicas and subsystem procedures with no single
   identity. Owner map: `data/funclet-ownership-2026-10-29.tsv`.
2. **979 stale `rep_*`.** 593 have been renamed from body evidence; the rest
   are real unnamed bodies whose labels point into unrelated functions. Per-row
   evidence: `data/rep-audit-2026-10-29-q*.tsv`. Highest-value still-stale:
   `0x1402e3580` (sound-name normaliser), the two `_CxxThrowException` funclets
   owned by `0x140013160`, and `0x1403182a0`.
3. **93 `FUN_*`**: the open funclets plus padding, `__scrt_*` outlines, split
   `CopyEscadraName` fragments, small predicates with unknown fields
   (`0x140073340`, `0x1400a6210`, `0x1400f51c0`, `0x1400bee20`,
   `0x1400fdec0`).
4. **Three withheld names**: `0x14017c780`, `0x14017c800`, `0x14004c7e0`.
5. **Six `Cloud`/`Ground`/`Landpart` vtable slots** with no function object,
   and four out-of-scope stale `rep_*` CRT labels reported by batch-9 agent 9.

Suggested order: the two `_CxxThrowException` funclets (owner `0x140013160`),
then the highest-value stale `rep_*` above, then the remaining `FUN_*`.

## `!` functions

Only two functions carry the `!` prefix in this database:

* `!ClickFunc` (0x14012f120) - already had a plate comment from
  [click-func.md](../rendering/click-func.md); unchanged.
* `!FrameFunc` (0x1401a8970) - **new plate comment**. It is the game loop's
  per-frame callback: frame delta from `QueryPerformanceCounter`, the global
  `GameClock` advance, the day/night phase (`_DAT_143a119d0`, 15-hour cycle),
  the current time-speed selection (`DAT_1403c1270`), then the fixed task chain
  `SomethingPreTask -> SomethingPhysicTask -> SomethingInputTask ->
  SomethingAITask -> SomethingGameTask -> SomethingSoundTask ->
  SomethingVideoTask`. Read from the decompiler (it decompiled after all, with
  the `!` name); no ASM pass was needed.

## Left for a later pass

The unnamed set at the start of the day was 2,201 `FUN_*` and 1,674 `rep_*`
(3,875 total; 990 named). After all eight waves: **142 `FUN_*` and 1,151
`rep_*`** remain unnamed, and the program has 4,128 named functions (76.15% of
5,421). What is left:

1. **66 open funclets** in `0x140336730–0x140350510`: 61 have an owner function
   object but no proven identity (generic container/allocator helpers, FX
   spawners, subsystem procedures), 5 have no function object at the funclet
   address. Owner map: `data/funclet-ownership-2026-10-29.tsv`.
2. **1,151 stale `rep_*`.** The audit has 1,496 rows (306 renamed); the rest are
   real unnamed bodies whose embedded labels point into unrelated functions.
   Per-row evidence: `data/rep-audit-2026-10-29-q*.tsv`. Known leftovers:
   `0x14021fe10`, `0x1402f3fd0`, and the five primary functions at
   `0x140336c80/d20/df0/ea0/f00` (stale `_CxxThrowException` labels, not
   funclets).
3. **~110 `FUN_*` without plates**: mostly the open funclets/padding plus the
   small predicates and thunks agents 8/9 deliberately skipped
   (`0x140073340`, `0x1400a6210`, `0x1400f51c0`, `0x1400bee20`, `0x1400fdec0`,
   `0x140319da0` is named, `0x14028b340`, the `__scrt_*` stubs).
4. **32 created-but-unnamed created functions**: 31 of agent 2's `.rdata`
   targets (created and plated, name withheld as unprovable) and
   `FUN_14004c7e0` (Body slot +0x240).
5. **The last unproven slots**: the four HGE RNG slots are done; `0x14004c7e0`
   is the only Body slot left.

Suggested order for the next pass: the 66 funclets (owner-by-owner), then the
1,151 `rep_*` body re-match, then the small predicates/thunks.

## `!` functions

Only two functions carry the `!` prefix in this database:

* `!ClickFunc` (0x14012f120) - already had a plate comment from
  [click-func.md](../rendering/click-func.md); unchanged.
* `!FrameFunc` (0x1401a8970) - **new plate comment**. It is the game loop's
  per-frame callback: frame delta from `QueryPerformanceCounter`, the global
  `GameClock` advance, the day/night phase (`_DAT_143a119d0`, 15-hour cycle),
  the current time-speed selection (`DAT_1403c1270`), then the fixed task chain
  `SomethingPreTask -> SomethingPhysicTask -> SomethingInputTask ->
  SomethingAITask -> SomethingGameTask -> SomethingSoundTask ->
  SomethingVideoTask`. Read from the decompiler (it decompiled after all, with
  the `!` name); no ASM pass was needed.

## Left for a later pass

The unnamed set at the start of the day was 2,201 `FUN_*` and 1,674 `rep_*`
(3,875 total; 990 named). After all seven waves: **197 `FUN_*` and 1,282
`rep_*`** remain unnamed, and the program has 3,772 named functions (71.83% of
5,251). What is left:

1. **73 open funclets** in `0x140336730–0x140350510` (68 whose owner still
   carries a stale `rep_*` label that the body disproves but does not replace,
   and 5 edge cases with no member displacement or no owner function object).
   Owner map: `data/funclet-ownership-2026-10-29.tsv`.
2. **1,282 `rep_*` names that are stale, not replicas.** 1,364 bodies were
   audited in this wave (176 promoted); the rest need a body-level re-match.
   Per-row evidence is in `data/rep-audit-2026-10-29-q*.tsv`. Known leftovers
   worth a pass: `0x14021fe10`, `0x1402f3fd0`.
3. **~170 `.rdata` targets into `0x140070000–0x1401AFFFF` with no function
   object** (real 8–40-byte getters/forwarders/scalar-deleting destructors,
   e.g. `0x140093080` = `LEA RAX,[RCX+8]; RET`), concentrated in the D3D11
   shader, GUI-element, HGE-media and font layers. A mechanical
   `create_function` pass; the list is in the batch-7 agent 8 note.
4. **Four created-but-unnamed Body slots** (`0x140018fb0`, `0x140053110`,
   `0x14004c7e0`, `0x14004d8e0`) whose behaviour is recorded but whose name
   needs a caller/editor read.
5. **The last real `FUN_*`** outside the funclet tail (about 56): the
   D3DEngine.cpp dispatch family `0x140083760`/`0x140085e80`/`eb0`/`f40`/`f80`/
   `fc0`, three GUI callbacks with stale-`rep_*` callees, small predicates with
   unknown fields (`0x140073340`), padding/thunks, and the
   `__scrt_*`/`0x140334c38` stubs.
6. **HGE RNG vtable targets** `0x140174350/320/2d0/310` (vtable
   `+0x100/+0x108/+0x110/+0x118`) were requested but not created; the LCG state
   is `0x1439e8688`.

Suggested order for the next pass: the ~170 `.rdata` creation targets (item 3),
then the 73 funclet owners (item 1), then the remaining real `FUN_*` (item 5).
