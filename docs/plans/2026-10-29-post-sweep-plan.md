# Post-sweep plan — Highfleet 1.163 RE coverage

Date: 2026-10-29. Baseline from the saved program
`Highfleet.exe.unpacked.exe v1.163` (project `HighfleetServer`).

## Current state

| Metric | Count |
|---|---:|
| Function objects | 5,430 |
| Named | 4,502 |
| **Unnamed** | **928** |
| — `FUN_*` | 80 |
| — `rep_*` | 848 |
| Coverage | 82.91% |

Remaining composition (agent estimates from batches 9–10):

| Class | Share | Nameable? |
|---|---|---|
| CRT / compiler glue (`memcpy`/`free`/`sqrt` wrappers, EH funclets, `__scrt_*`, thunks) | ~40% | mostly no — naming duplicates a target or adds noise |
| Container / allocator instantiations (`vector<T>`, RB-tree, stride-N emplace) | ~30% | yes when the element type/stride is provable |
| Subsystem bodies with an unread class/field map | ~20% | yes after `structures.md` is extended |
| Genuinely ambiguous / corrupt records | ~10% | no — record and close |

The audit already holds per-address evidence:
`docs/data/rep-audit-2026-10-29.tsv` (1,496 rows: 685 renamed, 811 stale) and
`q1..q4.tsv` (raw rows).

## Definition of done

Not 100% named. Done means:

1. every remaining unnamed function is either **named** or **classified** in a
   family table with a one-line reason (CRT / container / ambiguous);
2. the 40 open funclets are resolved or proven ownerless;
3. `docs/structures.md` contains every class/field map needed to name the
   subsystem 20%;
4. the changes doc and audit TSV are consistent with the live program;
5. the program is saved and the notes pushed.

## Phase 0 — classification pass (1 agent, ~0.5 day)

**Why first:** address-order sweeps are exhausted; the remainder is a small
number of families. Classify before naming.

1. For all 928 unnamed functions, dump: entry, size, current name, callees,
   string refs, referenced vtables, element stride (from `New`/alloc size and
   index scaling), and the owning region.
2. Cluster into families (same callee signature + stride + string cluster).
3. Write `docs/data/unnamed-classification-2026-10-30.tsv` and a summary in
   `docs/findings/` with per-family counts and a verdict: `nameable`,
   `needs structures`, `CRT noise`, `ambiguous`.
4. Pick the top 5 families by count × nameability for Phase 2.

**Exit:** a family table with counts; no renames required in this phase.

## Phase 1 — funclet close-out (2 agents, ~0.5 day)

1. **Owner walk (1 agent):** implement `FuncInfo4 -> FuncInfo -> UnwindMap`
   (the batch-10 agent 2 note documents the failing case `0x140342380`), map
   the 40 open funclets to owners, rename/create in bulk, and update
   `funclet-ownership-2026-10-29.tsv`.
2. **CRT EH glue (1 agent):** `0x14034b6b8`, `0x14034b743`, `0x14034b75b` and
   the `__scrt_*`/padding stragglers — name only distinct roles; record the
   rest as compiler glue.

**Exit:** open funclets either named or documented as ownerless.

## Phase 2 — family naming (5 agents, ~1–2 days)

Partition by **family**, not address range:

| agent | family |
|---|---|
| 1 | container/allocator instantiations with a provable stride/type |
| 2 | subsystem accessors unlocked by the structures map (Body/Part/Profile) |
| 3 | sound / video / HUD / render helpers |
| 4 | economy / shop / loadout / UI builders |
| 5 | CRT / `rep_*` wrong-label corrections still provable from the body |

Rules: rename a whole family from one proven pattern (`VectorStride40_InsertMove`,
`DtorGlobal_*`); one plate template per family with the member/stride filled in;
skip anything whose element type or owner class is unproven. Expected yield:
200–400 names. Rebuild the audit TSV after each family.

## Phase 3 — last game logic (1 agent, ~0.5 day)

The 80 `FUN_*` minus the funclets: `0x140073340`, `0x1400a6210`,
`0x1400f51c0`, `0x1400bee20`, `0x1400fdec0`, split `CopyEscadraName`
fragments, padding. Extend `structures.md` for a field before naming its
accessor; otherwise classify and close.

## Phase 4 — docs and close (1 agent, ~0.5 day)

1. Rebuild `rep-audit-2026-10-29.tsv` from the q-files; refresh
   `rep-audit-2026-10-29.md`.
2. **Remove the duplicated Batch-7 section** in
   `docs/data/ghidra-changes-2026-10-29.md` (it appears twice, around the
   batch-7 and batch-10 sections) and re-check the final counts paragraph.
3. Update `structures.md`, `STATUS.md`, `README.md`.
4. Save the program, commit, push (user checks in Ghidra).

## Guardrails

* **1.163 only** — never write to `Highfleet.exe.unpacked.exe v1.151`.
* Wrap any `startTransaction` in `try/finally`; a leaked transaction blocks
  `save_program` (see `RE_SUBAGENT_INSTRUCTIONS.md`).
* Agents do not `save_program`/commit; the parent saves once.
* Plate style: summary / `Algorithm:` / `Parameters:` / `Returns:`.
* Proof bar: body, RTTI/vtable, callees or strings. Skip rather than guess.
* Wrong/misleading names may be corrected via the posted rename protocol.

## Success estimate

Realistic plateau: **~86–88%** (≈120–200 more names), with the rest
classified as compiler/container noise. Chasing 100% would mean naming
hundreds of identical CRT clones, which we deliberately do not do.
