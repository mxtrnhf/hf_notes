# hf_ai: the tactical AI layer

> **Status (2026-10-19):** active. `hf_ai_v0.7.1.dll` is installed. Repo `hf_ai` (local git, no remote), last commit `ca7d678`. The repo's own README still says "v0.5.3" in its status line (stale, outside these notes).

A standalone modloader DLL (Steam 1.163 only) that keeps the stock per-ship AI tick (`FUN_140062f90`) and overrides its outputs from a small set of tactics: the steering waypoint (`creature+0xbf0/0xbf4`, written at `0x140064a8d`), the engine command strength (`0x140065744`), the fire bytes and the flare release. Design, decisions and the hook-ownership rules: [../findings/ai/ai-hf-ai-design.md](../findings/ai/ai-hf-ai-design.md). The ported flare/evasion algorithm: [../findings/ai/ai-flares.md](../findings/ai/ai-flares.md). The data it was designed from: [../findings/ai/ai-telemetry.md](../findings/ai/ai-telemetry.md), [../runs/ai-intrepid-benchmark.md](../runs/ai-intrepid-benchmark.md), [../runs/ai-underside.md](../runs/ai-underside.md).

## What it does (v0.7.1)
* **`ai_flares`** (ported from the QoL fork): a missile locked on an AI ship inside `trigger_range` starts a panic: flare burst, sidestep, sometimes a boosted evasion; v0.5 to v0.7 added the **flare curtain** (pre-emptive flares when the player's side launches a missile; timed by missile ETA; certain for the targeted ship; ships that cannot drop shelter behind one that can; retreat from the launched missile with boost).
* **`tactics`**: deny the dive (sidestep when the target is straight under or over), wrong-foot side, level pull, aim awareness (enemies slip off the player's aim line only while the player shoots), early fire (writes the group-0 fire byte for one second), stray-missile avoidance. "Strafe in the band" exists but is off (it did not show in play).
* Always installed: the log-only steering hook (CSV `hf_ai_steer_<unix>.csv`), and `hf_ai_panic_<unix>.log` with `log_panic`.

## Rules
* Exactly one of QoL `ai_flares.enabled` and hf_ai `ai_flares.enabled` may be on (both patch the same three sites). Installed: QoL off, hf_ai on.
* QoL `enable_flare_crash_fix` stays on.

## Installed config (`Modloader/config/hf_ai.json`, 2026-10-19)
`ai_flares` enabled, `log_panic`, `launch_flares_probability` 0.6, `launch_flares_targeted_only` and `launch_flares_shelter` on; `tactics` enabled, `blend_weight` 2.0, `strafe_enabled` false, `dive_enabled` true (`dive_min_s` 2, `dive_max_s` 4), `aim_enabled` true, `aim_fire_probability` 0.5.

## Versions
| Version | Commit | Added |
|---|---|---|
| 0.1.0 | `ebb91ee` | log-only steering hook with `decide()` |
| 0.2.0 | `2c563f5` | ported QoL `ai_flares` |
| 0.3.0 | `96c5739`, `91e4da2` | tactics stage "strafe in the band" (off by default) |
| 0.4.0 / 0.4.1 | `d938255` / `8ee7aac` | deny the dive; `dive_boost` through the engine hook |
| 0.5.0 to 0.5.5 | `29c2b90` to `746ee81` | flare curtain, all launchers per drop, retreat and boost, reserve, dive under/over split, curtain only near the target |
| 0.6.0 to 0.6.4 | `d729faa` to `3ef75d8` | aim awareness, early fire, shelter, aim dodge gated on the player shooting, panic evasion goes up not down |
| 0.7.0 / 0.7.1 | `6e4405f` / `ca7d678` | curtain first-drop delay and stray avoidance; ETA-timed curtain, certain curtain for the targeted ship, retreat range 3000 |

## Measured so far (2026-10-18, small samples, mostly one pilot) [data]
* The QoL missile-dump delay cut early missile deaths from 19% to 5%.
* A curtain on every enemy took the player's Zeniths to 0 of 23 hits; the preventive version (targeted ship plus neighbours) 6 of 15.
* Wrong-foot and level pull showed no gain. Aim dodge moved ships only ~17 u/s and was wasted when the player was not shooting (fixed in 0.6.3, unmeasured). Early fire is mostly extra close-range fire.
* Difficulty: v0.6.4 31.7 hp/s (v0.5.2 22.4, v0.6.0 42.5); the roster (Gladiator and Intrepid, 83% of shell damage) is the likely driver.
* The v0.7.1 run (sessions 1792342753/843/949/955) is replayed but not analysed.

## Open
Analyse the v0.7.1 run; allied bombers (needs bomb telemetry first); break-off and friendly-AI behaviour need your decisions; hf_ai has no remote. Current list: [../../STATUS.md](../../STATUS.md).
