# Explosion damage, 1.151 vs 1.163: why missile hits reach deeper into a ship

Status: **the rule changes are confirmed on both versions at run time (static decompile + `hf_probe` logs, incl. a controlled run on each version).** How much deeper a blast reaches in play depends on the target's parts (see the controlled run); the earlier uncontrolled 'parts per blast' numbers were target-dependent and are superseded. Tags as in `../../README.md`: **[game]** seen in play or in logs · **[code]** read from the decompilation · **[guess]**.
Addresses are image base `0x140000000`. Origin: report that 1.163 "feels like more spalling": explosions penetrate deeper and damage components more easily.

## Short answer
Four things stack on every ship-attacking missile hit (the player's "R-5 ZENITH" = `MDL_MISSILE_01`: name from the language pack, warhead 200 in the 1.151 `OL.seria` and 300 in the 1.163 one [game, data files]):
1. **Warhead explosive power 200 (1.151) -> 300 (1.163)**. Blast radius = sqrt(explosive): 14.1 -> 17.3 (+22%). [game + code]
2. **First armored part hit by the blast chain: damage = budget x2 (1.151) -> x4 (1.163)**; 30 -> 60 for a budget-15 blast. With budget = 0.5 x `m_missile_ap`, that is exactly the missile's AP (30) in 1.151 and twice its AP (60) in 1.163. [game + code]
3. **Cost of an ordinary part along the chain: flat 5 (1.151) -> `maxHealth / 20` (1.163)**. Fragile modules (ammo 20 HP = 1, fuel 30 HP = 1.5, FSS 10 HP = 0.5, truss 25 HP = 1.25) barely slow the blast. [game + code]
   How much each of these is felt depends on the target: the cost change only lengthens chains through parts under 100 HP; the warhead change applies to every Zenith hit, the x4 only when the directly hit part is armored (see the controlled run).
4. Unchanged: armor still costs 10, parts with category bit `0x80` (trusses `MDL_FERMA*`) are free in both versions, gun-shell blasts have no chain at all.

Rocket warheads changed too (`ITEM_AMMO_220MM` 90 -> 180, `ITEM_AMMO_300MM` 90 -> 500): [ammo-1151-vs-1163.md](ammo-1151-vs-1163.md).

The 180mm gun shells are **identical** in both versions (explosive 82, 90 damage per part at the centre, no chain). So the extra spalling is a missile-hit effect; guns are not the cause. [game]

## How an explosion works (both versions) [code]
Routine: 1.151 `handleExplosionSFX?` `0x140028520`, 1.163 `FUN_140029b60` (called from `+0x240dd` / `+0x231ac` in the log). Explosion object fields (1.163; 1.151 is `0x10` lower from `+0x2b0` on, and the radius `+0x20c` is `+0x208`): `+0x148/+0x14c` position, `+0x2c0` (1.151 `+0x2b0`) float, `+0x2dc` `explosive`, `+0x2e0` `strength`, `+0x2e4` kind (int), `+0x20c` stored radius.
* **Two separate damage mechanisms run in the same call:**
  * **Area damage** (1.151 `0x14002dca0`, 1.163 `FUN_14002cdc0`, caller seen in the log at `+0x2de8b` / `+0x2d01a`): for every body whose edge is inside `R = sqrt(explosive)`: `damage = floor(5 * k * 2*sqrt(explosive) * (1 - d/R)^2)`, `k` = 1.0 for the player's own explosions and **0.66 for other owners** (`Get_Profile().player_owner` test; 1.163 also folds in a profile flag at `+0x165` [guess on its meaning]). Seen: 180mm shell (E 82, player's) 90 at the centre = 5 * 2*sqrt(82); Zenith E 200 -> 93, E 300 -> 114 (= 5 * 0.66 * 2*sqrt(E)), so the factor 0.66 applies to the Zenith blasts in both versions, **including the 4 Zenith hits the user fired in the controlled run** (114 at the centre in 1.163), while the user's own gun shells use 1.0 (90). Missiles therefore seem to carry no player-owner link [guess]; `k` is not a reliable who-fired signal. [code + game]
  * **The budget chain (the "spalling"):** `budget = min(1, field(+0x2c0) + 0.5) * strength(+0x2e0)`; **`strength` is the missile's `m_missile_ap` from `OL.seria`**: 30 for the Zenith (`MDL_MISSILE_01`) and the R-6 Nadir (`MDL_MISSILE_02`), none (0) for the R-9 Sprint (`MDL_MISSILE_03`), the cluster missile and every gun shell, so only AP-30 missiles chain. A Zenith has field 0, so budget 15. Gun shells have strength 0, so no chain. The routine walks the parts near the impact point nearest first and calls the Body damage slot on each with `damage = remaining budget`; then it lowers the budget:
    * armored part (`ShipPart.category & 2`): `-10` (both versions);
    * any other part, unless `category & 0x80`: **`-5` (1.151) / `-maxHealth/20` (1.163)**;
    * the **first** part of the chain, when armored, is hit for `budget x 2` (1.151, `0x1400290dc`/`0x14002913c` area) or `budget x 4` (1.163, `0x14002a7a8`...).
    It stops when the budget reaches zero.
* The damage slot (1.151 `0x14004f540`, vtable `+0x208`; 1.163 `0x1400519d0`, vtable `+0x210`) is unchanged apart from two flags added in 1.163 (armor-check bypass and "store damage instead of applying"); the `0.6` damage multiplier on the player's ships in normal difficulty is in both. [code]
* Other differences read in the area routine, not observed in play: 1.163 multiplies blast damage x5 on bodies with an aircraft-logic pointer (`+0xa20`, i.e. aircraft and missiles) and divides it by 5 on armored parts against a flagged low-explosive (<100) source. [code, not live-tested]

## Evidence from the logs [game]
`hf_probe` 2.4 (`hf_probe_build/logs/`): `probe_v2.3_1.163_blast_run.log.gz` (1.163, first battle, hooks active), `probe_v2.4_1.151_first_battle.log.gz`, `probe_v2.4_1.151_kormoran_180mm.log.gz`, `probe_v2.4_1.163_kormoran_180mm.log.gz`. One `BLAST` line per explosion (fields above) and one `DMG` line per damage call from the explosion code (part name, damage, HP/max HP, caller).

**A budget-15 chain, 1.163 (blast #280):** damage by part = 15, 15, 15, 13.5, 9.5, 5.5, 5.5, 5.5, 4.0, 4.0, 2.5. Fuel (30 HP) costs 1.5, legs (80 HP) cost 4, trusses cost 0: the sequence is exact.
**A budget-15 chain, 1.151 (blast #24):** engine 15 (costs 5), three trusses 10 (free), ammo box 10 (costs 5), then 5, 5. First armored part hit: 30 (1.151) vs 60 (1.163).

| Zenith-class blast (strength 30) | 1.151 | 1.163 |
|---|---|---|
| explosive power | 200 | 300 |
| damage per part at the centre (enemy, k 0.66) | 93 | 114 |
| first armored part, chain hit | 30 | 60 |

A replay of 12 logged 1.163 chains under the 1.151 rule gave 41 vs 56 parts and 576 vs 843 damage; it assumes the same parts in the same order and is an upper bound. The uncontrolled battles (different fights, different targets) gave 2.6 vs 2.7 chain parts and 29.5 vs 38.6 chain damage per budget-15 blast, and the Kormoran runs 4.0 vs 9.3 parts per blast; **the controlled run below does not reproduce a parts-per-blast difference, so do not use those figures.**

**Gun shells:** 180mm HE (explosive 82, strength 0): 90 max damage per part, no chain, in both versions (26 blasts in 1.151, 71 in 1.163). [game]

## Controlled run (same ship, same order of events on each version) [game]
Ship `Lightning_Sarmat` (Lightning with 2x180mm), battle 1 against weak ships with the cannons, battle 2 with 4 Zenith hits. Logs: `probe_v2.4_1.151_controlled_sarmat_zenith.log.gz`, `probe_v2.4_1.163_controlled_sarmat_zenith.log.gz`.

| | 1.151 | 1.163 |
|---|---|---|
| 180mm shell blasts | 4, E 82, str 0, max 90 per part, 3-6 area parts, no chain | 6, E 82, str 0, max 90 per part, 4-12 area parts, no chain |
| Zenith blasts on ships | 4 (#18-#21): E 200, str 30, max **93** per part | 4 (#33-#36): E 300, str 30, max **114** per part |
| Zenith area parts per blast | 10, 9, 14, 14 | 21, 12, 3, 7 |
| Zenith chain parts per blast | 5, 3, 3, 6 | 11, 3, 3, 2 |

Every chain matches the rule of its version exactly:
* 1.151 #21: craft 15 (first target), deck 15 (costs 5), truss 10 (free), cannon mount 10 (costs 5), truss 5 (free), quarters 5. #20: truss 15, engine 15 (costs 5), armor 10 (costs 10 -> 0). Flat 5 everywhere, armor 10, trusses free.
* 1.163 #33: deck 15 (costs 5), trusses 10 (free), generator 10 (80 HP, costs 4), truss 6, FSS 6 (costs 0.5), trusses 5.5, ammo box 5.5 (costs 1), leg 4.5 (costs 4), fuel tank 0.5 (400 HP). 11 parts. Under the 1.151 rule this chain would have ended after 6 parts with 55 total damage instead of 78.5.
* 1.163 #36: leg 15 (costs 4), armor 11 (-10). Hardpoint `MDL_HARD1X1_01` seems free (budget stays 15 into the next part in #34) [guess].

What the controlled run shows, honestly:
* **Confirmed:** per-part blast damage x1.22 (93 -> 114; predicted sqrt(300/200) = 1.2247); `maxHP/20` cost vs flat 5; trusses free in both; 180mm shells identical.
* **Design-dependent:** the cost change only matters when the chain meets parts with less than 100 HP (ammo, fuel, FSS, generator, legs, quarters, small armor). Most chain parts in the 1.151 run were 100-HP parts, where `maxHP/20` = 5 = the old flat cost, so those chains are the same under both rules. Only #33 (11 parts) shows the big effect.
* **Not exercised:** the armor-hit x2 -> x4 change (no armored *first* part in either controlled run; it was seen earlier in the uncontrolled battles as 30 vs 60).
* **Not shown:** more parts hit per blast. Area-part counts are about the same (11.75 vs 10.75 average); with 22% more radius I expected more, but the targets differed (no distance is logged, so the radius effect itself is unverified) [open].

## Live-test recipe (controlled version)
1. Same ship (e.g. Kormoran), same fight setup, same target ship with an armor plate in front of soft modules.
2. Install `hf_probe` 2.4 (`Modloader/mods`), keep only `hook_blast` on in `Modloader/config/probe.json`. The probe starts on `Steam 1.151` and `Steam 1.163`; on 1.151 only the blast hooks run.
3. Take one Zenith hit on the same armor spot on each version. Compare the `BLAST` line (explosive, strength) and the `DMG` chain (first line = armor hit, then the costed parts).
4. Expected: 1.151 `explosive 200` / first armor hit 30 / flat 5 per part; 1.163 `explosive 300` / 60 / `maxHP/20`.
5. Copy `Libraries/OL.seria` and `parts.seria` while the 1.151 branch is installed and diff the missile stats against 1.163 (see open points).

## A mod that restores 1.151 behaviour (not written) [code]
Three byte patches in 1.163 would do it: the multiplier `4.0` at the first-armor call, the `maxHP/20` cost (`MOVSS XMM0,[RBX+0x2cc]; DIVSS XMM0,XMM9` at `0x14002ab1d`) replaced by a constant 5, and the Zenith `m_missile_explosive` in `OL.seria` (a data change, no code). Sites: loop unarmored cost `0x14002ab1d`..`0x14002ab2a`; armored `-10` at `0x14002a9ef`/`0x14002aa0c` (`ADDSS XMM11,XMM7`).

## Data files (OL.seria diff, 1.151 vs 1.163) [game]
The 1.151 `Libraries/OL.seria` was inspected while the Steam folder held 1.151 (not kept; see [../formats.md](../formats.md) on copying per version). Of the missiles, only `MDL_MISSILE_01` (Zenith) changed its warhead: `m_missile_explosive` 200 -> 300. Nadir 400, Sprint 100, cluster 200 are the same in both; `m_missile_ap` (30 on Zenith and Nadir) is the same in both. In 1.163 the nuke conversions (`MDL_NUKE_*_CONV`) went `m_missile_explosive` 500 -> 700 and gained `m_missile_ap` 100 (so they now have a chain, budget 50 at field 0) [not seen in a fight]. Zenith `m_mdl_sectors_threshold` 0.5 -> 0.3 and new `m_mdl_sectors_shift` 1. Part HP in `parts.seria` is unchanged.

## Open
* The x5 aircraft/missile multiplier and the /5 armor reduction in the area routine, and the `+0x165` profile flag in the 0.66 factor, were read but not exercised.
* The blast radius (+22% predicted) is not measured: the `DMG` lines do not log distance.
* A 1.163 mod reading 1.151 values would need the matching `m_missile_explosive` (data) and the 2x/flat-5 behaviour (code); not decided whether it is worth shipping.
