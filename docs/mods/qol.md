# highfleet-qol (logdot) and our fork

> **Status (2026-10-19):** installed as `highfleet_qol.dll` built from the local fork branch `ai-flares` at `95e8bc7` (`hf_qol_fork`, no remote). Pull-request states: [../../STATUS.md](../../STATUS.md).

logdot's `highfleet-qol` is the one monolith the public features go into. What each of our features is, where it lives, and whether it is released:

| Feature | Page | Upstream | In the installed DLL |
|---|---|---|---|
| refuel rate | [refuel.md](refuel.md) | merged, PR #19 | yes (`player_rate_multiplier` 10) |
| speed curve | [speed.md](speed.md) | merged, PR #19 | yes (`preset` classic) |
| manual elevation | [elevation.md](elevation.md) | PR #20 open | yes (`enabled` true) |
| AI flares and evasion (`ai_flares`) | [../findings/ai/ai-flares.md](../findings/ai/ai-flares.md) | local branch only | built in, **off** (hf_ai carries it) |
| AI missile dump (`ai_missile_dump_chance`, `_min_delay`, `_max_delay`) | [../findings/combat-missile-launch.md](../findings/combat-missile-launch.md) | local branch only | chance 0.7, delay 0.6 to 1.5 s |
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
