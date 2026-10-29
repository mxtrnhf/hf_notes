# Ghidra sweep batch 10 — agent 10 (documentation)

Program: `Highfleet.exe.unpacked.exe` v1.163 (read-only; no renames, no
`save_program`, no commit).

Baseline at the start of the wave: **5,422 function objects, 4,350 named
(80.23%), 93 `FUN_*`, 979 `rep_*`**.

## What I changed

| file | change |
|---|---|
| `docs/structures.md` | corrected the stale "five `_CxxThrowException` primaries" paragraph (batch 9 proved they are EH funclets, three already named after their owners); replaced the stale batch-8 `.rdata` TODO with the current state (only `0x14017c780`, `0x14017c800`, `0x14004c7e0` remain withheld); added the six `Cloud`/`Ground`/`Landpart` functionless-slot table and the vtable/spawn-object layout from batch 9; added the pending batch-10 funclet-owner block. |
| `docs/data/rep-audit-2026-10-29.tsv` | rebuilt from `q1..q4` with `0x` normalisation, de-duplication by address (newest row wins, order q1 -> q4), numeric sort and the header row restored. |
| `docs/data/rep-audit-2026-10-29.md` | header now says rebuilt in batches 7, 8, 9 and 10; added the batch-10 rebuild snapshot paragraph. |
| `docs/data/ghidra-changes-2026-10-29.md` | added the **Batch 10** skeleton section (assignment table, worker-results TODO, documentation results, counts TODO). |
| `/tmp/opencode/hf_ghidra_sweep/blackboard_b10.md` (outside the repo) | appended the `DONE agent10` status line. |

## Audit rebuild snapshot

Rebuild run at ~15:40 MSK, **before** the batch-10 `rep_*` agents appended their
rows (all four q-files still had their batch-9 content, mtime 15:16):

* q1 1,809 raw rows -> 513 unique; q2 1,652 -> 498; q3 546 -> 383; q4 151 -> 124.
* raw rows **4,158**, unique addresses **1,496**, 22 cross-file overlaps.
* verdicts **593 `renamed` / 903 `stale label` / 0 `unreadable`** — unchanged
  from the batch-9 totals.
* The only byte-level change from the previous consolidated file is the restored
  header row (`addr<TAB>old_label<TAB>verdict<TAB>new_name_or_identity<TAB>evidence`),
  which the batch-9 rebuild had dropped.

**TODO (parent):** after agents 3–6 append, re-run the command documented in
`rep-audit-2026-10-29.md` and refresh both count tables. The rebuild is safe to
re-run in place (append-only q-files, later row wins).

## Live program checks (read-only)

* `switch_program` confirmed `Highfleet.exe.unpacked.exe v1.163`
  (`D:/Games/Highfleet/Highfleet v1.163/Highfleet.exe.unpacked.exe`, base
  `0x140000000`). Never switched to the 1.151 program.
* `list_functions` at ~15:40 still reported 5,422 rows: 4,349 named, 94
  `FUN_*`, 979 `rep_*` (one extra `FUN_*` fragment vs the 93 baseline).
* `get_function_by_address` on the batch-10 targets at ~15:40:
  `0x14017c780`, `0x14017c800`, `0x14004c7e0` were still `FUN_*`;
  `0x1402e3580` and `0x1403182a0` were still stale `rep_*`; the six
  `Cloud`/`Ground`/`Landpart` slot addresses still had **no function object**.
  So no batch-10 worker result was available to fold when the skeleton was
  written.

## Placeholders left for the parent

1. **Batch 10 assignment table** — every worker row is `TODO`; agent 10's row is
   `done (below)`.
2. **Batch 10 worker results** — the whole subsection is a TODO paragraph.
3. **Batch 10 counts** — post-wave totals and the rename/create delta are TODO;
   only the baseline is a real number.
4. **`structures.md` batch-10 pending blocks** — (a) the funclet owner classes /
   funclet→owner pairs from agents 1–2; (b) the exact slot column and the six
   names for `0x1402f4b70`, `0x1402f4500`, `0x1402f4140`, `0x1402f4d90`,
   `0x140316150`, `0x1403365ac`; (c) the three withheld names.
5. **Audit counts** — re-run the rebuild after the batch-10 q-appends; the
   1,496 / 593 / 903 / 0 figures are the pre-append snapshot.

No renames, no creations, no plates, no tags, no `save_program`.
