# Ghidra sweep, batch 10 agent 4 — `rep_*` B in `0x140100000–0x1401FFFFF`

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: every live `rep_*` whose entry point is in
`0x140100000–0x1401FFFFF` (the range of batch-9 agent 5, Q2-B).
Start count: **293** live `rep_*` (batch-9 left 293 stale rows in `q2.tsv`).

| | count |
|---|---|
| `rep_*` in scope at start | 293 |
| **renamed + plated** | **28** |
| stale label (sharper row appended) | 12 read closely this pass |
| unreadable body | 0 |
| rows appended to `q2.tsv` | 40 (1652 → 1692) |

Every rename carries a plate (summary / `Algorithm:` / `Parameters:` /
`Returns:`). No `save_program`, no tags, no README/STATUS edits, no commits.
Two renames (`ResourceFile_CopyFields`, `Loadouts_AddEntry`) target functions
whose current labels were `rep_wrap_*`; all others were `rep_<target>_*`.

The remaining 253 in-scope `rep_*` still carry batch-9 agent 5's sharper stale
rows in `q2.tsv` (feature dump, vtable slot, caller set, SHA-1); they were not
re-read this pass, and re-appending duplicates would only add noise.

## Renames (28)

| addr | old label | new name | proof |
|---|---|---|---|
| 0x1401bf100 | `rep_1401aecc0_FastFail?` | `Map_FormatLatLon` | two float axis components from the map extents (`float_5000`, `_2000`) / 720 + fixed offsets; integer degrees + fraction*60 minutes; `sprintf("%d*%d' %d*%d'")`; `CopyString` into a std::string; callers `VideoTask_RenderMapScene`, `variousHUDDisplays?` |
| 0x14016f4c0 | `rep_1401639d0_CreateHGE` | `URParticle_InitPool` | zeroes a 5000-entry 0x5c-stride particle array, `CreateHGE(0x180)` texture from param_2, copies the 0x84-byte sprite descriptor, releases the temp object; **sole caller `URParticle_EnsureCreated`** |
| 0x14016d5b0 | `rep_140161ac0_CreateHGE` | `TextGrid_InitCellGrid` | `Matrix3x3_Identity`, `CreateHGE(0x180)`, allocates `cols*rows` cells of 0x58 with 0.5 UV / -1 tex / white defaults; **sole caller `TextGrid_CreateObject`** |
| 0x1401a4710 | `rep_140195ea0_CopyString` | `PlaneLoadout_EntryConstructor` | 0x60-byte record: std::strings at +0/+0x20, 3 qwords +0x40..+0x50, float +0x58, flag +0x5c; caller `LoadPlaneLoadouts` |
| 0x1401a4250 | `rep_1401959e0_CopyEscadraName` | `ShipEntry_CopyConstructor` | copies 8 embedded 0x20-byte names (+0x28..+0x108), dword +0x20, flag +0x108 (0x110 element); callers `Array_CopyConstruct272`, `VectorShipEntry_PushBack` |
| 0x140161ae0 | `rep_140156670_...ceilf` | `Text_ProcessTildeDirectives` | detects `'~'`, switches on the next byte (1..6), consumes parameter bytes and writes HGE text globals `DAT_1439e7f9c..DAT_1439e7fd8` + font handle |
| 0x1401626e0 | `rep_140157270_..._invalid_parameter_noinfo_noreturn` | `Text_ProcessAtDirectives` | detects `'@'`, applies line advance with `ceilf` (clamped), writes encoded colour/length words through `DAT_1439e7fd0` and the text-metrics globals |
| 0x140169160 | `rep_14015dc40_FastFail?` | `Gfx_DrawWorldTickMark` | `atan2f` direction between two points, ±10-unit perpendicular quad, colour param_4, submitted through HGE vtable +0x2d0 |
| 0x140169420 | `rep_14015df00_...sinf` | `Text_DrawRichLabel` | guards +0xd18, `Font_SetupByName` from the name at +0xd88, copies text into `DAT_1403bd668`, resets layout globals then renders `~`/`@` directives; callers `Panel_Draw`, `Body_UpdateShellTrajectory` |
| 0x1401a4310 | `rep_140195aa0_FastFail?` | `OrderRecord_Constructor` | dword id at +0, two embedded std::strings at +8/+0x28, frees both temporary strings; caller `orderSelect1` |
| 0x1401a4840 | `rep_140195fd0_FastFail?` | `NamedVec3_Constructor` | name std::string at +0, three floats +0x20/+0x24/+0x28, frees the temporary; caller `spawnTradeConvoy?` |
| 0x1401a4910 | `rep_1401960a0_FastFail?` | `NamedSize_Constructor` | name std::string at +0, two floats +0x20/+0x24, frees the temporary; caller `displayCharTraitsMouseOver` |
| 0x1401a5e40 | `rep_140197480_...free` | `PlaneLoadout_EntryDestructor` | frees the 0x40-stride string array at +0x40 and the strings at +0/+0x20; caller `LoadPlaneLoadouts`; field layout matches 0x1401a4710 |
| 0x1401a61a0 | `rep_1401977e0_...free` | `OwnedPointerVector_Destructor` | calls virtual deleting-dtor(obj,1) over [+0x10,+0x18), rewinds end, frees backing and zeroes the three vector words |
| 0x140174cd0 | `rep_wrap_0_FUN_14016c7d0` | `TextGrid_CopyFields` | shared ResDesc field copy then byte block +0xa0..+0x150; **sole caller `TextGrid_ParseResourceBlock`** |
| 0x140175410 | `rep_wrap_0_FUN_14016c7d0` | `URFont_CopyFields` | shared ResDesc field copy then +0xa0..+0x140; **sole caller `URFont_ParseResourceBlock`** |
| 0x140175b20 | `rep_wrap_0_FUN_14016c7d0` | `URMusic_CopyFields` | shared ResDesc field copy then +0xa0..+0x120; **sole caller `URMusic_ParseResourceBlock`** |
| 0x1401761d0 | `rep_wrap_0_FUN_14016c7d0` | `URParticle_CopyFields` | shared ResDesc field copy then the large block +0xa0..+0x19f; **sole caller `URParticle_ParseResourceBlock`** |
| 0x140176f00 | `rep_wrap_0_FUN_14016c7d0` | `ResDesc_CopyIndexedFields` | shared ResDesc field copy then +0xa0..+0x11f; **sole caller `ResDesc_ParseIndexedObject`** |
| 0x1401775b0 | `rep_wrap_0_FUN_14016c7d0` | `ResourceFile_CopyFields` | shared ResDesc field copy then +0xa0..+0x155 incl. two trailing flags; caller `ParseResourceFile_` for the object with vtable 0x140366c40 |
| 0x140177d10 | `rep_wrap_0_FUN_14016c7d0` | `URTexture_CopyFields` | shared ResDesc field copy then +0xa0..+0x120; **sole caller `URTexture_ParseResourceBlock`** |
| 0x1401720e0 | `rep_1401665f0_...sinf` | `Gfx_QuadSetGeometry` | rebuilds four hgeVertex corners (0x28 stride, u/v at +0x13/+0x14) from half-extents +0x188/+0x18c, cos/sin rotation about the centre |
| 0x1401a2b30 | `rep_1401941f0_...memcmp` | `StringList_FindNode` | walks next-links to a sentinel, compares node std::string length (+0x20) then `memcmp`, returns the first match iterator |
| 0x1401a3070 | `rep_wrap_0_rep_140188780_compData` | `Loadouts_AddEntry` | calls `AddToLoadouts` and copies its 9-byte `{pointer,flag}` result to the out record; caller `LoadPlaneLoadouts` |
| 0x14015c540 | `rep_140151190_CopyEscadraName` | `List_AddItem` | push-back name (0x20) into +0xe70 and Link (0x18) into +0xe88, frees the temp Link, syncs slider max/value at +0xed8/+0xa88/+0xe74; callers `ShipDesign_EnumerateDesignFiles`, `setupPropsSecondaryMapModes` |
| 0x1401b5e60 | `rep_1401a5d90_CopyObject` | `Creature_FinalizeNewCreature` | consumes staging globals (`someNewCreature`, timer `DAT_1439f14cc`), rebuilds subtree, `BodyArray_AppendFromPtrArray`, name +0xa90, `CalculateStats`, `Ship_RebuildAfterPartEdit` for 0x1f-flag bodies; caller `SomethingWithLevelSerias` |
| 0x1401b5140 | `rep_1401a5150_GetStats` | `Creature_CreateAndAttachBody` | positions a body between reference bodies, `GlobalNode_` add, `Body_TryAttachBodies`, destroys on failure, `Map_InsertU64Node`; callers `Shipworks_BuildAutoRepairSteps`, `memmoveMAIN` |
| 0x1401a3e80 | `rep_wrap_0_CopyEscadraName` | `ValueAndName_CopyConstructor` | copies the qword at +0 and copy-constructs the embedded std::string at +8 |

## Why the seven field-copy bodies are now provable

Batch 9 flagged `0x140174cd0..0x140177d10` as cheap next wins but had no
per-class evidence. Each is called from exactly one parser (except
`0x1401775b0`), and the copied tail range differs:

| body | tail end | caller |
|---|---|---|
| 0x140174cd0 | +0x150 | `TextGrid_ParseResourceBlock` |
| 0x140175410 | +0x140 | `URFont_ParseResourceBlock` |
| 0x140175b20 | +0x120 | `URMusic_ParseResourceBlock` |
| 0x1401761d0 | +0x19f | `URParticle_ParseResourceBlock` |
| 0x140176f00 | +0x11f | `ResDesc_ParseIndexedObject` |
| 0x1401775b0 | +0x155 | `ParseResourceFile_` (vtable 0x140366c40) |
| 0x140177d10 | +0x120 | `URTexture_ParseResourceBlock` |

So `URMusic` and `URTexture` share the same 0x120 tail extent but are
distinguished by their caller; `URParticle` has by far the largest field set.

## Structural findings

* **Rich-text parser split into three bodies.** `Text_DrawRichLabel`
  (`0x140169420`) owns the font/state setup, then two directive handlers:
  `Text_ProcessTildeDirectives` (`0x140161ae0`) for `~` and
  `Text_ProcessAtDirectives` (`0x1401626e0`) for `@`. The shared text layout
  state lives in the `0x1439e7f9c..0x1439e7fe0` globals; the output string is
  the global at `0x1403bd668` (length `0x1403bd680`).
* **`hgeQuad` layout confirmed**: 4 vertices of 0x28 bytes, x/y at +0/+4,
  u/v at +0x13/+0x14 relative to each vertex; half extents at +0x188/+0x18c.
  This complements batch-9's `hgeSprite` map.
* **Plane-loadout records** are 0x60 bytes (two std::strings, a 0x40-stride
  string array, a float and a flag); ship entries in the same subsystem are
  0x110 bytes with eight embedded 0x20-byte names. `AddToLoadouts` returns a
  9-byte `{pointer,flag}` pair.
* **Body construction** for shipworks repair uses
  `Creature_CreateAndAttachBody` + `Creature_FinalizeNewCreature`; the staging
  globals `someNewCreature`, `DAT_1439f14c0`, `DAT_1439f14cc` belong to that
  path.

## Stale read this pass (12, sharper rows in `q2.tsv`)

`0x140173330` (chain destructor + shared-HGE release), `0x140173d70`
(resource object init, no class name write), `0x1401741a0` (`FreeLibrary` on
+0x988), `0x140170a20` (`_vcomp_fork` thunk), `0x1401a30a0` and `0x1401a34f0`
(two 6.6 KB `__RTDynamicCast` container walks), `0x14015c7f0` (creature
background sprite scale/teardown), `0x1401c9840` (2263-byte profile/Seria file
enumeration), `0x14016f6a0` (generic 0x28-stride vector growth),
`0x140181880` (stdio-stream vtable install), `0x140181170` (streambuf-style
circular-buffer refill), `0x14017ec70` (`__stdio_common_vfprintf` forwarder).

None yielded a class/vtable identity from the body alone, so no rename.

## Hand-off

* 28 address-keyed renames with plates; old labels in column 2 of the appended
  `q2.tsv` rows.
* Still open in range: the compData family (`0x14018cbf0–0x1401a02a0`, 64),
  the 0x1401a4xxx cleanup-thunk hierarchy (destructor chain identifies the
  owning type only through the vtable, not the body), the two 6.6 KB RTTI
  walks, and `0x14015a600`/`0x14018b530`/`0x140116040` (over the 0x2000-byte
  read limit).
* `0x14016f4c0` and `0x14016d5b0` were the last two `CreateHGE`-named bodies in
  the range; both are now class init routines.
