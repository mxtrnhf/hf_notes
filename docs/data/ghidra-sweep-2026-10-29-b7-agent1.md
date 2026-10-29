# Ghidra sweep, batch 7 agent 1 — `/EH` funclet completion

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: `0x140337000–0x140350510` (the 926-row owner map from batch 6) plus the
13-funclet block `0x140336730–0x140336f50` added by the scope extension.

**281 of 354 funclets are now named and plated: 120 renamed in place, 161
created. 73 remain open** (68 whose owner still carries a stale `rep_*` label,
5 edge cases). No `save_program`, no tags, no README/STATUS edits, no commit.

| | main range | block 13 | total |
|---|---|---|---|
| addresses in scope | 341 | 13 | 354 |
| named + plated | 274 | 7 | **281** |
| … renamed in place | 114 | 6 | **120** |
| … `create_function` + named | 160 | 1 | **161** |
| still open | 67 | 6 | **73** |

Program state after (all agents' concurrent work included): 5,231 function
objects. All 281 names are unique and every one carries the 5-line plate.

## 1. Names applied

| group | scheme | count |
|---|---|---|
| ICF-shared body (2–34 owners) | `EhCleanup_Shared_<family>_<n>` — program-wide per-family index, **full owner list in the plate** | 90 |
| `!ClickFunc`-owned | `ClickFunc_EhCleanup_<member>` | 28 |
| single proven owner | `<Owner>_EhCleanup_<member>` | 163 |
| **total** | | **281** |

Family split of the 281: `freeField` 208, `string` 47, `rethrow` 13,
`linkFree` 7, `captain` 2, `vdtor` 2, `other` 2. 37 names needed a numeric
tail (`_2`, `_3`, …) because one owner destroys the same frame slot several
times (batch 6 used `_sz`/`_b` for the sized/bit variants; those are untouched
and the numeric tail continues after them). No `_sz`-type disambiguation was
needed here because every new single-owner row has a distinct member offset or
a distinct owner.

Plate form (5 lines, at the funclet address):

> /EH cleanup funclet of `<Owner>`; destroys member `+0x…` of the parent frame.
> Family: `…`.
> Algorithm: called by `__CxxFrameHandler4` with `(exceptionCode,frame)` in
> `(ECX,RDX)`; `RBP:=RDX`; guard test; run the destroy recorded below.
> Parameters: ECX = exception code, RDX = parent frame pointer; no return value.
> Returns: void.
> Owner and member recovered from the `.pdata` `RUNTIME_FUNCTION` /
> `FUNCINFO4` funclet table (sweep b7 agent 1); body `0x…-0x…`.

Shared bodies get the same plate with `Owners: ` + the full `0x… <name>; …`
list instead of the first line.

## 2. Owner renames that unblocked funclet names (7)

Only renamed when the body proved an identity beyond the stale `rep_*` label.
`rep-audit` had already ruled all of these "stale, no identity", so the proof
is recorded here.

| owner | new name | evidence |
|---|---|---|
| `0x140086fc0` | `Effect_CreateMatrixConstantBuffer` | allocates 0x68, `ShaderData_Constructor`, stores vftable `PTR_EffectMatrixConstantBuffer_Upload_140356ad8` (RTTI `ConstantBuffer<CBMatrix@Effect>`), records a 0x40/4 upload and appends to `Effect+0x68`. Callers `Effect_SetInstanceMatrices` / `Effect_SetMatrixParam` (agent 2 concurrently named it `EffectMatrixConstantBuffer_Constructor` — its name was kept, see below) |
| `0x1401a3d00` | `File_OpenOfstream` | stores `basic_ofstream` (0x140356810) / `basic_filebuf` (0x140356790) vftables, `basic_streambuf::_Init`, `OpenFile_`, sets failbit on failure |
| `0x14001bca0` | `Editor_CreateSlotEntry` | allocates a 0xc0 `ISerializable`, `SetLink` at +0x68, fields +0x48/+0x4c/+0x84/+0x85/+0xb8, pushes into the parent's **+0x350 slot vector**, ORs the bit into +0x368; 19 direct calls from `Editor_GenerateSlots` |
| `0x140051580` | `Body_AssignAircraftSlots` | walks the same +0x350 slot vector, `Body_FindNearestSlotIndex`, writes flag at slot+0xb0 and the parent name at +0x190 into slot+0x90; callers `AiShipTick`, `PlayerLaunchPlane`, `CreateMapAircraftGroup`, `ReconcileMapAircraftGroupOwners` |
| `0x14026e240` | `Precombat_BuildAmmoSelectorRow` | `AMMO_SELECT`/`AMMO_SELECT_TXT`/`AMMO_SELECT2` strings, `gui_std` skin, `Ammo_GetRecord`; callers `Precombat_BuildAmmoSelectors`, `ammoSelectButtonPress` |
| `0x1401c6a90` | `Dialog_BuildStatsRow` | `DIALOG_STATS` string + `dinpro_48_black` template; called 8× by `Dialog_DrawStatsRows` (agent 3 named it `Dialog_BuildStatsPanel` concurrently — its name was kept) |
| `0x1402d4330` | `Battle_InitPlayerRoster` | `Battle_PruneRoster` + `Roster_PruneOutsideLevelBounds` + `Profile_SetPlayerShip` + `Profile_GetFirstPlayerCreature`; called from `SCR_COMBAT` |

Three owners were renamed by agents 2/3 during the pass and the funclet names
followed them automatically (the pending pass resolves the owner name live):
`0x1401b7970` → `GameOver_CheckFlagshipLost` (3 funclets),
`0x140086fc0` → `EffectMatrixConstantBuffer_Constructor`,
`0x1401c6a90` → `Dialog_BuildStatsPanel`.
`0x14028bb70` (`Loadout_BuildLibrary`) and `0x14028c760`
(`Loadout_RebuildLibraryFromProfile`) had been renamed at the end of batch 6;
their 2 funclets are named after those.

## 3. The 165 funclets with no function object (creation request, executed)

Posted to the blackboard at 13:20 MSK (bulk request, 165 addresses; see
`**@agent1 -> creation**`), no objection, executed one cycle later. **161
created** (160 in the main range, 1 in block 13); 4 of the 165 turned out to
belong to the still-stale `rep_*` owners and were not created (they will be
created in the same way once the owner is named — the pending run does it
automatically).

Each creation used the `.pdata` `RUNTIME_FUNCTION` extent as the body
(`BeginAddress..EndAddress-1`, 24–95 bytes, 121 exactly 0x20), so no existing
function body was truncated: `getFunctionContaining` was checked first, and no
creation was blocked (`CREATE-BLOCKED` count = 0).

## 4. Block `0x140336730–0x140336f50` (scope extension)

The block has 22 `.pdata` records. Applying the batch-6 method (parse
`RUNTIME_FUNCTION` at `0x148078000`, decode `UNWIND_INFO`, bound each
`FUNCINFO4` blob by the next distinct handler-data start, scan the blob for the
target RVA) gives:

* **13 records with the generic funclet unwind** (`0x140381e6c` or
  `0x1403822b8`) and a funclet-shaped body — exactly the 13 of the request.
  **7 named, 6 open** (owner still `rep_*`).
* 5 small functions in the same block already carry stale `rep_*` names
  (`0x140336c80`, `0x140336d20`, `0x140336df0`, `0x140336ea0`, `0x140336f00`:
  each has **its own** `UNWIND_INFO`, 0x140385d8c / 0x140385df4 / 0x140385f58 /
  0x1403861f4 / 0x14038622c, and `_CxxThrowException` replica labels). They are
  real functions that ICF-folded onto a funclet body; **not touched** (outside
  this job, agent 4's range).
* `0x140336c40` (2 owners) and `0x140336e70` (owner `0x140336ea0`) have funclet
  prologues but a deleting-dtor / vtable-restore body, not a destroy; left
  alone and recorded.
* `0x140336cc0` is `NOFUNC` but owned, left for the same reason as above.
* `0x140336710` is a 6-byte `JMP [0x1403519c8]` thunk, not a funclet.

Named here:

| addr | name | owner | evidence |
|---|---|---|---|
| `0x140336730` | `LinkVec_EmplaceReallocate_EhCleanup_0xa0` | `LinkVec_EmplaceReallocate` | destroys `Link` ranges at +0xa0 and +0x40 (`Link_DestroyRange`, `deallocate`) |
| `0x140336850` | `Array_Push32_EhCleanup_0x60` | `Array_Push32` | `DeleteArray32(*(frame+0x60))` |
| `0x140336880` | `vec_realloc_insert_EhCleanup_0x60` | `vec_realloc_insert` | `deallocate(*(frame+0x60))` |
| `0x1403368b0` | `zzUnwindRelated3_EhCleanup_0x50` | `zzUnwindRelated3` | `deallocate(*(frame+0x50))` |
| `0x140336cf0` | `Vector16_InsertReallocate_EhCleanup_0x70` | `Vector16_InsertReallocate` | `deallocate(*(frame+0x70))` — **created** |
| `0x140336b00` | `EhCleanup_Shared_freeField_77` | 6 owners | `free(*(frame+0x48), 0x40)` |
| `0x140336b20` | `EhCleanup_Shared_freeField_78` | 3 owners | `free(*(frame+0x48), 0x38)` |

The 6 open ones are `0x1403368e0`, `0x140336d60`, `0x140336d90`,
`0x140336dc0`, `0x140336e30`, `0x140336f50`; their owners
(`0x1400dfa70`, `0x1400127f0`, `0x1400128f0`, `0x140012a30`, `0x140013160`,
`0x14016fa00`) are all stale `rep_*` labels (`_Change_array` / `_New` /
`_invalid_parameter_noinfo_noreturn` replicas) that the body disproves but does
not replace with an identity.

## 5. Shared bodies — the 90 `EhCleanup_Shared_*`

Numbering is per family over the whole program (`freeField_1…78`,
`string_1…10`, `rethrow_1`, `linkFree_1`). These are bodies MSVC/`/OPT:ICF`
folded; one address serves 2–34 different owners, so naming it after one owner
would be wrong. The plate carries the complete owner list with names as they
stood when the funclet was named.

| funclet | name | family | owners |
|---|---|---|---|
| `0x1403372f0` | `EhCleanup_Shared_freeField_1` | freeField | 2 |
| `0x140337350` | `EhCleanup_Shared_freeField_2` | freeField | 2 |
| `0x1403373b0` | `EhCleanup_Shared_freeField_3` | freeField | 3 |
| `0x140337420` | `EhCleanup_Shared_freeField_4` | freeField | 3 |
| `0x140337440` | `EhCleanup_Shared_freeField_5` | freeField | 2 |
| `0x1403374a0` | `EhCleanup_Shared_freeField_6` | freeField | 2 |
| `0x1403374c0` | `EhCleanup_Shared_freeField_7` | freeField | 21 |
| `0x1403375a0` | `EhCleanup_Shared_freeField_8` | freeField | 6 |
| `0x1403376c0` | `EhCleanup_Shared_freeField_9` | freeField | 11 |
| `0x140337810` | `EhCleanup_Shared_freeField_10` | freeField | 3 |
| `0x1403378f0` | `EhCleanup_Shared_freeField_11` | freeField | 6 |
| `0x140337af0` | `EhCleanup_Shared_freeField_12` | freeField | 4 |
| `0x140337b50` | `EhCleanup_Shared_freeField_13` | freeField | 7 |
| `0x140337b70` | `EhCleanup_Shared_freeField_14` | freeField | 2 |
| `0x140337e20` | `EhCleanup_Shared_freeField_15` | freeField | 4 |
| `0x140338a50` | `EhCleanup_Shared_freeField_16` | freeField | 34 |
| `0x140338c30` | `EhCleanup_Shared_string_1` | string | 2 |
| `0x140338c60` | `EhCleanup_Shared_freeField_17` | freeField | 2 |
| `0x140338cb0` | `EhCleanup_Shared_freeField_18` | freeField | 6 |
| `0x140338ce0` | `EhCleanup_Shared_freeField_19` | freeField | 9 |
| `0x140338d00` | `EhCleanup_Shared_freeField_20` | freeField | 7 |
| `0x140338d20` | `EhCleanup_Shared_freeField_21` | freeField | 7 |
| `0x140338d60` | `EhCleanup_Shared_freeField_22` | freeField | 2 |
| `0x140339260` | `EhCleanup_Shared_freeField_23` | freeField | 3 |
| `0x140339280` | `EhCleanup_Shared_freeField_24` | freeField | 2 |
| `0x1403392b0` | `EhCleanup_Shared_freeField_25` | freeField | 2 |
| `0x1403393c0` | `EhCleanup_Shared_freeField_26` | freeField | 7 |
| `0x140339530` | `EhCleanup_Shared_freeField_27` | freeField | 8 |
| `0x140339680` | `EhCleanup_Shared_freeField_28` | freeField | 5 |
| `0x1403396e0` | `EhCleanup_Shared_freeField_29` | freeField | 2 |
| `0x140339990` | `EhCleanup_Shared_freeField_30` | freeField | 3 |
| `0x14033a070` | `EhCleanup_Shared_freeField_31` | freeField | 26 |
| `0x14033a090` | `EhCleanup_Shared_string_2` | string | 2 |
| `0x14033c1b0` | `EhCleanup_Shared_string_3` | string | 3 |
| `0x14033c1e0` | `EhCleanup_Shared_string_4` | string | 3 |
| `0x14033c210` | `EhCleanup_Shared_string_5` | string | 2 |
| `0x14033c270` | `EhCleanup_Shared_string_6` | string | 2 |
| `0x14033c6c0` | `EhCleanup_Shared_freeField_32` | freeField | 4 |
| `0x14033c790` | `EhCleanup_Shared_freeField_33` | freeField | 3 |
| `0x14033c7b0` | `EhCleanup_Shared_freeField_34` | freeField | 6 |
| `0x14033c7d0` | `EhCleanup_Shared_freeField_35` | freeField | 4 |
| `0x14033c7f0` | `EhCleanup_Shared_freeField_36` | freeField | 2 |
| `0x14033c830` | `EhCleanup_Shared_freeField_37` | freeField | 5 |
| `0x14033c870` | `EhCleanup_Shared_freeField_38` | freeField | 3 |
| `0x14033c9f0` | `EhCleanup_Shared_freeField_39` | freeField | 3 |
| `0x14033ca10` | `EhCleanup_Shared_freeField_40` | freeField | 3 |
| `0x14033cad0` | `EhCleanup_Shared_freeField_41` | freeField | 2 |
| `0x14033d620` | `EhCleanup_Shared_freeField_42` | freeField | 2 |
| `0x14033d7b0` | `EhCleanup_Shared_freeField_43` | freeField | 2 |
| `0x14033d8b0` | `EhCleanup_Shared_freeField_44` | freeField | 3 |
| `0x14033db70` | `EhCleanup_Shared_freeField_45` | freeField | 6 |
| `0x14033df90` | `EhCleanup_Shared_freeField_46` | freeField | 2 |
| `0x14033e1b0` | `EhCleanup_Shared_freeField_47` | freeField | 2 |
| `0x14033e4b0` | `EhCleanup_Shared_freeField_48` | freeField | 2 |
| `0x14033f680` | `EhCleanup_Shared_freeField_49` | freeField | 3 |
| `0x14033f6a0` | `EhCleanup_Shared_freeField_50` | freeField | 4 |
| `0x140340800` | `EhCleanup_Shared_string_7` | string | 4 |
| `0x140340c00` | `EhCleanup_Shared_string_8` | string | 2 |
| `0x140340f90` | `EhCleanup_Shared_freeField_51` | freeField | 3 |
| `0x140341070` | `EhCleanup_Shared_freeField_52` | freeField | 2 |
| `0x1403410d0` | `EhCleanup_Shared_freeField_53` | freeField | 2 |
| `0x1403419f0` | `EhCleanup_Shared_freeField_54` | freeField | 2 |
| `0x140341e60` | `EhCleanup_Shared_rethrow_1` | rethrow | 2 |
| `0x140342c10` | `EhCleanup_Shared_linkFree_1` | linkFree | 2 |
| `0x140342f50` | `EhCleanup_Shared_freeField_55` | freeField | 3 |
| `0x140343280` | `EhCleanup_Shared_freeField_56` | freeField | 4 |
| `0x140343320` | `EhCleanup_Shared_freeField_57` | freeField | 7 |
| `0x140343360` | `EhCleanup_Shared_freeField_58` | freeField | 2 |
| `0x1403433a0` | `EhCleanup_Shared_freeField_59` | freeField | 6 |
| `0x140343600` | `EhCleanup_Shared_freeField_60` | freeField | 6 |
| `0x140343750` | `EhCleanup_Shared_freeField_61` | freeField | 5 |
| `0x140343770` | `EhCleanup_Shared_freeField_62` | freeField | 3 |
| `0x140343790` | `EhCleanup_Shared_freeField_63` | freeField | 2 |
| `0x140343940` | `EhCleanup_Shared_freeField_64` | freeField | 2 |
| `0x1403439a0` | `EhCleanup_Shared_freeField_65` | freeField | 2 |
| `0x140343a80` | `EhCleanup_Shared_freeField_66` | freeField | 2 |
| `0x140343c70` | `EhCleanup_Shared_freeField_67` | freeField | 2 |
| `0x140343ef0` | `EhCleanup_Shared_freeField_68` | freeField | 2 |
| `0x140343f30` | `EhCleanup_Shared_freeField_69` | freeField | 5 |
| `0x140344070` | `EhCleanup_Shared_freeField_70` | freeField | 2 |
| `0x1403442a0` | `EhCleanup_Shared_freeField_71` | freeField | 2 |
| `0x140345570` | `EhCleanup_Shared_freeField_72` | freeField | 2 |
| `0x140345660` | `EhCleanup_Shared_string_9` | string | 3 |
| `0x140345860` | `EhCleanup_Shared_freeField_73` | freeField | 2 |
| `0x140345880` | `EhCleanup_Shared_freeField_74` | freeField | 2 |
| `0x1403463b0` | `EhCleanup_Shared_string_10` | string | 2 |
| `0x140346bf0` | `EhCleanup_Shared_freeField_75` | freeField | 2 |
| `0x140347380` | `EhCleanup_Shared_freeField_76` | freeField | 2 |
| `0x140336b00` | `EhCleanup_Shared_freeField_77` | freeField | 6 |
| `0x140336b20` | `EhCleanup_Shared_freeField_78` | freeField | 3 |

## 6. Still open — 73

### 6a. Owner still carries a stale `rep_*` label (68)

The owner body disproves its embedded label (batch-6 audit: "stale, no
identity"), and neither RTTI/vftable, strings, callee set nor caller set proves a
specific replacement. Per ground rule 5 they are skipped, not guessed. The 62 in
the main ownership map:

| funclet | owner (stale) | member | family |
|---|---|---|---|
| `0x1403377e0` | `rep_140022650_MakeGlobal?` | `0x48` | freeField |
| `0x140338110` | `rep_140056260_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `0x80` | rethrow |
| `0x140338a10` | `rep_14005eca0_PlayRadioSound?` | `0xe0` | freeField |
| `0x140338a70` | `rep_140063d80_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `0x80` | string |
| `0x140339240` | `rep_140082f40_New` | `0x30` | freeField |
| `0x1403392f0` | `rep_140084ab0_VCRUNTIME140.DLL::memmove` | `0x60` | rethrow |
| `0x140339370` | `rep_140085340_VCRUNTIME140.DLL::memmove` | `0x60` | rethrow |
| `0x140339430` | `rep_1400871d0_VCRUNTIME140.DLL::memmove` | `0x60` | rethrow |
| `0x140339480` | `rep_140087d50_New` | `0x60` | rethrow |
| `0x140339700` | `rep_14008c780_New` | `0x60` | rethrow |
| `0x1403399d0` | `rep_140096840_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | `0x60` | rethrow |
| `0x14033c4d0` | `rep_1400b7900_VCRUNTIME140.DLL::memmove` | `0x80` | rethrow |
| `0x14033c700` | `rep_1400bc6b0_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | `0xe8` | linkFree |
| `0x14033c730` | `rep_1400bc6b0_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | `0x118` | linkFree |
| `0x14033cbd0` | `rep_1400d8690_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | `0x38` | string |
| `0x14033cc00` | `rep_1400d8690_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | `0x38` | string |
| `0x14033cc30` | `rep_1400d8690_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | `0x38` | string |
| `0x14033cc80` | `rep_1400d9e00_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | `0x60` | rethrow |
| `0x14033cd50` | `rep_1400da790_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | `0x70` | rethrow |
| `0x14033ce50` | `rep_1400dad20_VCRUNTIME140.DLL::memmove` | `0x70` | rethrow |
| `0x14033d500` | `rep_1400dfed0_CopyString` | `0x88` | freeField |
| `0x14033d640` | `rep_1400e5de0_WriteToClientLog` | `0x38` | freeField |
| `0x14033d930` | `rep_1400ec220_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | `0xe0` | freeField |
| `0x14033d950` | `rep_1400ec220_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | `0xe0` | freeField |
| `0x14033d970` | `rep_1400ec220_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | `0x60` | other |
| `0x14033dab0` | `rep_1400eeaf0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | `0x30` | linkFree |
| `0x14033db30` | `rep_1400f13a0_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | `0x80` | string |
| `0x14033dd30` | `rep_1400ff4f0_checkJammed?` | `0x70` | linkFree |
| `0x14033e120` | `rep_140114980_CopyEscadraName` | `0xe8` | string |
| `0x14033e150` | `rep_140114980_CopyEscadraName` | `0x68` | string |
| `0x14033e310` | `rep_140118570_New` | `0x60` | rethrow |
| `0x14033e4e0` | `rep_14011bb60_loadMediaByName?` | `0x88` | freeField |
| `0x14033e510` | `rep_14011c0d0_loadMediaByName?` | `0xe0` | freeField |
| `0x14033ec50` | `rep_140123550_New` | `0x58` | freeField |
| `0x1403410f0` | `rep_140163bb0_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | `0x80` | rethrow |
| `0x140341460` | `rep_1401781f0_std::vector<unsigned___int64,class_std::allocator<unsigned___int64>_>::_Change_array` | `0x60` | rethrow |
| `0x140341e10` | `rep_140189530_std::vector<struct_CHN*___ptr64,class_std::allocator<struct_CHN*___ptr64>_>::vector<struct_CHN*___ptr64,class_std::allocator<struct_CHN*___ptr64>_>` | `0xa0` | rethrow |
| `0x140341ef0` | `rep_14018a710_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `0x70` | rethrow |
| `0x140341f50` | `rep_14018aae0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `0x60` | rethrow |
| `0x140341fb0` | `rep_14018aed0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `0x70` | rethrow |
| `0x140342030` | `rep_14018b3e0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `0x80` | rethrow |
| `0x140342080` | `rep_14018b670_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `0x80` | rethrow |
| `0x1403421b0` | `rep_14018c110_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `0xa0` | rethrow |
| `0x140342420` | `rep_14018cbf0_VCRUNTIME140.DLL::memmove` | `0x80` | rethrow |
| `0x140343460` | `rep_1401b4600_Escadra::Escadra` | `0x60` | freeField |
| `0x140343ff0` | `rep_1401e7b50_GUI::GUI_2` | `0x148` | freeField |
| `0x1403445b0` | `rep_1401fc690_Node::Node` | `0xb8` | freeField |
| `0x140345630` | `rep_140219d90_API-MS-WIN-CRT-MATH-L1-1-0.DLL::ceilf` | `0x60` | string |
| `0x140345690` | `rep_14021a3c0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | `0xa0` | string |
| `0x1403456c0` | `rep_14021a3c0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | `0x80` | string |
| `0x1403456f0` | `rep_14021a3c0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | `0xa0` | string |
| `0x140345840` | `rep_14021e670_VCRUNTIME140.DLL::memmove` | `0x68` | freeField |
| `0x140345b80` | `rep_140231a90_CopyString` | `0x70` | string |
| `0x14034a310` | `rep_1402a18c0_New` | `0x30` | rethrow |
| `0x14034a4e0` | `rep_1402a8540_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `0xd8` | linkFree |
| `0x14034a660` | `rep_1402b0710_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `0x40` | freeField |
| `0x14034a680` | `rep_1402b0710_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `0x198` | freeField |
| `0x14034a760` | `rep_1402b2bd0_New` | `0x48` | freeField |
| `0x14034a7a0` | `rep_1402b58a0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::floorf` | `0x58` | linkFree |
| `0x14034a900` | `rep_1402ba770_std::vector<unsigned___int64,class_std::allocator<unsigned___int64>_>::_Change_array` | `0x60` | rethrow |
| `0x14034a930` | `rep_1402ba8d0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `0x70` | rethrow |
| `0x14034ab00` | `rep_1402c1e60_FID_conflict:~vector<struct_GSISymbolEntry,class_std::allocator<struct_GSISymbolEntry>_>` | `0xd8` | freeField |

The 6 in the block `0x140336730–0x140336f50` (owners are 0x1400dfa70,
0x1400127f0, 0x1400128f0, 0x140012a30, 0x140013160, 0x14016fa00):

| funclet | owner | member | family |
|---|---|---|---|
| `0x1403368e0` | `rep_1400da420_..._invalid_parameter_noinfo_noreturn` | `0x90` | freeField |
| `0x140336d60` | `rep_1400127d0_..._Change_array` | `0x60` | freeField |
| `0x140336d90` | `rep_140012a70_..._Change_array` | `0x50` | freeField |
| `0x140336dc0` | `rep_140012bb0_New` | `0x60` | freeField |
| `0x140336e30` | `rep_1400130e0_..._Change_array` | `0x80` | freeField |
| `0x140336f50` | `rep_1400163f10_..._invalid_parameter_noinfo_noreturn` | `0x50` | freeField |

These will be named mechanically once the owners are renamed: the pending pass
(`/tmp/opencode/hf_ghidra_sweep/b7a1_pending.tsv` + `B7A1Pending.java`) re-reads
the owner name at each run, so it can simply be re-executed.

### 6b. Edge cases (5) — recorded, not named

| addr | reason |
|---|---|
| `0x1403423c0` | owner `VectorString32_InsertRange` proves a name but the funclet body has **no member displacement** (a vector-range rethrow helper); naming would invent a `+0x…` |
| `0x14034b743` | `__scrt_is_nonwritable_in_current_image` owner (CRT), family `nobody`, no member displacement — same problem |
| `0x140340ff0` | owner has **no function object** in Ghidra (`0x14016bf00`, also an owner of the shared body `0x140336b00`) |
| `0x140341220` | owner has **no function object** in Ghidra (same `0x14016bf00`) |
| `0x140342380` | owner is itself `FUN_1403423c0` (not a real identity; batch-6 §6 anomaly: member +0xa0 exceeds the owner's 89-byte body) |

`0x1403423c0` and `0x14034b743` were briefly given a trailing-underscore name by
the first pending run (empty member field) and **reverted to `FUN_*`** with the
plate cleared; they are listed here as open.

## 7. Verification

* 354/354 addresses checked in the live program after the pass:
  **281 named, 281 with a plate, 73 unnamed, 0 named without a plate.**
* 0 name collisions (`setName`/`createFunction` failures = 0; the generator
  also pre-checked every name against all 5,231 existing function names).
* 161 creations: 0 blocked by an existing body, 0 null results.
* Every renamed owner was `rep_*` at the moment of rename; the two that had
  already been renamed by agents 2/3 were detected and kept.
* Nothing outside the funclet addresses and their 63 `rep_*` owners was
  modified; no `rep_*` that is not a funclet owner was touched (the 5 stale
  `rep_*` functions inside block 13 were deliberately left alone).

## 8. Hand-off notes

* The 68 stale-owner rows are the only thing blocking this range. They are
  spread over agents 2–4's `rep_*` ranges; whenever one of those owners is
  renamed for a *different* reason, the funclet can be completed with the
  pending pass above.
* `0x140336b00` / `0x140336b20` show that `free(*(frame+0x48))` bodies are
  ICF-folded across container helpers; their owner lists include one owner with
  no function object (`0x14016bf00`), which agent 9's range may want to create.

