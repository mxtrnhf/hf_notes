# Ghidra sweep, batch 9 agent 3 — open `/EH` funclets C (`0x140348000–0x140350510`)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: the open funclets of batch 8 in `0x140348000–0x140350510`. The assignment
line said 66, but that is the batch-8 total for all three funclet agents; the
live slice holds **10** (as agent 2 also reported for its range). 9 already had a
function object, 1 (`0x14034a660`) did not.

**5 stale owners renamed and plated; 9 funclets named + plated (8 renamed in
place, 1 created); 1 still open.**
No already-named function was renamed. No `save_program`, tags, README/STATUS
edits or commits; no non-funclet `rep_*` touched.

| | count |
|---|---|
| funclets in this slice | **10** |
| stale owners renamed + plated | **5** |
| funclets named + plated | **9** (8 renamed in place + 1 created) |
| still open | **1** (`0x14034b743`, corrupt owner record) |

Two owners were renamed by batch-9 agent 6 while this pass was running
(`0x1402c7c90`, `0x1402e5c70`); their live names are used and left untouched.

## 1. Owners and funclets completed

The funclet↔owner/member mapping is the `.pdata` + `FUNCINFO4` table from batch 6
agent 1 (rows in `funclet-ownership-2026-10-29.tsv`). Owner identity in every
case was proven from the owner body in this pass; the `sz=` sized-delete operand
of the funclet equals the temporary allocated by the owner, which confirms the
pair independently.

| funclet | new funclet name | owner (old → new) | member | family | owner evidence |
|---|---|---|---|---|---|
| `0x14034a310` | `VectorStride8_InsertPtrFieldFromStride24Range_EhCleanup_0x30` | `0x1402c7c90` already `VectorStride8_InsertPtrFieldFromStride24Range` (b9a6) | `0x30` | rethrow | `vector<Node*>::insert(pos,first,last)` over a range of 0x18-byte `Link` records; copies the `node` field at `+8`; three calls each in `SCR_COMBAT_ReturnToMap` and `SCR_COMBAT_SKIRMISH_ReturnShips`, on the global Link vectors `0x143a158e0/e8` and `0x143a159c0/c8` |
| `0x14034a4e0` | `Battle_DeployFromReserve_EhCleanup_0xd8` | `0x1402d22e0` `rep_1402a8540_...free` → **`Battle_DeployFromReserve`** | `0xd8` | linkFree | pops reserve ships from the list `param_1`, cost-gates on missile `+0x15f8` (<=15 / <=25 / else = 1/2/3 points, budget 6), spawns via `0x1402454a0`, appends 0x18-byte Links to the roster `param_2`; callers `SCR_COMBAT`, `SCR_COMBAT_SKIRMISH_TickRedeploy`, `battleManagerTick` |
| `0x14034a660` | `Body_TryAttachBodies_EhCleanup_0x40` | `0x1402dbb20` `rep_1402b0710_...free` → **`Body_TryAttachBodies`** | `0x40` | freeField | welds two unmounted bodies sharing a `+0xb8` mask: `Frame_Constructor` (0xa58) or `Joint_ConstructorWithNodes` (0x118), `SetLink`, joint queue `rep_14025d8a0_New`, optional `memmove` copy; returns 1 on attach |
| `0x14034a680` | `Body_TryAttachBodies_EhCleanup_0x198` | same owner | `0x198` | freeField | same |
| `0x14034a760` | `Sprite_CopyFrom_EhCleanup_0x48` | `0x1402de080` `rep_1402b2bd0_New` → **`Sprite_CopyFrom`** | `0x48` | freeField | field-copy half of the `Sprite` copy constructor: called from `0x1402ddad0` after `SpriteVFTABLE` + `createSprite_`; copies `+0x50…+0x160`, the std::strings at `+0x90/+0xb0`, and the `vector<Anistate*>` at `+0xf0` (`Anistate_CopyConstructor`, `New(0xb0)`) |
| `0x14034a7a0` | `Ground_DrawMarker_EhCleanup_0x58` | `0x1402e0d50` `rep_1402b58a0_...floorf` → **`Ground_DrawMarker`** | `0x58` | linkFree | only caller is vtable slot 4 of `0x1403770e8` (RTTI `.?AVGround@@`, base `.?AVLandpart@@`, COL `0x140381180`); draws one element of the object's `+0x18` list: its 0x58-stride sprite records at `+0x178` with colour `+0x48`, at the owner's transformed screen position |
| `0x14034a900` | `VectorStride8_InsertValuePair32_EhCleanup_0x60` | `0x1402e5c70` already `VectorStride8_InsertValuePair32` (b9a6) | `0x60` | rethrow | `vector<unsigned __int64>::insert(pos,value)` (8-byte element from two dwords), doubling growth, `_Change_array` |
| `0x14034a930` | `Vector_InsertStride12_EhCleanup_0x70` | `0x1402e5dd0` already `Vector_InsertStride12` | `0x70` | rethrow | 12-byte-stride vector insert (limit `0x1555555555555555`, `ThrowBadArrayLengthException`) |
| `0x14034ab00` | `CityLandscape_RenderTiles_EhCleanup_0xd8` | `0x1402ed2f0` `rep_1402c1e60_FID_conflict:~vector<GSISymbolEntry>` → **`CityLandscape_RenderTiles`** | `0xd8` | freeField | sole caller `generateCityLandscape`; buckets the `DAT_148021c70` building list by `+0x40` type, `RenderTarget_Create` per tile at the requested `ZOOM_LEVEL`, `Hud_DrawQueuedSprite` per record, one `CreateHGE` texture per tile, appends to `DAT_148021ca8` |

Funclet bodies (drives the `Algorithm:` line of each plate):

* `0x14034a310` — restores the parent vector's saved begin/end/capacity from
  `frame+0x80/+0x88/+0x90/+0x98` using the element count at `frame+0x30`
  (`memmove` paths), then `_CxxThrowException(0,0)`; this is the rollback path of
  the range insert.
* `0x14034a4e0` — `if (frame+0x50 & 1) { clear bit; freeLinkMemory_(frame+0xd8); }`.
* `0x14034a660` — `PUSH RBP; MOV RBP,RDX; MOV EDX,0x118; MOV RCX,[RBP+0x40]; CALL 0x1403340d0` (sized free wrapper), `RET`, `INT3` padding.
* `0x14034a680` — `free(*(frame+0x198))`, `sz=0x118`.
* `0x14034a760` — `free(*(frame+0x48))`, `sz=0xb0` (the `Anistate` temporary).
* `0x14034a7a0` — `if (frame+0x30 & 1) { clear bit; freeLinkMemory_(frame+0x58); }`.
* `0x14034a900` — `deallocate(frame+0x60, frame+0x20, frame+0x68)` then rethrow;
  frees the new 8-byte-element buffer when the insert unwinds.
* `0x14034a930` — `deallocate(frame+0x70, frame+0x20, frame+0x78)` then rethrow.
* `0x14034ab00` — `free(*(frame+0xd8))`, `sz=0x1a8`.

Owner plates follow the batch-9 four-line shape (summary / algorithm /
parameters / returns). Funclet plates are the batch-6/7 five-line template with
the live owner name, the member, the destroy operation and the temporary type.

## 2. Creation

`0x14034a660` had no function object. Evidence: `pdata:0x14034a660-0x14034a67d`,
`funcinfo4@0x1403b54e4`, `sz=0x118`; the bytes are a standalone 29-byte body
starting at a `PUSH RBP` immediately after the previous function's `RET` at
`0x14034a65f`, with `INT3` from `0x14034a67d` to the next function
`0x14034a680`. Creation from the `.pdata` extent therefore cannot split any
existing function. Posted on the blackboard before creating, per protocol.

## 3. Still open (1)

| funclet | owner | member | reason |
|---|---|---|---|
| `0x14034b743` | `0x140334358` `__scrt_is_nonwritable_in_current_image` | — | corrupt owner record (`TSV family "nobody"`). Body is a filter predicate, not a cleanup: `PUSH RBP; MOV RBP,RDX; MOV RAX,[RCX]; CMP dword ptr [RAX],0xC0000005; SETZ CL; MOV EAX,ECX; RET` — it tests whether the exception code is `STATUS_ACCESS_VIOLATION` (`0xC0000005`). The owner is a CRT section-flags loop with no EH and no matching temporary, so the FuncInfo4 attribution is suspect; naming it as `__scrt_*` would be wrong. Left open with this body recorded. |

## 4. Outside my scope, for the owner

* `0x1402f6910` still carries `rep_1402cb4d0_...sinf` but is vtable slot 4 of
  `0x1403770e8` (`.?AVGround@@` : `.?AVLandpart@@`) and draws the object's
  marker list; it is the only caller of `Ground_DrawMarker` (`0x1402e0d50`).
  It belongs to the `rep_*` D slice (`0x140300000–0x140350510` is not its range —
  it is `0x140200000–0x1402FFFFF`, i.e. agent 6) or to agent 9's `FUN_*` set.
* Because of that RTTI, the `Hud_Marker*` family (`Hud_MarkerSetColor`
  `0x1402e2000` and neighbours) is called on `Ground`/`Landpart` children; the
  `Hud_Marker` prefix may be a batch-3 approximation. Not changed here.

## 5. Method / hand-off

Same method as batch 8 agent 3 (`.pdata` owner/member + body proof + `sz=`
cross-check), plus the vector/link consumers at the call sites to fix the
element type for the three container helpers. The batch-7 pending pass
(`/tmp/opencode/hf_ghidra_sweep/b7a1_pending.tsv` + `B7A1Pending.java`) is not
needed for this slice: every funclet with a proven owner is now named.
