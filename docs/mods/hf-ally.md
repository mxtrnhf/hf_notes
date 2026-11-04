# hf_ally: AI allies, pre-combat buttons, ship panels

> Active. Source `hf_ally` in the public `mxtrnhf/highfleet-allies` repo (`ally/`). What is installed, the newest tester pack and the open items: [../../STATUS.md](../../STATUS.md).

A modloader DLL (Steam 1.163 only). In a battle entered through the pre-combat screen, a reserve ship is run by the game's own AI beside the player: it joins ~1.5 s after the start, can be told to retreat, is replaced by the next switched-on ship when it leaves or is lost, and spares prize ships. How the vanilla machinery works (what makes a Creature AI-run, the deploy, the retreat point, ORDER roles, prize ships, fleets and landing): [../findings/battle-ally.md](../findings/ships/battle-ally.md). The pre-combat buttons: [../rendering/precombat-screen.md](../rendering/precombat-screen.md). Run reports: [../runs/ally-runs.md](../runs/ally-runs.md), [../runs/ally-probe-run-1.md](../runs/ally-probe-run-1.md), tester plan [../runs/tester-test-plan.md](../runs/tester-test-plan.md).

## Features
* Per-ship ALLY buttons on the pre-combat screen (they travel with the moving cards), an `ALLY` toggle and a `PLAYER` label on slot 1; several allies (`max_allies`); the next ship steps in when one is lost or has left.
* Retreat: key F8 (`retreat_key` 119), automatic when the flagship leaves alive (`flagship_leaves`: `handover` or `retreat`), and when combat fuel falls to `ally_fuel_retreat_percent`. F8 restores the order (`+0xd70`) of ships sent out.
* `spare_prizes` (default on): allies re-target away from prize ships. Radio voice lines on join, F8, retreat and destruction. An `ALLY SUMMARY` log line after each battle.
* Battle UI: `ally_panels` (a half-size ship panel per ally), `ally_reticles` (the native target box around each ally's target, tinted with `ally_damage_color`), the optional `debug_overlay` (range rings, native driver state, hf_ai state and steering waypoint), and combat ship switching (**1** top panel, **2** bottom panel, **TAB** cycles; `ship_switching`).
* `ally_bombers` (default off): player-style bombing runs for bomb-carrying wingmen. Enemy waves: `max_enemy_ships`, `enemy_group_size`, `enemy_all_at_once`.
* Carrier plane-loadout buttons: the game's own craft and loadout tables are read at runtime, so custom aircraft and QoL-repriced loadouts get a button too (up to six plane types per card). `extra_gunpod` gives vanilla T-7/LA-29 bomb/rocket planes the 37 mm and a strafing phase after the payload.
* Diagnostics: version banner and crash reporter in every build; `logging.debug_log` adds the unbuffered megalog, heartbeat, clicks, scene states and a minidump. `logging.dead_node` keeps the dead-node text diagnostic.
* Telemetry (cargo feature `telemetry`): ships, parts/damage, flying bodies, player-ship 30 Hz rows, per-gun ammo type and a dead-node diagnostic. **It is a local development build, not part of the public packs**: the public tree dropped the CSV capture in v0.14.3, but the telemetry code is still maintained locally and older `highfleet-allies` commits/releases (up to v0.14.2) still contain it. Described in [../findings/ai/ai-telemetry.md](../findings/ai/ai-telemetry.md); the sim-era CSV set (sim, simparts, debris, ammo, fire, partdump, bodies) is described in the first lines of each CSV and in the local simulator handover.

## Config (`Modloader/config/ally.json`)
Keys are grouped in the public [ally config reference](https://github.com/mxtrnhf/highfleet-allies/blob/main/docs/ally-config.md); the headers are: `spawn_ally`, `ally_delay_seconds`, `auto_retreat`, `retreat_key`, `flagship_leaves`, `ally_toggle`, `max_allies`, `spare_prizes`, `ally_bombers`, `intercept_ignore_oids`, `plane_bombers`, `extra_gunpod`, `plane_k13`, `plane_attack_delay`, `plane_aa_range`/`_delay`/`_angle`/`_speed`, `ally_ai_ammo`, `max_enemy_ships`, `enemy_group_size`, `enemy_all_at_once`, `plane_loadouts`, `ally_damage_color`, `ally_panels`, `ship_switching`, `ally_reticles`, `ally_reticle_scale`, `debug_overlay`, `ally_sounds`, `ally_fuel_retreat_percent`, `marker_text`, `marker_seam`, `marker_delay_ms`, and the `logging` block. Installed values: [../../STATUS.md](../../STATUS.md).

`extra_gunpod` (default on) is the tactical-plane gunpod: a chosen FAB/NURS plane on a vanilla T-7/LA-29 gets the 37 mm and, once bombs and rockets are gone, stays in **Combat.seria** and strafes with it. Custom crafts (SB-15 etc.) and the strategic bomber scene are excluded. Details and addresses: [../findings/plane-combat-modes-and-gunpods.md](../findings/aircraft/plane-combat-modes-and-gunpods.md).

`ally_ai_ammo` (default on) gives each ally the enemy spawner's ammo dice (`+0xc7c` AP / `+0xc7d` proximity), so its AI controller uses AP / proximity. The reserve/refund accounting behind it and the v0.13.3 to 0.13.5 fixes: [../findings/gun-ammo-funding-and-refund.md](../findings/combat/gun-ammo-funding-and-refund.md).

The stock aircraft AI fix and the null-fleet/vector guards now live in the bundled QoL (`fix_plane_ai_crash`, `fix_merge_crash`), not in hf_ally. Keep the two DLLs from the same pack.

## Tested in play, and not
Seen: several allies, replacement after a retreat order, per-ship buttons, summary lines, handover when the flagship is shut down, flares on allies (now in `hf_ai`), combat ship switching, ally panels. Not seen as of the last update: an ally destroyed in battle with a replacement, prize-safe targeting on a convoy (fixed in 0.9.1, untested), several allies with `handover`, the v0.14.11-0.14.13 button-follow work in a real shuffle.

## Versions
| Versions | What |
|---|---|
| 0.1.0 to 0.3.1 (2026-10-15) | log-only hook, wingman from the reserve via the vanilla deploy, `ally_mode`, activity probe |
| 0.4.x | retreat (F8, auto, `flagship_leaves`) |
| 0.5.x to 0.7.x | pre-combat seam, ALLY toggle, per-ship buttons |
| 0.8.x | several allies, step-in, summaries |
| 0.9.x | prize ships spared, F8 guard, tester-friendly defaults |
| 0.10.x | radio sounds, loss detection |
| 0.11.x | diagnostics, buttons follow the shuffle, PLAYER label |
| 0.12.0 to 0.12.3 | fuel retreat, `ally_mode` removed |
| 0.12.4 to 0.12.10 | telemetry, 30 Hz player row, gun ammo, dead-node diagnostic |
| 0.12.11-sim.1 to sim.53 (2026-10-20 onward, `hf_ally_sim`) | simulator telemetry: `hf_ally_sim` (A/I/P/E/R/V rows), `simparts`, `debris`, `ammo`, `fire`, `partdump`, `bodies`, `current_battle.txt`; local development, not in public packs |
| 0.13.0 to 0.13.5 (2026-10-25 to 10-28) | custom aircraft / loadouts read from the game's craft and ammo tables; PLAYER / plane labels hidden once pre-combat is gone and under the Esc shade (0.13.4); ally ammo doctrine and the refund fixes (0.13.3 then 0.13.5) |
| 0.13.6 to 0.13.7 (2026-10-28) | `extra_gunpod`; 0.13.7 disables the vanilla class-3 stock draw for every chosen loadout |
| 0.14.0 to 0.14.15 (2026-10-30 to 11-04) | HEX ally damage colour (0.14.0); GLITCH-off label fix (0.14.1); enemy waves, ally ship bombers, crash fixes moved to QoL, public telemetry removed (0.14.3); ally ship panels and target boxes (0.14.4); combat ship switching and reticle scale (0.14.5); panel marker fixes (0.14.6-0.14.10); pre-combat buttons follow moving cards and the plane column follows its ship (0.14.11-0.14.13); debug overlay with hf_ai state and waypoints (0.14.14-0.14.15) |

Per-version commits: `git log` in `highfleet-allies` (`ally/`).

## Carrier plane buttons and custom aircraft (released in 0.13.2; commit `bd5e647`)
The pre-combat plane-loadout buttons follow the game's own craft and loadout tables instead of a fixed T-7 / LA-29 list, so loadouts re-priced or added through the qol `planes` option, and custom aircraft such as the Hara Vera SB-15, get a button too (up to six plane types per card, `PLANE_ARM_1..54`). Details and the install recipe for the SB-15: [../findings/custom-aircraft.md](../findings/aircraft/custom-aircraft.md); table layout: [../findings/carrier-plane-loadouts.md](../findings/aircraft/carrier-plane-loadouts.md) sections 14 and 24.
