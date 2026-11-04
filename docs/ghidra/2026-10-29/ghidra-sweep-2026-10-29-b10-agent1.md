# Ghidra sweep, batch 10 agent 1 — open `/EH` funclets A

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`. Only the
1.163 program was used; the 1.151 program was never switched to or written.

Scope: the open funclets in `0x140336730–0x140341FFF`.

**Scope count.** The blackboard's "52 open funclets" is the combined total for
agents 1 and 2 (the same line is repeated verbatim in the agent-2 row). This
slice held **41**: 37 live `FUN_*` records plus 4 `.pdata` funclet records with
no function object (`0x140336d60`, `0x14033ce50`, `0x14033d950`,
`0x14033d970`). Agent 2's slice
(`0x140342000–0x140350510`) held 11 live `FUN_*`, which makes 41 + 11 = **52** —
consistent with the batch-8 open-42 list (`b8a3_open66_live.tsv`) after the four
batch-9 names in this range (`0x140338a70`, `0x14033db30`, `0x14033e120`,
`0x14033e150`).

**Result: 1 stale owner renamed; 5 funclets named + plated; 2 function objects
created (both named + plated); 36 still open.** No `save_program`, no tags, no
README/STATUS edits, no commit. No non-funclet `FUN_*`/`rep_*` outside the
funclet set was touched; no transaction was started (so none could leak).

| | count |
|---|---|
| open funclets at start of pass | **41** |
| … live `FUN_*` / `.pdata` records without a function object | 37 / 4 |
| stale owners proven + renamed | **1** |
| funclets named + plated | **5** |
| function objects created | **2** |
| still open | **36** |
| … of those, records still without a function object | 2 |

## 1. Owner renamed (1)

Posted on the blackboard (`**@agent1 -> rename**`) before applying, then applied
in the same pass with no objection.

| owner | old stale label | new name | evidence |
|---|---|---|---|
| `0x1400f1940` | `rep_1400ec220_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | **`Escadra_BuildRoutePath`** | `__thiscall(Escadra*, Node* target, Node* outLinks, char weighted, Node* start)`, 5273 B. Clears the out list, collects `Get_Profile()->designs` (type > 1, nonzero cost) into a 0x18-stride `{design,cost,visited,pred}` vector, allocates the dense distance/predecessor matrices (`AllocArrayStride24`, `VectorStride24_*`), weights by 24 h travel time (`hourCount_`, `(24 - max(0, hourCount-8))/24`), Dijkstra-relaxes with a closest-approach penalty at 1000 units (600 near the fleet when `+0x3a8 == 6`), then follows the predecessor chain and appends `Link_ConstructFromBody`/`Link_CopyConstructor` nodes for each body on the route. Asserts `CHECK ERROR: %s, %d` with `...\Escadra.cpp` line `0x1916`. Callers `StrategicFleet_SelectPursuitTarget`, `StrategicFleet_UpdateAIState`. Owner plated with summary/`Algorithm:`/`Parameters:`/`Returns:`. |

## 2. Funclets named + plated (5)

All five were named after their proved owner (`<Owner>_EhCleanup_<member>`); two
of them needed a `create_function` first.

| funclet | new name | owner | member | family | basis |
|---|---|---|---|---|---|
| `0x14033d930` | `Escadra_BuildRoutePath_EhCleanup_0xe0` | `0x1400f1940` | `0xe0` | freeField | `free(*(frame+0xe0))` — the owner's `New(0x370)` Location temporary (free size `0x370`) |
| `0x14033d950` | `Escadra_BuildRoutePath_EhCleanup_0xe0_2` | `0x1400f1940` | `0xe0` | sized-delete | **created** from `.pdata` `0x14033d950-0x14033d96f`; `0x1403340d0(*(frame+0xe0), 0x18)` — the `New(0x18)` link-list head |
| `0x14033d970` | `Escadra_BuildRoutePath_EhCleanup_0x60` | `0x1400f1940` | `0x60` | other | **created** from `.pdata` `0x14033d970-0x14033d995`; guard `[frame+0x24]&1`, destroys the 0x18-stride vector-of-vectors at `frame+0x60` via `0x140017240` |
| `0x140340ff0` | `Replica_AddProperties_EhCleanup_0x38` | `0x140165b80` `Replica_AddProperties` | `0x38` | freeField | `free(*(frame+0x38))`; owner's first `New(0x58)` Property (`m_backname_hat`), free size 0x58 matches |
| `0x140341220` | `URAnimation_CreateObject_EhCleanup_0x70` | `0x140178d50` `URAnimation_CreateObject` | `0x70` | freeField | `free(*(frame+0x70))`; owner's `New(0x1c8)` + `hgeAnimation_Constructor` temporary, free size 0x1c8 matches |

### Owner-attribution correction

`b8a3_open66_live.tsv` attributed both `0x140340ff0` and `0x140341220` to
`0x14016bf00` ("large GUI layout/refresh method"). That is wrong for the current
program: `0x14016bf00` is now `Slider_SetValue`, has no `New(0x58)`/`New(0x1c8)`
and no matching frame slot. `funclet-ownership-2026-10-29.tsv` (FuncInfo4 parse)
attributes them to `0x140165b80` and `0x140178d50`, and both bodies/free sizes
match those owners exactly. `structures.md:309` still repeats the stale
"(owner of two open funclets)" note for `0x14016bf00` — documentation should
drop it.

## 3. Still open — 36

Live `FUN_*` (34) plus two records with no function object. Categories are the
batch-9 ones, unchanged except for the items closed above.

### G. Generic container / allocator / vector replica (22)

Owners are MSVC vector instantiations or two-line wrappers over them; bodies only
call `New`/`free`/`memmove`/`memset`/`vectorTooLong`/`_Change_array`, carry no
vftable store and no string, and caller sets use different element types. Naming
would invent the template argument.

| funclet | owner | member | family |
|---|---|---|---|
| `0x1403368e0` | `0x1400dfa70` (stale `rep_...invalid_parameter`) | `0x90` | freeField |
| `0x140336d90` | `0x1400128f0` (stale `vector<u64>::_Change_array`) | `0x50` | freeField |
| `0x140336dc0` | `0x140012a30` (stale `rep_...New`) | `0x60` | freeField |
| `0x140336e30` | `0x140013160` (stale `vector<u64>::_Change_array`) | `0x80` | freeField |
| `0x140336f50` | `0x14016fa00` (stale `rep_...invalid_parameter`) | `0x50` | freeField |
| `0x140338110` | `0x140058270` (stale `...free`) | `0x80` | rethrow |
| `0x1403392f0` | `0x140089300` (stale `...memmove`) | `0x60` | rethrow |
| `0x140339370` | `0x140089b90` (stale `...memmove`) | `0x60` | rethrow |
| `0x140339430` | `0x14008ba20` (stale `...memmove`) | `0x60` | rethrow |
| `0x140339480` | `0x14008c5a0` (stale `...New`) | `0x60` | rethrow |
| `0x140339700` | `0x140090fd0` (stale `...New`) | `0x60` | rethrow |
| `0x1403399d0` | `0x14009b090` (stale `...invalid_parameter`) | `0x60` | rethrow |
| `0x14033c4d0` | `0x1400bb800` (stale `...memmove`) | `0x80` | rethrow |
| `0x14033cc80` | `0x1400df450` (stale `...invalid_parameter`) | `0x60` | rethrow |
| `0x14033cd50` | `0x1400dfde0` (stale `...invalid_parameter`) | `0x70` | rethrow |
| `0x14033e310` | `0x14011e440` (stale `...New`) | `0x60` | rethrow |
| `0x1403410f0` | `0x14016f6a0` (stale `...invalid_parameter`) | `0x80` | rethrow |
| `0x140341460` | `0x140183e00` (stale `vector<u64>::_Change_array`) | `0x60` | rethrow |
| `0x140341e10` | `0x140197510` (stale `vector<CHN*>`) | `0xa0` | rethrow |
| `0x140341ef0` | `0x1401986f0` (stale `...free`) | `0x70` | rethrow |
| `0x140341f50` | `0x140198ac0` (stale `...free`) | `0x60` | rethrow |
| `0x140341fb0` | `0x140198eb0` (stale `...free`) | `0x70` | rethrow |

Two more generic records have **no function object** and a stale generic owner, so
there is nothing provable to name and nothing was created:

| funclet | owner | member | family |
|---|---|---|---|
| `0x140336d60` | `0x1400127f0` (stale `vector<u64>::_Change_array`) | `0x60` | freeField |
| `0x14033ce50` | `0x1400e0370` (stale `...memmove`) | `0x70` | rethrow |

### S. Subsystem procedure — area known, operation not proven (8)

| funclet | owner | member | family | why still open |
|---|---|---|---|---|
| `0x1403377e0` | `0x140023580` -> **`Body` vtable slot 81** | `0x48` | freeField | Builds a `Replica` label GUI (`{font=dinpro_14_med}{align=0}{color=…}`, `gui_mil`, `"@8"`, `displayYellowLable_` on `this+0x7d8`) and links it globally. Sits between slots 80 `Body_BuildPartStatsText` and 82 `Body_BuildPartInfoPanel`, but slot order does not prove the method name. Owner not renamed. |
| `0x14033c700` | `0x1400c12a0` (stale `...invalid_parameter`) | `0xe8` | linkFree | Editor/map tick: fills a vector from `DAT_1439e9408`, dedups by `+0xb8`, unifies co-located bodies (`Body_IsMountedOrPaired`, ≤1 unit) and handles the editor preselect back-stack (`IsInEditor`, `IN_MENU`, `Gui_HasPreselectBack`, `ZOOM_LEVEL`, `TARGET_SCREEN_X/Y`). Sole caller a one-line wrapper gated on `DAT_1403ef368`; the operation name is not provable. |
| `0x14033c730` | `0x1400c12a0` | `0x118` | linkFree | same owner |
| `0x14033cbd0` | `0x1400ddcd0` (stale `...invalid_parameter`) | `0x38` | string | Per-frame tutorial trigger cascade (`TUTORIAL_EDITOR_REPAIR`, `TUTORIAL_REPAIR_2`, `TUTORIAL_FUNDS_CARGO`, `TUTORIAL_EDITOR_MISSILES*`, spawns `MDL_MISSILE_01`, `formDialogStrings_`). A `Tutorial_*` name would be a summary, not a proved operation. |
| `0x14033cc00` | `0x1400ddcd0` | `0x38` | string | same owner |
| `0x14033cc30` | `0x1400ddcd0` | `0x38` | string | same owner |
| `0x14033dab0` | `0x1400f4210` (stale `...sqrtf`) | `0x30` | linkFree | Escadra refuel-partner evaluation: `Fleet_FindShipsWithinRadius`, fuel-ratio filter (`+0x494/+0x498/+0x4a0/+0x4a8`), stores a design at `+0x298`, builds an RbTree and counts candidates. Cannot be separated with certainty from `Escadra_FindRefuelTarget` (batch 9), so no "partner/source" name was invented. |
| `0x14033dd30` | `0x140104df0` (stale `...checkJammed?`) | `0x70` | linkFree | Location map draw for `Location_conflict*`: zoom-adjusted position (`ZOOM_LEVEL`, `SetAimRectZoom`, `Vec2_FloorIfGridEnabled`), `IntelPolygon` for type 2, `Gfx_QuadPositionFromExtents`; called per location from `handlePauseUnpause`. Exact draw step not distinguishable from the other `displayLables*` helpers. |

### X. FX spawner pair (2) — left open

`0x140121c50` and `0x140122200` are both "allocate a 0x270 `FX` object, `CreateFX`,
load the media named by the caller (`rep_14011d7f0_New`), `SetLink` to the body,
set position/zoom/lifetime, append to the global FX list". They differ only in
parameter packing (a vector-of-groups media list vs one media list) and in their
caller sets (fire/thrust vs explosion/debris); the effect name is always a
parameter and there is no distinguishing string, RTTI or vftable store. This pass
re-read both bodies (1400 B / 1110 B) and confirms batch 9: no provable operation
name.

| funclet | owner | member | family |
|---|---|---|---|
| `0x14033e4e0` | `0x140121c50` (stale `...loadMediaByName?`) | `0x88` | freeField |
| `0x14033e510` | `0x140122200` (stale `...loadMediaByName?`) | `0xe0` | freeField |

### E. Shared / corrupt records (2) — left open

| funclet | owner(s) | member | family | reason |
|---|---|---|---|---|
| `0x140336c40` | `0x1400112c0` `WriteString` **and** `0x14011ba00` `WriteCharArray` (ICF-shared) | `0x60` | vdtor | Both owners already named; the body calls the frame object's scalar deleting destructor. Naming after one owner would be wrong; project convention keeps ICF-shared funclets unnamed. |
| `0x140336e70` | `0x140336ea0` (itself a `_CxxThrowException` catch-handler funclet) | `0x88`/`0x98` | other | Corrupt record: the `.pdata` owner is not a real parent (it is a sibling catch handler in the `0x140336c80–0x140336f00` cluster). Body copies `[frame+0x88]` to `*[frame+0x98]` and calls `0x14033658e`. |

## 4. Method / hand-off

* Enumerated live `FUN_*` in the range from `list_functions` (477 functions in
  range, 37 `FUN_*`), then joined to the `.pdata` owner map and checked every owner's
  **current** name (`list_functions`), not the batch-8 snapshot. That is how the
  two `Replica_AddProperties` / `URAnimation_CreateObject` funclets were unblocked:
  their owners had no function object in batch 8 but are named today.
* Verified each funclet's member/guard from its own decompile or disassembly
  before naming; the two created bodies were disassembled from the exact
  `RUNTIME_FUNCTION` extent and checked to end in `RET` inside it.
* Count reconciliation: two independent sources of "open" disagree by a few rows
  (`b8a3_open66_live.tsv` vs `funclet-ownership-2026-10-29.tsv`); the TSV owner
  attribution was correct in the disputed `0x140340ff0`/`0x140341220` case, the
  batch-8 list was not. Compare owner identity against the owner's actual body
  (allocation size / frame slot), not against the previous note.
* Highest-value next targets in this band, in order: `0x140023580` (Body vtable
  slot 81 — needs a slot-name proof from the Body vtable family), `0x1400c12a0`
  (editor tick, 2 funclets), `0x1400ddcd0` (tutorial cascade, 3 funclets), then
  the `0x140121c50`/`0x140122200` FX pair via a pass over the 0x270 FX object's
  vtable.
