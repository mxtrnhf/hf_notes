# Ghidra sweep 2026-10-29 — batch 8, agent 10 (documentation)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Role: consolidation only — **no renames, no `create_function`, no
`save_program`, no commits**. Baseline at the start of the wave: 5,251 function
objects, 3,772 named (71.83%), 197 `FUN_*`, 1,282 `rep_*`.

Result: **0 renames, 0 created**; three docs updated and this note written.
The wave was still running while this note was written; the only worker results
visible were agent 3 (7 funclets closed, 66 open) and agent 7 (15 `rep_*`
renamed). The batch-8 section of `ghidra-changes-2026-10-29.md` is therefore a
**skeleton with `TODO` for the remaining agents**, not a result.

## Files changed

| file | change |
|---|---|
| `docs/structures.md` | new **HGE RNG** subsection; Body slot +0x298 resolved to `Body_ClosePartInfoPanel`; the four unnamed slots now carry their recorded behaviour |
| `docs/data/rep-audit-2026-10-29.tsv` | rebuilt from `q1..q4` (normalise, de-dup by address newest-wins, sort) |
| `docs/data/rep-audit-2026-10-29.md` | rebuild stamp, current per-file row/verdict table, explicit `TODO` for the post-batch-8 rebuild |
| `docs/data/ghidra-changes-2026-10-29.md` | new **Batch 8** section skeleton (assignment table, creation requests, agent-10 results, `TODO` counts) |
| this note | — |

## 1. `.rdata` / HGE RNG (read-only verification)

The four HGE RNG targets (`0x1401742d0`, `0x140174310`, `0x140174320`,
`0x140174350`) had **no function object** at the time of writing; I read their
bytes with `read_memory` rather than decompiling them:

* `0x1401742d0` — `IMUL EAX,[0x1439e8688],0x343fd; SUBSS; ADD EAX,0x269ec3;
  MOV [0x1439e8688],EAX; SHR EAX,0x10; CVTSI2SS; MULSS [0x140366c18] (bits
  `0x37800080`, ~2^-16); MULSS range; RET` — float in a range.
* `0x140174310` — `MOV EAX,[0x1439e8688]; RET` — get state.
* `0x140174320` — `IMUL ECX,[0x1439e8688],0x343fd; ...; DIV R8D; LEA EAX,[R9+RDX]`
  — int in `[min, max)`.
* `0x140174350` — `SUB RSP,0x28; TEST EDX,EDX; JNZ store; CALL [0x140351660];
  store` — seed setter (arg, or the imported clock when the arg is 0).

So the state is a single **dword at `0x1439e8688`**, the generator is the MSVC
`rand` LCG (`0x343fd` / `0x269ec3`). The float variant returns roughly
`(state >> 16) / 65536` scaled by its argument (constant at `0x140366c18`); the
int variant mixes the high half with the new state before the `DIV` remainder.
`read_memory` at `0x1439e8688` fails byte-wise because it sits in the
zero-initialised part of the big `.data` block (`0x1403c6400–0x14807720f`) with
no file bytes — seed before use. This agrees with the agent-9 creation request
posted on the blackboard.

Agent 1's creation request carries the batch-8 `.rdata` family map (Creature
slot 9, `basic_ofstream` / `basic_filebuf`, `TextureSingle` / `RenderTarget`,
`Effect` / `IShader` slot 18, twelve `Shader*` tables, four
`std::function<float(float)>` lambda tables at `0x140092f30–0x1400930c0`,
`Intel` / `Launched` dtor slots, `MapShip@Escadra`, the property containers,
`Escadra` / `Location` slot 43, `MapShipBody` slot 58, `ShaderParam*New`). I
recorded the family list in the batch-8 section; I did **not** turn it into a
structures table because no target had been created yet.

## 2. Body slot semantics (structures.md)

* The old "Slot +0x298 conflict" paragraph was resolved using batch-7's caller
  proof: `0x14004bba0` is `Body_ClosePartInfoPanel`, a five-instruction
  forwarder to slot +0x48 of the cached panel at Body `+0x9d0`. The "projectile
  cleanup" reading is disproved.
* The four created-but-unnamed slots (33/68/72/73) now point at their recorded
  behaviour in the batch-7 agent-7 note, including that slot 72 is a pure
  forward to slot 71 with a 0.0f argument.
* No new Body offset was proved by batch 8 while I was watching; the batch-8
  body-slot agent (9) had not posted a result.

## 3. `rep-audit-2026-10-29.tsv` rebuild

Rebuilt with the documented de-duplicating script (q1 -> q4 order, newest row
per address wins, lowercase `0x`, numeric sort). Snapshot after the batch-8
agent-7 append (its 21 rows override existing q4 addresses):

* **1,496 data rows**: 321 `renamed`, 1,174 `stale label`, 1 `unreadable`.
* Per file (unique addresses / raw rows / verdicts after in-file de-dup):
  q1 513 / 1005 / 48 renamed + 465 stale; q2 498 / 946 / 114 + 383 + 1
  unreadable; q3 383 / 397 / 43 + 340; q4 124 / 145 / 117 + 7.
* The files overlap each other by 22 addresses (hence 1,518 in-file uniques ->
  1,496 rows). Cross-file de-dup drops one `renamed` (322 -> 321).

**Placeholder:** the parent must re-run the same rebuild after agents 4–6 append
their batch-8 rows and update the counts in `rep-audit-2026-10-29.md` and in the
batch-8 section.

## 4. Batch-8 section skeleton (ghidra-changes-2026-10-29.md)

The section states the baseline, the assignment table (10 rows; agents 3 and 7
carry the two worker results visible while I was running, agents 1–2/4–6/8–9 are
`TODO`, agent 10 "done"), the three creation requests as *requests* (agent 1:
46 targets, agent 2: 120, agent 9: 4), short summaries of the agent-3 and
agent-7 notes, the agent-10 documentation results, and a `TODO (parent)` counts
paragraph. It does not invent any worker counts and does not carry batch-7
totals forward as results.

## 5. Worker results folded

* **Agent 3** (`ghidra-sweep-2026-10-29-b8-agent3.md`): 7 of the 73 open
  funclets closed — 7 `rep_*` owners proven and renamed (`Fleet_CreateEscadraFromShips`,
  `Moral_BuildMiniFigPanel`, `Escadra_AddIntelEntry`, `Escadra_CopyFrom`,
  `Creature_AddLandingLights`, `Gui_CopyConstructor`, `Shader_AddParam`), 7
  funclets named + plated, **66 remain open** (31 container/allocator helpers,
  2 FX spawners, 23 subsystem procedures, 5 edge cases, 5 without a function
  object). New proof signal: the `FUNCINFO4` sized-delete operand equals the
  owner's `New(sz)` temporary.
* **Agent 7** (`ghidra-sweep-2026-10-29-b8-agent7.md`): 21 `rep_*` audited in
  `0x140300000–0x140336FFF`, 15 renamed + plated, 6 stale, 0 unreadable; q4 now
  has 145 data rows (all 21 were overrides of existing addresses, so the
  consolidated row count stayed at 1,496). Highest-value result: the
  `VideoTask_Dispatch` branch map to four scene renderers, plus the correction
  that `0x140334b70` / `0x140334c28` are C initialisers from
  `_initterm_e(0x1403521b8, 0x1403521e0)`, not `__scrt_*` main stages.

## Open items handed to the parent

1. Fold the remaining worker reports into the batch-8 table and replace the
   `TODO`s; keep creation *requests* distinct from creation *results*.
2. Settle the agent-3 vs agent-7 disagreement about `0x140336c80/d20/df0/ea0/f00`
   (funclet vs primary function ICF-aliased onto a funclet-shaped body).
2. Re-run the de-duplicating audit rebuild after the q1..q4 appends and refresh
   both count tables.
3. If batch 8 proves the D3DEngine dispatch object model or additional Body slot
   names, add them to `structures.md`; at the time of writing neither had landed.
