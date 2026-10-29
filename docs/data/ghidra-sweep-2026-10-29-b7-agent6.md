# Unnamed-function sweep — batch 7 agent 6 (CRT C-initialiser table)

Scope: `.rdata` CRT C-initialiser table `0x1403519e8–0x1403521a8` (249 qword
entries) on `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Role: create/name the table targets in `0x140001000–0x140004a60` that had no
function object. **149 created + named + plated, 1 skipped/recorded.**

## Census

* 249 entries, **249 unique targets** (no duplicates).
* 99 targets already had a function object before this pass (the `InitGlobal_*`
  family from earlier batches).
* **150** had none. Of those, **149** are now functions; `0x140334c38` is skipped
  (below).
* After the pass every table target has a function object except that one:
  **248/249**. Verified programmatically: each created function sits exactly at
  its target, no body overlaps the next function entry, and every one has a
  plate.

Name map produced by the pass: `/tmp/opencode/hf_ghidra_sweep/cinit_live.tsv`;
plate source: `/tmp/opencode/hf_ghidra_sweep/cinit_plates.tsv`.

## Corrected pattern (supersedes b6 agent 9's description)

b6 wrote "every one has the shape `LEA RCX,[<global>]; JMP <ctor>`". That is only
half true, and the difference matters:

* **129 of the 150 are `LEA RCX,[<target>]; JMP 0x14033447c`**, and
  `0x14033447c` is **`atexit`** (Ghidra: "Library Function - Single Match",
  Library: Visual Studio 2019 Release). It calls `_onexit` `0x140334440` ->
  `_register_onexit_function`. So `<target>` is an **exit-time callback**, and in
  practice the MSVC "dynamic atexit destructor" of a global; the target is code
  in the `/EH` dtor region `0x14034b780–0x140350510`, not a data global. Examples:
  `0x14034b780` `DtorGlobal_LevelListHeadB` -> `0x1403c6330`,
  `0x14034c1c0` `DtorGlobal_AmmoLink` -> `AMMO_LINK` `0x1403bd440`.
  Many of these dtor symbols were renamed to `DtorGlobal_*` by agent 5 during
  this same batch, which is why most tags below are now readable.
* **20 are compound initialisers / constant stores** (zero-fill of big arrays,
  `ScreenWidth`/`ScreenHeight`, vector construction, vtable/`PLANE_TLL`
  installation, `VideoSettings_RegisterProperties`). These are the only real
  constructor-shaped entries.

Consequence for naming: for the 129 atexit rows the `LEA` operand is the
*callback*, not the object, so they are named `CInit_Atexit_<Tag>` rather than
`CInit_<Global>`; the plate records the registered callback and, where the
callback's first two instructions expose it, the global it tears down. The 20
constructor rows keep the requested `CInit_<Global>` scheme.

## Naming scheme

* Atexit rows: `CInit_Atexit_<Tag>`:
  * `DtorGlobal_<X>` -> `CInit_Atexit_<X>` (76 rows, e.g.
    `CInit_Atexit_AmmoLink`);
  * otherwise the callback address, `CInit_Atexit_<hex>` (53 rows, e.g.
    `CInit_Atexit_14034bc20`; these callbacks are still `FUN_*`/`LAB_*` or are
    compiler/CRT helpers with no provable object name).
* Constructor rows: `CInit_<Global>`, with `<Global>` the primary global symbol,
  or `DAT_<addr>` / bare address when unnamed
  (`CInit_ScreenWidth`, `CInit_DAT_1403edfd0`, `CInit_1403ef0f8`).

All names were checked against the global symbol table before creation: 0
collisions. None of the target addresses was inside an existing function body.

## Created — 20 constructor/store entries

| entry | name | target | note |
|---|---|---|---|
| `0x140001000` | `CInit_DAT_1403c6330` | `0x0` | compound init |
| `0x140001140` | `CInit_DAT_1403edfd0` | `0x1403edfd0` | DAT_1403edfd0 |
| `0x140001160` | `CInit_sprite_unset` | `0x140352968` | s_sprite_unset_140352968 |
| `0x140001260` | `CInit_1403ef0f8` | `0x0` | compound init |
| `0x1400014a0` | `CInit_DAT_1403bd548` | `0x14035b988` | s_ect_14035b980+8 |
| `0x140002c50` | `CInit_DAT_1439ef1c0` | `0x0` | compound init |
| `0x140002cb0` | `CInit_DAT_1439e9310` | `0x0` | compound init |
| `0x140003070` | `CInit_DAT_143a15b00` | `0x0` | compound init |
| `0x140003040` | `CInit_DAT_1403c13d0` | `0x1403690c4` | DAT_1403690c4 |
| `0x1400032e0` | `CInit_DAT_1403c1410` | `0x14035a2d8` | s_tv_screen_01_14035a2d8 |
| `0x140003320` | `CInit_ScreenWidth` | `0x1403566e0` | DAT_1403566e0 |
| `0x140003310` | `CInit_ScreenHeight` | `0x1403566e4` | DAT_1403566e4 |
| `0x1400032d0` | `CInit_GraphicsFrameWidth` | `0x1403566e0` | DAT_1403566e0 |
| `0x1400032c0` | `CInit_GraphicsFrameHeight` | `0x1403566e4` | DAT_1403566e4 |
| `0x1400035d0` | `CInit_PLANE_TLL` | `0x0` | compound init |
| `0x1400049e0` | `CInit_DAT_14801fd10` | `0x143a158fc` | graphicsFrameWidth |
| `0x140004650` | `CInit_DAT_14801fd30` | `0x14801fd30` | DAT_14801fd30 |
| `0x140004690` | `CInit_DAT_148021cc0` | `0x148021cc0` | DAT_148021cc0 |
| `0x140004670` | `CInit_DAT_14801dd90` | `0x14801dd90` | DAT_14801dd90 |
| `0x140004930` | `CInit_DAT_14801fd00` | `0x14801fd00` | DAT_14801fd00 |

## Created — 76 atexit rows with a named `DtorGlobal_*` callback

| entry | name | target | note |
|---|---|---|---|
| `0x140001240` | `CInit_Atexit_Container_1403ef090` | `0x14034bc20` | DtorGlobal_Container_1403ef090 (atexit target) |
| `0x140001250` | `CInit_Atexit_SharedObject` | `0x14034bb60` | DtorGlobal_SharedObject (atexit target) |
| `0x140001400` | `CInit_Atexit_GameEndFreeLoop` | `0x14034bdc0` | DtorGlobal_GameEndFreeLoop (atexit target) |
| `0x1400014f0` | `CInit_Atexit_Container_1403ef428` | `0x14034c040` | DtorGlobal_Container_1403ef428 (atexit target) |
| `0x1400014e0` | `CInit_Atexit_Container_1403ef498` | `0x14034bfd0` | DtorGlobal_Container_1403ef498 (atexit target) |
| `0x140001770` | `CInit_Atexit_RosterLink` | `0x14034c4e0` | DtorGlobal_RosterLink (atexit target) |
| `0x140001780` | `CInit_Atexit_GuiElementLinkB` | `0x14034c4f0` | DtorGlobal_GuiElementLinkB (atexit target) |
| `0x140001530` | `CInit_Atexit_ShopDisplayString` | `0x14034c0c0` | DtorGlobal_ShopDisplayString (atexit target) |
| `0x140001540` | `CInit_Atexit_ShipworksRecordVector` | `0x14034c130` | DtorGlobal_ShipworksRecordVector (atexit target) |
| `0x140001660` | `CInit_Atexit_MapPinLink` | `0x14034c2a0` | DtorGlobal_MapPinLink (atexit target) |
| `0x140001490` | `CInit_Atexit_Container_1403ef450` | `0x14034bef0` | DtorGlobal_Container_1403ef450 (atexit target) |
| `0x140001480` | `CInit_Atexit_Container_1403ef468` | `0x14034be50` | DtorGlobal_Container_1403ef468 (atexit target) |
| `0x140001620` | `CInit_Atexit_HullLink` | `0x14034c260` | DtorGlobal_HullLink (atexit target) |
| `0x140001590` | `CInit_Atexit_ArmorLink` | `0x14034c1d0` | DtorGlobal_ArmorLink (atexit target) |
| `0x1400015f0` | `CInit_Atexit_FuelLink` | `0x14034c230` | DtorGlobal_FuelLink (atexit target) |
| `0x140001580` | `CInit_Atexit_AmmoLink` | `0x14034c1c0` | DtorGlobal_AmmoLink (atexit target) |
| `0x140001630` | `CInit_Atexit_LegLink` | `0x14034c270` | DtorGlobal_LegLink (atexit target) |
| `0x1400015d0` | `CInit_Atexit_EngineLink` | `0x14034c210` | DtorGlobal_EngineLink (atexit target) |
| `0x140001610` | `CInit_Atexit_GunLink` | `0x14034c250` | DtorGlobal_GunLink (atexit target) |
| `0x140001650` | `CInit_Atexit_SensorLink` | `0x14034c290` | DtorGlobal_SensorLink (atexit target) |
| `0x1400015e0` | `CInit_Atexit_ExpendableLink` | `0x14034c220` | DtorGlobal_ExpendableLink (atexit target) |
| `0x1400015a0` | `CInit_Atexit_CraftLink` | `0x14034c1e0` | DtorGlobal_CraftLink (atexit target) |
| `0x1400015b0` | `CInit_Atexit_DefenceLink` | `0x14034c1f0` | DtorGlobal_DefenceLink (atexit target) |
| `0x140001600` | `CInit_Atexit_GeneratorLink` | `0x14034c240` | DtorGlobal_GeneratorLink (atexit target) |
| `0x140001640` | `CInit_Atexit_QuarterLink` | `0x14034c280` | DtorGlobal_QuarterLink (atexit target) |
| `0x1400015c0` | `CInit_Atexit_EmergencyLink` | `0x14034c200` | DtorGlobal_EmergencyLink (atexit target) |
| `0x1400017e0` | `CInit_Atexit_ContaminationShipName` | `0x14034c5a0` | DtorGlobal_ContaminationShipName (atexit target) |
| `0x140001880` | `CInit_Atexit_Container_1439e5f98` | `0x14034c7a0` | DtorGlobal_Container_1439e5f98 (atexit target) |
| `0x140002bd0` | `CInit_Atexit_Container_1439e7fe8` | `0x14034c980` | DtorGlobal_Container_1439e7fe8 (atexit target) |
| `0x140002be0` | `CInit_Atexit_String_1403bd668` | `0x14034c9f0` | DtorGlobal_String_1403bd668 (atexit target) |
| `0x140002e40` | `CInit_Atexit_LinkVector240` | `0x14034cff0` | DtorGlobal_LinkVector240 (atexit target) |
| `0x140003420` | `CInit_Atexit_Container_143a13e30` | `0x14034da10` | DtorGlobal_Container_143a13e30 (atexit target) |
| `0x140003140` | `CInit_Atexit_Container_143a13b78` | `0x14034d5e0` | DtorGlobal_Container_143a13b78 (atexit target) |
| `0x1400030c0` | `CInit_Atexit_SeriaToLoad` | `0x14034d510` | DtorGlobal_SeriaToLoad (atexit target) |
| `0x140002f30` | `CInit_Atexit_AtanCache` | `0x14034d290` | DtorGlobal_AtanCache (atexit target) |
| `0x140002f20` | `CInit_Atexit_Pi2Cash` | `0x14034d220` | DtorGlobal_Pi2Cash (atexit target) |
| `0x140003d20` | `CInit_Atexit_AmmoList` | `0x14034e380` | DtorGlobal_AmmoList (atexit target) |
| `0x1400036d0` | `CInit_Atexit_CaptainVector` | `0x14034dc70` | DtorGlobal_CaptainVector (atexit target) |
| `0x1400037a0` | `CInit_Atexit_EscadraNameList` | `0x14034de60` | DtorGlobal_EscadraNameList (atexit target) |
| `0x1400037b0` | `CInit_Atexit_EscadraNameList2` | `0x14034dee0` | DtorGlobal_EscadraNameList2 (atexit target) |
| `0x1400037c0` | `CInit_Atexit_CallsignList` | `0x14034df60` | DtorGlobal_CallsignList (atexit target) |
| `0x1400037d0` | `CInit_Atexit_EscadraNameList3` | `0x14034dfe0` | DtorGlobal_EscadraNameList3 (atexit target) |
| `0x1400040f0` | `CInit_Atexit_Container_143a13ad8` | `0x14034eb20` | DtorGlobal_Container_143a13ad8 (atexit target) |
| `0x140003a90` | `CInit_Atexit_Container_143a15880` | `0x14034e1c0` | DtorGlobal_Container_143a15880 (atexit target) |
| `0x140003750` | `CInit_Atexit_String_1403c1670` | `0x14034ddc0` | DtorGlobal_String_1403c1670 (atexit target) |
| `0x140003740` | `CInit_Atexit_Container_143a15918` | `0x14034dd50` | DtorGlobal_Container_143a15918 (atexit target) |
| `0x1400041a0` | `CInit_Atexit_StatList` | `0x14034ee20` | DtorGlobal_StatList (atexit target) |
| `0x1400041e0` | `CInit_Atexit_CreatureDllAiVector` | `0x14034ef60` | DtorGlobal_CreatureDllAiVector (atexit target) |
| `0x1400041f0` | `CInit_Atexit_Container_143faa638` | `0x14034ef70` | DtorGlobal_Container_143faa638 (atexit target) |
| `0x140004280` | `CInit_Atexit_Container_143faa650` | `0x14034f100` | DtorGlobal_Container_143faa650 (atexit target) |
| `0x140004270` | `CInit_Atexit_Container_143faa668` | `0x14034f090` | DtorGlobal_Container_143faa668 (atexit target) |
| `0x140004290` | `CInit_Atexit_ProfileList` | `0x14034f170` | DtorGlobal_ProfileList (atexit target) |
| `0x140004490` | `CInit_Atexit_Container_1403c2b80` | `0x14034f910` | DtorGlobal_Container_1403c2b80 (atexit target) |
| `0x140004410` | `CInit_Atexit_LevelBackground` | `0x14034f6a0` | DtorGlobal_LevelBackground (atexit target) |
| `0x140004500` | `CInit_Atexit_Container_147fc7560` | `0x14034f9c0` | DtorGlobal_Container_147fc7560 (atexit target) |
| `0x1400045b0` | `CInit_Atexit_AaDefenseList` | `0x14034fb50` | DtorGlobal_AaDefenseList (atexit target) |
| `0x140004460` | `CInit_Atexit_Container_147fc7490` | `0x14034f780` | DtorGlobal_Container_147fc7490 (atexit target) |
| `0x140004470` | `CInit_Atexit_BuildingCodes` | `0x14034f830` | DtorGlobal_BuildingCodes (atexit target) |
| `0x140004550` | `CInit_Atexit_Container_1403c2bf0` | `0x14034fa50` | DtorGlobal_Container_1403c2bf0 (atexit target) |
| `0x1400045a0` | `CInit_Atexit_Container_1403c2c10` | `0x14034fae0` | DtorGlobal_Container_1403c2c10 (atexit target) |
| `0x140004a20` | `CInit_Atexit_Container_14801fcd0` | `0x140350410` | DtorGlobal_Container_14801fcd0 (atexit target) |
| `0x1400049d0` | `CInit_Atexit_Container_14801dd78` | `0x140350380` | DtorGlobal_Container_14801dd78 (atexit target) |
| `0x140004940` | `CInit_Atexit_Container_14801fd18` | `0x14034ff50` | DtorGlobal_Container_14801fd18 (atexit target) |
| `0x1400049c0` | `CInit_Atexit_Container_148075cc8` | `0x1403502d0` | DtorGlobal_Container_148075cc8 (atexit target) |
| `0x1400049b0` | `CInit_Atexit_Container_148075cb0` | `0x140350260` | DtorGlobal_Container_148075cb0 (atexit target) |
| `0x140004950` | `CInit_Atexit_Container_148075c98` | `0x14034ffc0` | DtorGlobal_Container_148075c98 (atexit target) |
| `0x140004920` | `CInit_Atexit_Container_14801dd18` | `0x14034fee0` | DtorGlobal_Container_14801dd18 (atexit target) |
| `0x1400048f0` | `CInit_Atexit_Container_148021c70` | `0x14034fdd0` | DtorGlobal_Container_148021c70 (atexit target) |
| `0x1400048e0` | `CInit_Atexit_Container_14801dd30` | `0x14034fd60` | DtorGlobal_Container_14801dd30 (atexit target) |
| `0x140004960` | `CInit_Atexit_Container_148021c88` | `0x140350030` | DtorGlobal_Container_148021c88 (atexit target) |
| `0x140004970` | `CInit_Atexit_Container_148021ca8` | `0x1403500a0` | DtorGlobal_Container_148021ca8 (atexit target) |
| `0x140004980` | `CInit_Atexit_Container_14801fce8` | `0x140350110` | DtorGlobal_Container_14801fce8 (atexit target) |
| `0x140004990` | `CInit_Atexit_Container_14801dd48` | `0x140350180` | DtorGlobal_Container_14801dd48 (atexit target) |
| `0x1400049a0` | `CInit_Atexit_Container_148075c80` | `0x1403501f0` | DtorGlobal_Container_148075c80 (atexit target) |
| `0x140004900` | `CInit_Atexit_ExplosionDebrisLink` | `0x14034fe40` | DtorGlobal_ExplosionDebrisLink (atexit target) |
| `0x140004a30` | `CInit_Atexit_Container_14801dcd0` | `0x140350480` | DtorGlobal_Container_14801dcd0 (atexit target) |

## Created — 53 atexit rows named by callback address

| entry | name | target | note |
|---|---|---|---|
| `0x140004a5c` | `CInit_Atexit_140350510` | `0x140350510` | ~_Fac_tidy_reg_t (atexit target) |
| `0x140001130` | `CInit_Atexit_14034b850` | `0x14034b850` | FUN_14034b850 (atexit target) |
| `0x140001230` | `CInit_Atexit_14034bbb0` | `0x14034bbb0` | FUN_14034bbb0 (atexit target) |
| `0x140001670` | `CInit_Atexit_14034c2b0` | `0x14034c2b0` | FUN_14034c2b0 (atexit target) |
| `0x140001750` | `CInit_Atexit_14034c4a0` | `0x14034c4a0` | FUN_14034c4a0 (atexit target) |
| `0x140001760` | `CInit_Atexit_14034c4c0` | `0x14034c4c0` | FUN_14034c4c0 (atexit target) |
| `0x1400017c0` | `CInit_Atexit_14034c580` | `0x14034c580` | FUN_14034c580 (atexit target) |
| `0x1400017d0` | `CInit_Atexit_14034c590` | `0x14034c590` | FUN_14034c590 (atexit target) |
| `0x1400018d0` | `CInit_Atexit_14034c880` | `0x14034c880` | FUN_14034c880 (atexit target) |
| `0x1400018c0` | `CInit_Atexit_14034c870` | `0x14034c870` | FUN_14034c870 (atexit target) |
| `0x1400018e0` | `CInit_Atexit_14034c890` | `0x14034c890` | FUN_14034c890 (atexit target) |
| `0x140002d10` | `CInit_Atexit_14034ce20` | `0x14034ce20` | FUN_14034ce20 (atexit target) |
| `0x140002d90` | `CInit_Atexit_14034ce80` | `0x14034ce80` | FUN_14034ce80 (atexit target) |
| `0x140002d70` | `CInit_Atexit_14034ce60` | `0x14034ce60` | FUN_14034ce60 (atexit target) |
| `0x140002d20` | `CInit_Atexit_14034ce30` | `0x14034ce30` | FUN_14034ce30 (atexit target) |
| `0x140002da0` | `CInit_Atexit_14034ce90` | `0x14034ce90` | FUN_14034ce90 (atexit target) |
| `0x140002d80` | `CInit_Atexit_14034ce70` | `0x14034ce70` | FUN_14034ce70 (atexit target) |
| `0x140002e30` | `CInit_Atexit_14034cf60` | `0x14034cf60` | FUN_14034cf60 (atexit target) |
| `0x140003ec0` | `CInit_Atexit_14034e6e0` | `0x14034e6e0` | FUN_14034e6e0 (atexit target) |
| `0x1400030d0` | `CInit_Atexit_LAB_14034d580` | `0x14034d580` | LAB_14034d580 (atexit target) |
| `0x140003160` | `CInit_Atexit_zeroOutCertainData` | `0x14034d6d0` | zeroOutCertainData (atexit target) |
| `0x1400033b0` | `CInit_Atexit_14034d960` | `0x14034d960` | FUN_14034d960 (atexit target) |
| `0x140003390` | `CInit_Atexit_14034d940` | `0x14034d940` | FUN_14034d940 (atexit target) |
| `0x1400033c0` | `CInit_Atexit_14034d970` | `0x14034d970` | FUN_14034d970 (atexit target) |
| `0x1400033a0` | `CInit_Atexit_14034d950` | `0x14034d950` | FUN_14034d950 (atexit target) |
| `0x140003410` | `CInit_Atexit_14034d9a0` | `0x14034d9a0` | FUN_14034d9a0 (atexit target) |
| `0x1400033d0` | `CInit_Atexit_14034d980` | `0x14034d980` | FUN_14034d980 (atexit target) |
| `0x140003150` | `CInit_Atexit_14034d650` | `0x14034d650` | FUN_14034d650 (atexit target) |
| `0x140003030` | `CInit_Atexit_14034d430` | `0x14034d430` | FUN_14034d430 (atexit target) |
| `0x140002f80` | `CInit_Atexit_14034d320` | `0x14034d320` | FUN_14034d320 (atexit target) |
| `0x140003aa0` | `CInit_Atexit_14034e280` | `0x14034e280` | FUN_14034e280 (atexit target) |
| `0x140003b40` | `CInit_Atexit_14034e2c0` | `0x14034e2c0` | FUN_14034e2c0 (atexit target) |
| `0x140003c20` | `CInit_Atexit_14034e320` | `0x14034e320` | FUN_14034e320 (atexit target) |
| `0x140003e50` | `CInit_Atexit_14034e5f0` | `0x14034e5f0` | FUN_14034e5f0 (atexit target) |
| `0x140003e40` | `CInit_Atexit_14034e570` | `0x14034e570` | FUN_14034e570 (atexit target) |
| `0x140003e30` | `CInit_Atexit_14034e4f0` | `0x14034e4f0` | FUN_14034e4f0 (atexit target) |
| `0x140003a80` | `CInit_Atexit_14034e150` | `0x14034e150` | FUN_14034e150 (atexit target) |
| `0x140003f70` | `CInit_Atexit_14034e730` | `0x14034e730` | FUN_14034e730 (atexit target) |
| `0x140004200` | `CInit_Atexit_14034efe0` | `0x14034efe0` | FUN_14034efe0 (atexit target) |
| `0x140004250` | `CInit_Atexit_14034f010` | `0x14034f010` | FUN_14034f010 (atexit target) |
| `0x140004260` | `CInit_Atexit_14034f080` | `0x14034f080` | CFUN_1401228f0 (atexit target) |
| `0x1400042a0` | `CInit_Atexit_14034f1e0` | `0x14034f1e0` | FUN_14034f1e0 (atexit target) |
| `0x140004480` | `CInit_Atexit_14034f8a0` | `0x14034f8a0` | FUN_14034f8a0 (atexit target) |
| `0x1400044e0` | `CInit_Atexit_14034f9a0` | `0x14034f9a0` | FUN_14034f9a0 (atexit target) |
| `0x1400044f0` | `CInit_Atexit_14034f9b0` | `0x14034f9b0` | FUN_14034f9b0 (atexit target) |
| `0x1400045c0` | `CInit_Atexit_14034fbc0` | `0x14034fbc0` | FUN_14034fbc0 (atexit target) |
| `0x1400045d0` | `CInit_Atexit_14034fbd0` | `0x14034fbd0` | FUN_14034fbd0 (atexit target) |
| `0x140004910` | `CInit_Atexit_14034fe50` | `0x14034fe50` | FUN_14034fe50 (atexit target) |
| `0x1400046c0` | `CInit_Atexit_14034fd30` | `0x14034fd30` | FUN_14034fd30 (atexit target) |
| `0x1400046d0` | `CInit_Atexit_14034fd40` | `0x14034fd40` | FUN_14034fd40 (atexit target) |
| `0x1400046b0` | `CInit_Atexit_14034fcc0` | `0x14034fcc0` | FUN_14034fcc0 (atexit target) |
| `0x140004a40` | `CInit_Atexit_1403504f0` | `0x1403504f0` | CInit_b2ContactFilter (atexit target) |
| `0x140004a50` | `CInit_Atexit_140350500` | `0x140350500` | CInit_b2ContactListener (atexit target) |

## Skipped (1)

| entry | target | why |
|---|---|---|
| `0x1403519f0` | `0x140334c38` | `__scrt_set_unhandled_exception_filter` + `_set_new_mode` worker (batch 5 agent 1's finding). It is not a single-global initialiser: `MOV ECX,0x1; CALL 0x14033523c; CALL 0x140055f20; ... JMP 0x1403366c6`. No `LEA RCX,[global]`, so `CInit_<Global>` cannot be derived; left unnamed as documented by b5. |

## Observations / hand-offs

1. `0x1403504f0` and `0x140350500` are already named `CInit_b2ContactFilter`
   and `CInit_b2ContactListener` by an earlier pass, but their bodies are
   `LEA RAX,[0x140369200/0x140369218]; MOV [0x1403c2e10/0x1403c2e18],RAX; RET`
   — i.e. they install a vtable pointer into a global. They are the `atexit`
   callbacks of table entries `0x140004a40`/`0x140004a50`, so the `CInit_` prefix
   is misleading (they are not constructors and run at exit). Renaming them is
   outside this agent's assignment; flagged for the parent.
2. The table is best described as the CRT `__xc_a`/`__xc_z` block and mixes
   constructor entries with `atexit` registrations, so `__xc_a..__xc_z` should
   not be assumed to be 249 constructors.
3. `0x140004930` is the only entry that tail-jumps outside the CRT half:
   `LEA RCX,[DAT_14801fd00]; JMP VideoSettings_RegisterProperties
   (0x1402e6f90)`.

## Method notes

* Parsed the table with `run_script_inline` (`getLong` over 249 qwords), then
  read each target's first instructions with `getInstructionAt(...).getNext()`.
* Recovered the `LEA` operand and `JMP` target from the instruction text, and
  resolved symbols live so agent 5's `DtorGlobal_*` renames are reflected.
* Created with `createFunction(address, name)`, plated with
  `setPlateComment(address, ...)`.
