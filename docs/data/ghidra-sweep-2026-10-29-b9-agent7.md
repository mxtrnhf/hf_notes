# Ghidra sweep 2026-10-29 — batch 9, agent 7 (`rep_*` D + the "five primaries")

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: remaining `rep_*` with entry in **0x140300000–0x140350510**, excluding
addresses already mapped in `funclet-ownership-2026-10-29.tsv`.

## Counts

| | count |
|---|---|
| `rep_*` function objects in 0x140300000–0x140350510 at start | **105** |
| … of those already in `funclet-ownership-2026-10-29.tsv` (excluded by scope) | **99** |
| effective slice | **6** |
| renamed + plated this pass | **3** |
| stale label (sharpened) | **3** |
| unreadable | **0** |
| `rep_*` left in slice | **3** |

The 99 excluded rows are the funclet map's (`0x1403372d0`…`0x14034b75b`); they
were not touched. After the pass the range holds **102** `rep_*` function
objects, of which **3** are in my effective slice and all 3 are recorded stale.

Appended **6 data rows** to `rep-audit-2026-10-29-q4.tsv` (file now 152 lines /
151 data rows, still 5 columns). Prior rows were not rewritten.

No `save_program`, tags, README/STATUS edits, commits or `create_function`.

## The "five primaries" are EH funclets — correction to the batch-9 brief

The brief states that `0x140336c80`, `0x140336d20`, `0x140336df0`,
`0x140336ea0`, `0x140336f00` are "real functions with stale
`_CxxThrowException` labels (own `UNWIND_INFO`), not funclets". That premise is
wrong. Evidence, all re-checked live in this pass:

1. **No caller.** Every one of the five has exactly one reference in the whole
   program: a `DATA` reference from its own `.pdata` `RUNTIME_FUNCTION`. There
   is no `CALL`, no pointer table entry, no vtable slot.
2. **Funclet prologue/epilogue.** Each body is
   `MOV [RSP+0x10],RDX / PUSH … / SUB RSP,.. / MOV RBP,RDX`, then cleanup
   calls, then `XOR ECX,ECX; XOR EDX,EDX; CALL _CxxThrowException; INT3`.
   RDX is the establisher frame, and `_CxxThrowException(0,0)` is the MSVC
   rethrow path — the shape of a catch/cleanup funclet, not of a callable
   primary.
3. **Their own `UNWIND_INFO` has `Flags = 0`** (no `EHANDLER`/`UHANDLER`) and
   3–4 unwind codes; primaries that own EH data carry the handler flag and a
   `__CxxFrameHandler4`/FuncInfo4 pair.
4. **Neighbourhood.** All five sit in the funclet-only band
   `0x140336b00–0x140336f80`, next to already-named
   `EhCleanup_Shared_freeField_77/78` (`0x140336b00/b20`) and
   `0x140336cf0 Vector16_InsertReallocate_EhCleanup_0x70`.

"Own `UNWIND_INFO`" is a true but non-discriminating observation: every
secondary funclet also has its own `.pdata` `RUNTIME_FUNCTION`/`UNWIND_INFO`.
The distinguishing field is the handler flag, which is clear here.

## Owner recovery from the FuncInfo4 funclet list

`__CxxFrameHandler4` is at `0x140336594`. For a function with C++ EH, the
`UNWIND_INFO` has `flags & 1`, and after its unwind codes come
`[handler RVA = 0x140336594][FuncInfo4 RVA]`. The FuncInfo4 is a **compressed
stream** (no `0x19930522` magic anywhere in this file); the funclet table is a
run of 4-byte RVAs interleaved with 1-byte fields inside it. For the five, the
FuncInfo4 holding the funclet RVA is unique to one pdata owner each (no
ICF sharing):

| funclet | funclet-list location | FuncInfo4 | owner UNWIND_INFO | owner | owner's live name |
|---|---|---|---|---|---|
| `0x140336c80` | `0x140385d7c` (+0x18) | `0x140385d64` | `0x140385d48` | `0x1400118a0` | `Vector24_InsertReallocate` |
| `0x140336d20` | `0x140385de4` (+0x18) | `0x140385dcc` | `0x140385dac` | `0x140012030` | `VectorString56_InsertReallocate` |
| `0x140336df0` | `0x140386084` (+0x18) | `0x14038606c` | `0x140386050` | `0x140012c20` | `VectorString_InsertReallocate` |
| `0x140336ea0` | `0x1403861e4` (+0x34) | `0x1403861b0` | `0x140386194` | `0x140013160` | `rep_…_Change_array` (unnamed) |
| `0x140336f00` | `0x1403861eb` (+0x3b) | `0x1403861b0` | `0x140386194` | `0x140013160` | `rep_…_Change_array` (unnamed) |

Cross-check of the method against the existing map: for the known row
`0x1403372d0` (owner `0x140017e70`, ICF-shared with `0x140023ac0`) the
`funcinfo4@0x140383108` value in the TSV is the **address of the pointer
field**, whose value is the FuncInfo4 `0x14038310c`; the funclet RVA sits at
`0x140383117` (+0xb) in that record. So the TSV and this pass use the same
structure; offsets inside the compressed list vary (0x0b–0x3b) because the
preceding fields are variable-length. Beware: a raw 4-byte scan for a funclet
RVA can also hit deep offsets (+0x250) in unrelated FuncInfo4 blobs — only
small offsets that continue an ascending funclet run are real list entries.

## Renamed (3), all plated

| addr | old name | new name | proof |
|---|---|---|---|
| `0x140336c80` | `rep_14030bd40_VCRUNTIME140.DLL::_CxxThrowException` | `Vector24_InsertReallocate_EhCleanup_0x70` | owner `0x1400118a0` `Vector24_InsertReallocate`; body `Array_DestroyRange24(+0x70,+0x88,+0x28)`, `deallocate(+0x70,+0x78,+0x80)`, rethrow; member `+0x70` |
| `0x140336d20` | `rep_14030be30_VCRUNTIME140.DLL::_CxxThrowException` | `VectorString56_InsertReallocate_EhCleanup_0xd0` | owner `0x140012030` `VectorString56_InsertReallocate`; body cleanup wrapper `(+0xd0,+0x40,+0x50)`, `DeleteArray56(+0xd0,+0x58,+0x48)`, rethrow; member `+0xd0` |
| `0x140336df0` | `rep_14030d150_VCRUNTIME140.DLL::_CxxThrowException` | `VectorString_InsertReallocate_EhCleanup_0x70` | owner `0x140012c20` (already named); body `EhCleanup_FreeWrapper(+0x70,+0x78,+0x20)`, `DeleteArray32(+0x70,+0x28,+0x88)`, rethrow; member `+0x70` |

Owners `0x1400118a0` and `0x140012030` were **outside my scope**
(`0x140000000–0x1400FFFFF`, agent 4). I did not rename them; I posted the
identities to agent 4 on the blackboard at 14:50 and agent 4 renamed them to
exactly those names before the second rename cycle, which is what made the two
funclets nameable. `0x140012c20` was already named before this batch.

Plates follow the batch-6/7 funclet template (owner, member, family, algorithm,
parameters, returns) and end with the funclet-list addresses and the old label.

## Left stale (3), sharpened

| addr | reason |
|---|---|
| `0x140336ea0` | Funclet of **`0x140013160`**, the `vector<unsigned __int64>` range-insert / `_Change_array` replica, which is still `rep_*`. The owner has no provable identity (b8 agent 3 had already classed it as a generic vector helper); naming the funclet would have to invent the owner name. Member `+0x98`, family `freeField`; body does the 0x88/0x38 memmove pair then writes `[+0x98]=[+0x28]` before the rethrow. |
| `0x140336f00` | Second funclet of the **same** owner `0x140013160` (same FuncInfo4 `0x1403861b0`, RVA at +0x3b). The short variant of `0x140336ea0` (one memmove-wrapper call). Member `+0x98` — a name would also need a `_2` disambiguator against `ea0`. |
| `0x1403182a0` | `_Xtime_get_ticks`-based post-spawn guard: state `{uint interval; uint lastMs; qword handle}` at `QWORD_1403c2d78`; `elapsedMs=(now-_currentTimeData_)/10000`; if the handle is set and `elapsedMs-lastMs<=interval` it returns nonzero, otherwise it stores the handle/`lastMs` and returns the sign bit (0). At `BattleSpawner_SpawnShips` (`0x1402d1a60`, line 304) the result selects `ShipLink_SnapAllBodies` vs `Ship_CanFireAt`/`Creature_BroadcastCommand19A`/`Creature_SpawnRecalculateStats`; also used from `0x1402d2d00` and `Battle_DeployFromReserve` (`0x1402d22e0`). Spawn cadence is clear, the exact unit/polarity/return contract is not — left stale rather than guessing `*_CheckInterval`. |

## Hand-off

* `0x140013160` (owner of `0x140336ea0`/`0x140336f00`) is in agent 5's range
  (`0x140100000–0x1401FFFFF`). Posted to agent 5; once renamed, both funclets
  can be completed mechanically (`…_EhCleanup_0x98` and `…_EhCleanup_0x98_2`).
* The batch-9 premise line for agent 7 in the Assignment table should be
  corrected: these five are funclets, and the effective slice was 6, not ~105
  (99 of the 105 are already owned rows in the funclet TSV).
