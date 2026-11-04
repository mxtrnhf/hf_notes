# Ghidra sweep 2026-10-29 — batch 3, agent 5 (0x140200000–0x1402FFFFF)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Continues `ghidra-sweep-2026-10-29-agent5.md` (batch 2). Only `FUN_*` functions
that were still unnamed were touched; batch 2's `SCR_*`, `Battle_*`, `AiShip*`,
`Precombat_*` and container names were left alone.

Range: 184 unnamed `FUN_*` on entry, **141 renamed**, 43 left (list at the end).
`rep_*` thunks were not renamed: they are duplicated bodies of already-named
functions (e.g. `rep_1402a9430_...free` is a chunk of
`Player_SendThrustCommands` 0x1402a9300), so a name would only repeat the
original.

All renames have a doc plate (summary / Algorithm / Parameters / Returns).

## Scene-adjacent and app helpers (0x14024xxxx, 0x1402Cxxxx, 0x1402Fxxxx)

| addr | new name | description |
|---|---|---|
| 0x140240b90 | `App_ReloadSeria` | reload the level script named in `SeriaToLoad` (the `APP::reload_sg` path); on failure writes `OL.seria`/`Config.ini` and sets `g_bExitRequested` |
| 0x140241e90 | `Profile_EnumerateScreenshots` | walk `Saves/Profile_<n>/*.png` and load each into the screenshot list |
| 0x14024c8e0 | `Scene_ExitToHall` | clear the 0x148 scene block, save the event log, then select `Hall` / `Intermedia_01` / `PreselectSkirmish(.PVP).seria` |
| 0x140256a90 | — | (skipped) frame/hull elevation and floor pass, 7 KB |
| 0x140289d20 | `Location_Destructor` | location/city destructor, frees the child vectors and clears `CURRENT_LOCATION` |
| 0x14028db90 | `Scene_ResetGlobalLinks` | free the global link lists and reset the scene counter +0x118 |
| 0x14028dda0 | `Scene_ResetGlobalLinksAndCamera` | same free, then restore camera distances/modes |
| 0x1402c7a70 | `Sort_Median3Float1604` | median-of-three step of the introsort on object+0x1604 |
| 0x1402c7fb0 | `Sort_PartitionFloat1604` | partition step of the same sort |
| 0x1402c8460 | `Sort_IntrosortFloat1604` | introsort (insertion + quicksort + heap fallback) by object+0x1604, used by `SCR_BOMBERS` |
| 0x1402c82f0 | `List_MergeSortByFloatF8` | merge sort of a link list by node value +0xf8, used by `SCR_MISSILE_SpawnDefenders` |
| 0x1402c87c0 | `List_InsertRangeCopy` | insert a copy of a pointer range into a doubly linked list |
| 0x1402ee440 | `Gfx_DrawFullscreenQuad` | full-screen fade/overlay quad |
| 0x1402ee520 | `Gfx_DrawScreenRect` | 300x480 screen rectangle overlay |
| 0x1402f41b0 | `Sprite_LoadAll` | load every sprite of a holder vector |
| 0x1402f4410 | `Gfx_DrawOverlaySprite` | profile-driven overlay sprite at the origin |
| 0x1402fa100 | `Gui_FlushDrawList` | flush the deferred GUI draw list (list at +0x588) in reverse |
| 0x1402fd580 | `Camera_ZoomByXPreset` | zoom preset looked up by a creature x position |
| 0x1402ec730 | `Sprite_AddToGlobalList` | append to the global sprite vector, store the index at +8 |
| 0x1402ecb80 | `Array_DeleteObjectsBackward` | destroy the polymorphic objects of a vector back to front |

## Battle / fleet helpers (0x140210000–0x140240000)

| addr | new name | description |
|---|---|---|
| 0x140210000 | `List_MoveCursor` | move a GUI list cursor by a signed count and activate the element |
| 0x140210620 | `Creature_OnDestroyed` | return crew to the pool, clear the volume, kill the creature |
| 0x1402106a0 | `Battle_CleanupBodiesType210` | kill every active body with logic id 210 |
| 0x1402109d0 | `Hud_ShowLandModePrompt` | delete the land-mode prompt widgets when no fleet ship is in land mode |
| 0x1402111e0 | `Array_Erase16` | erase one 0x10-byte element from a vector |
| 0x140211220 | `City_EnterShipworks` | enter the shipworks from a city (`loadShipworks_`) |
| 0x1402151e0 | `Gfx_ApplyLensDistortion` | barrel distortion of a screen point, in place |
| 0x140215b60 | `Fleet_SetCompData` | forward a comp-data update to `PLAYER_ESCADRA_` |
| 0x140216450 | `Progress_GetFractionFromPair` | `((0x46-chapter)*100-step+10)/7020` campaign progress |
| 0x140216480 | `Progress_GetFraction` | `value/7020` campaign progress |
| 0x140216490 | `Localization_FindEntry` | map lookup of a localisation entry by `coreLanguage` |
| 0x140216e70 | `Fleet_FindSevastopol` | find the ship named "Sevastopol" in the fleet list |
| 0x140217370 | `Roster_CollectPartsClearFlag111` | collect live parts of every body in a roster, clear +0x111 |
| 0x14021aa50 | `Gfx_CenteredPosition` | centred position from an object's extents at +0x218/+0x21c |
| 0x14021ae20 | `Gfx_PositionWithExtents` | position + extents + signed offsets |
| 0x140220740 | `Math_LinesIntersect` | 2-D segment intersection test |
| 0x140222040 | `Ship_ClampPartsToLevel` | clamp top-level parts to the level bounds |
| 0x140222160 | `Ship_ClampPartsAndVelocity` | clamp parts and mirror their velocity on the bounds |
| 0x1402224f0 | `Global_DestroyObject` | destroy the object in global 0x1403c0d40 via vtable +0x48 |
| 0x140223ef0 | `Hud_CloseLandMode` | delete the `LANDMODE_`/`SHIPDESC_MAIN`/`HIRE_FUNDS` widgets |
| 0x14022a670 | `Camera_SetTargetScreenPos` | write `TARGET_SCREEN_X_/Y_` |
| 0x14022bc40 | `Math_PointInRect` | axis-aligned point-in-rectangle test |
| 0x14022bc90 | `Body_GetMountWorldPos` | rotated world position of a point on a body (+0xf8 offset) |
| 0x14022bea0 | `Ship_IsGunAimedAt` | any gun part (state +0xd0 == 1) aimed at an angle |
| 0x14022c010 | `Ship_CanFireAt` | `Ship_IsGunAimedAt` with the flag-0x40 and long-range checks |
| 0x140232e30 | `Shop_PlayAmmoSelectSounds` | shop click sounds per ammo entry |
| 0x140233110 | `Roster_GetBounds` | bounding box of a roster of bodies (`Frame_GetOrientedSize`) |
| 0x140246800 | `BattleHud_DrawRetreatStrips` | draw the `retreat_strips` arrows along the screen edges |
| 0x140243bf0 | `Hud_DrawWorldBarFrame` | filled partial bar plus outline |
| 0x140249500 | `Gfx_DrawWorldRect` | rectangle outline from four world lines |
| 0x14024a380 | `Gfx_DrawWorldCross` | X/cross marker |
| 0x14024bf40 | `Roster_ClearBodyFlag220` | clear +0x220 on every Body of a roster |
| 0x14024c0b0 | `Player_ClearShipControls` | zero the fire/bomb/flare bytes +0xbbc..+0xbc0 |
| 0x14024f270 | `Sound_SetBodyVolume` | set a body's looping sound volume from a stat value |
| 0x140251c60 | `StreamBuf_SeekOff` | `std::streambuf`-style relative seek |
| 0x140251dc0 | `StreamBuf_SeekPos` | `std::streambuf`-style absolute seek |
| 0x140264e00 | `Shipyard_SpawnShip` | shipyard placement: copy, sfx, state 3, full fuel |
| 0x140268a10 | `Sound_FreeFlaggedAudio` | release the audio objects flagged for deletion |
| 0x14026aeb0 | `RbTree_Rebalance` | red-black fix-up/rotation from a node |
| 0x14026dfa0 | `Dialog_DrawStatsRows` | draw the `DIALOG_STATS` rows at fixed offsets |
| 0x1402714e0 | `Battle_UpdateArcadeHangarBackground` | switch the arcade background to type 0x14 |
| 0x1402757f0 | `Battle_UpdateArcadeLaunchBackground` | switch the arcade background to 0x1e while launching |
| 0x14027e600 | `Roster_PruneEmpty` | drop roster links with a null node or state 0 |
| 0x14027fb00 | `List_ActivateIndex` | activate list element by index (vtable +0x50) |
| 0x14027fc10 | `Node_NotifyChildren98` | clear +0xec and call child vtable +0x98 |
| 0x140280010 | `Node_ChildCallB0` | broadcast vtable +0xb0 to children |
| 0x140280100 | `Node_ChildCallD8` | broadcast vtable +0xd8 to children |
| 0x1402803e0 | `Node_ChildCallC0` | broadcast vtable +0xc0 to children |
| 0x140280450 | `Node_ChildCall150` | broadcast vtable +0x150 to children |
| 0x1402805d0 | `Node_KillSelf` | kill via vtable +0x40(this,1) (matches the `structures.md` kill chain) |
| 0x140281490 | `Node_ChildCallA0` | broadcast vtable +0xa0 to children |
| 0x1402842f0 | `PhysicTask_Destructor` | `PhysicTaskSingleton` destructor |
| 0x1402869d0 | `PreTask_Destructor` | `PreTaskSingleton` destructor |
| 0x140287f50 | `List_MergeSortByUint` | merge sort of a link list by the qword at node+0x18 |
| 0x1402884c0 | `Array_CopyConstruct50` | copy a range of 0x50-byte objects into raw storage |

## Shop / profile / captain / generic containers (0x14028xxxx–0x1402ACxxx)

| addr | new name | description |
|---|---|---|
| 0x1402879c0 | `Array_InsertDefault80` | insert a default captain-like 0x50-byte element |
| 0x140287e00 | `Array_Resize80` | resize a 0x50-stride vector |
| 0x14028ae40 | `SingletonPM_Destructor` | PM singleton destructor |
| 0x14028ae90 | `Property_DestructorDerived1` | Property-derived destructor, vtable 0x140373730 |
| 0x14028b010 | `NPCInfo_Destructor` | destructor that runs 0x140289d20 |
| 0x14028b050 | `Property_DestructorDerived2` | Property-derived destructor, vtable 0x140373688 |
| 0x14028b300 | `Array_DestroyRange80` | destroy a range of 0x50-byte elements |
| 0x14028b360 | `Array_InitEmptyStrings` | default-init an array of 0x50-byte string holders |
| 0x14028b960 | `NPC_ConstructRecord` | allocate 0x158 and construct an NPC |
| 0x14028c430 | `List_FindValueByKey` | value for a key in a key/value list |
| 0x14028d730 | `Ammo_GetRecord` | `AMMO_LIST_BEGIN + id*0x188` |
| 0x140292240 | `Fleet_CountActiveShips` | count player creatures with mode > 1 and +0x248 != 0 |
| 0x1402922a0 | `Captain_PickByTimeThreshold` | lowest-index captain whose time threshold is reached |
| 0x140292450 | `Captain_GetMaxIndex` | max captain +0x4c, clamped to the time table |
| 0x140292c10 | `Profile_FindShipByName` | ship lookup by name (+0xc8) in profile +0x1f8 |
| 0x140292ce0 | `Profile_FindCreatureByName` | creature lookup by name in profile +0x210 |
| 0x140293470 | `Profile_Constructor` | default profile ctor ("Profile", version 3, empty slots) |
| 0x140295280 | `NPC_GetRank` | `floor(value/3)` |
| 0x1402a7f60 | — | (skipped) 11 KB profile/campaign pass |
| 0x1402a8760 | — | (skipped) 4 KB fleet/aircraft pass |
| 0x1402a9090 | — | (skipped) 3.8 KB `PLANE_LOADOUTS` assignment pass |
| 0x1402ab050 | `Shop_TransferItemForLocation` | `TransferShopItem` on location+0x348 or `GlobalNodeElectricBoogaloo` |
| 0x1402ab9f0 | `Perf_GetFps` | reciprocal of the mean frame time (µs) |
| 0x1402aba30 | `Perf_SumFrameTimes` | sum the 100-slot frame-time ring buffer |
| 0x1402abd10 | `Perf_GetFrameTimeSeconds` | one sample / 1e6 |
| 0x1402abd50 | `Perf_GetFpsForOffset` | reciprocal of one offset sample |
| 0x1402abda0 | `Perf_LogGraphicsInfo` | log a graphics-info line |
| 0x1402ac2b0 | `NPC_DestroyRange` | destroy a 0x50-stride range |
| 0x1402ac5c0 | `List_InitSentinel` | empty circular list with a 0x28-byte sentinel |
| 0x1402ac5f0 | `NPC_DestroyList` | destroy every record of an NPC vector |
| 0x1402ac630 | `NPC_ReleaseIteratorRange` | destroy an NPC iterator range |
| 0x1402ac6f0 | `List_ClearAndFree` | free all nodes and reset the list |
| 0x1402ac7c0 | `Fleet_GetFuelFraction` | +0x498/+0x4a0 |
| 0x1402ac7f0 | `Array_Insert8` | insert one qword into a pointer vector |
| 0x1402ac8a0 | `Check_Field168IsZero` | `+0x168 == 0` |
| 0x1402ac930 | `Array_PushCaptain` | append a default 0x50-byte captain |
| 0x1402d44b0 | `Roster_PruneOutsideLevelBounds` | remove links outside the level y bounds and count them on map missile +0x248 |
| 0x1402d92c0 | `Fleet_ConsumeLaunchFuel` | spend fleet fuel for launch-ready missiles |
| 0x1402dd070 | `Body_FindNearestSlotIndex` | index of the slot child nearest the body |
| 0x1402dd180 | `Body_GetSlotWorldPos` | slot world position with master transform |

## HUD marker / draw primitives (0x1402DDxxx–0x1402EAxxx)

| addr | new name | description |
|---|---|---|
| 0x1402dd370 | `Hud_DrawSlotPin` | draw the pin/slave sprite of a slot at its transformed position |
| 0x1402dedd0 | `Hud_MarkerCheckChildFlag` | test a marker child's +0x168 against a mode |
| 0x1402e08b0 | `Hud_DrawChildMarker` | colour a child marker and draw its sprite |
| 0x1402e0a20 | `Hud_DrawChildMarkerFiltered` | as above with a child-state filter |
| 0x1402e0bd0 | `Hud_DrawSpriteAt` | HGE sprite draw at a computed position |
| 0x1402e0cf0 | `Hud_DrawQueuedSprite` | draw a queued sprite descriptor |
| 0x1402e1140 | `Hud_MarkerType1Render` | type-1 marker update (owner vtable +0x238) |
| 0x1402e1190 | `Hud_MarkerType4Render` | type-4 marker update for class 0x4000f (vtable +0x2c8) |
| 0x1402e11f0 | `Hud_MarkerType2Render` | type-2 marker child sprite draw |
| 0x1402e1f50 | `Hud_MarkerGetScreenPos` | copy marker screen position into the HUD globals |
| 0x1402e2000 | `Hud_MarkerSetColor` | set marker + all child slot colours |
| 0x1402e2170 | `Hud_MarkerInitType1` | type-1 marker ctor |
| 0x1402e2190 | `Hud_MarkerInitType4` | type-4 marker ctor |
| 0x1402e21b0 | `Hud_MarkerSetTextFields` | set the marker text/scale fields |
| 0x1402e21e0 | `Hud_MarkerInitType2` | type-2 marker ctor |
| 0x1402e2d00 | `Sound_StopAllInTable` | stop every sound in the global audio slot tables |
| 0x1402e2da0 | `Camera_CenterOnPlayerFleet` | average the player creature positions and place the camera |
| 0x1402e4910 | `Sound_IsFinished` | report whether a sound handle is still playing |
| 0x1402e5620 | `Array_Push32` | append a 0x20-byte element |
| 0x1402e6050 | `Array_Push40` | append a 0x28-byte element |
| 0x1402e6220 | `Sort_Median3Vec2` | median-of-three for the Vec2 quicksort |
| 0x1402e63f0 | `Sort_PartitionVec2` | partition for the Vec2 quicksort |
| 0x1402e66e0 | `Array_Resize32` | resize a 0x20-stride vector |
| 0x1402e69c0 | `Array_Resize40` | resize a 0x28-stride vector |
| 0x1402e6e20 | `Array_MoveConstruct56` | move a range of 0x38-byte elements |
| 0x1402e6eb0 | `Array_Copy40` | copy a 0x28-stride vector plus header |
| 0x1402ea8f0 | `Array_DestroyRange24` | destroy a range of 0x18-byte elements |
| 0x1402ee080 | `Array_FreeStride38` | free a 0x38-stride array block |

## Skipped / open (43 functions)

Reasons: `> 0x2000` bytes and not read fully, or behaviour visible but the
semantic role not proven. These are still `FUN_*`.

* **Large, not read (skip per method)**: `0x1402038e0`, `0x140205ae0`,
  `0x140206060`, `0x140206950`, `0x1402077c0`, `0x1402114a0`, `0x140211e60`,
  `0x14021cf40` (70 KB), `0x14022ad00`, `0x140245180` (27 KB),
  `0x140247850`, `0x14024d960` (15 KB), `0x140256a90`, `0x140263700`,
  `0x14028a980`, `0x14028bf80`, `0x1402943f0` (21 KB), `0x140295500` (31 KB),
  `0x140296530` (15 KB), `0x140297100` (14 KB), `0x14029b3e0` (20 KB),
  `0x1402a7f60`, `0x1402a8760`, `0x1402a9090`, `0x1402da8f0`,
  `0x1402f5410`.
* `0x1402130b0` / `0x140213fc0` — get-or-create singleton at
  `DAT_143a13b08` with a status int at +0x3cc; the two differ only in the
  initial/resume status value, and the owning class is not proven. Names would
  be `<Class>_GetOrCreate*`.
* `0x140216f00` — copies `+0x15d0` into `+0xf8` on fleet ships and sorts the
  list; `+0x15d0` is unknown, so the name would be a guess.
* `0x14021b110` — resolves the player creature, reallocates a vector, calls
  vtable +0x50; role unclear.
* `0x14021b240` — proximity query over the `0x143faa4c0` cell table (1e4
  stride). The cell layout is not documented.
* `0x14021fdb0` — reads the global `DAT_143a13a78` and forwards to a duplicated
  chunk of `Player_SendThrustCommands`; the `rep_` target makes the name
  unreliable.
* `0x140220620` — angle wrap/compare (`floor`, 2π wrap). Likely a piece of an
  arc/cone test; the return value is not a single boolean.
* `0x140224ec0` — scene reset + seria load, 4.5 KB, not read.
* `0x140232830`, `0x140233490` — pre-combat card layout maths (already listed
  as open by batch 2), unchanged.
* `0x14022bea0`/`0x14022c010` — **renamed**; note the gun-aim semantics are
  inferred from `+0xd0 == 1` child state, worth a second look.
* `0x1402410b0` — copies a string into `DAT_143a13a78`; that global is also
  read as an object in `0x14021fdb0`, so its type is ambiguous here.
* `0x140268a30` — string repeat/append loop with a confusing `memcmp` return
  use; not trusted.
* `0x140269d00` — state machine on a `0x65`/`0x67` move command and a `100`
  entry push; the command ids are not decoded.
* `0x14028b340`, `0x140292820` — argument-shuffling wrappers around a `rep_`
  free; no behaviour of their own.
* `0x1402d3c10` — computes creature bounds and forwards to a duplicated chunk
  inside `Player_SendThrustCommands` (`rep_1402a9430`); the real callee is not
  identifiable from the `rep_` label.
* `0x1402d5140` — checks `GlobalNode_` vtable +0x80/+0x90 and
  `GlobalNodeElectricBoogaloo` +0x80 then forwards; looks like an
  "all tasks done / may leave scene" guard but the forwarded callee is a `rep_`
  chunk, so left unnamed.
* `0x1402f3d20` — **renamed** `MapMode_SelectMissionShip`; the mission-ship
  pointer flow is only partly read (4 KB).
