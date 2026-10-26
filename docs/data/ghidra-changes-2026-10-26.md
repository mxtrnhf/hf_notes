# Ghidra changes, 2026-10-26 (ghidra-curator, after reviewing the ds3 agent reports)
Program `Highfleet.exe.unpacked.exe` v1.163, saved; the check-in to the shared project is the user's.

| kind | address | change |
|---|---|---|
| rename | 0x1402fde80 | `tacticalCombat?` -> `DrawBattleShipPanel` (one function draws both bottom ship panels; mode 2 own ship, 3 target) + plate comment |
| plate | 0x140032fb0 | `Projectile_ExplodeAndCluster`: four call sites (not two); bomblet TTL 0.3 f / 1.0 f (constant at 0x1403524d8 read) |
| comment | 0x140309ab4, 0x140309b55 | the two panel calls |
| comment | 0x140010a51 | crash site `+0x10A51`, fix bytes `C4 03` -> `48 00` |
| comment | 0x1400f5b4f | crash site `+0xF5B4F`, 7-byte instruction: a 5-byte guard does not fit |
| comment | 0x1402b8a22, a27, a35, a3e | end-game gate: flag 1 is Khiva LOCATION +0x2ec (not Profile), flag 2 Profile +0x2e9, flag 3 global 0x147fc6fca |

Verified by the curator this session (bytes or disassembly re-read): bomblet xref count and constant, gate disassembly and "KHIVA" string, panel call sites, crash bytes at both sites, target-chooser foe test polarity (`JA` skip when side product > 0; a second same-side call `0x1402213e0` follows it, which the ds3-target report did not describe for the global-list branch). Not re-verified: missile report, sensors report beyond the callers of `0x1402378a0` (UpdateStrategicFleet is one, consistent with fleet vs fleet), colour/zoom details of the panel.

## Second batch (after reviewing the missile, sensors, endgame, crash, bomblet and subview reports)
Old names are in the plate comments (rule of 2026-10-26).
| kind | address | change |
|---|---|---|
| rename | 0x1402f7f00 | `rep_1402ccac0__Init_thread_header` -> `DrawNoiseHudOverlay` |
| rename | 0x14004dd50 | `rep_14004b960_..::cosf` -> `Body_UpdateRenderTransform` |
| rename | 0x1402104a0 | `rep_1401f4fd0_..::floorf` -> `Fleet_ElintGrade` (emitter is the first argument) |
| rename | 0x14021f2f0 | `FUN_14021f2f0` -> `Fleet_IrstStrength` |
| rename | 0x14022c250 | `rep_14020e2f0_WriteToClientLogMain` -> `ComputeInterceptPoint` |
| plate | 0x1402378a0 | `Fleet_DetectionStrength`: strategic map, gates, rule |
| plate | 0x140061260 | `Creature_MergeSectorArray`: rule byte, ten calls |
| plate | 0x14004ec80, 0x1400488d0, 0x14006c0e0 | `SetShipZoom`, `GetMissileFuzeType`, `Creature_GetFirstOfVec0xCA0` |
| plate | 0x140261a20 | `spawnEndgameShips?`: Khiva crash, guard cave, gate flags |
| plate | 0x1400f5b40 | `Escadra_FindLandingShipNode`: crash site +0xF5B4F and the 16-byte guard |
| plate | 0x1400109c0 | `AircraftLogic_State6_SelectTarget`: crash site +0x10A51 and the 2-byte fix |
| comments | 0x140036288, 0x14003641e, 0x14003635b, 0x140036318, 0x1400367c7, 0x140036886, 0x140036c68, 0x140034269, 0x140034448, 0x140037245, 0x1400361a2 | missile block: flare rule, constants, fuse, bomblet calls, steering, give-up state (two of these addresses already held a comment, which the batch overwrote) |
Verified by the curator (bytes or disassembly re-read): flare gate and `0x44c` compare, constants pi/4, 400, 0.01, 0.001, 20, 0.1; the four Khiva write blocks (84 bytes) and the `endWar` store; the detection function head and its callers. Not independently verified: the panel colours and zoom, the ELINT/IRST formulas, the steering aim table, the per-id table beyond the ids named above.

## Third batch: ClickFunc analysis workspace (hf_ml/analysis/clickfunc), verified items only
Old names are in the plate comments. Re-read by the curator: decompile or disassembly of every function below, the `XMM3` call site, the `m_spasmcode` and `m_intel_data` strings and the three difficulty writes.
| kind | address | change |
|---|---|---|
| rename | 0x1402d8ee0 | `FUN_1402d8ee0` -> `hotseatPrecombatOk` |
| rename | 0x1401404b0 | `rep_140135ac0_VCRUNTIME140.DLL::memcmp` -> `ClickFunc_ListMiniDispatch` |
| rename | 0x140264f20 | `FUN_140264f20` -> `Shipworks_CommitDesignAsControlledShip` |
| rename | 0x1401c32b0 | `FUN_1401c32b0` -> `Gui_CreateConfirmDialog` |
| rename | 0x1402213b0 | `FUN_1402213b0` -> `Ship_IsAliveWithThrust` (the analysis' "ready for 6/7" is inverted; corrected in the plate) |
| rename | 0x1400a61f0 | `FUN_1400a61f0` -> `Escadra_IsPlayerSide` |
| rename | 0x140251fd0 | `miscMapSomething2?` -> `MapUi_SelectFleet` |
| rename | 0x1400ba3a0, 0x1402923f0, 0x1402924d0 | `FUN_*` -> `Profile_SubtractCash`, `Profile_GetCaptainHirePrice`, `Profile_GetFirstPlayerCreature` |
| rename | 0x1400530e0, 0x1400188e0 | `diffArrayDivBy24`, `multElementsBy24` -> `Vec24_Size`, `Vec24_At` (0x18-byte elements, not editor-only) |
| rename | 0x14012ca00, 0x140165a00, 0x1401659c0, 0x140165940, 0x140129f40, 0x14012a4b0 | `FUN_*` -> `Vec2_DivScalar`, `VectorPtr_PushBack`, `VectorLink_PushBack`, `Vector58_PushBack`, `Iterator_Advance`, `VectorLink_CopyConstruct` |
| rename | 0x14020c010, 0x1402016d0 | `FUN_*` -> `Editor_GenerateSlots`, `Editor_GenerateMesh` |
| plate | 0x14012f120 | `!ClickFunc`: signature (float in XMM3), `std::string` element name, structure (old text kept) |
| comments | 0x1401373ec, 0x140137498, 0x140137559 | `PRESELECT_HARD`: `Profile+0x164` = easy flag, `+0x165` = hard flag |
Not applied: 0x140265070 (repair-card check twin) and the `FUN_1401c4ee0` / `FUN_1401c0dc0` UI builders (not re-read), and everything in the workspace's economy, map-mode, radio, intel, planes and options pages beyond what is listed.

## Fourth batch: ClickFunc workspace, second pass (decompile re-read)
| kind | address | change |
|---|---|---|
| rename | 0x140265070 | `FUN_140265070` -> `Shipworks_ExitCheckRepairCards` |
| rename | 0x1401ecb10 | `FUN_1401ecb10` -> `BuildQuitMenu` (also the app exit path; Save button gated by `Profile+0x164`) |
| rename | 0x1401f7d50, 0x1401d3500 | `FUN_*` -> `BuildSkirmishSlotScreen`, `BuildCampaignSlotScreen` (the second by analogy) |
| rename | 0x140292ab0 | `FUN_140292ab0` -> `Profile_GetActive` |
| rename | 0x14028b400, 0x14028b3c0 | `FUN_*` -> `ProfileVec5c0_EmplaceBack`, `ProfileVec5c0_PushBack` |
| plate | 0x140252270 | `sellShipButton?`: modes, condition factor, shop transfer |
| comments (data) | 0x147fc6fca, 0x147fc6880, 0x143a11901, 0x147fc6f81, 0x143a15930 | what the globals are |
Rejected from the workspace: "`rep_1401f80a0` is a profile-delete helper" (it is an address inside `BuildSkirmishSlotScreen`; `rep_` names embed 1.151 addresses).

## Fifth batch: ds3-target report (cursor, aim, target box)
| kind | address | change |
|---|---|---|
| rename | 0x14018b310 | `FUN_14018b310` -> `Input_UpdateMouseAim` (relative aim offset, `ship+0xbb4`) |
| plate | 0x14029c5c0 | `afterBattleStars??` (kept name): target box, spawn box, aim arrow |
| comments | 0x14029fee2, 0x14029ff1b | `sign_aim` target box at `playerShip+0xb00`, fixed 62 px |
Not applied: the `FUN_14018af40` rename (stick-mode twin, not re-read), the tracer and marker functions (agent only).
