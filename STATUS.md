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
