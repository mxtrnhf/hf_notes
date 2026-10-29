# Ghidra sweep, batch 8 agent 3 — open `/EH` funclets

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: the 73 funclets still open after batch 7 in
`0x140336730–0x140350510` — 68 whose `.pdata` owner still carried a stale
`rep_*` label and the 5 recorded edge cases.

**7 owners proven and renamed; their 7 funclets named + plated. 66 remain open**
(61 with a function object at the owner address, 5 with no function object at
the funclet address). No `save_program`, no tags, no README/STATUS edits, no
commit, no non-funclet `rep_*` touched.

| | count |
|---|---|
| addrs in the 73-address scope | 73 |
| owners renamed (stale `rep_*` → real identity) | **7** |
| funclets named + plated this pass | **7** |
| still open | **66** |
| … owner has a function object but no proven identity | 61 |
| … no function object at the funclet address | 5 |

Program after the pass: every one of the 7 names is unique, each funclet has
the 5-line plate. Nothing else in the range was modified.

## 1. Owners renamed and funclets completed (7)

Each owner was `rep_*` at the moment of the rename; each funclet was `FUN_*`
(the two in block 13 did not exist as function objects in batch 7 either).
Evidence is from the owner body; the `.pdata` owner/member mapping is unchanged
from batch 6/7. The funclet's `sz=` (the sized operator delete operand) matches
the temporary allocated in the owner — an independent confirmation of the
owner↔funclet pair.

| funclet | new funclet name | owner renamed to | member | family | evidence from the owner body |
|---|---|---|---|---|---|
| `0x140343460` | `Fleet_CreateEscadraFromShips_EhCleanup_0x60` | `0x1401c7060` `rep_1401b4600_Escadra::Escadra` → **`Fleet_CreateEscadraFromShips`** | `0x60` | freeField | `New(0x618)` → `Escadra::Escadra`; `CopyString(escadra+0x19, name)`; iterates the caller's `vector<0x20 string>` and calls `renderShipPhoto__` per ship, adding each via `vfn+0x50`; then `Get_Profile()->tadsRecord`, `p+0x1cc`, `HGE->vfn+0x110`. Callers `Fleet_CreateRandomEscadra`, `Fleet_CreateRandomEscadraForSlot` (via `spawnTradeConvoy?`), `Endgame_BuildEscadra`, `Prologue_SpawnEventEscadra`, `mainDialogWithChoices`. Funclet `sz=0x618` = the Escadra temporary. |
| `0x140343ff0` | `Moral_BuildMiniFigPanel_EhCleanup_0x148` | `0x140202010` `rep_1401e7b50_GUI::GUI_2` → **`Moral_BuildMiniFigPanel`** | `0x148` | freeField | `New(0xe70)` → `GUI::GUI_2`; `SetBackground_("bio_ramka_moral")`, a loop of `SetBackground_("bio_point_mini")` (one per moral point), `rep_140063d80…("MORAL_MINIFIG", …, "dinpro_14_bold", "myriad_10")`, `CreateSpriteCreature`; sole caller `Moral_BuildStatsPanel`. Funclet `sz=0xe70` = the GUI temporary. |
| `0x14033d640` | `Escadra_AddIntelEntry_EhCleanup_0x38` | `0x1400eb460` `rep_1400e5de0_WriteToClientLog` → **`Escadra_AddIntelEntry`** | `0x38` | freeField | `New(0x1b8)` + `ISerializable::ISerializable` + `IntelVFTABLE` + `LinkVFTABLE`; searches/updates the Intel list at `this+0x1f8` (keyed by classname and `+0x2c`), inserts `New(0x18)` list nodes, copies the Intel fields, `CHECK ERROR` assert string names `Escadra.cpp:0x6d8/0x6d9`. Callers `CreateMapAircraftGroup`, `Escadra_WriteMemberLog`, `ReconcileMapAircraftGroupOwners`. Funclet `sz=0x1b8` = the Intel temporary. |
| `0x14033d500` | `Escadra_CopyFrom_EhCleanup_0x88` | `0x1400e5530` `rep_1400dfed0_CopyString` → **`Escadra_CopyFrom`** | `0x88` | freeField | Copies every Escadra field (`+0x298…+0x558`) from `param_2` into `param_1` (`ReassignLinkNode` for the link members, `CopyString`), and for each element of the source vector at `+0x550` creates `New(0x70)` → `ISerializable` + `PTR_LastPlayerPosData_ScalarDeletingDestructor_14035dfa0` + `CopyString("LastPlayerPosData")` + `code=0x100003` + `vfn->SomethingWithProperties`; ends with `CopyObject(p2+0x520)`, `AssignRandomId(…,1)`, `vfn+0x30`. Called from `Escadra`. Funclet `sz=0x70` = the LastPlayerPosData temporary. |
| `0x140338a10` | `Creature_AddLandingLights_EhCleanup_0xe0` | `0x140061000` `rep_14005eca0_PlayRadioSound?` → **`Creature_AddLandingLights`** | `0xe0` | freeField | Iterates `Creature_CollectExtremeParts`; per part `New(0xa40)` → `Body::Body_Constructor`, `CreateShell_`, `SetLink(body+0x16, creature)`, `PlayRadioSound_("landing_light", i, 0)` + `SetBackground_` with that sprite, sets `+0x3c4=0xd84`; bumps `creature+0x169c` by 4. Callers `SomethingWithLevelSerias`, `rep_1402454a0_New`. Funclet `sz=0xa40` = the Body temporary. |
| `0x14033ec50` | `Gui_CopyConstructor_EhCleanup_0x58` | `0x14012c280` `rep_140123550_New` → **`Gui_CopyConstructor`** | `0x58` | freeField | Copy-constructor of the 0xe70-byte GUI object: `copyOverBody`, then copies `+0xa80…+0xe68` (`CopyString` for each std::string member, `ReassignLinkNode` for each Link), clears the child pointer vector at `+0xc80` and re-creates it with `New(0x68)` → `SLink_Constructor` + `vec_realloc_insert`; copies the tail strings. Callers `GUI_1`, `List_ConstructorFromPrototype`, `Replica_ConstructorFromPrototype`, `Slider_ConstructorFromPrototype` (prototype cloning). Funclet `sz=0x68` = the SLink temporary. |
| `0x140339240` | `Shader_AddParam_EhCleanup_0x30` | `0x140087790` `rep_140082f40_New` → **`Shader_AddParam`** | `0x30` | freeField | `New(0x28)` → `ShaderParamVectorArrayNew_Constructor`, then appends the result to the shader's parameter-pointer vector at `+0x80` (`*p==end` ? `vec_realloc_insert(shader+0x80)` : store at `+0x88` and bump). Callers `ShaderLighting_Init`, `ShaderDeferringFarPrerendered_Init`. Funclet `sz=0x28` = the ShaderParam temporary. |

Plates use the batch-6/7 template with the owner's real name, the member, the
destroy operation and the temporary's type; last line: *“Owner and member
recovered from the `.pdata` RUNTIME_FUNCTION / FUNCINFO4 funclet table (sweep
b6 agent 1); owner identity proven from its body in sweep b8 agent 3.”*

## 2. Verification

* 7/7 renames: `status=success`, old name `rep_*`, new name not previously in
  the symbol table (checked with `search_functions` for `Fleet_`, `Moral_`,
  `Escadra_`, `Creature_Add`, `Gui_`, `Shader_Add`, `ShaderParam`; tool
  warnings were only the usual repo-style warnings about `_`/module prefix).
* 7/7 funclet renames + 7/7 plates written; live re-read of all 73 addresses:
  **7 named (all plated), 66 open, 0 named-without-plate**.
* 0 non-funclet functions touched. `0x14016bf00` (an owner, see §3) was left
  alone: it is a creation target, not in this job.

## 3. Still open — 66

Each row keeps the `.pdata`-derived owner and member. The owner's live label is
still `rep_*` (or `FUN_*` for the one edge case); per-address evidence strings
are in `funclet-ownership-2026-10-29.tsv`.

### V. Generic container/allocator helper (31)

These owners are MSVC container/array instantiations (or small wrappers over
them). Their bodies call only `New`/`free`/`memmove`/`memset`/
`std::_Xlength_error`-family helpers, `vectorTooLong`, `_Change_array`,
`AllocateArrayOf8Byte` etc., and carry no vftable store, no string and no
caller set that fixes the element type. The funclet destroys a local temporary
in such a helper, so naming would require inventing the template argument.
Examples: the six shader helpers `0x140089300`, `0x140089b90`, `0x14008ba20`,
`0x14008c5a0`, `0x140090fd0`, `0x14009b090` are byte-similar
`vector`-growth bodies whose only callers are `Shader*_Constructor` /
`Shader*_Init`; `0x1400127f0`, `0x1400128f0`, `0x140013160`,
`0x1402e5c70` are `vector<unsigned __int64>` `_Change_array` replicas;
`0x1402de080` copies an ISerializable field block (caller
`rep_1402b2620_ISerializable::ISerializable`); `0x1402e0d50` is a
`Vec2_TransformByMat2` wrapper. All recorded as unidentifiable, not guessed.

| funclet | owner | member | family |
|---|---|---|---|
| `0x140338110` | `0x140058270` | `0x80` | rethrow |
| `0x1403392f0` | `0x140089300` | `0x60` | rethrow |
| `0x140339370` | `0x140089b90` | `0x60` | rethrow |
| `0x140339430` | `0x14008ba20` | `0x60` | rethrow |
| `0x140339480` | `0x14008c5a0` | `0x60` | rethrow |
| `0x140339700` | `0x140090fd0` | `0x60` | rethrow |
| `0x1403399d0` | `0x14009b090` | `0x60` | rethrow |
| `0x14033c4d0` | `0x1400bb800` | `0x80` | rethrow |
| `0x14033cc80` | `0x1400df450` | `0x60` | rethrow |
| `0x14033cd50` | `0x1400dfde0` | `0x70` | rethrow |
| `0x14033e310` | `0x14011e440` | `0x60` | rethrow |
| `0x1403410f0` | `0x14016f6a0` | `0x80` | rethrow |
| `0x140341460` | `0x140183e00` | `0x60` | rethrow |
| `0x140341e10` | `0x140197510` | `0xa0` | rethrow |
| `0x140341ef0` | `0x1401986f0` | `0x70` | rethrow |
| `0x140341f50` | `0x140198ac0` | `0x60` | rethrow |
| `0x140341fb0` | `0x140198eb0` | `0x70` | rethrow |
| `0x140342030` | `0x1401993c0` | `0x80` | rethrow |
| `0x140342080` | `0x140199650` | `0x80` | rethrow |
| `0x1403421b0` | `0x14019a0f0` | `0xa0` | rethrow |
| `0x140342420` | `0x14019aeb0` | `0x80` | rethrow |
| `0x14034a310` | `0x1402c7c90` | `0x30` | rethrow |
| `0x14034a760` | `0x1402de080` | `0x48` | freeField |
| `0x14034a7a0` | `0x1402e0d50` | `0x58` | linkFree |
| `0x14034a900` | `0x1402e5c70` | `0x60` | rethrow |
| `0x14034a930` | `0x1402e5dd0` | `0x70` | rethrow |
| `0x1403368e0` | `0x1400dfa70` | `0x90` | freeField |
| `0x140336d90` | `0x1400128f0` | `0x50` | freeField |
| `0x140336dc0` | `0x140012a30` | `0x60` | freeField |
| `0x140336e30` | `0x140013160` | `0x80` | freeField |
| `0x140336f50` | `0x14016fa00` | `0x50` | freeField |

### X. FX spawner pair (2)

`0x140121c50` and `0x140122200` are two near-identical FX spawners
(`New(0x270)` → `CreateFX`, `rep_14011d7f0_New(fx, name)` to load the effect
by name, `SetLink` to the body, position/zoom, `particleSystemInfo.lifetime`,
append to the global FX list at `DAT_1439e5fe0`). They differ only in the
parameter packing and in the media-list loop (one or two lists). Both are
generic "spawn a named FX on a body"; neither has a vftable store, an RTTI
reference or a distinguishing string, and both share callers
(`Engine_ApplyThrustForce`, plus a different second caller set), so the pair
cannot be split into two proven identities. Recorded, not guessed. Funclet
`sz=0x270` matches the FX allocation in both.

| funclet | owner | member | family |
|---|---|---|---|
| `0x14033e4e0` | `0x140121c50` | `0x88` | freeField |
| `0x14033e510` | `0x140122200` | `0xe0` | freeField |

### S. Subsystem procedure (23)

Large procedures (500 B – 5.3 KB) with real subsystem content — strings,
callers, sometimes `LinkVFTABLE`/`LocationVFTABLE` writes — but no single
provable identity: either the function is one generic helper used by several
subsystems, or the strings only bound the *area* (HUD, tutorial, strategic
fleet, shipworks) without naming the operation. Notes per owner:

* `0x140023580` — builds a formatted GUI text block
  (`{font=dinpro_14_med}{align=0}…`, `gui_mil`), `Replica_Constructor`,
  `displayYellowLable?`; **no callers at all** (vtable/dispatch only), so even
  the subsystem is unknown.
* `0x140066d20` — minifig counter card (`MINIFIG_NUMBER`, `fun_crayon`,
  `gui_std*`, `flash_large_shadow`); called by all six precombat/shipworks
  panel builders → a shared layout helper, not one screen.
* `0x1400c12a0` — editor hover/preselect handling (`IsInEditor`, `IN_MENU?`,
  `Gui_Get/SetHoveredElementPosition`, `Editor_UndoZoom`); caller
  `FUN_1400bc5c0`.
* `0x1400ddcd0` — `SomethingGameTask` body (3 strings destroyed); editor
  missile/repair/funds tutorial text; caller `SomethingGameTask`.
* `0x1400f1940` — strategic-fleet pursuit/AI helper (`LinkVFTABLE`,
  `LocationVFTABLE`, `StrategicFleet_*`); callers
  `StrategicFleet_SelectPursuitTarget`, `StrategicFleet_UpdateAIState`.
* `0x1400f4210` — RbTree + `Fleet_FindShipsWithinRadius` spatial query;
  callers `StrategicFleet_UpdateAIState`, `variousHUDDisplays?`.
* `0x1400f6b70` — RbTree + `CreateTriggerVal`, `CANT_FOUND_WHERE_TO_REFUEL`.
* `0x140104df0` — HUD label drawing (`ZOOM_LEVEL`, `displayLables`,
  `IntelPolygon`); caller `handlePauseUnpause`.
* `0x14011a850` — `CONTAMINATION_01`, `toupper`, `calculateShipClasses?`,
  `formDialogStrings?`; caller `UpdateStrategicFleet`.
* `0x1402199e0` — builds a `Node` + 0xc0 ISerializable from a creature after
  `Creature::CalculateStats`/`Body_RebuildSubtreeList`; callers `!ClickFunc`,
  editor helpers.
* `0x140237e30` — word-wrap/justify of an `EscadraName` string
  (`rightPadEscadraWithParam`, replaces disallowed chars with `_`).
* `0x140238460` — radio/tutorial text (`RADIO_SAVE`, `TUTORIAL_CODES`,
  `TUTORIAL_TRADER`, `RadioBearing?`); caller `!ClickFunc`.
* `0x14023c820` — ship recreation from backup (`RECREATE_SHIP_INNER_ERROR`,
  `LinkVec_EmplaceReallocate`, `Node`); caller `loadShipBackups?`.
* `0x140253300` — tutorial triggers (`TUTORIAL_HUNTED`, `Dronish_descent`,
  `validateNpc?`); caller `MapCraft_ReturnChildrenToParent`.
* `0x1402d22e0` — battle ship stats/bounds (`SCR_COMBAT`, `battleManagerTick`).
* `0x1402dbb20` — body/part rebuild with `__RTDynamicCast`,
  `Joint_ConstructorWithNodes`, RbTree; callers shipworks/editor helpers.
* `0x1402ed2f0` — render-state/D3D helper used by `generateCityLandscape`.

| funclet | owner | member | family |
|---|---|---|---|
| `0x1403377e0` | `0x140023580` | `0x48` | freeField |
| `0x140338a70` | `0x140066d20` | `0x80` | string |
| `0x14033c700` | `0x1400c12a0` | `0xe8` | linkFree |
| `0x14033c730` | `0x1400c12a0` | `0x118` | linkFree |
| `0x14033cbd0` | `0x1400ddcd0` | `0x38` | string |
| `0x14033cc00` | `0x1400ddcd0` | `0x38` | string |
| `0x14033cc30` | `0x1400ddcd0` | `0x38` | string |
| `0x14033d930` | `0x1400f1940` | `0xe0` | freeField |
| `0x14033dab0` | `0x1400f4210` | `0x30` | linkFree |
| `0x14033db30` | `0x1400f6b70` | `0x80` | string |
| `0x14033dd30` | `0x140104df0` | `0x70` | linkFree |
| `0x14033e120` | `0x14011a850` | `0xe8` | string |
| `0x14033e150` | `0x14011a850` | `0x68` | string |
| `0x1403445b0` | `0x1402199e0` | `0xb8` | freeField |
| `0x140345630` | `0x140237e30` | `0x60` | string |
| `0x140345690` | `0x140238460` | `0xa0` | string |
| `0x1403456c0` | `0x140238460` | `0x80` | string |
| `0x1403456f0` | `0x140238460` | `0xa0` | string |
| `0x140345840` | `0x14023c820` | `0x68` | freeField |
| `0x140345b80` | `0x140253300` | `0x70` | string |
| `0x14034a4e0` | `0x1402d22e0` | `0xd8` | linkFree |
| `0x14034a680` | `0x1402dbb20` | `0x198` | freeField |
| `0x14034ab00` | `0x1402ed2f0` | `0xd8` | freeField |

### E. Edge cases (5)

| funclet | owner | member | family | reason |
|---|---|---|---|---|
| `0x1403423c0` | `0x14019abe0` `VectorString32_InsertRange` | — | rethrow | owner is proven, but the funclet body has **no member displacement** (vector-range rethrow helper); naming would invent a `+0x…` |
| `0x14034b743` | `0x140334358` `__scrt_is_nonwritable_in_current_image` | — | nobody | CRT owner, no member displacement — same problem |
| `0x140340ff0` | `0x14016bf00` | `0x38` | freeField | owner was created during batch 8 (`FUN_14016bf00`, 0x18-byte body, refs `f0.5`, `DAT_140352890`) but is itself unnamed and is a creation target of another agent; not renamed here |
| `0x140341220` | `0x14016bf00` | `0x70` | freeField | same owner as above |
| `0x140342380` | `0x1403423c0` `FUN_1403423c0` | `0xa0` | rethrow | owner is itself a `FUN_*` (batch-6 anomaly: member `+0xa0` exceeds the owner's 89-byte body) — no real identity |

### N. No function object at the funclet address (5)

`.pdata` has a funclet record and the owner exists, but there is no Ghidra
function object at the funclet address (the four creation targets batch 7 did
not create because their owners were stale, plus the block-13 record). These
become nameable only after (a) the owner is named and (b) the function object is
created from the `RUNTIME_FUNCTION` extent (24–47 bytes here).

| funclet | owner | member | family |
|---|---|---|---|
| `0x14033ce50` | `0x1400e0370` (vector helper) | `0x70` | rethrow |
| `0x14033d950` | `0x1400f1940` (strategic-fleet proc) | `0xe0` | freeField |
| `0x14033d970` | `0x1400f1940` (strategic-fleet proc) | `0x60` | other |
| `0x14034a660` | `0x1402dbb20` (body rebuild) | `0x40` | freeField |
| `0x140336d60` | `0x1400127f0` (vector helper) | `0x60` | freeField |

## 4. Method / hand-off

* Method was the same as batch 7, plus one extra signal used here: the
  `FUNCINFO4` sized-delete operand (`sz=`) equals the size of the temporary
  that the owner allocates. When an owner's body contains `New(sz)` with a
  vftable/string-backed type, that pair proves the owner↔funclet relation.
* Once any of the 66 owners is renamed for another reason, its funclet can be
  completed mechanically by the batch-7 pending pass
  (`/tmp/opencode/hf_ghidra_sweep/b7a1_pending.tsv` + `B7A1Pending.java`), which
  re-reads the owner name at run time. The 5 no-object rows additionally need
  the function object created first.
* Highest-value future targets, in order: `0x1400f6b70`
  (`CANT_FOUND_WHERE_TO_REFUEL`), `0x140066d20` (`MINIFIG_NUMBER` card),
  `0x1400ddcd0` (`SomethingGameTask` body), and the `0x140121c50` /
  `0x140122200` FX pair (a `.pdata`/vftable pass on the 0x270 FX object would
  split them).
