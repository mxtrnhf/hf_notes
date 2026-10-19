# Project status

The only file with perishable state: what is installed, released, open upstream or broken. Everything else in these notes is meant to stay true without edits. Last updated 2026-10-19, read from the game folder (`~/.local/share/Steam/steamapps/common/HighFleet/Modloader`), the repos' `git log` and `gh pr list`, not from older notes. Older versions of this file are in git history.

## Installed in the game folder
| Mod | File in `mods/` | Source commit | Config that matters |
|---|---|---|---|
| [hf_ai](docs/mods/hf-ai.md) | `hf_ai_v0.7.1.dll` | `ca7d678` (repo HEAD `7db1521` only changed the README; the DLL is byte-identical to the repo's release build) | `hf_ai.json`: `ai_flares` on, `log_panic`, curtain 0.6; `tactics` on, dive on, aim awareness on, strafe off |
| [hf_ally](docs/mods/hf-ally.md) | `hf_ally_v0.12.10_debug_telemetry.dll` | `e9540a5` | `ally.json`: `max_allies` 2, `auto_retreat`, `flagship_leaves` handover, `telemetry` on |
| [QoL fork](docs/mods/qol.md) | `highfleet_qol.dll` | `95e8bc7` (branch `ai-flares`; the file was written 1 minute after that commit) | `qol.json`: `ai_flares.enabled` false (hf_ai carries it), flare crash fix on, dump chance 0.7, delay 0.6 to 1.5, refuel player x10, speed `classic`, elevation on |

Everything else in `mods/` is a `.bak` of an older build. Not installed: `hf_probe`, `hf_voice`.

## Repos
| Repo | Remote | State |
|---|---|---|
| `hf_ai`, `hf_ally`, `hf_voice`, `hf_probe`, `hf_draw_test` | none (the only copies are on this machine) | clean; `hf_ally` also has the **side branch** `side/ignore-intercept-oids` (`09571bd`, v0.12.11-ignoreoid.1, `intercept_ignore_oids`, for a modder's Sprint; never merged to master; tester pack in `hf_side_patches/ignoreoid_pack/` (a loose older DLL also sits in `hf_side_patches/`); untested in play) |
| `hf_qol_fork` | `origin` = `mxtrnhf/highfleet-qol`, `upstream` = logdot | feature branches (`elevation`, `refuel-rate`, `pin-highfleet-rs`) are on origin; branch `ai-flares` (installed build, `95e8bc7`) is local only; local `main` is 4 commits ahead of `origin/main` |
| `hf_notes` | `mxtrnhf/hf_notes` | pushed (origin/master) as of 2026-10-19 |
| `old_standalone/*` | `hf_elevation` and `hf_speed` published, the rest local | the pre-merge standalone mods |

## Upstream (logdot/highfleet-qol)
| PR | State | What |
|---|---|---|
| #19 | merged 2026-10-14 (`f5423ca`) | refuel rate and speed curve |
| #20 | open | manual elevation (rebased 2026-10-16 as `aafbf6e`, 5 commits) |
| #18 | open | pin `highfleet-rs` to the last revision that builds |

* **`enabled` rule (logdot's review of #19):** only `elevation` and `ai_flares` may have an `enabled` flag; every other section defaults to vanilla. The flag crept back into refuel and speed once, from branches cut before the review.
* **Build break (found 2026-10-14):** `highfleet-qol` depends on `highfleet-rs` by git URL with no pinned revision and `Cargo.lock` is gitignored, so a fresh build resolves the newest `highfleet-rs`. Its commit `cfa6ae28` removed `Ammo::unknown_180h`, which `src/plane_guns.rs:271` still uses, so `cargo check --features 1_163` fails. Pinning `highfleet` to `3f6b54b3` in a local lockfile builds (copy `hf_qol_fork/Cargo.lock` into a fresh worktree). Fixed by PR #18; CI on PR #20 stays red until it merges.
* **Modloader quirk:** the modloader README says the release zip is `Artifacts.zip` and yields both `bass.dll` and `bass.dll_`. v4.1.0's `Modloader.zip` has only the loader `bass.dll`, so users must rename the original `bass.dll` to `bass.dll_` themselves.
* Standalone repos are the pre-merge versions. Salvo is postponed. `hf_probe` and `hf_draw_test` are debug-only and not released.

## Tester packs (workspace root)
Newest: `hf_release_pack_v0.12.2_debug.zip` (folder `hf_release_pack_v0.12.2_debug`); earlier: `v0.11.11_debug`, `v0.11.3_debug`, `v0.11.2_debug`, `v0.10.3`, `v0.9.3`. A pack holds the DLLs, a `qol.json` with every required key at stock values, an `ally.json` and a `README.txt` (settings, where the logs are, the tester plan: [docs/runs/tester-test-plan.md](docs/runs/tester-test-plan.md)). The pack's `qol.json` must keep the keys that have no serde default (list in [docs/mods/qol.md](docs/mods/qol.md)). The v0.10.3 pack carries one custom audio file, `Media/Snd/RADIO/radio_stall_01.wav`, which overwrites the vanilla file (testers are told to back it up).

## Open items
| Item | Notes |
|---|---|
| Analyse the hf_ai v0.7.1 run | sessions 1792342753/843/949/955; replay `tuning_telemetry/visualizer/replay_v071.html`; check ETA timing, shelter, strays, difficulty |
| Ghidra check-in | the 2026-10-18 annotations (AI fire gates, Zenith launch, fire bytes) are applied and saved; the shared-project check-in with the message "Annotate 1.163: AI fire gates, Zenith launch, fire bytes" is yours |
| Merge/engagement crash (testers) | scene state 2 of `SomethingWithLevelSerias` (`0x1402be084`) calls `FUN_1400f5b40` at `0x1402be0c8` with no null check on the first entry of the player-side vector `0x143a158e0`, seen null after leaving a city and empty after a load [guess until a crash address arrives]. Needs: the crash address, the tester's save, the three-way test (no mods / QoL only / hf_ally only), land-after-merge and land-after-load repros. Details: [docs/runs/ally-runs.md](docs/runs/ally-runs.md), [docs/findings/battle-ally.md](docs/findings/battle-ally.md#fleets-landing-and-the-location-scene) |
| `Collect_dead` stock crash | 1 in about 60 kills; waiting for a `hf_ally_deadnode.log` capture: [docs/findings/collect-dead-crash.md](docs/findings/collect-dead-crash.md) |
| Missile dump | kills about 20% of some launchers' missiles at the old delay; delay 0.6 to 1.5 cut early deaths from 19% to 5%, still being tuned |
| Pre-combat ALLY buttons | `hf_ally_v0.11.8` cover gate untested; with `hf_voice` loaded (same hook) the buttons do not follow the cards: [docs/rendering/precombat-screen.md](docs/rendering/precombat-screen.md) |
| Ally untested paths | ally destroyed in battle, prize-safe targeting on a convoy, several allies with `handover` |
| Allied bombers | needs bomb telemetry first (inventory, release counter, altitude); see the AI ideas in [docs/roadmap.md](docs/roadmap.md) |
| Audio clipping | reported, cause unknown (game, or the flare curtain); parked |
| README follow-ups | troubleshooting, a worked "add a part" guide; optional move to the modloader's logging SDK |

## Data and working rules
* Combat telemetry is in `tuning_telemetry/`; the ledger `REVIEWED.tsv` lists analysed sessions, unlisted ones in `Modloader/logs` are new. The user labels ships (Shipworks designs are named `TestProject`).
* Install DLLs and change game configs only when asked; keep a `.bak`. Long open questions: [docs/open-questions.md](docs/open-questions.md).
