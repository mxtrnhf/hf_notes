# Ghidra sweep 2026-10-29 — batch 6, agent 10 (documentation / consolidation)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Role: documentation only. **No renames, no `create_function`, no `save_program`,
no tags, no README/STATUS edits, no commit.** Ghidra was used read-only (a
`get_function_by_address` sweep over the HGE vtable slot targets) to confirm
which slots already have a function object.

## Files changed

| file | change |
|---|---|
| `hf_notes/docs/structures.md` | eight edits, listed below |
| `hf_notes/docs/data/ghidra-changes-2026-10-29.md` | new "Batch 6" section skeleton (placeholders only) |
| `hf_notes/docs/data/rep-audit-2026-10-29.md` | new — one-line format note + provenance for the consolidated TSV |
| `hf_notes/docs/data/rep-audit-2026-10-29.tsv` | consolidated audit table (see "Audit TSV" below) |
| `hf_notes/docs/data/ghidra-sweep-2026-10-29-b6-agent10.md` | this note |

## `structures.md`

1. **Stats record** — added `+0xdc` power (`ED_PROP_POWER`), `+0xe8` ammobox
   (`m_mdl_ammobox`, `ED_PROP_AMMOBOX`), `+0xf0` ammobox priority
   (`ED_PROP_AMMOBOX_PRI`), `+0x108` rotation (`ED_PROP_ROTATION`), plus the
   now-documented `+0xe4` power_priority neighbour. Added a provenance
   paragraph: each field is proved twice (the `ED_PROP_*` display branch in
   `setupPropsSecondaryMapModes` and the `populateObjects` seria-key table) and
   named the four getters (`ShipStats_GetPower` 0x14015f840,
   `ShipStats_GetAmmobox` 0x14015f7b0, `ShipStats_GetAmmoboxPriority`
   0x14015f7e0, `ShipStats_GetRotation` 0x14015f8a0).
2. **Body vtable slots** — the vtable paragraph now lists +0xe8 world position,
   +0xf0 local angle -> world, +0xf8 local point -> world, +0x150 dropped-link
   collector, +0x208 set health and +0x298 projectile cleanup. It also states
   that `0x1480xxxx` xrefs are `.pdata`/unwind, not vtables, so they do not
   identify a class.
3. **New "Per-player input record" section** — stride 0xf0, player index +0xe4,
   pad type +0xe8, move vector +0x10, and the six held flags in their real
   address order: +0xde up, +0xdf left, +0xe0 down, +0xe1 right, +0xe2 rotate
   left, +0xe3 rotate right (note: **not** up/down/left/right in address order;
   this was checked against `Input_RebuildMoveVector` before writing). Names the
   readers and records that Q-vs-E assignment is still open.
4. **New "HGE vtable" section** — slot map for 0x1403672f0: +0x90/+0x98 file
   data load/free, +0x138/+0x140 sound, +0x160/+0x168/+0x178/+0x180 music,
   +0x1c0/+0x1c8 stream, +0x1e8 channel frequency, +0x2e0 quad render,
   +0x300/+0x308 factories, +0x310 `Texture_Load`, +0x320 float->int adapter.
   Verified live: +0x2e0 now resolves to the created `Gfx_RenderQuad`
   (0x14016cc80), while +0x310 still carries the wrong
   `rep_140161260_USER32.DLL::MessageBoxA` name and +0x300/+0x308 still have no
   function object. The table says so instead of implying all slots are named.
5. **New "D3D11 shader layer" subsection** — the 29 `Shader*` classes, the
   `Effect` hierarchy, `ConstantBuffer<CBConstants<...>>`, the
   `ShaderData`/`ShaderParam*New`/`ShaderResourceView` family, the concrete
   shader slot convention (1 dtor, 2 Init, 8/9 emit) and a pointer to
   `data/ghidra-sweep-2026-10-29-b3-agent1.md` for the per-class table.
6. **New "Box2D build quirks" section** — `b2Pair` is **12 bytes** here (buffer
   at broadphase+0x40, count +0x4c, indexed `*3*4`), plus the six-slot joint
   vtable order, the two-slot contact tables and the seven-method
   `b2ContactSolver`. Links to `findings/box2d-function-map.md` and
   `findings/box2d-struct-layouts.md`.
7. **New "Naming caveats" section** — the `rep_*` caveat (0/207 byte-identical
   twins, 174/199 embedded targets inside unrelated bodies, four concrete
   wrong-label examples) and the `/EH` funclet summary (shape, why the owner
   comes from `.pdata` + the FH4 `FuncInfo4` funclet list at `0x14808a000`, the
   `<Owner>_EhCleanup_<member>` convention, pointer to
   `funclet-ownership-2026-10-29.tsv`). Counts filled from agent 1's TSV and
   note after it landed: 926/926 funclets owned, 347 owners, 97 ICF-shared, 165
   without a function object, 448 renamed, 176 left with a recorded owner.
8. **Creature fields** — added `+0x15d0` ship total value (single writer
   0x14007171d, from agent 6) and `+0x8f8` GUI alpha (the halve/restore pair,
   guard `+0xc7c`). Both were on the "unknown field" list in the batch-4/5 notes.

## Audit TSV

`rep-audit-2026-10-29.tsv` is the concatenation of the four per-agent tables
`rep-audit-2026-10-29-q{1,2,3,4}.tsv`, in q1 -> q4 order, one header row,
columns `addr<TAB>old_label<TAB>verdict<TAB>new_name_or_identity<TAB>evidence`.
Provenance, the rebuild command and the per-file stats are in
`rep-audit-2026-10-29.md`.

All four files existed by the end of the pass, so the TSV was produced:
**1,420 rows** — 130 `renamed`, 1,289 `stale label`, 1 `unreadable`; every row
has exactly 5 tab-separated columns (checked). Per file: q1 513/21, q2 497/48,
q3 361/34, q4 49/27. The agents' `DONE` lines quote 49 and 28 renames for q2/q4,
i.e. two more than the rows carrying verdict `renamed`; that discrepancy is
recorded for the parent rather than silently reconciled.

## `ghidra-changes-2026-10-29.md`

Added a "Batch 6: structural + volume (same day) — SKELETON, parent to finalise"
section between Batch 5 and the `!` functions section: the 10-agent assignment
table (role + scope + result), a program-count line, a "Results by agent" list
and a "What this wave established" list. The table and the results list were
filled from the `DONE` lines and notes of agents 1–5 and 7–9 after they landed;
agent 6 was folded in at the end. **Still `TODO`:** the program totals (named /
`FUN_*` / `rep_*` after the wave) and the last "what this wave established"
bullet, which need the parent's reconciliation. The wave intro at the top of the
file ("ran in five waves", the 822/1,579/2,483 counts) was **not** touched —
the parent should update it together with the TODO counts.

## Left for the parent

1. Fill the program totals in the Batch 6 section (named / `FUN_*` / `rep_*`
   after the wave) and the closing "what this wave established" bullet, and
   update the intro paragraph counts ("ran in five waves" -> six).
2. Reconcile the two-row difference between the q2/q4 `DONE` rename totals
   (49 + 28) and the TSV rows with verdict `renamed` (48 + 27).
3. `0x14016cd50` still needs its `rep_..._MessageBoxA` label replaced with
   `Texture_Load` (agent 8 proved the body; renaming was outside its brief and
   outside mine). Same for `0x140324330` (`b2Island_SolveTOI`).
4. Two new hand-offs from agent 9: the CRT C-initialiser table
   `0x1403519e8–0x1403521a8` (150 targets, `CInit_<Global>` is provable) and the
   19 Body/Node base-class vtable slots with no function object.
