# Ghidra sweep, batch 4 agent 3 — `0x140000000–0x14006FFFF`

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Range started with 343 unnamed functions (99 `FUN_*` + 244 `rep_*`) out of 699
in range. **124 functions renamed, every one plated.** No `save_program`, tags
or commits were issued (the user owns the check-in).

The range is the C++ static-initialisation / CRT startup block. Method:

1. List every function in range that calls `atexit` — that isolates the
   per-global static initialisers, which are the bulk of the range.
2. For each initialiser, take the global it *writes* (not the `atexit`
   argument and not the RTTI/vtable constants in `0x140334xxx`) and look at
   which named functions reference that global. The referencing function names
   the subsystem, so the initialiser gets `InitGlobal_<Subsystem>Link` /
   `...Array` / `...ListHead`.
3. Where a global has no external reference at all (nothing named touches it
   yet) the fallback `InitGlobal_Container_<global address>` is used, as
   agreed on the blackboard. Those are the 21 entries with a hex address in
   the name; they are honest placeholders, not guesses.
4. MSVC RTTI (`vtable[-1]` -> CompleteObjectLocator -> TypeDescriptor -> name)
   was used to name the deleting destructors, following the batch-3 recipe.
   Note the pTypeDescriptor RVA is relative to the *image base*, not to the
   locator.

## Renames — static initialisers (90)

All of these are `void(void)` functions that build one global and register its
destructor with `atexit`. The third column is the global they build.

| addr | new name | global / role |
|---|---|---|
| 0x140001040 | `InitGlobal_LevelListHead` | 1403c6320, `ResetLevelListHeads` |
| 0x140001080 | `InitGlobal_AircraftFormationMapArray` | 1403c6380, 4 `std::map` headers |
| 0x1400010c0 | `InitGlobal_AircraftCraftMapArray` | 1403c6340, 4 `std::map` headers |
| 0x140001100 | `InitGlobal_PartPanelLink` | 1403eef70, `Body_BuildPartInfoPanel` |
| 0x140001190 | `InitGlobal_Container_1403ef0a8` | anonymous list sentinel |
| 0x1400011c0 | `InitGlobal_Container_1403ef0b8` | anonymous list sentinel |
| 0x1400013d0 | `InitGlobal_TimeLogEntryList` | 1403ef328, `writeTimeToLog?` |
| 0x140001500 | `InitGlobal_ShopAmountLink` | 1403ef480, `displayAmountFromShop?` |
| 0x140001550 | `InitGlobal_SeriaLibraryLink` | 1403ef4f0, `loadSeriaForLibraries?` |
| 0x140001680 | `InitGlobal_SliderStateLinks` | three sentinels, `Gui_HandleSliderChange` |
| 0x1400016d0 | `InitGlobal_SurvivorStateLinkA` | 1403ef440, `Battle_ApplySurvivorState` |
| 0x140001710 | `InitGlobal_SurvivorStateLinkB` | 1403ef400, same users |
| 0x140001790 | `InitGlobal_Container_1403ef598` | anonymous list sentinel |
| 0x1400017f0 | `InitGlobal_VideoTaskLink` | 1439e5fe8, `SomethingVideoTask` |
| 0x140001820 | `InitGlobal_ParticleLink` | 1439e5f88, `LoadParticle?` |
| 0x140001850 | `InitGlobal_SerializableSingletonLink` | 1439e5fd8 |
| 0x140001890 | `InitGlobal_TrailList` | 1439e5fc8, `Trail_*` |
| 0x140002bf0 | `InitGlobal_KeyBindingLink` | 1439e93a0, `SetDefaultKeyBindings` |
| 0x140002d30 | `InitGlobal_LinkPool1000` | 1439e9400, 1000 x `Link` |
| 0x140002db0 | `InitGlobal_Container_1439e9378` | anonymous list sentinel |
| 0x140002df0 | `InitGlobal_Container_1439e9368` | anonymous list sentinel |
| 0x140002ee0 | `InitGlobal_StringArray256` | 1439ef360, 256 `std::string` |
| 0x140002f40 | `InitGlobal_CombatLinkPool` | 143a1c260, 10 x `Link` |
| 0x140002f90 | `InitGlobal_Container_143a15a50` | anonymous, `App_ReloadSeria` |
| 0x1400030e0 | `InitGlobal_LogTextLink` | 143a13e48, `LocalFileReadAndUpdate` |
| 0x140003110 | `InitGlobal_KeyRebindLink` | 143a13e00, `Settings_ApplyKeyRebind` |
| 0x140003170 | `InitGlobal_ProfileFleetLink` | 143a13ea8, `UpdateStrategicFleet` |
| 0x1400031a0 | `InitGlobal_Container_143a15a08` | anonymous `Link` |
| 0x1400031d0 | `InitGlobal_ZoomLink` | 143a159d8, `UpdateZoom` |
| 0x140003200 | `InitGlobal_ProfileContainerLink` | 143a15948 |
| 0x140003230 | `InitGlobal_TraitMedalLink` | 143a15960, `givePlayerTraitMedals` |
| 0x140003260 | `InitGlobal_Container_143a15898` | anonymous `Link` |
| 0x140003290 | `InitGlobal_RadioBackgroundLink` | 143a159a8 |
| 0x140003330 | `InitGlobal_GuiElementLink` | 143a13ac8, `FindGuiElement` |
| 0x140003360 | `InitGlobal_LostShipLink` | 143a13c90, `RemoveLostAIShip` |
| 0x1400033e0 | `InitGlobal_Container_143a15ae8` | anonymous `Link` |
| 0x140003430 | `InitGlobal_Container_143a13c08` | anonymous `Link` |
| 0x140003460 | `InitGlobal_Container_143a13ab0` | anonymous `Link` |
| 0x140003490 | `InitGlobal_GraphicsBufferA` | 143a13ca0, per-row float-pair buffer |
| 0x140003610 | `InitGlobal_LocalizationLink` | 143a13dd8, `Localization_FindEntry` |
| 0x140003650 | `InitGlobal_AmmoLink` | 143a15a60, `AircraftLogic_SetState` |
| 0x140003690 | `InitGlobal_ShipCardLink` | 143a1c220, `displayShipCards` |
| 0x140003700 | `InitGlobal_ChnVectorPairA` | 143a157f0, 2 x `vector<CHN*>` |
| 0x140003760 | `InitGlobal_ChnVectorPairB` | 143a15838, 2 x `vector<CHN*>` |
| 0x1400037e0 | `InitGlobal_UiElementLinks` | 143a1c3a0..3d8, six sentinels |
| 0x140003860 | `InitGlobal_HudElementLinks` | 1403c1470..1668 sentinel block |
| 0x140003a50 | `InitGlobal_Container_143a13af0` | anonymous list sentinel |
| 0x140003ab0 | `InitGlobal_BattleBackgroundLink` | 143a159f0 |
| 0x140003ae0 | `InitGlobal_BattleBackgroundLinkB` | 143a13c78 |
| 0x140003b10 | `InitGlobal_Container_143a1c230` | anonymous `Link` |
| 0x140003b50 | `InitGlobal_Container_143a13b00` | anonymous `Link` |
| 0x140003b80 | `InitGlobal_IRSTLink` | 143a13e78, `handleIRST?` |
| 0x140003bb0 | `InitGlobal_IRSTLinkB` | 143a13b60, `handleIRST?` |
| 0x140003be0 | `InitGlobal_LinkArray10` | 143a13cd0, 10 x `Link` |
| 0x140003c30 | `InitGlobal_LandingFrameLink` | 143a13bc8, `buildLandingFrame` |
| 0x140003c60 | `InitGlobal_RadarBackgroundLink` | 143a13b48 |
| 0x140003c90 | `InitGlobal_Container_143a13b98` | anonymous list sentinel |
| 0x140003cc0 | `InitGlobal_PrecombatButtonLink` | 143a15900 |
| 0x140003cf0 | `InitGlobal_Container_143a13c20` | anonymous list sentinel |
| 0x140003d30 | `InitGlobal_Container_143a13c38` | anonymous list sentinel |
| 0x140003d60 | `InitGlobal_FleetMapGuiLink` | 143a13e90 |
| 0x140003d90 | `InitGlobal_FleetMapGuiLinkB` | 143a13e60 |
| 0x140003dc0 | `InitGlobal_MissileTypeLinkArray` | 143a15a70, 4 x `Link` |
| 0x140003e00 | `InitGlobal_ClickFuncLink` | 143a13c60, `!ClickFunc` |
| 0x140003e60 | `InitGlobal_VictoryBadgeLink` | 143a1c248 |
| 0x140003e90 | `InitGlobal_Container_143a13bf8` | anonymous list sentinel |
| 0x140003ed0 | `InitGlobal_AmmoDefinitionArray` | 143a13ef0, 100 x 0x40 |
| 0x140003f10 | `InitGlobal_SecondaryMapModeLink` | 143a13e18 |
| 0x140003f40 | `InitGlobal_MissileTypeLinkB` | 143a15ad0 |
| 0x140003f80 | `InitGlobal_VictoryBadgeLinkB` | 143a13b18 |
| 0x140003fb0 | `InitGlobal_GraphicsBufferB` | 143a13ed8, twin of A |
| 0x140004100 | `InitGlobal_Container_143a2ddf8` | anonymous list sentinel |
| 0x140004130 | `InitGlobal_DeadNodeList` | 143a2de10, `CollectDeadNodes` |
| 0x140004160 | `InitGlobal_PartStatsIndexMap` | 143a33c08, `BuildStatsNameIndexMap` |
| 0x1400041b0 | `InitGlobal_PhysicTaskLink` | 143a33c48, `SomethingPhysicTask` |
| 0x140004210 | `InitGlobal_BigRecordPool` | 143faa680, 2,800,000 x 0x18 (~64 MB) |
| 0x1400042b0 | `InitGlobal_TadsDamageEntryList` | 147fc6898 |
| 0x1400042e0 | `InitGlobal_ExplosionLink` | 147fc68a8, `Body_Explode` |
| 0x140004310 | `InitGlobal_Container_147fc6db8` | anonymous list sentinel |
| 0x140004340 | `InitGlobal_BattleStarList` | 147fc7500, `afterBattleStars??` |
| 0x140004370 | `InitGlobal_PrecombatSlotLists` | 147fc7510, 4 sentinels |
| 0x1400043b0 | `InitGlobal_CombatSceneLink` | 147fc73b0, `SCR_COMBAT*` |
| 0x1400043e0 | `InitGlobal_CombatSceneLinkB` | 147fc75a8 |
| 0x140004420 | `InitGlobal_AiTargetLink` | 147fc7550, `AiShipTick` |
| 0x1400044a0 | `InitGlobal_SkirmishSpawnArray` | 147fc75d0 |
| 0x140004510 | `InitGlobal_LevelNameStringsA` | 147fc73f0, 2 `std::string` |
| 0x140004560 | `InitGlobal_LevelNameStringsB` | 147fc74c0, 2 `std::string` |
| 0x1400045e0 | `InitGlobal_PrecombatBodyArray` | 147fc7430, 4 x 0x18 |
| 0x140004620 | `InitGlobal_SfxLink` | 147fc76a0, `playSFXSound?` |
| 0x1400046e0 | `InitGlobal_ChnVectorPool` | 14801dd00, 100 `vector<CHN*>` |

Three of these are worth flagging:

* `InitGlobal_BigRecordPool` calls `_eh_vector_constructor_iterator` with
  **2,800,000 elements of 0x18 bytes** — a ~64 MB startup allocation.
* `InitGlobal_GraphicsBufferA/B` build a `graphicsFrameHeight`-sized array of
  float pairs initialised to `FLT_MAX` and hand it to the object constructor at
  `0x140195830` together with `graphicsFrameWidth`. Two parallel layers; the
  semantics beyond "graphics layer buffer" are not established.
* `InitGlobal_ChnVectorPool` is 100 default-constructed `vector<CHN*>` objects
  in a single 0x960-byte block, used by `Gui_FlushDrawList`.

## Renames — destructors (6)

| addr | new name | evidence |
|---|---|---|
| 0x140018ba0 | `b2Shape_ScalarDeletingDestructorA` | RTTI `.?AVb2Shape@@`, vtable 0x140352998 |
| 0x140018bd0 | `b2Shape_ScalarDeletingDestructorB` | ICF twin of the above |
| 0x14005e6b0 | `Captain_Destructor` | vtable 0x140354bf8 (`.?AVCaptain@@`), tail-jump to 0x14018f7d0 |
| 0x14005e560 | `Captain_DestructorSubobject8` | identical body operating on `this+8` |
| 0x140060010 | `ObjectProperty_Captain_ScalarDeletingDestructor` | RTTI `.?AV?$ObjectProperty@VCaptain@@@@` |
| 0x140060180 | `ListLinksProperty_ScalarDeletingDestructor` | RTTI `.?AVListLinksProperty@@` |

The two `Captain_*` destructors are thunks: they only overwrite the vptr and
jump to the shared destructor at `0x14018f7d0`. That target is currently
mis-named `rep_140181ca0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free`; it is really a
base/container destructor (it walks and frees a linked list, then frees
`this`) and should be renamed in a later pass.

## Renames — helpers (28)

| addr | new name | what it is |
|---|---|---|
| 0x140047f70 | `Part_ScaleValueByAmountRatio` | `GetValue() * (amount / field2CC)`, 0 when equal |
| 0x140048050 | `Body_CopyWorldPositionTo` | +0x210 copy + vtable slot +0xe8 |
| 0x14004aee0 | `Vector8_PushBack` | `vector<void*>` push_back, inline path |
| 0x14004af00 | `Vector8_PushBackRealloc` | same, grow through `vec_realloc_insert` |
| 0x14004bb10 | `ObjectArray_DeleteAll` | deleting-dtor loop over the +0x8c0 vector |
| 0x14004c7f0 | `Creature_DebugDrawDetails` | helper of `Creature_DebugDrawOverlay` |
| 0x14004dfa0 | `Creature_DrawLinkSprites` | one sprite per +0x998 link, alpha from radius |
| 0x14004e0d0 | `Hud_DrawSlotPinsForChildren` | mask-filtered `Hud_DrawSlotPin` loop |
| 0x14004eab0 | `RenderMesh_ScaleAndFlip` | scale vertices, reverse winding on sign flip |
| 0x140052070 | `Gui_DrawScaledShape` | body-mesh wrapper, 4 sides at cos45 |
| 0x140053df0 | `Body_CollectNeighbourParts` | recursive face-adjacency collect |
| 0x140054d90 | `BodyNode_ApplyToChildrenIfReady` | vtable +0x78 guard, then +0x1d8 + children |
| 0x140056850 | `ThrowOutOfRangeException` | `MSVC _Xout_of_range` |
| 0x140058840 | `SortPointersByInt88C` | median-of-3 introsort, key int +0x88c |
| 0x140058a40 | `SortPointersByFloat88` | median-of-3 introsort, key float +0x88 |
| 0x140058c60 | `SortElem32ByInt48` | heap build, 0x20-byte records, key int +0x48 |
| 0x140059120 | `SortElem32SwapByFields` | less-than + swap for 0x20-byte records |
| 0x140059a60 | `SortElem16ByFloat88` | quicksort, 0x10 stride, key float +0x88 |
| 0x14005a0b0 | `SortElem32_Introsort` | introsort driver, 0x20-byte records |
| 0x14005a8c0 | `SortElem64_SiftDown` | sift-down, 0x40-byte records, key int +0x48 |
| 0x14005acf0 | `SortInsertionByInt88C` | insertion fallback, key int +0x88c |
| 0x14005b6e0 | `SortInsertionByFloat88` | insertion fallback, key float +0x88 |
| 0x14005c3c0 | `Object_MoveRange30` | move-construct a range of 0x30-byte objects |
| 0x1400608d0 | `DurationCursor_Advance` | consumes entries of `DAT_1403ef0f8..0x100` |
| 0x140060a20 | `Creature_CallLinkedSlot1A0` | forwards an argument to the linked creature |
| 0x140061e40 | `Gui_DestroyElementAt30` | destroy + null the pointer at +0x30 |
| 0x1400671d0 | `Precombat_FormatStatRowText` | `Precombat_BuildStatRows` text builder |
| 0x14006bb80 | `Creature_ResetChildAlpha` | sets +0x80c = 1.0 on child entries |

The `Sort*` family (`0x140058840`–`0x14005b6e0`) is one std::sort/introsort
implementation instantiated over three element layouts (8-byte pointers keyed
by an int at +0x88c, 8-byte pointers keyed by a float at +0x88, and 0x20/0x40
byte records). Names describe the layout and key, not a guessed C++ type.

## Boilerplate left in range (no action)

* **ICF-merged replicas — 207 of the remaining `rep_*`.** Every one is named
  `rep_<canonical>_<target>` by the server and points either at a CRT/DLL
  import (`free`, `memcpy`, `memmove`, `memcmp`, `memset`, `sqrtf`, `atan2f`,
  `pow`, `_fdclass`, `_invalid_parameter_noinfo_noreturn`,
  `__std_exception_destroy`, `_Xout_of_range`, `_CxxThrowException`) or at an
  already-named game function (e.g. `rep_140004e70_GetStats`,
  `rep_140004060_deallocateString?`). They are compiler output; naming each
  copy would add noise without information.
* **CRT startup / exception plumbing:** `FUN_140019990` (forwards to
  `_invalid_parameter_noinfo_noreturn`), `FUN_1400199b0` (forwards to `free`),
  `FUN_1400199d0` (identity function used as a no-op deleter by the throw
  paths), `FUN_140055f20` (one-instruction stub reached from `_set_app_type`),
  `FUN_140017d10` (22-byte virtual forwarder).
* **`rep_1400016c0_`eh_vector_destructor_iterator'`** at `0x1400018f0`
  (4818 bytes). The replica target `0x1400016c0` is *inside*
  `InitGlobal_SliderStateLinks`, so the name is bogus. The body is a real
  global-init routine (copies strings, allocates objects, registers `atexit`)
  referenced from data at `0x140360xxx`; it needs a dedicated read. Left as is.

## Skipped — needs more context

| addr | size | why |
|---|---|---|
| 0x14000ad80 | 0x14 | `*(int*)(this+0x190) != 0`, called once from `Projectile_DetonateOnImpulse` inside a target-state test; the field meaning is unclear |
| 0x140019310 | 0xa0 | vtable +0x290/+0x280 state switch plus `_Xtime_get_ticks`; no callers (vtable slot only) |
| 0x140019380 | 0x30 | counterpart of the above with `Frame_ResetCounter`; no callers |
| 0x1400211a0 | 0x7c0 | large GUI text builder (`{max=2000}` tag, `GetStats`, `tutorialForPartName`); no xrefs recorded, so the owning vtable slot is unknown |
| 0x140027f90 | 0xa0 | part loop calling a `MakeGlobal?` helper when `part+0x58 != 0`; callers are `memcmp_editor`/`?BuyPartShop`, semantics unclear |
| 0x1400458c0 | 0x1a00 | large frame/part placement routine (`RbTree_InsertLinkByFloatPair`, `__RTDynamicCast`, `Body_IsMountedOrPaired`); needs a full read |
| 0x140049cd0 | 0x20 | two-field test (`+0x2e8` int, `+0x248` float) used from `creatureLogic`, `!ClickFunc`; field roles unknown |

## Counts

* renamed: **124** (90 static initialisers, 6 destructors, 28 helpers)
* `FUN_*` left in range: **12** (5 pure CRT boilerplate, 7 listed above)
* `rep_*` left in range: **207** (ICF replicas of CRTs/named functions)
