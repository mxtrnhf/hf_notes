# Ghidra sweep, batch 9 agent 2 — open `/EH` funclets B

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: the open funclets in `0x140340000–0x140347FFF` from the batch-8
open-66 list (`/tmp/opencode/hf_ghidra_sweep/b8a3_open66_live.tsv`), owner-mapped
in `docs/data/funclet-ownership-2026-10-29.tsv`.

**Note on the count:** the batch-9 blackboard repeats "66 open funclets" for all
three funclet agents, but the 66 is the *total* after batch 8; the slices are
disjoint and this slice contains **21** of them (agent 1 has 35 in
`0x140336730–0x14033FFFF`, agent 3 has 10 in `0x140348000–0x140350510`).
All 21 in this slice have a function object (the five batch-8 `NOFUNC` rows are
all outside `0x140340000–0x140347FFF`).

**3 funclets named + plated (2 of them after proving and renaming their stale
owner); 18 remain open.** No `save_program`, no tags, no README/STATUS edits, no
commit, no non-funclet `rep_*` touched.

| | count |
|---|---|
| open funclets in this slice (batch-8 list, re-read live) | 21 |
| stale owners proven + renamed | **2** |
| funclets named + plated this pass | **3** |
| still open | **18** |
| … generic container/allocator helper | 10 |
| … subsystem procedure, area only | 5 |
| … edge case (unnamed owner / funclet-owns-funclet) | 3 |

## 1. Owners renamed (stale `rep_*` → real identity)

| owner | old stale label | new name | evidence from the body |
|---|---|---|---|
| `0x1402199e0` | `rep_1401fc690_Node::Node` | **`HistoryDesign_CreateFromCreature`** | Allocates `Node(0x128)` + `Node::Node`, copies the creature name from `this+0x560` into the node, runs `Body_RebuildSubtreeList`/`Roster_CopyIntoVolume`, then `New(0xc0)` + **`HistoryDesign_Constructor(node, …)`**. Sole nearby caller `0x140073200` (now `HistoryDesign_EnsureForCreature`, which clones a node by name or calls this) and `HistoryDesign_InitBaseFields 0x140073180` confirm the family. Only caller set: `!ClickFunc`, `0x140073200`, `0x1400da8b0`. |
| `0x14023c820` | `rep_14021e670_VCRUNTIME140.DLL::memmove` | **`Ship_RecreateFromBackup`** | Rebuilds a ship from a backup record: finds the creature by name (`memcmp`), frees the old body, `Body_RebuildSubtreeList`, `Creature_BroadcastCommand19A(3)`, recreates `Node(0x128)`, restores the name, and on failure logs **`RECREATE_SHIP_INNER_ERROR`**. Assert strings `main.cpp:0x6bf0/0x6bf7/0x6bfd`. Sole caller `loadShipBackups? 0x14023cd00`. |

Both were plated (summary / `Algorithm:` / `Parameters:` / `Returns:` + a note
that the owner identity was proven this pass).

## 2. Funclets named + plated (3)

| funclet | new name | owner | member | family | plate basis |
|---|---|---|---|---|---|
| `0x1403445b0` | `HistoryDesign_CreateFromCreature_EhCleanup_0xb8` | `0x1402199e0` | `0xb8` | freeField | body is `free(*(frame+0xb8))` — the HistoryDesign/Node temporary of the owner |
| `0x140345840` | `Ship_RecreateFromBackup_EhCleanup_0x68` | `0x14023c820` | `0x68` | freeField | body is `free(*(frame+0x68))` — the recreated Node temporary of the owner |
| `0x1403423c0` | `VectorString32_InsertRange_EhCleanup` | `0x14019abe0` `VectorString32_InsertRange` | — | rethrow | body moves the 0x20-byte string range back (`Array_MoveConstruct32String`), frees the wrapper, stores the rollback end and `_CxxThrowException`s. It touches `frame+0xa0/a8/b0/b8`, not one member, so **no `_0xNN` suffix was invented** (batch-8 edge case closed here because the owner name is proven). |

## 3. Still open — 18

Per-address `.pdata` evidence stays in `funclet-ownership-2026-10-29.tsv`.

### Generic container / allocator helper (10)

Owners are MSVC vector instantiations or tiny wrappers whose bodies only call
`New`/`free`/`memmove`/`Relocate_MoveConstruct*`/`vectorTooLong`. Their callers
use **different element types**, so any name would have to invent the template
argument. Verified in this pass:

| funclet | owner | member | family | caller set (why unnamed) |
|---|---|---|---|---|
| `0x1403410f0` | `0x14016f6a0` | `0x80` | rethrow | vector of 0x28-byte std::string growth (`Relocate_MoveConstruct40String`, `Array_DestroyStringRange40`); caller `Texture_LoadAllFromFolder` |
| `0x140341460` | `0x140183e00` | `0x60` | rethrow | `vector<u64>::_Change_array`; callers `Shipworks_BuildAutoRepairSteps`, `VectorPointer_PushBack`, `memmoveMAIN`, `InputTask` |
| `0x140341e10` | `0x140197510` | `0xa0` | rethrow | `vector<CHN*>` ctor; caller `playSoundsOfFallingDebris?` |
| `0x140341ef0` | `0x1401986f0` | `0x70` | rethrow | callers `Shipworks_BuildAutoRepairSteps`, `memmoveMAIN` |
| `0x140341f50` | `0x140198ac0` | `0x60` | rethrow | caller `renderDocksProcedurally?` |
| `0x140341fb0` | `0x140198eb0` | `0x70` | rethrow | caller `Precombat_BuildAmmoSelectorRow` |
| `0x140342030` | `0x1401993c0` | `0x80` | rethrow | caller `displayCharTraitsMouseOver` |
| `0x140342080` | `0x140199650` | `0x80` | rethrow | caller `Precombat_BuildAmmoSelectorRow` |
| `0x1403421b0` | `0x14019a0f0` | `0xa0` | rethrow | caller `playSoundsOfFallingDebris?` |
| `0x140342420` | `0x14019aeb0` | `0x80` | rethrow | caller `rep_1401fc9c0_New` |

### Subsystem procedure — area known, operation not provable (5)

| funclet | owner | member | family | state |
|---|---|---|---|---|
| `0x140345630` | `0x140237e30` | `0x60` | string | splits a string into space-separated words, pads each with `rightPadEscadraWithParam`, replaces `./,=;:-@` etc. with `_`, keeps `ceil(lines*ratio)` lines and emits an `EscadraName`. Used by the radio-sighting handler `0x1400eece0` and by `0x140238460`. No class/RTTI proof, so only "text wrap" is certain — not a name. |
| `0x140345690` | `0x140238460` | `0xa0` | string | tutorial radio/codes handler: `RADIO_SAVE`, `TUTORIAL_CODES`, `TUTORIAL_CODES_1`, `TUTORIAL_TRADER`, `PETR` NPC, `RadioBearing_`, sets the creature text at `+0xc10`; called only from `!ClickFunc`. Area (tutorial radio) is clear, the operation name is not. |
| `0x1403456c0` | `0x140238460` | `0x80` | string | same owner |
| `0x1403456f0` | `0x140238460` | `0xa0` | string | same owner |
| `0x140345b80` | `0x140253300` | `0x70` | string | tutorial enigma/alarm handler: `Dronish_descent`, `TUTORIAL_HUNTED`, `TUTORIAL_ALARM_1`, advances `enigmaGot1` and sets the enigma flags; callers `MapCraft_ReturnChildrenToParent`, `Get_Profile?`. Area only. |

### Edge cases (3)

| funclet | owner | member | family | reason |
|---|---|---|---|---|
| `0x140340ff0` | `0x14016bf00` `FUN_14016bf00` | `0x38` | freeField | owner is a created-but-unnamed batch-8 creation target assigned to agent 8; not renamed here |
| `0x140341220` | `0x14016bf00` `FUN_14016bf00` | `0x70` | freeField | same owner |
| `0x140342380` | `0x1403423c0` (now `VectorString32_InsertRange_EhCleanup`) | `0xa0` | rethrow | anomaly already in batch 6/8: the member `+0xa0` exceeds the owner's 89-byte body, i.e. a funclet whose "owner" is itself a funclet — no real identity |

## 4. Hand-off

* `0x140340ff0` and `0x140341220` unblock automatically once agent 8 names
  `0x14016bf00`; their funclet names then follow the owner name (`_0x38`, `_0x70`).
* `0x140342380` should stay unnamed: its `.pdata` owner record is corrupt/aliased.
* The five "area only" funclets need a caller-level proof of the operation (e.g.
  a vftable slot or a dispatch-table entry for `0x140238460` / `0x140253300`),
  not more body reading.
* No `structures.md` facts discovered beyond the two owner identities.
