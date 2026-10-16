# Project status

Volatile state: what is released, what is open upstream, what is broken. Everything else in these notes is meant to stay true without edits; keep dated, perishable facts here. Last updated 2026-10-14.

## Release plan
* **One monolith, the QoL mod.** Elevation, refuel and speed go into logdot's `highfleet-qol` by pull request: #18 pin `highfleet-rs`, #19 refuel and speed, #20 elevation draft. None accepted yet.
* The standalone repos (`highfleet-elevation`, `highfleet-speed` public; `hf_refuel`, `hf_multicharge`, `hf_salvo`, `hf_multimissile` local only) are the pre-merge versions. Salvo is postponed.
* `hf_probe` and `hf_draw_test` are debug-only, local, not released.
* To do: run the reinstall checklist ([docs/install.md](docs/install.md)); README follow-ups (troubleshooting, a worked "add a part" guide); optional move to the modloader's logging SDK. LICENSE names are set (`mxtrnhf`).

## QoL build break (found 2026-10-14)
`highfleet-qol` depends on `highfleet-rs` by git URL with no pinned revision and `Cargo.lock` is gitignored, so a fresh build or CI run resolves the newest `highfleet-rs`. Commit `cfa6ae28` (2026-10-13, 'Rename and document 1.163 ammo fields') removed `Ammo::unknown_180h`, which `src/plane_guns.rs:271` (`ammo_max_load`) still uses, so `cargo check --features 1_163` fails. Pinning `highfleet` to `3f6b54b3` in a local lockfile builds.
* Upstream fix: rename the field use, or commit `Cargo.lock`.
* Pinned in PR #18 ("Pin highfleet-rs to the last revision that builds", open). CI on PRs #19 and #20 stays red until #18 merges.

## Modloader quirk
The modloader README still says the release zip is `Artifacts.zip` and yields both `bass.dll` and `bass.dll_`; v4.1.0's `Modloader.zip` has only the loader `bass.dll`, so users must rename the original themselves (see [docs/install.md](docs/install.md)).

## Ally ships mod and ai-flares (state at the end of the 2026-10-16 session)
* **Installed builds** (game folder `Modloader/mods/`): `hf_ally_v0.9.1.dll` (archive and build copy `hf_ally_build/hf_ally_v0.9.1.dll`, older ones in `hf_ally_build/versions/`) and `highfleet_qol.dll` = `hf_qol_fork_build/archive/highfleet_qol_ai-flares-v6-allies.dll` (ai-flares plus missile dump plus the `allies` option). Config files: `Modloader/config/ally.json`, `Modloader/config/qol.json`. In `ally.json`: `max_allies 2`, `ally_toggle` on, `auto_retreat` on, `flagship_leaves handover`, `gui_inspect` and `log_precombat` off, `spare_prizes` default on. In `qol.json`: `ai_flares.allies true` (the file was rewritten with indent 2).
* **Where the sources are**: `hf_ally` is a local git repo with **no remote** (the only copy of the source is on this machine; last commit `7d8b18e`). The QoL fork's working source (`src/ai_flares.rs`, `src/ai_missile_dump.rs`, `src/config/ai_flares.rs`, the modified `config.rs`, `lib.rs`, `elevation.rs`, README) is **uncommitted on the fork branch `ai-flares`**, plus a stray `README.md.orig`.
* **Tested in play**: several allies, replacement after a retreat order, per-ship ally buttons, summary lines, handover when the flagship is shut down, flares on allies. **Not yet seen**: an ally destroyed in battle, prize-safe targeting on a convoy (the v0.9.0 hook fired but read the flag on the wrong object; fixed in v0.9.1, untested), several allies with `handover`.
* **Ghidra**: the annotations of 2026-10-16 are saved in the program; the shared-project check-in is the user's.
* **Tester pack** (2026-10-16): `/home/maksim/Development_Highfleet/hf_release_pack/` (and `hf_release_pack.zip` beside it): both DLLs (QoL v6 with allies, `hf_ally_v0.9.1`), a `qol.json` with every required key at stock values plus our `ai_flares` and `ai_missile_dump_chance 0.7`, an `ally.json`, and a `README.txt` explaining the settings and where the logs are (`Modloader/logs/Highfleet_*.log`, newest file). The QoL `qol.json` of the pack uses `planes {}` (vanilla) and no refuel/speed/elevation sections; those required keys were missing from a first lean draft, which the QoL loader would have rejected (`enable_anti_wobble`, `enable_unblocked_guns`, `enable_reduced_shake`, `enable_arcade_zoom`, the zoom keys, `planes`, `enable_shop_parts` have no serde default).
* Tester pack logging profile: `logging.json` (debug) is included, `ally.json` has `probe_lines` and `log_precombat` on; `gui_inspect` (very large) and `log_creatures` (huge) stay off. The Modloader default level when `logging.json` is absent was not checked.

