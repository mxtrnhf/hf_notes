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

## `elevation_rules` (top-level key, 1.163 only, added 2026-10-26)
Values: `vanilla` (default; the game's own), `classic` (1.151 firing-arc rules), `modern` (the 1.163 rules, same as `vanilla` for now), `classic_kaz` (`classic` plus empty hull does not block the KAZ). A missing key means `vanilla`; an existing `qol.json` is not rewritten, so add the key by hand.
* `classic`: (1) the `cmovz` that keeps the plain floor of a candidate body in `World_RaycastBodies` becomes `mov edx,eax` (`0x14023a103`, `0F 44 D0` -> `89 C2 90`): free-standing parts no longer block same-level guns; (2) the two `movss` loads of pi/4 in `Weapon_FlakInterceptScan` (`0x14002f864`, `0x14002faf8`) point at an existing `1.2f` (`0x140354758`); (3) the type 5 branch of `UpdateEngineCovered` (`0x14001c68a`, 17 bytes) loads `0.5f` (`0x1403527a4`) into the threshold register and jumps to the type 3 branch (`0x14001c65f`): the KAZ covered test as in 1.151 (rear 34 degrees, 50%), `OL.seria` untouched.
* `classic_kaz` adds: a detour at `0x140239f5b` (after the prologue of `World_RaycastBodies`, RCX = shooter) remembers whether the shooter's category is `1<<25` (KAZ); a detour at `0x14023a120` (the `GetPartFlagsWord` call of the candidate loop) skips a candidate whose oid starts with `MDL_FERMA` when the shooter is a KAZ. Trusses and hardpoints share category 128, hence the name test. Blocks, command bridge, hardpoints, armor and modules still block.
* Every patch checks the original bytes first and logs `... is not what was expected` and skips if they differ. Source: `hf_qol_fork/src/elevation_rules.rs`, README section "Elevation rules". The analysis behind it: [findings/elevation-rules-1151-vs-1163.md](../findings/elevation-rules-1151-vs-1163.md); the two agent reports are in `~/Development_Highfleet/elevation_port/` (`a-blocking`, `b-kaz-angles`; [agent] material, key bytes re-read by Claude).

