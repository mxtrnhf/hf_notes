# Ghidra sweep 2026-10-30 — parent (Phase 0/1 window)

Program: `Highfleet.exe.unpacked.exe` v1.163 only.

## Renames by the parent while Phase 0/1 ran

| address | old | new | proof |
|---|---|---|---|
| 0x1401783c0 | `FUN_1401783c0` | `ResDesc_CopyBaseFields` | shared callee of all eight per-type `ResDesc_*_CopyFields` routines; copies bytes +0x08..+0x87, dword +0x88, qwords +0x90/+0x98, skips the vtable at +0x00 |
| 0x1400458c0 | `FUN_1400458c0` | `Frame_BuildLinkList` | sole call site `Editor_RebuildGlobalLinkLists` (class 4–6 branch); body uses `Frame_ClassifyPartMix`, `Link_ConstructFromBody`, `Link_CopyConstructor`, `RbTree_InsertLinkByFloatPair`, body vtable +0xe8; inserts one distance-sorted link per qualifying body into the caller's RB tree |

The caller plate (`Editor_RebuildGlobalLinkLists` 0x14018c320) was updated to
reference `Frame_BuildLinkList` instead of the old `FUN_` address.

## Evaluated but left unnamed

| address | body | blocking fact |
|---|---|---|
| 0x14016dde0 / 0x14016ddf0 | bare setters of TextGrid +0x1a4 / +0x1a0 | values lost at the call sites (same conclusion as batch-6 agent 8) |
| 0x140073340 | empty body, 9 callers (Body_Explode, BulletImpact, physics contact, FX, scene spawn) | no observable behaviour; naming would be a guess |
| 0x140049cd0 | `arg <= this[0x2e8] && this[0x248] != 0.0` predicate, 7 callers | owning class and both field meanings unproven |
| 0x140073530 | releases child at +0x48 via vtable +0x48 then nulls it | two callers (`!ClickFunc`, `Scene_RebuildFromProfile`), no class proof |
| 0x1400bee20 | clears +0x128 on elements of the +0x8c0 vector whose +0x71 flag is set | called from one constructor; element class unproven |
| 0x1400fdec0 | clears +0x1d0/+0x1a4/+0x1b8 and the SSO string at +0x1a8 | called from `Radio_ReportContact`; struct ownership unproven |
| 0x1401941f0 | frees the nested buffer at +0x58 and returns whether it was non-null | caller pair (`APP:MoveVolume`, `SaveVolume`); role not distinct |
| 0x14019ae0f / 0x14019ae66 / 0x14019ae94 | compiler-split `CopyEscadraName` 0x20-stride loop fragments, no callers | split fragments, not standalone identities |
| 0x140017d10 / 0x14018f910 | identical 36-byte bodies: release interface at `*(int(vtbl)+4)+0x48` through vtable +0x10 | no callers, ICF pair, no class proof |
| 0x1401a4b40 | frees the nested buffer at +8 (`+0x20` inner) then the container | no callers, generic destructor |
| 0x1401a4210 / 0x1401a47f0 | 8-arg / 5-arg constructor-style initialisers | callers (`displayCityOnMap`, `memmoveMAIN`) do not carry field semantics |

## Doc cleanup (Phase 4 item 2)

`hf_notes/docs/data/ghidra-changes-2026-10-29.md` had accumulated duplicated
tails: a stale batch-7 documentation/counts block inside the Batch 10 section,
a second full Batch 8 section, and three repeated `! functions` + `Left for a
later pass` pairs (batch 7/8/9 text). Removed; the Batch 10 section now carries
its own documentation results and counts, and the file ends with the current
`Left for a later pass`. 1,054 lines, one section per batch.

## Incident 2026-10-30 ~16:25–17:47 (runaway EH walk)

`EhWalk.java` (Phase 1a) hung the Ghidra AWT script thread for ~80 minutes.
Root cause: the handler-map loop read `hn` (handler count) from a FuncInfo
record as an unbounded unsigned varint, then looped `for (j = 0; j < hn; j++)`.
On an aliased/corrupt record `hn` held a garbage 32-bit value, and
`readUnsigned` never throws (it returns -1 on unmapped memory), so the loop spun
~4e9 times. `jstack` showed `AWT-EventQueue-0` RUNNABLE inside
`EhWalk.walkFuncInfo(EhWalk.java:74)` with three MCP worker threads queued
behind it in `EventQueue.invokeAndWait`.

Recovery: the Ghidra JVM was restarted (new pid 3194354, 17:47). The program
was reopened from the shared project unchanged (5,430 function objects).

Hardening applied to `/home/maksim/ghidra_scripts/EhWalk.java` (backup in
`/tmp/opencode/EhWalk.java.bak`):

* `readUnsigned` rejects any pointer outside `0x140000000..0x140400000` and
  zeroes the cursor, so a bad record ends the walk instead of running on.
* new `cnt()` helper clamps every count read from an EH record to `1..64`;
  both the unwind-map and handler-map loops use it.

Rules for future EH scripts: never loop on a count read from the image without
clamping it; bound every pointer walk; a script runs on the AWT event thread
and cannot be cancelled from outside the JVM.

Side effect: the MCP tool catalog for the parent session dropped the Ghidra
server when the bridge exited. All parent Ghidra work now goes through
`/tmp/opencode/hf_ghidra_sweep/call.py` (direct UDS client, same API).

Unsaved parent renames were lost in the restart and re-applied afterwards:
`ResDesc_CopyBaseFields` (0x1401783c0) and `Frame_BuildLinkList` (0x1400458c0),
plus the caller plate fix at 0x14018c320.
