# hf_ai: the tactical AI layer

> Active. Source `hf_ai` in the public `mxtrnhf/highfleet-allies` repo (`ai/`). What is installed and the open items: [../../STATUS.md](../../STATUS.md).

A standalone modloader DLL (Steam 1.163 only) that keeps the stock per-ship AI tick (`AiShipTick` `0x140062f90`) and overrides its outputs from a small set of tactics: the steering waypoint (`creature+0xbf0/0xbf4`, written at `0x140064a8d`), the engine command strength (`0x140065744`), the native group-0 range gate (`0x14007ba84`) and the flare release. Design, decisions and the hook-ownership rules: [../findings/ai/ai-hf-ai-design.md](../findings/ai/ai-hf-ai-design.md). The ported flare/evasion algorithm: [../findings/ai/ai-flares.md](../findings/ai/ai-flares.md). The data it was designed from: [../findings/ai/ai-telemetry.md](../findings/ai/ai-telemetry.md) (telemetry is a local build), [../runs/ai-intrepid-benchmark.md](../runs/ai-intrepid-benchmark.md), [../runs/ai-underside.md](../runs/ai-underside.md).

## What it does (v0.10.15)
* **`tactics`**: universal aim dodging (enemy and allied ships slip off the closest hostile aim ray, player or AI, with a per-ship `aim_chance` roll), offensive early fire (a one-second widening of the native group-0 range gate; native alignment, friendly-fire, ammunition and burst-start checks remain), dive avoidance with merged `dive_chance` / `dive_dwell_s`, and dashing `dive_boost` / `aim_boost` escapes. Strafe/band positioning was removed in v0.10.6. Since v0.10.15, dive denial only reacts to an airborne combat target (`mode == 1`); a landed/taking-off target cancels an existing dive, while aim dodging and early fire remain available. Tactical courses retain the configured ground-clearance floor across the whole 400-unit waypoint and stop boosting/dashing at or below it; panic and curtain movement keep their older `NO_DESCENT_BELOW_Y` (-250) guard, and stock movement remains unguarded.
* **`ai_flares`**: missile panic (flare burst, sidestep, boosted/dashing panic evasion, rare barrel roll), stray-missile evasion, and the preventive flare curtain (ETA-timed, targeted ship plus neighbours, 1-8 s clamped wait, `launch_flares_min_rack` checked before every salvo, retreat with boost). Enemy ships react to player-side launches; allied AI ships react to enemy launches when `allies` is on. Curtain sheltering was retired in v0.10.11; ships without launchers evade directly.
* **`ai_missile_dump_*`**: AI ships empty their Zenith racks in a spaced burst (default 0.6-1.5 s between launches, 4 s timeout) instead of waiting for the game's 2 s cooldown.
* **`plane_group_*`**: AI carriers launch ready aircraft in groups instead of one at a time.
* **`twr_cutoff`**: top-level minimum strategic/Shipworks TWR (`creature +0x160c`) for tactics, early fire, missile evasion, rolls/boosts, curtain retreat and stray-missile reactions. Below it these manoeuvres are suppressed; locked-missile flare bursts, curtain flare drops, missile dumping and carrier plane groups remain available.
* **Layouts (v0.10.14):** Creature, Body, PartStats and AircraftLogic offsets now come from highfleet-rs revision `05c6207`; compile-time assertions keep the 1.163 contract. Fields upstream does not model (strategic TWR `+0x160c`, aim vector `+0xbf8`, gun reload/latch words, node identity `+0x18`) stay local in `ai/src/native_layout.rs`.
* Logging: `hf_ai_panic_<unix>.log` with `logging.log_panic`; the old steering/scan CSVs are gone from public builds (they belonged to the local telemetry build).

## Current implementation map
| Module | Responsibility |
|---|---|
| `ai/src/lib.rs` | config load, steering/engine/early-fire/plane-group/missile-dump hook installation, steering stage order (`decide` -> panic -> store) |
| `ai/src/tactics.rs` + `tactics_math.rs` | live-ship scan, hostile aim rays, dive/aim composition, ground and arena limits, early-fire permission |
| `ai/src/ai_flares.rs` + `panic_math.rs` | locked/stray threat scan, flare bursts, evasion, panic escape and barrel roll |
| `ai/src/curtain_math.rs` | preventive flare-curtain timers |
| `ai/src/early_fire.rs` | byte-checked detour of the native group-0 range gate |
| `ai/src/missile_dump.rs` | Zenith burst roll/launch wrappers |
| `ai/src/plane_group.rs` + `plane_group_math.rs` | tactical carrier launch groups |
| `ai/src/debug_state.rs` | versioned shared-memory feed for hf_ally's debug overlay |
| `ai/src/native_layout.rs` | highfleet-rs re-exports and the local offset contract |
| `ai/src/twr_math.rs` | strategic/Shipworks TWR cutoff |

## Rules
* Exactly one of QoL `ai_flares.enabled` and hf_ai `ai_flares.enabled` may be on (both patch the same flare/evasion sites). Installed: QoL off, hf_ai on.
* QoL `ai_missile_dump_chance` stays `0` while hf_ai's is above `0`; hf_ai warns about this at startup.
* QoL `enable_flare_crash_fix` stays on.
* The stock plane AI fix and the null-fleet/vector guards live in the bundled QoL, not in hf_ai.

## Config (`Modloader/config/hf_ai.json`)
Installed values: [../../STATUS.md](../../STATUS.md). The full key list with code defaults is in the public repo's `docs/hf-ai-config-reference.md`; the current plain-language guide is its `docs/hf-ai-tuning-guide.md` (the older v0.9.0 guide in this repo is [hf-ai-tuning-guide.md](hf-ai-tuning-guide.md)). The v0.10.11 preset has 49 leaf settings (48 gameplay plus `logging.log_panic`) and is unchanged through v0.10.15. It enables `ai_flares` (curtain probability 0.6, targeted-only, evade range 400), `tactics` (dive and universal aim dodging, `aim_chance` 0.75, `aim_fire_probability` 0.5), `ai_missile_dump_chance` 0.4 and `twr_cutoff` 2.0. Retired keys: `strafe_enabled`, `blend_weight`, `launch_flares_shelter`, `dive_min_accel`, `min_accel` (see the config reference's retirement table).

## Versions
| Version | Commit | Added |
|---|---|---|
| 0.1.0 | `ebb91ee` | log-only steering hook with `decide()` |
| 0.2.0 | `2c563f5` | ported QoL `ai_flares` |
| 0.3.0 | `96c5739`, `91e4da2` | tactics stage "strafe in the band" (off by default; removed in 0.10.6) |
| 0.4.0 / 0.4.1 | `d938255` / `8ee7aac` | deny the dive; `dive_boost` through the engine hook |
| 0.5.0 to 0.5.5 | `29c2b90` to `746ee81` | flare curtain, all launchers per drop, retreat and boost, reserve, dive under/over split, curtain only near the target |
| 0.6.0 to 0.6.4 | `d729faa` to `3ef75d8` | aim awareness, early fire, shelter, aim dodge gated on the player shooting, panic evasion goes up not down |
| 0.7.0 / 0.7.1 | `6e4405f` / `ca7d678` | curtain first-drop delay and stray avoidance; ETA-timed curtain, certain curtain for the targeted ship, retreat range 3000 |
| 0.8.0 to 0.9.0 | — | config trim, aim-dodge and dive tuning, the v0.9.0 tuning guide |
| 0.10.0 to 0.10.5 | — | `twr_cutoff` replaces the per-tactic accel gates (0.10.4), `tactics.allies` rename (0.10.5), carrier launch groups (0.10.3) |
| 0.10.6 to 0.10.10 | — | strafe/band removed (0.10.6), debug state table, preset trim |
| 0.10.11 to 0.10.13 | `5fcb139` to `ce1e20a` | 49-leaf preset, universal aim dodging, native group-0 early fire (0.10.12), dashing dive/aim/panic escapes (0.10.13); 0.10.12/0.10.13 are source-only |
| 0.10.14 | `894304f` | highfleet-rs `05c6207` layouts with compile-time offset asserts; no behaviour or config change; source-only (no release pack) |
| 0.10.15 | `3a78a54` | dive denial requires an airborne target; tactical ground-clearance floor and boost/dash cutoff; pack v0.14.17 |

## Measured so far (2026-10-18, small samples, mostly one pilot) [data]
* The QoL missile-dump delay cut early missile deaths from 19% to 5%.
* A curtain on every enemy took the player's Zeniths to 0 of 23 hits; the preventive version (targeted ship plus neighbours) 6 of 15.
* Dive v0.4.1 fired in 88% of alignments with no panic overlap and no errors, but the player's under+over share only moved from 59% to 56%: the sidestep (~120 u in 2 s) is smaller than the ~200 u needed while the player closes ~110 u in 2 s. Wrong-foot and level pull showed no gain (cone exit time 2.04 s unchanged). Aim dodge moved ships only ~17 u/s and was wasted when the player was not shooting (fixed in 0.6.3, unmeasured). Early fire is mostly extra CLOSE-range fire (median start 0.34 x reach, 13 of 34 episodes produced shells, at most 5-8% of the player's damage). Strays are real but did no measured damage. `ground_hard_y` cannot stop the stock AI from descending; since v0.10.15 it is a floor for tactical waypoints/boosts only. Panic and curtain movement keep their older `NO_DESCENT_BELOW_Y` guard; stock movement has none.
* Difficulty: v0.6.4 31.7 hp/s (v0.5.2 22.4, v0.6.0 42.5), about 2000 hp per battle in all three; the roster (Gladiator and Intrepid, 83% of shell damage) is the likely driver.
* The v0.7.1 run (sessions 1792342753/843/949/955) was replayed from a local capture (not in this repo) but is not analysed.
* No new measured data for v0.10.14/v0.10.15; their changes are cross-build only (see Open).

## Rollback and data
Every DLL swap and config change keeps a backup in the game folder (`hf_ai_v<ver>.dll.bak`, `hf_ai.json.bak_pre-<change>`, `qol.json.bak_pre-<change>`). Historical telemetry and reports are in the local `tuning_telemetry/` folder (not in git).

## Open
Validate v0.10.15 in game: the landed-target dive cancellation, the ground-clearance/boost cutoff, the dashing dive/aim/panic escapes and the native group-0 early-fire checks still need combat evidence; break-off and friendly-AI behaviour need your decisions. Current list: [../../STATUS.md](../../STATUS.md).
