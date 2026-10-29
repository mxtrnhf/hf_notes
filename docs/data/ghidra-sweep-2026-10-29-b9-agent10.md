# Ghidra sweep 2026-10-29 — batch 9, agent 10 (documentation)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Role: consolidate documentation only. **No renames, no plates, no
`create_function`, no `save_program`, no tags, no commit.** Ghidra was connected
read-only only to verify the live names/bodies quoted below.

## Result

**0 renames.** Three documents touched/created:

| file | change |
|---|---|
| `docs/structures.md` | 31 withheld-name `.rdata` slots table; five `_CxxThrowException` primaries paragraph; Body slots 33/68/72/73 named and slot 72 forwarded to slot 71; batch-8 funclet owner list + 66-open split |
| `docs/data/rep-audit-2026-10-29.tsv` | rebuilt from `q1..q4` (de-duped, normalised, sorted) |
| `docs/data/rep-audit-2026-10-29.md` | batch-9 rebuild note, title, TODO for the post-append re-run |
| `docs/data/ghidra-changes-2026-10-29.md` | batch-9 assignment skeleton with `TODO (parent)` placeholders |
| this file | new |

## 1. `rep-audit-2026-10-29.tsv` rebuild

Rebuilt with the command documented in `rep-audit-2026-10-29.md` (header only
skipped when the first field is `addr`, `0x` normalisation, later row wins in
q1 -> q4 order, numeric sort). Snapshot at 14:40 MSK, **before** any batch-9
agent appended.

| | value |
|---|---|
| consolidated data rows | **1,496** |
| `renamed` | **430** |
| `stale label` | **1,065** |
| `unreadable` | **1** |

Identical to the batch-8 numbers: no q-file mtime moved after the batch-8
appends. Per-file state used:

| file | unique addrs | raw rows | verdicts after in-file de-dup |
|---|---|---|---|
| q1 | 513 | 1,415 | 74 renamed, 439 stale |
| q2 | 498 | 1,326 | 168 renamed, 329 stale, 1 unreadable |
| q3 | 383 | 446 | 72 renamed, 311 stale |
| q4 | 124 | 145 | 117 renamed, 7 stale |

Cross-file overlap: 22 addresses; 1,518 per-file uniques -> 1,496 consolidated.
The consolidated file in the worktree was rebuilt; the diff is a re-written
header + rows in sorted order, not new data.

**TODO (parent):** re-run the same block after batch-9 agents 4–7 append to
`q1..q4`, then refresh the count tables in `rep-audit-2026-10-29.md` and the
batch-9 `Counts` section.

## 2. Facts verified read-only in the live program

* **The five primaries are still stale `rep_*`.** `0x140336c80/d20/df0/ea0/f00`
  all still answer as `rep_..._VCRUNTIME140.DLL::_CxxThrowException`, body sizes
  0x3e / 0x3e / 0x3b / 0x59 / 0x3f. They decompile as container rethrow guards:
  destroy a range / deallocate / `memmove` the saved vector pointers back, then
  `_CxxThrowException(0,0)`. They are primary functions (own prologue and
  `UNWIND_INFO`, absent from the funclet-ownership TSV), which is what
  `structures.md` now records. Batch-9 agent 7 owns their rename.
* **All 31 withheld `.rdata` targets are still `FUN_*`** at the time of writing
  (checked each address with `get_function_by_address`). So `structures.md`
  lists their batch-8 vtable/slot + behaviour and marks the names as pending
  batch-9 agent 8, not as results.
* `FUN_14004c7e0` (Body slot `+0x240`) is still `FUN_*`, body
  `0x14004c7e0–0x14004c7e6` (7 bytes) — the two-instruction forwarder to slot 71.

## 3. `structures.md` edits

1. Body vtable table rows 33/68/73 now carry `Body_OnClick`,
   `Body_LinkAdjacentParts`, `Body_DrawMeshPolygon`; row 72 stays `FUN_*` with
   the forwarder note. The old "batch-8 slot agent is naming them" paragraph was
   replaced with the resolved names and the slot-72 reason; points at the
   batch-8 agent-9 note for the 16-table map.
2. New section **`.rdata` slots created with the name withheld (31)** after the
   D3D11 shader-layer summary: all 31 addresses + one-line recorded behaviour,
   with a `TODO (parent)` to replace the list with batch-9's proven names.
3. Funclet caveat: added the seven batch-8 proven owners, the 66-open split
   (31 container/allocator, 2 FX, 23 subsystem, 5 edge, 5 no-object) and the
   pointer to `ghidra-sweep-2026-10-29-b8-agent3.md` §3.
4. New **five `_CxxThrowException` primaries** paragraph: addresses, sizes, the
   frame offsets they destroy/revert, and that they are not funclets.

## 4. Batch-9 skeleton

`ghidra-changes-2026-10-29.md` gets a `## Batch 9: final tail` section with:
baseline line, a warning that every `TODO (parent)` is a placeholder, the
10-row assignment table copied from the blackboard, one bullet per worker
result, a dedicated **Corrections to existing names** table, the agent-10
documentation results, and `TODO (parent)` Counts / "What this wave
established". Nothing in it is a claimed result.

**Mid-wave rename protocol.** The blackboard gained a rule allowing an existing
name that is provably wrong/misleading to be renamed (ground rule 2 / §Rename
protocol). For documentation those are **corrections**, not new names: the
skeleton has an `old name -> new name + evidence + agent` table for them, and
the Counts placeholder says to exclude them from the newly-named total. No such
correction had been applied when this note was written (`rep_*` -> real-name
renames on unnamed functions, such as agent 2's two funclet owners, are *not*
corrections by that definition).

## 5. Placeholders left for the parent

* All batch-9 worker `result` cells and the `Worker results` bullets.
* The **Corrections to existing names** table (old -> new + evidence), once
  agents apply renames under the mid-wave rename protocol.
* Batch-9 `Counts` (objects/named/`FUN_*`/`rep_*`, renames, created, net).
* "What this wave established" and the final "Left for a later pass" list.
* The 31 withheld `.rdata` names in `structures.md` (batch-9 agent 8) and the
  slot-72 name (batch-9 slot/created agent).
* The post-append `rep-audit` re-run and refreshed counts.

## 6. Verification / hand-off

* No Ghidra mutation calls were made; only `get_function_by_address`,
  `disassemble_function` and `decompile_function` reads (five primaries and
  `FUN_14004c7e0`).
* The TSV rebuild was re-counted independently (`Counter` over the merged rows,
  per-file unique/raw counts, pairwise overlap) and matches the table above.
* Blackboard: `DONE agent10: ...` appended to `## Status`.
