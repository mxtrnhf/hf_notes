# Ghidra sweep, batch 10 agent 2 — open funclets B (`0x140342000–0x140350510`)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: the open funclets of `0x140342000–0x140350510` (funclet-ownership table
`docs/data/funclet-ownership-2026-10-29.tsv`, live state re-read from Ghidra).

**Note on the count:** the blackboard repeats "52 open funclets" for both funclet
agents; 52 is the batch total. The live slice contained **37** unnamed functions
(`FUN_*`/`rep_*`) in my range — agent 1 holds the other 15 in
`0x140336730–0x140341FFF` (37 + 15 = 52). Every one of the 37 is a row of the
ownership table; nothing outside the funclet set was touched.

**33 funclets named + plated; 15 stale owners renamed + plated; 4 still open.**
No already-named function was renamed. No `save_program`, tags, README/STATUS
edits or commits. Only `rename_function_by_address` and `set_plate_comment` were
used (both transactional), so no transaction was left open.

| | count |
|---|---|
| open funclets in this slice (live) | **37** |
| stale owners proven + renamed + plated | **15** |
| funclets named + plated | **33** |
| still open | **4** (1 aliased funclet record, 3 CRT EH helpers) |

## 1. Stale owners renamed (15)

All were carrying stale `rep_*` ICF-replica labels from the batch-2 pass. Each
identity was proven from the body plus its allocation/destructor helpers before
the funclet was named, so the two operations are consistent with each other.

### Vector / container instantiations (12)

| owner | old stale label | new name | proof |
|---|---|---|---|
| `0x1401993c0` | `rep_14018b3e0_…free` | **`VectorStride40_InsertMove`** | `vector<T>::insert(pos,T&&)`, 0x28-byte element (SSO string), 1.5× growth, `Array_MoveConstruct40`, `Array_DestroyRange40` |
| `0x140199650` | `rep_14018b670_…free` | **`VectorStride40_InsertMove_2`** | same stride/op, different value type (3-pointer buffer); destroys through `Thunk_DestroyVectorRange40`. `_2` follows the project's duplicate-name convention |
| `0x1401998e0` | `rep_14018b900_…free` | **`VectorStride3_Insert`** | 3-byte POD element, `Heap_FreeOverAlignedStride3` |
| `0x140199b60` | `rep_14018bb80_…free` | **`VectorStride272_InsertCopy`** | 0x110-byte element, `Array_CopyConstruct272`, `Array_FreeStride272` |
| `0x140199e10` | `rep_14018be30_…free` | **`VectorStride72_InsertMove`** | 0x48-byte element with two SSO strings, `Array_MoveConstruct144`, `Array_FreeStride72Alt` |
| `0x14019a0f0` | `rep_14018c110_…free` | **`VectorStride72_InsertCopy`** | copy counterpart, `Array_CopyStride72`, `Array_FreeStride72` |
| `0x14019aeb0` | `rep_14018cbf0_…memmove` | **`VectorStride8_InsertMapValueRange`** | counts a red-black map range (`+0x10/+0x18/+0x19` links), stores each node's 8-byte value into the vector, commits with `vector<u64>::_Change_array` |
| `0x140287c60` | `rep_140264e70_CopyEscadraName` | **`VectorStride80_InsertMoveNamePair`** | 0x50-byte element = two `CopyEscadraName` strings at +0/+0x20 + four dwords; `Array_MoveConstruct50`; sole caller `TadsDamage_AddEntry` |
| `0x1402ac2f0` | `rep_140289390_New` | **`VectorCityBuildingType_Insert`** | 0x30-byte records built by `City_InitBuildingTypes`, name at +8; destructor `NPC_ReleaseIteratorRange` |
| `0x1402e57a0` | `rep_…FID_conflict:~vector<GSISymbolEntry>` | **`VectorGSISymbolEntry_Insert`** | 0x38-byte element; element destructor symbol and `VectorGSI_DestroyRange` prove the type |
| `0x1402692f0` | `rep_1402476c0_…basic_ostream` | **`FormatFloatRoundedToString`** | snaps to `FLOAT_ARRAY_1403c1730[index]`, builds an `ostringstream` and copies its buffer into the out string |
| `0x140210790` | `rep_1401f5290_FastFail?` | **`Text_ExpandSignedDigitRuns`** | per char: count from a 4-slot table, sign from `param_7`, glyph from `Localization_FindEntry` (pos/neg/src triple), repeat \|count\| times |

### Radio / tutorial procedures (3)

| owner | old stale label | new name | proof |
|---|---|---|---|
| `0x140237e30` | `rep_140219d90_…ceilf` | **`EscadraName_WrapText`** | splits the text on spaces, keeps `ceil(words*ratio)` words, maps separators to `_`/space, emits an `EscadraName`; used by the radio report and `0x140238460` |
| `0x140238460` | `rep_14021a3c0_…sqrtf` | **`Radio_ReportContact`** | plays `RADIO_SAVE`, computes the bearing from the contact's +0x150/+0x154 position into `RadioBearing_`, gates on the `TUTORIAL` trigger, wraps the contact name, expands char stats (`charWealth/charForce/charFaith/charRight`), writes the creature radio text at `+0xc10` |
| `0x140253300` | `rep_140231a90_CopyString` | **`Tutorial_UpdateHuntedAlarm`** | guards on `profile->enigmaGot1`, plays `Dronish_descent`, copies `DAT_143a119d0` into `enigmaGot5..8`, sets `enigmaGot9..12`, reads/initialises `TUTORIAL_HUNTED` and checks `TUTORIAL_ALARM` + the `PETR` NPC |

These three were the batch-9 "area known, operation not provable" set. Reading the
full bodies (not just strings) settled the operations: `0x140238460` is a
*report generator* (bearing + stats + creature text), not a generic handler, and
`0x140253300` is an *alarm-state advance*, not a generic radio handler. Both names
stay at the operation level (no invented class/RTTI identity).

Owner plates are the four-line shape (summary / `Algorithm:` / `Parameters:` /
`Returns:`).

## 2. Funclets named + plated (33)

All named `<Owner>_EhCleanup_<member>` from the `.pdata` RUNTIME_FUNCTION /
FUNCINFO4 row; each plate records the live owner, the member, the destroy
operation and the temporary. Bodies were re-read with `disassemble_function`
before plating, and every `sz=` operand was matched to the allocation in the
owner.

### Owners already carrying a proven name (14)

| funclet | new name | member | family | body |
|---|---|---|---|---|
| `0x1403425c0` | `File_OpenIfstream_EhCleanup_0x50` | 0x50 | vdtor | `~basic_ios` on the ifstream temp via IAT `0x1403511e8` |
| `0x140342990` | `PrepareMainLoop_EhCleanup_0x30` | 0x30 | freeField | sized delete 0x80 |
| `0x1403429b0` | `PrepareMainLoop_EhCleanup_0x40` | 0x40 | freeField | sized delete 0x19380 |
| `0x140342b30` | `MapDecal_Constructor_EhCleanup_0x88` | 0x88 | freeField | sized delete 0x58 |
| `0x140342b50` | `Gui_UpdateRamMoral_EhCleanup_0xd0` | 0xd0 | string | `String_Tidy(frame+0xd0)`, guard +0x38 bit 0x1 |
| `0x140343fa0` | `FX_SpawnCloudPuff_EhCleanup_0x110` | 0x110 | freeField | sized delete 0xa40 |
| `0x140346c70` | `VectorStride64_InsertDefault_EhCleanup_0x70` | 0x70 | rethrow | destroy range + `deallocate` + throw |
| `0x140346d40` | `Array_Resize80_EhCleanup_0x60` | 0x60 | rethrow | `Array_DestroyRange80` + `deallocate` + throw |
| `0x140347b90` | `Profiler_CreateMainLoopNode_EhCleanup_0x38` | 0x38 | freeField | sized delete 0x3b8 |
| `0x140348bd0` | `SomethingWithLevelSerias_EhCleanup_0x3328` | 0x3328 | string | guard +0x98 bit 0x1000000 |
| `0x140348c60` | `SomethingWithLevelSerias_EhCleanup_0x33a8` | 0x33a8 | string | guard +0x98 bit 0x2000000 |
| `0x14034a2d0` | `VectorStride8_InsertPtrFieldFromStride24Range_EhCleanup_0x80` | 0x80 | rethrow | range rollback + throw |
| `0x14034a640` | `spawnGroundDefense_EhCleanup_0x80` | 0x80 | freeField | sized delete 0x1a0 |
| `0x14034a9c0` | `VectorStride24_ResizeDefault_EhCleanup_0x60` | 0x60 | rethrow | `Thunk_DestroyVectorRange24` + `deallocate` + throw |

### Owners renamed in this pass (19)

| funclet | new funclet name | member | family |
|---|---|---|---|
| `0x140342030` | `VectorStride40_InsertMove_EhCleanup_0x80` | 0x80 | rethrow |
| `0x140342080` | `VectorStride40_InsertMove_2_EhCleanup_0x80` | 0x80 | rethrow |
| `0x1403420d0` | `VectorStride3_Insert_EhCleanup_0x60` | 0x60 | rethrow |
| `0x140342110` | `VectorStride272_InsertCopy_EhCleanup_0xa0` | 0xa0 | rethrow |
| `0x140342150` | `VectorStride72_InsertMove_EhCleanup_0x80` | 0x80 | rethrow |
| `0x1403421b0` | `VectorStride72_InsertCopy_EhCleanup_0xa0` | 0xa0 | rethrow |
| `0x140342420` | `VectorStride8_InsertMapValueRange_EhCleanup_0x80` | 0x80 | rethrow |
| `0x140342500` | `VectorStride8_InsertMapValueRange_EhCleanup_0x80` | 0x80 | rethrow |
| `0x140344500` | `Text_ExpandSignedDigitRuns_EhCleanup_0x30` | 0x30 | string |
| `0x140345e70` | `FormatFloatRoundedToString_EhCleanup_0x40` | 0x40 | vdtor |
| `0x140345ea0` | `FormatFloatRoundedToString_EhCleanup_0x28` | 0x28 | string |
| `0x140346cf0` | `VectorStride80_InsertMoveNamePair_EhCleanup_0x80` | 0x80 | rethrow |
| `0x140347c30` | `VectorCityBuildingType_Insert_EhCleanup_0xa0` | 0xa0 | rethrow |
| `0x14034a8b0` | `VectorGSISymbolEntry_Insert_EhCleanup_0x80` | 0x80 | rethrow |
| `0x140345630` | `EscadraName_WrapText_EhCleanup_0x60` | 0x60 | string |
| `0x140345690` | `Radio_ReportContact_EhCleanup_0xa0` | 0xa0 | string |
| `0x1403456c0` | `Radio_ReportContact_EhCleanup_0x80` | 0x80 | string |
| `0x1403456f0` | `Radio_ReportContact_EhCleanup_0xa0` | 0xa0 | string |
| `0x140345b80` | `Tutorial_UpdateHuntedAlarm_EhCleanup_0x70` | 0x70 | string |

Note: `0x140342420` and `0x140342500` are two unwind entries of the **same**
parent (`VectorStride8_InsertMapValueRange`), so they deliberately share the
`_EhCleanup_0x80` name; Ghidra accepts the duplicate because only the address is
the identity. Same for the two `Radio_ReportContact_EhCleanup_0xa0` entries.

`0x140342150` deserves a note: at the start of the sweep it was a row marked "no
function object", but a function object now exists there
(`rep_14018be30_…_free_EhCleanup_0x80`, created by an earlier batch), so it was
renamed rather than created. No `create_function` was needed anywhere in this
slice.

## 3. Still open (4)

| funclet | recorded owner | reason |
|---|---|---|
| `0x140342380` | `0x1403423c0` (now `VectorString32_InsertRange_EhCleanup`) | aliased record: this cleanup has its own funcinfo4 (`0x1403add1c`, `U=0x140385d8c`) while the insert's is `0x1403adc60/U=0x1403adcc4`, so the "owner" is a *neighbouring funclet*, not a parent. Body is the end-pointer rollback (`RBX:=*(frame+0xb0); memmove-undo 0x1400199b0(frame+0xa0, frame+0x30, *RBX); *RBX:=*(frame+0xb8); throw`) and looks like a second cleanup of the `VectorString32_InsertRange` parent, but there is no way to prove *which* FuncInfo owns `0x1403add1c` from the body. Left open rather than guessing. |
| `0x14034b6b8` | `0x140334174` `` `eh_vector_destructor_iterator' `` | CRT helper: `if (!*(byte*)(frame+0x20)) __ArrayUnwind(frame+0x60, frame+0x68, frame+0x70, frame+0x78)`. This is compiler-generated EH glue for a vector destructor; the recorded owner is the CRT iterator itself, so any name would be a fabricated parent. |
| `0x14034b743` | `0x140334358` `__scrt_is_nonwritable_in_current_image` | corrupt record (TSV family `nobody`). Body is a filter predicate: `RAX:=*RCX; SETZ CL of (*(int*)RAX == 0xC0000005)` = `STATUS_ACCESS_VIOLATION` test. No EH, no matching temporary in the owner — naming it `__scrt_*` would be wrong (batch-9 agent 3 reached the same conclusion). |
| `0x14034b75b` | `0x140334c54` `mainCRTStartup` | body `RAX:=*RCX; RDX:=RCX; ECX:=*(int*)RAX; CALL 0x14033667e` — a `_seh_filter_exe`-shaped thunk. `mainCRTStartup` is not its parent (it has no such temporary), and the `pdata` extent `0x14034b75b–0x14034b779` is CRT EH glue. No provable parent → skipped. |

## 4. Method and hand-off

* Same method as batch 9: `.pdata` RUNTIME_FUNCTION + FUNCINFO4 gives
  owner/member; the funclet body confirms the destroy operation; the owner body
  confirms the temporary size. Every `sz=` in this slice matched an allocation in
  the owner.
* Container owners were named by **stride + operation** (the house style already
  used by `Array_Resize80`, `Array_InsertDefault80`, `VectorStride8_InsertValuePair32`,
  `VectorStride64_InsertDefault`, `Vector_InsertStride12`). No template argument
  was invented: where the element type is provable it is in the name
  (`GSISymbolEntry`, `CityBuildingType`), otherwise only the stride is used.
* `0x140342380` needs a FuncInfo4 → FuncInfo → UnwindMap walk to identify its
  real parent (binary data, not a body read) — good follow-up for whoever owns
  the EH table next; the funclet itself is a correct end-pointer rollback.
* The 3 CRT entries (`0x14034b6b8`, `0x14034b743`, `0x14034b75b`) are compiler
  EH glue, not game funclets; leaving them `rep_*`/`FUN_*` is the honest state.
