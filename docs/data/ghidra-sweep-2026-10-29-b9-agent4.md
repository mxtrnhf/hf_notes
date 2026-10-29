# Ghidra sweep batch 9, agent 4 — `rep_*` re-match `0x140000000–0x1400FFFFF` (Q1)

Program `Highfleet.exe.unpacked.exe` v1.163 (project `HighfleetServer`).
Scope: every current `rep_*` function with entry in `0x140000000–0x1400FFFFF`,
minus every address in `docs/data/funclet-ownership-2026-10-29.tsv`
(`funclet_addr` + `owner_addr`). Live enumeration at start: **384** in scope
(433 `rep_*` in the range, 49 excluded as funclet-ownership addresses).

**384 audited. 42 renamed + plated (40 `rep_*` + 2 `rep_*` from agent 7's owner
report). 342 stale labels left, each with a sharper identity. 0 unreadable.
0 byte-identical named twins.**

No `save_program`, no tags, no README/STATUS edits, no commits, no
`create_function`.

| | before | after |
|---|---|---|
| `rep_*` in scope | 384 | 342 |
| renamed + plated this pass | — | 42 |
| q1 rows appended | — | 394 |

## Method

1. Enumerated the live `rep_*` set with an inline script into
   `/tmp/opencode/hf_ghidra_sweep/b9a4_shapes.tsv` (entry, body size, exact
   body SHA-1, a **masked shape hash**, strings) and `b9a4_info.tsv`
   (vtable class, string literals, data symbols, callees, callers).
2. Shape hash = SHA-1 over mnemonic + operand kinds, with all 64-bit
   addresses and all scalars ≥ 0x10000 masked, plus the callee-name tokens.
   This was used to hunt near-twins of already-named functions. Result:
   **0 groups contain both a named function and an in-scope `rep_*`** — the
   "replica" premise is still false in this range; the collateral is template
   and ICF cloning among *unnamed* functions only.
3. Rebuilt the RTTI reader (x64 `_RTTICompleteObjectLocator`: `pTypeDescriptor`
   RVA at COL+0x0C, `pSelf` RVA at COL+0x14, `TypeDescriptor::name` inline at
   TD+0x10). **247 vtables** resolve in `0x140352288–0x1403765xx`
   (`b9a4_vtables.tsv`). Vtable operands are *scalars* in this listing
   (`LEA RAX,[0x140356a08]` has no reference), so they were matched by scalar
   value, not by xref. Only **1** in-scope `rep_*` references a vtable directly
   (`0x14004a2f0`, `.?AVb2PolygonShape@@`); the rest of the population is not
   constructor/destructor code.
4. Decompiled in batches of ≤10, skipping bodies > 0x2000 B. Every rename is
   proved from the body (vtable install, class literal, unique string, or a
   unique callee), never from the embedded label.

## Renames (42) — all with doc plates

### Escadra strategic-AI state messages (6)

| addr | new name | proof |
|---|---|---|
| 0x1400ef330 | `Escadra_UpdateSearchAndPursuit` | per-tick search/pursuit decision on `+0x75`; emits `"STOP SEARCHING."` via vtable +0x170 when `+0x3ac == 7` and resets it to 1 |
| 0x1400efdd0 | `Escadra_ReportNeedRefuel` | distance vs `Creature_GetFuelRate()`, `MakeGlobal(8)`, emits `"NEED TO REFUEL."` |
| 0x1400f56f0 | `Escadra_BeginMoveToGarrison` | `MakeGlobal(3)`, relinks `+0x6b`→`+0x6a`, emits `"MOVING TO GARNISONE."` |
| 0x1400f68a0 | `Escadra_BeginPursuit` | `MakeGlobal(5)`, emits `"ON PORSUE."` |
| 0x1400f7010 | `Escadra_HandleFlagshipLost` | replacement-escort scan; `"FLAGSHIP_LOST."` / `"CANT FOUND WHERE TO FLAGSHIP_LOST"` |
| 0x1400eea70 | `Escadra_TryTransferToGarrison` | `Escadra_MergeAdjacentFleet` + `"TO GARRISON - 1"`/`"- 2"` |

### Ship-constructor editor (9)

| addr | new name | proof |
|---|---|---|
| 0x1400c1f50 | `Editor_CollectPartsToPlayerEscadra` | `ED_SHPWRK_LIST` take-all: animates parts to the list centre, `Escadra_TransferShopItems(PLAYER_ESCADRA_)` |
| 0x1400c2460 | `Editor_ClearSubPinElements` | destroys every `ED_SUB_PIN` element (vtable +0x48) |
| 0x1400d2ec0 | `Editor_LoadSelectedSeria` | `"Objects/Designs/"`/`"Ships/"` + `ED_SAVELOAD_LIST` selection + `".seria"` → `Volume_LoadAndRecenter` |
| 0x1400d3dd0 | `Editor_RebuildSlotPins` | one `ED_SLOT_PIN` per roster body, `slot_pin`/`_master`/`_slave` backgrounds |
| 0x1400d4140 | `Editor_RefreshSlotPinsForBody` | same rebuild for one body after `Roster_PruneEmpty` |
| 0x1400dbf60 | `Editor_CreateSlotPinElements` | one `GUI::GUI_2("ED_SLOT_PIN")` per slot, appends `Link` to `DAT_1403ef3e8` |
| 0x1400dce10 | `Editor_CreateSubPinElement` | one `ED_SUB_PIN` from the `ED_SUB_LIST` selection, `"pin"` background |
| 0x1400da620 | `Editor_CreateNewProfile` | `CreateCreature`, name `"PROFILE"`+random, `"no_photo"`, `Creature::CalculateStats` |
| 0x1400dda20 | `Editor_ResetShipworksList` | destroys the first player creature, `EDITORCPP`, refreshes `ED_SHPWRK_LIST` (vtable +0x370) |

### Aircraft / creature (8)

| addr | new name | proof |
|---|---|---|
| 0x140009a80 | `AircraftLogic_UpdateAttackRun` | `Ballistics_PredictHit` lead check, fires via `MakeGlobal_`, logs `"STATE_RETIREMENT_AFTER_ATTACK"`, state → 4/7 |
| 0x14000a8a0 | `Creature_CollectByArrayPos` | picks the `DAT_1403c6340` tree by arrayPos 0..3, logs `"incorrect arrayPos: %d"`, inserts into the caller's RbTree |
| 0x14006e950 | `Creature_DisplayShipNameTag` | strips whitespace from the `+0xa90` name, prefixes `"SHIP_NAME_"`, `displayOnUI_` |
| 0x140078020 | `Creature_Relink` | `Body::relink` + virtual +0xa68, logs `"Creature::relink failed with m_escadra..."`, walks `+0x1558` children |
| 0x14006d9f0 | `Creature_SpawnThrustSmoke` | per-nozzle `"smoke_09"` + `"Media/Prt/thrust_01.psi"` on a 0.9 s cadence |
| 0x140072b90 | `Creature_InitBaseFields` | class literal `"Creature"` + type `0x2f` + full field reset; caller `CreateCreature` |
| 0x1400ea840 | `Creature_DistributeRepairPoints` | `ceilf` proportional split of the repair budget over missile properties, stores `+0x4bc` |
| 0x1400e9100 | `Body_ResetPartToDefinition` | `Shop_ReturnItemToPlayer` + `DefinePart(ALL_PARTS,name)` + part vtable +0x48 |

### Escadra object model / map (7)

| addr | new name | proof |
|---|---|---|
| 0x1400e8f70 | `Escadra_AddMissileProperty` | `Node::add` override, back-links missile `+0x178`, renumbers children by `+0x168`, `Profile_UnlockShip` |
| 0x1400e6100 | `Node_CopyConstructor` | `copyNode_` + SSO `std::string` + scalar-block copy |
| 0x1400f05a0 | `Escadra_DestroyMemberList` | destroy-walk of an intrusive list through `0x1400e36a0`, sentinel reset |
| 0x1400f0620 | `Escadra_UpdateEscortOffset` | places `+0x2d0/+0x2d4` 100 units along the `+0x530` heading when 150<d<500 |
| 0x1400f9170 | `Escadra_ClearMapModeFields` | zeroes `+0x168/+0x368/+0x464/+0x461`, `MAPMODE_THRUST_SLIDER`→1.0 |
| 0x1400f92b0 | `Escadra_ApplyMapModeFields` | `+0x168/+0x368`=9600.0, `+0x461`=1, slider 0, resets every missile `+0x16c/+0x248` |
| 0x1400f5080 | `MapGrid_CellToWorldPosition` | 10-unit grid cell → world position rotated by `+0x15c` |

### Profile / shop / fleet (6)

| addr | new name | proof |
|---|---|---|
| 0x1400f74b0 | `Profile_FindEscadraByName` | walks the profile escadra list, `memcmp` of the `+0xb0` name, requires `+0xf9` |
| 0x1400ba0f0 | `Profile_GetDiscontentEventName` | creates/queries `"EVENT_DISCONTENT_01"` when the player has >1 escadra and >1 qualifying missile |
| 0x1400f85d0 | `Editor_BuyPartFromLibraries` | gathers the 14 editor part libraries, `Shipworks_BuyPart` |
| 0x1400f89b0 | `Editor_RepairPartFromLibraries` | same gather, `Shipworks_RepairPart` |
| 0x1400e9310 | `Fleet_RecordPairEncounter` | increments the N×N fleet-pair matrices `DAT_1403ef580`/`DAT_1403ef598` |
| 0x1400f8e00 | `Object_IsWithin100Units` | `sqrt(delta +0x25c/+0x260 vs +0x150/+0x154) < 100` |

### Misc (6)

| addr | new name | proof |
|---|---|---|
| 0x140087b50 | `Shader_ReportNoTechnique` | formats `"No technique: "` + four fragments; on `RTDynamicCast` success appends to `+0x98` |
| 0x140091cb0 | `ShaderDeferringMid_Init` | `Effect_SetMatrixParam(0x4c,1)` + `BuildShaders___(this,"DeferringMid","vs_main","ps_main_mid")` |
| 0x1400c0b40 | `Editor_AttachPartToBody` | `MDL_FERMA2X2_01`/`MDL_FIGHTER_01` pair, `"screwdriver"` sound, reassigns `+0x16` link, recalculates stats |
| 0x1400bb3a0 | `std_stoi` | `strtol` + `errno==ERANGE`; throws `"invalid stoi argument"`/`"stoi argument out of range"` |
| 0x1400118a0 | `Vector24_InsertReallocate` | vector<0x18> grow-and-insert, limit `0xaaaaaaaaaaaaaaa`; renamed on agent 7's owner report, verified |
| 0x140012030 | `VectorString56_InsertReallocate` | vector<0x38> grow-and-insert, limit `0x492492492492492`; renamed on agent 7's owner report, verified |

## Already-named function renamed under the new protocol

Posted `**@agent4 -> rename**` at 14:55, applied ~15:05.

| addr | old name | new name | evidence |
|---|---|---|---|
| 0x1400e36a0 | `Escadra` | `Escadra_Constructor` | `Mark::Mark(this)` → `*(this) = &EscadraVFTABLE`, allocates four intrusive-list sentinels (`+0x288/+0x2a0/+0x318/+0x328`), installs eight `LinkVFTABLE`s, zeroes `+0x2c0..+0x608`, then `Escadra_InitBaseFields(this)` + `Escadra_CopyFrom(this,src)`. Decompiler: `Mark * Escadra::Escadra(...)`. Old name recorded in the plate. |

No other already-named function in the slice was proved wrong.

## Sharper stale identities (no rename)

Roles now proved but no unique, non-colliding name:

* `0x14004a2f0` — b2 overlap test: two `b2PolygonShape` copies (0.05 scale) from
  `+0x168/+0x178` fed to the b2 collide dispatcher `0x1402ed930`; only in-scope
  body referencing a vtable (`.?AVb2PolygonShape@@`).
* `0x140012220` / `0x140012410` / `0x140012600` — the other three
  `vector<0x38>` emplace-reallocate overloads (slot ctor `0x140016ff0` takes 4,
  5 and 7 args respectively). Same shape as `VectorString56_InsertReallocate`;
  naming them apart would require inventing suffixes.
* `0x1400f3c10` / `0x1400f4070` — missile motion offset vs backward offset along
  the heading, both with `CHECK ERROR … Escadra.cpp` NaN logging.
* `0x1400f9460` — statistics display (`CalculateStats`/`GetStats` +
  `WriteToClientLog` + `sprintf`).
* `0x1400fd340` — profile escort scan (`CopyEscadraName`/`GetStats` +
  `List_MergeSortByCreatureKeyAsc`).
* `0x1400ee280` — intercept geometry over escadra positions (`atan2f`).
* `0x1400f0fb0` / `0x1400f4c40` — list walks over property-linked objects.
* `0x1400e4cc0`, `0x1400f3270` — 5-byte import thunks (`jmp`), not bodies.

All 342 stale rows carry body size, exact SHA-1, whether the embedded label
target is a function entry (and whether its body hash differs), vtable class if
any, the first string literals, up to two callers and the callee signature.

## Negative results

* **0 named near-twins** under the masked shape hash. Nothing in the population
  is a byte/shape clone of an already-named function, so no name can be
  transferred by analogy without violating rule 8.
* The embedded address in the label is still not the function's identity: for
  the overwhelming majority the target is not a function entry (mid-instruction
  or undefined bytes); 0 rows point at a same-body function.
* 14 of the 52-byte `ShaderData_ResetVTable(); if(flag) free(this)` bodies remain
  the templated `ConstantBuffer<T>` slot-1 deleting destructor — not nameable
  without per-instantiation suffixes.
* The `0x140000000–0x1400A0000` remainder is std::vector / RbTree / string /
  fstream machinery plus `GetStats` template instantiations; each is recorded
  with its callee/string signature instead of a guessed name.
* 1 in-scope `rep_*` references a vtable; the rest of the range is not
  constructor/destructor code, so the RTTI map contributed fewer names than in
  batch 8.

## Output

* Appended **394** rows to `hf_notes/docs/data/rep-audit-2026-10-29-q1.tsv`
  (384 audited + 5 delta rows for the two agent-7 renames and the three
  `vector<0x38>` emplace overloads, + 5 CORRECTION rows that supersede the
  placeholder SHA-1 values in the first delta block). Existing rows untouched.
* Working dumps: `/tmp/opencode/hf_ghidra_sweep/b9a4_shapes.tsv`,
  `b9a4_info.tsv`, `b9a4_vtables.tsv`, `b9a4_final.txt`, `b9a4_rem.json`.

## Counts

* audited: **384**
* renamed + plated: **42** (40 `rep_*` + 2 `rep_*` from agent 7's report);
  plus 1 already-named function (`0x1400e36a0`) under the new protocol
* stale label left: **342**
* unreadable: **0**
* byte-identical / shape-identical named twins: **0**
