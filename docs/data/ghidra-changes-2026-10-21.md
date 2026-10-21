# Ghidra 1.163 changes made by ghidra-miner on 2026-10-21 (program `/Highfleet.exe.unpacked.exe v1.163`)
Source of every entry: decompile / disassembly read in this session; details in [findings/box2d-struct-layouts.md](../findings/box2d-struct-layouts.md), [findings/static-engine-force-path.md](../findings/static-engine-force-path.md), [findings/player-attitude-stabiliser.md](../findings/player-attitude-stabiliser.md). Nothing else in the program was touched; 1.151 was not opened for writing. Style warnings from the tool (PascalCase) are ignored: the program already uses `b2*_*` and `Creature_*` names.

## Function renames (auto-named functions only; no deliberate name overwritten)
| address | old name | new name |
|---|---|---|
| 0x1401c3bd0 | rep_140047e60_New | Hull_CreateAntennaChain |
| 0x140319c50 | FUN_140319c50 | b2Body_Ctor |
| 0x140320b30 | FUN_140320b30 | b2Fixture_Create |
| 0x140319f80 | FUN_140319f80 | b2Body_ResetMassData |
| 0x140324750 | FUN_140324750 | b2Joint_Ctor |
| 0x1403247c0 | FUN_1403247c0 | b2Joint_Create |
| 0x14031e2e0 | rep_wrap_0_FUN_1402f9760 | b2WeldJoint_Ctor |
| 0x14031e590 | FUN_14031e590 | b2WeldJoint_InitVelocityConstraints |
| 0x14031f030 | FUN_14031f030 | b2WeldJoint_SolveVelocityConstraints |
| 0x14031be80 | rep_wrap_0_FUN_1402f9760 | b2RevoluteJoint_Ctor |
| 0x14031d470 | rep_wrap_0_FUN_1402f9760 | b2DistanceJoint_Ctor |
| 0x14031dc80 | FUN_14031dc80 | b2DistanceJointDef_Initialize |
| 0x140321f60 | FUN_140321f60 | b2ContactManager_Collide |
| 0x14006bf60 | FUN_14006bf60 | Creature_RegisterInWorldLists |
| 0x1402a7e30 | FUN_1402a7e30 | Profile_SetControlledShip |

## Functions created (were undefined)
| address | name | note |
|---|---|---|
| 0x140078300 | Creature_DebugDrawOverlay | debug line-drawing routine, gated on the AI flag `+0xbd4`; not the vtable `+0x78` predicate |
| 0x140019be0 | Body_AddTorque | Body vtable `+0x1a0`; adds `torque * 0.05^5 * invI` to the b2 angular velocity immediately |

## Plate comments (set)
0x1401c3bd0 (antenna chain: 4 dynamic density-1e-06 links, weld kind arg 2), 0x14031e590 and 0x14031f030 (weld: mass scale at `+0x8c` = 6.0 applied to linear invMass only, freq 0 = rigid), 0x14031e2e0 (weld ctor field map), 0x14006bf60 (creature joins the AI list only if `+0xbd4 != 0`), 0x140019be0 (AddTorque semantics and callers).

## End-of-line comments (set)
0x140080c24 (`+0x180c` turn gate = 2 * min(`+0x1684`, `+0x1688`)), 0x14006d0f2 and 0x140064fe7 (gate test in the AI steering code).

## Second batch, 2026-10-21 (after the first check-in)
| kind | address | change |
|---|---|---|
| created | 0x140019be0 | `Body_AddTorque` (was undefined) + plate comment (already checked in) |
| rename | 0x140048720 | `FUN_140048720` -> `GetMdlAt` (Stats +0x100) (already checked in) |
| comments | 0x140035652, 0x1400356a2, 0x14003573d, 0x140035757, 0x1400357cb | hull-stabiliser case (creatureLogic logic id 200) (already checked in) |
| rename | 0x140078b40 | `FUN_140078b40` -> `AiShip_ChooseTarget`, plate comment (target choice and scoring) |
| plate | 0x1400739c0 | `aiShipDriver`: kind `+0xbd8`, state `+0xbdc` table, re-derive step |
| plate | 0x1402cc260 | `battleManagerTick`: battle result codes -1 / 1 / 2 |
| plate | 0x140028360 | `Engine_ApplyThrustForce`: gates, +0xbc4 x0.01, f(X), bank sums (replaces the earlier plate text, which is included) |
| plate | 0x14007eb50 | `CreatureUpdate`: dispatch of creatureLogic, `+0xbc4` spool ramp, history record |
| comments | 0x14007910f, 0x140073c64, 0x1400638a0, 0x140266036, 0x140004fff, 0x140005a93 | state / kind writers (state 2, 7, 2, 5; kind 2, 3) |
