# Ghidra changes, 2026-10-29 (unnamed-function sweep, first pass)

Program `Highfleet.exe.unpacked.exe` v1.163, saved (version after the sweep). The
check-in to the shared project is the user's.

This pass started from the full function list and worked through the unnamed
`FUN_*` / `rep_*` functions, prioritising (a) helpers that almost every game
function calls, (b) game logic whose callers/callees were already named, and
(c) clusters that can be identified from an existing note or from a string
reference. 166 functions were renamed and given a plate comment in doc-comment
style (summary sentence, `Algorithm`, `Parameters`, `Returns`). `!FrameFunc`,
one of the two `!` (decompile-size) functions, also got a plate comment.

Conventions used in this pass:

* names follow the existing `<Subsystem>_<Verb><Object>` shape (`Body_Explode`,
  `Part_GetRange`, `AircraftLogic_SetState`);
* std/CRT helpers keep a `String_` / `Vector` / `RbTree_` / `NewArray` prefix
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
| 0x140005620 | `ThrowBadArrayNewLength` | throws `std::bad_array_new_length` |
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
| 0x140007d00 | `NewArray8` | `operator new[]` for 8-byte elements |
| 0x140055f50 | `NewArray24` | 24-byte elements |
| 0x140055fd0 | `NewArray40` | 40-byte elements |
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
| 0x140015f00 | `Body_Constructor` | `Body::Body` |
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

The unnamed set at the start of the pass was 2201 `FUN_*` and 1674 `rep_*`
(4865 total functions). After the pass: 2042 `FUN_*` and 1667 `rep_*`. The rest
is deliberately not renamed yet, because a name would be a guess:

1. **CRT / compiler boilerplate at the bottom of the image.** `_eh` cleanup
   funclets, duplicated `free`-one-field destructors (0x140344000..0x140345000
   is a long run of identical 0x20-byte functions), exception copy helpers and
   the `atexit` stubs. Naming these adds noise; they are compiler output, not
   game logic.
2. **The `FUN_*` factory block 0x140086000..0x14009b000.** Some 300 small
   three-line functions that each `New` a derived object, call a specific
   constructor (`FUN_14009f9xx`, `FUN_14009faxx`) and push it into one of the
   owner's vectors. They are one class factory per GUI/serialiser type; naming
   them needs the class of each constructor, which the constructors do not
   reveal (they only differ in vtable). This is the single biggest remaining
   cluster.
3. **The `SomethingWithLevelSerias` callees 0x1402ca070..0x1402d45c0.** These
   are the per-frame ticks of the `SCR_*` scenes (one of them,
   `0x1402ca2b0`, is already `SCR_BOMBERS`; `0x1402cdaf0` / `0x1402cdfb0` are
   `SCR_COMBAT` / `SCR_COMBAT_SKIRMISH_PVP` from the 2026-10-28 pass). They have
   no arguments and only touch globals, and the dispatcher calls them
   conditionally, so identifying each one needs reading the dispatcher's branch
   conditions for that call site, not the callee.
4. **Box2D internals 0x140330000..0x140350510.** Most `b2*` entry points are
   already named; the unnamed ones are per-joint solver/init pairs and the
   contact/TOI internals. The matrix and body helpers that could be identified
   from their call sites (`b2Body_SetEnabled`, `b2Mat22_GetInverse`,
   `b2Mat33_GetSymInverse33`, `b2Mat22_Solve`, `b2Mat33_Solve33`,
   `b2World_ResetProfile`, `b2Island_Destroy`) were done in this pass; the rest
   needs the Box2D 2.3 source read side by side with each joint's solver.
5. **Functions whose identity depends on an unread global.** e.g.
   0x1400dd0d0 (0x950, called from `!ClickFunc`, Shipworks commit/exit), the
   `0x1402cf4d0` / `0x1402d45c0` scene ticks, 0x1401c7270 (0x25d0, called by
   `World_ThermalPass`), 0x1400b1440 (0x77d0, `mainDialogWithChoices` and
   `!ClickFunc`). These are good next targets once their main caller is read.

Suggested order for the next pass: the `SomethingWithLevelSerias` ticks first
(one dispatcher read names up to fourteen functions), then the Box2D joint
pairs (mechanical), then the factory block if it is needed at all.
