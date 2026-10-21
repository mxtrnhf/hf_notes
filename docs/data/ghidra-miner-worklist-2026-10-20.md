# Ghidra miner work list (eight items) with effort estimates, from 2026-10-20
Source: the assistant message of 2026-10-20 17:14 in the session transcript `21bbac05-d5f2-4442-a58c-58d666d5dee6.jsonl` (line 10669), written when the `ghidra-miner` session sent its list. The rotation problem was the driver. Status column added 2026-10-21.

| # | What | Why it matters | Effort | Status 2026-10-21 |
|---|---|---|---|---|
| 1 | Which engines answer to which bank command | Most likely cause of the torque mismatch; I assumed banks 100/102 = left and 101/103 = right; the player controller might map them differently | 1-2 h | done: bank 1 = codes {100,102}, bank 2 = {101,103}; player sends 100/0x65 (angle) then 0x66/0x67 (force) ([static-engine-force-path.md](../findings/static-engine-force-path.md)) |
| 2 | Box2D solver settings and any non-stock behaviour | A rotation clamp or unusual constant would explain the 0.84 rad/s Q-spin ceiling better than game logic | 2-3 h | done: solver is stock (maxRotation pi/2, damping 0.05); the ceiling came from the per-engine stabiliser torque ([hull-stabiliser-engine-logic.md](../findings/hull-stabiliser-engine-logic.md), [box2d-struct-layouts.md](../findings/box2d-struct-layouts.md)) |
| 3 | The AI's attitude law and its avoidance term | Shows what the AI does that the player controller does not; unblocks the AI port | 1-2 h | done: `AiShip_SteerController` read (see [ai-tick-patch-sites.md](../findings/ai/ai-tick-patch-sites.md)); the same shape as the per-engine stabiliser |
| 4 | Gun fire control, shell flight, shell-vs-part hit rules | Biggest unknown for combat; aim, reload and spread first, hit rules second | 3-5 h | partly: [guns-aim-reload-fire.md](../findings/guns-aim-reload-fire.md), [blast-and-penetration.md](../findings/blast-and-penetration.md) |
| 5 | AI behaviour states (circling, retreat, target choice) | Needed to copy vanilla AI; much already known | 2-4 h | mostly done: [ai-behaviour-states.md](../findings/ai/ai-behaviour-states.md) (state table `+0xbdc`, kinds `+0xbd8`, target choice and scoring); open: states 3 and 5 meaning, sensor list source |
| 6 | Missile guidance, flare-vs-seeker rule | Moderate value until guns work | ~2 h | open |
| 7 | Ship removal and victory rules, campaign vs arcade | Needed to end simulated battles correctly | 1-2 h | mostly done: [ship-removal-and-battle-result.md](../findings/ship-removal-and-battle-result.md) (loss checks, removal, result codes -1/1/2); open: roster list criteria |
| 8 | Check numbers against logs once `sim.22` data exists | Replaces guesses with exact values | ~1 h | ongoing (sim.28 to sim.30 logs checked the stabiliser formula) |

Notes from the original message: the miner would do planes last; items 1-7 need no new flights; recommended order was 1 and 2 first (cheap, aimed at the rotation problem), then 3 and 4 in parallel with flights, then 5-7 once the flight model works.
