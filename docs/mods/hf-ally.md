# hf_ally: AI allies from the reserve, pre-combat buttons, telemetry

> Active. Repo `hf_ally` (local git, no remote). What is installed, the newest tester pack and the open items: [../../STATUS.md](../../STATUS.md).

A modloader DLL (Steam 1.163 only). In a battle entered through the pre-combat screen, a reserve ship is run by the game's own AI beside the player: it joins ~1.5 s after the start, can be told to retreat, is replaced by the next switched-on ship when it leaves or is lost, and spares prize ships. How the vanilla machinery works (what makes a Creature AI-run, the deploy, the retreat point, ORDER roles, prize ships, fleets and landing): [../findings/battle-ally.md](../findings/battle-ally.md). The pre-combat buttons: [../rendering/precombat-screen.md](../rendering/precombat-screen.md). Run reports: [../runs/ally-runs.md](../runs/ally-runs.md), [../runs/ally-probe-run-1.md](../runs/ally-probe-run-1.md), tester plan [../runs/tester-test-plan.md](../runs/tester-test-plan.md).

## Features
* Per-ship ALLY buttons on the pre-combat screen (follow the card shuffle), `ALLY` toggle, a `PLAYER` label on slot 1; several allies (`max_allies`); the next ship steps in when one is lost or has left.
* Retreat: key F8 (`retreat_key` 119), automatic when the flagship leaves alive (`flagship_leaves`: `handover` or `retreat`), and when combat fuel falls to `ally_fuel_retreat_percent`. F8 restores the order (`+0xd70`) of ships sent out.
* `spare_prizes` (default on): allies re-target away from prize ships. Radio voice lines on join, F8, retreat, destroyed. An `ALLY SUMMARY` log line after each battle.
* Diagnostics: version banner, crash reporter in every build; the `megalog` cargo feature adds an unbuffered log, heartbeat, clicks, scene states, fleet snapshots and a minidump (the modloader log is buffered, so a crash loses its tail: [../findings/collect-dead-crash.md](../findings/collect-dead-crash.md) and the crash hunt in [../runs/ally-runs.md](../runs/ally-runs.md)).
* Telemetry (cargo feature `telemetry`, config `telemetry: true`): ships, parts/damage and flying bodies CSVs, the player ship at 30 Hz, per-gun ammo type, a dead-node diagnostic. Described in [../findings/ai/ai-telemetry.md](../findings/ai/ai-telemetry.md) (v0.12.3 to 0.12.7); the simulator files of 0.12.11-sim.x (sim, simparts, debris, ammo, fire, partdump, bodies) are described in `hf_ml/handover/probe-dev.md` and in the first lines of each CSV.

## Config (`Modloader/config/ally.json`)
Keys: `spawn_ally`, `ally_delay_seconds`, `auto_retreat`, `retreat_key` (virtual-key code, 119 = F8), `flagship_leaves`, `ally_toggle`, `max_allies`, `ally_fuel_retreat_percent`, `telemetry`, `spare_prizes`, `ally_ai_ammo`, `plane_loadouts`, `extra_gunpod`, and the log switches `log_creatures`, `log_precombat`, `gui_inspect` (the last two are very large). Installed values: [../../STATUS.md](../../STATUS.md).

`extra_gunpod` (default on) is the tactical-plane gunpod: a chosen FAB/NURS plane on a vanilla T-7/LA-29 gets the 37 mm and, once bombs and rockets are gone, stays in **Combat.seria** and strafes with it. Custom crafts (SB-15 etc.) and the strategic bomber scene are excluded. Details and addresses: [../findings/plane-combat-modes-and-gunpods.md](../findings/plane-combat-modes-and-gunpods.md).

`ally_ai_ammo` (default on) gives each ally the enemy spawner's ammo dice (`+0xc7c` AP / `+0xc7d` proximity), so its AI controller uses AP / proximity. The reserve/refund accounting behind it and the v0.13.3 to 0.13.5 fixes: [../findings/gun-ammo-funding-and-refund.md](../findings/gun-ammo-funding-and-refund.md).

## Tested in play, and not
Seen: several allies, replacement after a retreat order, per-ship buttons, summary lines, handover when the flagship is shut down, flares on allies (now in `hf_ai`). Not seen as of the 2026-10-16 list: an ally destroyed in battle, prize-safe targeting on a convoy (fixed in 0.9.1, untested), several allies with `handover`.

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
| 0.12.11-sim.1 to sim.21 (2026-10-20, branch `feat/sim-telemetry` in `hf_ally_sim`) | simulator telemetry: `hf_ally_sim` (A/I/P/E/R/V rows), `simparts`, `debris`, `ammo`, `fire`, `partdump` CSVs, `bodies` tracks for planes, `current_battle.txt` for the probe. Every file and column, the sim.1..21 changelog and the quirks: `hf_ml/handover/probe-dev.md` (local repo `hf_ml`, not part of these notes) |
| 0.13.0 to 0.13.5 (2026-10-25 to 10-28) | custom aircraft / loadouts read from the game's craft and ammo tables; PLAYER / plane labels hidden once pre-combat is gone and under the Esc shade (0.13.4); ally ammo doctrine and the refund fixes (0.13.3 then 0.13.5): paid ammo returns to the inventory, the free 9999 base pool is never minted, and pre-combat ammo clicks are left alone. Tested in game 2026-10-28 |
| 0.13.6 to 0.13.7 (2026-10-28) | `extra_gunpod`: vanilla T-7/LA-29 bomb/rocket planes get the 37 mm and stay for a strafing phase after the payload; only in `Combat.seria`; custom crafts excluded. 0.13.7 also disables the vanilla class-3 stock draw for every chosen loadout, so a FAB plane no longer gets NAR-122 from another loadout of the craft. Tested in campaign; SB-15/no-draw re-test pending |

Per-version commits: `git log` in the `hf_ally` repo.

## Carrier plane buttons and custom aircraft (2026-10-25, unreleased, commit `bd5e647`)
The pre-combat plane-loadout buttons follow the game's own craft and loadout tables instead of a fixed T-7 / LA-29 list, so loadouts re-priced or added through the qol `planes` option, and custom aircraft such as the Hara Vera SB-15, get a button too (up to four plane types per card). Details and the install recipe for the SB-15: `docs/findings/custom-aircraft.md`; table layout: `docs/findings/carrier-plane-loadouts.md` sections 14 and 24.
