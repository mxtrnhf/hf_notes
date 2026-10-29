# Ghidra sweep 2026-10-30 — Phase 2 agent E (structures-unlocked subsystem bodies)

Program: `Highfleet.exe.unpacked.exe v1.163` (project `HighfleetServer`). **1.163 only.**
Scope: the `verdict=needs structures` rows of
[data/unnamed-classification-2026-10-30.tsv](unnamed-classification-2026-10-30.tsv)
whose family starts with `subsystem_` — 323 rows in total.
Field maps used: [structures.md](../structures.md) (Body, Stats, Fleet/Escadra,
Missile, Creature, Location, Gui, HGE) plus the per-field evidence in
`findings/*.md` where structures.md is silent (noted per row).
No `save_program`, no transaction, no `create_function` was issued.

Method: every row was decompiled in bounded batches (12 addresses per
`run_script_inline`, `DecompInterface` with a 60 s per-function timeout, no
loop over the program). 319 of 323 rows were decompiled; the 4
`subsystem_crt_eh_*` rows were not (see §4). A body was renamed only when
**every** field it touches is documented, or when a newly proved field could be
stated with a writer/reader pair. Everything else is in the skipped table with
the first blocking field.

Result: **17 renamed / 302 skipped**, 0 bodies created.

## 1. Renamed

| address | new name | family | evidence (field → meaning) |
|---|---|---|---|
| `0x140005390` | `Body_AssignAmmoSlotByCaliber` | `subsystem_core_physics_GetStats` | walks a Link vector (stride 0x18, entry +8 = part); for each part clears `+0x850` then scans `AMMO_LIST_BEGIN..END` (stride 0x188) for `ammo[+0x154] == Stats(part+0x188)[+0x144]` and writes `+0x850/+0x854/+0x858/+0x85c`. All of those are documented (weapon ammo fields in structures.md §Body; ammo `index` at `+0x154` in findings/ammo-1151-vs-1163.md) |
| `0x14006e090` | `Creature_EnablePartsWithPower` | `subsystem_core_physics_GetStats` | for each part in the `+0x1330/+0x1338` part list with `Stats+0xdc` (power) != 0 and `Stats+0xe0` (power_need) == 0, writes `1.0f` to `part+0x80c`. `+0x80c` = part "enabled/armed" (findings/ship-serializer.md, guns-aim-reload-fire.md) |
| `0x1400796d0` | `Creature_EnablePartsWithSensors` | `subsystem_core_physics_GetStats` | same loop/write, parts selected by `Stats+0x10c` radar / `+0x118` elint / `+0x11c` irst |
| `0x140081670` | `Creature_EnablePartsWithWeapons` | `subsystem_render_shaders_GetStats` | same loop/write, parts selected by `Stats+0x144` caliber != 0, `part+0x3c4` logic id == 1, or `Stats+0xe8` ammobox != 0 |
| `0x14007a160` | `Creature_SetPartsOwnerRef` | `subsystem_core_physics_SetLink` | for every part in `+0x1330/+0x1338`: `SetLink(part+0xb0, creature)`; `+0xb0` = owner smart-ref, `+0x1330` = part list (both documented) |
| `0x1401b1ed0` | `Body_AccumulateOidCount` | `subsystem_seria_level_rep_140012bb0_New` | deduplicating counter: compares `m_oid` of two bodies (`+0x190` data / `+0x1a0` length / `+0x1a8` capacity, all documented) and increments / appends a `{body*, int count}` (stride 0x10) element |
| `0x14004e4c0` | `Body_RepairHealthStep` | `subsystem_core_physics_GetStats` | moves `+0x2c8` health toward `+0x2cc` health_max at a rate derived from `Stats+0x94` repair_cost, consuming a work budget; health pair and repair_cost are documented |
| `0x1400f4070` | `Escadra_PredictPosition` | `subsystem_strategic_map_WriteToClientLog_source_path` | `(x,y) = pos + heading-rotated (0,1) * speed * k * dt` using Escadra `+0x150/+0x154` position, `+0x158` speed, `+0x15c` heading (all documented; source file is `Escadra.cpp` per the CHECK-ERROR string) |
| `0x1400f3c10` | `Missile_PredictPosition` | `subsystem_strategic_map_WriteToClientLog_source_path` | same shape for the map Missile: `+0x15c` angle, `+0x158` speed, `+0x150/+0x154` position (documented Missile row) |
| `0x1401b6d10` | `ComputeInterceptTime` | `subsystem_seria_level_ComputeInterceptPoint` | `ComputeInterceptPoint` → `|P-A| / speed`; `ComputeInterceptPoint` is an existing named function |
| `0x140215110` | `Profile_CreateTutorialTrigger` | `subsystem_seria_level_CreateTriggerVal` | `CreateTriggerVal(&Profile+0x3f0, "TUTORIAL")` — the literal names the new field |
| `0x140202e30` | `Gui_CreateStdChild` | `subsystem_seria_level_GUI_2_other` | `New(0xe70)` (Gui size), `GUI::GUI_2`, added through vtable `+0x50` (add child), initialised via slot `+0x2c0` with the `gui_std` / `gui_std_focus` / `gui_std_click` / `flash_large_shadow` template, then `resetGuiStrings` |
| `0x1402abf90` | `RadioBeacon_ConstructorDefault` | `subsystem_scene_hud_ISerializable` | ISerializable base, stores `RadioBeacon` vtable, zeroes the next two qwords, calls `RadioBeacon_Constructor` (same shape as `Stats_ConstructorDefault` / `Sprite_ConstructorDefault`) |
| `0x1402ddad0` | `Sprite_CopyConstructor` | `subsystem_scene_hud_CreateHGE` | stores `SpriteVFTABLE`, zero-inits, `createSprite_`, `Sprite_CopyFrom(source)` |
| `0x1400a0f50` | `GameEnd_RegisterFreeItem` | `subsystem_render_shaders_New` | `New(0x78)` + `Values_Item_ConstructorWithCallback`, appended to the global `GameEndFreeLoopStart/End` vector |
| `0x140173380` | `Math_AngleBetween2D` | `subsystem_engine_res_acosf` | acos of the normalised dot product of two 2D vectors (falls back to `atan2f` for a zero vector); no struct field |
| `0x14024b440` | `Gfx_DrawArcQuads` | `subsystem_seria_level_Matrix3x3_Identity` | emits one quad per arc step through HGE slot `+0x2e0` (`Gfx_RenderQuad`, documented) |

Name style follows the existing database (`Body_*`, `Creature_*`, `Escadra_*`,
`Profile_*`, `Gui_*`, `Stats_*`); the MCP renamed with the usual
"not PascalCase" style warnings, which every existing name also produces.

## 2. Skipped

302 rows. The single blocking field is given per row; `[+0x..]` lists the
distinct constant offsets the body touches so the next pass can look at the
right field first. Offsets are the raw immediates from the decompiled C
(Ghidra's struct-pointer arithmetic is already folded in, so they are byte
offsets into the pointee).

Where the reason is a family phrase (container / string / sort / box2d / …) it
was derived from the callee set, not from a field map: for those rows the
`[+0x..]` offset list is the authoritative part. The Gui, Sprite, Property and
Creature rows were read individually; their reason names the exact field that
stopped the rename.

| address | family | current name | size | blocking field / reason |
|---|---|---|---:|---|
| `0x1400052b0` | `subsystem_core_physics_freeLinkMemory` | `rep_140004d90_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 177 | Link-list teardown helper (`freeLinkMemory`) — container family [(no +const)] |
| `0x140007de0` | `subsystem_core_physics_Aircraft_ApplyFlightForces_source_path` | `rep_1400078b0_WriteToClientLogAircraftLogic` | 1818 | undocumented field (see offsets) [+0x40, +0x44, +0x48, +0x50, +0x68, +0x6c, +0x78, +0x7c] |
| `0x1400085d0` | `subsystem_core_physics_GetStats` | `rep_1400080a0_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 3192 | undocumented Creature field (see offsets) [+0xc, +0x10, +0x14, +0x18, +0x1c, +0x20, +0x26, +0x3e] |
| `0x14000da20` | `subsystem_core_physics_Body_SetLinearVelocity` | `rep_14000dc50_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 891 | `aircraftLogic` (+0xa20, documented) reads +0x64; the zigzag-scatter trajectory itself has no documented struct |
| `0x14000e6a0` | `subsystem_core_physics_Math_NormalizeAngleDifference` | `rep_14000e8a0_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 880 | undocumented field (see offsets) [+0x50, +0x70, +0x74, +0xbc, +0xc0, +0x130, +0x194, +0x198] |
| `0x14000eb20` | `subsystem_core_physics_vectorCalculateAngles` | `rep_14000ed20_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | 137 | undocumented field (see offsets) [+0xe] |
| `0x14000f2a0` | `subsystem_core_physics_Math_NormalizeAngleDifference` | `rep_14000ef80_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 782 | undocumented field (see offsets) [+0x40, +0x44, +0x50, +0x70, +0x74, +0x178] |
| `0x14000faf0` | `subsystem_core_physics_Math_NormalizeAngleDifference` | `rep_14000f7c0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | 203 | undocumented field (see offsets) [+0xc, +0x20, +0xc0, +0xc4] |
| `0x140010520` | `subsystem_core_physics_Creature_CollectByArrayPos` | `rep_140010340_API-MS-WIN-CRT-MATH-L1-1-0.DLL::atan2f` | 1177 | undocumented Creature field (see offsets) [+0x10, +0x18, +0x19, +0x20, +0x28, +0x48, +0x50, +0x130] |
| `0x1400115e0` | `subsystem_core_physics_rep_1400144b0_New` | `rep_140011400_VCRUNTIME140.DLL::memcpy` | 292 | undocumented field (see offsets) [(no +const)] |
| `0x140013390` | `subsystem_core_physics_GetStats` | `rep_140013310_GetStats` | 710 | introsort sift-down on element stride 0x28 (comparator uses Body Stats +0xb0 armor bit) — sort family |
| `0x140013660` | `subsystem_core_physics_GetStats` | `rep_1400135e0_GetStats` | 455 | sort comparator/swap for element stride 0x28 — sort family |
| `0x140013860` | `subsystem_core_physics_GetStats` | `rep_1400137e0_GetStats` | 1622 | sort driver for element stride 0x28 — sort family |
| `0x1400141a0` | `subsystem_core_physics_GetStats` | `rep_140014120_GetStats` | 498 | sort partition for element stride 0x28 — sort family |
| `0x1400147b0` | `subsystem_core_physics_GetStats` | `rep_140014730_GetStats` | 872 | introsort for element stride 0x28 — sort family |
| `0x140014b20` | `subsystem_core_physics_Sort16_PartitionFloat` | `rep_140014aa0_VCRUNTIME140.DLL::memmove` | 889 | sort/partition/sift helper on an element stride — element layout only, sort family [+0xc, +0x10] |
| `0x140015080` | `subsystem_core_physics_CopyString` | `rep_140015130_CopyString` | 226 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x10, +0x38] |
| `0x140015570` | `subsystem_core_physics_New` | `rep_1400156a0_New` | 279 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x27, +0x28] |
| `0x140016ef0` | `subsystem_core_physics_CopyEscadraName` | `rep_140016ff0_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 226 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x20, +0x24, +0x28, +0x2c, +0x30] |
| `0x140018860` | `subsystem_core_physics_CopyString` | `rep_140018950_CopyString` | 86 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [(no +const)] |
| `0x1400190d0` | `subsystem_core_physics_Editor_UndoZoom` | `rep_1400191c0_MakeGlobal?` | 371 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x52, +0x13d, +0x1b0, +0x294] |
| `0x140019d60` | `subsystem_core_physics_Body_Constructor_other` | `rep_140019ee0_New` | 1605 | Sprite layout missing (+0x78 owner, +0x90 name string, +0xdc..+0x124) [+0x38, +0x50, +0x58, +0x79, +0x7a, +0x88, +0xe8, +0x108] |
| `0x14001baf0` | `subsystem_core_physics_WriteToClientLog_source_path` | `rep_14001b5f0_FastFail?` | 424 | box2d proxy/joint internals [+0x28, +0x2c, +0x178, +0x1a8] |
| `0x140023580` | `subsystem_core_physics_New_other` | `rep_140022650_MakeGlobal?` | 956 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x48, +0x50, +0x88, +0x11b, +0x147, +0x152, +0x1d9, +0x358] |
| `0x140027b20` | `subsystem_core_physics_atof` | `rep_140026500_API-MS-WIN-CRT-CONVERT-L1-1-0.DLL::atof` | 85 | undocumented field (see offsets) [+0x10, +0x18] |
| `0x140027b80` | `subsystem_core_physics_atoi` | `rep_140026560_API-MS-WIN-CRT-CONVERT-L1-1-0.DLL::atoi` | 71 | undocumented field (see offsets) [+0x10, +0x18] |
| `0x140027bd0` | `subsystem_core_physics_SetLink` | `rep_1400265b0_MakeGlobal?` | 171 | Body +0x100 (child/dependant list) and +0x7ac byte |
| `0x140027f90` | `subsystem_core_physics_rep_1402b1a80_MakeGlobal` | `FUN_140027f90` | 120 | undocumented field (see offsets) [+0x58, +0x350, +0x358] |
| `0x14002de30` | `subsystem_core_physics_Creature_WorldToScreen` | `rep_14002e9e0_GetStats` | 933 | undocumented Creature field (see offsets) [+0xb0] |
| `0x14002e7d0` | `subsystem_core_physics_Body_SetLinearVelocity` | `rep_14002f1b0_Get_Profile?` | 347 | Body +0x1c0 flag word (`|= 0x205`) and +0x7ac byte |
| `0x140048cd0` | `subsystem_core_physics_CopyEscadraName_other` | `rep_140046980_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 368 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x10, +0x18] |
| `0x140048e50` | `subsystem_core_physics_Vec2_TransformByMat2` | `rep_140046b00_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | 318 | undocumented field (see offsets) [+0x48, +0x218, +0x21c, +0x350, +0x358, +0x8fc] |
| `0x140049c30` | `subsystem_core_physics_ReassignLinkNode` | `rep_1400477f0_MakeGlobal?` | 152 | undocumented field (see offsets) [+0x98, +0xb0, +0xb8, +0xf4, +0x180, +0x818, +0x820] |
| `0x140049d00` | `subsystem_core_physics_GetStats` | `rep_1400478c0_GetStats` | 160 | no field blocks it: Stats +0xb0, Body +0x188 and `m_oid` are documented, but the category whitelist {0x400,0x800,0x4000,0x200000,4,0x8000000,1,0x10} has no proven meaning |
| `0x14004a2f0` | `subsystem_core_physics_Physics_ShapeDistance` | `rep_140047ef0_FastFail?` | 616 | box2d proxy/joint internals [+0xc, +0x10, +0x14, +0x18, +0x28, +0x88, +0x98, +0x168] |
| `0x14004ae40` | `subsystem_core_physics_Link_CopyConstructor_other` | `rep_140048ac0_New` | 146 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [(no +const)] |
| `0x14004e220` | `subsystem_core_physics_GetStats` | `rep_14004be30_MSVCP140.DLL::_Xtime_get_ticks` | 670 | undocumented field (see offsets) [+0x59, +0xb0, +0x11e, +0x12e, +0x248, +0x2cc, +0x2f4, +0x91d] |
| `0x14004e870` | `subsystem_core_physics_GetStats_other` | `rep_14004c3e0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 551 | undocumented field (see offsets) [+0x88, +0xb0, +0x188, +0x4f0, +0x4f8] |
| `0x140051420` | `subsystem_core_physics_WriteString` | `rep_14004ef90_MSVCP140.DLL::std::basic_ostream<char,struct_std::char_traits<char>_>::<<` | 170 | stream dump of a `vector<int>` (`%d` + separator + `\n`) — debug/CRT helper, no struct field |
| `0x140051f90` | `subsystem_core_physics_CopyString` | `rep_14004fa70_CopyString` | 221 | Sprite layout missing (+0x78 owner, +0x90 name string, +0xdc..+0x124) [+0x90, +0xdc, +0x114, +0x118, +0x11c, +0x120, +0x124, +0x8b8] |
| `0x140053870` | `subsystem_core_physics_GetStats` | `rep_140051060_API-MS-WIN-CRT-MATH-L1-1-0.DLL::atan2f` | 1183 | box2d proxy/joint internals [+0xc, +0x10, +0x27, +0x3b, +0xe8, +0xec, +0x103, +0x104] |
| `0x140054040` | `subsystem_core_physics_Vec2_TransformByMat2_source_path` | `rep_140051890_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 828 | undocumented field (see offsets) [+0x48, +0x58, +0xb8, +0x218, +0x21c, +0x350, +0x358, +0x8fc] |
| `0x140054380` | `subsystem_core_physics_Get_Profile` | `rep_140051bd0_Get_Profile?` | 915 | Gui member map missing (see +0xa34/+0xa39/+0x91c/+0xee8/+0xd70 group in the field list) [+0xe8, +0x122, +0x20c, +0x885, +0x90c, +0x914, +0x91c, +0x91d] |
| `0x140058090` | `subsystem_core_physics_CopyEscadraName` | `rep_140056080_CopyEscadraName` | 474 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x18, +0x20, +0x38] |
| `0x140058270` | `subsystem_core_physics_New` | `rep_140056260_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 732 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x27, +0x30] |
| `0x140059060` | `subsystem_core_physics_isCollinear` | `rep_140057050_isCollinear` | 190 | sort/partition/sift helper on an element stride — element layout only, sort family [+0xc, +0x14, +0x1c] |
| `0x140059da0` | `subsystem_core_physics_isCollinear` | `rep_140057d90_isCollinear` | 771 | sort/partition/sift helper on an element stride — element layout only, sort family [+0xc] |
| `0x14005a770` | `subsystem_core_physics_isCollinear` | `rep_140058760_isCollinear` | 324 | sort/partition/sift helper on an element stride — element layout only, sort family [+0x10] |
| `0x14005ba40` | `subsystem_core_physics_isCollinear` | `rep_1400598c0_isCollinear` | 940 | sort/partition/sift helper on an element stride — element layout only, sort family [+0xc, +0x14, +0x1c] |
| `0x14005bdf0` | `subsystem_core_physics_SortElem32ByInt48` | `rep_140059c70_VCRUNTIME140.DLL::memmove` | 703 | sort/partition/sift helper on an element stride — element layout only, sort family [+0x20] |
| `0x14005c460` | `subsystem_core_physics_CopyEscadraName` | `rep_14005a2e0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 287 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x20, +0x24, +0x28, +0x2c, +0x30] |
| `0x140060500` | `subsystem_core_physics_FillRange8_other` | `rep_14005e090_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 851 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x18, +0x20, +0x27, +0x28, +0x30, +0x38] |
| `0x140060a60` | `subsystem_core_physics_CalculateStats` | `rep_14005e760_Creature::CalculateStats` | 281 | Body +0x92c (float, zeroed) and Creature +0x1540/+0x1548 (stride-0x30 list, entries memcmp-ed against a Body) |
| `0x140060b80` | `subsystem_core_physics_GetStats` | `rep_14005e820_GetStats` | 503 | undocumented field (see offsets) [+0x18, +0xd4, +0x188, +0x804, +0xc80, +0x1480, +0x1488, +0x17ec] |
| `0x1400619b0` | `subsystem_core_physics_FillIntRange` | `rep_14005f650_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 496 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [(no +const)] |
| `0x140061bb0` | `subsystem_core_physics_Body_GetSlotWorldPos` | `rep_14005f850_VCRUNTIME140.DLL::memcmp` | 493 | undocumented field (see offsets) [+0x18, +0x20, +0x58, +0x90, +0xa0, +0xa8, +0xb0, +0x128] |
| `0x140062e10` | `subsystem_core_physics_Body_ResetPartToDefinition` | `rep_1400609f0_MakeGlobal?` | 376 | undocumented Creature field (see offsets) [+0x3e, +0x48, +0x79, +0x9b, +0x24c, +0x3c4, +0x3cc, +0x7ac] |
| `0x140065fa0` | `subsystem_core_physics_CopyEscadraName_model_name` | `rep_140063000_CopyEscadraName` | 1307 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x50, +0x88, +0x11b, +0x147, +0x177, +0x2c0, +0x2d8, +0xa14] |
| `0x1400664c0` | `subsystem_core_physics_CopyEscadraName_model_name` | `rep_140063520_ShipCards?` | 2130 | Sprite layout missing (+0x78 owner, +0x90 name string, +0xdc..+0x124) [+0x28, +0x50, +0x5c, +0x88, +0x11b, +0x128, +0x147, +0x177] |
| `0x14006c100` | `subsystem_core_physics_traverseLinkedListCreature` | `rep_140068980_API-MS-WIN-CRT-MATH-L1-1-0.DLL::atan2f` | 818 | undocumented Creature field (see offsets) [+0xc, +0x10, +0x20, +0xe8, +0x128, +0x130, +0x134, +0xca0] |
| `0x14006d930` | `subsystem_core_physics_GetStats` | `rep_14006a210_GetStats` | 191 | Creature +0xc80 (double quantity) and the +0x1378 launch list; +0x1638/+0x1640, Body +0x7f8, Stats +0xc8 documented |
| `0x14006e130` | `subsystem_core_physics_freeLinkMemory` | `rep_14006aa10_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 171 | Link-list teardown helper (`freeLinkMemory`) — container family [+0x48, +0xa58, +0xa60] |
| `0x14006e1e0` | `subsystem_core_physics_FID_conflict_sprintf_s_other` | `rep_14006aac0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 1680 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x13, +0x27, +0x28, +0x158, +0x1403561eb] |
| `0x14006ee10` | `subsystem_core_physics_freeLinkMemory` | `rep_14006b5c0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 158 | Link-list teardown helper (`freeLinkMemory`) — container family [+0xa48, +0xa50] |
| `0x14006ef10` | `subsystem_core_physics_CalculateStats_source_path` | `rep_14006b6c0_CreateSpriteCreature` | 246 | Sprite +0x78 (owner) and +0x160 (part list) |
| `0x14006f010` | `subsystem_core_physics_CreateCreature_source_path` | `rep_14006b7c0_CreateSprite` | 319 | Sprite layout missing (+0x78 owner, +0x90 name string, +0xdc..+0x124) [+0x48, +0x68, +0x88, +0x160] |
| `0x140070cc0` | `subsystem_core_physics_Body_RebuildSubtreeList` | `rep_14006d470_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 607 | duplicate of the existing `Creature_ComputePartBounds` (bbox over the +0x1330 part list) |
| `0x140073360` | `subsystem_core_physics_compareEscadraString` | `rep_14006f8d0_compData` | 134 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x19, +0xa90] |
| `0x1400741e0` | `subsystem_core_physics_CopyEscadraName` | `rep_140070650_CopyEscadraName` | 54 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x10, +0x20] |
| `0x1400780c0` | `subsystem_core_physics_freeLinkMemory` | `rep_1400740f0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 135 | Link-list teardown helper (`freeLinkMemory`) — container family [+0x888, +0x88c, +0x1558, +0x1560] |
| `0x14007a6a0` | `subsystem_core_physics_Escadra_TransferShopItems` | `rep_1400760e0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 247 | Link-list teardown helper (`freeLinkMemory`) — container family [+0x16, +0x18, +0x68, +0x111, +0x88c, +0xa70, +0x1558, +0x1560] |
| `0x14007a7a0` | `subsystem_core_physics_GetValue` | `rep_1400761d0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 298 | Link-list teardown helper (`freeLinkMemory`) — container family [+0xb8, +0x340, +0x888, +0xa70, +0xb60, +0xb64, +0xb68, +0x1558] |
| `0x14007bfc0` | `subsystem_core_physics_GetStats` | `rep_140077720_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 1068 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x18, +0x27, +0x28, +0x8c, +0x188, +0x1a0, +0x1a8, +0x1330] |
| `0x140082430` | `subsystem_render_shaders_List_InitHeaderNode68` | `rep_14007dbe0_New` | 325 | undocumented field (see offsets) [+0x14, +0x18, +0x1c, +0x20, +0x24, +0x28, +0x2c, +0x30] |
| `0x140082db0` | `subsystem_render_shaders_unshift` | `rep_14007e560_API-MS-WIN-CRT-STDIO-L1-1-0.DLL::fwrite` | 232 | undocumented field (see offsets) [+0x18, +0x71, +0x74] |
| `0x140082f30` | `subsystem_render_shaders_WriteToClientLog_source_path` | `rep_14007e6e0_FastFail?` | 439 | undocumented field (see offsets) [+0x20, +0x28, +0x30, +0x38, +0x3c, +0x40, +0x44, +0x68] |
| `0x1400830f0` | `subsystem_render_shaders_Render_SelectBlendState_source_path` | `rep_14007e8a0_FastFail?` | 404 | undocumented field (see offsets) [+0x20, +0x28, +0x38, +0x3c, +0x40, +0x44, +0x108, +0x160] |
| `0x140083e80` | `subsystem_render_shaders_Std_Locale_GetCodecvtFacet` | `rep_14007f630_MSVCP140.DLL::std::codecvt_base::always_noconv` | 80 | undocumented field (see offsets) [+0x68] |
| `0x14009b8b0` | `subsystem_render_shaders_CopyString` | `rep_140097060_CopyString` | 149 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [(no +const)] |
| `0x1400a03f0` | `subsystem_render_shaders_Vector_ThrowSubscriptOutOfRange` | `rep_14009bbc0_VCRUNTIME140.DLL::memcmp` | 150 | undocumented field (see offsets) [+0x10, +0x18, +0x20, +0x28] |
| `0x1400a0860` | `subsystem_render_shaders_New` | `rep_14009c030_VCRUNTIME140.DLL::__RTDynamicCast` | 258 | undocumented field (see offsets) [+0x2e0] |
| `0x1400a1170` | `subsystem_render_shaders_CopyEscadraName_other` | `rep_14009d480_MSVCP140.DLL::std::_Xlength_error` | 631 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0xc, +0xe] |
| `0x1400a13f0` | `subsystem_render_shaders_CopyEscadraName` | `rep_14009d700_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 467 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x10, +0x20] |
| `0x1400a1740` | `subsystem_render_shaders_freeLinkMemory` | `rep_14009da50_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 743 | undocumented field (see offsets) [+0x1b, +0x22, +0x2a, +0x2e, +0x32, +0x36] |
| `0x1400a2ae0` | `subsystem_render_shaders_CopyEscadraName` | `rep_14009edd0_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 420 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x20] |
| `0x1400a2ff0` | `subsystem_render_shaders_Get_Profile_other` | `rep_14009f2e0_MSVCP140.DLL::std::_Xlength_error` | 400 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x48, +0x50, +0x8c, +0x94, +0x9c, +0xa4, +0xac, +0xb4] |
| `0x1400a31f0` | `subsystem_render_shaders_CopyEscadraName_other` | `rep_14009f4a0_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 1421 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x50, +0x79, +0x7f, +0x83, +0x88, +0x92, +0x11b, +0x11f] |
| `0x1400a39e0` | `subsystem_render_shaders_CopyEscadraName` | `rep_14009fc90_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 868 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x18, +0x27, +0x28] |
| `0x1400a60c0` | `subsystem_render_shaders_CopyString` | `rep_1400a2320_CopyString` | 303 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [(no +const)] |
| `0x1400b8d80` | `subsystem_render_shaders_CopyEscadraName` | `rep_1400b4e60_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 684 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x30, +0x108] |
| `0x1400b9f30` | `subsystem_render_shaders_CopyString` | `rep_1400b6000_MakeGlobal?` | 444 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x30, +0x38, +0x48, +0x50, +0x68, +0x70, +0x78, +0x80] |
| `0x1400ba3c0` | `subsystem_render_shaders_atan` | `rep_1400b6470_API-MS-WIN-CRT-MATH-L1-1-0.DLL::atan` | 117 | undocumented field (see offsets) [+0x110] |
| `0x1400bb430` | `subsystem_render_shaders_CopyEscadraName` | `rep_1400b7530_petrCharacterEvents?` | 964 | undocumented Creature field (see offsets) [+0x20, +0x178, +0x248, +0x2e8] |
| `0x1400bc740` | `subsystem_render_shaders_Engine_ApplyThrustCommand_other` | `rep_1400b8d70_VCRUNTIME140.DLL::memmove` | 4999 | Gui member map missing (see +0xa34/+0xa39/+0x91c/+0xee8/+0xd70 group in the field list) [+0xc, +0x25, +0x27, +0x28, +0x32, +0x42, +0x48, +0x4c] |
| `0x1400c09e0` | `subsystem_render_shaders_Get_Profile` | `rep_1400bbe10_Get_Profile?` | 350 | Gui member map missing (see +0xa34/+0xa39/+0x91c/+0xee8/+0xd70 group in the field list) [+0x1848, +0x184c] |
| `0x1400c0e50` | `subsystem_render_shaders_Body_IsMountedOrPaired` | `rep_1400bc260_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 1097 | undocumented field (see offsets) [+0x28, +0x48, +0x58, +0x70, +0x78, +0x84, +0x85, +0xb8] |
| `0x1400d25e0` | `subsystem_render_shaders_CopyEscadraName` | `rep_1400cd6c0_compData` | 800 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x20, +0x27, +0x28, +0x50, +0x98] |
| `0x1400d37c0` | `subsystem_render_shaders_New` | `rep_1400ce870_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 1550 | undocumented field (see offsets) [+0x18, +0x90, +0x98, +0xf8, +0x128] |
| `0x1400d4380` | `subsystem_render_shaders_Color_SetPulsingAlpha_other` | `rep_1400cf430_VCRUNTIME140.DLL::memmove` | 11210 | Property / linked map object layout missing (property node list at +0x100, node payload +0x2b4) [+0xc, +0x10, +0x14, +0x18, +0x20, +0x28, +0x58, +0x88] |
| `0x1400da8b0` | `subsystem_render_shaders_AssignRandomId_source_path` | `rep_1400d51d0_WriteToClientLogEDITOR` | 576 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0xe, +0x48, +0x80, +0x348, +0x520, +0xa90] |
| `0x1400db8e0` | `subsystem_render_shaders_CopyString_other` | `rep_1400d6040_FindGuiElement` | 861 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x3e, +0x50, +0x58, +0x5c, +0x68, +0x78, +0x88, +0xe8] |
| `0x1400dc300` | `subsystem_render_shaders_CopyString_other` | `rep_1400d6ae0_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 2738 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x18, +0x28, +0x48, +0x68, +0x1c0, +0xe08, +0xe40, +0xe50] |
| `0x1400ddcd0` | `subsystem_render_shaders_CalculateStats_other` | `rep_1400d8690_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 4093 | Property / linked map object layout missing (property node list at +0x100, node payload +0x2b4) [+0x18, +0x19, +0x28, +0x30, +0x48, +0x50, +0xd8, +0xe0] |
| `0x1400dece0` | `subsystem_render_shaders_Link_CopyConstructor` | `rep_1400d9690_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 463 | undocumented field (see offsets) [(no +const)] |
| `0x1400df060` | `subsystem_render_shaders_AllocArrayStride24` | `rep_1400d9a10_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 513 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x18] |
| `0x1400df810` | `subsystem_render_shaders_FUN_1401a4210` | `rep_1400da1c0_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 604 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x10, +0x20, +0x27] |
| `0x1400e11f0` | `subsystem_strategic_map_Sort3ByComparator` | `rep_1400dbba0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | 1562 | sort/partition/sift helper on an element stride — element layout only, sort family [+0x50, +0x78, +0xb0, +0xb4, +0x4c8] |
| `0x1400e2180` | `subsystem_strategic_map_AllocArrayStride24` | `rep_1400dcb30_std::vector<struct_CHN*___ptr64,class_std::allocator<struct_CHN*___ptr64>_>::vector<struct_CHN*___ptr64,class_std::allocator<struct_CHN*___ptr64>_>` | 506 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x10, +0x18] |
| `0x1400e2380` | `subsystem_strategic_map_AllocArrayStride24` | `rep_1400dcd30_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 451 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x10] |
| `0x1400e2850` | `subsystem_strategic_map_SortIndicesByValuePartition` | `rep_1400dd200_VCRUNTIME140.DLL::memmove` | 808 | sort/partition/sift helper on an element stride — element layout only, sort family [(no +const)] |
| `0x1400e2d00` | `subsystem_strategic_map_bool_cdecl_struct_tagFRAMEDATA_con` | `rep_1400dd6b0_VCRUNTIME140.DLL::memmove` | 901 | undocumented field (see offsets) [+0x10, +0x18, +0x20] |
| `0x1400e3390` | `subsystem_strategic_map_AllocArrayStride24_other` | `rep_1400ddd40_std::vector<struct_CHN*___ptr64,class_std::allocator<struct_CHN*___ptr64>_>::vector<struct_CHN*___ptr64,class_std::allocator<struct_CHN*___ptr64>_>` | 293 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x18] |
| `0x1400e4c00` | `subsystem_strategic_map_freeLinkMemory` | `rep_1400df5a0_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 182 | Link-list teardown helper (`freeLinkMemory`) — container family [(no +const)] |
| `0x1400e5fd0` | `subsystem_strategic_map_CopyString` | `rep_1400e0950_CopyString` | 290 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x30, +0x49, +0x4a, +0x4b, +0x4d, +0x50, +0x53, +0x55] |
| `0x1400e62d0` | `subsystem_strategic_map_SetLink` | `rep_1400e0e30_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | 1004 | undocumented field (see offsets) [+0x150, +0x154, +0x254, +0x268] |
| `0x1400e84c0` | `subsystem_strategic_map_freeLinkMemory` | `rep_1400e2e40_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 216 | Link-list teardown helper (`freeLinkMemory`) — container family [(no +const)] |
| `0x1400e8960` | `subsystem_strategic_map_Vector_Resize8_other` | `rep_1400e32e0_MSVCP140.DLL::std::_Xlength_error` | 496 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x11, +0x12, +0x13, +0x14, +0x15, +0x16, +0x17, +0x18] |
| `0x1400e91f0` | `subsystem_strategic_map_Link_CopyConstructor_other` | `rep_1400e3b80_New` | 285 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x18, +0x78, +0x2a0, +0x2a8, +0x338, +0x340] |
| `0x1400ed6e0` | `subsystem_strategic_map_SetLink` | `rep_1400e8040_MakeGlobal?` | 372 | undocumented field (see offsets) [+0x50, +0x2d8, +0x2e0, +0x318, +0x3a8, +0x3ac, +0x3b0, +0x3b4] |
| `0x1400ee280` | `subsystem_strategic_map_Get_Profile` | `rep_1400e8be0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | 2024 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x60, +0x150, +0x154, +0x248, +0x2d0, +0x2d8, +0x2e8, +0x318] |
| `0x1400eece0` | `subsystem_strategic_map_CopyString` | `rep_1400e9600_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | 1017 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x16, +0x2a, +0x31, +0x32, +0x81, +0x82, +0x83, +0xb4] |
| `0x1400ef0e0` | `subsystem_strategic_map_LinkedList_ClearFree` | `rep_1400e9a00_MakeGlobal?` | 580 | undocumented field (see offsets) [(no +const)] |
| `0x1400f0cc0` | `subsystem_strategic_map_Get_Profile` | `rep_1400eb5e0_New` | 494 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x48, +0x100, +0x108, +0x150, +0x528] |
| `0x1400f0fb0` | `subsystem_strategic_map_CalculateStats_other` | `rep_1400eb8d0_New` | 511 | Property / linked map object layout missing (property node list at +0x100, node payload +0x2b4) [+0x100] |
| `0x1400f2de0` | `subsystem_strategic_map_Get_Profile` | `rep_1400ed6c0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | 1159 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x18, +0x2a, +0x2d, +0x2e, +0x150, +0x154, +0x168, +0x16c] |
| `0x1400f32c0` | `subsystem_strategic_map_Get_Profile` | `rep_1400edba0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | 1030 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x2a, +0x2d, +0x2e, +0x150, +0x154, +0x168, +0x16c, +0x174] |
| `0x1400f4c40` | `subsystem_strategic_map_GetPropertyLinkedObject_other` | `rep_1400ef4e0_New` | 899 | Property / linked map object layout missing (property node list at +0x100, node payload +0x2b4) [+0x100, +0x108, +0x478] |
| `0x1400f75d0` | `subsystem_strategic_map_Fleet_CountActiveShips` | `rep_1400f1e00_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | 509 | undocumented Escadra field (see offsets) [+0xb0, +0xb4, +0x108, +0x110, +0x150, +0x154, +0x2d8, +0x2e0] |
| `0x1400f9460` | `subsystem_strategic_map_CalculateStats_source_path` | `rep_1400f3d20_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 1012 | Property / linked map object layout missing (property node list at +0x100, node payload +0x2b4) [+0x48, +0x50, +0xd4, +0x4bc] |
| `0x1400f9860` | `subsystem_strategic_map_CopyEscadraName_other` | `rep_1400f4120_CopyEscadraName` | 473 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x50, +0x58, +0x79, +0x7a, +0x88, +0x8f, +0x90, +0x11b] |
| `0x1400fb610` | `subsystem_strategic_map_AircraftGroup_FindAttackTarget` | `rep_1400f5f50_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sinf` | 1526 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x28, +0x48, +0x50, +0x78, +0xb0, +0xb4, +0x110, +0x150] |
| `0x1400fd340` | `subsystem_strategic_map_CopyEscadraName_other` | `rep_1400f7c20_GetStats` | 1486 | Property / linked map object layout missing (property node list at +0x100, node payload +0x2b4) [+0x10, +0x18, +0x1f, +0xf8, +0x100, +0x160, +0x164, +0x188] |
| `0x1400fd990` | `subsystem_strategic_map_GetPartFlagsWord` | `rep_1400f8270_std::vector<unsigned___int64,class_std::allocator<unsigned___int64>_>::_Reallocate_exactly` | 1145 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x10, +0x2c8] |
| `0x1400fe160` | `subsystem_strategic_map_GetPropertyLinkedObject` | `rep_1400f8a40_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 667 | Property / linked map object layout missing (property node list at +0x100, node payload +0x2b4) [+0x100, +0x17ec, +0x17f0, +0x17f4] |
| `0x140104ae0` | `subsystem_strategic_map_GetPropertyLinkedObject` | `rep_1400ff1e0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::ceilf` | 270 | Property / linked map object layout missing (property node list at +0x100, node payload +0x2b4) [+0x100, +0x4bc] |
| `0x140107780` | `subsystem_strategic_map_Escadra_DestroyMemberList` | `rep_140101e20_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 1760 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x10, +0x18, +0x27, +0x150, +0xff00] |
| `0x14010f1f0` | `subsystem_strategic_map_ComputeInterceptPoint` | `rep_140109710_Get_Profile?` | 1771 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x2a, +0x2b, +0x30, +0x48, +0x4a, +0x4b, +0x4d, +0x53] |
| `0x1401102c0` | `subsystem_strategic_map_Object_GetPos150` | `FUN_1401102c0` | 117 | undocumented field (see offsets) [+0xb0, +0x494] |
| `0x1401105b0` | `subsystem_strategic_map_FindAmmoIndex_other` | `rep_14010a970_MSVCP140.DLL::std::_Xlength_error` | 316 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x48, +0x4c, +0x338, +0x340] |
| `0x140110e20` | `subsystem_strategic_map_LinkedList_ClearFree` | `rep_14010b1e0_MakeGlobal?` | 361 | undocumented field (see offsets) [+0x2d8, +0x2e0, +0x318, +0x328, +0x3a8, +0x3ac, +0x3b0, +0x3b4] |
| `0x140110f90` | `subsystem_strategic_map_PlayRadioSound` | `rep_14010b350_playSFXSound?` | 370 | undocumented field (see offsets) [+0x49, +0x178] |
| `0x140111e00` | `subsystem_strategic_map_GetPropertyLinkedObject` | `rep_14010c1b0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 489 | Property / linked map object layout missing (property node list at +0x100, node payload +0x2b4) [+0x50, +0xa5, +0x52c] |
| `0x140116040` | `subsystem_strategic_map_FindGuiElement_other` | `rep_140110240_rightPadInteger` | 4363 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0xb, +0xc, +0xd, +0xe, +0xf, +0x14, +0x1c, +0x27] |
| `0x1401186a0` | `subsystem_strategic_map_LoadParticle_other` | `rep_1401127e0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | 2710 | undocumented field (see offsets) [+0x50, +0x68, +0x80, +0x90, +0x94, +0x98, +0x9c, +0x128] |
| `0x1401195d0` | `subsystem_strategic_map_Mark_UpdateIntel` | `rep_140113710_API-MS-WIN-CRT-MATH-L1-1-0.DLL::_fdclass` | 1641 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [(no +const)] |
| `0x140119c40` | `subsystem_strategic_map_Get_Profile` | `rep_140113d80_Get_Profile?` | 267 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x2a, +0x48, +0x50, +0x154, +0x178] |
| `0x140119d70` | `subsystem_strategic_map_Escadra_BuildRoutePath` | `rep_140113eb0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | 977 | undocumented Escadra field (see offsets) [+0x10, +0x150, +0x154, +0x248, +0x2d0, +0x2d4, +0x2d8, +0x2e0] |
| `0x14011a150` | `subsystem_strategic_map_GetStats` | `rep_140114280_GetStats` | 210 | as above |
| `0x14011b450` | `subsystem_strategic_map_GetPropertyLinkedObject` | `rep_140115580_Get_Profile?` | 1445 | Property / linked map object layout missing (property node list at +0x100, node payload +0x2b4) [+0x100, +0x158, +0x168, +0x174, +0x178, +0x17c, +0x464, +0x47c] |
| `0x14011e5d0` | `subsystem_strategic_map_New` | `rep_140118700_New` | 666 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x10, +0x18, +0x27] |
| `0x14011e910` | `subsystem_strategic_map_New` | `rep_140118a40_New` | 423 | undocumented field (see offsets) [(no +const)] |
| `0x14011f690` | `subsystem_strategic_map_Get_Profile` | `rep_1401195d0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | 2114 | Property / linked map object layout missing (property node list at +0x100, node payload +0x2b4) [+0xc, +0x10, +0x11, +0x14, +0x15, +0x18, +0x19, +0x1c] |
| `0x140120470` | `subsystem_gui_ui_Body_SpawnBurningParticles` | `rep_14011a3a0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::atan2f` | 3994 | Property / linked map object layout missing (property node list at +0x100, node payload +0x2b4) [+0xb, +0xc, +0xe, +0x10, +0x11, +0x13, +0x15, +0x16] |
| `0x1401215c0` | `subsystem_gui_ui_rep_140118570_New` | `rep_14011b4f0_VCRUNTIME140.DLL::memset` | 562 | undocumented field (see offsets) [+0x1f] |
| `0x140122650` | `subsystem_gui_ui_CopyString` | `rep_14011c4e0_loadMediaByName?` | 569 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [(no +const)] |
| `0x140125000` | `subsystem_gui_ui_FX_OffsetParticles` | `rep_14011e650_MSVCP140.DLL::_Xtime_get_ticks` | 1296 | undocumented field (see offsets) [(no +const)] |
| `0x1401262b0` | `subsystem_gui_ui_VectorBool_InsertRange` | `rep_14011f1e0_VCRUNTIME140.DLL::memset` | 635 | undocumented field (see offsets) [(no +const)] |
| `0x140127090` | `subsystem_gui_ui_Vector24_At` | `rep_14011f490_API-MS-WIN-CRT-MATH-L1-1-0.DLL::floorf` | 836 | Sprite layout missing (+0x78 owner, +0x90 name string, +0xdc..+0x124) [+0x18, +0x20, +0x7c, +0x80, +0x84, +0x90, +0x9c, +0xc0] |
| `0x14012ebe0` | `subsystem_gui_ui_CopyString` | `rep_140125ca0_CopyString` | 116 | Gui second string +0xcc8 and byte +0xc98 (the +0xa60 string family is documented) |
| `0x14012ec60` | `subsystem_gui_ui_CopyString` | `rep_140125d20_CopyString` | 125 | Gui +0xab8/+0xac8/+0xad0 and +0xc98/+0xcc8 — member map missing |
| `0x14015c410` | `subsystem_gui_ui_CopyString` | `rep_140151060_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 298 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x2e8, +0x300, +0xc9c] |
| `0x14015c7f0` | `subsystem_gui_ui_GetStats` | `rep_140151440_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 1076 | sort/partition/sift helper on an element stride — element layout only, sort family [+0x60, +0x68, +0x6c, +0x71, +0x78, +0x80, +0x88, +0x90] |
| `0x140163640` | `subsystem_engine_res_Gui_DrawScaledShape` | `rep_wrap_0_FUN_14004fb50` | 112 | Gui +0xd70/+0xd74 (int x/y) and +0xdbc/+0xdc0 (float accumulators) |
| `0x140166420` | `subsystem_engine_res_CopyEscadraName_source_path` | `rep_14015af50_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | 3807 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x48, +0x50, +0x110, +0x1008, +0x100c, +0x1010, +0x1014, +0x1018] |
| `0x14016b6c0` | `subsystem_engine_res_copyVariousEscadraBulk` | `rep_wrap_0_rep_14015ed90_CopyString` | 137 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0xa39] |
| `0x14016c160` | `subsystem_engine_res_CopyString` | `rep_140160750_CopyString` | 87 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [(no +const)] |
| `0x140170b90` | `subsystem_engine_res_CopyString_other` | `rep_1401650a0_VCOMP140.DLL::_vcomp_for_static_end` | 657 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x10, +0x18, +0x20, +0x28, +0x88] |
| `0x140183350` | `subsystem_engine_res_New` | `rep_140177740_New` | 184 | undocumented field (see offsets) [+0x19, +0x24, +0x2c] |
| `0x140183520` | `subsystem_engine_res_New` | `rep_140177aa0_New` | 860 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x27] |
| `0x140183a10` | `subsystem_engine_res_GetStats` | `rep_140177e00_New` | 1005 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x10, +0x18, +0x19, +0x1c, +0x1d, +0x20, +0x27, +0xb0] |
| `0x140183e00` | `subsystem_engine_res_AllocArrayStride8` | `rep_1401781f0_std::vector<unsigned___int64,class_std::allocator<unsigned___int64>_>::_Change_array` | 243 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x10] |
| `0x140183f00` | `subsystem_engine_res_Array_CopyConstruct56` | `rep_1401782f0_New` | 635 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x27, +0x38] |
| `0x1401845c0` | `subsystem_engine_res_RbTree_FreeAllNodes` | `rep_1401789f0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 113 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x19] |
| `0x1401847d0` | `subsystem_engine_res_New` | `rep_140178b80_New` | 156 | undocumented field (see offsets) [+0xc] |
| `0x140184870` | `subsystem_engine_res_CopyEscadraName` | `rep_140178c20_New` | 819 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0xc, +0xe, +0x18, +0x1a, +0x1c, +0x1e, +0x20, +0x22] |
| `0x1401859b0` | `subsystem_engine_res_ISerializable_Destructor` | `rep_140179e70_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 108 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x19, +0x48] |
| `0x140186810` | `subsystem_engine_res_Editor_HandleClickMode9` | `rep_14017ae80_Get_Profile?` | 694 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x18, +0x19, +0x1c, +0x88, +0x110] |
| `0x14018e6a0` | `subsystem_engine_res_Locale_GetCtypeFacet` | `rep_140180b70_MSVCP140.DLL::std::basic_istream<char,struct_std::char_traits<char>_>::_Ipfx` | 472 | undocumented field (see offsets) [+0x10, +0x18, +0x28, +0x48] |
| `0x14018ecd0` | `subsystem_engine_res_CopyString_other` | `rep_1401811a0_New` | 709 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0xc, +0xe] |
| `0x140191a80` | `subsystem_engine_res_FillRange8` | `rep_140183f50_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 264 | undocumented field (see offsets) [+0x10, +0x18, +0x20, +0x38] |
| `0x140191b90` | `subsystem_engine_res_FillRange8` | `rep_140184060_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 220 | undocumented field (see offsets) [+0x10, +0x18, +0x20, +0x38] |
| `0x140191f60` | `subsystem_engine_res_DynNewSerializable_other` | `rep_140184430_API-MS-WIN-CRT-CONVERT-L1-1-0.DLL::_atoi64` | 215 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x18] |
| `0x140192250` | `subsystem_engine_res_DynNewSerializable` | `rep_140184720_API-MS-WIN-CRT-CONVERT-L1-1-0.DLL::_atoi64` | 89 | undocumented field (see offsets) [+0x18] |
| `0x1401923b0` | `subsystem_engine_res_DynNewSerializable` | `rep_140184880_API-MS-WIN-CRT-CONVERT-L1-1-0.DLL::_atoi64` | 161 | undocumented field (see offsets) [+0x10, +0x18] |
| `0x1401938b0` | `subsystem_engine_res_SetLink` | `rep_140185c80_MakeGlobal?` | 179 | undocumented field (see offsets) [+0xd, +0x10, +0x13, +0x16, +0x1c, +0x20, +0x22, +0x38] |
| `0x140195100` | `subsystem_engine_res_basic_ios_char` | `rep_140187440_MSVCP140.DLL::std::basic_streambuf<char,struct_std::char_traits<char>_>::streambuf` | 206 | undocumented field (see offsets) [+0x70, +0x7c, +0x88, +0xa8] |
| `0x140195240` | `subsystem_engine_res_FileBuf_Destructor` | `rep_140187580_MSVCP140.DLL::std::basic_istream<char,struct_std::char_traits<char>_>::~basic_istream<char,struct_std::char_traits<char>_>` | 101 | undocumented field (see offsets) [+0x16] |
| `0x140195b50` | `subsystem_engine_res_WriteToClientLog` | `rep_140187e90_WriteToClientLog` | 192 | undocumented field (see offsets) [(no +const)] |
| `0x140196120` | `subsystem_engine_res_CopyEscadraName` | `rep_140188460_CopyEscadraName` | 508 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [(no +const)] |
| `0x140196ff0` | `subsystem_engine_res_CopyString` | `rep_140189170_CopyString` | 540 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x18] |
| `0x140197510` | `subsystem_engine_res_AllocArrayStride40` | `rep_140189530_std::vector<struct_CHN*___ptr64,class_std::allocator<struct_CHN*___ptr64>_>::vector<struct_CHN*___ptr64,class_std::allocator<struct_CHN*___ptr64>_>` | 465 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [(no +const)] |
| `0x140197870` | `subsystem_engine_res_Array_MoveConstruct40String` | `rep_140189890_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 743 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x20, +0x27] |
| `0x14019a870` | `subsystem_engine_res_Object_FreeTwoVectors` | `rep_14018c880_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 118 | undocumented field (see offsets) [+0x19] |
| `0x14019ae0f` | `subsystem_engine_res_CopyEscadraName` | `FUN_14019ae0f` | 50 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x20] |
| `0x14019b1c0` | `subsystem_engine_res_compareEscadraString` | `rep_14018cf00_compData` | 923 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x32, +0xe8] |
| `0x14019b560` | `subsystem_engine_res_compareEscadraString` | `rep_14018d2a0_VCRUNTIME140.DLL::memmove` | 521 | same {+0x28,+0xd8,+0xe0,+0x108} comparator family |
| `0x14019b770` | `subsystem_engine_res_stringCopyWithMemoryFree` | `rep_14018d4b0_VCRUNTIME140.DLL::memcmp` | 694 | undocumented field (see offsets) [+0x10, +0x18, +0x20, +0x28] |
| `0x14019bd90` | `subsystem_engine_res_compareEscadraString` | `rep_14018dad0_compData` | 635 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x10, +0x28, +0xd8, +0xe0, +0x108] |
| `0x14019c010` | `subsystem_engine_res_compareEscadraString` | `rep_14018dd50_compData` | 797 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x18, +0x20, +0x28, +0x48, +0x50, +0x70] |
| `0x14019c330` | `subsystem_engine_res_compareEscadraString` | `rep_14018e070_compData` | 913 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [(no +const)] |
| `0x14019c920` | `subsystem_engine_res_compareEscadraString` | `rep_14018e660_compData` | 306 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [(no +const)] |
| `0x14019ca60` | `subsystem_engine_res_compareEscadraString` | `rep_14018e7a0_compData` | 182 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [(no +const)] |
| `0x14019cb20` | `subsystem_engine_res_GetStats` | `rep_14018e860_GetStats` | 391 | undocumented field (see offsets) [+0x10, +0xb4, +0x188] |
| `0x14019ef90` | `subsystem_engine_res_compareEscadraString` | `rep_1401907c0_compData` | 1147 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [(no +const)] |
| `0x14019f410` | `subsystem_engine_res_compareEscadraString` | `rep_140190c40_compData` | 758 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [(no +const)] |
| `0x14019f810` | `subsystem_engine_res_compareEscadraString` | `rep_140191040_compData` | 950 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x10, +0x32, +0xe8] |
| `0x14019fcf0` | `subsystem_engine_res_compareEscadraString` | `rep_140191520_compData` | 540 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x10, +0x28, +0xd8, +0xe0, +0x108] |
| `0x14019ff10` | `subsystem_engine_res_compareEscadraString` | `rep_140191740_compData` | 393 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x20, +0x28, +0x48, +0x50, +0x70] |
| `0x1401a00a0` | `subsystem_seria_level_compareEscadraString` | `rep_1401918d0_compData` | 510 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [(no +const)] |
| `0x1401a0aa0` | `subsystem_seria_level_Sort_IntrosortFloat` | `rep_1401920b0_VCRUNTIME140.DLL::memmove` | 772 | sort/partition/sift helper on an element stride — element layout only, sort family [(no +const)] |
| `0x1401a0db0` | `subsystem_seria_level_Sort_HeapSiftByValue3D8` | `rep_1401923c0_VCRUNTIME140.DLL::memmove` | 730 | sort/partition/sift helper on an element stride — element layout only, sort family [+0x3d8] |
| `0x1401a1230` | `subsystem_seria_level_Sort_HeapSiftByStats` | `rep_140192840_VCRUNTIME140.DLL::memmove` | 867 | sort/partition/sift helper on an element stride — element layout only, sort family [(no +const)] |
| `0x1401a1710` | `subsystem_seria_level_rep_14018dd50_compData` | `rep_140192d20_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 573 | undocumented field (see offsets) [(no +const)] |
| `0x1401a1950` | `subsystem_seria_level_rep_14018e070_compData` | `rep_140192f60_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 475 | undocumented field (see offsets) [(no +const)] |
| `0x1401a1c00` | `subsystem_seria_level_CopyEscadraName_other` | `rep_140193210_CopyEscadraName` | 647 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0xc, +0xe] |
| `0x1401a3fe0` | `subsystem_seria_level_CopyEscadraName` | `rep_140195770_CopyEscadraName` | 189 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x20] |
| `0x1401a6310` | `subsystem_seria_level_rep_14019eab0_New` | `rep_140197950_VCRUNTIME140.DLL::memmove` | 238 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [(no +const)] |
| `0x1401a7c10` | `subsystem_seria_level_compareEscadraString` | `rep_140198590_VCRUNTIME140.DLL::memcmp` | 185 | comparator over {+0x28 key, +0xd8/+0xe0 string, +0x108} records (record layout undocumented) |
| `0x1401a7f30` | `subsystem_seria_level_compareEscadraString` | `rep_140198650_VCRUNTIME140.DLL::memcmp` | 361 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x32, +0xe8] |
| `0x1401a80a0` | `subsystem_seria_level_StringBuf_Destructor` | `rep_1401987c0_MSVCP140.DLL::std::basic_ios<char,struct_std::char_traits<char>_>::~basic_ios<char,struct_std::char_traits<char>_>` | 95 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x11] |
| `0x1401a8160` | `subsystem_seria_level_StringBuf_Destructor` | `rep_140198880_MSVCP140.DLL::std::basic_ios<char,struct_std::char_traits<char>_>::~basic_ios<char,struct_std::char_traits<char>_>` | 146 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [(no +const)] |
| `0x1401ae4a0` | `subsystem_seria_level_freeLinkMemory` | `rep_140019710_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_invalid_parameter_noinfo_noreturn` | 209 | Link-list teardown helper (`freeLinkMemory`) — container family [+0x10, +0x38] |
| `0x1401ae9c0` | `subsystem_seria_level_Map_EraseNodeRebalance` | `rep_14019eea0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 142 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x19, +0x28] |
| `0x1401b4890` | `subsystem_seria_level_Get_Profile` | `rep_1401a48b0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sinf` | 2214 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x10, +0x24, +0x1840, +0x1844, +0x1850] |
| `0x1401b67c0` | `subsystem_seria_level_CopyEscadraName_other` | `rep_1401a66f0_VCRUNTIME140.DLL::memmove` | 1347 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0xf, +0x10, +0x27, +0x28, +0x2d8, +0x1008, +0x100c] |
| `0x1401b8ff0` | `subsystem_seria_level_Creature_FindBestMissile` | `rep_1401a8f80_Get_Profile?` | 232 | Creature +0xc18 byte (next to the +0xc19 prize flag) and fleet-object +0x108 |
| `0x1401b9650` | `subsystem_seria_level_Get_Profile` | `rep_1401a95e0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::floorf` | 744 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x2a, +0x2d, +0x2f, +0x30, +0x9a, +0x9b, +0x9c, +0x178] |
| `0x1401b99a0` | `subsystem_seria_level_Fleet_IrstStrength` | `rep_1401a9930_API-MS-WIN-CRT-MATH-L1-1-0.DLL::pow` | 1101 | undocumented Escadra field (see offsets) [+0x2a, +0x2d, +0x6f, +0x72, +0x178, +0x17c, +0x461, +0x4dc] |
| `0x1401ba570` | `subsystem_seria_level_Fleet_DetectionStrength` | `rep_1401aa500_API-MS-WIN-CRT-MATH-L1-1-0.DLL::atan2f` | 2019 | undocumented Escadra field (see offsets) [+0x2a, +0x6f, +0x72, +0x9a, +0x154, +0x178, +0x29c, +0x42c] |
| `0x1401c9840` | `subsystem_seria_level_CopyEscadraName` | `rep_1401b47d0_VCRUNTIME140.DLL::memchr` | 2263 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x27, +0x28] |
| `0x140202f50` | `subsystem_seria_level_Gui_DestroyElementsByName_other` | `rep_1401e8a70_VCRUNTIME140.DLL::memmove` | 1575 | sort/partition/sift helper on an element stride — element layout only, sort family [+0x10, +0x50, +0xb0, +0xb8, +0xf8, +0x100, +0x108, +0x11b] |
| `0x140203580` | `subsystem_seria_level_CopyString_other` | `rep_1401e90a0_VCRUNTIME140.DLL::memmove` | 857 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x10, +0x12, +0x18, +0x20, +0x28, +0x30, +0x31, +0x954] |
| `0x140209b00` | `subsystem_seria_level_CalculateStats_other` | `rep_1401ee7b0_FastFail?` | 549 | undocumented Creature field (see offsets) [+0x10, +0x19, +0x88, +0xb8, +0x108, +0x329, +0xad4, +0xc19] |
| `0x14020e180` | `subsystem_seria_level_CopyString_other` | `rep_1401f2e60_MSVCP140.DLL::std::_Xlength_error` | 1755 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x10, +0x19, +0x2d, +0x34, +0x50, +0x68, +0x6a, +0x75] |
| `0x14020eba0` | `subsystem_seria_level_Creature_BroadcastCommand19A` | `rep_1401f3880_API-MS-WIN-CRT-MATH-L1-1-0.DLL::cosf` | 909 | undocumented Creature field (see offsets) [+0x18, +0x25, +0x27, +0x28, +0x48, +0x58, +0xb8, +0xe8] |
| `0x14020ef30` | `subsystem_seria_level_APP_MoveVolume` | `rep_1401f3c10_APP:MoveVolume` | 1560 | undocumented Escadra field (see offsets) [+0x18, +0x19, +0x48, +0x50, +0x88, +0x122, +0x2fc, +0x348] |
| `0x140210450` | `subsystem_seria_level_Body_RepairForGold` | `rep_wrap_0_rep_14005e660_New` | 66 | wrapper object +0x8 (Body +0xb8 documented) |
| `0x140213120` | `subsystem_seria_level_Get_Profile` | `rep_1401f7190_API-MS-WIN-CRT-MATH-L1-1-0.DLL::atan2f` | 3737 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x28, +0x150, +0x154, +0x168, +0x17c, +0x254, +0x461, +0x4dc] |
| `0x140214030` | `subsystem_seria_level_CreateTriggerVal_other` | `rep_1401f80a0_VCRUNTIME140.DLL::memmove` | 580 | Gui member map missing (see +0xa34/+0xa39/+0x91c/+0xee8/+0xd70 group in the field list) [+0xe, +0x18, +0x20, +0x30, +0x118, +0x1cc, +0x1d0, +0x1d4] |
| `0x140215430` | `subsystem_seria_level_Effect_SetColour4f_other` | `rep_1401f9490_API-MS-WIN-CRT-MATH-L1-1-0.DLL::atan2f` | 1833 | undocumented field (see offsets) [+0xa8, +0x10d, +0x110, +0x194, +0x1a4, +0x1ac, +0x1b4, +0x1bc] |
| `0x1402161e0` | `subsystem_seria_level_Get_Profile` | `rep_1401fa230_API-MS-WIN-CRT-MATH-L1-1-0.DLL::cosf` | 619 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [(no +const)] |
| `0x140222510` | `subsystem_seria_level_Body_SetAngularVelocity` | `rep_140204c60_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sinf` | 4886 | undocumented field (see offsets) [+0x18, +0x20, +0x25, +0x27, +0x28, +0x70, +0x78, +0xe8] |
| `0x1402410c0` | `subsystem_seria_level_Body_RebuildSubtreeList` | `rep_140222060_CopyString` | 558 | undocumented Creature field (see offsets) [+0x28, +0x48, +0x88, +0xa90, +0xaa0, +0xaa8] |
| `0x140242c10` | `subsystem_seria_level_SetLink` | `rep_140223bb0_MakeGlobal?` | 370 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x48] |
| `0x140243ff0` | `subsystem_seria_level_CopyEscadraName` | `rep_140225190__Init_thread_footer` | 1896 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x20, +0x27, +0x28, +0x58] |
| `0x140246de0` | `subsystem_seria_level_Gfx_DrawWorldLine` | `rep_140226320__Init_thread_footer` | 2646 | undocumented field (see offsets) [+0xc, +0x10, +0x18, +0x20, +0x58, +0x70, +0x78, +0x224] |
| `0x140249770` | `subsystem_seria_level_CreateTriggerVal_other` | `rep_140228570_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | 2324 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x10, +0x30, +0x150, +0x154, +0x2c8, +0x884, +0x100c] |
| `0x14024af20` | `subsystem_seria_level_Matrix3x3_Identity` | `rep_140229cc0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sinf` | 1303 | undocumented field (see offsets) [+0x2e0] |
| `0x14024b810` | `subsystem_seria_level_VideoTask_Dispatch` | `rep_14022a5b0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 1023 | undocumented field (see offsets) [+0x10, +0x11, +0x84, +0x8c, +0xb0, +0xe8, +0x910] |
| `0x14024c110` | `subsystem_seria_level_Creature_RebuildRepairQueue_source_path` | `rep_14022aed0_New` | 1332 | undocumented Creature field (see offsets) [+0x10, +0x18, +0x48, +0x50, +0x68, +0xb8] |
| `0x14024c740` | `subsystem_seria_level_AssignRandomId` | `rep_14022b500_CopyString` | 412 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x48, +0x80, +0x88, +0xf5, +0x2d4, +0xfffffffffffffff8] |
| `0x14024d790` | `subsystem_seria_level_CopyEscadraName_image_path` | `rep_14022c300_CopyEscadraName` | 454 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [(no +const)] |
| `0x14024e6d0` | `subsystem_seria_level_Body_RebuildSubtreeList_other` | `rep_14022cff0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 1504 | box2d proxy/joint internals [+0xc, +0xd, +0x18, +0x28, +0x48, +0x111] |
| `0x140252dc0` | `subsystem_seria_level_CopyString` | `rep_140231550_CopyString` | 1341 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x70, +0x90, +0xa0, +0xa8, +0x8c0, +0x8c8] |
| `0x14025f270` | `subsystem_seria_level_Body_CollectNeighbourParts_model_name` | `rep_14023d420_VCRUNTIME140.DLL::memcmp` | 1394 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x28, +0x100, +0x108, +0x1a0, +0x1a8, +0x9b8, +0x9bc] |
| `0x14025f810` | `subsystem_seria_level_AdjustWindowRect` | `rep_14023d8f0_USER32.DLL::AdjustWindowRect` | 536 | undocumented field (see offsets) [+0x28, +0x38, +0x50, +0x1a8, +0x1ac, +0x2e8, +0x2f0, +0x2f8] |
| `0x1402641f0` | `subsystem_seria_level_setXposYpos_other` | `rep_1402423c0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::powf` | 2764 | undocumented field (see offsets) [+0x48, +0x58, +0x488, +0x48c, +0xa40, +0xa50, +0xa58] |
| `0x140264cc0` | `subsystem_seria_level_CalculateStats` | `rep_140242e90_AlwaysReturn1` | 306 | undocumented Creature field (see offsets) [+0x10, +0x48, +0x50, +0x68, +0xb8] |
| `0x140265240` | `subsystem_seria_level_Body_Constructor_other` | `rep_140243450_New` | 1041 | Gui member map missing (see +0xa34/+0xa39/+0x91c/+0xee8/+0xd70 group in the field list) [+0xc, +0x3e, +0x50, +0x79, +0x7a, +0x7b, +0x88, +0x92] |
| `0x140265880` | `subsystem_seria_level_Get_Profile` | `rep_140243a90_Get_Profile?` | 264 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [(no +const)] |
| `0x140265b70` | `subsystem_seria_level_AssignRandomId_model_name` | `rep_140243d80_MakeGlobal?` | 519 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x3e, +0x49, +0x50, +0x79, +0x7a, +0x80, +0x88, +0x95] |
| `0x140265d80` | `subsystem_seria_level_CalculateStats` | `rep_140243f90_MakeGlobal?` | 885 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x10, +0x28, +0x6d, +0xb8, +0x100, +0x108, +0x148, +0x178] |
| `0x140269fe0` | `subsystem_seria_level_CopyString_model_name` | `rep_140248320_New` | 3021 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x27, +0x28, +0x32, +0x43, +0x48, +0x58, +0x60, +0x88] |
| `0x14026abc0` | `subsystem_seria_level_Engine_ApplyThrustCommand_model_name` | `rep_140248f00_New` | 750 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x18, +0x28, +0x48, +0xe8, +0x1a0, +0x1a8, +0x1390, +0x1398] |
| `0x140271200` | `subsystem_seria_level_SetBackground_other` | `rep_14024f4f0_Get_Profile?` | 733 | Gui member map missing (see +0xa34/+0xa39/+0x91c/+0xee8/+0xd70 group in the field list) [+0x18, +0x88, +0x860, +0x1408, +0x1410] |
| `0x14027fb50` | `subsystem_seria_level_Joint_CreateB2Joint_other` | `rep_14025d8a0_New` | 181 | box2d proxy/joint internals [+0x50, +0x58, +0x110, +0x118] |
| `0x14027fc70` | `subsystem_seria_level_CopyEscadraName` | `rep_14025d9c0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 916 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x18] |
| `0x140280fa0` | `subsystem_scene_hud_Joint_DestroyB2Joint` | `rep_14025ecf0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 209 | box2d proxy/joint internals [+0x50, +0x58, +0x60, +0x78, +0x90, +0x110, +0x118] |
| `0x140286a60` | `subsystem_scene_hud_New` | `rep_14005e3f0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 470 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x10, +0x18, +0x27] |
| `0x140289280` | `subsystem_scene_hud_CopyString` | `rep_140266750_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 574 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x10, +0x18] |
| `0x14028d750` | `subsystem_scene_hud_VectorStride64_DestroyRange` | `rep_14026b130_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 1073 | undocumented field (see offsets) [+0xc, +0xf, +0x10, +0x40, +0x108, +0x110, +0x588, +0x590] |
| `0x14028fec0` | `subsystem_scene_hud_GetEscadraOrCallsign` | `rep_14026d620_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 844 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0xf8, +0x108, +0x150, +0x154, +0x1f8, +0x200, +0x208, +0x210] |
| `0x1402924e0` | `subsystem_scene_hud_Profile_GetActive` | `rep_14026f9b0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::atan2f` | 832 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x18, +0x24, +0x40, +0x578, +0x57c, +0x580, +0x588, +0x590] |
| `0x140293940` | `subsystem_scene_hud_Profile_GetActive` | `rep_140270c50_compData` | 239 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x19, +0x30, +0x430, +0xa90, +0xad0] |
| `0x14029ad00` | `subsystem_scene_hud_Gfx_QuadRenderEx` | `rep_140277fe0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 317 | undocumented field (see offsets) [+0x14, +0x1c, +0xffffff] |
| `0x1402a34e0` | `subsystem_scene_hud_Profile_GetActive` | `rep_14027fad0_Get_Profile?` | 733 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x150, +0x178, +0x1f8, +0x200] |
| `0x1402ab760` | `subsystem_scene_hud_IObject_Destructor` | `rep_1402877e0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 345 | undocumented field (see offsets) [+0x73] |
| `0x1402cbd80` | `subsystem_scene_hud_CopyString` | `rep_1402a4e40_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 1234 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0x10] |
| `0x1402d0670` | `subsystem_scene_hud_AircraftGroup_UpdateAttackMove` | `rep_1402a7190_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 1630 | Profile member map missing (only +0x1f8..+0x200 and +0x2a8 are documented) [+0x10, +0x18, +0x19, +0x28, +0x150, +0x154] |
| `0x1402d3150` | `subsystem_scene_hud_Landscape_GroundHeightAt` | `rep_1402a9430_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 2744 | undocumented field (see offsets) [+0x18, +0x78, +0xe8, +0x108, +0x110, +0x20c, +0x30a, +0xad4] |
| `0x1402d3cf0` | `subsystem_scene_hud_New_other` | `rep_1402aa000_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 1096 | container/alloc/CRT family (vector/RbTree/string grow or teardown) — owned by the container agents [+0x14, +0x18, +0x48, +0xe8, +0x128, +0x188, +0x19c, +0x218] |
| `0x1402da7e0` | `subsystem_scene_hud_CopyString` | `rep_1402afb60_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 268 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [(no +const)] |
| `0x1402daf20` | `subsystem_scene_hud_CopyString` | `rep_1402afc70_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 268 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [(no +const)] |
| `0x1402db900` | `subsystem_scene_hud_BlankInit` | `rep_1402b04f0_ISerializable::ISerializable` | 227 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0xf, +0x48, +0x84, +0x85, +0x90, +0xa0, +0xa8, +0xb0] |
| `0x1402db9f0` | `subsystem_scene_hud_BlankInit` | `rep_1402b05e0_ISerializable::ISerializable` | 108 | undocumented field (see offsets) [+0xf] |
| `0x1402dba60` | `subsystem_scene_hud_ISerializable_Destructor` | `rep_1402b0650_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 180 | Link-list teardown helper (`freeLinkMemory`) — container family [+0xd, +0x12] |
| `0x1402dcbc0` | `subsystem_scene_hud_CopyEscadraName` | `rep_1402b1710_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 870 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [(no +const)] |
| `0x1402dcf30` | `subsystem_scene_hud_Joint_QueueDead` | `rep_1402b1a80_MakeGlobal?` | 316 | box2d proxy/joint internals [+0x50, +0x58, +0x70, +0x78, +0x80, +0x88, +0xb8, +0x230] |
| `0x1402ddda0` | `subsystem_scene_hud_ISerializable_Destructor` | `rep_1402b28f0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 286 | box2d proxy/joint internals [+0xd] |
| `0x1402ddec0` | `subsystem_scene_hud_Array_DestroyObjectVector` | `rep_1402b2a10_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 437 | Sprite layout missing (+0x78 owner, +0x90 name string, +0xdc..+0x124) [+0x12, +0x16, +0x1a, +0x2f, +0x160] |
| `0x1402df020` | `subsystem_scene_hud_CopyEscadraName` | `rep_1402b3b70_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 3005 | string helper (CopyString/CopyEscadraName/compareEscadraString), no game struct field — CRT/string family [+0xb, +0xc, +0xd, +0xf] |
| `0x1402e2c10` | `subsystem_scene_hud_freeLinkMemory` | `rep_1402b7750_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 239 | Link-list teardown helper (`freeLinkMemory`) — container family [+0xd, +0x10, +0x2c, +0x200, +0x220] |
| `0x1402eaa10` | `subsystem_scene_hud_freeLinkMemory` | `rep_1402bf4e0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | 174 | Link-list teardown helper (`freeLinkMemory`) — container family [+0x10, +0x38] |
| `0x1402ecbc0` | `subsystem_scene_hud_D3DEngine_DrawVertices1` | `rep_1402c1690_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sinf` | 1839 | box2d proxy/joint internals [+0xc, +0xd, +0xe, +0xf, +0x10, +0x6c, +0x74, +0x7c] |
| `0x1402ee1b0` | `subsystem_scene_hud_normalizeVectors` | `rep_1402c2d20_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sinf` | 387 | undocumented field (see offsets) [(no +const)] |
| `0x1402f5580` | `subsystem_scene_hud_` | `rep_1402ca140_FastFail?` | 2460 | Property / linked map object layout missing (property node list at +0x100, node payload +0x2b4) [+0x80, +0xa8, +0x168] |
| `0x1402f5f20` | `subsystem_scene_hud_D3DEngine_DrawVertices1` | `rep_1402caae0_FastFail?` | 2541 | Property / linked map object layout missing (property node list at +0x100, node payload +0x2b4) [+0x80, +0xa8, +0x168] |
| `0x1402f6b00` | `subsystem_scene_hud_Gfx_DrawArcClipped_source_path` | `rep_1402cb6c0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | 2283 | sort/partition/sift helper on an element stride — element layout only, sort family [+0xc, +0x10] |
| `0x1402f73f0` | `subsystem_scene_hud_Array_Resize40` | `rep_1402cbfb0_Creature::CalculateStats` | 2819 | undocumented Creature field (see offsets) [+0x28, +0x80, +0xb8, +0x108, +0x168, +0x2c8, +0x2f4, +0x888] |
| `0x1402fa610` | `subsystem_scene_hud_Array_Resize40` | `rep_1402cf1e0_Get_Profile?` | 6041 | box2d proxy/joint internals [+0xc, +0xd, +0x10, +0x28, +0x6c, +0x7c, +0x80, +0xa8] |
| `0x1403161a0` | `subsystem_box2d_FUN_140316a50` | `FUN_1403161a0` | 132 | broadphase proxy lookup through DAT_14801dd00 (stride 0x18) — box2d |
| `0x140316a50` | `subsystem_box2d_Property_SetFloat` | `FUN_140316a50` | 213 | writes GUI property/global floats (+0x128/+0x130/+0x1b0/+0x138) of the DAT_143a139xx objects |

## 3. Fields to add to `structures.md` (consolidated)

Ordered by how many skipped bodies they unblock. Each row names the writer and
the reader so the docs agent can paste one line per field.

### Body (3 bodies unblocked directly, ~10 indirectly)

| offset | type | meaning | writer / reader evidence |
|---|---|---|---|
| `+0x80c` | float | **part "enabled / armed" flag** (1.0 = armed). Gates gun reload, launcher release and flare release | writers: `Creature_ResetLaunchItemField80c` 0x14006d900, `Creature_SetSensorPartsEnabled` 0x1400738d0, new `Creature_EnablePartsWithPower/Sensors/Weapons`; readers: findings/guns-aim-reload-fire.md, findings/flares-and-missiles.md, findings/ship-serializer.md. **Already used all over the docs but missing from §Body** |
| `+0x808` | float | `m_mdl_side` (serialised between `m_mdl_crew` +0x804 and the weapon block) | findings/ship-serializer.md; missing from the §Body table |
| `+0x818` | float | power factor `P` in [0,1] (thrust gain `P^2`, reload/power gate) | findings/player-thrust-keys-and-engine-heat.md §4/§13 |
| `+0x814`, `+0x844` | byte/flag | power-consumer membership and exemption flags | same section (`CalculateStats` power budget) |
| `+0x92c` | float | zeroed by the "reset part to definition" path; no reader proved yet | `0x140060a60` (`Body_ResetPartToDefinition` callers) |
| `+0x1c0` | dword | flag word, `|= 0x205` when a part is dropped as debris | `0x14002e7d0` |
| `+0x7ac` | byte | tested together with the documented blueprint flag `+0x7ad` (teardown vs. reparent) | `0x140027bd0` |
| `+0x100` | list head | child/dependant list walked during Body teardown (self-pointer sentinel); different object from the Escadra `+0x100` ship list | `0x140027bd0` |

### Creature

| offset | type | meaning | evidence |
|---|---|---|---|
| `+0x1378` / `+0x1380` | Link vector (stride 0x18, entry +8 = part) | **launch-item list** | `Creature_ResetLaunchItemField80c` writes `+0x80c` over it; `0x14006d930` resets each item's `+0x7f8` fuel to `Stats+0xc8` |
| `+0x1498` / `+0x14a0` | Link vector | **sensor-part list** | `Creature_SetSensorPartsEnabled`; filled by `Creature_AccumulatePartStats` |
| `+0x1348` / `+0x1350` | Link vector | **power-consumer list** | findings/player-thrust-keys-and-engine-heat.md §13 |
| `+0x1540` / `+0x1548` | Link vector, stride 0x30 | part-definition/blueprint comparison list (entries are `memcmp`-ed against a Body) | `0x140060a60` |
| `+0xc80` | double | quantity read before "refill fuel to capacity"; candidate `m_fuel_quantity` | `0x14006d930` |
| `+0xc18` | byte | flag next to the documented prize byte `+0xc19`, gates "has missile" | `0x1401b8ff0` |
| `+0x280` / `+0x288` | Link / node | target link + target node of the "nearest same-side fleet" scan (the documented target is `+0x270`) | `0x140119c40` |

### Profile

| offset | type | meaning | evidence |
|---|---|---|---|
| `+0x3f0` | trigger value | written by `CreateTriggerVal(&profile+0x3f0, "TUTORIAL")` | new `Profile_CreateTutorialTrigger` 0x140215110 |
| `+0x1f8` / `+0x200` | vector<escadra*> | fleet list. `structures.md` documents this pair only as a world-singleton field; `Get_Profile_()+0x1f8` is the same pair | `0x140119c40`, `0x1401b8ff0` |

### Gui — the biggest gap (blocks ~40 bodies)

| offset | type | meaning | evidence |
|---|---|---|---|
| `+0xa34` int, `+0xa39` byte, `+0xa3c` word | | element state set on creation | `0x1400db8e0` (editor pin), `0x14016b6c0` |
| `+0x91c`, `+0x929` bytes | | element flags | `0x1400db8e0` |
| `+0xee8` int | | child index (editor pin / sprite selection) | `0x1400db8e0` |
| `+0xcc8` std::string, `+0xc98` byte, `+0xb08`, `+0xb10` | | second name string + virtual-sprite state (the `+0xa60` string family is already documented) | `0x14012ebe0`, `0x14012ec60` |
| `+0xab8/+0xac8/+0xad0` | std::string (SSO data/len/cap) | media/resource name resolved by `Gui_ResolveMediaName` | `0x14012ec60` |
| `+0xd70`, `+0xd74` int | | draw x/y offsets | `0x140163640` |
| `+0xdbc`, `+0xdc0` float | | draw-position accumulators | `0x140163640` |

### Sprite (blocks 7 bodies)

`+0x78` owner/back-pointer to the HGE-created object, `+0x90` name std::string,
`+0xdc` int, `+0x114..+0x124` ints/floats (frame state), `+0x160` part list.
Evidence: `0x140051f90`, `0x14006ef10`, `0x1400db8e0`.

### Property / linked map object (blocks 15 bodies)

Record used by the map-property code: key at `+0x28`, name std::string at
`+0xc8`/`+0xd8`/`+0xe0` (the same layout as the Location city name), tiebreak
value at `+0x108`; the owning object keeps a property-node list at `+0x100`
and the node payload dword is at `+0x2b4`. Evidence: comparator `0x1401a7c10`
(+ twin `0x14019b560`), distributor `0x140104ae0`.

## 4. Not in scope / caveats

* The 4 `subsystem_crt_eh_*` rows (`0x14033cea0`, `0x14033e350`, `0x1403412f0`,
  `0x140341420`) are `/EH` funclets inside the excluded
  `0x140336730–0x140350510` range and belong to the funclet/CRT agents. They
  were not decompiled here.
* 302 of the 323 `subsystem_*` rows are genuinely structure-gated: 53 are
  container/alloc bodies, 12 Link-list teardown, 58 string helpers and 14 sort
  helpers (all owned by the container/CRT agents), and the rest need the
  Gui / Sprite / Property / Creature maps above.
* Rows whose only field access is a `+0x8`-family record key were left
  unnamed: proving `Body_RepairForGold` from a wrapper (`0x140210450`) needs the
  wrapper object's `+0x8`, not a Body field.
* `0x140070cc0` duplicates the existing `Creature_ComputePartBounds`; it was
  left unnamed rather than duplicating a name.
* Decompilation only (`run_script_inline`, 12 addresses per call, 60 s
  per-function timeout); no rename was applied to a row whose body I did not
  read in full.
