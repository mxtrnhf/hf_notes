# Unnamed-function sweep, 2026-10-29 — batch 5, agent 4

Range: `0x140348000–0x140350510` (second half of the compiler tail: the tail of
the `/EH` funclet run, then the `atexit` static-object destructors).

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
**23 functions renamed, every one plated.** No `create_function` (there is no
code address without a function object in this range), no `save_program`, no
tags, no README/STATUS edits, no commits.

This range was already surveyed by batch 4 agent 2 (`...-b4-agent2.md`, which
covered `0x140340000–0x140350510` and named 53). The renames below are the ones
that were still missing; where batch 4 left a family unnamed on purpose I say so
rather than re-naming its copies.

## Starting / ending state

| | start | end |
|---|---|---|
| `FUN_*` in range | 196 | 173 |
| `rep_*` in range | 83 | 83 (untouched) |
| already named | 48 | 71 |
| funclet half `0x140348000–0x14034b3ff` | 109 `FUN_*` | 105 `FUN_*` (6 named) |
| destructor cluster `0x14034b400–0x140350510` | 87 `FUN_*` | 68 `FUN_*` (65 named) |

## Method

1. `run_script_inline` listing of every function in range with body size, then a
   size/shape census (the range is almost entirely small compiler output, so the
   body size *is* the family: 12, 15, 32, 41, 47, 52, 55, 82, 99, 101, 105, 108,
   127, 134 bytes).
2. For the funclet half, every body was reduced to an instruction-level
   signature (callee names + immediates in the 0x20–0x3000 window) and grouped.
   That gave 52 distinct shapes over 109 functions, i.e. 57 copies; grouping was
   done without the decompiler.
3. For the destructor cluster, every unnamed body was scanned for address
   operands (both `Scalar` and `Address` forms — the 101-byte `vec8` bodies use
   RIP-relative loads through the `free` pointer table at `0x1403517c0` and are
   invisible to a scalar-only scan). Each touched global was then resolved to its
   primary symbol and to the **named** functions that reference it.
4. Destructors were paired with initialisers **by global address**, using batch-4
   agent 3's initialiser table. Reference-based reverse lookup: for each global,
   search the functions referencing it for an `InitGlobal_*` name. That found
   four exact pairs that batch 4 missed (below).
5. Batch `decompile_function` (10 at a time) only on the shapes the census left
   ambiguous; the decompiler was kept out of the scripts.

## Cluster map

| span | count | what it is | action |
|---|---|---|---|
| `0x140348000–0x14034b3ff` | 109 | MSVC `/EH` + `/GS` funclets `(int code, void* frame)` | 4 anchors named, 105 copies left |
| `0x14034b400–0x14034b780` | 2 | `__ArrayUnwind`, `_seh_filter_exe` replicas (`rep_*`) | untouched |
| `0x14034b780–0x140350510` | 87 | `atexit` static-object destructors `void f(void)` | 19 named, 68 left |
| everywhere | 83 | ICF `rep_*` replicas of CRT/game targets | untouched |

## Renames — funclet families (4)

All four are *distinct* families with no existing anchor (batch 4's ten anchors
cover the string/free/ios/vector families; the two new string families I found
turned out to be already anchored in agent 3's half, see "coordination").

| addr | name | family | copies |
|---|---|---|---|
| 0x140348670 | `EhCleanup_WideRecordStrings` | guard word at `frame+0x98`, eight `std::string` members at `+0x2ec8…+0x2fe8`, one construction bit each (`0x100…0x2000`) | 8 |
| 0x14034a4b0 | `EhCleanup_LinkMember` | construction bit + `freeLinkMemory_` on a `Link` member | 6 |
| 0x14034a850 | `EhCleanup_DeleteArrayThenRethrow` | `DeleteArray16` then `_CxxThrowException(0,0)`; `0x14034a990` is the `DeleteArray32` variant | 2 |
| 0x14034a880 | `EhCleanup_DeallocateThenRethrow` | `deallocate` then `_CxxThrowException(0,0)` | 5 |

Left in the funclet half (105), by family — all byte-identical to an anchor
outside the range, only the frame offset differs:

| family | count | note |
|---|---|---|
| member-string cleanup, guard `+0x98` (also `+0x34`), string `+0x640`/`+0x98` | 51 | copies of `EhCleanup_MemberString88` (0x140340150) |
| member-string cleanup, guard `+0xa8`, string `+0x3e88` | 24 | copies of agent 3's `EhCleanup_MemberStringA8` (0x140344900) |
| member-string cleanup, guard `+0x30`, strings `+0xa0…+0x1a0` | 6 | copies of agent 3's `EhCleanup_MemberString30` (0x140344550) |
| `free(*(void**)(frame+N))` | 6 | copies of `EhCleanup_FreeField70` |
| guard + `freeLinkMemory_` | 6 | covered by the new anchor |
| wide-record strings | 8 | covered by the new anchor |
| deallocate/DeleteArray + rethrow | 7 | covered by the two new anchors |
| `memmove` insert rollback | 1 (0x14034a310) | copy of `EhCleanup_InsertRollback` |

6 `rep_*` in the same span are ICF replicas (`free`, `_CxxThrowException`,
`deallocateString?`) and were left.

## Renames — global destructors (19)

All are `void(void)` bodies, registered only from the `atexit` block at
`0x140001000–0x140004400`. Evidence column is what the body destroys.

### Exact initialiser pairs (global address)

| addr | name | global | initialiser |
|---|---|---|---|
| 0x14034cea0 | `DtorGlobal_Container_1439e9378` | 0x1439e9378 | `InitGlobal_Container_1439e9378` (0x140002db0) |
| 0x14034cf20 | `DtorGlobal_Container_1439e9368` | 0x1439e9368 | `InitGlobal_Container_1439e9368` (0x140002df0) |
| 0x14034e0f0 | `DtorGlobal_Container_143a13af0` | 0x143a13af0 | `InitGlobal_Container_143a13af0` (0x140003a50) |
| 0x14034e680 | `DtorGlobal_Container_143a13bf8` | 0x143a13bf8 | `InitGlobal_Container_143a13bf8` (0x140003e90) |

All four are singly linked lists: clear the tail pointer, free every node from
the head, free the sentinel. Batch 4's pairing only matched globals whose name
already appeared in the initialiser table; these four were in the table but were
not matched because the batch-4 pass read only scalar operands.

### Default-escadra-name block (all reset to `DEFAULT_ESCRADANAME_VALUES`)

| addr | name | global | shape |
|---|---|---|---|
| 0x14034cb60 | `DtorGlobal_DefaultEscadraNameA` | 0x1439e80c8 (string, reset word 0x1439e80d8) | 99 B |
| 0x14034ca60 | `DtorGlobal_DefaultEscadraNameB` | 0x1439e8178 (string, reset word 0x1439e8188) | 99 B |
| 0x14034cc60 | `DtorGlobal_DefaultEscadraNameC` | 0x1439e81c0 (string, reset word 0x1439e81d0) | 99 B |
| 0x14034cad0 | `DtorGlobal_DefaultEscadraNameVectorA` | 0x1439e8150 (0xc-stride vector) | 134 B |
| 0x14034cbd0 | `DtorGlobal_DefaultEscadraNameVectorB` | 0x1439e80a0 (0xc-stride vector) | 134 B |

The block `0x1439e80a0–0x1439e81d8` is five statics; each string destructor
writes the literal `DEFAULT_ESCRADANAME_VALUES` back over the string header word
after freeing, which is what identifies the block.

### Named from the global's consumers (single subsystem each)

| addr | name | global | consumers (named refs) |
|---|---|---|---|
| 0x14034b780 | `DtorGlobal_LevelListHeadB` | 0x1403c6330, tree destroy | `ResetLevelListHeads`, `AircraftFormationManager`; twin of 0x1403c6320 (`DtorGlobal_LevelListHead`), both reset by `ResetLevelListHeads` |
| 0x14034c130 | `DtorGlobal_ShipworksRecordVector` | 0x1403ef3b8, 0x20-stride vector | `somethingShipworks?`, `loadShipworks?` |
| 0x14034c2a0 | `DtorGlobal_MapPinLink` | 0x1403ef3d0 (`Link`) | `Editor_HandleClickMode9`, `moveMapPin?`, `removeMapPin?`, `loadShipworks?` |
| 0x14034c4e0 | `DtorGlobal_RosterLink` | 0x1403ef410 (`Link`) | `Roster_RemoveEntry`, `Gui_ClearElementListA` |
| 0x14034c4f0 | `DtorGlobal_GuiElementLinkB` | 0x1403ef3e8 (`Link`) | `Gui_ClearElementListB` |
| 0x14034e470 | `DtorGlobal_LootHazardLinkA` | 0x143a2bf00 (`Link`) | `handleLootHazards` only |
| 0x14034e460 | `DtorGlobal_LootHazardLinkB` | 0x143a2bf20 (`Link`) | `handleLootHazards` only |
| 0x14034e480 | `DtorGlobal_LootHazardLinkC` | 0x143a2bf40 (`Link`) | `handleLootHazards` only |
| 0x14034e450 | `DtorGlobal_LootHazardLinkD` | 0x143a2bf60 (`Link`) | `handleLootHazards` only |
| 0x14034fe40 | `DtorGlobal_ExplosionDebrisLink` | 0x1403c2d98 | `FX_SpawnExplosionDebris` only |

## Left deliberately in the destructor cluster (68)

Batch 4's scheme stands: these globals have no symbol and no initialiser-table
entry, so an address-encoded name would add nothing over the function address.
They are characterised by shape instead:

| shape | count | addresses |
|---|---|---|
| `Link` destructor, `freeLinkMemory_(&global)` (12 B) | 30 | 0x14034b850 0x14034c2b0 0x14034c500 0x14034c580 0x14034c590 0x14034c870 0x14034c880 0x14034ce20 0x14034ce30 0x14034ce60 0x14034ce70 0x14034ce80 0x14034ce90 0x14034d940 0x14034d950 0x14034d960 0x14034d970 0x14034d980 0x14034de50 0x14034e280 0x14034e2c0 0x14034e320 0x14034e490 0x14034e6e0 0x14034efe0 0x14034f9a0 0x14034f9b0 0x14034fbc0 0x14034fd30 0x14034fd40 |
| `vec8` (ptr/size/cap, 101 B) | 15 | 0x14034b8e0 0x14034b950 0x14034b9c0 0x14034bbb0 0x14034bc90 0x14034c610 0x14034c890 0x14034eef0 0x14034f010 0x14034f1e0 0x14034fbd0 0x14034fcc0 0x140350030 0x140350260 0x140350480 |
| `std::string` (105 B, capacity reset to 0xf) | 9 | 0x14034bf60 0x14034d320 0x14034d430 0x14034d4a0 0x14034d800 0x14034d9a0 0x14034e150 0x14034e730 0x14034f8a0 |
| singly linked list, 108 B | 4 | 0x14034eab0 0x14034f3f0 0x14034f460 0x14034f4d0 |
| `vec32` (0x20-stride, 127 B) | 4 | 0x14034d650 0x14034e4f0 0x14034e570 0x14034e5f0 |
| `vec12` (134 B) | 2 | 0x14034cf60 0x14034fe50 |
| two static `Link` objects in one body (32 B) | 2 | 0x14034c4a0 0x14034c4c0 |
| not destructors (15 B) | 2 | 0x1403504f0 0x140350500 — they *assign* `PTR_FUN_140369200/140369218` to `PTR_PTR_1403c2e10/18`; still no recoverable role |

Reasons for leaving the ones that *do* have named consumers:
* 0x14034c2b0 (0x1403ef3a0) is read by `loadShipworks?`, `Gui_GetTopElementB`
  and `memcmp_editor` — no single subsystem, so a subsystem name would be a
  guess.
* 0x14034d940/950/960/970/980, 0x14034eef0, 0x14034f9a0/9b0/fbc0 are `Link`
  heads read by 7–20 named functions from different subsystems (city, missile,
  strategic fleet, battle manager) — shared list heads, not one owner.
* 0x14034e4f0/0x14034e5f0/0x14034d650 are 0x20-stride vectors whose only named
  readers are `initGame`, `GetCityName`, `Body_PreStepUpdate`; the record type is
  not established.

## `rep_*` in range (83, untouched)

Each already carries its target's name (`free`, `_CxxThrowException`,
`_invalid_parameter_noinfo_noreturn`, `_ArrayUnwind`, `_seh_filter_exe`,
`basic_ios::~basic_ios`, `deallocateString?`, `memmove`). Renaming would
duplicate existing names, which the blackboard forbids.

## Coordination (posted to the batch-5 blackboard)

* The four `DtorGlobal_Container_*` pairs above are additional to batch 4's ten
  and are relevant to agent 3's initialiser bookkeeping.
* `EhCleanup_MemberStringA8` (0x140344900) and `EhCleanup_MemberString30`
  (0x140344550) already exist in agent 3's half — they appeared between my
  census and my rename pass, so my byte-copies at 0x140349b70 and 0x14034b2a0
  were correctly rejected by the name-collision check and left as clones.

## Open questions

* Funclet ownership is still the only real unknown: every funclet has exactly
  one data xref from the unwind/funclet table at `0x14808a000`, so the owning
  function can only be recovered by parsing `RUNTIME_FUNCTION`/scope tables, not
  from calls. Nothing in this range is a `create_function` candidate.
* `0x1403504f0/0x140350500` assign a function-table pointer pair to
  `0x1403c2e10/0x1403c2e18`; they are the last two functions in the image and
  their role (some late-bound import/thunk table?) is not established.
