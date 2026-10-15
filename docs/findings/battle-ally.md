# Battle ally: an AI-run, player-side ship that fights beside you

Status: **static reading of 1.163 plus a log-only prototype plan (`hf_ally`). Nothing here has been run in game yet.** Tags: legend in `../../README.md`. Addresses are 1.163 (image base `0x140000000`) unless stated.
Goal: when a battle starts, bring a second ship onto the player's side. The player flies one ship; the other is run by the stock AI (it "copies the enemy AI" for now) and attacks the same enemies.

## Address warning (a mistake in an earlier summary)
Ghidra labels of the form `rep_<hex>_Name` carry the **1.151** address in the label, not the 1.163 one. Example: the 1.163 function at `0x1402672c0` is labelled `rep_1402454a0_New`; the correct 1.163 address is `0x1402672c0`. Always take call targets from the `CALL` operand in the disassembly, never from the label. (Same for `rep_140205f80_Creature__CalculateStats` = the function at `0x140223830`, `rep_14006fe20_shipKill_` = `0x1400739c0`, and so on.)

## What decides "AI-run" [code]
* **Add-to-level hook of a Creature: `FUN_14006bf60(creature, removing)`** (`0x14006bf60`, reached through the Creature vtable at `0x14807ac4c`, no direct callers). With `removing == 0` it:
  * always appends the creature to the **global creature list** `0x143faa5d8` (end pointer `loopVar10e0_`, 0x18-byte `Link` entries, pointer at +8);
  * appends it to the **AI vector** `0x143faa608` (end `0x143faa610`) **only if the byte `creature+0xbd4` is non-zero**;
  * puts the raw pointer into a **side bucket** chosen by the sign of the float `creature+0xad4`: negative -> vector `0x143faa5f0..0x143faa5f8`, zero -> `0x143faa650..0x143faa658`, positive -> `0x143faa638..0x143faa640` (skipped if state `+0xbdc == 6`).
* **`SomethingAITask`** (`0x1400111b0`) walks the AI vector, calls `vtbl+0x78` (is-active) and then the per-ship driver `0x1400739c0` for each entry. So a creature is AI-run when `+0xbd4 != 0` when it is added; side is not part of this test.
* **Per-ship driver `0x1400739c0`** switches on the state int `+0xbdc`: states 1 and 2 call the AI tick `FUN_140062f90` (after `FUN_140079b20(ship, 1)` when the float `+0xbc4 >= 0.5` and mode `+0xb48 != 1`); 0 and 7 call `FUN_14006cb30` (follow/hold, no shooting); 4 is a variant of the same. For states other than 4, 5 and 7 (and 6) the driver first re-derives the state: 0 if both target links (`+0xb00`, `+0xb18`) are empty, otherwise 1.
* **Target choice `FUN_140078b40`**: candidates come from the global creature list; a candidate is a foe when `side_self * side_other <= 0` (a **neutral side 0 counts as foe for everyone**), evac pods excluded, and it is ranked by distance (`-20` if it has no weapons). The choice is stored in the link `+0xaf8`/`+0xb00` and re-rolled about every 3.0 s (`+0xb28`). `FUN_140220170`/`FUN_140220120` are the same-side tests.
  * Consequence [code]: a ship with a **positive** side never targets the player's side and does target negative-side ships, and enemies pick it as a foe (product < 0). Nothing here needs the ally to be special.
* **Control** of the player's ship is separate: a smart-ref global `0x143a1c260` holds the controlled creature (written by `SetLink`). In the Missile scenario it is written only for the first spawned ship whose float `+0xad4 > 0` (`0x1402d4c4f`..`0x1402d4c77`: `CALL 0x1402a7e20(profile, ship)` then `SetLink(0x143a1c260, result)`).

## Spawn recipe seen in the Missile scenario [code]
`FUN_1402d45c0` (SCR_MISSILE state 1, called at `0x1402c4dfc`) is the only complete example read so far of "spawn up to four ships from a sorted list, one is controlled, the rest are not":
1. The defender fleet's ships are sorted; for `i < 4` it pops the next ship (a `Property` that links a ship **template** node), computes a position from the level bounds (`lvlHighXHighY`/`lvlLowXLowY`, staggered by `i`) and calls **`0x1402672c0(template, &pos, 0, 0)`** (call at `0x1402d4ba3`). That function copies the template's parts into a fresh Creature, runs `CalculateStats`, the sub-initialisers, resets ammo from the stats record, plays an optional radio sound and returns the Creature; the template node is killed through `vtbl+0x48` (the template is *consumed*, so the parts end up in the new ship).
2. Mode split on the flag held in `R13B` (derived at the top from a field of the A-list entry):
   * flag set: `FUN_140079b20(ship, 1)`, `+0xbc4 = 1.0`;
   * flag clear: `FUN_140079b20(ship, 3)`, `FUN_14022c010(ship, 1)`, `0x140223830(ship, 1, 0)` (recalculate stats), `+0xbc4 = 0.0`.
3. `+0xc98 = i`, the ship is appended to the roster vector `0x147fc7590` (`end 0x147fc7598`), and for `i == 0` the controlled link is set (above).
4. The state `+0xbdc == 7` is reset to 0 in teardown `FUN_1402d4f20`.
What is **not** yet found: where `+0xad4` (side) and `+0xbd4` (AI flag) are written for these ships. They may come from the template (saved ship data) or from `0x1402672c0`/its callees. The log-only prototype reads both on every add, which settles it.

## Teardown (the return path) [code, partly]
`FUN_1402d4f20` (end of the scenario state) walks the global creature list: for every creature with `+0x48 != 0` it resets state 7 to 0 and calls `MakeGlobal` (`0x1400609f0`) and `APP_MoveVolume` (`0x1401f3c10`), then positions fleets from the A-list and frees the roster vectors. It was read for the Missile scenario; **whether Combat's teardown returns every roster creature to its fleet is unverified**, and it is the most expensive way for this idea to fail (the second ship could be lost or left dangling). Test on a backup save.

## What is still unknown
1. **Combat's own spawn site.** `0x1402672c0` has 22 call sites (listed in the Ghidra xrefs), including three inside `SomethingWithLevelSerias` (`0x1402b3834`, `0x1402b3a10`, `0x1402c2368`), `FUN_1402c9cb0`, `FUN_1402d1a60`, `FUN_1402d7110`, `0x1402be0f4`, `0x1402c06cf`. The one that deploys the player's ships for `Combat.seria` is not identified. `FUN_1402ce060` runs in a state that then loads another level; it looks like end-of-battle, not setup.
2. Where the player's chosen ship is written in Combat; whether vanilla Combat ever puts a second player-side creature in play (the Preselect screen suggests one ship).
3. How to get a ship **template** for the ally: from the player's escadra (a second ship of the fleet) or from a `Ships/*.seria` blueprint. The second needs the shipworks/`LoadSeriaFile` (`0x140225930`) path; not traced.
4. Battle-end bookkeeping: the positive-side bucket `0x143faa638` may count toward win/lose.
5. Whether the sort order, `+0xd70` (mode 2 target variant) and `+0xc78` need setting for an ally.

## Prototype plan (`hf_ally`, standalone Rust crate; port to a fork branch once the sites are confirmed)
Standalone because a failed patch in QoL makes `init` return false and takes every QoL feature down with it ([../hooks.md](../hooks.md)). The crate follows the QoL rules: JSON config section, off-by-default behaviour, Steam 1.163 guard, byte pre-check before preparing a patch, one owner per site.
* **Milestone (a), log-only (this file's first prototype):** entry hook on `0x14006bf60`, 10 stolen bytes `48 89 5c 24 08 57 48 83 ec 40`. On every add and remove it logs the creature pointer, the side float, the AI flag, `+0xbc4`, `+0xbdc`, `+0xb48`, `+0xc98`, whether it is the controlled creature, and the sizes of the global, AI and side-bucket vectors. Run one Combat and one Missile battle. Answers unknowns 1, 2 and the `+0xad4`/`+0xbd4` question without changing behaviour.
* **Milestone (b):** with the data from (a), spawn a second ship from the fleet through `0x1402672c0` using the Missile recipe's non-controlled branch and side = positive, AI flag set, added when the player's ship appears.
* **Milestone (c):** confirm the ship returns to the fleet after the battle (teardown), in a backup save.

## Test recipe for milestone (a)
Copy `hf_ally_v0.1.0.dll` into `<game dir>/Modloader/mods/`, start a skirmish or a campaign battle, play to the end, then read `Modloader/logs/*.log` for lines starting `ALLY`. The expected result is a list of `ADD` lines for the player's ship and each enemy with their sides.
