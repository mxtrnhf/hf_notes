# highfleet-qol (logdot) and our fork

> The QoL fork carries our public and local features; the installed build, the PR states and the build break are in [../../STATUS.md](../../STATUS.md). The fork `hf_qol_fork` has `origin` (`mxtrnhf/highfleet-qol`) and `upstream` (logdot); branch `ai-flares` is local only.

logdot's `highfleet-qol` is the one monolith the public features go into. What each of our features is, where it lives, and whether it is released:

| Feature | Page | Upstream | In the installed DLL |
|---|---|---|---|
| refuel rate | [refuel.md](refuel.md) | merged, PR #19 | yes (`player_rate_multiplier` 10) |
| speed curve | [speed.md](speed.md) | merged, PR #19 | yes (`preset` classic) |
| manual elevation | [elevation.md](elevation.md) | PR #20 open | yes (`enabled` true) |
| elevation rules (`elevation_rules`: vanilla/classic/modern/classic_kaz) | [../findings/elevation-rules-1151-vs-1163.md](../findings/elevation-rules-1151-vs-1163.md) | fork branch `elevation-rules` (pushed), merged locally into `allies-qol`; not game-tested | built in, **vanilla** (`classic` = 1.151 firing-arc rules) |
| AI flares and evasion (`ai_flares`) | [../findings/ai/ai-flares.md](../findings/ai/ai-flares.md) | local branch only | built in, **off** (hf_ai carries it) |
| AI missile dump (`ai_missile_dump_chance`, `_min_delay`, `_max_delay`) | [../findings/combat-missile-launch.md](../findings/combat-missile-launch.md) | local branch only | chance 0.7, delay 0.6 to 1.5 s (key defaults 0.1 / 0.5; commit `95e8bc7` also fixed `drop_stale`, which dropped bursts whose delay was over 1 s) |
| `allies` option of `ai_flares` | [hf-ally.md](hf-ally.md) | local branch only | `true` (only matters if `ai_flares` is on) |
| flare crash fix (`enable_flare_crash_fix`) | [../findings/flare-crash-hunt.md](../findings/flare-crash-hunt.md) | upstream | on; keep it on |

## Rules
* **`enabled` rule (logdot's review of #19):** only `elevation` and `ai_flares` may have an `enabled` flag; every other section defaults to vanilla. The flag crept back into refuel and speed once, via branches cut before the review.
* **No refuel clamp**; speed presets `vanilla`/`classic`/`modern`/`custom`.
* `highfleet-rs` is pinned by PR #18 (open): without it a fresh build breaks on `Ammo::unknown_180h`; the local `Cargo.lock` pins `3f6b54b3`.

## Fork branches
Working source is committed on the local branch `ai-flares` (rebuilt 2026-10-16 as `5c3ab73` on top of `elevation`, plus the dump-delay commit `95e8bc7`). Old tips are tags `old/elevation`, `old/ai-flares`, `old/ai-missile-dump`, `old/ai-flares-wip`, `old/refuel-rate`, `old/ai-flares-v2-tested`; a bundle and ref list are in `hf_qol_fork_build/archive/`.

## Required keys
A hand-made `qol.json` must carry every key without a serde default (`enable_anti_wobble`, `enable_unblocked_guns`, `enable_reduced_shake`, `enable_arcade_zoom`, the zoom keys, `planes`, `enable_shop_parts`) or the loader rejects it.
