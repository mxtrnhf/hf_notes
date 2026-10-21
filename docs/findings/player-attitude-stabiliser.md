# Does the player ship get an automatic attitude stabiliser? (v1.163), ghidra-miner, 2026-10-21

Question from the simulator session: the user heard that ships "auto stabilize" and that `m_mdl_at` (Stats `+0x100`) is involved; the sim data (sim_runs14, Lightning_Stock vs Lightning_nostatic) show an angle-dependent hull torque residual. Tags: [code] read in the 1.163 decompile/disassembly, [inference], [open].

## Where the fields are written and read [code]
| field | writer | readers |
|---|---|---|
| Stats `+0x100` (`m_mdl_at`) | data (`OL.seria`) | only `Creature_AccumulatePartStats` (0x140071380): for each live engine part whose command list contains 0x66 (bank 1) it adds `+0x100` to creature `+0x1684` (0x140071614/1c); for 0x67 (bank 2) to `+0x1688` (0x1400716f6/fe). **Static engines count too**: there is no swivel test around the add. |
| creature `+0x1684` / `+0x1688` | the same function; zeroed in `Creature_ResetStatAccumulators` (0x140061fbf) | `CalculateStats` 0x140080c02/0x140080c0a, plus display code (`showShipData?` 0x1400765f7, `variousHUDDisplays?` 0x14023172f/0x140231770, 0x1402b5a84/aaf take their address only) |
| creature `+0x180c` (turn gate) | `CalculateStats` 0x140080c24: `2 * min(+0x1684, +0x1688)` | **only** `AiShipTick` 0x140064fe7 and `AiShip_SteerController` 0x14006d0f2 (full program instruction search, 4 hits in total) |

## Is it applied to the player ship? [code + one open point]
* Both readers are reached only through `aiShipDriver` 0x1400739c0, whose only caller is `SomethingAITask` 0x140011180, which walks the AI list `creatureDLL_AI_StdVec_` (0x143faa608).
* A creature is put on that list by `Creature_RegisterInWorldLists` 0x14006bf60 only if `creature+0xbd4 != 0`. `+0xbd4` is the AI flag: the Creature constructor sets it to 1 (0x140072d4e); `Profile_SetControlledShip` 0x1402a7e30 sets the player-controlled ship to 0 (and demotes the previous one to 1). `ShipStatusCheck` and `Profile_IsPlayerShip` also treat `+0xbd4 == 0` as the player.
* The player's input path (`0x14018dbf0`, called from `!FrameFunc` 0x1401a8970) never touches `+0x180c`, `+0x1684`, `+0x1688` (no hit in the instruction search outside the table above).
* So by code the attitude-hold term (`e = wrap(0 - angle)`, `k = e * I / 20` added to bank 1 and subtracted from bank 2, gate `+0x180c / I > 0.02`; formula in [ai-tick-patch-sites.md](ai/ai-tick-patch-sites.md)) **does not run for the player ship**.
* **Open:** list membership is decided when the creature is registered. A ship registered while `+0xbd4 == 1` and flipped to 0 later by `Profile_SetControlledShip` is not removed from the AI list by anything I read; `SomethingAITask` also calls a per-creature virtual at vtable `+0x78` before `aiShipDriver`; **correction 2026-10-21: I earlier guessed that this was 0x140078300; that function (now `Creature_DebugDrawOverlay`) is a debug line-drawing routine and is NOT the `+0x78` predicate**, so the predicate was not identified and its return value for the player is unknown. **Decisive live check:** log the player's `+0xbd4` and whether `aiShipDriver` (0x1400739c0) is entered with the player's pointer (hf_ally can hook it).

## Statics [code]
* In the AI controller the term only changes the bank vectors (`bank1 += k*h`, `bank2 -= k*h`, `h = (sin a, -cos a)`), sent as angle + strength commands to every part with command 0x66/0x67. A static engine cannot swivel, so the vector's angle only changes its cos gate; its `+0x100` still counts in the gate (above).

## A constant opposing torque on the Frame? [inference, not a Stats/AI term]
* I found no per-frame stabiliser, damping or "assist" for the player ship in the readers above.
* Box2D angular damping on every body is 0.05 (`Body_CreateB2Body` 0x14004b330, applied as `w / (1 + dt * 0.05)`): proportional to the spin, not flat.
* **A better candidate for an angle-dependent residual is the antenna welds.** The antenna links are dynamic bodies with tiny mass, welded to the hull with a joint that scales the linear inverse mass by 6.0 but not the inverse inertia ([box2d-struct-layouts.md](box2d-struct-layouts.md)), so the joint does not conserve angular momentum, and the links hang in gravity (a hull-angle-dependent load). Test: rotate the same ship with and without antenna parts (`MDL_ANTENNA_01`), and compare with sim_runs14. [open]

## Not done
* The vtable `+0x78` function above, the exact place where the player's creature is added to the world lists, and `Stats+0x100` readers in the editor/UI (only the accumulator reads it in the game code).
