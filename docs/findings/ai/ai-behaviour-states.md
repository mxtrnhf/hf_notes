# Tactical AI behaviour states and target choice (1.163), ghidra-miner, 2026-10-21
Work-list item 5 ([../../data/ghidra-miner-worklist-2026-10-20.md](../../data/ghidra-miner-worklist-2026-10-20.md)). Builds on [ai-tick-patch-sites.md](ai-tick-patch-sites.md) (stand-off, orbit, ammo, launches) and [../battle-ally.md](../battle-ally.md) (roles, retreat). Tags: [code] decompile/disassembly read today, [prior] earlier notes, [guess].

## The three selectors on a creature
| field | meaning | values seen |
|---|---|---|
| `+0xbd4` (byte) | AI flag | 1 = AI-run (constructor default), 0 = player-controlled (`Profile_SetControlledShip`) |
| `+0xbd8` (int) | kind | **1** ship (constructor default); **2** ground-defence creature (`createGroundDefenseCreatures` 0x140004fff): `aiShipDriver` returns at once, no AI; **3** a launched missile / aircraft body (`FireMissile??` 0x140005a93): moves toward its target point and waits if another AI creature is within 100 |
| `+0xbdc` (int) | behaviour state, switched by `aiShipDriver` 0x1400739c0 | see next table |
| `+0xd70` (int) | role: 1 = flagship / controlled, 2 = bombing role (strike runs), 0 = normal | [prior] |

## `+0xbdc` state table, from `aiShipDriver` 0x1400739c0 [code]
| state | what the driver does | set by |
|---|---|---|
| 0 | idle / hold: points the move target at the root part's position (`+0x20c`) and runs `AiShip_SteerController` 0x14006cb30 (follow/hold, **no weapon controller**) | re-derive: no target links |
| 1 | **engage**: `AiShipTick` 0x140062f90 (steering, launches, weapon controller) | re-derive: a ship target `+0xb00` or a missile/aircraft target `+0xb18` exists |
| 2 | **engage, fixed**: same `AiShipTick`, but the driver does not re-derive the state | `FUN_140078b40` when the target choice leaves no ship target (`+0xb00 == 0`); `AiShipTick` twice (0x1400638a0, 0x1400638e9) inside its steering when it switches to its second steering variant [guess on the condition]; hf_ally's retreat (mode 2 + state 2) |
| 3 | **move to the stored point and wait**: returns at once if the point is (0,0); if another AI creature is within 100 units it does nothing this tick, otherwise `AiShip_SteerController` | no immediate-constant writer; set through registers by the battle manager (`FUN_1402cb6a0`, `FUN_1402ce060`) [guess: arrival / formation] |
| 4 | **go to the arena edge**: move target = the creature's own x (`+0x1840`) and y = `_DAT_143a1c374 - 100` (the arena edge), then `AiShip_SteerController` | `mainDialogWithChoices` 0x1400b06f2 and `FUN_1400b1440` 0x1400b5194 (dialog / cinematic events) [guess: "ship leaves"] |
| 5 | driver does nothing (returns 1) | `MakeGlobal` wrapper 0x140266036 and `somethingHireShips?` 0x140266794: ships created for the hire / port screens [guess: parked] |
| 6 | removed / dead: `ShipStatusCheck` and the AI list skip it ([ship-removal-and-battle-result.md](../ship-removal-and-battle-result.md)) | `FUN_14020ef30` extraction path, kill path |
| 7 | **alarm / no valid targets**: plays `alarm_01` (louder with mass, `+0x15b8 / 1e7`), sets an 8-slot array to 1, then behaves like state 0 (hold) | `aiShipDriver` itself, see below |

**Re-derive step** (every tick unless the state is 2 or 4..7, or the state is 6): `ShipStatusCheck`; return if the creature's own `+0x48 == 0`; then, if the prize-safe byte `+0xc19` is clear or the global `DAT_147fc75b0` is 0, call the target choice `FUN_140078b40`, relink `+0xb10` (a target position / escadra link), and set state 1 if either target link `+0xb00` / `+0xb18` is set, else 0. If the prize-safe mode is on (`+0xc19` set and `DAT_147fc75b0 != 0`), the driver first scans the enemy side vector `0x143faa5f0..` for any ship with thrust (`+0x1604 != 0`) that is not itself prize-safe; if there is one it re-picks, **if there is none it sets state 7** (all remaining enemies are disabled prizes: the AI stops). The mode `+0xbd8 == 2` returns early, `== 3` takes the "move and wait" path.

## Target choice `FUN_140078b40` [code, read today]
Runs from the driver; the choice is re-rolled every **3.0 s** (`+0xb28`, reset to 3.0 after a pick, or at once if there is no ship target `+0xb00`). Result: link `+0xaf8` (node at `+0xb00` = the target creature or part).
* **Role 2 (bombing)**: candidates are foes (`FUN_140220120` side test) found in the allowance map `0x147fc7550`; ships on the same side with role 2 vote (`+0xb00` of their target) and the ship picks the most-voted target (the group attacks one target).
* **Normal**: 1) build the candidate list from the ship's **sensor list** `+0xb38` (parts it currently detects): entry alive (`+0x48 != 0`), master not a class-7 node, the root part's flag `0x40` not active, root name not `MDL_EVAC`; 2) if that list is empty, fall back to the **global creature list** `0x143faa5d8`: alive, same filters, not itself, side product `self+0xad4 * other+0xad4 <= 0` (foe, **neutral side 0 counts as a foe for everyone**), and (`FUN_1402213e0()` is true, i.e. `DAT_147fc6fe0` with zoom > 3, **or** both creatures have byte `+0xb78` set).
* **Score**: `20000 / distance` (`FUN_14020fce0`), minus 20 if the candidate has no weapons (`+0x15e8 + +0x15ec == 0`); sort, take the best; scores are then zeroed. The prize flag `+0xc19` is never read here (hf_ally re-links around it).
* After the pick: if the ship-target node `+0xb00` is still null the state is forced to 2; if the target changed, `+0xc78` (ammo re-roll timer) is zeroed and `AiRerollAmmoFlags` 0x140079810 runs.

## Circling, backing off, retreat [prior + code]
* **Circling**: perpendicular orbit term with weight `1 - |radial|` around the target at the stand-off distance; **backing off**: radial weight negative inside the stand-off ([ai-tick-patch-sites.md](ai-tick-patch-sites.md) section 2).
* **Retreat to the arena edge**: state 4 (edge point) and the roles/states used by hf_ally (mode 2 + state 2) with the manager extracting ships that reach the edge ([../battle-ally.md](../battle-ally.md)). No AI code retreats on its own because of damage: loss is judged by `ShipStatusCheck` (removal), not by a flee behaviour [code: none found in the driver].

## Open
* Exact meaning of states 3 and 5 and the condition under which `AiShipTick` switches to state 2; which events set 4.
* The sensor list `+0xb38`: who fills it and with what range / type rules (the candidate source for most picks).
* `+0xb78` (the byte that opens the fallback list) and `DAT_147fc75b0` (prize-safe mode global).
