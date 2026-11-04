# Ghidra sweep 2026-10-29 — agent 5 (0x140200000–0x1402FFFFF)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Range: AI, battle/fleet management, scenes (`SomethingWithLevelSerias` ticks),
shipworks/precombat. Names follow `<Subsystem>_<Verb><Object>`; scene ticks keep
the `SCR_<SCENE>` name from the docs, with a `_<role>` suffix for helpers.

Scene-branch map recovered this pass (branch test = address of the `LEA RDX` of
the scene string inside `SomethingWithLevelSerias`):

| scene | branch test | tick call sites |
|---|---|---|
| `SCR_RUINS` | 0x1402c1f4b | |
| `SCR_COMBAT` | 0x1402c24d9 | 0x1402c254c, 0x1402c2862, 0x1402c3237 |
| `SCR_COMBAT_SKIRMISH` | 0x1402c3c78 | 0x1402c40b9, 0x1402c4217 |
| `SCR_COMBAT_SKIRMISH_PVP` | 0x1402c44c4 | 0x1402c4745, 0x1402c474f, 0x1402c478e |
| `SCR_COMBAT_TEST` | 0x1402c4848 | |
| `SCR_MISSILE` | 0x1402c4baf | 0x1402c4dfc, 0x1402c50f1 |
| `SCR_CRAFTS_VS_MISSILE` | 0x1402c510c | 0x1402c515e |
| `SCR_BOMBERS` | 0x1402c52ee | 0x1402c552e, 0x1402c5540, 0x1402c5340 |
| `SCR_CRAFTS_VS_CRAFTS` | 0x1402c5890 | 0x1402c58db, 0x1402c58ed |
| `SCR_CREDITS` | 0x1402c5a86 | |

The per-frame state counter is `DAT_147fc6fc4`; state `0x61` (97) is the
"leave the scene" state and state `1` is usually the scene setup.

## Renames

| addr | new name | description |
|---|---|---|
| 0x1402ca2b0 | `SCR_BOMBERS` | SCR_BOMBERS scene setup: clears the reserve/loadout lists, splits the planes of the map craft into armed/unarmed vectors, arms them with `stateSelectorAircraft_` 2/3 and starts the strike (`0x140267700`) |
| 0x1402ca070 | `SCR_BOMBERS_Tick` | per-frame tick of the bombers scene: prunes dead planes from the reserve, puts idle planes into state 5, checks the player is within 1500 units and counts the redeploy timer down; returns "scene still running" |
| 0x1402cdaf0 | `SCR_COMBAT` | SCR_COMBAT scene setup: resets the aircraft selector and the spawn tree, deploys `Profile.default` ships from the reserve (or the arcade attacker) and spawns the ground defences |
| 0x1402cd1f0 | `SCR_COMBAT_TickWaveSpawner` | SCR_COMBAT wave/end supervisor: evac-volume moves, combat score bookkeeping, wave timers, spawns the next wave from the spawner and sets the battle result (`DAT_147fc7004`) |
| 0x1402ce060 | `SCR_COMBAT_ReturnToMap` | SCR_COMBAT return-to-map handler: returns the surviving ships and their gun ammo to their fleets, removes the AA defences, selects the fleet on the map and fires the post-battle triggers |
| 0x1402cd9a0 | `Battle_PruneRoster` | removes dead/detached ships (and state-7 ships outside a scripted scene) from a 0x18-stride roster vector; returns the number removed |
| 0x1402cc7e0 | `SCR_COMBAT_SKIRMISH_TickRedeploy` | skirmish per-frame redeploy: moves ships that reached the retreat point out, redeploys from the reserve into the free control slots |
| 0x1402ce8f0 | `SCR_COMBAT_SKIRMISH_ReturnShips` | skirmish end: splits the two sides, returns ships, ammo and volumes to the map and appends the results to the profile vectors |
| 0x1402cce70 | `SCR_COMBAT_SKIRMISH_PVP_Tick` | PVP skirmish per-frame tick: retreat-point handling per control slot, prunes each slot's roster, cleans the container lists |
| 0x1402cdfb0 | `SCR_COMBAT_SKIRMISH_PVP` | PVP skirmish setup: resets the aircraft selector and the retreat point, clears every control slot and fills it with one ship per player from the spawner |
| 0x1402ceee0 | `SCR_COMBAT_SKIRMISH_PVP_ReturnShips` | PVP skirmish end: collects the surviving side-A/B properties, destroys the empty ones and returns the ships to their volumes |
| 0x1402cb6a0 | `MapCraft_ReturnChildrenToParent` | end of a craft-group scene: resets state 7, makes every child global, moves it back into the map volume, detaches the class-0x500 children and adds their count back to the parent map craft |
| 0x1402cf2a0 | `SCR_CRAFTS_VS_CRAFTS_CheckEnd` | prunes both craft rosters and reports whether one side has no armed plane left (scene over) |
| 0x1402cf4d0 | `SCR_CRAFTS_VS_CRAFTS` | SCR_CRAFTS_VS_CRAFTS setup: builds the loadout map from `PLANE_LOADOUTS`, splits planes into armed groups, calls `0x140267700` per group and starts the next level seria |
| 0x1402d1510 | `SCR_CRAFTS_VS_MISSILE_ReturnShips` | CRAFTS_VS_MISSILE end: detaches the class-0x500 planes, returns them to the carrier and adds the surviving count back to the map missile's `+0x248` |
| 0x1402d45c0 | `SCR_MISSILE_SpawnDefenders` | SCR_MISSILE state 1: sorts the defender fleet, spawns up to four ships, makes the first one the player's, defines the incoming missiles from side B[0] and assigns their targets |
| 0x1402d4f20 | `SCR_MISSILE_Teardown` | SCR_MISSILE exit: resets state 7, returns every spawned body to the map volume and frees the roster |
| 0x1402c9cb0 | `SCR_COMBAT_SpawnPlayerShip` | spawns one ship from a template list at a staggered arena position, sets it as the player's ship, picks its retreat point and computes its radius |

## Skipped / open

* `0x1402ca2b0` had a long first-pass plate comment; it is replaced by the
  short doc-style plate, the detail is preserved in
  `findings/plane-combat-modes-and-gunpods.md`.
* Not renamed yet in this range: AI helpers around 0x1402xx (see below), the
  shipworks/precombat GUI block, and most `rep_*` thunks.

### Second block: battle helpers, HUD, pre-combat, generic containers

| addr | new name | description |
|---|---|---|
| 0x140288250 | `List_MergeSortByDistanceToPoint` | recursive merge sort of a link list by distance from each object to a reference object |
| 0x140288080 | `List_MergeSortByStat154` | recursive merge sort of a link list by the creature stat at `+0x154` |
| 0x140220170 | `Side_IsSameId` | two integer side ids equal |
| 0x1402d4140 | `Landscape_MinSurfaceHeightInRange` | lowest terrain surface y overlapping an x interval (battle spawn height) |
| 0x1402d7110 | `Battle_SpawnQueuedShipForSlot` | pops one ship from a control slot's queue and spawns it at the level edge |
| 0x1402d9500 | `Precombat_SplitFleetIntoReserveLists` | pre-combat: split the player fleet into roster/reserve lists and fund gun reserves |
| 0x1402d9a70 | `Precombat_BuildSlotQueues` | pre-combat: rebuild the four per-slot ship queues from side A |
| 0x14026f990 | `Precombat_BuildAmmoSelectors` | pre-combat: rebuild the AMMO_SELECT GUI elements per player card |
| 0x1402692d0 | `Text_RightPadInteger` | right-pad an integer string to a fixed width |
| 0x140289be0 | `Array_DestroyRange50` | destroy a vector of 0x50-byte polymorphic objects |
| 0x140288400 | `Array_MoveConstruct50` | move-construct a range of 0x50-byte objects |
| 0x140288580 | `Math_PowInt` | `pow(double, int)` wrapper |
| 0x14029ae40 | `BattleHud_DrawBodyMarkers` | draw the class-mask sign sprite over every active body on the battle HUD |
| 0x1402952c0 | `Profile_PreloadPurge` | `PM::preload` purge of the loaded profile containers |
| 0x140251eb0 | `Camera_DeathCamFocus` | move the camera and zoom onto a ship that is dying |
| 0x140252af0 | `Hud_UpdatePlayerScreenPos` | copy the player escort position into the HUD target globals |
| 0x140253bf0 | `Sound_PlayShopAmbient` | start/stop the shipworks `amb_shop_1` ambient sound |
| 0x1402a7060 | `Vector_Resize50` | resize a vector of 0x50-byte elements |
| 0x1402a7150 | `Node_DetachChildrenToGlobal` | kill all children of a node and re-add them to the global node |
| 0x1402dee60 | `Array_DestroyObjectVector` | destroy a vector of owned polymorphic objects |
| 0x1402dd840 | `SoundTask_Destructor` | destructor of the sound task singleton |

## Skipped / open (examined, not renamed)

* `0x1402ce060` / `0x1402cd1f0` — both are reached from the `SCR_COMBAT`
  branch; the split between "return to map" and "wave spawner" is from
  behaviour, not from a read of the dispatcher's state values. Worth a second
  look if the combat state machine is ever mapped fully.
* `0x1402ca070` is reached at `0x1402c552e`, immediately after the
  `TUTORIAL_AAM_CRAFTS` handoff block and just before the `SCR_BOMBERS` state-1
  call. It prunes rosters and manages the wave timer; named `SCR_BOMBERS_Tick`
  on that placement, but it may in fact be the tutorial scene tick.
* `0x1402ce8f0` / `0x1402ceee0` / `0x1402d1510` all return ships to the map and
  differ only in which scene state list they read; the exact state numbers were
  not read.
* `0x1402879c0`, `0x140287e00`, `0x140289d20` — NPC/Profile constructors and
  destructors in the serialisation cluster; the class each one builds is not
  proven, so they were left alone.
* `0x140288080`/`0x140288250` use `+0x154` of a stat record indexed through
  `AMMO_LIST_BEGIN`; the field name is unknown.
* `0x1402d92c0`, `0x1402da8f0`, `0x140232830` — pre-combat card layout maths
  (craft distribution, spawn timers, escape-pod spread). Behaviour is visible
  but the output fields are not identified; left unnamed.
* `0x14024c8e0` clears a 0x148-qword level block and sets an initial
  `lvlRendezvous`; likely a level-reset helper but the caller was not read.
* `0x1402ab050` forwards to `TransferShopItem` for the current location (or the
  global node); the exact shop action is unread.
* HUD/GUI child-sprite block `0x1402dedd0`, `0x1402e0a20`, `0x1402e08b0`,
  `0x1402e0bd0`, `0x1402e0cf0` — they all index a child sprite through
  `element+0x8c0`, but which property each one sets was not read.
