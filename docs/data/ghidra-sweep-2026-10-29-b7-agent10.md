# Batch 7, agent 10 — documentation and consolidation

Role: documentation only. **No renames, no `create_function`, no
`save_program`, no commit, no README/STATUS edits.** Everything here is either
a rebuild of an existing table or a read-only check against the live program
(`Highfleet.exe.unpacked.exe v1.163`, project `HighfleetServer`).

Written 2026-10-29 13:15 MSK, while the rest of the wave was still running.

## What the wave looked like from here

At the time of writing:

* the batch-7 blackboard `Status` had **no `DONE agentN` line**;
* no `ghidra-sweep-2026-10-29-b7-agent*.md` note existed;
* `rep-audit-2026-10-29-q{1..4}.tsv` still had their batch-6 row counts
  (514/498/362/50 lines including the headers that q1 and q3 carry), i.e. no
  batch-7 re-match rows had been appended.

So the batch-7 section in `ghidra-changes-2026-10-29.md` is a **skeleton**:
assignment table + verified documentation results + `TODO` for every result. It
does not quote a single count for agents 1–9.

## Changes made

### 1. `docs/structures.md`

* **New `### Body vtable slot map 0x140352a30`** under the Body section.
  Verified by reading the `.rdata` table: slot 0 at `0x140352a30` =
  `0x140018b60`, RTTI CompleteObjectLocator in the qword before it
  (`0x140352a28` -> `0x140379a98`). All 19 addresses from the batch-6
  "Body/Node slots" list are slots of this one table, so the offset of each is
  now pinned:

  | slot | offset | target |
  |---|---|---|
  | 0 | +0x0 | 0x140018b60 |
  | 24 | +0xc0 | 0x14002e300 |
  | 25 | +0xc8 | 0x14002e290 |
  | 33 | +0x108 | 0x140018fb0 |
  | 48 | +0x180 | 0x14001bf60 |
  | 49 | +0x188 | 0x14001b7f0 |
  | 53 | +0x1a8 | 0x140049e10 |
  | 54 | +0x1b0 | 0x14004a560 |
  | 56 | +0x1c0 | 0x14004a9f0 |
  | 57 | +0x1c8 | 0x14004a8b0 |
  | 58 | +0x1d0 | 0x140048020 |
  | 65 | +0x208 | 0x140051de0 |
  | 67 | +0x218 | 0x140019300 |
  | 68 | +0x220 | 0x140053110 |
  | 72 | +0x240 | 0x14004c7e0 |
  | 73 | +0x248 | 0x14004d8e0 |
  | 78 | +0x270 | 0x140054dd0 |
  | 83 | +0x298 | 0x14004bba0 |
  | 87 | +0x2b8 | 0x14004eaa0 |

  Corroboration: +0x208 (`0x140051de0`) tests the byte at +0x2d0 and the float
  at +0x2c8, i.e. the documented health pair — consistent with "set health".

* **+0x298 name conflict recorded, not resolved.** Batch 6 called
  `0x14004bba0` `Body_ClosePartInfoPanel` (and separately called slot +0x298
  "projectile cleanup"). The body is:

  ```
  MOV RCX, [RCX+0x9d0]
  TEST RCX, RCX
  JZ  ret
  MOV RAX, [RCX]
  JMP qword ptr [RAX+0x48]      ; kill/remove slot of the +0x9d0 object
  ```

  A forwarder to slot +0x48 of the object at `+0x9d0`. Both proposed names are
  unsupported as written; structures.md now says so and flags a caller read.

* **New `## CRT C-initialiser table 0x1403519e0–0x1403521a8`.** Verified: the
  run is **249 pointers / 0x7c8 bytes** and starts one qword *before* the
  batch-6 hand-over address `0x1403519e8`. Breakdown: 247 targets in
  `0x140001000–0x140004a60`, 1 null entry, 1 target `0x140334c38` in the
  funclet tail. Entry shape is mixed:
  * stub `LEA RCX,[global]; JMP ctor` — e.g. `0x140004a5c` =
    `LEA RCX,[0x140350510]; JMP 0x14033447c`;
  * full C++ constructor — e.g. `0x140001000` allocates 0x40 bytes, calls
    `0x140334094`, then `LEA RCX,[0x14034b780]`, and can initialise several
    globals in one body.

  Consequence documented: `CInit_<Global>` is mechanically derivable only for
  the stub subset; the full-constructor entries need their globals read from
  the body. The family split is left to agent 6 / the parent (`TODO`).

* Funclet owner classes: no new class/owner fact was available (agent 1 had not
  landed), so structures.md's existing funclet section is unchanged. `TODO`.

### 2. `docs/data/rep-audit-2026-10-29.tsv`

Rebuilt from `q1..q4`:

* header row kept, `addr` normalised to lowercase `0x` (q1–q3 were bare hex,
  q4 had `0x`);
* de-duplicated **by address, newest row wins** (q1 -> q4 order, so a later
  re-match overrides an earlier verdict); today there are no duplicate
  addresses, so this only future-proofs the batch-7 appends;
* sorted by address.

Result: **1,421 data rows — 131 `renamed`, 1,289 `stale label`, 1
`unreadable`**. The previous file had 1,420 rows / 130 renamed: the batch-6
merge had lost q2's **first** row `0x140100c30` (`Explosion_AddProperty`,
`renamed`) because q2 has no header and the merge trimmed its first line as if
it did. No other row changed (checked row-by-row against the previous file).

Note kept in the `.md`: the agents' `DONE` totals sum to 132 renames
(21 + 49 + 34 + 28), one more than the TSV's 131; the remaining gap is agent
5's q4 worklog row that never reached the TSV. The batch-6 live check that all
131 tabulated renames exist still stands.

### 3. `docs/data/rep-audit-2026-10-29.md`

* Title now notes the batch-7 rebuild.
* Contents table updated to 1,421 / 131 / 1,289 / 1 and per-file rows to
  q1 513, q2 498, q3 361, q4 49.
* Documents the dropped-q2-row bug and its fix.
* Rebuild recipe replaced with the de-duplicating Python version (the old
  `head -1 | grep '^addr'` shell recipe is what caused the q2 loss).
* Source-file table is described as append-in-place sources for batch 7.

### 4. `docs/data/ghidra-changes-2026-10-29.md`

Inserted `## Batch 7: ...` before `## `!` functions`: intro, "skeleton, not a
result" warning, the ten-row assignment table with `TODO` results, the
completed documentation results, and a `TODO` list of the five points the
parent must reconcile (funclet completion, CInit families, Body/Node slot
names + the +0x298 question, audit-TSV delta, program totals + "Left for a
later pass").

## What remains a placeholder

* Every result cell for agents 1–9 in the batch-7 table.
* "What this wave established" for batch 7 — all five bullets are `TODO`,
  including the post-wave program totals.
* CInit family split / first three families, and the identity of the
  `0x140334c38` table entry.
* The +0x298 / `0x14004bba0` name (evidence says it is a kill-forwarder, not
  `Body_ClosePartInfoPanel`; needs a caller read before naming).
* Which of the 19 slots are declared on Node vs Body (needs the Node base
  vtable; the offsets in the Body table are not proof of the declaring class).
* The batch-7 audit appends: when they land, re-run the recipe in
  `rep-audit-2026-10-29.md` and update its counts plus the batch-7 section.

## Commands worth reusing

```sh
# audit rebuild (also embedded in rep-audit-2026-10-29.md)
python3 - <<'PY'
... see that file ...
PY
```

Read-only Ghidra reads used: `read_memory` at `0x1403519d0` (+0x240),
`0x1403519e0` (+0x7c8), `0x140352980` (+0x220), `0x140352a30` (+0x600);
`get_function_by_address` on the 19 slots (all "No function found" at 13:1x);
`disassemble_bytes` at `0x140001000/40/80`, `0x140004a5c`, `0x14004bba0`,
`0x140051de0`.
