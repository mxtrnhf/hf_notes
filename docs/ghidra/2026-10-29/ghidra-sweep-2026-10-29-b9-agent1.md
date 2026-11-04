# Ghidra sweep, batch 9 agent 1 — open `/EH` funclets A

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: the open funclets of batch 8 in `0x140336730–0x14033FFFF`. The
assignment line says 66, but that is the batch-8 total for all three funclet
agents; the slice that starts at `0x140336730` held **35** in batch 8's list and
holds **37** live funclet records today.

**2 owners proven and renamed; 4 funclets named + plated. 33 still open.**
No `save_program`, no tags, no README/STATUS edits, no commit; no non-funclet
`FUN_*`/`rep_*` was touched.

| | count |
|---|---|
| open funclet records in `0x140336730–0x14033FFFF` (live) | 37 |
| … with a Ghidra function object | 33 |
| … without a function object | 4 |
| owners renamed (stale `rep_*` → real identity) | **2** |
| funclets named + plated this pass | **4** |
| still open | **33** |
| … of those, records missing from batch 8's 35-row list | 2 |

Program after the pass: 4/4 new names unique and plated; 33/33 remaining rows
still `FUN_*` (29 with a function object, 4 without). Nothing else in the range
was modified.

## 1. Owners renamed (2)

Both were stale `rep_*` replica labels naming a CRT import that is not the body
at that address (and the named address itself — `0x1400f13a0`, `0x140063d80` —
is not a function in the program). Each owner was replated with the evidence
below. Posted on the blackboard at 14:47 and applied at 14:59 (one cycle, no
objection).

| owner | old label | new name | why |
|---|---|---|---|
| `0x1400f6b70` | `rep_1400f13a0_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | **`Escadra_FindRefuelTarget`** | `this` is an Escadra (`+0x150` position, `+0x3a8` state, `+0x550/+0x558` location list, `+0x3c0` message string). For state 1/3 it walks `Get_Profile()->designs`, keeps the design nearest to any fleet location if within 600 units, skips tutorial-gated designs (`CreateTriggerVal`), and returns the chosen design; both callers store it at `fleet+0x610`. With no candidate it appends `"CANT FOUND WHERE TO REFUEL\n"` to the fleet message. 1170 B, callers `StrategicFleet_UpdateAIState` + a compare helper. |
| `0x140066d20` | `rep_140063d80_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | **`Gui_BuildMinifigCard`** | Builds one card GUI: `New(0xe70)` + `GUI::GUI_2`, background sprite from the caller (`ED_SHPWRK_MINIFIG` from `Shipworks_BuildResultCards`), two `CreateSpriteCreature` ship sprites, optional `Precombat_FormatStatRowText` row, optional `MINIFIG_NUMBER` child (`Text_RightPadInteger`) with `fun_crayon`; returns the GUI. Seven callers are all card/panel builders (`Shipworks_BuildResultCards` stores the result at `+0x3ec`, plus Precombat_BuildCardLayout/BuildMapLayout, Landing_BuildPrelandingPanel, Moral_BuildMiniFigPanel, Victory_BuildBadgePanel, buildPrecombatScreen). 1194 B. |

Third proposed owner `0x14011a850` was renamed to `Escadra_UpdateContamination`
by the concurrent `rep_*` pass between the post and the apply; nothing was done
to it here beyond naming its two funclets (§2).

## 2. Funclets named + plated (4)

Each plate follows the batch-6/7/8 template (owner + `0x140000000+offset`,
member, family, `Algorithm:`, `Parameters:`, `Returns:`, provenance). All four
bodies are the standard `String_Tidy(frame+MEMBER)` clone (`0x140006d70`) with a
guard bit; the `sz`/member pairing with the owner's temporary was checked
against the decompiled owner.

| funclet | new name | member | guard | body |
|---|---|---|---|---|
| `0x14033db30` | `Escadra_FindRefuelTarget_EhCleanup_0x80` | `+0x80` | `[frame+0x30]` bit 1 | `0x14033db30-0x14033db59` |
| `0x140338a70` | `Gui_BuildMinifigCard_EhCleanup_0x80` | `+0x80` | `[frame+0x6c]` bit 1 | `0x140338a70-0x140338a99` |
| `0x14033e120` | `Escadra_UpdateContamination_EhCleanup_0xe8` | `+0xe8` | `[frame+0x30]` bit 1 | `0x14033e120-0x14033e149` |
| `0x14033e150` | `Escadra_UpdateContamination_EhCleanup_0x68` | `+0x68` | `[frame+0x30]` bit 2 | `0x14033e150-0x14033e176` |

All four were `FUN_*` at the start of the pass, so no already-named function was
renamed here; the rename protocol was used only for the two owners in §1.

## 3. Still open — 33

### G. Generic container / allocator / vector replica (18)

Owners are MSVC container/array instantiations or two-line wrappers over them.
Their bodies call only `New`/`free`/`memmove`/`memset`/`vectorTooLong`/
`ThrowBadArrayLengthException`/`_Change_array`/`AllocateArrayOf8Byte`, carry no
vftable store and no string, and their caller sets do not fix the element type.
Naming would invent the template argument (and several are exact `rep_*` twins
of already-named `std::vector<unsigned __int64>::_Change_array` bodies, so the
name-collision rule would reject a derived funclet name anyway).

| funclet | owner | member | family | owner shape / callers |
|---|---|---|---|---|
| `0x1403368e0` | `0x1400dfa70` | `0x90` | freeField | `New`/`free` growth helper; callers `displayAircraftStrategicMap`, `displayLables` |
| `0x140336d90` | `0x1400128f0` | `0x50` | freeField | `vector<uint64>::_Change_array` replica, 27 callers |
| `0x140336dc0` | `0x140012a30` | `0x60` | freeField | `New`/`free`/`memmove` growth helper, 11 callers |
| `0x140336e30` | `0x140013160` | `0x80` | freeField | `vector<uint64>::_Change_array` replica, caller `copyOverBody` |
| `0x140336f50` | `0x14016fa00` | `0x50` | freeField | 8-byte-array `memset`/`memmove` resize helper; caller `Texture_LoadAllFromFolder` |
| `0x140338110` | `0x140058270` | `0x80` | rethrow | `Object_MoveRange30` + `New`; caller is a generic free wrapper |
| `0x1403392f0` | `0x140089300` | `0x60` | rethrow | shader vector growth; callers `ShaderBackground`/`ShaderDeferringSubscreen_Constructor` |
| `0x140339370` | `0x140089b90` | `0x60` | rethrow | same, 10 `Shader*_Constructor` callers |
| `0x140339430` | `0x14008ba20` | `0x60` | rethrow | same, `ShaderColor`/`ShaderDeferringCloseAndPrebloom_Constructor` |
| `0x140339480` | `0x14008c5a0` | `0x60` | rethrow | same, `ShaderDefault`/`ShaderDepth_Constructor` |
| `0x140339700` | `0x140090fd0` | `0x60` | rethrow | same, `ShaderDeferringFarStepness_Constructor` |
| `0x1403399d0` | `0x14009b090` | `0x60` | rethrow | same, `ShaderShockwaveTemplate_Constructor` |
| `0x14033c4d0` | `0x1400bb800` | `0x80` | rethrow | `vector<uint64>::_Change_array`, callers `SCR_BOMBERS` + two generic |
| `0x14033cc80` | `0x1400df450` | `0x60` | rethrow | `New`/`free` growth helper, one generic caller |
| `0x14033cd50` | `0x1400dfde0` | `0x70` | rethrow | 12-byte-stride push helper; callers `Ballistics_PredictHit`, `Vector12_PushBack`, … |
| `0x14033e310` | `0x14011e440` | `0x60` | rethrow | `New`/`memmove` growth helper; caller a `memset`-labelled wrapper |
| `0x140336d60` | `0x1400127f0` | `0x60` | freeField | `vector<uint64>::_Change_array` replica, 29 callers — **no function object** |
| `0x14033ce50` | `0x1400e0370` | `0x70` | rethrow | `vector<uint64>::_Change_array` replica — **no function object** |

### S. Subsystem procedure, area known but operation not proven (11)

Real subsystem bodies with strings/callers/links, but the evidence only bounds
the area. New findings since batch 8 are marked ★.

| funclet | owner | member | family | owner evidence |
|---|---|---|---|---|
| `0x1403377e0` | `0x140023580` | `0x48` | freeField | ★ **Body vtable method**: slot 0 of five Body-derived vtables (`0x140354ec0`, `0x140361158`, `0x1403630e0`, `0x140362a20`, `0x140361f88`), immediately between `Body_BuildPartStatsText` (slot −1) and `Body_BuildPartInfoPanel` (+1). Builds a `Replica` GUI with `{font=dinpro_14_med}{align=0}{color=…}`, `gui_mil`, `"@8"`, then links it globally. No callers (dispatch only); the slot ordering does not force a name. |
| `0x14033c700` | `0x1400c12a0` | `0xe8` | linkFree | Editor/map tick: fills a vector from `DAT_1439e9408` and dedups by `+0xb8`, then handles the editor preselect back-stack (`IsInEditor`, `IN_MENU`, `Gui_HasPreselectBack`, `ZOOM_LEVEL`, `TARGET_SCREEN_X/Y`). Sole caller `FUN_1400bc5c0`, a one-line wrapper gated on `DAT_1403ef368`. |
| `0x14033c730` | `0x1400c12a0` | `0x118` | linkFree | same owner. |
| `0x14033cbd0` | `0x1400ddcd0` | `0x38` | string | ★ Per-frame tutorial trigger cascade (caller `SomethingGameTask`): `TUTORIAL_EDITOR_REPAIR`/`TUTORIAL_REPAIR_2`/`TUTORIAL_FUNDS_CARGO`/`TUTORIAL_EDITOR_MISSILES*`, spawns `MDL_MISSILE_01`, `formDialogStrings_`, writes trigger values. A `Tutorial_*` name would be a summary, not a provable operation. |
| `0x14033cc00` | `0x1400ddcd0` | `0x38` | string | same owner. |
| `0x14033cc30` | `0x1400ddcd0` | `0x38` | string | same owner. |
| `0x14033d930` | `0x1400f1940` | `0xe0` | freeField | ★ Escadra route/waypoint planner: `LinkedList_ClearFree` on the out-list, builds `LocationVFTABLE` nodes from `Profile->designs`, a pairwise distance matrix over the candidates (`VectorStride24_*`, `AllocArrayStride24`), weights by 24 h travel time (`hourCount_`), closest-approach test at 1000 units; 5267 B. Callers `StrategicFleet_SelectPursuitTarget`, `StrategicFleet_UpdateAIState`. |
| `0x14033dab0` | `0x1400f4210` | `0x30` | linkFree | ★ Escadra refuel-partner evaluation: `Fleet_FindShipsWithinRadius`, filter by fuel ratio (`+0x494/+0x498/+0x4a0/+0x4a8`), pick a ship and store its design at `+0x298`, then build an RbTree. Callers `StrategicFleet_UpdateAIState`, `variousHUDDisplays?`. Cannot be split from `Escadra_FindRefuelTarget` with certainty, so neither is renamed to a "partner/source" name. |
| `0x14033dd30` | `0x140104df0` | `0x70` | linkFree | ★ Location map draw: zoom-adjusted position (`ZOOM_LEVEL`, `SetAimRectZoom`, `Vec2_FloorIfGridEnabled`), `IntelPolygon` for type 2, `Gfx_QuadPositionFromExtents`, `displayAircraftStrategicMap`/`displayLables`; called per location from `handlePauseUnpause`. Body is a draw routine, but the object is a `Location_conflict*` and the exact draw step is not distinguishable from the other `displayLables*` helpers. |

### X. FX spawner pair (2)

`0x140121c50` and `0x140122200` are near-identical "spawn a named FX on a body"
factories (`New(0x270)` → `CreateFX`, `rep_14011d7f0_New(fx, name)` to load the
effect, `SetLink` to the body, position/zoom, lifetime, append to the global FX
list `DAT_1439e5fe0`). They differ in parameter packing and in the number of
media lists; both take the effect name as a parameter and have no distinguishing
string, RTTI or vftable store. Caller sets overlap
(`Engine_ApplyThrustForce`); `0x140121c50` leans fire/thrust
(`Body_SpawnBurningParticles`, `Body_SpawnFireEffect`, `World_ThermalPass`),
`0x140122200` leans explosion/debris (`Body_Explode`,
`Creature_SpawnImpactDebris`, `FX_SpawnExplosionDebris`,
`rescueSurvivorsEffect?`), which is suggestive but not proof. Funclet `sz=0x270`
matches both.

| funclet | owner | member | family |
|---|---|---|---|
| `0x14033e4e0` | `0x140121c50` | `0x88` | freeField |
| `0x14033e510` | `0x140122200` | `0xe0` | freeField |

### E. Shared / corrupt records (2 — not in batch 8's list)

Both are genuine `RUNTIME_FUNCTION` records in
`0x140336730–0x140337000`, attributed by the b7 block-13 scan
(`b7a1_new13.txt`), but they were dropped from the batch-8 working list and are
still `FUN_*` today.

| funclet | owner(s) | member | family | reason |
|---|---|---|---|---|
| `0x140336c40` | `0x1400112c0` `WriteString` **and** `0x14011ba00` `WriteCharArray` (ICF-shared) | `0x60` | vdtor | Both owners are already named. The body calls the frame object's scalar deleting destructor (`RDX=[frame+0x60]`, `[vtable+4]`, delete flag `R8B=1`, CFG dispatch). Sharing means naming after one owner would be wrong; the project convention keeps ICF-shared funclets unnamed (cf. the 73 shared ones in `structures.md`). |
| `0x140336e70` | `0x140336ea0` (`rep_14030bf70_VCRUNTIME140.DLL::_CxxThrowException`) | `0x88`/`0x98` | other | Corrupt record: the owner is itself a catch-handler stub (a `.pdata` primary of the same `_CxxThrowException` cluster), so the funclet's "owner" is not a real parent. Body copies `[frame+0x88]` into `*[frame+0x98]` and calls `0x14033658e`. |

### N. No function object at the funclet address (4, of which 2 are also G)

`.pdata` has the record and the owner exists, but there is no Ghidra function
object, so naming needs both a proven owner and a `create_function` from the
`RUNTIME_FUNCTION` extent. Two owners are generic vector helpers (§G), two are
the Escadra planner in §S; none is proven, so no object was created.

| funclet | owner | member | family |
|---|---|---|---|
| `0x140336d60` | `0x1400127f0` | `0x60` | freeField |
| `0x14033ce50` | `0x1400e0370` | `0x70` | rethrow |
| `0x14033d950` | `0x1400f1940` | `0xe0` | freeField |
| `0x14033d970` | `0x1400f1940` | `0x60` | other |

## 4. Method / hand-off

* Order of work: enumerate live `FUN_*` in the range, join to the `.pdata`
  owner map (b6) and the b7 block-13 attribution for addresses below
  `0x140337000`, then prove each owner from its body (fields, strings, callees,
  vtable slots). Function objects were never created before an owner was proven.
* The `rep_*` labels in this band are all wrong (`rep_<nonexistent addr>_<CRT
  import>`); they are stale dedup labels, not identities.
* Two useful new cross-checks this pass: (a) a funclet record can be missing
  from the working list — compare the live `FUN_*` set against `.pdata`, not
  against the previous note; (b) `.pdata` attribution alone is not enough for
  the `_CxxThrowException` cluster at `0x140336c80–0x140336f00`, because those
  are catch handlers, and a funclet can be attributed to one of them
  (`0x140336e70`).
* Highest-value next targets in this band, in order: `0x1400f1940`
  (Escadra route planner — naming it also unlocks the two no-object funclets
  `0x14033d950`/`0x14033d970`), `0x1400ddcd0` (tutorial cascade, 4 funclets),
  `0x1400c12a0` (editor tick, 2 funclets), and the `0x140121c50`/`0x140122200`
  FX pair (a pass over the 0x270 FX object's vtable/callers could split them).
