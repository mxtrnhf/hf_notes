# Explosion damage, 1.151 vs 1.163: why missile hits reach deeper into a ship

Status: **cause found and confirmed on both versions at run time (static decompile + matched `hf_probe` logs).** The size of the effect is measured on two uncontrolled battles per version, so the percentages below are indicative. Tags as in `../../README.md`: **[game]** seen in play or in logs · **[code]** read from the decompilation · **[guess]**.
Addresses are image base `0x140000000`. Origin: report that 1.163 "feels like more spalling": explosions penetrate deeper and damage components more easily.

## Short answer
Four things stack on every ship-attacking missile hit (the player's "Zenith"; part `MDL_MISSILE_01` is the 300 warhead in 1.163 `OL.seria`, the Zenith = `MDL_MISSILE_01` link is [guess]):
1. **Warhead explosive power 200 (1.151) -> 300 (1.163)**. Blast radius = sqrt(explosive): 14.1 -> 17.3 (+22%). [game + code]
2. **First armored part hit by the blast chain: damage = budget x2 (1.151) -> x4 (1.163)**; 30 -> 60 for a budget-15 blast. [game + code]
3. **Cost of an ordinary part along the chain: flat 5 (1.151) -> `maxHealth / 20` (1.163)**. Fragile modules (ammo 20 HP = 1, fuel 30 HP = 1.5, FSS 10 HP = 0.5, truss 25 HP = 1.25) barely slow the blast. [game + code]
4. Unchanged: armor still costs 10, parts with category bit `0x80` (trusses `MDL_FERMA*`) are free in both versions, gun-shell blasts have no chain at all.

The 180mm gun shells are **identical** in both versions (explosive 82, 90 damage per part at the centre, no chain). So the extra spalling is a missile-hit effect; guns are not the cause. [game]

## How an explosion works (both versions) [code]
Routine: 1.151 `handleExplosionSFX?` `0x140028520`, 1.163 `FUN_140029b60` (called from `+0x240dd` / `+0x231ac` in the log). Explosion object fields (1.163; 1.151 is `0x10` lower from `+0x2b0` on, and the radius `+0x20c` is `+0x208`): `+0x148/+0x14c` position, `+0x2c0` (1.151 `+0x2b0`) float, `+0x2dc` `explosive`, `+0x2e0` `strength`, `+0x2e4` kind (int), `+0x20c` stored radius.
* **Two separate damage mechanisms run in the same call:**
  * **Area damage** (1.151 `0x14002dca0`, 1.163 `FUN_14002cdc0`, caller seen in the log at `+0x2de8b` / `+0x2d01a`): for every body whose edge is inside `R = sqrt(explosive)`: `damage = floor(5 * k * 2*sqrt(explosive) * (1 - d/R)^2)`, `k` = 1.0 for the player's own explosions and **0.66 for other owners** (`Get_Profile().player_owner` test; 1.163 also folds in a profile flag at `+0x165` [guess on its meaning]). Seen: 180mm shell (E 82, player's) 90 at the centre = 5 * 2*sqrt(82); Zenith E 200 -> 93, E 300 -> 114 (= 5 * 0.66 * 2*sqrt(E)), so the factor 0.66 applies to Zenith blasts in both versions, **including the player's own missiles** (controlled 1.163 run: own Zenith hit = 114 at the centre; own 300mm rocket E 500 = 147 = 5 * 0.66 * 2*sqrt(500)), while own gun shells use 1.0. Missiles/rockets therefore seem to carry no player-owner link in that test [guess]; the `k` is not a reliable who-fired signal. [code + game]
  * **The budget chain (the "spalling"):** `budget = min(1, field(+0x2c0) + 0.5) * strength(+0x2e0)`; a Zenith has strength 30 and field 0, so budget 15. Gun shells have strength 0, so no chain. The routine walks the parts near the impact point nearest first and calls the Body damage slot on each with `damage = remaining budget`; then it lowers the budget:
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
| first battles (not the same fight): chain parts per budget-15 blast, 24 vs 25 blasts | 2.6 | 2.7 |
| first battles: chain damage per budget-15 blast | 29.5 | 38.6 |
| Kormoran runs: parts hit per ship-hitting Zenith blast (area + chain), 7 vs 10 blasts | 4.0 | 9.3 |
| Kormoran runs: area damage per hitting blast | 248 | 359 |

The chain length is short in both versions because few parts are in range; the difference shows most on armor hits and on chains that pass through low-HP modules. The 15-23 part blasts in the 1.163 Kormoran run probably include non-ship bodies [guess]. A replay of 12 logged 1.163 chains under the 1.151 rule gave 41 vs 56 parts and 576 vs 843 damage, but it assumes the same parts in the same order, so treat it as an upper bound.

**Gun shells:** 180mm HE (explosive 82, strength 0): 90 max damage per part, no chain, in both versions (26 blasts in 1.151, 71 in 1.163). [game]

## Live-test recipe (controlled version)
1. Same ship (e.g. Kormoran), same fight setup, same target ship with an armor plate in front of soft modules.
2. Install `hf_probe` 2.4 (`Modloader/mods`), keep only `hook_blast` on in `Modloader/config/probe.json`. The probe starts on `Steam 1.151` and `Steam 1.163`; on 1.151 only the blast hooks run.
3. Take one Zenith hit on the same armor spot on each version. Compare the `BLAST` line (explosive, strength) and the `DMG` chain (first line = armor hit, then the costed parts).
4. Expected: 1.151 `explosive 200` / first armor hit 30 / flat 5 per part; 1.163 `explosive 300` / 60 / `maxHP/20`.
5. Copy `Libraries/OL.seria` and `parts.seria` while the 1.151 branch is installed and diff the missile stats against 1.163 (see open points).

## A mod that restores 1.151 behaviour (not written) [code]
Three byte patches in 1.163 would do it: the multiplier `4.0` at the first-armor call, the `maxHP/20` cost (`MOVSS XMM0,[RBX+0x2cc]; DIVSS XMM0,XMM9` at `0x14002ab1d`) replaced by a constant 5, and the Zenith `m_missile_explosive` in `OL.seria` (a data change, no code). Sites: loop unarmored cost `0x14002ab1d`..`0x14002ab2a`; armored `-10` at `0x14002a9ef`/`0x14002aa0c` (`ADDSS XMM11,XMM7`).

## Open
* Confirm the 1.151 Zenith warhead (200) from the 1.151 `OL.seria` (we only saw it in blast logs; the 1.163 data file says `MDL_MISSILE_01` 300, `MDL_MISSILE_CLUSTER_SFW_01` 200, `MDL_MISSILE_02` 400, `MDL_MISSILE_03` 100).
* Which part name the game's UI "Zenith" is. [guess] `MDL_MISSILE_01`.
* The 15-23 part blasts in the 1.163 log: ships or other bodies?
* The x5 aircraft/missile multiplier and the /5 armor reduction in the area routine, and the `+0x165` profile flag in the 0.66 factor, were read but not exercised.
* A 1.163 mod reading 1.151 values would need the matching `m_missile_explosive` and the 2x/flat-5 behaviour; not decided whether it is worth shipping.
