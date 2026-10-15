# Ally probe run 1 (hf_ally v0.3.1)

Evidence report, not reference. Date 2026-10-15, Steam 1.163 under Proton, campaign fights, `ally_mode = 0`, log `Highfleet_2026-10-15_19-05-48.log`. Tags: legend in `../../README.md`. Method: for the first 60 s of each battle (or until it ends) the mod writes one `ALLY probe ally` and one `ALLY probe enemy` line per game second (the enemy is the one nearest to the ally at that moment), and counts launches and shots every frame. Summary script: `hf_ally/tools/probe_summary.py`.

## Numbers [game]
Three battles, 29, 39 and 42 probe seconds. All lines were in state 1 (attack) for both sides, mode 0 for both.

| battle | ally rounds spent (reserve drop) | enemy rounds spent | ally speed avg / max | enemy speed avg / max | enemy lines targeting the ally |
|---|---|---|---|---|---|
| 1 | 66 | 62 | 74 / 92 | 42 / 118 | 21 of 29 |
| 2 | 10 (reserve 10 -> 0, ran dry) | 92 | 108 / 182 | 26 / 90 | 26 of 39 |
| 3 | 150 | 68 | 93 / 242 | 65 / 120 | 34 of 42 |

* **The ally is not slower or quieter than the enemy.** Over a whole battle it moved at least as fast on average and spent a comparable amount of ammunition (more in battle 3, less in battle 2). The "enemy-level sluggish" impression is the stock AI itself, not a handicap of the ally. The player's guess that ally and enemy AI are matched fits; the wingman-mode behaviour of run 1 and 2 was the mode-2 strike logic, not this.
* **Ammunition is part of "less active"**: in battle 2 the ally's gun reserve was 10 rounds and ran out within the probe window. A ship with a small magazine goes quiet, and the AI does not retreat to reload or switch behaviour [game, one ship].
* **Enemy targeting**: the enemy nearest to the ally targeted the ally in 21/29, 26/39 and 34/42 lines, so enemies close to the ally do shoot it. This sample is biased (it is the nearest enemy, not all of them); the player's impression that most fire goes to the flagship because it moves around more is not contradicted or confirmed for the whole field.
* **Duels**: ally and nearest enemy report the same `target_dist` and point at each other in most lines.
* **Zenith launcher list empty for both ships in all three battles** (`zenith n=0`, no launches counted). Either these ships carry no anti-ship missiles or the list offsets used (`+0x13d8/+0x13e0`, from the AI tick) are not the right list for these parts; in earlier runs the player saw allies launch missiles occasionally. Not settled: pick a fight with a known missile ship and compare with `reserve`/`loaded` of the list.
* **Counters**: `shots` counts drops of the summed loaded rounds and over-counts compared with the reserve drop (143 against 150 spent is fine, 8 against 10 fine, 46 against 66 and 52 against 62 under-count); use the reserve drop. `flags` (`+0xbbc..`) were `0,0,0,0,0` almost always, once `1,0,0,0,0` for the ally; they do not say much.

## Player observations from the same sessions [game]
* Bombs were never dropped by the ally; the ship probably never got into a diving position (conditions not read).
* An ally died from a **bomb explosion after taking enemy fire**, and its loss was counted on the end-of-battle screen: allies are full participants in the casualty accounting.
* When the player's ship leaves, control passes to the ally and there is no way to retreat (see `../findings/battle-ally.md`).
* Hypothesis from the player: the stock AI is tuned conservatively because bolder settings made ships ram the ground or fire too aggressively [guess, not tested].
