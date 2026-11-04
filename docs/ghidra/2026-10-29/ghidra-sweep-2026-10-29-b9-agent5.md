# Ghidra sweep, batch 9 agent 5 — `rep_*` re-match B in `0x140100000–0x1401FFFFF`

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: every function still named `rep_*` whose entry point is in
`0x140100000–0x1401FFFFF` (batch-8 agent 5's range, third pass / Q2-B).
Start count: **326** live `rep_*` (the blackboard estimate of ~328).

| | count |
|---|---|
| `rep_*` in scope at start | 326 |
| **renamed + plated** | **33** |
| stale label (recorded, sharper row) | 293 |
| unreadable body | 0 (the former `0x1401a4da0` is readable — see below) |
| rows appended to `q2.tsv` | 326 (1326 → 1652) |

No `save_program`, no tags, no README/STATUS edits, no commits. Every rename
carries a plate (summary / `Algorithm:` / `Parameters:` / `Returns:`). The old
label is preserved in column 2 of the appended audit rows.

## Method

1. Listed all 326 by script (entry, size, insn count, caller count) and hashed
   the body address set. `0x1401a4da0` now hashes as UNREADABLE only because
   its body reaches an `EXTERNAL` address; the body itself decompiles and was
   read (see below).
2. Feature dump for all 326: callees, referenced string literals, referenced
   named globals, callers, so the stale rows carry concrete evidence rather
   than the old label.
3. **RTTI vtable scan.** For every function, walked the qword array that
   contains a pointer to it back to the vtable start, validated the
   `RTTICompleteObjectLocator` signature (`1`) and read the
   `TypeDescriptor` name. This produced the class+slot map used below
   (`hf_b9_a5_vtables.tsv`) and, separately, every function that *writes* a
   vtable (`hf_b9_a5_vtrefs.tsv`) — this is what finally identified the four
   unnamed `ResDesc` subclasses.
4. Targeted decompilation of ~55 bodies in batches of ≤10, all ≤0x2000 B.
   Every rename below was read.

## Renames (33)

| addr | old label | new name | proof |
|---|---|---|---|
| 0x140123c00 | `rep_14011d5a0_CopyString` | `FXPS_Constructor` | writes class name `"FXPS"` at +8, class word `0x8000000003` at +0x28, calls vtable +0x38; caller `CreateFX`; FXPS vtable 0x140360a70 |
| 0x14011a850 | `rep_140114980_CopyEscadraName` | `Escadra_UpdateContamination` | per-ship timer +0x2b4 -= hours/3600; builds `name + ":@10"` into `contaminationShipName_`; `CONTAMINATION_01` dialog |
| 0x140170420 | `rep_140164930_New` | `URTexture_EnsureCreated` | allocates 0x128, writes ResDesc vtable 0x140366650 then URTexture 0x140366690, media handle +0x90, `HashList_InsertNode` bucket 2 |
| 0x140179fb0 | `rep_14016e3c0_...atoi` | `URMusic_ParseResourceBlock` | writes URMusic vtable 0x1403666d0 over ResDesc base 0x140366650; `Resource_ParseNextToken`; called from `ParseResourceFile?` |
| 0x14017a2e0 | `rep_14016e6f0_...atoi` | `URParticle_ParseResourceBlock` | writes URParticle vtable 0x140366ce0 over ResDesc base |
| 0x14017afe0 | `rep_14016f3f0_...atoi` | `URTarget_ParseResourceBlock` | writes URTarget vtable 0x140366c60 over ResDesc base |
| 0x14017b380 | `rep_14016f790_...atoi` | `URTexture_ParseResourceBlock` | writes URTexture vtable 0x140366690 over ResDesc base |
| 0x14017b6b0 | `rep_14016fac0_PrintError` | `ResDesc_ParseFlagValue` | token 0x35..0x3a set/clear bits 0/1/2; `Unsupported value`; called by TextGrid and URFont parsers |
| 0x14017b780 | `rep_14016fb90_...atoi` | `ResDesc_ParseIndexedObject` | per-index bucket parser+0x10+idx*8, name at +8, chain +0x98, field copy, head insert |
| 0x14017ba40 | `rep_14016fe50_...atof` | `ResDesc_ParseCommonFields` | full ResDesc token switch (+0x88 int, +0xa0 name, +0x120..+0x144 rect/extents, +0x148 flags, +0x14c hex, +0x160 flags) |
| 0x14018f760 | `rep_140181c30_...free` | `IObject_Destructor` | installs `IObjectVFTable`, frees string +8, resets size/cap |
| 0x1401a4550 | `rep_140195ce0_New` | `Serializable_CopyConstructor` | IObject base copy, then `ISerializableVFTable`, deep-copies +0x30 list into 0x18 nodes, copies +0x40 |
| 0x1401a4da0 | `rep_1401964b0_...free` | `StringBuf_Destructor` | basic_stringbuf vtable (RTTI `1403714a0`), frees owned buffer, chains to `~basic_streambuf` |
| 0x14011a320 | `rep_140114450_...sqrtf` | `Escadra_UpdateMapMarkers` | player escadra ship icons: `renderMissilesOnMap`, `setXposYpos`, contact count +0xc04, colour/zoom/fade |
| 0x14015c340 | `rep_140150f90_New` | `SLinkVector_PushBack` | `New(0x68)` + `SLink_Constructor`, store at +0xc88 or `vec_realloc_insert(+0xc80)`; 83 callers |
| 0x1401b21c0 | `rep_1401a2290_givePlayerTraitMedals` | `Profile_AddMedalProgress` | switch picks profile counter pair, adds delta, mirrors int, calls `givePlayerTraitMedals` |
| 0x1401bbeb0 | `rep_1401abe30_FastFail?` | `Creature_HandleTutorialTrigger` | literal `"TUTORIAL"` (`0x4c4149524f545554`) via `CreateTriggerVal`, then vtable +0x68/+0x50, +0xad4 = -1 |
| 0x1401bfa10 | `rep_1401af5d0_..._Reallocate_exactly` | `Creature_CloneSubtree` | `Creature_FlattenTreeIntoVector` + `CopyObject` per node, `Node::add` relations, `AssignRandomId` on clone |
| 0x1401b08a0 | `rep_1401a0a70_LoadSeriaFile` | `Ship_LoadSeriaAndMarkPrize` | `Node(0x128)` + `LoadSeriaFile`; name at +0xa90 matched against Pegasus/Odyssey/Kastor/Pollux/Kadesh Mk1 → prize +0xc19 |
| 0x1401a3be0 | `rep_1401952a0_...basic_streambuf::_Init` | `File_OpenIfstream` | ifstream vtable + basic_ios + filebuf, `OpenFile_`, failbit on failure |
| 0x14018d2a0 | `rep_14017fbe0_...free` | `KeyBindings_ResetAll` | frees `binding` / `bindingMapmode` / `bindingOther` trees, resets counters, `SetDefaultKeyBindings` |
| 0x1401ce910 | `rep_1401b9880_New` | `Cinematic_BuildArgumentPanels` | `DIALOG_ARGUMENT` list sort + column layout, `cinematicDialouge_` per entry |
| 0x140119140 | `rep_140113280_Get_Profile?` | `Mark_UpdateIntel` | VMark slot 44; `Escadra_AddIntelEntry` to visible escadras, `PlayMorseSound`, two hour timers |
| 0x140171d50 | `rep_140166260_CreateHGE` | `hgeSprite_SetTextureRect` | creates 0x180 sprite from texture, HGE dims 0x318/0x320, four normalised corner sets; 37 callers |
| 0x1401ae060 | `rep_14019e780_displayOnUI?` | `Gui_DisplayStringOnUI` | unwraps std::string, tail-calls `displayOnUI_` |
| 0x14016bc70 | `rep_140160260_...memcmp` | `Gui_ResolveMediaName` | cached name +0xa98, else `CopyNameIntoMedia_(Media_res)` cached at +0xb78; 32 callers |
| 0x1401a9210 | `rep_140199930_...memcmp` | `Gui_FindElements` | walks `GUI_ELEMENTS`, element name +0xa40, prefix mode, appends to vector; 57 callers |
| 0x1401a8710 | `rep_140198e70_LoadNameIntoMedia` | `Font_SetupByName` | `LoadNameIntoMedia`, size +0x100c, `Font_SetGlyphParam`, optional `Font_SetColor`; 71 callers |
| 0x14016cfa0 | `rep_1401614b0_...floorf` | `hgeSprite_SetFrame` | frame % count +0x1c0, row/col, corner sets normalised, `Gfx_QuadSetFlip`; 21 callers |
| 0x14016f290 | `rep_1401637a0_...vsprintf` | `Text_DrawSingleLineFormat` | vsprintf into global 0x1439e8240 → `displayLableRotation_`, no wrap; 159 callers |
| 0x14016f340 | `rep_140163850_...vsprintf` | `Text_DrawWrappedFormat` | same plus glyph-width wrapping via +0x808/+0xc08/+0x1018; 55 callers |
| 0x1401640a0 | `rep_140158c20_CopyEscadraName` | `Replica_LayoutTextGrid` | VReplica slot 110; `Gui_LayoutText`, then 4x4 `TextGrid_SetCellPosition` |
| 0x1401a9420 | `rep_140199b40_...free` | `Gui_DestroyElementsByName` | calls `Gui_FindElements` (name in RCX), vtable +0x48 per match; 123 callers |

## Stale labels left in range (293) — sharper evidence in `q2.tsv`

Every appended stale row now carries: cluster, body size, concrete non-CRT
callees, string literals, RTTI-vtable membership (class+slot or "not referenced
from any RTTI vtable"), caller count/names, a fresh SHA-1 and the resolved
embedded target of the old label. Clusters:

| cluster | count | note |
|---|---|---|
| unclassified helper | 106 | mostly >0x400 B bodies not decompiled this pass; no vtable, small caller sets |
| small deallocation/cleanup thunk | 70 | only CRT/`free` callees, ≤250 B; many are compiler-generated deleting/users |
| ordered-container compare/copy helper (compData family) | 64 | `0x14018cbf0–0x1401a02a0`, `compareEscadraString`/`memcmp` shape |
| vector/array growth helper | 13 | `AllocateArrayOf8Byte`/`Array_*`/`vec_realloc_insert` |
| red-black tree insert/find helper | 11 | `RbTree_*`/`tooLongError` |
| `std::list` "list too long" variant | 10 | identical splice shape, only node/value type differs |
| tiny wrapper/stub | 7 | ≤120 B, no named callee |
| sort/introsort helper | 6 | `Sort_Introsort*`/`Sort_Heap*` |
| unordered_map/set "too long" variant | 4 | FNV-1a template |
| string-key ordered-container comparator | 2 | `compareEscadraString` + `memcmp` |

The `compData` family is one template family (38 of them sit between
`0x14018cbf0` and `0x1401a02a0`); splitting it needs the value-type token from
the caller, which is not recoverable from the body alone.

## Structural findings

* **Resource parser is table-driven and now fully mapped.** `ParseResourceFile?`
  dispatches to one parser per resource class:
  URMusic `0x140179fb0`, URParticle `0x14017a2e0`, URTarget `0x14017afe0`,
  URTexture `0x14017b380` (plus the already-named `URFont`, `TextGrid`).
  The parsers write `<class> vtable over the shared ResDesc base 0x140366650`,
  so the base is at object offset 0 and the class vtable at +0.
  Helpers: `ResDesc_ParseCommonFields`, `ResDesc_ParseFlagValue`,
  `ResDesc_ParseIndexedObject`, and the seven field-copy bodies
  `0x140174cd0..0x140177d10` (one per class; still unnamed).
* **ResDesc flag words**: `+0x148` is a 3-bit flag word parsed by
  `ResDesc_ParseFlagValue` (token ids 0x35..0x3a = clear/set pairs);
  `+0x160` is the extended 3-bit word parsed inline in
  `ResDesc_ParseCommonFields` (token ids 0x3b..0x40).
* **GUI element name is at `+0xa40`** (std::string, length +0xa50, capacity
  +0xa58), not at the property-name offset; `GUI_ELEMENTS` is the global
  intrusive list of all elements. `Gui_FindElements` supports prefix matching
  (third argument) — that is the general "find by name" primitive used 57×.
* **`hgeSprite`**: texture rect at +0x170..+0x184, texture dims +0x194/+0x190,
  frame count +0x1c0, current frame +0x1c4, flip flags +0x1a0..+0x1a2, and four
  vertex corner sets at +0x1c, +0x74, +0xcc, +0x124.
* **`FXPS`** object: class name at +0x08, class word `0x8000000003` at +0x28,
  string at +0x68, colour/alpha at +0x88, flags at +0x28; 0x260 bytes.
* **Contamination**: `contaminationShipName_` (`0x1403bd608` length,
  `0x1403bd610` capacity) holds `"<SHIP>:@10"`; the `:@10` suffix and
  `CONTAMINATION_01` dialog identify the contamination screen.
* **Prize ships**: `Ship_LoadSeriaAndMarkPrize` hard-codes Pegasus, Odyssey,
  Kastor, Pollux and `Kadesh Mk1`; the existing plate on that function already
  documented the `+0xc19` prize flag.

## Already-named neighbours checked (new §Rename rule)

Read four already-named functions in range to test the new wrong-name rule:
`Texture_Load` 0x14016cd50, `URParticle_EnsureCreated` 0x140179160,
`URParticle_Release` 0x140178b60 and `ResDesc_ScalarDeletingDtor` 0x140170140.
All four bodies match their existing names and plates; **no rename request was
posted**. No out-of-scope misnamed function was found worth reporting.

## Hand-off

* 33 address-keyed renames with plates; old labels in column 2 of `q2.tsv`.
* Cheapest next wins: name the seven `ResDesc` field-copy bodies
  `0x140174cd0..0x140177d10` once their per-class field sets are mapped
  (each copies a different `+0xa0..+0x150` subrange, so the ranges identify the
  class), and split the 10 `std::list` variants by caller value type.
* `0x140116040` (VExplosion slot 44, 4363 B), `0x14015a600` (7035 B) and
  `0x14018b530` (3563 B) remain unread because of the 0x2000-byte rule.
* `0x1401a4da0` is no longer unreadable; its UNREADABLE hash status is only
  the `EXTERNAL` byte in the body address set.
