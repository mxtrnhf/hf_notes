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
Keys: `spawn_ally`, `ally_delay_seconds`, `auto_retreat`, `retreat_key` (virtual-key code, 119 = F8), `flagship_leaves`, `ally_toggle`, `max_allies`, `ally_fuel_retreat_percent`, `telemetry`, `spare_prizes`, and the log switches `log_creatures`, `log_precombat`, `gui_inspect` (the last two are very large). Installed values: [../../STATUS.md](../../STATUS.md).

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

Per-version commits: `git log` in the `hf_ally` repo.
